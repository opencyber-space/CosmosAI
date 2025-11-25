from vllm import LLM, SamplingParams
def main():

    modelname = "/home/ubuntu/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    #modelname = "/home/ubuntu/models/unsloth/Qwen3-1.7B"
    # Configurae the sampling parameters (for thinking mode)
    sampling_params = SamplingParams(temperature=0.6, top_p=0.95, top_k=20, max_tokens=512)

    # Initialize the vLLM engine
    llm = LLM(model=modelname)

    # Prepare the input to the model
    prompt = "Give me a short introduction to large language models."
    system_message = "You are a helpful assistant that helps people find information."
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]

    # Generate outputs
    outputs = llm.chat(
        [messages], 
        sampling_params,
        chat_template_kwargs={"enable_thinking": False},  # Set to False to strictly disable thinking
    )

    # Print the outputs.
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")

if __name__ == "__main__":
    main()