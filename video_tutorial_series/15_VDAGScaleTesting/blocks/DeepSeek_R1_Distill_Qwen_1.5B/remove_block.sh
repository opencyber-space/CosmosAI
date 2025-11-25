#!/bin/bash

curl -X POST http://MANAGEMENTMASTER:30600/controller/removeBlock/gcp-cluster-2 \
    -H "Content-Type: application/json" \
    -d '{"block_id": "deepseek-r1-distill-qwen-1-5b-vllm-block"}'