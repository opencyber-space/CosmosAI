import json
import hashlib
import time
import redis
from urllib.parse import urlparse


class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
       
        # Parse Redis connection URL
        redis_url = parameters["db_url"]
        parsed = urlparse(redis_url)

        self.redis_client = redis.Redis(
            host=parsed.hostname,
            port=parsed.port or 6379,
            db=int(parsed.path.lstrip("/")) if parsed.path else 0,
            decode_responses=True  # Store values as strings
        )

    def eval(self, parameters, input_data, context):
        try:
            request_packet = input_data["input_data"]["request"]
            response_packet = input_data["input_data"]["response"]

            # Extract JSON data fields
            request_json = json.loads(request_packet.data)
            response_json = json.loads(response_packet.data)

            # Create audit record
            record = {
                "timestamp": time.time(),
                "session_id": request_packet.session_id,
                "seq_no": request_packet.seq_no,
                "request": request_json,
                "response": response_json
            }

            # Generate Redis key
            key = f"audit:{record['session_id']}:{record['seq_no']}"

            # Save to Redis
            self.redis_client.set(key, json.dumps(record))

        except Exception as e:
            context["last_error"] = str(e)

        return {}

    def management(self, action: str, data: dict) -> dict:
        try:
            if action == "get":
                session_id = data.get("session_id")
                seq_no = data.get("seq_no")
                if not session_id or seq_no is None:
                    return {"status": "error", "message": "Missing session_id or seq_no"}

                key = f"audit:{session_id}:{seq_no}"
                val = self.redis_client.get(key)
                return {"status": "ok", "value": json.loads(val) if val else None}

            elif action == "get_latest":
                session_id = data.get("session_id")
                if not session_id:
                    return {"status": "error", "message": "Missing session_id"}

                pattern = f"audit:{session_id}:*"
                keys = self.redis_client.keys(pattern)

                if not keys:
                    return {"status": "ok", "value": None}

                # Parse seq_nos from keys
                def extract_seq(key):
                    try:
                        return int(key.split(":")[-1])
                    except ValueError:
                        return -1

                latest_key = max(keys, key=extract_seq)
                val = self.redis_client.get(latest_key)
                return {"status": "ok", "key": latest_key, "value": json.loads(val) if val else None}

            elif action == "list_keys":
                pattern = data.get("pattern", "audit:*")
                keys = self.redis_client.keys(pattern)
                return {"status": "ok", "keys": keys}

            elif action == "delete":
                session_id = data.get("session_id")
                seq_no = data.get("seq_no")
                if not session_id or seq_no is None:
                    return {"status": "error", "message": "Missing session_id or seq_no"}

                key = f"audit:{session_id}:{seq_no}"
                deleted = self.redis_client.delete(key)
                return {"status": "ok", "deleted": deleted}

            return {"status": "error", "message": f"Unsupported action '{action}'"}

        except Exception as e:
            return {"status": "error", "message": str(e)}
