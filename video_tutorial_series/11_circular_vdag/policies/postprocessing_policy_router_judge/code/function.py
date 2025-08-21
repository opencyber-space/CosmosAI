import logging
import os
import json
import time
from typing import List, Dict, Any, Optional
import hashlib


# Module-level logger
LOGGER_NAME = "postprocessing.policy_router.judge"
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
            "total_rounds": 0,
            "judge_continue_count": 0,
            # Track per-role counts observed from debater router (for deriving total_rounds)
            "role_counts": {"A": 0, "B": 0},
        }

    def _get_state(self, debate_key: str) -> Dict[str, Any]:
        st = STATE.get(debate_key)
        if st is None:
            st = self._default_state()
            STATE[debate_key] = st
        return st

    def _save_state(self, debate_key: str, st: Dict[str, Any]) -> None:
        STATE[debate_key] = st

    def _parse_decision(self, judge_text: str) -> Dict[str, Any]:
        """
        Parse judge_text robustly by extracting the last explicit DECISION line that does not
        contain option menus like "CONTINUE_A|CONTINUE_B|FINAL_JUDGMENT". If no such DECISION
        line is found, fall back to scanning other lines (still ignoring any line with '|').
        Defaults to FINAL_JUDGMENT when nothing valid is found.
        """
        t = (judge_text or "")
        lines = t.splitlines()

        def scan(only_decision_lines: bool) -> Optional[str]:
            last: Optional[str] = None
            for line in lines:
                up = line.strip().upper()
                if '|' in up:
                    # Ignore instructional/menu lines
                    continue
                if only_decision_lines and "DECISION" not in up:
                    continue
                if "CONTINUE_A" in up:
                    last = "CONTINUE_A"
                if "CONTINUE_B" in up:
                    last = "CONTINUE_B"
                if "FINAL_JUDGMENT" in up:
                    last = "FINAL_JUDGMENT"
            return last

        choice = scan(only_decision_lines=True) or scan(only_decision_lines=False)

        if choice == "CONTINUE_A":
            return {"type": "CONTINUE", "role": "A"}
        if choice == "CONTINUE_B":
            return {"type": "CONTINUE", "role": "B"}
        # Default to finalize if unrecognized or missing
        return {"type": "FINAL_JUDGMENT"}

    def _apply_caps(self, st: Dict[str, Any]) -> bool:
        # Use strict non-zero defaults to prevent indefinite loops
        max_rounds = int((self.settings or {}).get("max_rounds", 20) or 20)
        cont_cap = int((self.settings or {}).get("judge_continue_cap", 5) or 5)
        if max_rounds and st.get("total_rounds", 0) >= max_rounds:
            logger.info("[judge] max_rounds reached: %s (cap=%s)", st.get("total_rounds"), max_rounds)
            return True
        if cont_cap and st.get("judge_continue_count", 0) >= cont_cap:
            logger.info("[judge] continue cap reached: %s (cap=%s)", st.get("judge_continue_count"), cont_cap)
            return True
        return False

    def _node_labels(self) -> Dict[str, str]:
        defaults = {"A": "debater-A", "B": "debater-B", "judge": "judge-llm"}
        cfg = (self.settings or {}).get("node_labels") or {}
        return {**defaults, **cfg}

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

            # Parse upstream judge output
            output = json.loads(output_json or '{}')
            logger.debug("[judge] input_payload=%s", _snippet(output))

            node_to_block_map = (self.settings or {}).get("assignment_info", {})
            labels = self._node_labels()

            debate_key = self._derive_debate_key(output)
            st = self._get_state(debate_key)
            logger.debug("[judge] state_pre=%s", _snippet(st))

            judge_text = output.get("judge_text") or output.get("reply") or ""
            topic = output.get("topic")
            opponent_last = output.get("opponent_last") or ""
            router_meta = output.get("router_meta") if isinstance(output.get("router_meta"), dict) else {}

            # Merge per-role counts if provided by debater router via judge block
            try:
                rc = router_meta.get("router_counts") if isinstance(router_meta, dict) else None
                if isinstance(rc, dict):
                    for k in ("A", "B"):
                        if k in rc:
                            try:
                                v = int(rc.get(k) or 0)
                            except Exception:
                                try:
                                    v = int(float(rc.get(k) or 0))
                                except Exception:
                                    v = 0
                            prev = int((st.get("role_counts", {}) or {}).get(k, 0))
                            if v > prev:
                                st.setdefault("role_counts", {"A": 0, "B": 0})
                                st["role_counts"][k] = v
                    combined = int(st.get("role_counts", {}).get("A", 0)) + int(st.get("role_counts", {}).get("B", 0))
                else:
                    combined = int(st.get("role_counts", {}).get("A", 0)) + int(st.get("role_counts", {}).get("B", 0))
            except Exception:
                logger.exception("[judge] failed to merge router_counts")
                combined = int(st.get("role_counts", {}).get("A", 0)) + int(st.get("role_counts", {}).get("B", 0))

            # prev_role seen by judge is the role that spoke last before escalation
            incoming_prev_role = output.get("prev_role") or "judge"
            mode = str((self.settings or {}).get("judge_prev_role_mode", "incoming")).strip().lower()
            if mode == "fixed_judge":
                outgoing_prev_role = "judge"
            else:
                outgoing_prev_role = incoming_prev_role

            # Update counters: use bump_round and also respect counts observed from debater router
            prev_total = int(st.get("total_rounds", 0) or 0)
            bump = 1 if output.get("bump_round", False) else 0
            st["total_rounds"] = max(prev_total + bump, combined)
            if combined and st["total_rounds"] == combined and combined != prev_total:
                logger.info("[judge] total_rounds synced from router_counts: %s (prev=%s, bump=%s)", st["total_rounds"], prev_total, bump)

            force_finalize = self._apply_caps(st)
            decision = self._parse_decision(judge_text)
            logger.info("[judge] decision=%s force_finalize=%s prev_role_mode=%s incoming_prev_role=%s outgoing_prev_role=%s role_counts=%s total_rounds=%s", decision, force_finalize, mode, incoming_prev_role, outgoing_prev_role, st.get("role_counts"), st.get("total_rounds"))

            gt = GraphTools(output_ptr_str)

            # Helper to determine cap reason
            def _cap_reason() -> str:
                try:
                    max_rounds = int((self.settings or {}).get("max_rounds", 20) or 20)
                    cont_cap = int((self.settings or {}).get("judge_continue_cap", 5) or 5)
                except Exception:
                    max_rounds, cont_cap = 10, 2
                if st.get("total_rounds", 0) >= max_rounds:
                    return "max_rounds_cap"
                if st.get("judge_continue_count", 0) >= cont_cap:
                    return "judge_continue_cap"
                return "cap_reached"

            # Route logic with forced-finalization handshake to judge
            if decision.get("type") == "FINAL_JUDGMENT":
                updated_output_ptr = gt.finalize(output_ptr_str)
                logger.info("[judge] finalized outputs (judge decided)")
            elif force_finalize:
                # If caps hit but judge didn't conclude, send one forced-finalization prompt to the judge.
                if not st.get("force_finalize_requested"):
                    reason = _cap_reason()
                    # Merge router_meta safely and add flags
                    new_meta = {}
                    try:
                        if isinstance(router_meta, dict):
                            new_meta.update(router_meta)
                    except Exception:
                        pass
                    new_meta["force_finalize"] = True
                    new_meta["force_termination_reason"] = reason
                    # Carry forward observed role counts for judge context (optional)
                    try:
                        rc = st.get("role_counts") or {}
                        if isinstance(rc, dict):
                            new_meta["router_counts"] = rc
                    except Exception:
                        pass

                    payload = {"topic": topic, "router_meta": new_meta}
                    packet.data = json.dumps(payload)
                    updated_output_ptr = gt.set_destination_nodes([labels.get("judge", "judge-llm")], node_to_block_map)
                    st["force_finalize_requested"] = True
                    logger.info("[judge] force-finalize handshake sent to judge (reason=%s) payload_keys=%s", reason, list(payload.keys()))
                else:
                    # Already requested once; finalize regardless to avoid loops
                    updated_output_ptr = gt.finalize(output_ptr_str)
                    logger.info("[judge] finalized outputs after prior force-finalize request")
            else:
                # Continue routing to debater A/B
                st["judge_continue_count"] = st.get("judge_continue_count", 0) + 1
                target_role = decision.get("role")
                target_label = labels.get(target_role, f"debater-{target_role}")

                # Author-consistent selection of previous turn text
                def _last_from_meta(meta: Dict[str, Any], role: str) -> str:
                    try:
                        turns = (meta or {}).get("recent_turns")
                        if isinstance(turns, list):
                            for t in reversed(turns):
                                try:
                                    if str((t.get("role") or "")).upper() == role:
                                        return str(t.get("reply") or "")
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    return ""

                opp_role = "B" if target_role == "A" else "A"
                opp_reply = opponent_last or _last_from_meta(router_meta or {}, opp_role)
                self_reply = _last_from_meta(router_meta or {}, target_role)

                if opp_reply:
                    prev_text = opp_reply
                    prev_author = opp_role
                    branch = "opponent"
                elif self_reply:
                    prev_text = self_reply
                    prev_author = target_role
                    branch = "self_fallback"
                else:
                    prev_text = ""
                    prev_author = target_role
                    branch = "empty_fallback"

                # Canonical payload to the receiver (no legacy keys, no suffix flipping)
                try:
                    incoming_sid = output.get("session_id")
                    if not incoming_sid and hasattr(packet, "session_id"):
                        incoming_sid = getattr(packet, "session_id", None)
                except Exception:
                    incoming_sid = None

                payload = {
                    "prev_turn_text": prev_text,
                    "prev_turn_role": prev_author,
                    "receiver_role": target_role,
                    "topic": topic,
                }
                if incoming_sid:
                    payload["session_id"] = incoming_sid

                packet.data = json.dumps(payload)
                updated_output_ptr = gt.set_destination_nodes([target_label], node_to_block_map)
                logger.info("[judge] routed_to=%s branch=%s payload=%s", target_role, branch, _snippet(payload))

            # Persist state
            self._save_state(debate_key, st)

            # Update packet and write back to input_data
            packet.output_ptr = updated_output_ptr
            input_data['packet'] = packet

            dt = (time.monotonic() - t0) * 1000.0
            logger.debug("[Policy:eval] done in %.2f ms", dt)
            return input_data

        except Exception as e:
            logger.exception("[Policy:eval] Exception during policy evaluation")
            raise e
