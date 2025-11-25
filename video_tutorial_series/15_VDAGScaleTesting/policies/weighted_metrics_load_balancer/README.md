# Weighted Metrics Load Balancer Policy

An advanced load balancer policy for AI inference systems that routes requests to optimal instances based on weighted combination of multiple metrics, with intelligent session management and redistribution for even load distribution.

## Overview

This policy provides sophisticated load balancing for distributed AI model serving, ensuring high availability, optimal resource utilization, and user preference matching. It combines real-time metrics evaluation with session-aware routing and automatic load redistribution.

## Key Features

- **Multi-Metric Load Balancing**: Combines active sessions, queue length, latency, tokens/second, and hardware utilization
- **Session Stickiness**: Caches sessions to instances for consistency and reduced overhead
- **Automatic Redistribution**: Rebalances sessions when new instances are added or periodically
- **User Preference Matching**: Routes based on desired response speed (fast/thoughtful/balanced)
- **Configurable Selection Modes**: Choose between random or best-instance selection during redistribution
- **Task Count Tracking**: Prioritizes redistribution of sessions with fewer tasks
- **Extensible Metrics**: Easy to add new performance indicators

## Overall Flow

### 1. Initialization
- Policy loads configuration parameters (weights, thresholds, redistribution settings)
- Initializes session cache and task count tracking
- Sets up logging and metric configurations

### 2. Request Evaluation
For each incoming request:

1. **Instance Update Check**: Detects changes in available instances
   - If new instances added: Triggers redistribution of sessions from overloaded instances
   - If periodic interval reached: Triggers redistribution across all instances

2. **Session Cache Lookup**: Checks if request belongs to existing session
   - If cached: Routes to cached instance (if still available)
   - If not cached: Proceeds to metric-based selection

3. **Metric Collection**: Retrieves real-time metrics from all available instances
   - Active sessions, queue length, latency, tokens/second, hardware usage

4. **Weighted Scoring**: Calculates composite score for each instance
   - Normalizes each metric to 0-1 scale
   - Applies configured weights to create final score
   - Higher score = better instance for routing

5. **Instance Selection**: Chooses optimal instance
   - Selects instance with highest weighted score
   - Applies tie-breaking if multiple instances have similar scores

6. **Session Caching**: Stores session-to-instance mapping for future requests
   - Increments task count for the session

### 3. Session Redistribution
Triggered by:
- **Event-driven**: When new instances are detected
- **Periodic**: Every configured interval (default 5 minutes)

Process:
1. Identifies overloaded instances (above average sessions)
2. Selects sessions to redistribute (prioritizing low-task-count sessions)
3. Chooses target instances using configured selection mode:
   - **Random**: Random selection from available targets
   - **Best**: Selects instance with best weighted score
4. Updates session cache with new mappings
5. Logs redistribution details for monitoring

### 4. Management Operations
- **Health Check**: Returns current instance list and status
- **Session Mapping**: Provides current session-to-instance mappings
- **Streaming Assignment**: Pre-allocates instances for streaming sessions

## Configuration Parameters

### Core Parameters
```json
{
  "weights": {
    "active_sessions": 0.5,
    "queue_length": 0.5,
    "latency": 0.0,
    "requested_tokens_per_second": 0.0
  },
  "averaging_period": "average_1m",
  "tie_breaker": "first"
}
```

### Redistribution Parameters
```json
{
  "redistribution_percentage": 0.2,
  "redistribution_interval": 300,
  "redistribution_selection_mode": "random"
}
```

### User Preference Configuration
```json
{
  "user_preference_config": {
    "response_speed_preference": "balanced",
    "fast_threshold": 50,
    "thoughtful_threshold": 20
  }
}
```

### Metric Thresholds
```json
{
  "metric_configs": {
    "active_sessions": {"max_threshold": 100, "invert_score": true},
    "queue_length": {"max_threshold": 1000, "invert_score": true}
  }
}
```

## User Preference Matching

### Response Speed Options

1. **Fast Response** (`"response_preference": "fast"`)
   - Routes to instances with high tokens/second (>50)
   - Best for: Quick answers, summaries, simple queries

2. **Thoughtful Response** (`"response_preference": "thoughtful"`)
   - Routes to instances with low tokens/second (<20)
   - Best for: Detailed analysis, complex reasoning, creative tasks

3. **Balanced Response** (`"response_preference": "balanced"`)
   - Routes to instances with moderate tokens/second (20-50)
   - Best for: General purpose, balanced speed/quality

4. **Exact Rate** (`"requested_tokens_per_second": 40`)
   - Matches specific desired tokens/second rate

## Supported Metrics

- `llm_active_sessions`: Current active sessions
- `queue_length`: Request queue depth
- `latency`: Response time
- `llm_tokens_per_second`: Generation throughput
- `memory_usage_percent`: Memory utilization
- `cpu_usage_percent`: CPU utilization
- `gpu_usage_percent`: GPU utilization
- `requested_tokens_per_second`: User preference score

## Deployment

```bash
./register.bash
```

## Example Usage

### Request with User Preference
```json
{
  "instances": ["inst1", "inst2", "inst3"],
  "packet": {"session_id": "session123"},
  "request": {
    "response_preference": "fast"
  }
}
```

### Response
```json
{
  "instance_id": "inst2",
  "reason": "Selected based on weighted metrics and user preference"
}
```

## Monitoring and Logging

The policy provides detailed logging for:
- Instance selection decisions
- Redistribution events (sessions moved, reasons, targets)
- Metric values and scoring
- Cache operations
- Error conditions

Use logs to monitor load distribution effectiveness and adjust weights/thresholds as needed.
