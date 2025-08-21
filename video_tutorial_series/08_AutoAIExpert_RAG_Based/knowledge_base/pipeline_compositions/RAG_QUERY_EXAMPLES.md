# RAG Query Examples for Pipeline Generation

This document provides example queries and their expected complete pipeline responses to improve RAG retrieval quality.

## Example 1: Basic Loitering Detection

### Query:
"Build a loitering detection pipeline for surveillance cameras"

### Expected Complete Response:
```
Pipeline Architecture: Camera Input → Person Detection → Zone Filtering → Tracking → Loitering Detection → Alerts

Complete Pipeline Configuration:
1. Camera Input
   - fps: "5/1"
   - resolution: 1024x1024
   - format: BGR

2. Person Detection (YOLOv8)
   - conf: 0.4
   - width: 1024
   - height: 1024
   - max_dets: 100

3. Zone Filtering
   - zones: ["ZoneLoitering"]
   - filter_type: "inside_zone"
   - classes: ["person"]

4. Person Tracking
   - ttl: 8
   - sigma_iou: 0.3
   - sigma_h: 0.3
   - t_min: 3

5. Loitering Detection Logic
   - loiteringThresholdSeconds: 120
   - alert_interval: 600
   - severity: "high"

6. Alert System
   - alert_url: security system
   - storage: mongodb
   - real_time: true
```

## Example 2: ATM Loitering Detection

### Query:
"Create a loitering detection system for ATM surveillance with 60-second threshold"

### Expected Complete Response:
```
ATM Loitering Detection Pipeline:
Camera → Person Detection → ATM Zone Filter → Tracking → 60s Loitering Logic → Security Alerts

Detailed Configuration:
1. ATM Camera Input
   - fps: "3/1" (optimized for ATM monitoring)
   - resolution: 1024x1024
   - night_vision: enabled

2. Person Detection
   - conf: 0.6 (higher confidence for ATM security)
   - model: YOLOv8m
   - max_dets: 50

3. ATM Zone Filtering
   - zones: ["ATMPerimeter", "QueueArea"]
   - buffer_distance: 2.0 meters
   - priority_zones: true

4. Person Tracking
   - ttl: 10 (extended for ATM analysis)
   - sigma_iou: 0.4
   - t_min: 5

5. Loitering Detection (60s threshold)
   - loiteringThresholdSeconds: 60
   - alert_interval: 300
   - severity: "high"
   - immediate_escalation: true

Hardware Requirements:
- GPU: RTX 3060 or better
- Memory: 8GB RAM minimum
- Storage: SSD for alert logs
```

## Example 3: High-Performance Real-Time Detection

### Query:
"I need 50+ FPS object detection on T4 GPU for real-time processing"

### Expected Complete Response:
```
High-Performance Detection Pipeline:
Camera → YOLOv8n (optimized) → Post-Processing → Real-Time Output

Optimized Configuration:
1. High-Speed Camera Input
   - fps: "60/1"
   - resolution: 640x640 (optimized for speed)
   - buffer_size: minimal

2. YOLOv8n Detection (Speed Optimized)
   - model: YOLOv8n (nano - fastest variant)
   - conf: 0.25
   - width: 640
   - height: 640
   - batch_size: 8
   - use_fp16: true
   - max_dets: 100

3. Minimal Post-Processing
   - nms_iou: 0.45
   - filter_classes: as needed
   - no_tracking: true (for maximum speed)

4. System Optimization
   - use_cuda: true
   - tensorrt: enabled
   - memory_pool: optimized
   - concurrent_inference: true

Expected Performance:
- T4 GPU: 130+ FPS @ 640x640
- Latency: <8ms per frame
- Memory: ~2GB GPU memory
```

## Example 4: Multi-Use Case Security System

### Query:
"Design a comprehensive security pipeline with intrusion detection, loitering, and weapon detection"

### Expected Complete Response:
```
Multi-Use Case Security Pipeline:
Camera → Multi-Object Detection → Parallel Processing → [Intrusion | Loitering | Weapon] → Unified Alerts

Architecture:
1. Security Camera Input
   - fps: "5/1"
   - resolution: 1920x1080
   - multiple_streams: true

2. Multi-Object Detection Hub
   - person_detector: YOLOv8m
   - weapon_detector: specialized model
   - conf_person: 0.4
   - conf_weapon: 0.7

3. Parallel Use Case Processing:

   A. Intrusion Detection Branch:
      - zone_filter: perimeter zones
      - line_crossing: boundary detection
      - alert_interval: 60
      - severity: "medium"

   B. Loitering Detection Branch:
      - zone_filter: restricted areas
      - tracking: ttl=8
      - threshold: 120 seconds
      - severity: "high"

   C. Weapon Detection Branch:
      - person_weapon_association: true
      - immediate_alert: true
      - severity: "critical"

4. Unified Alert System
   - priority_routing: by severity
   - escalation_rules: configured
   - multi_channel: sms, email, dashboard
```

## Example 5: Edge Device Deployment

### Query:
"Create a loitering detection pipeline for edge devices with limited compute"

### Expected Complete Response:
```
Edge-Optimized Loitering Pipeline:
Camera → Lightweight Detection → Simple Tracking → Loitering Logic → Local Alerts

Edge Configuration:
1. Edge Camera Input
   - fps: "2/1" (reduced for edge performance)
   - resolution: 640x480
   - compression: high

2. Lightweight Detection
   - model: YOLOv8n or MobileNet
   - conf: 0.5
   - width: 640
   - height: 480
   - use_fp16: false (CPU compatibility)
   - batch_size: 1

3. Simple Tracking
   - tracker: lightweight (SORT/IoU)
   - ttl: 6
   - minimal_features: true

4. Loitering Detection
   - loiteringThresholdSeconds: 90
   - alert_interval: 600
   - local_storage: true

5. Edge Optimizations
   - use_cuda: false
   - cpu_threads: 4
   - memory_limit: 2GB
   - offline_capable: true

Hardware Requirements:
- CPU: ARM Cortex-A78 or x86 equivalent
- RAM: 4GB minimum
- Storage: 32GB eMMC
- Power: <15W
```

## Query Pattern Guidelines

### Effective Query Patterns:
1. **Specific Use Case**: "Build a [use_case] pipeline for [environment]"
2. **Performance Requirements**: "I need [metric] on [hardware]"
3. **Environmental Constraints**: "Create [use_case] for [lighting/weather/crowd] conditions"
4. **Hardware Specific**: "Design [use_case] for [GPU/CPU/edge] deployment"
5. **Multi-Feature**: "Combine [use_case1] and [use_case2] in one pipeline"

### Response Structure:
1. **Pipeline Overview**: High-level architecture diagram
2. **Detailed Components**: Each stage with specific parameters
3. **Configuration**: JSON or parameter tables
4. **Hardware Requirements**: Minimum and recommended specs
5. **Performance Expectations**: FPS, latency, accuracy metrics
6. **Integration Notes**: How components connect and communicate

### Keywords for Better Retrieval:
- **Architecture terms**: pipeline, components, stages, flow
- **Technical specs**: parameters, configuration, settings
- **Performance**: FPS, latency, throughput, accuracy
- **Hardware**: GPU, CPU, edge, memory, compute
- **Use cases**: loitering, intrusion, tracking, detection
- **Environment**: indoor, outdoor, low-light, high-traffic

This structure ensures RAG queries return complete, actionable pipeline designs rather than fragmented information.
