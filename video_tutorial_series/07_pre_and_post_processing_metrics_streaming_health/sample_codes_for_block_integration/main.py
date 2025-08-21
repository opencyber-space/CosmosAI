import json
import logging,os,sys,glob
import copy
from typing import Dict, Any, List

from aios_instance import PreProcessResult, OnDataResult, Block
from aios_llama_cpp import LLAMAUtils, LLMMetrics,LLMMetricsUpdated

from huggingface_hub import hf_hub_download,snapshot_download

logger = logging.getLogger(__name__)

def find_first_gguf_part(directory_path: str) -> str:
    """
    Finds the first part of a multi-part GGUF model in a directory.

    Args:
        directory_path: The path to the folder containing the .gguf files.

    Returns:
        The full path to the first part of the GGUF model, or an error message.
    """
    # Check if the provided path is a valid directory
    if not os.path.isdir(directory_path):
        return f"Error: Directory not found at '{directory_path}'"

    # Search for the file ending in '-00001-of-' and '.gguf'
    for filename in os.listdir(directory_path):
        if "-00001-of-" in filename and filename.endswith(".gguf"):
            # If found, return the full, absolute path
            return os.path.join(directory_path, filename)

    return f"Error: Could not find a GGUF file matching the pattern '...-00001-of-....gguf' in '{directory_path}'"


