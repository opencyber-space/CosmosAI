import json
import logging
import os
import glob
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import re

from aios_instance import PreProcessResult, OnDataResult, Block
from aios_llama_cpp import LLAMAUtils, LLMMetrics, LLMMetricsUpdated  # noqa: F401
from huggingface_hub import hf_hub_download, snapshot_download

LOGGER_NAME = "judge.capped.min"
logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    _lvl = os.getenv("JUDGE_LOG_LEVEL", "DEBUG").upper()
    lvl = getattr(logging, _lvl, logging.DEBUG)
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


def _find_first_gguf_part(directory_path: str) -> str:
    if not os.path.isdir(directory_path):
        return f"Error: Directory not found at '{directory_path}'"
    for filename in os.listdir(directory_path):
        if "-00001-of-" in filename and filename.endswith(".gguf"):
            return os.path.join(directory_path, filename)
    return f"Error: Could not find a GGUF file matching the pattern '...-00001-of-....gguf' in '{directory_path}'"


def _strip_think_tags(text: Optional[str]) -> str:
    try:
        s = text or ""
        s = re.sub(r"(?is)<think>.*?</think>", "", s)
        s = re.sub(r"(?is)</?think>", "", s)
        return s.strip()
    except Exception:
        return (text or "").strip()


@dataclass
class JudgeSimpleInit:
    model_name: str
    system_message: str = (
        "You are an impartial debate judge. Decide CONTINUE_A, CONTINUE_B, or FINAL_JUDGMENT concisely."
    )
    # llama.cpp config
    n_ctx: int = 8192
    use_gpu: bool = True
    gpu_id: int = 0
    # generation
    max_tokens: int = 1024
    temperature: float = 0.4
    top_p: float = 0.9


