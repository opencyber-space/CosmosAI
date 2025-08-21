#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

curl -X GET http://MANAGEMENTMASTER:30102/policy/preprocessing_policy_for_summarization:0.0.1-stable | json_pp
