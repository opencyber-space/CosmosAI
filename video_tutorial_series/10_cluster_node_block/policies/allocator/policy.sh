curl -X POST http://MANAGEMENTMASTER:30102/policy \
     -H "Content-Type: application/json" \
     -d '{
           "name": "allocator-2",
           "version": "2.0",
           "release_tag": "stable",
           "metadata": {"author": "admin", "category": "analytics"},
           "tags": "analytics,ai",
           "code": "http://MANAGEMENTMASTER:32555/allocator-2.zip",
           "code_type": "tar.xz",
           "type": "policy",
           "policy_input_schema": {"type": "object", "properties": {"input": {"type": "string"}}},
           "policy_output_schema": {"type": "object", "properties": {"output": {"type": "string"}}},
           "policy_settings_schema": {},
           "policy_parameters_schema": {},
           "policy_settings": {},
           "policy_parameters": {},
           "description": "A policy for factual analysis.",
           "functionality_data": {"strategy": "ML-based"},
           "resource_estimates": {}
         }'
