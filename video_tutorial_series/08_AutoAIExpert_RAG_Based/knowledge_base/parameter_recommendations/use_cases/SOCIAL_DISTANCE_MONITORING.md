# Social Distance Monitoring Parameter Recommendations

## Use Case Overview
Social distance monitoring systems detect and alert when people maintain insufficient physical distance, typically used in public health compliance, workplace safety, and crowd management scenarios.

## Core Parameters by Building Block

### Object Detection Parameters
- **conf**: 0.2 (Lower confidence to detect more people in crowded environments)
- **iou**: 0.45 (Standard IoU for person detection balance)
- **max_dets**: 300 (High detection limit for crowded areas)
- **width**: 416 (Standard input width for person detection)
- **height**: 416 (Standard input height for person detection)

### Tracking Parameters
- **ttl**: 4 (Moderate track persistence for people movement)
- **sigma_iou**: 0.3 (Standard IoU threshold for track association)
- **sigma_h**: 0.3 (Height similarity threshold for track matching)
- **sigma_l**: 0.1 (Lower location threshold for stationary people)
- **t_min**: 2 (Minimum track length before analysis)
- **iou**: 0.45 (Tracking IoU threshold)

### Social Distance Specific Parameters
- **window**: 30 (Time window in seconds for distance analysis)
- **min_people**: 5 (Minimum people count to trigger distance monitoring)
- **distance_realworld**: 1.8 (Required distance in meters - WHO standard)
- **violation_percentage**: 50 (Percentage of violations to trigger alert)
- **alert_type**: "zone" (Alert type for zone-based monitoring)
- **alert_interval**: 120 (Alert frequency in seconds)
- **severity**: "medium" (Alert severity level)

### System Parameters
- **fps**: "2/1" (Lower fps for processing efficiency in crowded areas)
- **use_cuda**: true (GPU acceleration recommended)
- **use_fp16**: true (Half precision for performance)
- **batch_size**: 8 (Standard batch size for object detection)

## Environmental Condition Recommendations

### High Density Areas (Malls, Airports, Stations)
```
Object Detection:
- conf: 0.15 (Lower confidence to catch all people)
- max_dets: 500 (Higher detection limit for crowds)

Social Distance:
- min_people: 10 (Higher threshold for busy areas)
- violation_percentage: 60 (More lenient in high-traffic areas)
- distance_realworld: 1.5 (Reduced distance for practical enforcement)
- alert_interval: 180 (Less frequent alerts to avoid spam)

System:
- fps: "1/1" (Lower fps to handle computational load)
- batch_size: 16 (Larger batches for efficiency)
```

### Office/Workplace Environments
```
Object Detection:
- conf: 0.25 (Higher confidence for controlled environment)
- max_dets: 100 (Lower limit for office spaces)

Social Distance:
- min_people: 3 (Lower threshold for smaller groups)
- violation_percentage: 30 (Stricter enforcement in workplace)
- distance_realworld: 2.0 (WHO recommended distance)
- alert_interval: 60 (More frequent monitoring)

System:
- fps: "3/1" (Higher fps for responsive monitoring)
```

### Outdoor Public Spaces
```
Object Detection:
- conf: 0.3 (Higher confidence to reduce false positives)
- width: 640 (Higher resolution for distant people)
- height: 640

Tracking:
- ttl: 6 (Longer persistence for people moving in/out of frame)
- sigma_h: 0.4 (More flexible height matching for perspective)

Social Distance:
- distance_realworld: 2.0 (Standard outdoor distance)
- window: 45 (Longer analysis window for outdoor movement)
```

## Camera Height Scenarios

### High-Mounted Cameras (8-15m) - Overhead View
```
Object Detection:
- conf: 0.35 (Higher confidence needed for overhead detection)
- width: 640 (Higher resolution for smaller person appearance)
- height: 640

Tracking:
- sigma_h: 0.5 (More flexible height matching for perspective distortion)
- sigma_l: 0.2 (Adjusted for overhead movement patterns)

Social Distance:
- distance_realworld: 1.5 (Adjusted for perspective scaling)
```

### Standard Height Cameras (3-6m) - Angled View
```
Object Detection:
- conf: 0.2 (Standard confidence for angled views)
- width: 416
- height: 416

Social Distance:
- distance_realworld: 1.8 (Standard WHO distance)
```