class LlamaCppChatBlock:
    """A feature‑rich chat/completion block around **aios‑llama‑cpp**.

    Added capabilities vs. v1:
      • support for LLMMetrics hooks
      • runtime generation parameter overrides (temperature, max_tokens, top_p, stop, seed…)
      • multiple‑sequence sampling via ``generate_text``
      • expose ``tokenize`` / ``detokenize`` / model info / save_model through ``management``
      • richer health‑check payload
    """

    # --------------------------------------------------------------------- #
    #                               LIFECYCLE                               #
    # --------------------------------------------------------------------- #
    def __init__(self, context):
        self.context = context
        self.chat_sessions: Dict[str, bool] = {}
        self.model_path = context.common_path
        init_data = context.block_init_data or {}
        init_params = context.block_init_parameters or {}
        init_settings = context.block_init_settings or {}

        # --------------------- model / device configuration ----------------
        self.model_name: str = init_data.get("model_name")
        if not self.model_name:
            raise ValueError("Missing 'model_name' in blockInitData")

        model_config = init_settings.get("model_config", {})

        self.blocks_system_message = init_data.get("system_message", "You are a helpful assistant.")

        self.use_gpu: bool = init_settings.get("use_gpu", True)
        self.gpu_id: int = init_settings.get("gpu_id", 0)

        # -------------------------- metrics hooks --------------------------
        enable_metrics = init_settings.get("enable_metrics", True)
        # self.metrics = LLMMetrics(self.context.metrics) if enable_metrics and self.context.metrics else None
        self.metrics = LLMMetricsUpdated(self.context.metrics) if enable_metrics and self.context.metrics else None

        # --------------------- default generation config -------------------
        self.default_gen_args: Dict[str, Any] = {
            "max_tokens": init_params.get("max_tokens", 2048),
            "temperature": init_params.get("temperature", 0.6),
            "top_p": init_params.get("top_p", 0.9)
            }
            # "stop": init_params.get("stop", ["Q:", "\n"]),
        # Cleanup configuration
        self.cleanup_config = {
            "enabled": init_settings.get("cleanup_enabled", True),
            "check_interval": init_settings.get("cleanup_check_interval", 300),
            "session_timeout": init_settings.get("cleanup_session_timeout", 3600)
        }

        self.model_config = {
            "n_gpu_layers": -1,      # Offload all layers to GPU
            "n_ctx": 4096,           # Increased context size for better performance
            "verbose": True,        # Set to True for detailed llama.cpp logging
            #"n_batch": 512,          # Batch size for prompt processing
            # "chat_format": "llama-2" # Manually set chat format if needed
        }
        for key, value in model_config.items():
            self.model_config[key] = value

        self._download_models()

        # -------------------------- llama‑cpp init -------------------------
        
        #print(f"Local model path: {self.local_model_name}")
        self.llama = LLAMAUtils(
            model_path=self.local_model_name,
            use_gpu=self.use_gpu,
            gpu_id=self.gpu_id,
            metrics=self.metrics,
            model_config=copy.deepcopy(self.model_config),  # Use a copy to avoid modifying the original
            cleanup_config=copy.deepcopy(self.cleanup_config)  # Use a copy to avoid modifying the original
        )

        if not self.llama.load_model():
            raise RuntimeError(f"Failed to load model from {self.local_model_path}")

        self.chat_supported: bool = self.llama.supports_chat()
        logger.info(
            "[LlamaCppChatBlock] Model loaded · chat support=%s", self.chat_supported
        )

    def _download_models(self):
        #os.environ['HF_HOME'] = self.model_path
        if ".gguf" not in self.model_name:
            if self.model_name[-1]=='/':
                self.model_name = self.model_name[:-1]
            self.local_model_path = os.path.join(self.model_path, self.model_name)
            if not os.path.exists(self.local_model_path):
                namespace = self.model_name.split("/")[0]
                repo_name = self.model_name.split("/")[1]
                repo_id = f"{namespace}/{repo_name}"
                allow_patterns_1 = self.model_name.replace(repo_id + "/", "")
                allow_patterns_2 = allow_patterns_1 + "/*"
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=self.local_model_path.replace(allow_patterns_1,""),
                    allow_patterns=allow_patterns_2,  # This glob pattern matches everything in the BF16 folder
                    local_dir_use_symlinks=False # Recommended to download actual files
                )
            self.local_model_name = find_first_gguf_part(self.local_model_path)
        else: 
            self.local_model_path = os.path.join(self.model_path, os.path.dirname(self.model_name))
            if os.path.exists(self.local_model_path):
                # Look for common model files that indicate a valid model directory
                model_files = glob.glob(os.path.join(self.local_model_path, "*.gguf"))
                #print(model_files)
                has_model_files = False
                for k in model_files:
                    #print(f"Found model file: {k}")
                    if self.model_name.split("/")[-1] in k:
                        has_model_files = True
                        break
                    else:
                        has_model_files = False
                
                if not has_model_files:
                    print(f"Downloading model {self.model_name} to {self.local_model_path}...")
                    namespace = self.model_name.split("/")[0]
                    repo_name = self.model_name.split("/")[1]
                    repo_id = f"{namespace}/{repo_name}"
                    print(f"repo_id: {repo_id}")
                    filename = self.model_name.replace(os.path.join(namespace, repo_name)+"/", "")
                    print(f"filename: {filename}")
                    download_path = os.path.join(self.model_path, repo_id)
                    # This function downloads all files and returns the path to the local directory
                    hf_hub_download(
                        repo_id=repo_id,
                        filename=filename,
                        local_dir=download_path
                    )
            else:
                print(f"Path Doesn't Exist: Downloading model {self.model_name} to {self.local_model_path}...")
                # This function downloads all files and returns the path to the local directory
                namespace = self.model_name.split("/")[0]
                repo_name = self.model_name.split("/")[1]
                repo_id = f"{namespace}/{repo_name}"
                print(f"repo_id: {repo_id}")
                filename = self.model_name.replace(os.path.join(namespace, repo_name)+"/", "")
                print(f"filename: {filename}")
                download_path = os.path.join(self.model_path, repo_id)
                hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,  # Use the model name as the filename
                    local_dir=download_path
                )
            self.local_model_name = os.path.join(self.model_path, self.model_name)

    # --------------------------------------------------------------------- #
    #                               HELPERS                                 #
    # --------------------------------------------------------------------- #
    def _merge_gen_args(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        gen_args = copy.deepcopy(self.default_gen_args)
        if overrides:
            gen_args.update({k: v for k, v in overrides.items() if v is not None})
        print("final value is ",gen_args)
        return gen_args

    def _merge_cleanup_config(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        cleanup_args = copy.deepcopy(self.cleanup_config)
        if overrides:
            cleanup_args.update({k: v for k, v in overrides.items() if v is not None})
        print("final clean up value is ",cleanup_args)
        return cleanup_args

    # --------------------------------------------------------------------- #
    #                           BLOCK INTERFACES                            #
    # --------------------------------------------------------------------- #
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

    def on_data(self, preprocessed_entry, is_ws=False):
        """Handles both completion and multi‑turn chat."""
        try:
            input_data = preprocessed_entry.extra_data["input"]
            logger.info("input_data:", input_data)
            # --------------------------- CHAT PATH --------------------------
            if isinstance(input_data, dict) and "mode" in input_data:
                mode = input_data["mode"]
                if mode == "chat" and not self.chat_supported:
                    raise RuntimeError("Loaded model does not support chat")
                
                if mode == "chat":
                    message: str = input_data["message"]
                elif mode == "generate":
                    message: str = input_data.get("prompt", "")
                elif mode == "embed":
                    message: str = input_data.get("text", "")
                elif mode == "tokens":
                    message: str = input_data.get("prompt", "")
                else:
                    raise ValueError(f"Unknown mode '{mode}' in input data")
                session_id: str = input_data.get("session_id", "default")
                if session_id == "default":
                    session_id = preprocessed_entry.session_id
                gen_params: Dict[str, Any] = input_data.get("gen_params", {})

                if mode == "chat":
                    if session_id not in self.chat_sessions:
                        self.llama.create_chat_session(
                            session_id,
                            system_message=input_data.get(
                                "system_message", self.blocks_system_message
                            ),
                        )
                        self.chat_sessions[session_id] = True
                        print(f"Created new chat session: {session_id}")
                    if not self.llama.has_chat_session(session_id):
                        self.llama.create_chat_session(
                            session_id,
                            system_message=input_data.get(
                                "system_message", self.blocks_system_message
                            ),
                        )
                        self.chat_sessions[session_id] = True
                        print(f"Created new chat session: {session_id}")
                    #print(gen_params)
                    self.llama.add_message_to_chat(session_id, message)
                    # if not is_ws:
                    #     #for non-streaming chat response
                    #     reply = self.llama.run_chat_inference(
                    #         session_id, stream=False, context=None, **self._merge_gen_args(gen_params)
                    #     )
                    #     return True, OnDataResult(output={"reply": reply})
                    # else:
                    # streaming chat response
                    collected: List[str] = []
                    reply = self.llama.run_chat_inference(
                        session_id, stream=True, context=self.context, is_ws=True,**self._merge_gen_args(gen_params)
                    )
                    logger.info("[Preprocess] output data is %s", {"reply": reply})
                    return True, OnDataResult(output={"reply": reply})

            # ------------------------ COMPLETION PATH ----------------------
            # allow: raw string or dict with "prompt"
            if isinstance(input_data, dict):
                prompt = input_data.get("prompt", "")
                gen_params = input_data.get("gen_params", {})
                num_sequences = input_data.get("num_sequences", 1)
                stream = input_data.get("stream", False)
            else:
                prompt = str(input_data)
                gen_params = {}
                num_sequences = 1
                stream = False

            if num_sequences > 1:
                # multiple completions
                completions: List[str] = self.llama.generate_text(
                    prompt,
                    num_sequences=num_sequences,
                    **self._merge_gen_args(gen_params),
                )
                return True, OnDataResult(output={"reply": completions})

            # single completion (optionally streaming)
            if stream:
                # run_inference handles internal streaming; we collect into string
                collected: List[str] = []
                for chunk in self.llama.run_inference(
                    prompt, stream=False, **self._merge_gen_args(gen_params)
                ):
                    collected.append(chunk)
                return True, OnDataResult(output={"reply": "".join(collected)})

            result = self.llama.run_inference(
                prompt, **self._merge_gen_args(gen_params)
            )
            text = result["choices"][0]["text"].strip() if result else ""
            logger.info("[Preprocess] output data is %s", {"reply": text})
            return True, OnDataResult(output={"reply": text})

        except Exception as e:
            logger.error("[Llama‑CPP Inference Error] %s", e)
            return False, str(e)

    # ------------------------------------------------------------------ #
    #                         RUNTIME MANAGEMENT                         #
    # ------------------------------------------------------------------ #
    def on_update(self, updated_parameters):
        """Dynamically adjust default generation arguments."""
        try:
            self.default_gen_args = self._merge_gen_args(updated_parameters)
            return True, self.default_gen_args
        except Exception as e:
            logger.error("[Update Error] %s", e)
            return False, str(e)

    def health(self):
        """Health probe with extended metadata."""
        try:
            info = self.llama.get_model_info() or {}
        except Exception:
            info = {}
        return {
            "status": "healthy" if self.llama and self.llama.model_loaded else "unhealthy",
            "chat_supported": self.chat_supported,
            **info,
        }

    def management(self, action: str, data: Dict[str, Any]):
        """Management endpoints for orchestration layers."""
        try:
            if action == "reset":
                for sid in list(self.chat_sessions.keys()):
                    self.llama.remove_chat_session(sid)
                self.chat_sessions.clear()
                return {"message": "Chat sessions cleared"}

            if action == "info":
                return self.llama.get_model_info() or {}

            if action == "save":
                path = data.get("path")
                if not path:
                    return {"error": "'path' missing"}
                ok = self.llama.save_model(path)
                return {"saved": ok, "path": path}

            if action == "set_seed":
                seed = data.get("seed")
                if seed is None:
                    return {"error": "'seed' missing"}
                ok = self.llama.set_seed(seed)
                return {"seed_set": ok, "seed": seed}

            if action == "tokenize":
                text = data.get("text", "")
                return {"tokens": self.llama.tokenize(text)}

            if action == "detokenize":
                tokens = data.get("tokens", [])
                return {"text": self.llama.detokenize(tokens)}

            if action == "update_cleanup_config":
                cleanup_config = data.get("cleanup_config", {})
                self.cleanup_config = self._merge_cleanup_config(cleanup_config)
                self.llama.update_cleanup_config(**self.cleanup_config)
                return {"message": "Cleanup config updated"}

            return {"error": f"Unknown action '{action}'"}
        except Exception as e:
            return {"error": str(e)}

    def get_muxer(self):
        return None


# --------------------------------------------------------------------------- #
#                                ENTRY‑POINT                                 #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    block = Block(LlamaCppChatBlock)
    block.run()
