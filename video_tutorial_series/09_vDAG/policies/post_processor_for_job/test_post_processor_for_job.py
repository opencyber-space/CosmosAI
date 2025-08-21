from aios_policy_sandbox import LocalPolicyEvaluator
from code.function import AIOSv1PolicyRule

import json
from types import SimpleNamespace

if __name__ == '__main__':

    settings={
        "job_policy_name": "alerter:1.0.0-stable",
        "classification_patterns": [
            "(?i)(?:\*\*)?Classification(?:\*\*)?\s*:\s*`?Alert(?:able)?`?",
            "(?:\\*\\*)?Classification:(?:\\*\\*)?\\s*Alertable",
            "(?:\\*\\*)?Classification:(?:\\*\\*)?\\s*Alert",
            "(?:\\*\\*)?Classification:(?:\\*\\*)?\\s*`Alertable",
            "(?:\\*\\*)?Classification:(?:\\*\\*)?\\s*`Alert",
            "(?:\\*\\*)?Classification(?:\\*\\*)?:\\s*`Alertable`",
            "(?:\\*\\*)?Classification(?:\\*\\*)?:\\s*`Alert`",
            "(?:\\*\\*)?Classification(?:\\*\\*)?:\\s*Alertable",
            "(?:\\*\\*)?Classification(?:\\*\\*)?:\\s*Alert"
        ],
        #"classification_patterns": ['(?i)(?:\*\*)?Classification(?:\*\*)?\s*:\s*`?Alert(?:able)?`?'],
        "zip_store_url" : "http://MANAGEMENTMASTER:32555",
        "BASE_URI": "http://10.138.0.5:5000/receive",
        "pusher_url": "http://POLICYSTORESERVER:30186/upload",
        "policy_registration_url": "http://MANAGEMENTMASTER:30102/policy",
        "job_deployment_url": "http://MANAGEMENTMASTER:30102/jobs/submit/executor-001"
    } # override the settings if needed
    parameters={} # override the parameters if needed

    policy_rule_uri="post_processor_for_job:1.0.0-stable"

    executor = LocalPolicyEvaluator(
        policy_rule_uri=policy_rule_uri,
        parameters=parameters,
        settings=settings,
        custom_class=AIOSv1PolicyRule,
        mode="local"
    )

    llm_response = """
### **Event Analysis**

**Classification**: `Alertable`

**Summary:** A law and order situation has been detected where a person is seen snatching a victim's bag and running away. Immediate action is required to alert authorities and initiate a response.

---

### **alerter.py**

```python
import logging
import requests

class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters

    def eval(self, parameters, input_data, context):
        try:
            summary = input_data.get("summary", "")
            if not summary:
                return

            destination_url = self.settings.BASE_URI
            payload = {
                "source_rule_id": self.rule_id,
                "message_content": summary
            }

            response = requests.post(destination_url, json=payload)
            result = [{
                "api_status_code": response.status_code,
                "api_response_body": response.json()
            }]

            return {
                "result": result,
                "input_data": input_data,
                "reason": "Success"
            }
        except requests.exceptions.RequestException as e:
            return {
                "result": [],
                "input_data": input_data,
                "reason": f"Request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "result": [],
                "input_data": input_data,
                "reason": f"Error: {str(e)}"
            }
```

### **registration.json**

```json
{
    "name": "alerter",
    "version": "1.0.0",
    "release_tag": "stable",
    "metadata": {
      "author_name": "AI Analyst",
      "author_email": "analyst@example.com",
      "organization": "my.org",
      "country": "US",
      "license": "MIT",
      "category": "Alert",
      "use_case": "Use the policy to push the Alert to 3rd party endpoint",
      "geographic_scope": "Global",
      "audience": ["vdag_users"],
      "integration_notes": "",
      "tested_environments": [],
      "execution_environment": "Python 3.10+",
      "compliance_tags": ["ISO/IEC 27001"]
    },
    "tags": "alerting, webhook",
    "code": "http://YOUR_CONTENT_STORE_IP:PORT/alerter.zip",
    "code_type": "zip",
    "type": "policy",
    "policy_input_schema": {
        "summary": {
            "type": "string",
            "description": "The summary message to be sent to the 3rd party service."
        }
    },
    "policy_output_schema": {
        "result": {
            "type": "array",
            "description": "An array containing the status code and response body from the API call."
        },
        "input_data": {
            "type": "object",
            "description": "The original input data passed to the policy."
        },
        "reason": {
            "type": "string",
            "description": "Reason for the decision (e.g., 'Success' or an error message)."
        }
    },
    "policy_settings_schema": {
        "BASE_URI": {
            "type": "string",
            "description": "The destination URL for the HTTP POST request."
        }
    },
    "policy_parameters_schema": {},
    "policy_settings": {
        "BASE_URI": "http://3rdpartyserviceIP:port/receive"
    },
    "policy_parameters": {},
    "management_commands_schema": [],
    "description": "A policy to push alert messages to a third-party service via HTTP POST.",
    "functionality_data": {},
    "resource_estimates": {}
}
```

### **pusher.sh**

```bash
#!/bin/bash

# The path to the zip file you want to upload
FILE_PATH="alerter.zip"

# The destination URL for the content store
ENDPOINT="http://YOUR_CONTENT_STORE_IP:PORT/upload"

echo "Uploading $FILE_PATH to $ENDPOINT..."
# Use curl to post the file
curl -X POST -F "file=@$FILE_PATH" $ENDPOINT
```

### **register.sh**

```bash
#!/bin/bash

# The endpoint for the policy registry
ENDPOINT="http://YOUR_REGISTRY_IP:PORT/policy"

echo "Registering policy using registration.json..."
# Use curl to post the registration file
curl -X POST -H "Content-Type: application/json" --data @./registration.json $ENDPOINT
```

### **deploy_job.sh**

```bash
#!/bin/bash

# The endpoint for the job submission API
ENDPOINT="http://YOUR_JOB_API_IP:PORT/jobs/submit/executor-001"

echo "Submitting job for alerter policy..."
# Use curl to post the job submission
curl -X POST $ENDPOINT \
 -H "Content-Type: application/json" \
 -d '{
    "name": "alerter-critical-node-job",
    "policy_rule_uri": "alerter:1.0.0-stable",
    "policy_rule_parameters": {},
    "node_selector": {},
    "inputs": {
      "summary": "Critical alert: High CPU usage detected on node-123."
    }
  }'
```"""


    # input_data = {
    #     "packet": {
    #         "data": json.dumps({
    #             "reply": llm_response
    #         })
    #     }
    # }

    # 1. Create the innermost object first
    data_object = SimpleNamespace(
        reply=llm_response
    )

    # 2. Create the packet object, embedding the data object
    # We use json.dumps here as in your example
    packet_object = SimpleNamespace(
        data=json.dumps(data_object.__dict__)
    )

    # 3. Create the final input_data object
    input_data = {
         "packet": packet_object
    }

    output = executor.execute_policy_rule(input_data=input_data)
    print(output)