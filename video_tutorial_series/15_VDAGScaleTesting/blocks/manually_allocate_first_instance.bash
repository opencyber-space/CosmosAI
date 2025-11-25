
CUR_DIR=$(dirname "$(realpath "$0")")
cd "$CUR_DIR"


#bash $CUR_DIR/DeepSeek_R1_Distill_Qwen_1.5B/create_block.bash
bash $CUR_DIR/Llama-3.2-1B-Instruct/create_block.bash

bash $CUR_DIR/gemma-3-1b-it/create_block.bash

bash $CUR_DIR/Phi-4-mini-instruct/create_block.bash

bash $CUR_DIR/qwen3_1.7b_vllm/create_block.bash