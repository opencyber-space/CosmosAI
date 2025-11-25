"""Quick integration test for the **vLLMChatBlock**.

Run:
    python test_llama_cpp_chat_block.py

It demonstrates:
  1. Initial inference (multi‑turn batch)
  2. A runtime `management()` call that reloads the model
  3. A hot `on_update()` that tweaks generation defaults
  4. Inference again with the new settings
"""

import pprint
from main_orig_vllmbatch import vLLMChatBlock
from aios_instance import TestContext, BlockTester
import time
#from aios_llama_cpp import LLMMetrics

def main():
    # -----------------------------------------------------------------------------
    # Context setup
    # -----------------------------------------------------------------------------
    context = TestContext()
    context.common_path = "/home/ubuntu/models"
    context.instance_path = ""
    # -- defaults that *can* be changed via `on_update` ---------------------------
    vllm_config = {
                "max_model_len": 512,     #"tensor_parallel_size": 4,
                "max_num_seqs": 4,            # keep low to avoid OOM, Batch Size
                #"kv_cache_dtype": "auto",     #"gpu_memory_utilization": 0.8,
                "dtype": "bfloat16",
                "enable_prefix_caching": False,
                #"kv_cache_memory_bytes": 1.5*1024*1024*1024, # 1 GiB
                #"tokenizer_mode": "mistral",
                #"quantization": "bitsandbytes",
                "enable_chunked_prefill": True,
                "enable_thinking": False
            }
    # -- immutable during block lifetime -----------------------------------------
    context.block_init_data = {
        #"model_name": "mistralai/Magistral-Small-2506_gguf/Magistral-Small-2506_Q8_0.gguf",   # change to your local path
        #"model_name": "mistralai/Magistral-Small-2506_gguf/Magistral-Small-2506.gguf",
        #"model_name": "unsloth/Magistral-Small-2506-GGUF/Magistral-Small-2506-Q8_0.gguf",
        #"model_name": "unsloth/Qwen3-32B-GGUF/BF16",
        #"model_name": "unsloth/Qwen3-32B-GGUF/Qwen3-32B-Q8_0.gguf"
        
        #vllm triied
        #"model_name": "Qwen_Qwen3-32B"
        #"model_name": "mistralai/Magistral-Small-2506"
        #"model_name": "Qwen/Qwen2-0.5B"
        "model_name": "unsloth/Qwen3-1.7B"
    }
    context.block_init_settings = {
        "use_gpu": True,
        "gpu_id": 0,
        "enable_metrics": False,  # hook LLMMetrics automatically
        "model_config": vllm_config
        
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
        "repetition_penalty": 1.0,
        "min_p": 0.01,
        "top_k": -1,
        "top_p": 0.95,
        "max_tokens": 256, # Set a limit for the response length,
        "max_history": 1
    }

    # Attach a metrics collector (optional)
    #context.metrics = LLMMetrics()

    # -----------------------------------------------------------------------------
    # Instantiate the block in a tester harness
    # -----------------------------------------------------------------------------

    tester = BlockTester.init_with_context(vLLMChatBlock, context)

    # -----------------------------------------------------------------------------
    # 1) Run a two‑turn chat inside a single batch
    # -----------------------------------------------------------------------------
    generation_config = {
        "temperature": 0.7,
        "repetition_penalty": 1.0,
        "min_p": 0.01,
        "top_k": -1,
        "top_p": 0.95,
        "max_tokens": 256 # Set a limit for the response length
    }

    while True:

        payload = {
            "inputs": [
                {
                    "mode": "chat",
                    "message": 'hi, how are you?',
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
                    "message": 'hi, what is your name?',
                    "session_id": "101",
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
                    "message": 'how is whether in Bengaluru today?',
                    "session_id": "102",
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
                    "message": 'what day is today?',
                    "session_id": "103",
                    "gen_params": generation_config
                }
            ]
        }
        before = tester.run(payload)
        pprint.pprint(before)



        payload = {
            "inputs": [
                {
                    "mode": "chat",
                    "message": 'how to check fake currencies?',
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
                    "message": 'what is the capital of India?',
                    "session_id": "101",
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
                    "message": 'what is content of potatoes?',
                    "session_id": "102",
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
                    "message": 'can llms be run in mobile phones?',
                    "session_id": "103",
                    "gen_params": generation_config
                }
            ]
        }
        before = tester.run(payload)
        pprint.pprint(before)

if __name__ == "__main__":
    main()
