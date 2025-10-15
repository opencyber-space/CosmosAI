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

    # observability_config = ObservabilityConfig(
    #     show_hidden_metrics_for_version="v0.10.2",  # pass string, not bool
    #     otlp_traces_endpoint=None,
    #     collect_detailed_traces=None
    # )

    llm = LLM(
        model="/home/ubuntu/models/Qwen_Qwen3-32B",
        tensor_parallel_size=4,
        max_model_len=2048,
        max_num_seqs=4,            # keep low to avoid OOM
        gpu_memory_utilization=0.8,
        kv_cache_dtype="fp8",
        dtype="bfloat16"
    )

    # Prompts
    prompts = [
        "Write a haiku about the sea.",
        "Explain what sequence batching means in large language models.",
        "Summarize the plot of Hamlet in one paragraph.",
        "What is the capital of France?"
    ]

    temp = {
            "max_tokens":  30,
            "presence_penalty": 1.0,
            "repetition_penalty": 1.0,
            "temperature": 1.0,
            "top_p": 0.9,
            "top_k": 40,
            "min_p": 0.5,
            "seed": 1234
    }

    #sampling_params = [SamplingParams(**temp) for i in range(len(prompts))]

    # Per-prompt sampling configs (must be same length as prompts)
    sampling_params = [
        SamplingParams(temperature=0.7, max_tokens=30),
        SamplingParams(temperature=0.8, max_tokens=100),
        SamplingParams(temperature=0.5, max_tokens=50),
        SamplingParams(temperature=0.9, max_tokens=10),
    ]

    # Track total generation time
    start_time = time.time()

    # ✅ Correct: pass both lists
    #results = llm.generate(prompts, sampling_params)
    results = llm.generate(prompts, sampling_params)

    end_time = time.time()
    total_time = end_time - start_time

    for i, output in enumerate(results):
        print(f"=== Prompt {i+1} ===")
        print("Prompt:", prompts[i])
        print("Generated:", output.outputs[0].text)

        stats = compute_throughputs(output)
        print("Prompt tokens:", stats["prompt_tokens"])
        print("Generated tokens:", stats["generated_tokens"])
        print("Total tokens:", stats["total_tokens"])
        print("Prompt eval throughput:", stats.get("prompt_eval_tok_per_s"))
        print("Decode throughput:", stats.get("decode_tok_per_s"))
        print("End-to-end throughput:", stats.get("total_tok_per_s"))
        print()

    # Optional: Check vLLM memory stats (per worker, approximate)
    if hasattr(llm.llm_engine, "executor"):
        executor = llm.llm_engine.executor
        print(f"Executor info: cuda blocks: {executor.num_cuda_blocks}, CPU blocks: {executor.num_cpu_blocks}")
        print(f"Max concurrency estimate: {executor.max_concurrency_per_request:.2f}x")


if __name__ == "__main__":
    main()