"""Quick integration test for the **LlamaCppChatBlock**.

Run:
    python test_llama_cpp_chat_block.py

It demonstrates:
  1. Initial inference (multi‑turn batch)
  2. A runtime `management()` call that reloads the model
  3. A hot `on_update()` that tweaks generation defaults
  4. Inference again with the new settings
"""

import pprint
from main import LlamaCppChatBlock
from aios_instance import TestContext, BlockTester
import time
#from aios_llama_cpp import LLMMetrics

# -----------------------------------------------------------------------------
# Context setup
# -----------------------------------------------------------------------------
context = TestContext()
context.common_path = "/home/ubuntu/models"
context.instance_path = ""
# -- defaults that *can* be changed via `on_update` ---------------------------
llama_config = {
    "n_gpu_layers": -1,         # -1 is the standard way to say "all layers"
    "n_threads": -1,            # Corresponds to --threads -1
    "n_ctx": 4096,             # Corresponds to --ctx-size
    #"type_k": "f16",            # Corresponds to --cache-type-k f16
    "seed": 3407,               # Corresponds to --seed
    #"chat_format": "jinja2",    # Corresponds to --jinja
    "verbose": True            # Good practice to control logging output
}
# -- immutable during block lifetime -----------------------------------------
context.block_init_data = {
    "model_name": "mistralai/Magistral-Small-2506_gguf/Magistral-Small-2506_Q8_0.gguf",   # change to your local path
    #"model_name": "mistralai/Magistral-Small-2506_gguf/Magistral-Small-2506.gguf",
    #"model_name": "unsloth/Magistral-Small-2506-GGUF/Magistral-Small-2506-Q8_0.gguf",
    #"model_name": "unsloth/Qwen3-32B-GGUF/BF16",
    #"model_name": "unsloth/Qwen3-32B-GGUF/Qwen3-32B-Q8_0.gguf"
    
}
context.block_init_settings = {
    "use_gpu": True,
    "gpu_id": 0,
    "enable_metrics": False,  # hook LLMMetrics automatically
    "model_config": llama_config,
    "cleanup_enabled":  True,
    "cleanup_check_interval": 10,
    "cleanup_session_timeout": 30

}

# context.block_init_data = {
#     # "model_path": "Llama-4-Scout-17B-16E-Instruct-UD-Q8_K_XL/Llama-4-Scout-17B-16E-Instruct-UD-Q8_K_XL-00001-of-00003.gguf",
#     # "model_path": "./DeepSeek-R1-Distill-Llama-70B-GGUF-UD-Q8_K_XL/*.gguf",   # change to your local path
#     "model_path": "DeepSeek-R1-Distill-Llama-70B-UD-Q8_K_XL/DeepSeek-R1-Distill-Llama-70B-UD-Q8_K_XL-00001-of-00002.gguf",   # change to your local path
#     "use_gpu": True,
#     "gpu_id": [0,1],
#     "enable_metrics": False,  # hook LLMMetrics automatically
# }



context.block_init_parameters = {
    "temperature": 0.7,
    "max_tokens": 1024,
    "top_p": 0.95,
}

# Attach a metrics collector (optional)
#context.metrics = LLMMetrics()

# -----------------------------------------------------------------------------
# Instantiate the block in a tester harness
# -----------------------------------------------------------------------------

tester = BlockTester.init_with_context(LlamaCppChatBlock, context)

# -----------------------------------------------------------------------------
# 1) Run a two‑turn chat inside a single batch
# -----------------------------------------------------------------------------
generation_config = {
    "temperature": 0.7,
    "repeat_penalty": 1.0,
    "min_p": 0.01,
    "top_k": -1,
    "top_p": 0.95,
    "max_tokens": 50  # Set a limit for the response length
}

totalSessions = 100
session_id = 100  # Use a fixed session ID for testing
for i in range(totalSessions):
    payload = {
        "inputs": [
            {
                "mode": "chat",
                "message": 'hi',
                "system_message": "You are a helpful assistant.",
                "session_id": str(session_id),
                "gen_params": generation_config
            }
        ]
    }

    before = tester.run(payload)
    print(f"\n--- sessionID:{session_id} ---")
    pprint.pprint(before)

    session_id = session_id + 1
    time.sleep(1)
