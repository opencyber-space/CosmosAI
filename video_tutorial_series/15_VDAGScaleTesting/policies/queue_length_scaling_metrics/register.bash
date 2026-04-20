curl -X POST http://MANAGEMENTMASTER:30102/policy \
     -H "Content-Type: application/json" \
     -d '{
           "name": "queuebasedautoscaler",
           "version": "2.0",
           "release_tag": "stable",
           "metadata": {"author": "admin", "category": "autoscaling"},
           "tags": "autoscaling,queue,load-balancing",
           "code": "http://MANAGEMENTMASTER:32555/queuebasedautoscaler.zip",
           "code_type": "zip",
           "type": "policy",
           "policy_input_schema": {
             "type": "object",
             "properties": {
               "current_instances": {
                 "type": "array",
                 "items": {"type": "string"},
                 "description": "List of current instance IDs for autoscaling"
               }
             },
             "required": ["current_instances"]
           },
           "policy_output_schema": {
             "type": "object",
             "properties": {
               "skip": {"type": "boolean"},
               "operation": {"type": "string", "enum": ["upscale", "downscale"]},
               "instances_count": {"type": "integer"},
               "instances_list": {"type": "array", "items": {"type": "string"}},
               "reason": {"type": "string"}
             }
           },
           "policy_settings_schema": {
             "type": "object",
             "properties": {
               "get_metrics": {
                 "type": "object",
                 "description": "Function to retrieve system metrics"
               }
             }
           },
           "policy_parameters_schema": {
             "type": "object",
             "properties": {
               "averaging_period": {
                 "type": "string",
                 "enum": ["average_1m", "average_5m", "average_15m", "current"],
                 "default": "average_1m",
                 "description": "Time period for queue length averaging"
               },
               "queue_up_threshold": {
                 "type": "number",
                 "default": 10.0,
                 "description": "Queue length threshold for scaling up"
               },
               "queue_down_threshold": {
                 "type": "number",
                 "default": 2.0,
                 "description": "Queue length threshold for scaling down"
               },
               "min_replicas": {
                 "type": "integer",
                 "default": 1,
                 "description": "Minimum number of replicas to maintain"
               },
               "max_replicas": {
                 "type": "integer",
                 "default": 10,
                 "description": "Maximum number of replicas allowed"
               },
               "cooldown_seconds": {
                 "type": "integer",
                 "default": 120,
                 "description": "Cooldown period in seconds between scaling actions"
               },
               "allow_downscale_with_jobs": {
                 "type": "boolean",
                 "default": true,
                 "description": "Whether to allow downscaling if the candidate instance has jobs in its queue"
               },
               "idle_time_downscale_threshold": {
                 "type": "number",
                 "minimum": 60,
                 "default": 600,
                 "description": "Maximum idle time in seconds before an instance is considered for downscaling due to inactivity"
               }
             }
           },
           "policy_settings": {
           },
           "policy_parameters": {
             "averaging_period": "average_1m",
             "queue_up_threshold": 100.0,
             "queue_down_threshold": 20.0,
             "min_replicas": 1,
             "max_replicas": 3,
             "cooldown_seconds": 120,
             "allow_downscale_with_jobs": true,
             "idle_time_downscale_threshold": 600
           },
           "description": "A policy for queue length based autoscaling that monitors both average and per-instance queue lengths to make intelligent scaling decisions, including downscaling based on idle time.",
           "functionality_data": {
             "strategy": "Queue-based autoscaling",
             "features": ["Hybrid scaling", "Instance-specific monitoring", "Cooldown protection", "Idle time downscaling"]
           },
           "resource_estimates": {
             "cpu_cores": 0.1,
             "memory_mb": 50
           }
         }'