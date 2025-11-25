#from llama_cpp import Llama
import logging
import time,os,sys,json,subprocess
import threading
import torch
#from vllm import LLM, SamplingParams

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_valid_tp(model_dir, num_gpus):
    cfg_path = os.path.join(model_dir, "config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)
    num_heads = cfg.get("num_attention_heads")
    logger.info(f"num_attention_heads from config.json: {num_heads}")
    if num_heads is None:
        raise ValueError("num_attention_heads not found in config.json")

    # Pick the largest divisor of num_heads that does not exceed num_gpus
    for tp in range(num_gpus, 0, -1):
        if num_heads % tp == 0:
            return tp   # return the first (largest) valid TP found

    return 1  # fallback, though this should always succeed

def get_best_fp8_dtype() -> str:
    """Selects the best FP8 dtype for the container environment.
    
    If multiple GPUs are present, chooses the lowest common denominator
    so that all GPUs can run consistently.
    """
    num_gpus = torch.cuda.device_count()
    if num_gpus == 0:
        return "auto"

    sm_to_dtype = {
        # Arch → Recommended dtype
        70: "auto",       # V100 (Volta, no FP8)
        75: "auto",       # T4 (Turing, no FP8)
        80: "auto", #"fp8_e4m3",   # A100 (Ampere, emulated FP8)
        86: "auto",       # A10, RTX 30xx (no FP8 tensor cores)
        89: "fp8_e4m3",   # Ada (L4, L40, RTX 4090)
        90: "fp8_e5m2",   # Hopper (H100, GH200)
    }

    # Collect recommended dtypes for all visible GPUs
    dtypes = []
    for i in range(num_gpus):
        sm_major, sm_minor = torch.cuda.get_device_capability(i)
        sm = sm_major * 10 + sm_minor
        dtypes.append(sm_to_dtype.get(sm, "auto"))

    # If all GPUs agree → return that
    if len(set(dtypes)) == 1:
        if dtypes[0] == "auto":
            os.environ["VLLM_USE_V1"] = "0"
            logger.info("⚡ Using VLLM_USE_V1=0 for auto dtype")
        return dtypes[0]

    if dtypes[0] == "auto":
            os.environ["VLLM_USE_V1"] = "0"
            logger.info("⚡ Using VLLM_USE_V1=0 for auto dtype")
    # Otherwise fallback to "auto" to avoid mismatched configs
    return "auto"

def estimate_kv_cache_bytes(model_config_path, max_seq_len, max_num_seqs, tp_size, dtype_size=1):
    with open(os.path.join(model_config_path, "config.json")) as f:
        cfg = json.load(f)
    num_layers = cfg["num_hidden_layers"]
    hidden_size = cfg["hidden_size"]

    kv_per_seq = 2 * num_layers * hidden_size * max_seq_len * dtype_size
    total_kv = kv_per_seq * max_num_seqs
    per_gpu = total_kv / tp_size
    return per_gpu

# --- Auto-detect GPUs and compute tensor_parallel_size and kv-cache memory ---
def _detect_num_gpus():
    # Try torch first (if available)
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.device_count()
    except Exception:
        pass

    # Fallback to environment variables
    for env_var in ('CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES'):
        env = os.environ.get(env_var)
        if env:
            ids = [x for x in env.split(',') if x.strip() != '']
            return max(1, len(ids))

    # Fallback to nvidia-smi
    try:
        out = subprocess.check_output([
            'nvidia-smi',
            '--query-gpu=index',
            '--format=csv,noheader'
        ], text=True, stderr=subprocess.DEVNULL)
        lines = [l for l in out.splitlines() if l.strip()]
        if lines:
            return len(lines)
    except Exception:
        pass

    # Last-resort: assume 1 GPU
    return 1

def _get_per_gpu_memory_bytes():
    # Try nvidia-smi to get total memory of first GPU
    try:
        out = subprocess.check_output([
            'nvidia-smi',
            '--query-gpu=memory.total',
            '--format=csv,noheader,nounits'
        ], text=True, stderr=subprocess.DEVNULL)
        vals = [int(x.strip()) for x in out.splitlines() if x.strip()]
        if vals:
            # return list of per-gpu totals in bytes
            return [v * 1024 * 1024 for v in vals]
    except Exception:
        pass
    # Fallback default to 24 GiB
    default = 24 * 1024 * 1024 * 1024
    return [default]

def _get_per_gpu_free_bytes():
    # Query free memory per GPU using nvidia-smi
    try:
        out = subprocess.check_output([
            'nvidia-smi',
            '--query-gpu=memory.free',
            '--format=csv,noheader,nounits'
        ], text=True, stderr=subprocess.DEVNULL)
        vals = [int(x.strip()) for x in out.splitlines() if x.strip()]
        if vals:
            return [v * 1024 * 1024 for v in vals]
    except Exception:
        pass
    return None

# Ensure tensor_parallel_size is the largest power of 2 <= num_gpus (minimum 1)
def largest_power_of_two(n):
    return 2 ** (n.bit_length() - 1) if n > 0 else 1

class vLLMUtils:
    def __init__(self, model_path, use_gpu=False, gpu_id=0, metrics=None, model_config={}, use_native_timings=True, cleanup_config=None):
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.gpu_id = gpu_id
        self.model = None
        self.metrics = metrics
        self.model_config = model_config
        self.chat_sessions = {}
        self.use_native_timings = use_native_timings  # Flag to use llama_cpp native performance data
        # Cleanup configuration
        self.cleanup_config = cleanup_config or {
            "enabled": True,
            "check_interval": 300,  # Check every 5 minutes (in seconds)
            "session_timeout": 3600  # Remove sessions inactive for 1 hour (in seconds)
        }
        logger.info(f"\033[93mCleanup configuration: {self.cleanup_config}\033[0m")

        # Thread control
        self.cleanup_thread = None
        self.cleanup_stop_event = threading.Event()

        if "max_num_seqs" not in self.model_config:
            self.model_config["max_num_seqs"] = 1

        max_num_batched_tokens = self.model_config.get("max_num_seqs",1) * self.model_config.get("max_model_len",256)
        self.model_config["max_num_batched_tokens"] = max_num_batched_tokens

        ###### TO Set KV Cache Memory if not set ######
        try:

            num_gpus = _detect_num_gpus()
            print(f"Detected num_gpus: {num_gpus}")
            self.model_config['tensor_parallel_size'] = largest_power_of_two(max(1, num_gpus))
            print(f"Set tensor_parallel_size to: {self.model_config['tensor_parallel_size']}")
            finalTP = get_valid_tp(self.model_path, num_gpus)
            self.model_config['tensor_parallel_size'] = finalTP
            print(f"Set tensor_parallel_size to after checking num_attention_heads: {self.model_config['tensor_parallel_size']}")

            DTYPE_SIZE_MAP = {
                "fp32": 4,
                "fp16": 2,
                "bf16": 2,
                "fp8": 1,
                "fp8_e4m3": 1,
                "fp8_e5m2": 1,
                "fp8_inc": 1,
                "auto": None,   # let vLLM decide, you’ll need to query after init
            }
            #any other fp8's will give cache_dtype = 1
            cache_dtype = DTYPE_SIZE_MAP.get(self.model_config.get("kv_cache_dtype", "fp8"), 1)
            #update kv_cache_memory_bytes if not asked by user explictly
            if "kv_cache_memory_bytes" not in self.model_config:
                if cache_dtype:
                    kvcache_bytes = estimate_kv_cache_bytes(
                            self.model_path,
                            max_seq_len=self.model_config["max_model_len"],
                            max_num_seqs=self.model_config["max_num_seqs"],
                            tp_size=self.model_config["tensor_parallel_size"],
                            dtype_size=cache_dtype,  
                        )
                    self.model_config["kv_cache_memory_bytes"] = kvcache_bytes
            
            self.kv_cache_dtype = get_best_fp8_dtype()
            logger.info(f"Using {self.kv_cache_dtype} kv_cache_dtype")
            self.model_config["kv_cache_dtype"] = self.kv_cache_dtype

        except Exception as e:
            logger.warning(f"Auto GPU/kv-cache detection failed: {e}. Falling back to configured values.")


        # Start cleanup thread if enabled
        if self.cleanup_config.get("enabled", True):
            self.start_cleanup_thread()

        self.model_state = {
            "loaded": False,
            "error": None
        }

    def start_cleanup_thread(self):
        """Start the background cleanup thread"""
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            self.cleanup_stop_event.clear()
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_worker,
                daemon=True,
                name="ChatSessionCleanup"
            )
            self.cleanup_thread.start()
            logger.info("Chat session cleanup thread started")

    def stop_cleanup_thread(self):
        """Stop the background cleanup thread"""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_stop_event.set()
            self.cleanup_thread.join(timeout=5)
            logger.info("Chat session cleanup thread stopped")

    def _cleanup_worker(self):
        """Background worker that periodically cleans up inactive sessions"""
        while not self.cleanup_stop_event.is_set():
            try:
                # Get current check_interval (allows dynamic updates)
                check_interval = self.cleanup_config.get("check_interval", 300)
                
                self._cleanup_inactive_sessions()
                
                # Wait for the next check interval or until stop event is set
                self.cleanup_stop_event.wait(check_interval)
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                # Continue running even if there's an error
                self.cleanup_stop_event.wait(30)  # Wait 30 seconds before retrying

    def _cleanup_inactive_sessions(self):
        """Clean up sessions that have been inactive for too long"""
        # Get current session_timeout (allows dynamic updates)
        session_timeout = self.cleanup_config.get("session_timeout", 3600)
        current_time = time.time()
        sessions_to_remove = []
        
        # Find sessions that need to be removed
        for session_id, session_data in self.chat_sessions.items():
            last_activity = session_data.get("timestamp_latest", 0)
            time_since_activity = current_time - last_activity
            
            if time_since_activity > session_timeout:
                sessions_to_remove.append((session_id, time_since_activity))
        
        # Remove inactive sessions
        for session_id, inactive_time in sessions_to_remove:
            try:
                logger.info(f"\033[93mRemoving inactive session: {session_id} (inactive for {inactive_time:.1f} seconds)\033[0m")
                self.remove_chat_session(session_id)
            except Exception as e:
                logger.error(f"Error removing session {session_id}: {e}")
    
        if sessions_to_remove:
            logger.info(f"\033[93mCleaned up {len(sessions_to_remove)} inactive sessions\033[0m")

    def update_cleanup_config(self, **config):
        """Update cleanup configuration at runtime and apply changes to running thread"""
        old_enabled = self.cleanup_config.get("enabled", True)
        old_check_interval = self.cleanup_config.get("check_interval", 300)
        
        # Update the configuration
        self.cleanup_config.update(config)
        
        new_enabled = self.cleanup_config.get("enabled", True)
        new_check_interval = self.cleanup_config.get("check_interval", 300)
        
        logger.info(f"Updating cleanup config: {config}")
        
        # Handle enabled/disabled state changes
        if not old_enabled and new_enabled:
            # Was disabled, now enabled - start thread
            logger.info("Enabling cleanup thread")
            self.start_cleanup_thread()
        elif old_enabled and not new_enabled:
            # Was enabled, now disabled - stop thread
            logger.info("Disabling cleanup thread")
            self.stop_cleanup_thread()
        elif old_enabled and new_enabled:
            # Was enabled and still enabled - check if we need to restart for interval change
            if old_check_interval != new_check_interval:
                logger.info(f"Check interval changed from {old_check_interval} to {new_check_interval}, restarting thread")
                self.stop_cleanup_thread()
                self.start_cleanup_thread()
            else:
                # Just session_timeout changed - no need to restart thread
                # The worker will pick up the new timeout on next check
                logger.info("Session timeout updated, will take effect on next cleanup cycle")

    def get_session_stats(self):
        """Get statistics about current sessions"""
        current_time = time.time()
        stats = {
            "total_sessions": len(self.chat_sessions),
            "session_details": []
        }
        
        for session_id, session_data in self.chat_sessions.items():
            last_activity = session_data.get("timestamp_latest", 0)
            time_since_activity = current_time - last_activity
            
            stats["session_details"].append({
                "session_id": session_id,
                "created": session_data.get("timestamp_init", 0),
                "last_activity": last_activity,
                "inactive_seconds": time_since_activity,
                "message_count": len(session_data.get("messages", []))
            })
        
        return stats

    def load_model(self):
        MAX_RETRIES = 3
        RETRY_DELAY = 5
        for attempt in range(1, MAX_RETRIES + 1):
            try:

                from vllm import LLM, SamplingParams

                logger.info(f"Loading model from {self.model_path} with config: {self.model_config}")
                kv_cache_dtype = self.model_config.get("kv_cache_dtype", "fp8")
                if "fp8" in kv_cache_dtype:
                    self.model_config["kv_cache_dtype"] = "fp8"
                self.model = LLM(
                    model=self.model_path,
                    **self.model_config
                    # tensor_parallel_size=4,
                    # max_model_len=2048,
                    # max_num_seqs=4,            # keep low to avoid OOM
                    # gpu_memory_utilization=0.8,
                    # kv_cache_dtype="fp8",
                    # dtype="bfloat16"
                )
                # print(f"Model architecture: {self.model.metadata().get('general.architecture_name', 'unknown')}")
                # print(f"Model parameters: {self.model.metadata().get('general.parameter_count', 'unknown')}")
                # print(f"Model capabilities: {self.model.metadata().get('general.capabilities', 'unknown')}")
                logger.info("Model loaded successfully.")
                
                # Pass model reference to metrics for native timing access
                if self.metrics and hasattr(self.metrics, 'set_model_reference'):
                    logger.info("📊 Setting model reference in metrics for native timings")
                    self.metrics.set_model_reference(self.model, self.use_native_timings)
                self.model_state = {
                    "loaded": True,
                    "error": None
                }

                def force_fp8_dtype(llm: LLM, dtype: str = "fp8e4b15"):
                    """Force a specific fp8 dtype in the engine (bypassing pydantic validator)."""
                    engine = llm.llm_engine
                    cache_cfg = engine.cache_config
                    cache_cfg.cache_dtype = dtype
                    # Also patch underlying CUDA cache if already built
                    if hasattr(engine.model_executor.driver_worker, "cache_config"):
                        engine.model_executor.driver_worker.cache_config.cache_dtype = dtype
                    print(f"⚡ Forced KV cache dtype to {dtype}")
                # Force after initialization
                force_fp8_dtype(self.model, kv_cache_dtype)
                return True
            except (ValueError, RuntimeError) as e:
                # Config or validation errors (bad kv_cache_dtype, TP mismatch, etc.)
                logger.error(f"[Config/Runtime error] {e}")
                if attempt == MAX_RETRIES:
                    self.model_state = {
                        "loaded": False,
                        "error": str(e)
                    }
                    raise
            except torch.cuda.OutOfMemoryError as e:
                logger.error(f"[CUDA OOM] {e}")
                if attempt == MAX_RETRIES:
                    self.model_state = {
                        "loaded": False,
                        "error": str(e)
                    }
                    raise
            except torch.cuda.CudaError as e:
                logger.error(f"[CUDA kernel error] {e}")
                if attempt == MAX_RETRIES:
                    self.model_state = {
                        "loaded": False,
                        "error": str(e)
                    }
                    raise
            except OSError as e:
                # Missing model/tokenizer files
                logger.error(f"[File/IO error] {e}")
                if attempt == MAX_RETRIES:
                    self.model_state = {
                        "loaded": False,
                        "error": str(e)
                    }
                    raise
            except Exception as e:
                # Catch-all for unexpected issues
                logger.error(f"[Unexpected {type(e).__name__}] {e}")
                if attempt == MAX_RETRIES:
                    self.model_state = {
                        "loaded": False,
                        "error": str(e)
                    }
                    raise
                
                #return False
            print(f"Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

    def supports_chat(self):
        #return hasattr(self.model, "create_chat_completion")
        return False



    def get_model_info(self):
        if not self.model:
            logger.error("Model is not loaded.")
            return False
        try:
            return self.model_state.get("loaded",False)
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            logger.error(f"Error from model_state: {self.model_state.get('error','UNKNOWN')}")
            return False

    def set_seed(self, seed):
        if not self.model:
            logger.error("Model is not loaded.")
            return False
        try:
            self.model.set_seed(seed)
            return True
        except Exception as e:
            logger.error(f"Error setting seed: {e}")
            return False

    def _compute_throughputs(self, request_output,duration):
        """
        Compute throughput metrics from a vLLM RequestOutput object.

        Args:
            request_output: A vLLM RequestOutput instance.

        Returns:
            dict with prompt_eval_tok_per_s, decode_tok_per_s, total_tok_per_s
        """
        m = request_output.metrics
        results = {}

        outputs = request_output.outputs[0]

        prompt_tokens = len(request_output.prompt_token_ids)
        gen_tokens = len(outputs.token_ids)
        total_tokens = prompt_tokens + gen_tokens

        # Also return token counts for logging
        results["prompt_tokens"] = prompt_tokens
        results["generated_tokens"] = gen_tokens
        results["total_tokens"] = total_tokens

        if m is not None:
            #print("=== Metrics ===")
            results["arrival_time"] = m.arrival_time
            results["first_scheduled_time"] = m.first_scheduled_time
            results["first_token_time"] = m.first_token_time
            results["last_token_time"] = m.last_token_time
            results["time_in_queue"] = m.time_in_queue
            results["finished_time"] = m.finished_time
            results["scheduler_time"] = m.scheduler_time
            results["model_forward_time"] = m.model_forward_time
            results["model_execute_time"] = m.model_execute_time

            # Prompt eval throughput
            if m.first_token_time and m.first_scheduled_time:
                prompt_eval_dur = m.first_token_time - m.first_scheduled_time
                if prompt_eval_dur > 0:
                    results["prompt_eval_tok_per_s"] = prompt_tokens / prompt_eval_dur

            # Decode throughput
            if m.last_token_time and m.first_token_time:
                decode_dur = m.last_token_time - m.first_token_time
                if decode_dur > 0:
                    results["decode_tok_per_s"] = gen_tokens / decode_dur

            # End-to-end throughput
            if m.finished_time and m.arrival_time:
                total_dur = m.finished_time - m.arrival_time
                if total_dur > 0:
                    results["total_tok_per_s"] = total_tokens / total_dur
        else:
            results["prompt_eval_tok_per_s"] = prompt_tokens / duration
            results["decode_tok_per_s"] = gen_tokens / duration
            results["total_tok_per_s"] = total_tokens / duration

        

        return results

    def generate_text(self, prompts, generation_configs):
        MAX_RETRIES = 3
        RETRY_DELAY = 5
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                from vllm import SamplingParams
                import torch
                if not self.model:
                    logger.error("Model is not loaded.")
                    return None

                if len(prompts) != len(generation_configs):
                    logger.error("Length of prompts and generation_configs must match.")
                    return None
                if len(prompts) > self.model_config.get("max_num_seqs", 1):
                    logger.error(f"Number of prompts exceeds max_num_seqs ({self.model_config.get('max_num_seqs', 1)}).")
                    return None

                #print("prompts:",prompts)

                num_sequences = len(prompts)
                sampling_params = [SamplingParams(**generation_configs[i]) for i in range(num_sequences)]
                #print("sampling_params:",sampling_params)

                # Track total generation time
                start_time = time.time()
                start = time.perf_counter()
                # ✅ Correct: pass both lists
                torch.cuda.synchronize()
                results = self.model.generate(prompts, sampling_params)
                torch.cuda.synchronize()
                end = time.perf_counter()
                total_time = end - start
                #force_fp8_dtype(self.model, self.kv_cache_dtype)

                resultsToReturn = []

                for i, output in enumerate(results):
                    logger.debug(f"=== Prompt {i+1} ===")
                    logger.debug(f"Prompt: {prompts[i]}")
                    logger.debug(f"Generated: {output.outputs[0].text}")
                    if len(output.outputs[0].text) <= 1:
                        logger.warning(f"⚠️ Generated text is very short (<=1 char), 🛑")
                        if self.metrics:
                            self.metrics.increment_inference_empty_tokens()
                    resultsToReturn.append(output.outputs[0].text)
                    stats = self._compute_throughputs(output,total_time)
                    logger.info(f"Prompt tokens: {stats['prompt_tokens']}")
                    logger.info(f"Generated tokens: {stats['generated_tokens']}")
                    logger.info(f"Total tokens: {stats['total_tokens']}")
                    logger.info(f"Prompt eval throughput: {stats.get('prompt_eval_tok_per_s')}")
                    logger.info(f"Decode throughput: {stats.get('decode_tok_per_s')}")
                    logger.info(f"End-to-end throughput: {stats.get('total_tok_per_s')}")
                    logger.debug(f"Stats: {stats}")
                    if self.metrics:
                        prompt_tokens = stats["prompt_tokens"]
                        generated_tokens = stats["generated_tokens"]

                        self.metrics.log_prompt(prompt_tokens)
                        self.metrics.log_response(generated_tokens)
                        self.metrics.observe_time_to_first_token(stats.get("first_token_time"))
                        self.metrics.observe_inference_time(stats.get("first_scheduled_time"))
                        self.metrics.observe_time_per_output_token(stats.get("first_token_time"), generated_tokens)
                        duration = stats.get("last_token_time") - stats.get("first_token_time")
                        self.metrics.update_tokens_per_second(generated_tokens, duration)
                        self.metrics.update_last_processed_time(time.time())
                        
                        # Update rolling metrics for autoscaling
                        self.update_rolling_metrics()


                return resultsToReturn
            except torch.cuda.OutOfMemoryError as e:
                logger.error(f"Error generating tex [CUDA OOM] {e}")
                if attempt == MAX_RETRIES:
                    if self.metrics:
                        self.metrics.increment_inference_errors()
                        return None
            except torch.cuda.CudaError as e:
                logger.error(f"Error generating text [CUDA kernel error] {e}")
                if attempt == MAX_RETRIES:
                    if self.metrics:
                        self.metrics.increment_inference_errors()
                        return None
            except RuntimeError as e:
                logger.error(f"Error generating text [Runtime error] {e}")
                if attempt == MAX_RETRIES:
                    if self.metrics:
                        self.metrics.increment_inference_errors()
                        return None
            except Exception as e:
                logger.error(f"Error generating text [Unexpected {type(e).__name__}] {e}")
                if attempt == MAX_RETRIES:
                    if self.metrics:
                        self.metrics.increment_inference_errors()
                        return None

            logger.info(f"Retrying generation in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)


    def create_chat_session(self, session_id, system_message="", tools_list=None, tools_choice=None):
        logger.info(f"🗣️ Creating chat session: {session_id}")
        self.chat_sessions[session_id] = {
            "messages": [{
                "role": "system",
                "content": system_message
            }],
            "tools": tools_list or [],
            "tool_choice": tools_choice or {},
            "timestamp_init": time.time(),
            "timestamp_latest": time.time()
        }
        if self.metrics:
            logger.info(f"📈 Calling increase_active_sessions for session: {session_id}")
            try:
                self.metrics.increase_active_sessions()
                logger.info(f"✅ increase_active_sessions completed. Total sessions: {len(self.chat_sessions)}")
            except Exception as e:
                logger.error(f"❌ METRICS ERROR in increase_active_sessions: {e}")
        else:
            logger.warning("⚠️ No metrics object available for session tracking")

    def add_message_to_chat(self, session_id, message, role="user"):
        if session_id not in self.chat_sessions:
            raise Exception(f"session_id {session_id} not found")
        self.chat_sessions[session_id]["messages"].append({
            "role": role,
            "content": message
        })
        #update the timestamp for the session
        self.chat_sessions[session_id]["timestamp_latest"] = time.time()

    def _handle_context_of_chat(self, session):
        try:
            n_ctx = self.model_config.get("n_ctx", 4096)
            safe_margin = int(0.125 * n_ctx)
            max_tokens = n_ctx - safe_margin

            #print("before",session["messages"])
            # Always keep the system prompt (index 0)
            prompt_tokens = 0
            while True:
                # Tokenize all messages except system prompt
                messages_to_check = session["messages"]
                total_tokens = sum(len(self.model.tokenize(bytes(msg['content'], "utf-8"))) for msg in messages_to_check)
                #print("total tokens:", total_tokens, "max tokens:", max_tokens)
                if total_tokens < max_tokens or len(messages_to_check) <= 1:
                    prompt_tokens = total_tokens
                    break
                # Remove oldest user/assistant message (index 1)
                session["messages"].pop(1)
            #print("after",session["messages"])
            return prompt_tokens
        except Exception as e:
            logger.error(f"Error during _handle_context_of_chat: {e}")
            if self.metrics:
                self.metrics.increment_inference_errors()
            raise

    def has_chat_session(self, session_id):
        """
        Check if a chat session exists for the given session_id.
        """
        return session_id in self.chat_sessions and "messages" in self.chat_sessions[session_id]

    def run_chat_inference(self, session_id, stream, context,is_ws, **kwargs):
        print(f"[DEBUG] run_chat_inference called for session_id: {session_id}, stream={stream}")
        if not self.model:
            raise Exception("Model is not loaded")

        if session_id not in self.chat_sessions:
            raise Exception(f"session_id {session_id} not found")

        if not self.supports_chat():
            raise Exception("Chat mode is not supported by this model")

        try:
            session = self.chat_sessions[session_id]
            if session["tools"]:
                kwargs["tools"] = session["tools"]
            if session["tool_choice"]:
                kwargs["tool_choice"] = session["tool_choice"]
            # print("kwargs for chat inference:", kwargs)
            # kwargs["max_tokens"] = 1024
            # kwargs["stop"] = ['Q:']
            # print("kwargs for chat inference: after", kwargs)
            print("kwargs for chat inference", kwargs)
            prompt_tokens = self._handle_context_of_chat(session)
            start_time = time.time()
            response = self.model.create_chat_completion(
                messages=session["messages"],
                stream=stream,
                **kwargs
            )
            end_time = time.time()
            print("duration of inference:", end_time - start_time)

            if not stream:
                message = response.get("message") or response.get("choices", [{}])[0].get("message")
                if not message:
                    raise Exception("Invalid response structure")
                #print("message before adding and will be returned:", message)
                #print("message content:", message["content"])
                session["messages"].append(message)
                performance_data = self.model._ctx.get_timings()
                print(f"[DEBUG] performance_data: {performance_data}")
                if self.metrics:
                    #prompt_tokens = sum(len(self.model.tokenize(m["content"])) for m in session["messages"])
                    generated_tokens = response["usage"]["completion_tokens"]
                    duration = end_time - start_time
                    # print(f"[DEBUG] METRICS: prompt_tokens={prompt_tokens}, generated_tokens={generated_tokens}, duration={duration}")
                    try:
                        print("[DEBUG] Calling log_prompt...")
                        self.metrics.log_prompt(prompt_tokens)
                        print("[DEBUG] log_prompt completed")
                        print("[DEBUG] Calling log_response...")
                        self.metrics.log_response(generated_tokens)
                        print("[DEBUG] log_response completed")
                        print("[DEBUG] Calling observe_time_to_first_token...")
                        self.metrics.observe_time_to_first_token(start_time)
                        print("[DEBUG] observe_time_to_first_token completed")
                        print("[DEBUG] Calling observe_inference_time...")
                        self.metrics.observe_inference_time(start_time)
                        print("[DEBUG] observe_inference_time completed")
                        print("[DEBUG] Calling observe_time_per_output_token...")
                        self.metrics.observe_time_per_output_token(start_time, generated_tokens)
                        print("[DEBUG] observe_time_per_output_token completed")
                        print("[DEBUG] Calling update_tokens_per_second...")
                        self.metrics.update_tokens_per_second(generated_tokens, duration)
                        print("[DEBUG] update_tokens_per_second completed")
                        print("[DEBUG] Updating rolling metrics for autoscaling...")
                        self.update_rolling_metrics()
                        print("[DEBUG] Rolling metrics updated")
                        print("[DEBUG] ALL METRICS CALLS COMPLETED SUCCESSFULLY")
                    except Exception as metrics_error:
                        print(f"[DEBUG] METRICS ERROR in run_chat_inference: {metrics_error}")
                        logger.error(f"❌ METRICS ERROR in run_chat_inference: {metrics_error}")
                        import traceback
                        print(traceback.format_exc())
                        logger.error(f"   Traceback: {traceback.format_exc()}")
                return message["content"]
            else:
                # Initialize an empty string to store the full response
                full_response = ""
                generated_tokens = 0
                first_token_observed = False

                # Iterate through the response
                lastchunk = None
                ttft = 0
                for chunk in response:
                    # Observe TTFT on the very first chunk
                    if not first_token_observed and self.metrics:
                        ttft = time.time() - start_time
                        self.metrics.observe_time_to_first_token(start_time)
                        first_token_observed = True

                    delta = chunk['choices'][0]['delta']
                    if 'content' in delta and delta['content'] is not None:
                        generated_tokens += 1
                        content_piece = delta['content']
                        
                        # Print the piece to the console in real-time
                        #print(content_piece, end="", flush=True)
                        
                        # Add the piece to our full_response string
                        full_response += content_piece
                        lastchunk = chunk
                        if is_ws:
                            context.write_ws(session_id,{"delta":content_piece})
                end_time = time.time()
                print("ttft:", ttft)
                print("eval time:", end_time - start_time)
                # get perfomance metrics
                # performance_data = self.model._ctx.get_timings()
                # print(performance_data)
 
                if lastchunk:
                    # Write the last chunk to the websocket
                    #lastchunk["choices"][0]["delta"]["content"] = "[END_OF_STREAM]"
                    lastchunk = {"delta":"[END_OF_STREAM]"}
                    if is_ws:
                        context.write_ws(session_id, lastchunk)
                print("metrics is ", self.metrics)
                performance_data = self.model._ctx.get_timings()
                print(f"[DEBUG] performance_data: {performance_data}")
                if self.metrics:
                    # Note: llama-cpp-python's response usage for streams is often incomplete.
                    # We use our own token count.

                    prompt_tokens = performance_data.get("n_p_eval", 0)
                    generated_tokens = performance_data.get("n_eval", 0)
                    duration = end_time - start_time
                    print(f"[DEBUG] METRICS (Stream): prompt_tokens={prompt_tokens}, generated_tokens={generated_tokens}, duration={duration}")
                    try:
                        print("[DEBUG] Calling log_prompt...")
                        self.metrics.log_prompt(prompt_tokens)
                        print("[DEBUG] log_prompt completed")
                        print("[DEBUG] Calling log_response...")
                        self.metrics.log_response(generated_tokens)
                        print("[DEBUG] log_response completed")
                        # TTFT is now observed when the first token arrives.
                        print("[DEBUG] Calling observe_inference_time...")
                        self.metrics.observe_inference_time(start_time)
                        print("[DEBUG] observe_inference_time completed")
                        print("[DEBUG] Calling observe_time_per_output_token...")
                        self.metrics.observe_time_per_output_token(start_time, generated_tokens)
                        print("[DEBUG] observe_time_per_output_token completed")
                        print("[DEBUG] Calling update_tokens_per_second...")
                        self.metrics.update_tokens_per_second(generated_tokens, duration)
                        print("[DEBUG] update_tokens_per_second completed")
                        print("[DEBUG] Updating rolling metrics for autoscaling...")
                        self.update_rolling_metrics()
                        print("[DEBUG] Rolling metrics updated")
                        print("[DEBUG] ALL METRICS CALLS COMPLETED SUCCESSFULLY")
                    except Exception as metrics_error:
                        print(f"[DEBUG] METRICS ERROR in run_chat_inference (stream): {metrics_error}")
                        logger.error(f"❌ METRICS ERROR in run_chat_inference (stream): {metrics_error}")
                        import traceback
                        print(traceback.format_exc())
                        logger.error(f"   Traceback: {traceback.format_exc()}")

                # get perfomance metrics
                performance_data = self.model._ctx.get_timings()
                print(performance_data)
                # After the loop, full_response has the complete message.
                # Now, add it to the chat history with the 'assistant' role.
                if full_response:
                    session["messages"].append({
                        "role": "assistant",
                        "content": full_response
                    })

                return full_response
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during chat inference at line {line_number}: {e}")
            logger.error(f"Error during chat inference at line {line_number}: {e}")
            if self.metrics:
                self.metrics.increment_inference_errors()
            raise e

    def remove_chat_session(self, session_id):
        logger.info(f"🗑️ Removing chat session: {session_id}")
        if session_id not in self.chat_sessions:
            raise Exception(f"session_id {session_id} not found")
        del self.chat_sessions[session_id]
        if self.metrics:
            logger.info(f"📈 Calling decrease_active_sessions for session: {session_id}")
            try:
                self.metrics.decrease_active_sessions()
                logger.info(f"✅ decrease_active_sessions completed. Remaining sessions: {len(self.chat_sessions)}")
            except Exception as e:
                logger.error(f"❌ METRICS ERROR in decrease_active_sessions: {e}")
        else:
            logger.warning("⚠️ No metrics object available for session tracking")

    def update_rolling_metrics(self):
        """
        Update rolling averages for gauge metrics.
        
        This should be called periodically (e.g., every 10-30 seconds) to ensure
        rolling averages are kept up-to-date for autoscaling decisions.
        """
        if self.metrics and hasattr(self.metrics, 'update_rolling_metrics'):
            logger.info("📊 Updating rolling metrics for autoscaling")
            try:
                self.metrics.update_rolling_metrics()
                logger.info("✅ Rolling metrics updated successfully")
            except Exception as e:
                logger.error(f"❌ ERROR updating rolling metrics: {e}")
        else:
            logger.warning("⚠️ No enhanced metrics available for rolling updates")

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_cleanup_thread()
