curl -X POST http://MANAGEMENTMASTER:30102/policy \
     -H "Content-Type: application/json" \
     -d '{
           "name": "weightedmetricsloadbalancer",
           "version": "2.0",
           "release_tag": "stable",
           "metadata": {"author": "admin", "category": "load-balancing"},
           "tags": "load-balancing,weighted,metrics,routing",
           "code": "http://MANAGEMENTMASTER:32555/weightedmetricsloadbalancer.zip",
           "code_type": "zip",
           "type": "policy",
           "policy_input_schema": {
             "type": "object",
             "properties": {
               "instances": {
                 "type": "array",
                 "items": {"type": "string"},
                 "description": "List of available instance IDs for routing"
               },
               "packet": {
                 "type": "object",
                 "description": "Packet containing session information",
                 "properties": {
                   "session_id": {
                     "type": "string",
                     "description": "Session ID for request tracking"
                   }
                 }
               },
               "request": {
                 "type": "object",
                 "description": "Request details for routing decision",
                 "properties": {
                   "response_preference": {
                     "type": "string",
                     "enum": ["fast", "balanced", "thoughtful"],
                     "description": "User preference for response speed/length"
                   },
                   "requested_tokens_per_second": {
                     "type": "number",
                     "minimum": 0,
                     "description": "Specific tokens/second rate requested by user"
                   }
                 }
               }
             },
             "required": ["instances"]
           },
           "policy_output_schema": {
             "type": "object",
             "properties": {
               "instance_id": {"type": "string"},
               "weighted_score": {"type": "number"},
               "metrics_used": {"type": "object"},
               "reason": {"type": "string"}
             }
           },
           "policy_settings_schema": {
             "type": "object",
             "properties": {
               "get_metrics": {
                 "type": "object",
                 "description": "Function to retrieve block metrics"
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
                 "description": "Time period for metric averaging"
               },
               "tie_breaker": {
                 "type": "string",
                 "enum": ["first", "round_robin"],
                 "default": "first",
                 "description": "Strategy for breaking ties when multiple instances have similar scores"
               },
               "weights": {
                 "type": "object",
                 "description": "Weights for different metrics (should sum to 1.0)",
                 "properties": {
                   "active_sessions": {
                     "type": "number",
                     "minimum": 0,
                     "maximum": 1,
                     "default": 0.5,
                     "description": "Weight for active sessions metric"
                   },
                   "queue_length": {
                     "type": "number",
                     "minimum": 0,
                     "maximum": 1,
                     "default": 0.5,
                     "description": "Weight for queue length metric"
                   },
                   "latency": {
                     "type": "number",
                     "minimum": 0,
                     "maximum": 1,
                     "default": 0.0,
                     "description": "Weight for latency metric"
                   },
                   "tokens_per_second": {
                     "type": "number",
                     "minimum": 0,
                     "maximum": 1,
                     "default": 0.0,
                     "description": "Weight for tokens per second metric"
                   },
                   "requested_tokens_per_second": {
                     "type": "number",
                     "minimum": 0,
                     "maximum": 1,
                     "default": 0.0,
                     "description": "Weight for requested tokens per second preference matching"
                   },
                   "memory_usage_percent": {
                     "type": "number",
                     "minimum": 0,
                     "maximum": 1,
                     "default": 0.0,
                     "description": "Weight for memory usage metric"
                   },
                   "cpu_usage_percent": {
                     "type": "number",
                     "minimum": 0,
                     "maximum": 1,
                     "default": 0.0,
                     "description": "Weight for CPU usage metric"
                   },
                   "gpu_usage_percent": {
                     "type": "number",
                     "minimum": 0,
                     "maximum": 1,
                     "default": 0.0,
                     "description": "Weight for GPU usage metric"
                   }
                 }
               },
               "metric_configs": {
                 "type": "object",
                 "description": "Configuration for each metric",
                 "properties": {
                   "active_sessions": {
                     "type": "object",
                     "properties": {
                       "max_threshold": {"type": "number", "default": 10},
                       "invert_score": {"type": "boolean", "default": true}
                     }
                   },
                   "queue_length": {
                     "type": "object",
                     "properties": {
                       "max_threshold": {"type": "number", "default": 20},
                       "invert_score": {"type": "boolean", "default": true}
                     }
                   },
                   "latency": {
                     "type": "object",
                     "properties": {
                       "max_threshold": {"type": "number", "default": 5000},
                       "invert_score": {"type": "boolean", "default": true}
                     }
                   },
                   "tokens_per_second": {
                     "type": "object",
                     "properties": {
                       "max_threshold": {"type": "number", "default": 100},
                       "invert_score": {"type": "boolean", "default": false}
                     }
                   },
                   "requested_tokens_per_second": {
                     "type": "object",
                     "properties": {
                       "max_threshold": {"type": "number", "default": 100},
                       "invert_score": {"type": "boolean", "default": false}
                     }
                   },
                   "memory_usage_percent": {
                     "type": "object",
                     "properties": {
                       "max_threshold": {"type": "number", "default": 90},
                       "invert_score": {"type": "boolean", "default": true}
                     }
                   },
                   "cpu_usage_percent": {
                     "type": "object",
                     "properties": {
                       "max_threshold": {"type": "number", "default": 80},
                       "invert_score": {"type": "boolean", "default": true}
                     }
                   },
                   "gpu_usage_percent": {
                     "type": "object",
                     "properties": {
                       "max_threshold": {"type": "number", "default": 90},
                       "invert_score": {"type": "boolean", "default": true}
                     }
                   }
                 }
               },
               "user_preference_config": {
                 "type": "object",
                 "description": "Configuration for user response preference matching",
                 "properties": {
                   "response_speed_preference": {
                     "type": "string",
                     "enum": ["fast", "balanced", "thoughtful"],
                     "default": "balanced",
                     "description": "Default response speed preference when not specified in request"
                   },
                   "fast_threshold": {
                     "type": "number",
                     "default": 50,
                     "description": "Tokens/second threshold above which instances are considered fast"
                   },
                   "thoughtful_threshold": {
                     "type": "number",
                     "default": 20,
                     "description": "Tokens/second threshold below which instances are considered thoughtful"
                   }
                 }
               },
               "redistribution_percentage": {
                 "type": "number",
                 "minimum": 0,
                 "maximum": 1,
                 "default": 0.2,
                 "description": "Percentage of sessions to redistribute when new instances are added (0.0 to 1.0)"
               },
               "redistribution_interval": {
                 "type": "number",
                 "minimum": 60,
                 "default": 300,
                 "description": "Interval in seconds for periodic redistribution (minimum 60 seconds)"
               },
               "redistribution_selection_mode": {
                 "type": "string",
                 "enum": ["random", "best", "least_loaded"],
                 "default": "random",
                 "description": "Mode for selecting target instance during redistribution: 'random' for random choice, 'best' for best weighted score, 'least_loaded' for instance with fewest sessions (or least queue length if selection_mode is 'equal')"
               },
               "selection_mode": {
                 "type": "string",
                 "enum": ["weighted", "equal"],
                 "default": "weighted",
                 "description": "Mode for instance selection: 'weighted' uses metrics scoring, 'equal' selects based on least queue length for balance"
               },
               "imbalance_threshold": {
                 "type": "number",
                 "minimum": 0,
                 "default": 1,
                 "description": "Skip redistribution if the maximum-minimum difference across instances is <= this threshold. Uses queue_length difference in 'equal' mode, session count difference in 'weighted' mode"
               },
               "task_imbalance_threshold": {
                 "type": "number",
                 "minimum": 0,
                 "default": 10,
                 "description": "Threshold for task count imbalance to trigger redistribution when metrics are not available"
               },
               "overload_threshold_percentage": {
                 "type": "number",
                 "minimum": 0,
                 "default": 0.2,
                 "description": "Percentage above average queue length to consider an instance overloaded (e.g., 0.1 for 10% above average). Default 0.2 means 20% above average qualifies as overloaded"
               },
               "session_timeout_seconds": {
                 "type": "number",
                 "minimum": 60,
                 "default": 3600,
                 "description": "Maximum time in seconds to keep a session in cache before automatic cleanup (minimum 60 seconds, default 1 hour)"
               },
               "metrics_interval": {
                 "type": "number",
                 "minimum": 5,
                 "default": 60,
                 "description": "Interval in seconds to poll metrics; metrics are refreshed only if this interval has elapsed or when the instance list changes (default 60 seconds)"
               }
             }
           },
           "policy_settings": {
           },
           "policy_parameters": {
             "averaging_period": "average_1m",
             "tie_breaker": "round_robin",
             "weights": {
               "active_sessions": 0.1,
               "queue_length": 0.9,
               "latency": 0.0,
               "requested_tokens_per_second": 0.0
             },
             "metric_configs": {
               "active_sessions": {"max_threshold": 10, "invert_score": true},
               "queue_length": {"max_threshold": 20, "invert_score": true},
               "latency": {"max_threshold": 5000, "invert_score": true}
             },
             "user_preference_config": {
               "response_speed_preference": "balanced",
               "fast_threshold": 50,
               "thoughtful_threshold": 20
             },
             "redistribution_percentage": 0.2,
             "redistribution_interval": 300,
             "redistribution_selection_mode": "random",
             "selection_mode": "weighted",
             "imbalance_threshold": 1,
             "task_imbalance_threshold": 10,
             "overload_threshold_percentage": 0.2,
             "session_timeout_seconds": 3600,
             "metrics_interval": 60
           },
           "description": "A load balancer policy focused on queue length and active sessions, routing requests based on weighted combination of these metrics for optimal load distribution. Supports equal distribution mode for perfect balance based on queue length and configurable imbalance thresholds to avoid unnecessary redistribution. Includes automatic session timeout management to prevent cache bloat.",
           "functionality_data": {
             "strategy": "Weighted load balancing based on queue length and active sessions, with options for equal distribution and intelligent redistribution controls",
             "features": ["Weighted scoring", "Queue length metric", "Active sessions metric", "Configurable thresholds", "Tie-breaking mechanisms", "Equal distribution mode", "Imbalance threshold for redistribution", "Automatic session timeout management"]
           },
           "resource_estimates": {
             "cpu_cores": 0.1,
             "memory_mb": 50
           }
         }'
