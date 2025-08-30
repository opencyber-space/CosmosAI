#!/bin/bash
CUR_DIR=$(dirname "$(realpath "$0")")
cd "$CUR_DIR"
curl -X POST -d @$CUR_DIR/block.json \
     -H "Content-Type: application/json" \
     http://MANAGEMENTMASTER:30501/api/createBlock