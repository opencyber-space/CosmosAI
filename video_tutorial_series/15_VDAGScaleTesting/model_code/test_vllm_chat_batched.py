from vllm import LLM, SamplingParams
import time
#from vllm.config import ObservabilityConfig


def compute_throughputs(request_output):
    """
    Compute throughput metrics from a vLLM RequestOutput object.

    Args:
        request_output: A vLLM RequestOutput instance.

    Returns:
        dict with prompt_eval_tok_per_s, decode_tok_per_s, total_tok_per_s
    """
    m = request_output.metrics

    if m is not None:
        print("=== Metrics ===")
        print(f"Arrival time: {m.arrival_time:.4f}")
        print(f"First scheduled time: {m.first_scheduled_time}")
        print(f"First token time: {m.first_token_time}")
        print(f"Last token time: {m.last_token_time}")
        print(f"Time in queue: {m.time_in_queue}")
        print(f"Finished time: {m.finished_time}")
        print(f"Scheduler time: {m.scheduler_time}")
        print(f"Model forward time: {m.model_forward_time}")
        print(f"Model execute time: {m.model_execute_time}")

    outputs = request_output.outputs[0]

    prompt_tokens = len(request_output.prompt_token_ids)
    gen_tokens = len(outputs.token_ids)
    total_tokens = prompt_tokens + gen_tokens

    results = {}

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

    # Also return token counts for logging
    results["prompt_tokens"] = prompt_tokens
    results["generated_tokens"] = gen_tokens
    results["total_tokens"] = total_tokens

    return results


def main():

    #modelname = "/home/ubuntu/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    modelname = "/home/ubuntu/models/unsloth/Qwen3-1.7B"
    #modelname = "/home/ubuntu/models/google/gemma-3-1b-it"
    # modelname = "/home/ubuntu/models/microsoft/Phi-4-mini-instruct"
    # modelname = "/home/ubuntu/models/TinyLlama/TinyLlama_v1.1"

    llm = LLM(
        model=modelname,
        tensor_parallel_size=1,
        max_model_len=2048,
        max_num_seqs=4,
        gpu_memory_utilization=0.8,
        kv_cache_dtype="fp8",
        dtype="bfloat16",
    )

    # Build N conversations
    conv1 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a haiku about the sea."},
    ]
    conv2 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain what sequence batching means in LLMs."},
    ]
    conv3 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Summarize the plot of Hamlet in one paragraph."},
    ]
    conv4 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ]

    conversations = [conv1, conv2, conv3, conv4]  # batch list

    # Per-conversation sampling parameters (optional)
    sampling_params = [
        SamplingParams(temperature=0.7, max_tokens=256),
        SamplingParams(temperature=0.8, max_tokens=256),
        SamplingParams(temperature=0.5, max_tokens=256),
        SamplingParams(temperature=0.9, max_tokens=256),
    ]

    # Batched offline chat inference
    outputs = llm.chat(
        messages=conversations,
        sampling_params=sampling_params,  # can also pass a single SamplingParams for all
        use_tqdm=True,                    # optional progress bar,
        chat_template_kwargs={"enable_thinking": False}
    )

    for i, out in enumerate(outputs):
        print(f"=== Conversation {i+1} ===")
        print(out.outputs[0].text)
        print(out)
        stats = compute_throughputs(out)
        print("Prompt tokens:", stats["prompt_tokens"])
        print("Generated tokens:", stats["generated_tokens"])
        print("Total tokens:", stats["total_tokens"])
        print("Prompt eval throughput:", stats.get("prompt_eval_tok_per_s"))
        print("Decode throughput:", stats.get("decode_tok_per_s"))
        print("End-to-end throughput:", stats.get("total_tok_per_s"))
        print()


if __name__ == "__main__":
    main()