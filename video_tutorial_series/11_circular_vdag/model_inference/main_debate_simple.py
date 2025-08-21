import json
import logging
import os
import glob
from dataclasses import dataclass
from typing import Any, Dict, Optional
import re

from aios_instance import PreProcessResult, OnDataResult, Block
from aios_llama_cpp import LLAMAUtils, LLMMetrics, LLMMetricsUpdated  # noqa: F401
from huggingface_hub import hf_hub_download, snapshot_download

# Logger for simplified debater
LOGGER_NAME = "debater.reviewer.simple.min"
logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    lvl = getattr(logging, os.getenv("DEBATER_LOG_LEVEL", "DEBUG").upper(), logging.DEBUG)
    logger.setLevel(lvl)
    h = logging.StreamHandler()
    h.setLevel(lvl)
    h.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(h)
    logger.propagate = False


def _short(s: Any, limit: int = 500) -> str:
    try:
        t = s if isinstance(s, str) else json.dumps(s, default=str)
    except Exception:
        t = str(s)
    return t if len(t) <= limit else t[:limit] + "..."


def _strip_think_tags(text: Optional[str]) -> str:
    try:
        s = text or ""
        s = re.sub(r"(?is)<think>.*?</think>", "", s)
        s = re.sub(r"(?is)</?think>", "", s)
        return s.strip()
    except Exception:
        return (text or "").strip()


def _find_first_gguf_part(directory_path: str) -> str:
    if not os.path.isdir(directory_path):
        return f"Error: Directory not found at '{directory_path}'"
    for filename in os.listdir(directory_path):
        if "-00001-of-" in filename and filename.endswith(".gguf"):
            return os.path.join(directory_path, filename)
    return (
        "Error: Could not find a GGUF file matching the pattern '...-00001-of-....gguf' in '"
        + directory_path
        + "'"
    )


@dataclass
class DebaterSimpleInit:
    fixed_role: str
    model_name: str
    system_message: str = "You are a helpful assistant."
    # llama.cpp config
    n_ctx: int = 4096
    use_gpu: bool = True
    gpu_id: int = 0
    # generation
    max_tokens: int = 512
    temperature: float = 0.6
    top_p: float = 0.9


