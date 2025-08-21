import json
import logging
import traceback
from typing import Optional
import importlib
# Attempt optional dynamic import of tiktoken to avoid hard dependency during static checks
try:  # pragma: no cover
    tiktoken = importlib.import_module("tiktoken")
except Exception:  # pragma: no cover
    tiktoken = None  # type: ignore
import requests
import time
import hashlib
import re

# Module-level logger for use in helpers as well
logger = logging.getLogger(__name__)


def call_external_llm(server_address, block_id, prompt):
    """
    Calls an external LLM service via HTTP POST.

    Args:
        server_address (str): The address of the HTTP server (e.g., 'CLUSTER1MASTER:31504').
        block_id (str): The ID of the model/block to call.
        prompt (str): The prompt to send to the LLM.

    Returns:
        str: The response from the LLM, or an error message.
    """
    url = f"http://{server_address}/v1/infer"
    headers = {"Content-Type": "application/json"}
    
    # Construct the payload based on the curl example
    payload = {
        "model": block_id,
        "session_id": f"external-call-{int(time.time())}",
        "seq_no": 1,
        "data": {
          "mode": "chat",
          "message": prompt
        }
    }

    try:
        logger.debug("[pre.summarizer] POST %s (model=%s) payload_len=%s", url, block_id, len(prompt or ""))
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()
        
        # The actual reply is often nested inside the 'data' field of the response packet
        if 'data' in response_data and isinstance(response_data['data'], str):
            try:
                inner_data = json.loads(response_data['data'])
                # print("Full response data:", inner_data) 
                return inner_data.get("reply", "")
            except json.JSONDecodeError:
                # If data is not a JSON string, it might be the reply itself
                return response_data['data']
        # print("Full response data:", response_data)  # Debugging line to inspect the full response
        # Fallback for simpler response structures that might have a top-level 'reply'
        return response_data["data"].get("reply", "Could not find 'reply' in response.")

    except requests.exceptions.RequestException as e:
        logger.error("HTTP Request Error calling external LLM: %s\n%s", e, traceback.format_exc())
        return f"HTTP Request Error calling external LLM: {e}"
    except json.JSONDecodeError as e:
        logger.error("JSON decode error from external LLM response: %s\n%s", e, traceback.format_exc())
        return "Error decoding JSON response from external LLM."
    except Exception as e:
        logger.error("Unexpected error calling external LLM: %s\n%s", e, traceback.format_exc())
        return f"An unexpected error occurred: {e}"


