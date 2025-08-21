#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <blockId>"
  exit 1
fi

BLOCK_ID=$1

curl -X POST -H "Content-Type: application/json" \
    http://MANAGEMENTMASTER:30501/api/executeMgmtCommand \
    -d "
    {
      \"header\": {
        \"templateUri\": \"Parser/V1\",
        \"parameters\": {}
      },
      \"body\": {
        \"spec\": {
          \"values\": {
            \"blockId\": \"${BLOCK_ID}\",
            \"service\": \"executor\",
            \"mgmtCommand\": \"get_logs\",
            \"mgmtData\": {}
          }
        }
      }
    }
"
