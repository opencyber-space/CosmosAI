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
    "model_config": llama_config
    
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
    "max_tokens": 2048,
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
    "max_tokens": 2048 # Set a limit for the response length
}

payload = {
    "inputs": [
        {
            "mode": "chat",
            "message": 'provide a code to add two numbers and print it along with my name in python',
            "system_message": "You are a helpful assistant.",
            "session_id": "100",
            "gen_params": generation_config
        }
    ]
}

before = tester.run(payload)
print("\n--- before management updates ---")
pprint.pprint(before)


payload = {
    "inputs": [
        {
            "mode": "chat",
            "message": 'provide a code to add two numbers and print it along with my name in java',
            "session_id": "100",
            "gen_params": generation_config
        }
    ]
}

before = tester.run(payload)
print("\n--- before management updates ---")
pprint.pprint(before)

payload = {
    "inputs": [
        {
            "mode": "chat",
            "message": 'provide a code to add two numbers and print it along with my name in c++',
            "session_id": "100",
            "gen_params": generation_config
        }
    ]
}

before = tester.run(payload)
print("\n--- before management updates ---")
pprint.pprint(before)

for i in range(100):
    payload = {
        "inputs": [
            {
                "mode": "chat",
                "message": 'provide a code to add two numbers and print it along with my name in c#',
                "session_id": "100",
                "gen_params": generation_config
            }
        ]
    }

    before = tester.run(payload)
    pprint.pprint(before)

# start = time.time()
# result = tester.run({"inputs":[{"message": "Could you explain the chatgpt LLM model ?"}],"session_id":"100","gen_params":{"top_p": 95,"max_tokens":256,"temperature": 0.2}})
# print("response time 2nd inference ",time.time() - start)
# print(result)
# start = time.time()
# result = tester.run({"inputs":[{"message": "Could you explain the gemma model?"}],"session_id":"100","gen_params":{"top_p": 95,"max_tokens":256,"temperature": 0.2}})
# print("response time 3rd inference ",time.time() - start)
# print(result)
# start = time.time()
# result = tester.run({"inputs":[{"message": "Could you explain the Phi LLM model?"}],"session_id":"100","gen_params":{"top_p": 95,"max_tokens":256,"temperature": 0.2}})
# print("response time 4th inference ",time.time() - start)
# print(result)
# result = tester.run({"inputs":[{"message": "What do you know about multi-modal llms?"}],"session_id":"100","gen_params":{"top_p": 95,"max_tokens":256,"temperature": 0.2}})
# print("response time 5th inference ",time.time() - start)
# print(result)

# # -----------------------------------------------------------------------------
# # 2) Management: swap to a lighter model file (if available)
# # -----------------------------------------------------------------------------

# management_resp = tester.block_instance.management(
#     "reload_model",
#     {"model_path": "/models/tinyllama-1.1b-chat-v1.0.Q8_0"},
# )
# print("\n--- management() response ---")
# pprint.pprint(management_resp)

# # -----------------------------------------------------------------------------
# # 3) Hot‑update generation defaults
# # -----------------------------------------------------------------------------
# update_params = tester.block_instance.on_update({"temperature": 0.3})
# print("\n--- on_update() response ---")
# pprint.pprint(update_params)

# # -----------------------------------------------------------------------------
# # 4) Run inference again with the new model / settings
# # -----------------------------------------------------------------------------

# after = tester.run(payload)
# print("\n--- after management updates ---")
# pprint.pprint(after)
