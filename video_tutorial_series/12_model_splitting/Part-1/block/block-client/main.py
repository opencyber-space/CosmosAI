import json
import logging
import os
import requests
from aios_instance import PreProcessResult, OnDataResult, Block, Context

logger = logging.getLogger(__name__)


class HelloChatBlock:
    def __init__(self, context: Context):
        self.context = context
        self.chat_sessions = {}  # session_id -> List[{"role": ..., "content": ...}]

        init_data = context.block_init_data or {}
        init_params = context.block_init_parameters or {}
        init_settings = context.block_init_settings or {}

        self.blocks_system_message = init_settings.get("system_message", "You are an helpful assistant")
        

        self.model_split_id = init_data.get("model_split_id", "")
        if not self.model_split_id:
            raise Exception("model_split_id is expected")

        self.api = f"http://{self.model_split_id}-rank-master.splits.svc.cluster.local:8080"


    # def on_preprocess(self, packet):
    #     try:
    #         data = packet.data
    #         if isinstance(data, str):
    #             data = json.loads(data)

    #         if "inputs" in data:
    #             results = [
    #                 PreProcessResult(packet=packet, extra_data={"input": item})
    #                 for item in data["inputs"]
    #             ]
    #             return True, results
    #         else:
    #             return True, [
    #                 PreProcessResult(packet=packet, extra_data={"input": data}, session_id=packet.session_id)
    #             ]
    #     except Exception as e:
    #         logger.error(f"[Preprocess Error] {e}")
    #         return False, str(e)

    def on_preprocess(self, packet):
        """Normalises input into a list of ``PreProcessResult`` objects.

        Accepted formats:
          ① raw string → completion
          ② {"inputs": [...]} → batch of ①/③
          ③ {"message": "...", "session_id": "chatX", "gen_params": {...}}
        """
        try:
            data = packet.data
            logger.info("on_preprocess data: %s", data)
            if isinstance(data, str):
                try:
                    data = json.loads(data)  # maybe JSON string
                except Exception:
                    # plain prompt string
                    data = data
            logger.info("[Preprocess] input data is %s", data)


            if isinstance(data, dict) and "inputs" in data:
                for item in data["inputs"]:
                    if "messages" in item and type(item["messages"]) is dict and "reply" in item["messages"]:
                        item["messages"] = item["messages"]["reply"]
                    elif "message" in item and type(item["message"]) is dict and "reply" in item["message"]:
                        item["message"] = item["message"]["reply"]
                    elif "reply" in item:
                        item["message"] = item["reply"]
                        del item["reply"]
                logger.info("item data: %s", item)
                results = [
                    PreProcessResult(packet=packet, extra_data={"input": item}, session_id=packet.session_id)
                    for item in data["inputs"]
                ]
                return True, results
            elif isinstance(data, dict) and "reply" in data:
                # single completion input with "reply" key
                data["message"] = data["reply"]
                data["mode"] = "chat"
                del data["reply"]
                return True, [PreProcessResult(packet=packet, extra_data={"input": data}, session_id=packet.session_id)]

            return True, [PreProcessResult(packet=packet, extra_data={"input": data}, session_id=packet.session_id)]
        except Exception as e:
            logger.error("[Preprocess Error] %s", e)
            return False, str(e)

    def on_data(self, preprocessed_entry, is_ws):
        try:
            session_id = preprocessed_entry.session_id
            input_data = preprocessed_entry.extra_data["input"]

            # Required fields
            message = input_data.get("message", "").strip()
            mode = input_data.get("mode", "chat").strip().lower()

            logger.info("[on_data] message %s", message)
            logger.info("[on_data] mode %s", mode)

            generation_config = input_data.get("generation_config", {
                "max_new_tokens": 2048,
                "do_sample": True,
                "top_k": 50,
                "top_p": 0.95,
                "temperature": 1.0
            })

            if not message:
                return True, OnDataResult(output={"message": "Empty input"})
            if mode not in {"chat", "completions"}:
                return False, f"Invalid mode: {mode}. Expected 'chat' or 'completions'."

            headers = {
                "Content-Type": "application/json"
            }

            if mode == "chat":
                # Chat mode
                if session_id not in self.chat_sessions:
                    system_message=input_data.get(
                        "system_message", self.blocks_system_message
                    )
                    self.chat_sessions[session_id] = [{
                        "role": "system",
                        "content": system_message
                    }]
                    

                self.chat_sessions[session_id].append({
                    "role": "user",
                    "content": message
                })

                payload = {
                    "messages": self.chat_sessions[session_id],
                    "enable_streaming": False,
                    "generation_config": generation_config
                }
                url = f"{self.api}/v1/chat/"

            else:
                # Generate mode
                #prompt = self._build_prompt(session_id, message)
                prompt = message
                payload = {
                    "prompt": prompt,
                    "temperature": generation_config.get("temperature", 1.0),
                    "max_new_tokens": generation_config.get("max_new_tokens", 512),
                    "do_sample": generation_config.get("do_sample", False),
                    "top_k": generation_config.get("top_k", 50),
                    "top_p": generation_config.get("top_p", 0.95)
                }
                #"enable_streaming": generation_config.get("stream", False),
                url = f"{self.api}/generate"
            logger.info("[on_data] going for requests.post %s", url)
            logger.info("[on_data] with payload %s", payload)
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code != 200:
                logger.error(f"LLM API error: {response.text}")
                return False, response.text

            result = response.json()
            logger.info(f"[result json] {result}")
            if mode == "chat":
                #reply = result["choices"][0]["message"]["content"]
                self.chat_sessions[session_id].append({
                    "role": "assistant",
                    "content": reply
                })
                logger.info(f"[LLM Completion] {reply}")
                return True, OnDataResult(output={"message": reply})
            else:
                output = result["output"]
                logger.info(f"[LLM Completion] {output}")
                return True, OnDataResult(output={"generated": output})

        except Exception as e:
            logger.error(f"[Hello Chat Error] {e}")
            return False, str(e)

    def _build_prompt(self, session_id, user_message):
        if session_id not in self.chat_sessions:
            system_message=input_data.get(
                "system_message", self.blocks_system_message
            )
            self.chat_sessions[session_id] = [{
                "role": "system",
                "content": system_message
            }]

        self.chat_sessions[session_id].append({
            "role": "user",
            "content": user_message
        })

        # Simple prompt builder
        prompt_parts = []
        for msg in self.chat_sessions[session_id]:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "system":
                prompt_parts.append(f"System: {content}")
        return "\n".join(prompt_parts) + "\nAssistant:"

    def on_update(self, updated_parameters):
        return True, updated_parameters

    def health(self):
        return {"status": "healthy"}

    def management(self, action, data):
        if action == "reset":
            self.chat_sessions.clear()
            return {"message": "All sessions cleared"}
        return {"message": f"Unknown action: {action}"}

    def get_muxer(self):
        return None


if __name__ == "__main__":
    block = Block(HelloChatBlock)
    block.run()