### Low-Mounted Cameras (1-3m) - Eye Level
```
Object Detection:
- conf: 0.25 (Good confidence for eye-level detection)
- max_dets: 50 (Lower limit as fewer people visible)

Tracking:
- ttl: 3 (Shorter persistence for frequent occlusions)

Social Distance:
- distance_realworld: 2.0 (Full distance visible at eye level)
```

## Hardware-Specific Optimizations

### High-End GPU (RTX 3080+, A100)
```
System:
- batch_size: 16 (Large batches for maximum throughput)
- use_fp16: true
- fps: "4/1" (Higher processing rate)

Object Detection:
- width: 640 (Higher resolution processing)
- height: 640
- max_dets: 500 (Process more detections)
```

### Mid-Range GPU (RTX 2060, GTX 1080)
```
System:
- batch_size: 8 (Balanced batch size)
- use_fp16: true
- fps: "2/1"

Object Detection:
- width: 416 (Standard resolution)
- height: 416
- max_dets: 300
```

### Edge/CPU-Only Devices
```
System:
- batch_size: 1 (Single frame processing)
- use_cuda: false
- use_fp16: false
- fps: "1/2" (Lower processing rate)

Object Detection:
- conf: 0.4 (Higher confidence to reduce processing)
- max_dets: 100 (Lower detection limit)
- width: 320 (Reduced resolution)
- height: 320
```

## Specific Environment Scenarios

### Healthcare Facilities
```
Social Distance:
- distance_realworld: 2.0 (Medical spacing requirements)
- violation_percentage: 20 (Strict enforcement)
- severity: "high" (Health priority)
- alert_interval: 30 (Immediate response needed)
- min_people: 2 (Monitor any gathering)
```

### Educational Institutions
```
Social Distance:
- distance_realworld: 1.5 (Practical for classroom settings)
- violation_percentage: 40 (Balanced for learning environment)
- window: 60 (Longer observation for natural classroom movement)
- min_people: 8 (Classroom group threshold)
```

### Manufacturing/Warehouses
```
Object Detection:
- conf: 0.3 (Higher confidence in industrial environment)

Social Distance:
- distance_realworld: 1.8 (Standard workplace distance)
- violation_percentage: 35 (Moderate enforcement)
- alert_type: "zone" (Zone-based for work areas)
```

### Retail Environments
```
Object Detection:
- max_dets: 200 (Moderate crowd handling)

Social Distance:
- min_people: 4 (Small group threshold)
- violation_percentage: 45 (Customer-friendly enforcement)
- distance_realworld: 1.5 (Practical for shopping)
- alert_interval: 300 (Less frequent alerts for customer comfort)
```

### Public Transportation
```
Object Detection:
- conf: 0.2 (Detect all passengers)
- max_dets: 400 (High capacity vehicles)

Social Distance:
- distance_realworld: 1.0 (Reduced for transit reality)
- violation_percentage: 70 (Very lenient for practical use)
- window: 15 (Shorter window for transit movement)
```

## Troubleshooting Common Issues

### Too Many False Alerts
```
Social Distance:
- violation_percentage: +20 (Increase tolerance)
- alert_interval: +60 (Reduce alert frequency)
- min_people: +2 (Raise group threshold)
```

### Missing Distance Violations
```
Object Detection:
- conf: -0.1 (Lower detection confidence)
- max_dets: +100 (Increase detection limit)

Social Distance:
- violation_percentage: -10 (Stricter threshold)
```

### Poor Performance
```
System:
- batch_size: /2 (Reduce batch size)
- fps: /2 (Lower processing rate)

Object Detection:
- width: -96 (Reduce resolution)
- height: -96
- max_dets: -100 (Fewer detections)
```

### Tracking Issues in Crowds
```
Tracking:
- ttl: +2 (Longer track persistence)
- sigma_iou: +0.1 (More flexible matching)
- t_min: -1 (Shorter minimum track length)
```

## Integration Notes

- Combine with face mask detection for comprehensive health monitoring
- Integrate with access control systems for compliance enforcement
- Use with occupancy counting for density management
- Coordinate with HVAC systems for air circulation optimization
- Link with announcement systems for real-time guidance
