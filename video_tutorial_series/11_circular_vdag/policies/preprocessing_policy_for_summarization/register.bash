#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

curl -X POST -H "Content-Type: application/json" -d @./pre_processor.json http://MANAGEMENTMASTER:30102/policy | json_pp
