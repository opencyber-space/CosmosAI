#!/usr/bin/env bash
curl -X GET http://MANAGEMENTMASTER:30102/policy/postprocessing_policy_router_debater:0.0.1-stable | json_pp
