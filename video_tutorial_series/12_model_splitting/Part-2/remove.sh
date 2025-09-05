#!/bin/bash

curl -X POST http://MANAGEMENTMASTER:30600/controller/removeBlock/gcp-cluster-1 \
    -H "Content-Type: application/json" \
    -d '{"block_id": "vllm-block-1"}'
