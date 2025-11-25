#!/bin/bash

# curl -X POST http://MANAGEMENTMASTER:30600/controller/removeBlock/gcp-cluster-2 \
#     -H "Content-Type: application/json" \
#     -d '{"block_id": "deepseek-r1-distill-qwen-1-5b-vllm-block"}'

curl -X POST http://MANAGEMENTMASTER:30600/controller/removeBlock/gcp-cluster-2 \
    -H "Content-Type: application/json" \
    -d '{"block_id": "llama-3-2-1b-instruct-vllm-block"}'

curl -X POST http://MANAGEMENTMASTER:30600/controller/removeBlock/gcp-cluster-2 \
    -H "Content-Type: application/json" \
    -d '{"block_id": "gemma-3-1b-it-vllm-block"}'

curl -X POST http://MANAGEMENTMASTER:30600/controller/removeBlock/gcp-cluster-2 \
    -H "Content-Type: application/json" \
    -d '{"block_id": "phi-4-mini-instruct-vllm-block"}'

curl -X POST http://MANAGEMENTMASTER:30600/controller/removeBlock/gcp-cluster-2 \
    -H "Content-Type: application/json" \
    -d '{"block_id": "qwen3-1-7b-vllm-block"}'