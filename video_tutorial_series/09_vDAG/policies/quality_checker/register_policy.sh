curl -X POST http://MANAGEMENTMASTER:30102/policy \
     -H "Content-Type: application/json" \
     -d '{
           "name": "quality-checker",
           "version": "2.0",
           "release_tag": "stable",
           "metadata": {
             "author": "admin",
             "category": "audit"
           },
           "tags": "audit,quality,compliance",
           "code": "http://MANAGEMENTMASTER:32555/quality_checker.zip",
           "code_type": "tar.xz",
           "type": "policy",
           "policy_input_schema": {
             "type": "object",
             "properties": {
               "vdag_info": {"type": "object"},
               "input_data": {
                 "type": "object",
                 "properties": {
                   "request": {"type": "object"},
                   "response": {"type": "object"}
                 },
                 "required": ["request", "response"]
               }
             },
             "required": ["vdag_info", "input_data"]
           },
           "policy_output_schema": {
             "type": "object",
             "properties": {}
           },
           "policy_settings_schema": {
             "type": "object",
             "properties": {}
           },
           "policy_parameters_schema": {
             "type": "object",
             "properties": {
               "db_url": {"type": "string"}
             },
             "required": ["db_url"]
           },
           "policy_settings": {},
           "policy_parameters": {
             "db_url": "redis://POLICYSTORESERVER:6379/0"
           },
           "description": "Collects request/response samples and audits them for quality compliance.",
           "functionality_data": {"strategy": "sampling"},
           "resource_estimates": {}
         }'
