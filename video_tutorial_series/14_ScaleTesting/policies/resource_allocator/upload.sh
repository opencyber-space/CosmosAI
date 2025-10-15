#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

curl -X POST http://POLICYSTORESERVER:30186/upload   -F "file=@${SCRIPT_DIR}/scaletest_block_resource_allocator.zip" -F "path=."
