#!/usr/bin/env bash
set -euo pipefail
curl -X DELETE http://MANAGEMENTMASTER:30102/policy/postprocessing_policy_router_judge:0.0.1-stable | json_pp
