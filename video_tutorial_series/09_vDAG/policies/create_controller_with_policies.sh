curl -X POST http://MANAGEMENTMASTER:30600/vdag-controller/gcp-cluster-2 \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create_controller",
    "payload": {
      "vdag_controller_id": "policies-test-c", 
      "vdag_uri": "llm-analyzer:0.0.3-stable",
      "config": {
        "policy_execution_mode": "local",
        "replicas": 1,
        "custom_data": {
            "quotaChecker": {
                "quotaCheckerPolicyRule": {
                    "policyRuleURI": "quota-checker:2.0-stable",
                    "parameters": {
                        "default_limit": 1,
                        "whitelist": ["session10"]
                    }
                }
            },
            "qualityChecker": {
              "qualityCheckerPolicyRule": {
                "policyRuleURI": "quality-checker:2.0-stable",
                "parameters": {
                  "db_url": "redis://POLICYSTORESERVER:6379/0"
                }
              },
              "framesInterval": 1
            }
        }
      },
      "search_tags": []
    }
  }'