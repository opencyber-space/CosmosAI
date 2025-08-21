import logging

class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters

        # This is NOT a timestamp, it's seconds since last metric
        self.allowed_metrics_age = parameters.get("allowed_metrics_age", 30)
        self.forced_health_status = {}  # {block_id: True/False}
        self.last_healthy = False

        logging.warning(f"[INIT] HealthCheckerPolicy initialized with allowed_metrics_age={self.allowed_metrics_age}")

    def eval(self, parameters, input_data, context):
        logging.warning("[EVAL] eval() called with input_data keys: %s", list(input_data.keys()))

        # if input_data['mode'] != "default": #fast_check
        #     return {"overall_healthy": self.last_healthy}

        health_data = input_data.get("health_check_data", {})
        if not health_data:
            logging.warning("[EVAL] No health_check_data found in input.")
            return {
                "blocks": {},
                "overall_healthy": False
            }

        result = {"blocks": {}, "overall_healthy": True}

        for block_id, data in health_data.items():
            logging.warning("[EVAL] Processing block_id: %s", block_id)

            if block_id in self.forced_health_status:
                is_healthy = self.forced_health_status[block_id]
                reason = "forced_override"
                logging.warning("[EVAL] Forced status for %s: %s", block_id, is_healthy)
            else:
                instances = data.get("instances", [])
                healthy_instances = []

                for inst in instances:
                    if inst.get("healthy") is not True:
                        continue

                    last_metrics_age = inst.get("lastMetrics")
                    if last_metrics_age is None:
                        logging.warning("[EVAL] Skipping instance without lastMetrics: %s", inst.get("instanceId"))
                        continue

                    if last_metrics_age <= self.allowed_metrics_age:
                        healthy_instances.append(inst)
                    else:
                        logging.warning(
                            "[EVAL] instance %s too old: lastMetrics=%s > allowed=%s",
                            inst.get("instanceId"), last_metrics_age, self.allowed_metrics_age
                        )

                is_healthy = len(healthy_instances) > 0
                reason = f"{len(healthy_instances)} healthy (age ≤ {self.allowed_metrics_age}s)"

            result["blocks"][block_id] = {
                "healthy": is_healthy,
                "reason": reason
            }

            if not is_healthy:
                result["overall_healthy"] = False
                self.last_healthy = False
            else:
                self.last_healthy = True

        logging.warning("[EVAL] Final health check result: %s", result)
        return result

    def management(self, action: str, data: dict) -> dict:
        logging.warning(f"[MGMT] management() called with action={action}, data={data}")
        try:
            action = action.lower()

            if action == "get_forced_status":
                return {"status": "ok", "value": self.forced_health_status}

            elif action == "force_healthy":
                block_id = data["block_id"]
                self.forced_health_status[block_id] = True
                return {"status": "ok", "message": f"Block {block_id} forced to healthy"}

            elif action == "force_unhealthy":
                block_id = data["block_id"]
                self.forced_health_status[block_id] = False
                return {"status": "ok", "message": f"Block {block_id} forced to unhealthy"}

            elif action == "clear_forced":
                block_id = data["block_id"]
                self.forced_health_status.pop(block_id, None)
                return {"status": "ok", "message": f"Forced status cleared for {block_id}"}

            elif action == "clear_all_forced":
                self.forced_health_status.clear()
                return {"status": "ok", "message": "All forced statuses cleared"}

            elif action == "set_allowed_metrics_age":
                self.allowed_metrics_age = int(data["value"])
                return {"status": "ok", "message": f"allowed_metrics_age set to {self.allowed_metrics_age}"}

            else:
                return {"status": "error", "message": f"Unknown action '{action}'"}

        except Exception as e:
            logging.error(f"[MGMT] Error handling management action: {e}")
            return {"status": "error", "message": str(e)}
