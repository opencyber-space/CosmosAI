#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

curl -X POST -H "Content-Type: application/json" -d @${SCRIPT_DIR}/cluster_add_node_policy_registration.json http://MANAGEMENTMASTER:30102/policy | json_pp