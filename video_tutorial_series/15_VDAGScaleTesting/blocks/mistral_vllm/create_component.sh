#!/bin/bash
CUR_DIR=$(dirname "$(realpath "$0")")
cd "$CUR_DIR"

curl -X POST http://MANAGEMENTMASTER:30112/api/registerComponent \
  -H "Content-Type: application/json" \
  -d @$CUR_DIR/component.json