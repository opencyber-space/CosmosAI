#!/bin/bash

curl -X POST http://CLUSTER1MASTER:30526/health/mgmt  -H "Content-Type: application/json" \
    -d '{"mgmt_action": "set_allowed_metrics_age", "mgmt_data": {"value": 5}}'