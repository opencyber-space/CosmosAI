#!/bin/bash
CUR_DIR=$(dirname "$(realpath "$0")")
cd "$CUR_DIR"
docker build -f  Dockerfile -t MANAGEMENTMASTER:31280/third-party/vllm:demo .