class DebaterReviewerSimpleBlock:
    """
    Simplified debater block.
    - Fixed role A or B (from init settings or data).
    - Builds a minimal prompt using topic + optional opponent last according to incoming prev_role.
    - Generates a reply and outputs only: {reply, prev_role: fixed_role, topic} plus router_meta with history.
    - No 'nodes' field and no judge/review/caps logic. Routing is delegated to the postprocessing debater router.
    - Preserves preprocessing-based summary seeding into the chat session.
    - Keeps per-debate history (running_summary and recent_turns) locally and emits it in router_meta each turn.
    """

    def __init__(self, context):
        self.context = context
        init_settings = context.block_init_settings or {}
        init_params = context.block_init_parameters or {}
        init_data = context.block_init_data or {}

        # Determine role and model
        _fr = init_settings.get("fixed_role") or init_data.get("fixed_role")
        if not (_fr and isinstance(_fr, str) and _fr.upper() in ("A", "B")):
            raise ValueError("fixed_role must be provided as 'A' or 'B' via init settings or data")
        self.fixed_role: str = _fr.upper()
        model_name = init_data.get("model_name")
        if not model_name:
            raise ValueError("Missing 'model_name' in blockInitData")

        # Logging control
        try:
            full_flag = init_settings.get("log_full_payloads", True)
            self.log_full_payloads = bool(full_flag) if isinstance(full_flag, bool) else str(full_flag).strip().lower() in ("1", "true", "yes", "y", "on")
        except Exception:
            self.log_full_payloads = True

        # History config and storage (per debate prefix)
        try:
            self.recent_turns_window = int((init_settings.get("recent_turns_window") if isinstance(init_settings, dict) else None) or 6)
        except Exception:
            self.recent_turns_window = 6
        # state: prefix -> {"running_summary": str|None, "turns": list[{role, reply}]}
        self._histories: Dict[str, Dict[str, Any]] = {}

        # llama.cpp config
        self.model_base_path = getattr(self.context, "common_path", "/home/ubuntu/models/")
        n_ctx = int(init_settings.get("model_config", {}).get("n_ctx", 4096))
        use_gpu = bool(init_settings.get("model_config", {}).get("use_gpu", True))
        gpu_id = int(init_settings.get("model_config", {}).get("gpu_id", 0))
        self.gen_args: Dict[str, Any] = {
            "max_tokens": int(init_params.get("max_tokens", 512)),
            "temperature": float(init_params.get("temperature", 0.6)),
            "top_p": float(init_params.get("top_p", 0.9)),
        }
        # Optional stop sequences for cleaner prompts
        try:
            stops = init_params.get("stop") or init_params.get("stop_sequences")
            if isinstance(stops, str):
                stops = [stops]
            if isinstance(stops, list) and stops:
                self.gen_args["stop"] = stops
                logger.info("[debater.min] using stop sequences: %s", stops)
        except Exception:
            pass

        # Resolve model path
        self.local_model_name: Optional[str] = None
        self._download_models(model_name)

        # Metrics best-effort
        metrics = None
        if getattr(self.context, "metrics", None):
            try:
                metrics = LLMMetricsUpdated(self.context.metrics)
            except Exception:
                try:
                    metrics = LLMMetrics(self.context.metrics)
                except Exception:
                    metrics = None

        # Create LLAMA utils and load model
        self.llama = LLAMAUtils(
            model_path=self.local_model_name,
            use_gpu=use_gpu,
            gpu_id=gpu_id,
            metrics=metrics,
            model_config={"n_gpu_layers": -1, "n_ctx": n_ctx, "verbose": True},
            cleanup_config={
                "enabled": init_settings.get("cleanup_enabled", True),
                "check_interval": init_settings.get("cleanup_check_interval", 300),
                "session_timeout": init_settings.get("cleanup_session_timeout", 3600),
            },
        )
        if not self.llama.load_model():
            raise RuntimeError("Failed to load debater model (simple.min)")

        self.blocks_system_message = init_data.get("system_message", "You are a helpful assistant.")

    # ------------------------- model resolution -------------------------
    def _download_models(self, model_name: str):
        base = getattr(self.context, "common_path", "/home/ubuntu/models/")
        if ".gguf" not in model_name:
            if model_name.endswith("/"):
                model_name = model_name[:-1]
            local_dir = os.path.join(base, model_name)
            if not os.path.exists(local_dir):
                namespace, repo = model_name.split("/")[:2]
                repo_id = f"{namespace}/{repo}"
                allow_patterns_1 = model_name.replace(repo_id + "/", "")
                allow_patterns_2 = allow_patterns_1 + "/*"
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=local_dir.replace(allow_patterns_1, ""),
                    allow_patterns=allow_patterns_2,
                    local_dir_use_symlinks=False,
                )
            self.local_model_name = _find_first_gguf_part(local_dir)
        else:
            local_dir = os.path.join(base, os.path.dirname(model_name))
            if os.path.exists(local_dir):
                model_files = glob.glob(os.path.join(local_dir, "*.gguf"))
                has = any(model_name.split("/")[-1] in k for k in model_files)
                if not has:
                    namespace, repo = model_name.split("/")[:2]
                    repo_id = f"{namespace}/{repo}"
                    filename = model_name.replace(os.path.join(namespace, repo) + "/", "")
                    hf_hub_download(repo_id=repo_id, filename=filename, local_dir=os.path.join(base, repo_id))
            else:
                namespace, repo = model_name.split("/")[:2]
                repo_id = f"{namespace}/{repo}"
                filename = model_name.replace(os.path.join(namespace, repo) + "/", "")
                hf_hub_download(repo_id=repo_id, filename=filename, local_dir=os.path.join(base, repo_id))
            self.local_model_name = os.path.join(base, model_name)

    # ----------------------------- helpers -----------------------------
    def _normalize_prefix(self, raw: Any) -> str:
        try:
            s = str(raw)
            if "::" in s:
                return s.split("::")[-1]
            return s
        except Exception:
            return str(raw)

    def _get_hist(self, prefix: str) -> Dict[str, Any]:
        h = self._histories.get(prefix)
        if h is None:
            h = {"running_summary": None, "turns": []}
            self._histories[prefix] = h
        return h

    def _trim_turns(self, turns: list) -> list:
        w = self.recent_turns_window
        if isinstance(w, int) and w > 0 and len(turns) > w:
            return turns[-w:]
        return turns

    def _compose_prompt(self, topic: Optional[str], role: str, prev_role: Optional[str], upstream_reply: Optional[str], user_msg: str) -> str:
        parts = []
        if topic:
            parts.append(f"TOPIC: {topic}")
        parts.append(f"YOUR ROLE: Debater {role}")
        # Treat any upstream from not-self (A/B or judge-continue) as opponent last turn
        if upstream_reply and (prev_role is None or prev_role != role):
            parts.append(f"OPPONENT LAST TURN: {upstream_reply}")
            parts.append("Provide a focused rebuttal.")
        if user_msg:
            parts.append("")
            parts.append(str(user_msg))
        return "\n".join(parts)

    # ----------------------------- I/O -----------------------------
    def on_preprocess(self, packet):
        try:
            data = packet.data
            logger.info("[debater.min on_preprocess] raw=%s", data if self.log_full_payloads else _short(data, 800))
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    data = {"input": data}

            # Preserve and inject summarization if provided
            try:
                if isinstance(data, dict) and data.get("_summarized") and data.get("_summary"):
                    prefix = self._normalize_prefix(data.get("session_prefix") or packet.session_id)
                    hist = self._get_hist(prefix)
                    # sanitize before storing/injecting
                    sanitized = _strip_think_tags(str(data.get("_summary")))
                    hist["running_summary"] = sanitized
                    sid = f"debate::{self.fixed_role}::{prefix}"
                    try:
                        if self.llama.has_chat_session(sid):
                            self.llama.remove_chat_session(sid)
                        self.llama.create_chat_session(sid, system_message=self.blocks_system_message)
                        self.llama.add_message_to_chat(sid, sanitized, role="system")
                        logger.debug("[debater.min on_preprocess] injected sanitized summary into %s", sid)
                    except Exception:
                        logger.exception("[debater.min on_preprocess] failed to inject summary; continuing")
            except Exception:
                logger.exception("[debater.min on_preprocess] summarization handling error (ignored)")

            extra = {"input": data}
            return True, [PreProcessResult(packet=packet, extra_data=extra, session_id=packet.session_id)]
        except Exception:
            logger.exception("[debater.min on_preprocess] error")
            return False, "on_preprocess error"

    def on_data(self, preprocessed_entry, is_ws=False):
        try:
            inp = preprocessed_entry.extra_data.get("input", {})
            logger.debug("[debater.min on_data] input=%s", inp if self.log_full_payloads else _short(inp, 800))

            if not isinstance(inp, dict) or inp.get("mode", "chat") != "chat":
                raise ValueError("DebaterSimple (min) expects chat mode inputs")

            role = self.fixed_role
            topic = inp.get("topic")
            # Canonical incoming fields from routers
            prev_role = inp.get("prev_turn_role") or inp.get("prev_role")  # support transitional producers
            upstream_reply = inp.get("prev_turn_text") if inp.get("prev_turn_text") is not None else inp.get("reply")
            receiver_role = inp.get("receiver_role")
            user_message = inp.get("message", "")
            system_message = inp.get("system_message") or self.blocks_system_message

            # Respect under_review flag to avoid storing history during retries
            under_review_val = inp.get("under_review")
            under_review = False
            try:
                if isinstance(under_review_val, str):
                    under_review = under_review_val.strip().lower() in {"true", "1", "yes", "y", "review", "under_review"}
                elif isinstance(under_review_val, (int, float)):
                    under_review = int(under_review_val) == 1
                else:
                    under_review = bool(under_review_val)
            except Exception:
                under_review = False

            # Unique per-debate chat session (never forwarded)
            prefix = self._normalize_prefix(inp.get("session_prefix") or preprocessed_entry.session_id)
            hist = self._get_hist(prefix)

            # Update history with upstream turn if present (skip when under_review)
            try:
                if not under_review and prev_role and upstream_reply:
                    hist_turns = hist.get("turns", [])
                    hist_turns.append({"role": str(prev_role), "reply": str(upstream_reply)})
                    hist["turns"] = self._trim_turns(hist_turns)
            except Exception:
                logger.exception("[debater.min] failed to record upstream turn")

            # Build minimal prompt and run inference
            prompt = self._compose_prompt(topic, role, prev_role, upstream_reply, user_message)
            logger.debug("[debater.min] prompt=%s", prompt if self.log_full_payloads else _short(prompt, 800))

            # If we have a running summary in history, also print the prompt in code fences for debugging
            try:
                rs = hist.get("running_summary")
                if isinstance(rs, str) and rs.strip():
                    logger.info("\n===== Debater Prompt (summary present) =====\n```\n%s\n```\n===== End Debater Prompt =====", prompt)
            except Exception:
                pass

            sid = f"debate::{role}::{prefix}"
            if not self.llama.has_chat_session(sid):
                self.llama.create_chat_session(sid, system_message=system_message)
            try:
                self.llama.add_message_to_chat(sid, prompt)
            except Exception:
                pass
            reply = self.llama.run_chat_inference(sid, stream=False, context=self.context, is_ws=is_ws, **self.gen_args)

            # Update history with our own turn (skip when under_review)
            try:
                if not under_review:
                    hist_turns = hist.get("turns", [])
                    hist_turns.append({"role": role, "reply": str(reply)})
                    hist["turns"] = self._trim_turns(hist_turns)
            except Exception:
                logger.exception("[debater.min] failed to record self turn")

            # Minimal payload for router: reply + prev_role=fixed_role + topic + router_meta(history)
            out: Dict[str, Any] = {
                "reply": reply,
                "prev_role": role,
                "topic": topic,
                # provide session_id for routers to scope state per session; no role suffix per canonical schema
                "session_id": f"{preprocessed_entry.session_id}",
                # Sidecar history emitted in router_meta only
                "router_meta": {
                    "running_summary": hist.get("running_summary"),
                    "recent_turns": list(hist.get("turns", [])),
                },
            }
            logger.info("[debater.min] emit minimal payload (no nodes/no session)")
            logger.debug("[debater.min] output=%s", out if self.log_full_payloads else _short(out, 800))
            return True, OnDataResult(output=out)
        except Exception:
            logger.exception("[debater.min on_data] error")
            return False, "on_data error"

    def management(self, action: str, data: Dict[str, Any]):
        try:
            if action == "info":
                return {"role": self.fixed_role}
            if action == "reset":
                self._histories.clear()
                return {"message": "cleared"}
            return {"error": f"unknown action {action}"}
        except Exception as e:
            logger.exception("[debater.min management] error")
            return {"error": str(e)}

    def get_muxer(self):
        return None


if __name__ == "__main__":
    block = Block(DebaterReviewerSimpleBlock)
    block.run()
