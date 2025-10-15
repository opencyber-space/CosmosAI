#!/bin/bash

curl -X POST http://MANAGEMENTMASTER:30600/controller/removeBlock/gcp-cluster-2 \
    -H "Content-Type: application/json" \
    -d '{"block_id": "magistral-small-2506-vllm-block"}'