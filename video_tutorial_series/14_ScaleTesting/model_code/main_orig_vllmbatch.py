import json
import logging,os,sys,glob
import copy,time
from typing import Dict, Any, List

import multiprocessing as mp
mp.set_start_method("spawn", force=True)

from aios_instance import PreProcessResult, OnDataResult, Block
from aios_llama_cpp import vLLMUtils, LLMMetrics,LLMMetricsUpdated
from batcher import Batcher

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
        elif filename.endswith(".safetensors"):
            #May be a single file model in safetensors format which is Huugging Face model
            return directory_path

    return f"Error: Could not find a GGUF file matching the pattern '...-00001-of-....gguf' in '{directory_path}'"




def fp8Support():
    import torch
    try:
        prop = torch.cuda.get_device_properties(0)
        sm = prop.major * 10 + prop.minor  # e.g. 80 = A100, 89 = L4, 90 = H100
        name = prop.name.lower()

        # Known FP8-capable architectures (expand if needed later)
        fp8_arches = {
            89: ["l4", "l40", "l40s"],   # Ada Lovelace GPUs
            90: ["h100"],        # Hopper GPUs
        }

        fp8_supported = False
        if sm in fp8_arches:
            for tag in fp8_arches[sm]:
                if tag in name:
                    fp8_supported = True
                    break

        kv_cache_dtype = "fp8" if fp8_supported else "bf16"
        print(f"Using kv_cache_dtype={kv_cache_dtype} on {prop.name} (SM {sm})")
        return fp8_supported

    except Exception as e:
        print(f"Could not detect GPU FP8 support: {e}")
        return False