class AIOSv1PolicyRule:
    CONFIG_DEFAULTS = {
        "external_llm_addr": "CLUSTER1MASTER:31504",
        "external_llm_model_id": "qwen3-32b-llama-cpp-block",
        "summarize_prompt": """You are a neutral judge-summarizer. You will receive input that may include:\n- 'Previous summary:' (the last running summary)\n- 'Recent turns:' (the latest A/B messages)\n\nTask: Produce an updated, self-contained summary that:\n- Incorporates new information from Recent turns while preserving still-valid points from the Previous summary\n- Merges repeated points; preserve key claims and cited evidence; do not invent information\n- Remains neutral and balanced\n- Provides no chain-of-thought or analysis; output the final answer only\n\nFormat:\n- Concise bullet points labeled 'A:' and 'B:' reflecting the order they appear in Recent turns; merge repeats\n- Then add one neutral takeaway line\n\nIf 'Previous summary' is absent, summarize Recent turns alone.""",
        "enable_summarization": True,
        "min_tokens_for_summarization": 300,
        # Window size for our own recent_turns buffer (kept for compatibility)
        "history_max_messages": 3,
        "tokenizer_encoding": "cl100k_base",
        # Session-scoped controls
        "enable_session_state": True,
        # Canonical schema uses a single session_id without role suffixes; no normalization required
        "normalize_session_ids": False,
        # Summarize every turn by default
        "summarize_every_n_messages": 3,
        "emit_marker": True,
        "marker_field_name": "_summary_marker",
        "emit_recent_appendix": False,
        "recent_appendix_field": "_recent_appendix",
        "session_ttl_seconds": 3600,
        "max_sessions": 10000,
        # Allow router to mark packets as under review so we skip state/summarization
        "respect_under_review_flag": True,
        "under_review_field_name": "under_review",
        "under_review_true_values": [True, "true", "1", 1, "yes", "y", "review", "under_review"],
        # Guard use of incoming seq_no; disabled by default to avoid skipping turns when seq_no is static
        "use_seq_no_guard": False,
        # NEW: Ingest only A/B roles into recent_turns (skip judge/system/etc.)
        "filter_roles_to_ab_only": True,
        # NEW: Count sidecar prev_turn ingestion toward msgs_since_summary (enables cadence)
        "count_sidecar_into_msgs_since_summary": True,
        # NEW: Optionally include last summary text in the next summarization window
        "include_last_summary_in_prompt": True,
        "last_summary_label": "Previous summary",
        # NEW: Also ingest receiver self-turns provided via router_meta without bumping cadence by default
        "count_router_meta_into_msgs_since_summary": True,
    }

    def __init__(self, rule_id, settings, parameters):
        """
        Simple preprocessing policy for text summarization using external LLM.
        """
        self.rule_id = rule_id
        self.settings = settings or {}
        self.parameters = parameters or {}
        self.tokenizer = None

        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

        self._load_config()
        self._initialize_tokenizer()
        self._validate_config()

        # Session-scoped state: { norm_session_id: { msgs_since_summary, last_total_msgs, last_summary_hash, last_update_ts, summary_version } }
        self._session_state = {}
        self._last_prune_ts = 0.0

    def _load_config(self):
        """Loads configuration from settings using defaults."""
        for key, default_value in self.CONFIG_DEFAULTS.items():
            setattr(self, key, self.settings.get(key, default_value))

    def _validate_config(self):
        """Validates the loaded configuration."""
        if self.enable_summarization and (not self.external_llm_addr or not self.external_llm_model_id):
            raise ValueError("Summarization is enabled, but external LLM address or model ID is missing.")

    def _initialize_tokenizer(self):
        """Initializes the tiktoken tokenizer, or a fallback if unavailable."""
        try:
            if tiktoken is not None:
                self.tokenizer = tiktoken.get_encoding(self.tokenizer_encoding)
                self.logger.info(f"Tokenizer '{self.tokenizer_encoding}' loaded successfully.")
            else:
                self.tokenizer = None
                self.logger.warning("tiktoken not installed; using whitespace token approximation.")
        except Exception as e:
            self.tokenizer = None
            self.logger.error(f"Failed to load tokenizer '{self.tokenizer_encoding}': {e}. Falling back to whitespace tokens.")

    def _count_tokens(self, text: str) -> int:
        """Counts tokens in a text string using the configured tokenizer or a fallback."""
        try:
            if self.tokenizer is not None:
                return len(self.tokenizer.encode(text))
        except Exception:
            pass
        # Fallback: simple whitespace split
        return len((text or "").split())

    # --- New helpers: text normalization and sanitization ---
    def _normalize_ws(self, text: Optional[str]) -> str:
        try:
            return " ".join((text or "").split())
        except Exception:
            return (text or "")

    def _strip_think_tags(self, text: Optional[str]) -> str:
        """Remove <think>...</think> blocks and bare <think> tags. Case-insensitive."""
        try:
            s = text or ""
            # Remove paired tags
            s = re.sub(r"(?is)<think>.*?</think>", "", s)
            # Remove any remaining lone tags
            s = re.sub(r"(?is)</?think>", "", s)
            return s.strip()
        except Exception:
            return (text or "").strip()

    def _summarize_text(self, text: str) -> Optional[str]:
        """Summarizes text using an external LLM."""
        if not text or not text.strip():
            self.logger.warning("Empty text provided for summarization.")
            return None
        
        try:
            full_prompt = f"{self.summarize_prompt}\n\n{text.strip()}"
            self.logger.info(f"Calling external LLM for summarization. Text tokens: {self._count_tokens(text)}")
            
            summary = call_external_llm(self.external_llm_addr, self.external_llm_model_id, full_prompt)
            
            if summary and summary.strip():
                self.logger.info(f"Successfully generated summary. Length: {len(summary)} chars")
                # Also print the exact prompt used in code fences for debugging
                try:
                    self.logger.info("\n===== Summarization Prompt =====\n```\n%s\n```\n===== End Summarization Prompt =====", full_prompt)
                except Exception:
                    pass
                return summary.strip()
            
            self.logger.warning("External LLM returned an empty summary.")
            return None
        except Exception as e:
            self.logger.error(f"Error during summarization: {e}\n{traceback.format_exc()}")
            return None

    def _prune_sessions_if_needed(self):
        now = time.time()
        if not self.enable_session_state:
            return
        # Periodic prune every 60s
        if now - self._last_prune_ts < 60:
            return
        self._last_prune_ts = now
        ttl = float(self.session_ttl_seconds or 0)
        to_delete = []
        if ttl > 0:
            for sid, st in self._session_state.items():
                if now - st.get("last_update_ts", 0) > ttl:
                    to_delete.append(sid)
        # Enforce max_sessions by dropping oldest
        remaining = len(self._session_state) - len(to_delete)
        if remaining > int(self.max_sessions):
            # Sort by last_update_ts ascending
            extras = sorted(
                ((sid, st.get("last_update_ts", 0)) for sid, st in self._session_state.items() if sid not in to_delete),
                key=lambda x: x[1]
            )
            overflow = remaining - int(self.max_sessions)
            for sid, _ in extras[:overflow]:
                to_delete.append(sid)
        for sid in to_delete:
            self._session_state.pop(sid, None)
        if to_delete:
            self.logger.info("Pruned %d session state entries (ttl/max)", len(to_delete))

    # ---- New helpers: session recent_turns ingestion and building ----
    def _get_or_init_state(self, norm_sid: Optional[str]) -> Optional[dict]:
        if not (self.enable_session_state and norm_sid):
            return None
        st = self._session_state.setdefault(
            norm_sid,
            {
                "msgs_since_summary": 0,
                "last_total_msgs": 0,
                "last_summary_hash": None,
                "summary_version": 0,
                "last_update_ts": time.time(),
                # recent_turns holds [{"role": "A"|"B"|..., "text": str, "ts": float}]
                "recent_turns": [],
                "last_turn_hash": None,
                "last_seq_no": None,
                # Maintain a set of normalized turn signatures to prevent duplicates
                "seen_turn_sigs": set(),
            },
        )
        # Ensure set type on reload
        if not isinstance(st.get("seen_turn_sigs"), set):
            try:
                st["seen_turn_sigs"] = set(st.get("seen_turn_sigs") or [])
            except Exception:
                st["seen_turn_sigs"] = set()
        return st

    def _turn_sig(self, role: Optional[str], text: Optional[str]) -> Optional[str]:
        try:
            if not text:
                return None
            r = (role or "").strip().upper()
            return hashlib.sha1(f"{r}|{text}".encode("utf-8")).hexdigest()
        except Exception:
            return None

    def _ingest_minimal_turn(self, st: dict, target: dict, *, count_toward_msgs: bool = True) -> int:
        """Ingest a minimal turn from target into st['recent_turns'] if new.
        Returns 1 if a new turn was added, else 0.
        count_toward_msgs controls whether msgs_since_summary is incremented (used to optionally exclude sidecar)."""
        if not isinstance(st, dict):
            return 0
        try:
            # Prefer 'prev_role' as author of the incoming reply per design; fallback to 'role'
            role_raw = target.get("prev_role") or target.get("role")
            role = (role_raw or "").strip().upper()
            text = target.get("reply") or ""
            if not text:
                self.logger.debug("[recent_turns] skip: empty reply (role=%s)", role)
                return 0
            # Optional role filtering (skip judge/system/etc.)
            try:
                if getattr(self, "filter_roles_to_ab_only", False):
                    if (role or "").upper() not in ("A", "B"):
                        self.logger.debug("[recent_turns] skip: role filtered out (role=%s)", role)
                        return 0
            except Exception:
                pass

            seq_no = target.get("seq_no")
            # Basic out-of-order guard is optional; ignore seq_no by default
            try:
                if getattr(self, "use_seq_no_guard", False):
                    if seq_no is not None and st.get("last_seq_no") is not None and int(seq_no) <= int(st.get("last_seq_no")):
                        self.logger.debug("[recent_turns] skip: seq_no guard (incoming=%s <= last=%s)", seq_no, st.get("last_seq_no"))
                        return 0
            except Exception:
                pass
            # Normalized text for dedupe across entire window
            norm_txt = self._normalize_ws(text)
            sig = self._turn_sig(role, norm_txt)
            # Fast-path dedupe using seen signatures
            seen = st.get("seen_turn_sigs") if isinstance(st.get("seen_turn_sigs"), set) else set()
            if sig and sig in seen:
                self.logger.debug("[recent_turns] skip: seen signature (role=%s, chars=%d)", role, len(text))
                return 0
            if sig and st.get("last_turn_hash") == sig:
                self.logger.debug("[recent_turns] skip: duplicate hash of last turn (role=%s, chars=%d)", role, len(text))
                return 0
            # Also dedupe against entire included window (normalize whitespace)
            for existing in st.get("recent_turns", []) or []:
                try:
                    if ((existing.get("role") or "").strip().upper() == role) and (self._normalize_ws(existing.get("text")) == norm_txt):
                        self.logger.debug("[recent_turns] skip: duplicate within window (role=%s, chars=%d)", role, len(text))
                        # Track signature to avoid future re-add attempts
                        if sig:
                            seen.add(sig)
                            st["seen_turn_sigs"] = seen
                        return 0
                except Exception:
                    continue
            # Append and clamp window
            pre_len = len(st.setdefault("recent_turns", []))
            st["recent_turns"].append({"role": role, "text": text, "ts": time.time()})
            # Keep only the configured window
            try:
                win = int(self.history_max_messages) if self.history_max_messages else 5
            except Exception:
                win = 5
            if len(st["recent_turns"]) > max(1, win):
                st["recent_turns"] = st["recent_turns"][ -max(1, win) : ]
            post_len = len(st["recent_turns"])
            trimmed = (pre_len + 1) - post_len
            # Update signatures and counters
            st["last_turn_hash"] = sig
            # Recompute seen signatures from current window to stay consistent after clamping
            try:
                recompute: set = set()
                for t in st["recent_turns"]:
                    rr = (t.get("role") or "").strip().upper()
                    tt = self._normalize_ws(t.get("text") or "")
                    s2 = self._turn_sig(rr, tt)
                    if s2:
                        recompute.add(s2)
                st["seen_turn_sigs"] = recompute
            except Exception:
                # Fallback to adding current sig only
                if sig:
                    try:
                        seen.add(sig)
                        st["seen_turn_sigs"] = seen
                    except Exception:
                        st["seen_turn_sigs"] = {sig}
            if getattr(self, "use_seq_no_guard", False) and seq_no is not None:
                st["last_seq_no"] = seq_no
            if count_toward_msgs:
                st["msgs_since_summary"] = int(st.get("msgs_since_summary", 0)) + 1
            else:
                self.logger.debug("[recent_turns] ingested without incrementing msgs_since_summary")
            st["last_update_ts"] = time.time()
            # Diagnostics: window size and samples
            try:
                tail = st["recent_turns"][ -2: ]
                sample = [
                    f"{(t.get('role') or '')}: chars={len(t.get('text') or '')}" for t in tail
                ]
                self.logger.debug(
                    "[recent_turns] appended (role=%s, chars=%d). total=%d, window=%d, trimmed=%d, msgs_since_summary=%d, tail<=2=%s",
                    role,
                    len(text),
                    post_len,
                    win,
                    max(0, trimmed),
                    st.get("msgs_since_summary", 0),
                    sample,
                )
            except Exception:
                pass
            return 1
        except Exception:
            return 0

    def _build_text_from_recent(self, st: Optional[dict]) -> Optional[str]:
        if not isinstance(st, dict):
            return None
        turns = st.get("recent_turns") or []
        total = len(turns)
        if not turns:
            self.logger.debug("[recent_turns] build: no turns yet")
            return None
        try:
            win = max(1, int(self.history_max_messages or 5))
        except Exception:
            win = 5
        included = min(total, win)
        parts = []
        for t in turns[-win : ]:
            role = t.get("role") or ""
            txt = t.get("text") or ""
            if txt:
                if role:
                    parts.append(f"{role}: {txt}")
                else:
                    parts.append(txt)
        joined = "\n".join(parts) if parts else None
        if joined is None:
            self.logger.debug("[recent_turns] build: parts empty despite turns=%d", total)
            return None
        # Diagnostics: window composition
        try:
            tail = turns[-2:]
            sample = [f"{(t.get('role') or '')}: chars={len(t.get('text') or '')}" for t in tail]
            self.logger.debug(
                "[recent_turns] build: total=%d, window=%d, included=%d, chars=%d, tail<=2=%s",
                total,
                win,
                included,
                len(joined),
                sample,
            )
        except Exception:
            pass
        return joined

    def eval(self, parameters, input_data, context):
        """Processes input data for summarization using only session recent_turns; ignores upstream history."""
        if not self.enable_summarization:
            self.logger.info("Summarization is disabled.")
            return input_data

        try:
            packet = input_data.get("packet")
            if not packet:
                self.logger.warning("No packet found in input_data.")
                return input_data

            # Safer extraction of packet data (supports string JSON, dict, or envelope)
            raw = packet.data if hasattr(packet, "data") else packet
            self.logger.debug("Packet raw type: %s", type(raw))
            parsed = None
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                    self.logger.debug("Parsed JSON string into dict. Top-level keys: %s", list(parsed.keys())[:20])
                except Exception as e:
                    self.logger.error("Failed to parse packet.data JSON string: %s\n%s", e, traceback.format_exc())
                    return input_data
            elif isinstance(raw, dict):
                parsed = raw
                self.logger.debug("Packet raw is dict. Top-level keys: %s", list(parsed.keys())[:20])
            elif hasattr(raw, "data") and isinstance(raw.data, dict):
                parsed = raw.data
                try:
                    self.logger.debug("Packet has .data dict. Keys: %s", list(parsed.keys())[:20])
                except Exception:
                    pass
            else:
                self.logger.warning("Unsupported packet data type: %s", type(raw))
                return input_data

            is_batch = False
            envelope = parsed
            target = parsed
            if isinstance(parsed, dict) and isinstance(parsed.get("inputs"), list) and parsed["inputs"]:
                first = parsed["inputs"][0]
                if isinstance(first, dict):
                    is_batch = True
                    target = first
                    self.logger.debug("Detected inputs[] envelope; operating on inputs[0]")
                else:
                    self.logger.warning("Encountered inputs[0] that is not a dict; skipping summarization.")
                    return input_data
            self.logger.debug("Envelope detection: is_batch=%s; operating_on=%s", is_batch, "inputs[0]" if is_batch else "packet root")

            # Early skip when under review
            try:
                if getattr(self, "respect_under_review_flag", False):
                    flag_key = getattr(self, "under_review_field_name", "under_review")
                    flag_val = target.get(flag_key)
                    true_vals = set(str(v).lower() for v in getattr(self, "under_review_true_values", [True, "true", "1", 1, "yes", "y", "review", "under_review"]))
                    is_trueish = False
                    if isinstance(flag_val, str):
                        is_trueish = flag_val.strip().lower() in true_vals
                    elif isinstance(flag_val, (int, float, bool)):
                        is_trueish = str(flag_val).lower() in true_vals or int(bool(flag_val)) == 1
                    self.logger.debug("Under-review check: key=%s value=%s -> %s", flag_key, flag_val, is_trueish)
                    if is_trueish:
                        self.logger.info("Under-review flag detected; skipping summarization and session counters (flag=%s)", flag_key)
                        return input_data
            except Exception:
                # Best-effort; do not fail pipeline on flag parsing issues
                pass

            # Extract session id and normalize
            session_id = None
            try:
                session_id = target.get("session_id") or target.get("conversation_id")
            except Exception:
                session_id = None
            # Fallback to envelope's packet.session_id if JSON omitted it
            try:
                if not session_id and hasattr(packet, "session_id"):
                    session_id = getattr(packet, "session_id", None)
                    if session_id:
                        self.logger.debug("Session: using packet.session_id fallback=%s", session_id)
            except Exception:
                pass
            norm_sid = session_id if self.enable_session_state else None
            self.logger.debug("Session: id=%s (state_enabled=%s)", session_id, self.enable_session_state)

            # Initialize state and ingest minimal turn (canonical fields only)
            st = self._get_or_init_state(norm_sid)
            if st is None:
                self.logger.debug("Session state unavailable (norm_sid=%s); history won't persist.")

            # Ingest the receiver's own last message if provided in router_meta.recent_turns (older turn first)
            try:
                if st is not None and isinstance(target.get("router_meta"), dict):
                    recent = target["router_meta"].get("recent_turns")
                    receiver_role = None
                    try:
                        receiver_role = target.get("receiver_role")
                        if isinstance(receiver_role, str):
                            receiver_role = receiver_role.strip().upper()
                    except Exception:
                        receiver_role = None
                    kept = 0
                    total_sidecar = len(recent) if isinstance(recent, list) else 0
                    if isinstance(recent, list) and recent:
                        for item in recent:
                            if not isinstance(item, dict):
                                continue
                            r = item.get("role")
                            txt = item.get("text") or item.get("reply") or item.get("prev_turn_text")
                            # Only ingest receiver's own last (if we know receiver_role); else fallback to A/B filter
                            if receiver_role in ("A", "B") and (r or "").upper() != receiver_role:
                                continue
                            if isinstance(txt, str) and txt.strip() and r in ("A", "B"):
                                added = self._ingest_minimal_turn(
                                    st,
                                    {"prev_role": r, "reply": txt},
                                    count_toward_msgs=bool(getattr(self, "count_router_meta_into_msgs_since_summary", False)),
                                )
                                kept += int(bool(added))
                        self.logger.debug(
                            "[ingest.router_meta] ingested %d/%d sidecar turns for receiver_role=%s (counted=%s)",
                            kept,
                            total_sidecar,
                            receiver_role,
                            getattr(self, "count_router_meta_into_msgs_since_summary", False),
                        )
            except Exception:
                pass

            # Ingest the previous turn intended for the receiver (prev_turn_*) if present (newer turn)
            try:
                prev_turn_text = target.get("prev_turn_text")
                prev_turn_role = target.get("prev_turn_role")
                if st is not None and isinstance(prev_turn_text, str) and prev_turn_text.strip() and prev_turn_role in ("A", "B"):
                    added = self._ingest_minimal_turn(
                        st,
                        {"prev_role": prev_turn_role, "reply": prev_turn_text, "seq_no": target.get("seq_no")},
                        count_toward_msgs=bool(getattr(self, "count_sidecar_into_msgs_since_summary", False)),
                    )
                    if added:
                        self.logger.debug(
                            "[ingest.prev_turn] added role=%s chars=%d counted=%s",
                            prev_turn_role,
                            len(prev_turn_text),
                            getattr(self, "count_sidecar_into_msgs_since_summary", False),
                        )
            except Exception:
                pass

            # Ingest the receiver's own message if provided in canonical fields
            try:
                receiver_role = target.get("receiver_role")
                _ = receiver_role  # reserved for future use
            except Exception:
                pass

            # Build text window from session recent_turns
            text_content = self._build_text_from_recent(st) if st is not None else None
            if not text_content:
                self.logger.debug("No content from recent_turns; skipping summarization for this packet.")
                return input_data

            # Optionally prepend last summary for recursive summarization
            try:
                if st is not None and getattr(self, "include_last_summary_in_prompt", False):
                    last_sum = st.get("last_summary_text")
                    if isinstance(last_sum, str) and last_sum.strip():
                        label = getattr(self, "last_summary_label", "Previous summary")
                        text_content = f"{label}:\n{last_sum.strip()}\n\nRecent turns:\n{text_content}"
                        self.logger.debug("Included last summary in prompt (chars=%d)", len(last_sum))
            except Exception:
                pass

            token_count = self._count_tokens(text_content.strip())
            self.logger.debug("Token count computed: %d", token_count)
            if token_count <= self.min_tokens_for_summarization:
                self.logger.info("Text too short for summarization (%d <= %d).", token_count, self.min_tokens_for_summarization)
                # Emit marker even if too short, to expose pending deltas (msgs_since_summary already reflects per-turn ingestion)
                if self.enable_session_state and norm_sid and self.emit_marker:
                    st = self._get_or_init_state(norm_sid)
                    if st is not None:
                        st["last_update_ts"] = time.time()
                        marker = {
                            "session": norm_sid,
                            "pending_new_messages": st.get("msgs_since_summary", 0),
                            "summary_version": st.get("summary_version", 0),
                            "last_total_messages": st.get("last_total_msgs", 0),
                        }
                        try:
                            target[self.marker_field_name] = marker
                            self.logger.debug("Emitted short-text marker: %s", marker)
                        except Exception:
                            pass
                else:
                    self.logger.debug(
                        "No marker emitted (enable_state=%s norm_sid=%s emit_marker=%s)",
                        self.enable_session_state,
                        norm_sid,
                        self.emit_marker,
                    )
                return input_data

            # Session state based gating: summarize only every N new messages
            self._prune_sessions_if_needed()
            should_summarize = True
            if self.enable_session_state and st is not None:
                try:
                    every_n = int(self.summarize_every_n_messages)
                except Exception:
                    every_n = 5
                should_summarize = st.get("msgs_since_summary", 0) >= max(1, every_n)

            self.logger.debug(
                "Gate trace: is_batch=%s norm_sid=%s msgs_since=%s every_n=%s token_count=%s min_tokens=%s should_summarize=%s",
                is_batch,
                norm_sid,
                None if st is None else st.get("msgs_since_summary"),
                self.summarize_every_n_messages,
                token_count,
                self.min_tokens_for_summarization,
                should_summarize,
            )

            if should_summarize:
                # Log the full conversation window that will be summarized
                try:
                    self.logger.info("\n===== Summarization Window (tokens=%s, chars=%s) =====\n%s\n===== End Window =====", token_count, len(text_content), text_content)
                except Exception:
                    pass
                summary = self._summarize_text(text_content)
                if summary:
                    # Sanitize summary from hidden thoughts before storing/logging
                    sanitized = self._strip_think_tags(summary)
                    try:
                        self.logger.info("\n===== External Summary (chars=%s) =====\n%s\n===== End Summary =====", len(sanitized), sanitized)
                    except Exception:
                        pass
                    target["_summary"] = sanitized
                    target["_original_token_count"] = token_count
                    target["_summarized"] = True
                    self.logger.info("Summary added (chars=%d). is_batch=%s", len(sanitized), is_batch)

                    # Update session state after summarization
                    if st is not None:
                        st["msgs_since_summary"] = 0
                        st["last_summary_hash"] = hashlib.sha1(sanitized.encode("utf-8")).hexdigest()
                        st["summary_version"] = st.get("summary_version", 0) + 1
                        st["last_update_ts"] = time.time()
                        st["last_summary_text"] = sanitized
                        # Track the current total messages retained in window
                        try:
                            st["last_total_msgs"] = len(st.get("recent_turns") or [])
                        except Exception:
                            pass
                        self.logger.debug(
                            "Session updated after summarize: %s",
                            {k: st.get(k) for k in ("msgs_since_summary", "last_total_msgs", "summary_version")},
                        )
                else:
                    self.logger.info("No summary generated by external LLM.")
            else:
                # Emit marker with pending delta and optionally the recent appendix
                if self.emit_marker and st is not None:
                    marker = {
                        "session": norm_sid,
                        "pending_new_messages": st.get("msgs_since_summary", 0),
                        "summary_version": st.get("summary_version", 0),
                        "last_total_messages": st.get("last_total_msgs", 0),
                    }
                    try:
                        target[self.marker_field_name] = marker
                        self.logger.debug("Emitted cadence marker: %s", marker)
                    except Exception:
                        pass
                if getattr(self, "emit_recent_appendix", False):
                    try:
                        target[self.recent_appendix_field] = text_content
                        self.logger.debug("Attached recent appendix (%d chars)", len(text_content))
                    except Exception:
                        pass

            # Write back packet
            updated = envelope if is_batch else target
            try:
                if hasattr(packet, "data"):
                    packet.data = json.dumps(updated)
                else:
                    input_data["packet"] = updated
                self.logger.debug("Packet updated successfully. Envelope=%s", is_batch)
            except Exception as e:
                self.logger.error("Failed to serialize updated packet: %s\n%s", e, traceback.format_exc())

        except Exception as e:
            self.logger.error("Error in preprocessing evaluation: %s\n%s", e, traceback.format_exc())
        
        return input_data

    def management(self, action: str, data: dict) -> dict:
        """Management interface for the policy."""
        try:
            if action == "get_config":
                # Return current config values
                cfg = {k: getattr(self, k, None) for k in self.CONFIG_DEFAULTS.keys()}
                return {"status": "success", "config": cfg}
            elif action == "update":
                # Update runtime-configurable settings
                updates = data or {}
                for k, v in updates.items():
                    if k in self.CONFIG_DEFAULTS:
                        setattr(self, k, v)
                        self.settings[k] = v
                return {"status": "success", "updated": list(updates.keys())}
            elif action == "test_connection":
                # Simple ping to external LLM
                try:
                    probe = call_external_llm(self.external_llm_addr, self.external_llm_model_id, "Ping")
                    if isinstance(probe, str):
                        return {"status": "success", "message": "External LLM connection successful."}
                    return {"status": "error", "message": "External LLM returned an empty response."}
                except Exception as e:
                    return {"status": "error", "message": f"Connection test failed: {e}"}
            elif action == "reset_sessions":
                self._session_state.clear()
                return {"status": "success", "message": "Session state cleared."}
            elif action == "get_sessions":
                # Return a sanitized shallow copy (do not expose texts)
                safe = {}
                for k, v in self._session_state.items():
                    if not isinstance(v, dict):
                        continue
                    c = {kk: vv for kk, vv in v.items() if kk not in ("recent_turns", "last_summary_text")}
                    try:
                        c["recent_turns_len"] = len(v.get("recent_turns", []))
                    except Exception:
                        c["recent_turns_len"] = 0
                    safe[k] = c
                return {"status": "success", "sessions": safe}
            else:
                return {"status": "error", "message": f"Unknown action '{action}'"}
        except Exception as e:
            self.logger.error("Management error: %s\n%s", e, traceback.format_exc())
            return {"status": "error", "message": str(e)}
