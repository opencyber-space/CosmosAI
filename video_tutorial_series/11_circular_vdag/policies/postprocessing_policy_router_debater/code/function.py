import logging
import os
import json
import time
from typing import List, Dict, Any, Optional
import hashlib
import requests
import traceback


# Module-level logger
LOGGER_NAME = "postprocessing.policy_router.debater"
logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    # Configure only if not already configured by the runtime
    _level = os.getenv("POSTPROC_LOG_LEVEL", "DEBUG").upper()
    try:
        logger.setLevel(getattr(logging, _level, logging.DEBUG))
    except Exception:
        logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False


def _snippet(s: Any, limit: int = 500) -> str:
    try:
        t = s if isinstance(s, str) else json.dumps(s, default=str)
    except Exception:
        t = str(s)
    return t if len(t) <= limit else t[:limit] + "..."


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
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()
        
        # The actual reply is often nested inside the 'data' field of the response packet
        if 'data' in response_data and isinstance(response_data['data'], str):
            try:
                inner_data = json.loads(response_data['data'])
                return inner_data.get("reply", "")
            except json.JSONDecodeError:
                return response_data['data']
        return response_data["data"].get("reply", "Could not find 'reply' in response.")

    except requests.exceptions.RequestException as e:
        error_message = f"HTTP Request Error calling external LLM: {e}\n{traceback.format_exc()}"
        print(error_message)
        return error_message
    except json.JSONDecodeError:
        error_message = f"Error decoding JSON response from external LLM.\n{traceback.format_exc()}"
        print(error_message)
        return error_message
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}\n{traceback.format_exc()}"
        print(error_message)
        return error_message


class GraphTools:
    def __init__(self, graph_json_str: str):
        self.block_id = os.getenv("BLOCK_ID")
        if not self.block_id:
            logger.error("[GraphTools] BLOCK_ID missing in environment")
            raise EnvironmentError("BLOCK_ID not set in environment variables")

        logger.debug("[GraphTools:init] block_id=%s, input_len=%s", self.block_id, len(graph_json_str or ""))
        try:
            self.graph_data = json.loads(graph_json_str)
        except json.JSONDecodeError as e:
            logger.exception("[GraphTools:init] Invalid JSON input for graph: %s", _snippet(graph_json_str))
            raise ValueError(f"Invalid JSON input: {e}")

        if "graph" not in self.graph_data:
            logger.error("[GraphTools:init] 'graph' key missing in input")
            raise ValueError("Input JSON must contain a 'graph' key")

        if self.block_id not in self.graph_data["graph"]:
            logger.error("[GraphTools:init] block_id %s not found in graph keys=%s", self.block_id, list(self.graph_data["graph"].keys()))
            raise ValueError(f"Current block_id '{self.block_id}' not found in the graph")

    def set_destination_nodes(self, nodes: List[str], node_to_block_map: Dict[str, str]) -> str:
        logger.info("[GraphTools:set_destination_nodes] nodes=%s map_keys=%s", nodes, list(node_to_block_map.keys()))
        try:
            outputs = []
            for node in nodes:
                if node not in node_to_block_map:
                    logger.error("[GraphTools:set_destination_nodes] node '%s' missing in node_to_block_map", node)
                    raise ValueError(f"Node '{node}' not found in node_to_block_map")

                block_id = node_to_block_map[node]
                outputs.append({
                    "host": f"{block_id}-executor-svc.blocks.svc.cluster.local",
                    "port": 6379,
                    "queue_name": "EXECUTOR_INPUTS",
                    "block_id": block_id
                })

            self.graph_data["graph"][self.block_id]["outputs"] = outputs
            logger.debug("[GraphTools:set_destination_nodes] outputs_count=%d", len(outputs))
            return json.dumps(self.graph_data)
        except Exception:
            logger.exception("[GraphTools:set_destination_nodes] error while setting destinations")
            raise

    def set_destination_blocks(self, block_ids: List[str]) -> str:
        logger.info("[GraphTools:set_destination_blocks] block_ids=%s", block_ids)
        try:
            outputs = []
            for dest_block in block_ids:
                outputs.append({
                    "host": f"{dest_block}-executor-svc.blocks.svc.cluster.local",
                    "port": 6379,
                    "queue_name": "EXECUTOR_INPUTS",
                    "block_id": dest_block
                })

            self.graph_data["graph"][self.block_id]["outputs"] = outputs
            logger.debug("[GraphTools:set_destination_blocks] outputs_count=%d", len(outputs))
            return json.dumps(self.graph_data)
        except Exception:
            logger.exception("[GraphTools:set_destination_blocks] error while setting blocks")
            raise

    def finalize(self, data: str) -> str:
        logger.info("[GraphTools:finalize] clearing outputs for block_id=%s", self.block_id)
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            logger.exception("[GraphTools:finalize] Invalid JSON input: %s", _snippet(data))
            raise ValueError(f"Invalid JSON input for finalize: {e}")

        if "graph" not in parsed or self.block_id not in parsed["graph"]:
            logger.error("[GraphTools:finalize] Invalid graph or block missing: keys=%s", list(parsed.keys()))
            raise ValueError("Graph structure invalid or current block_id not found in input")

        parsed["graph"][self.block_id]["outputs"] = []
        return json.dumps(parsed)



