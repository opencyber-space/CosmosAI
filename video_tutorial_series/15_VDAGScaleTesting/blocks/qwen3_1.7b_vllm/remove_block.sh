#!/bin/bash

curl -X POST http://MANAGEMENTMASTER:30600/controller/removeBlock/gcp-cluster-2 \
    -H "Content-Type: application/json" \
    -d '{"block_id": "qwen3-1-7b-vllm-block"}'