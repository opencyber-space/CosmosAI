curl -X POST http://MANAGEMENTMASTER:30102/policy \
     -H "Content-Type: application/json" \
     -d '{
           "name": "quota-checker",
           "version": "2.0",
           "release_tag": "stable",
           "metadata": {
             "author": "admin",
             "category": "access-control"
           },
           "tags": "quota,control,access",
           "code": "http://MANAGEMENTMASTER:32555/quota_checker.zip",
           "code_type": "tar.xz",
           "type": "policy",
           "policy_input_schema": {
             "type": "object",
             "properties": {
               "quota_table": {"type": "object"},
               "input": {"type": "object"},
               "quota": {"type": "integer"},
               "session_id": {"type": "string"}
             },
             "required": ["quota_table", "input", "quota", "session_id"]
           },
           "policy_output_schema": {
             "type": "object",
             "properties": {
               "allowed": {"type": "boolean"}
             },
             "required": ["allowed"]
           },
           "policy_settings_schema": {
             "type": "object",
             "properties": {}
           },
           "policy_parameters_schema": {
             "type": "object",
             "properties": {
               "default_limit": {"type": "integer"},
               "session_limits": {"type": "object"},
               "whitelist": {
                 "type": "array",
                 "items": {"type": "string"}
               }
             }
           },
           "policy_settings": {},
           "policy_parameters": {},
           "description": "Restricts usage of inference API by session-level quotas.",
           "functionality_data": {"strategy": "quota-based"},
           "resource_estimates": {}
         }'
