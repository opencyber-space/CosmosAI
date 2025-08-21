

class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
        self.default_limit = parameters.get("default_limit", 1000)
        self.session_limits = parameters.get("session_limits", {})
        self.whitelist = set(parameters.get("whitelist", []))

    def eval(self, parameters, input_data, context):
        quota_table = input_data["quota_table"]
        session_id = input_data["session_id"]
        quota = input_data["quota"]  # proposed quota (current + 1)

        # Whitelisted session_ids are always allowed
        if session_id in self.whitelist:
            return {"allowed": True}

        # Determine limit (session-specific or default)
        limit = self.session_limits.get(session_id, self.default_limit)

        # Reject if quota exceeds limit
        if quota > limit:
            return {"allowed": False}

        return {"allowed": True}

    def management(self, action: str, data: dict) -> dict:

        try:
            action = action.lower()
            qt = data.get("quota_table")
            sid = data.get("session_id")

            if action == "get_quota":
                return {"status": "ok", "value": qt.get(sid)}

            elif action == "reset_quota":
                qt.reset(sid)
                return {"status": "ok", "message": f"Quota reset for {sid}"}

            elif action == "set_quota":
                value = int(data.get("value", 0))
                qt.remove(sid)
                for _ in range(value):
                    qt.increment(sid)
                return {"status": "ok", "message": f"Quota set to {value} for {sid}"}

            elif action == "update_limit":
                limit = int(data.get("limit"))
                self.session_limits[sid] = limit
                return {"status": "ok", "message": f"Limit updated for {sid} to {limit}"}

            elif action == "update_default_limit":
                self.default_limit = int(data.get("limit"))
                return {"status": "ok", "message": f"Default limit updated to {self.default_limit}"}

            elif action == "add_whitelist":
                self.whitelist.add(sid)
                return {"status": "ok", "message": f"{sid} added to whitelist"}

            elif action == "remove_whitelist":
                self.whitelist.discard(sid)
                return {"status": "ok", "message": f"{sid} removed from whitelist"}

            elif action == "clear_all":
                qt.clean()
                return {"status": "ok", "message": "All quotas cleared"}

            else:
                return {"status": "error", "message": f"Unknown action '{action}'"}

        except Exception as e:
            return {"status": "error", "message": str(e)}