class vLLMChatBlock:
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
            "max_tokens": init_params.get("max_tokens", 512),
            "presence_penalty": init_params.get("presence_penalty", 1.0),
            "repetition_penalty": init_params.get("repetition_penalty", 1.0),
            "temperature": init_params.get("temperature", 1.0),
            "top_p": init_params.get("top_p", 0.9),
            "top_k": init_params.get("top_k", 40),
            "min_p": init_params.get("min_p", 0.5),
            "seed": init_params.get("seed", 1234)
            }

        # "stop": init_params.get("stop", ["Q:", "\n"]),
        # Cleanup configuration
        self.cleanup_config = {
            "enabled": init_settings.get("cleanup_enabled", True),
            "check_interval": init_settings.get("cleanup_check_interval", 300),
            "session_timeout": init_settings.get("cleanup_session_timeout", 3600)
        }

        if "hf_token" in init_settings:
            self.hf_token = init_settings["hf_token"]
            # Set the environment variables
            os.environ["HUGGING_FACE_HUB_TOKEN"] = self.hf_token
            os.environ["HF_TOKEN"] = self.hf_token

        self.batcher = Batcher(4)

        self.model_config = {
            "tensor_parallel_size": 1,
            "max_model_len": 512,
            "max_num_seqs": 4,            # keep low to avoid OOM, Batch Size
            "enable_prefix_caching": True,
            #"kv_cache_dtype": "fp8",
            "dtype": "bfloat16"   #"gpu_memory_utilization": 0.8,
        }
        
        #self.model_config["show_hidden_metrics_for_version"] = "v0"
        for key, value in model_config.items():
            self.model_config[key] = value

        

        self._download_models()

        # -------------------------- llama‑cpp init -------------------------
        #print(f"Local model path: {self.local_model_name}")
        self.vllmUtil = vLLMUtils(
            model_path=self.local_model_name,
            use_gpu=self.use_gpu,
            gpu_id=self.gpu_id,
            metrics=self.metrics,
            model_config=copy.deepcopy(self.model_config),  # Use a copy to avoid modifying the original
            cleanup_config=copy.deepcopy(self.cleanup_config)  # Use a copy to avoid modifying the original
        )

        self.vllmUtil.load_model()

        while True:
            print("calling self.health()")
            health_status = self.health()
            print(f"health status: {health_status}")
            if health_status.get("status") == "healthy":
                break
            time.sleep(2)
            #if not self.vllmUtil.load_model():
            #    raise RuntimeError(f"Failed to load model from {self.local_model_path}")

        self.chat_supported: bool = self.vllmUtil.supports_chat()
        logger.info(
            "[vLLMChatBlock] Model loaded · chat support=%s", self.chat_supported
        )

    def _download_models(self):
        #os.environ['HF_HOME'] = self.model_path
        if ".gguf" not in self.model_name:
            if self.model_name[-1]=='/':
                self.model_name = self.model_name[:-1]
            self.local_model_path = os.path.join(self.model_path, self.model_name)
            print("11:",self.local_model_path)
            if not os.path.exists(self.local_model_path):
                print("12:",self.local_model_path)
                namespace = self.model_name.split("/")[0]
                repo_name = self.model_name.split("/")[1]
                repo_id = f"{namespace}/{repo_name}"
                allow_patterns_1 = self.model_name.replace(repo_id + "/", "")
                allow_patterns_2 = allow_patterns_1 + "/*"
                print(f"repo_id: {repo_id}")
                print(f"local_dir: {self.local_model_path.replace(allow_patterns_1,'')}")
                print(f"allow_patterns_2: {allow_patterns_2}")
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=self.local_model_path.replace(allow_patterns_1,""),
                    allow_patterns=allow_patterns_2,  # This glob pattern matches everything in the BF16 folder
                    local_dir_use_symlinks=False # Recommended to download actual files
                )
            self.local_model_name = find_first_gguf_part(self.local_model_path)
            print("13:",self.local_model_name)
            if "Error:" in self.local_model_name:
                print(f"Downloading model 14 {self.model_name} to {self.local_model_path}...")
                namespace = self.model_name.split("/")[0]
                repo_name = self.model_name.split("/")[1]
                repo_id = f"{namespace}/{repo_name}"
                print(f"repo_id: {repo_id}")
                filename = self.model_name.replace(os.path.join(namespace, repo_name)+"/", "")
                print(f"filename: {filename}")
                download_path = os.path.join(self.model_path, repo_id)
                # This function downloads all files and returns the path to the local directory
                download_path_ = snapshot_download(
                    repo_id=self.model_name,
                    local_dir=download_path,
                    local_dir_use_symlinks=False
                )
                self.local_model_name = download_path
            print("13:",self.local_model_name)
            #raise RuntimeError(f"Failed to find GGUF model part in {self.local_model_path}: {self.local_model_name}")
        else: 
            self.local_model_path = os.path.join(self.model_path, os.path.dirname(self.model_name))
            print("1:",self.local_model_path)
            if os.path.exists(self.local_model_path):
                print("2:",self.local_model_path)
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
        #print("final value is ",gen_args)
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
            prompts = []
            session_ids = []
            generation_args = []
            all_modes_of_batch = []

            batch = self.batcher.add_to_batch({"packet": packet})
            if batch:
                # Process the full batch
                for oneItemInBatch in batch:
                    packet = oneItemInBatch["packet"]
                    data = packet.data
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)  # maybe JSON string
                        except Exception:
                            # plain prompt string
                            data = data
                    #logger.info("[Preprocess] input data is %s", data)


                    if isinstance(data, dict) and "inputs" in data:
                        for item in data["inputs"]:
                            if "messages" in item and type(item["messages"]) is dict and "reply" in item["messages"]:
                                item["messages"] = item["messages"]["reply"]
                            elif "message" in item and type(item["message"]) is dict and "reply" in item["message"]:
                                item["message"] = item["message"]["reply"]
                            elif "reply" in item:
                                item["message"] = item["reply"]
                                del item["reply"]
                        #logger.info("item data: %s", item)

                        if len(data["inputs"]) > 1:
                            #TODO: handle mux
                            #for item in data["inputs"]:
                            pass
                        else:
                            item = data["inputs"][0]
                            #print("item:",item)
                            if isinstance(item, dict):
                                if "messages" in item:
                                    #item["messages"] = item["messages"]["reply"]
                                    #TODO: handle messages of GEMMA which is MulitModal
                                    pass
                                else:
                                    message = ""
                                    mode = item["mode"]
                                    if mode == "chat" and not self.chat_supported:
                                        raise RuntimeError("Loaded model does not support chat")
                
                                    if mode == "chat":
                                        message: str = item["message"]
                                        raise ValueError(f"Unsupported mode '{mode}' in input data")
                                    elif mode == "generate":
                                        message: str = item.get("prompt", "hi")
                                    elif mode == "embed":
                                        message: str = item.get("text", "")
                                        raise ValueError(f"Unsupported mode '{mode}' in input data")
                                    elif mode == "tokens":
                                        message: str = item.get("prompt", "")
                                        raise ValueError(f"Unsupported mode '{mode}' in input data")
                                    else:
                                        raise ValueError(f"Unknown mode '{mode}' in input data")
                                    all_modes_of_batch.append(mode)
                                    session_id: str = item.get("session_id", "default")
                                    gen_params: Dict[str, Any] = item.get("gen_params", item.get("generation_config", {}))
                                    prompts.append(message)
                                    generation_args.append(self._merge_gen_args(gen_params))
                                    session_ids.append(session_id)
                                # results = [
                                #     PreProcessResult(packet=packet, extra_data={"input": item}, session_id=packet.session_id)
                                #     for item in data["inputs"]
                                # ]
                        #return True, results
                    elif isinstance(data, dict) and "reply" in data:
                        # single completion input with "reply" key
                        # TODO: handle this, mode will not be present in general
                        data["message"] = data["reply"]
                        data["mode"] = "chat"
                        del data["reply"]
                        #return True, [PreProcessResult(packet=packet, extra_data={"input": data}, session_id=packet.session_id)]
                    elif isinstance(data, dict):
                        message = ""
                        mode = data["mode"]
                        if mode == "chat" and not self.chat_supported:
                            raise RuntimeError("Loaded model does not support chat")
    
                        if mode == "chat":
                            message: str = data["message"]
                            raise ValueError(f"Unsupported mode '{mode}' in input data")
                        elif mode == "generate":
                            message: str = data.get("prompt", "hi")
                        elif mode == "embed":
                            message: str = data.get("text", "")
                            raise ValueError(f"Unsupported mode '{mode}' in input data")
                        elif mode == "tokens":
                            message: str = data.get("prompt", "")
                            raise ValueError(f"Unsupported mode '{mode}' in input data")
                        else:
                            raise ValueError(f"Unknown mode '{mode}' in input data")
                        all_modes_of_batch.append(mode)
                        session_id: str = packet.session_id
                        gen_params: Dict[str, Any] = data.get("gen_params", data.get("generation_config", {}))
                        prompts.append(message)
                        generation_args.append(self._merge_gen_args(gen_params))
                        session_ids.append(session_id)
                    #return True, [PreProcessResult(packet=packet, extra_data={"input": data}, session_id=packet.session_id)]
            else:
                # No output yet; waiting for batch to fill
                return True, None

            # Do batched inferences
            all_modes_of_batch = list(set(all_modes_of_batch))
            #print("all_modes_of_batch:",all_modes_of_batch)
            if len(all_modes_of_batch)>1:
                raise ValueError("Mixing multiple mode with other modes in the same batch is not supported")
            elif "generate" in all_modes_of_batch:
                results = self.vllmUtil.generate_text(prompts, generation_args)
                key = "generated"
                if results:
                    returnData = []
                    for i,session_id in enumerate(session_ids):
                        returnData.append(PreProcessResult(packet=batch[i]["packet"], extra_data={"input": {"mode":"generate","session_id":session_id,"gen_params":generation_args[i],"prompt":prompts[i],key:results[i]}}, session_id=session_id))
                    return True, returnData
                else:
                    returnData = []
                    for i,session_id in enumerate(session_ids):
                        returnData.append(PreProcessResult(packet=batch[i]["packet"], extra_data={"input": {"mode":"generate","session_id":session_id,"gen_params":generation_args[i],"prompt":prompts[i],key:""}}, session_id=session_id))
                    return True, returnData
            else:
                return False, "Only 'generate' mode is supported in batch currently"
        except Exception as e:
            logger.error("[Preprocess Error] %s", e)
            return False, str(e)

    def on_data(self, preprocessed_entry, is_ws):
        """Handles both completion and multi‑turn chat."""
        try:
            input_data = preprocessed_entry.extra_data["input"]
            logger.info("input_data:", input_data)
            mode = input_data.get("mode", "generate")
            session_id = input_data.get("session_id", "default")
            gen_params = input_data.get("gen_params", {})
            if mode == "generate":
                prompt = input_data.get("prompt", "")
                key = "generated"
                response_text = input_data.get(key, "")
                #logger.debug(f"[on_data] mode={mode}, session_id={session_id}, gen_args={gen_params}, prompt={prompt}, {key}={response_text}")
            return True, OnDataResult(output={key: response_text, "mode": mode})

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
            info = self.vllmUtil.get_model_info()
            if info:
                return {
                    "status": "healthy",
                }
            else:
                return {
                    "status": "unhealthy",
                }
        except Exception:
            return {
                "status": "unhealthy"
            }

    def management(self, action: str, data: Dict[str, Any]):
        """Management endpoints for orchestration layers."""
        try:
            if action == "reset":
                for sid in list(self.chat_sessions.keys()):
                    self.vllmUtil.remove_chat_session(sid)
                self.chat_sessions.clear()
                return {"message": "Chat sessions cleared"}

            if action == "info":
                return self.vllmUtil.get_model_info() or {}

            if action == "set_seed":
                seed = data.get("seed")
                if seed is None:
                    return {"error": "'seed' missing"}
                ok = self.vllmUtil.set_seed(seed)
                return {"seed_set": ok, "seed": seed}

            if action == "update_cleanup_config":
                cleanup_config = data.get("cleanup_config", {})
                self.cleanup_config = self._merge_cleanup_config(cleanup_config)
                self.vllmUtil.update_cleanup_config(**self.cleanup_config)
                return {"message": "Cleanup config updated"}

            return {"error": f"Unknown action '{action}'"}
        except Exception as e:
            return {"error": str(e)}

    def get_muxer(self):
        return None


# --------------------------------------------------------------------------- #
#                                ENTRY‑POINT                                 #
# --------------------------------------------------------------------------- #
# if __name__ == "__main__":
#     block = Block(vLLMChatBlock)
#     block.run()

def main():
    block = Block(vLLMChatBlock)
    block.run()

if __name__ == "__main__":
    import multiprocessing as mp
    mp.set_start_method("spawn", force=True)  # safer for vLLM
    main()