class JudgeCappedBlock:
    """
    Simplified judge block.
    - Consumes minimal inputs from debater router escalations: {reply, prev_role, topic} plus optional router_meta.
    - Maintains only lightweight per-debate context: last A/B utterances based on prev_role.
    - Builds a concise judging prompt including topic, optional running_summary, and recent_turns.
    - Emits minimal payload for the judge router: {judge_text, topic, opponent_last, bump_round=True}.
    - No routing or caps logic; those are enforced by the postprocessing judge router.
    - Preserves preprocessing summary seeding into the judge chat session.
    """

    def __init__(self, context):
        self.context = context
        init_settings = context.block_init_settings or {}
        init_params = context.block_init_parameters or {}
        init_data = context.block_init_data or {}
        self.model_base_path = getattr(context, "common_path", "/home/ubuntu/models/")

        # Control full-payload logging via init settings; default True
        try:
            full_flag = init_settings.get("log_full_payloads", True)
            self.log_full_payloads = bool(full_flag) if isinstance(full_flag, bool) else str(full_flag).strip().lower() in ("1", "true", "yes", "y", "on")
        except Exception:
            self.log_full_payloads = True
        logger.info("[init] log_full_payloads=%s", self.log_full_payloads)

        self.model_name = init_data.get("model_name")
        if not self.model_name:
            raise ValueError("Missing 'model_name' in blockInitData for judge")

        self.judge_system_message = init_data.get(
            "system_message",
            "You are an impartial debate judge. Decide CONTINUE_A, CONTINUE_B, or FINAL_JUDGMENT concisely.",
        )

        self.gen_args: Dict[str, Any] = {
            "max_tokens": int(init_params.get("max_tokens", 1024)),
            "temperature": float(init_params.get("temperature", 0.4)),
            "top_p": float(init_params.get("top_p", 0.9)),
        }

        self.model_config: Dict[str, Any] = {
            "n_gpu_layers": -1,
            "n_ctx": int((init_settings.get("model_config") or {}).get("n_ctx", 8192)),
            "verbose": True,
        }

        # Eager load model path
        self.local_model_name: Optional[str] = None
        self._download_models(self.model_name)

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

        self.llama = LLAMAUtils(
            model_path=self.local_model_name,
            use_gpu=bool((init_settings.get("model_config") or {}).get("use_gpu", True)),
            gpu_id=int((init_settings.get("model_config") or {}).get("gpu_id", 0)),
            metrics=metrics,
            model_config={k: v for k, v in self.model_config.items()},
            cleanup_config={
                "enabled": init_settings.get("cleanup_enabled", True),
                "check_interval": init_settings.get("cleanup_check_interval", 300),
                "session_timeout": init_settings.get("cleanup_session_timeout", 3600),
            },
        )
        if not self.llama.load_model():
            raise RuntimeError("Failed to load judge model (simple.min)")

        # lightweight state: per debate prefix
        self.last_by_role: Dict[str, Dict[str, Optional[str]]] = {}

    def _download_models(self, model_name: str):
        base = self.model_base_path
        if ".gguf" not in model_name:
            if (model_name.endswith("/")):
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

    def _compose_prompt(
        self,
        topic: Optional[str],
        last_a: Optional[str],
        last_b: Optional[str],
        running_summary: Optional[str],
        recent_turns: Optional[List[Dict[str, str]]],
        force_finalize: bool = False,
        force_reason: Optional[str] = None,
    ) -> str:
        head = [f"TOPIC: {topic or '(no topic)'}", ""]
        body: List[str] = []
        if running_summary:
            body.append("RUNNING SUMMARY (earlier turns):")
            body.append(str(running_summary))
            body.append("")
        if recent_turns:
            body.append("RECENT TURNS (most recent last):")
            for t in recent_turns:
                try:
                    body.append(f"{t.get('role')}: {t.get('reply')}")
                except Exception:
                    continue
            body.append("")
        else:
            if last_a is not None:
                body.append(f"A: {last_a}")
            if last_b is not None:
                body.append(f"B: {last_b}")
            body.append("")
        if force_finalize:
            tail = [
                "IMPORTANT: The system has reached caps. You MUST conclude now.",
                f"Reason: {force_reason}" if force_reason else "Reason: cap reached.",
                "Return exactly:",
                "DECISION: FINAL_JUDGMENT",
                "WINNER: A|B|DRAW",
                "REASON: <short>",
            ]
        else:
            tail = [
                "Return exactly:",
                "DECISION: CONTINUE_A|CONTINUE_B|FINAL_JUDGMENT",
                "If FINAL_JUDGMENT, add WINNER: A|B|DRAW and REASON: <short>.",
            ]
        return "\n".join(head + body + tail)

    # ----------------------------- I/O -----------------------------
    def on_preprocess(self, packet):
        try:
            data = packet.data
            logger.info("[judge.min on_preprocess] raw=%s", data if self.log_full_payloads else _short(data, 800))
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    data = {"input": data}

            # Preserve and inject summarization if provided
            try:
                if isinstance(data, dict) and data.get("_summarized") and data.get("_summary"):
                    prefix = self._normalize_prefix(data.get("session_prefix") or packet.session_id)
                    sid = f"judge::{prefix}"
                    sanitized = _strip_think_tags(str(data.get("_summary")))
                    try:
                        if self.llama.has_chat_session(sid):
                            self.llama.remove_chat_session(sid)
                        self.llama.create_chat_session(sid, system_message=self.judge_system_message)
                        self.llama.add_message_to_chat(sid, sanitized, role="system")
                        logger.debug("[judge.min on_preprocess] injected sanitized summary into %s", sid)
                    except Exception:
                        logger.exception("[judge.min on_preprocess] failed to inject summary; continuing")
            except Exception:
                logger.exception("[judge.min on_preprocess] summarization handling error (ignored)")

            extra = {"input": data}
            return True, [PreProcessResult(packet=packet, extra_data=extra, session_id=packet.session_id)]
        except Exception:
            logger.exception("[judge.min on_preprocess] error")
            return False, "on_preprocess error"

    def on_data(self, preprocessed_entry, is_ws=False):
        try:
            inp = preprocessed_entry.extra_data.get("input", {})
            logger.debug("[judge.min on_data] input=%s", inp if self.log_full_payloads else _short(inp, 800))

            topic = inp.get("topic")
            # Legacy fields no longer provided by debater router on escalation
            # prev_role = inp.get("prev_role")
            # reply = inp.get("reply") or ""

            # Router-provided meta with history
            router_meta = inp.get("router_meta") if isinstance(inp.get("router_meta"), dict) else {}
            recent_turns = router_meta.get("recent_turns") if isinstance(router_meta, dict) else None
            running_summary = router_meta.get("running_summary") if isinstance(router_meta, dict) else None
            # Force-finalize hint from router
            ff_raw = router_meta.get("force_finalize") if isinstance(router_meta, dict) else None
            ff = False
            try:
                if isinstance(ff_raw, bool):
                    ff = ff_raw
                elif isinstance(ff_raw, str):
                    ff = ff_raw.strip().lower() in ("true", "1", "yes", "y", "on")
                elif isinstance(ff_raw, (int, float)):
                    ff = int(ff_raw) == 1
            except Exception:
                ff = False
            ff_reason = router_meta.get("force_termination_reason") if isinstance(router_meta, dict) else None
            if ff:
                logger.info("[judge.min] force_finalize requested (reason=%s)", ff_reason)

            # Maintain light state by prefix (use router_meta recent_turns when available)
            prefix = self._normalize_prefix(inp.get("session_prefix") or preprocessed_entry.session_id)
            state = self.last_by_role.setdefault(prefix, {"A": None, "B": None})
            try:
                if recent_turns and isinstance(recent_turns, list):
                    last_a_rt = next((str(t.get("reply")) for t in reversed(recent_turns) if t.get("role") == "A" and t.get("reply")), None)
                    last_b_rt = next((str(t.get("reply")) for t in reversed(recent_turns) if t.get("role") == "B" and t.get("reply")), None)
                    if last_a_rt:
                        state["A"] = last_a_rt
                    if last_b_rt:
                        state["B"] = last_b_rt
            except Exception:
                pass
            last_a = state.get("A")
            last_b = state.get("B")

            # Judge prompt (prefer router_meta history if present)
            sid = f"judge::{prefix}"
            if not self.llama.has_chat_session(sid):
                self.llama.create_chat_session(sid, system_message=self.judge_system_message)
            prompt = self._compose_prompt(topic, last_a, last_b, running_summary, recent_turns, force_finalize=ff, force_reason=ff_reason)
            logger.debug("[judge.min] prompt=%s", prompt if self.log_full_payloads else _short(prompt, 800))
            # If we have running summary or recent_turns, also print the prompt in code fences for debugging
            try:
                if (isinstance(running_summary, str) and running_summary.strip()) or (isinstance(recent_turns, list) and recent_turns):
                    logger.info("\n===== Judge Prompt (context present) =====\n```\n%s\n```\n===== End Judge Prompt =====", prompt)
            except Exception:
                pass
            try:
                self.llama.add_message_to_chat(sid, prompt)
            except Exception:
                pass
            text = str(self.llama.run_chat_inference(sid, stream=False, context=self.context, is_ws=is_ws, **self.gen_args))
            logger.debug("[judge.min] raw_judge_text=%s", text if self.log_full_payloads else _short(text, 800))

            # Compute opponent_last preference: use last turn of the opposite role from recent_turns if decision points there
            up = text.upper()
            if recent_turns and isinstance(recent_turns, list):
                try:
                    # last statements by A/B for quick access
                    last_a_rt = next((t.get("reply") for t in reversed(recent_turns) if t.get("role") == "A"), None)
                    last_b_rt = next((t.get("reply") for t in reversed(recent_turns) if t.get("role") == "B"), None)
                except Exception:
                    last_a_rt = None
                    last_b_rt = None
            else:
                last_a_rt = None
                last_b_rt = None

            opponent_last = ""
            if "CONTINUE_A" in up:
                opponent_last = last_b_rt or last_b or ""
            elif "CONTINUE_B" in up:
                opponent_last = last_a_rt or last_a or ""

            out = {
                "judge_text": text,
                "topic": topic,
                "opponent_last": opponent_last,
                "bump_round": True,
                # provide session_id for routers to scope state per session
                "session_id": preprocessed_entry.session_id,
                # forward router meta so judge router can read router_counts
                "router_meta": router_meta if isinstance(router_meta, dict) else {},
            }
            logger.info("[judge.min] emit minimal payload (no nodes/no session)")
            logger.debug("[judge.min] output=%s", out if self.log_full_payloads else _short(out, 800))
            return True, OnDataResult(output=out)
        except Exception:
            logger.exception("[judge.min on_data] error")
            return False, "on_data error"

    def management(self, action: str, data: Dict[str, Any]):
        try:
            if action == "reset":
                self.last_by_role.clear()
                return {"message": "cleared"}
            return {"error": f"unknown action {action}"}
        except Exception as e:
            logger.exception("[judge.min management] error")
            return {"error": str(e)}

    def get_muxer(self):
        return None


if __name__ == "__main__":
    block = Block(JudgeCappedBlock)
    block.run()
