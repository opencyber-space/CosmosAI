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

        # Model config
        self.api_base = self.context.block_init_data['initContainer']['inference_url']
        self.model_name = self.context.block_init_data['model']

        self.blocks_system_message = init_settings.get("system_message", "You are a helpful assistant")

        self.generation_config = init_settings.get("generation_config", {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 512,
                        "stream": False
                    })
        logger.info(f"[__init__] self.generation_config {self.generation_config}")

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

                generation_config = input_data.get(
                        "generation_config", self.generation_config
                    )
                extra_body = {}
                removal_keys = []
                for k, v in generation_config.items():
                    if k in ["top_k"]:
                        extra_body[k] = v
                        removal_keys.append(k)

                for k in removal_keys:
                    del generation_config[k]

                payload = {
                    "model": self.model_name,
                    "messages": self.chat_sessions[session_id],
                    "extra_body": extra_body,
                    **generation_config

                }
                logger.info(f"[LLM Chat payload] {payload}")
                url = f"{self.api_base}/v1/chat/completions"

            else:
                # Completions mode
                prompt = self._build_prompt(session_id, message)

                generation_config = input_data.get(
                        "generation_config", self.generation_config
                    )
                extra_body = {}
                removal_keys = []
                for k, v in generation_config.items():
                    if k in ["top_k"]:
                        extra_body[k] = v
                        removal_keys.append(k)

                for k in removal_keys:
                    del generation_config[k]

                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    **generation_config
                }
                logger.info(f"[LLM completions payload] {payload}")
                url = f"{self.api_base}/v1/completions"

            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code != 200:
                logger.error(f"LLM API error: {response.text}")
                return False, response.text

            result = response.json()
            logger.info(f"[LLM Response] {result}")
            if mode == "chat":
                reply = result["choices"][0]["message"]["content"]
                self.chat_sessions[session_id].append({
                    "role": "assistant",
                    "content": reply
                })
            else:
                reply = result["choices"][0]["text"]
                # self.chat_sessions[session_id].append({
                #     "role": "user",
                #     "content": message
                # })
                self.chat_sessions[session_id].append({
                    "role": "assistant",
                    "content": reply
                })

            logger.info(f"[LLM Completion] {reply}")
            return True, OnDataResult(output={"message": reply})

        except Exception as e:
            logger.error(f"[Hello Chat Error] {e}")
            return False, str(e)

    def _build_prompt(self, session_id, user_message):
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []

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
