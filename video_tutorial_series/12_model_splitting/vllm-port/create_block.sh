#!/bin/bash

curl -X POST -d @./block.json \
     -H "Content-Type: application/json" \
     http://MANAGEMENTMASTER:30501/api/createBlock