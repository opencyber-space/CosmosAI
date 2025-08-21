#!/bin/bash

curl -X POST http://MANAGEMENTMASTER:30600/vdag-controller/gcp-cluster-2 \
  -H "Content-Type: application/json" \
  -d '{
    "action": "remove_controller",
    "payload": {
      "vdag_controller_id": "policies-test-c"
    }
  }'