# Module-level state store for debates
STATE: Dict[str, Dict[str, Any]] = {}

class AIOSv1PolicyRule:
    
    def __init__(self, rule_id, settings, parameters):
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters

    # Optional management hook kept for compatibility and introspection
    def management(self, parameters: Dict[str, Any], input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("[Policy:management] rule_id=%s", self.rule_id)
            logger.debug("[Policy:management] settings=%s", _snippet(self.settings))
            return {
                "status": "ok",
                "rule_id": self.rule_id,
                "logger": LOGGER_NAME,
                "settings_keys": list(self.settings.keys()) if isinstance(self.settings, dict) else None,
            }
        except Exception:
            logger.exception("[Policy:management] Exception during management call")
            return {"status": "error"}

    # -------------------- Helper methods (private) --------------------
    def _derive_debate_key(self, output: Dict[str, Any]) -> str:
        # Prefer explicit session_id passed from blocks to support concurrent sessions on same topic
        sid = output.get("session_id")
        if sid:
            return f"session:{sid}"
        key = (self.settings or {}).get("debate_key")
        if key:
            return str(key)
        topic = output.get("topic") or ""
        h = hashlib.sha1(str(topic).encode("utf-8")).hexdigest()
        return f"debate:{h}"

    def _default_state(self) -> Dict[str, Any]:
        return {
            "rounds_by_role": {"A": 0, "B": 0},
            "consec_count": 0,
            "last_role": None,
            "total_rounds": 0,
            "retry_counts": {"A": 0, "B": 0},
            # retain last_by_role for simple stats; do not keep long turn buffers here
            "last_by_role": {"A": None, "B": None},
            # track self-retry cycles locally (per-router/role)
            "retry_pending": False,
        }

    def _get_state(self, debate_key: str) -> Dict[str, Any]:
        st = STATE.get(debate_key)
        if st is None:
            st = self._default_state()
            STATE[debate_key] = st
        return st

    def _save_state(self, debate_key: str, st: Dict[str, Any]) -> None:
        STATE[debate_key] = st

    def _augment_router_meta_for_judge(self, router_meta_in: Optional[Dict[str, Any]], st: Dict[str, Any], role: Optional[str]) -> Dict[str, Any]:
        """
        Merge ONLY the per-role count for the current debater into router_meta for judge escalation.
        Produces a minimal structure: {"router_counts": {"A": 4}} or {"router_counts": {"B": 3}}
        If role is unknown, no count is added.
        """
        meta = dict(router_meta_in) if isinstance(router_meta_in, dict) else {}
        try:
            count = 0
            if role in {"A", "B"}:
                try:
                    count = int((st.get("rounds_by_role", {}) or {}).get(role, 0) or 0)
                except Exception:
                    count = 0
                meta["router_counts"] = {role: count}
        except Exception:
            # Never fail escalation due to meta packing
            logger.exception("[debater] failed to pack router_counts into router_meta")
        return meta

    def _invert_assignment_info(self, node_to_block_map: Dict[str, str]) -> Dict[str, str]:
        return {v: k for k, v in (node_to_block_map or {}).items()}

    def _current_node_label(self, node_to_block_map: Dict[str, str]) -> str:
        block_id = os.getenv("BLOCK_ID")
        inv = self._invert_assignment_info(node_to_block_map)
        lbl = inv.get(block_id)
        if not lbl:
            logger.warning("[debater] current block_id %s not found in assignment_info; falling back to 'debater-%s'", block_id, (self.settings or {}).get("role", "A"))
        return lbl or f"debater-{(self.settings or {}).get('role', 'A')}"

    def _node_labels(self) -> Dict[str, str]:
        defaults = {"A": "debater-A", "B": "debater-B", "judge": "judge-llm"}
        cfg = (self.settings or {}).get("node_labels") or {}
        return {**defaults, **cfg}

    def _sanitize_payload(self, reply: str, prev_role: str, topic: Any, router_meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = {"reply": reply, "prev_role": prev_role, "topic": topic}
        if router_meta:
            payload["router_meta"] = router_meta
        return payload

    def _short_circuit_to_judge(self, output: Dict[str, Any]) -> bool:
        reason = (output or {}).get("reason")
        return reason in {"low_relevance_after_retries", "both_roles_reached_cap", "cap_exceeded", "periodic_review"}

    def _should_periodic_judge(self, st: Dict[str, Any]) -> bool:
        interval_cfg = (self.settings or {}).get("judge_interval_rounds")
        # Default to a strict non-zero interval to prevent indefinite loops
        try:
            interval = int(interval_cfg) if interval_cfg is not None else 4
        except Exception:
            interval = 4
        try:
            total_rounds = int(st.get("total_rounds") or 0)
        except Exception:
            total_rounds = 0
        return interval > 0 and total_rounds > 0 and (total_rounds % interval == 0)

    def _should_consec_judge(self, st: Dict[str, Any]) -> bool:
        try:
            limit = int((self.settings or {}).get("max_consec_by_same_role", 3))
        except Exception:
            limit = 3
        try:
            cc = int(st.get("consec_count") or 0)
        except Exception:
            cc = 0
        return limit > 0 and cc >= limit

    def _run_evaluator(self, text: str, topic: Any) -> float:
        # Return a score in [0,1]. If not configured, accept by default.
        settings = self.settings or {}
        evaluator = (settings or {}).get("evaluator") or {}
        # Fallbacks for ad-hoc evaluator inference
        default_addr = settings.get("external_llm_addr") or "CLUSTER1MASTER:31504"
        default_model = settings.get("external_llm_model_id") or "qwen3-32b-llama-cpp-block"
        server_address = evaluator.get("url") or evaluator.get("server_address") or default_addr
        model_id = evaluator.get("model") or evaluator.get("model_id") or default_model
        if not server_address or not model_id:
            logger.debug("[debater] evaluator configuration missing; defaulting score=1.0 (addr=%s, model=%s)", server_address, model_id)
            return 1.0
        prompt = f"You are a strict relevance scorer. Read the topic and the candidate reply and return a single line 'SCORE: <0..1>'.\n\nTopic:\n{topic}\n\nCandidate Reply:\n{text}\n\nRespond ONLY with 'SCORE: <number>'"
        try:
            response_text = call_external_llm(server_address, model_id, prompt)
            logger.debug("[debater] evaluator_raw=%s", _snippet(response_text, 300))
            score = None
            for line in (response_text or "").splitlines():
                if "SCORE" in line.upper():
                    try:
                        score = float(line.split(":", 1)[1].strip())
                        break
                    except Exception:
                        continue
            if score is None:
                logger.warning("[debater] evaluator score not found; defaulting to 1.0")
                return 1.0
            return max(0.0, min(1.0, score))
        except Exception:
            logger.exception("[debater] evaluator call failed; defaulting score=1.0")
            return 1.0

    def eval(self, parameters: Dict[str, Any], input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.monotonic()
        try:
            logger.info("[Policy:eval] rule_id=%s", self.rule_id)
            logger.debug("[Policy:eval] settings=%s", _snippet(self.settings))
            logger.debug("[Policy:eval] parameters=%s", _snippet(parameters))
            logger.debug("[Policy:eval] input_data_keys=%s", list(input_data.keys()))

            packet = input_data['packet']
            output_json = packet.data #ondata 's output will be present here
            output_ptr_str = packet.output_ptr

            # Parse upstream data
            output = json.loads(output_json or '{}')
            logger.debug("[debater] input_payload=%s", _snippet(output))

            # Settings and mappings
            node_to_block_map = (self.settings or {}).get("assignment_info", {})
            labels = self._node_labels()
            # role = str((self.settings or {}).get("role", "A")).upper()
            # if role not in ("A", "B"):
            #     logger.warning("[debater] invalid role '%s'; defaulting to 'A'", role)
            #     role = "A"

            # Debate key and state
            debate_key = self._derive_debate_key(output)
            st = self._get_state(debate_key)
            logger.debug("[debater] state_pre=%s", _snippet(st))

            # Extract minimal fields
            topic = output.get("topic")
            prev_role = output.get("prev_role")
            reply = output.get("reply") or ""
            router_meta_in = output.get("router_meta") if isinstance(output.get("router_meta"), dict) else None

            # Derive router role strictly from inbound prev_role; no defaults
            role = prev_role
            if role not in {"A", "B"}:
                judge_label = labels.get("judge", "judge-llm")
                nodes = [judge_label]
                router_meta_out = self._augment_router_meta_for_judge(router_meta_in, st, None)
                # Canonical minimal payload to judge (no legacy fields)
                try:
                    incoming_sid = output.get("session_id")
                    if not incoming_sid and hasattr(packet, "session_id"):
                        incoming_sid = getattr(packet, "session_id", None)
                except Exception:
                    incoming_sid = None
                payload = {"topic": topic, "router_meta": router_meta_out}
                if incoming_sid:
                    payload["session_id"] = incoming_sid
                st["retry_pending"] = False
                logger.warning("[debater] unknown prev_role='%s'; escalating to judge", prev_role)
                # Persist state
                self._save_state(debate_key, st)
                # Route immediately
                gt = GraphTools(output_ptr_str)
                packet.data = json.dumps(payload)
                updated_output_ptr = gt.set_destination_nodes(nodes, node_to_block_map)
                packet.output_ptr = updated_output_ptr
                input_data['packet'] = packet
                dt = (time.monotonic() - t0) * 1000.0
                logger.debug("[Policy:eval] done in %.2f ms (early escalate)", dt)
                return input_data

            # Determine if this inbound is a retry turn for this role
            is_retry_turn = bool(st.get("retry_pending") and prev_role == role)

            # Update counters only for real A/B turns (not retries)
            if not is_retry_turn and prev_role in {"A", "B"}:
                st["rounds_by_role"][prev_role] = st["rounds_by_role"].get(prev_role, 0) + 1
                st["total_rounds"] = st.get("total_rounds", 0) + 1
                if st.get("last_role") == prev_role:
                    st["consec_count"] = st.get("consec_count", 0) + 1
                else:
                    st["consec_count"] = 1
                st["last_role"] = prev_role
                st["last_by_role"][prev_role] = reply

            # Consec same-role guard (no upstream short-circuit reasons from debaters)
            if self._should_consec_judge(st):
                judge_label = labels.get("judge", "judge-llm")
                nodes = [judge_label]
                router_meta_out = self._augment_router_meta_for_judge(router_meta_in, st, role)
                # Canonical minimal payload
                try:
                    incoming_sid = output.get("session_id")
                    if not incoming_sid and hasattr(packet, "session_id"):
                        incoming_sid = getattr(packet, "session_id", None)
                except Exception:
                    incoming_sid = None
                payload = {"topic": topic, "router_meta": router_meta_out}
                if incoming_sid:
                    payload["session_id"] = incoming_sid
                st["retry_pending"] = False
                logger.info("[debater] consec_guard triggered: consec_count=%s", st.get("consec_count"))
            # Periodic judge intervention
            elif self._should_periodic_judge(st):
                judge_label = labels.get("judge", "judge-llm")
                nodes = [judge_label]
                router_meta_out = self._augment_router_meta_for_judge(router_meta_in, st, role)
                try:
                    incoming_sid = output.get("session_id")
                    if not incoming_sid and hasattr(packet, "session_id"):
                        incoming_sid = getattr(packet, "session_id", None)
                except Exception:
                    incoming_sid = None
                payload = {"topic": topic, "router_meta": router_meta_out}
                if incoming_sid:
                    payload["session_id"] = incoming_sid
                st["retry_pending"] = False
                logger.info("[debater] periodic_judge_intervention total_rounds=%s", st.get("total_rounds"))
            else:
                # Run evaluator gating
                score = self._run_evaluator(reply, topic)
                threshold = float((self.settings or {}).get("review_threshold", 0.5))
                logger.info("[debater] evaluator score=%.3f threshold=%.3f", score, threshold)
                if score >= threshold:
                    # Route to opponent using canonical fields only
                    opponent_role = "B" if role == "A" else "A"
                    opponent_label = labels.get(opponent_role, f"debater-{opponent_role}")
                    nodes = [opponent_label]
                    # Build canonical payload (no legacy keys, no suffix flipping)
                    try:
                        incoming_sid = output.get("session_id")
                        if not incoming_sid and hasattr(packet, "session_id"):
                            incoming_sid = getattr(packet, "session_id", None)
                    except Exception:
                        incoming_sid = None
                    payload = {
                        "prev_turn_text": reply,
                        "prev_turn_role": role,
                        "receiver_role": opponent_role,
                        "topic": topic,
                    }
                    if incoming_sid:
                        payload["session_id"] = incoming_sid

                    # Sidecar recent_turns for the receiver's preprocessor:
                    # 1) propagate any inbound router_meta.recent_turns from the debater block (thin & normalize)
                    # 2) append the receiver's own last reply if we have it in local state
                    try:
                        sidecar_meta: Dict[str, Any] = {}
                        # (1) Pass-through of inbound recent_turns (kept small and canonicalized)
                        recent_in = None
                        if isinstance(router_meta_in, dict):
                            recent_in = router_meta_in.get("recent_turns")
                        norm_list: List[Dict[str, str]] = []
                        if isinstance(recent_in, list) and recent_in:
                            for it in recent_in[-4:]:  # cap to last few to avoid bloat
                                if not isinstance(it, dict):
                                    continue
                                r = it.get("role")
                                t = it.get("text") or it.get("reply") or it.get("prev_turn_text")
                                if r in {"A", "B"} and isinstance(t, str) and t.strip():
                                    norm_list.append({"role": r, "text": t})
                        # (2) Receiver's last (older turn than prev_turn_*)
                        receiver_last = (st.get("last_by_role", {}) or {}).get(opponent_role)
                        if isinstance(receiver_last, str) and receiver_last.strip():
                            # Only add if not already present in the pass-through list
                            if not any((d.get("role") == opponent_role and d.get("text") == receiver_last) for d in norm_list):
                                norm_list.append({"role": opponent_role, "text": receiver_last})
                        if norm_list:
                            sidecar_meta["recent_turns"] = norm_list
                            payload["router_meta"] = sidecar_meta
                            logger.debug("[debater] attached sidecar recent_turns (n=%d, roles=%s)", len(norm_list), [d.get("role") for d in norm_list])
                        else:
                            logger.debug("[debater] no sidecar recent_turns available to attach")
                    except Exception:
                        logger.exception("[debater] failed building/attaching sidecar recent_turns")

                    st["retry_pending"] = False
                    st["consec_count"] = 0
                else:
                    # Self-route for retry or escalate to judge
                    max_retries = int((self.settings or {}).get("max_router_retries", 0))
                    cur = int(st.get("retry_counts", {}).get(role, 0))
                    if cur < max_retries:
                        st["retry_counts"][role] = cur + 1
                        st["retry_pending"] = True
                        current_label = self._current_node_label(node_to_block_map)
                        nodes = [current_label]
                        # Canonical payload back to self with under_review flag
                        try:
                            incoming_sid = output.get("session_id")
                            if not incoming_sid and hasattr(packet, "session_id"):
                                incoming_sid = getattr(packet, "session_id", None)
                        except Exception:
                            incoming_sid = None
                        payload = {
                            "prev_turn_text": reply,
                            "prev_turn_role": role,
                            "receiver_role": role,
                            "topic": topic,
                            "under_review": True,
                        }
                        if incoming_sid:
                            payload["session_id"] = incoming_sid
                        logger.info("[debater] self_route_retry attempt=%d/%d", cur + 1, max_retries)
                    else:
                        judge_label = labels.get("judge", "judge-llm")
                        nodes = [judge_label]
                        router_meta_out = self._augment_router_meta_for_judge(router_meta_in, st, role)
                        # Escalate to judge with minimal canonical payload (no legacy fields)
                        try:
                            incoming_sid = output.get("session_id")
                            if not incoming_sid and hasattr(packet, "session_id"):
                                incoming_sid = getattr(packet, "session_id", None)
                        except Exception:
                            incoming_sid = None
                        payload = {
                            "topic": topic,
                            "router_meta": router_meta_out,
                        }
                        if incoming_sid:
                            payload["session_id"] = incoming_sid
                        st["retry_pending"] = False
                        logger.info("[debater] escalate_to_judge after retries cur=%d max=%d", cur, max_retries)

            # Persist state
            self._save_state(debate_key, st)

            # Enforce minimal payload and route
            gt = GraphTools(output_ptr_str)
            packet.data = json.dumps(payload)
            updated_output_ptr = gt.set_destination_nodes(nodes, node_to_block_map) if nodes else gt.finalize(output_ptr_str)
            if nodes:
                logger.info("[debater] routed_to_nodes=%s payload=%s", nodes, _snippet(payload))
            else:
                logger.info("[debater] finalized outputs (no nodes)")

            # Update packet and write back to input_data
            packet.output_ptr = updated_output_ptr
            input_data['packet'] = packet

            dt = (time.monotonic() - t0) * 1000.0
            logger.debug("[Policy:eval] done in %.2f ms", dt)
            return input_data

        except Exception as e:
            logger.exception("[Policy:eval] Exception during policy evaluation")
            raise e
