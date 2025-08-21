#!/bin/bash

curl -X POST http://MANAGEMENTMASTER:30102/policy \
     -H "Content-Type: application/json" \
     -d '{
           "name": "health-checker",
           "version": "3.0",
           "release_tag": "stable",
           "metadata": {
             "author": "admin",
             "category": "monitoring"
           },
           "tags": "monitoring,health,infra",
           "code": "http://MANAGEMENTMASTER:32555/health_checker_2.zip",
           "code_type": "tar.xz",
           "type": "policy",
           "policy_input_schema": {
             "type": "object",
             "properties": {
               "mode": {
                 "type": "string",
                 "enum": ["default", "fast_check"]
               },
               "vdag": {"type": "object"},
               "health_check_data": {
                 "type": "object",
                 "additionalProperties": {
                   "type": "object",
                   "properties": {
                     "healthy": {"type": "boolean"},
                     "instances": {
                       "type": "array",
                       "items": {
                         "type": "object",
                         "properties": {
                           "healthy": {"type": "boolean"},
                           "instanceId": {"type": "string"},
                           "lastMetrics": {"type": "number"}
                         },
                         "required": ["healthy", "instanceId"]
                       }
                     }
                   },
                   "required": ["healthy", "instances"]
                 }
               }
             },
             "required": ["mode", "vdag", "health_check_data"]
           },
           "policy_output_schema": {
             "type": "object",
             "properties": {
               "blocks": {
                 "type": "object",
                 "additionalProperties": {
                   "type": "object",
                   "properties": {
                     "healthy": {"type": "boolean"},
                     "reason": {"type": "string"}
                   },
                   "required": ["healthy", "reason"]
                 }
               },
               "overall_healthy": {"type": "boolean"}
             },
             "required": ["blocks", "overall_healthy"]
           },
           "policy_settings_schema": {
             "type": "object",
             "properties": {}
           },
           "policy_parameters_schema": {
             "type": "object",
             "properties": {
               "allowed_metrics_age": {"type": "integer"}
             },
             "required": ["allowed_metrics_age"]
           },
           "policy_settings": {},
           "policy_parameters": {
             "allowed_metrics_age": 60
           },
           "description": "Checks health of each block based on recent metrics and instance health.",
           "functionality_data": {"strategy": "last_metrics_threshold"},
           "resource_estimates": {}
         }'
