# Person Tracking Parameter Recommendations

## Use Case Overview
Person tracking systems continuously monitor and track individuals across multiple frames, typically used for security surveillance, people counting, behavior analysis, and access control scenarios.

## Core Parameters by Building Block

### Object Detection Parameters
- **conf**: 0.4 (Balanced confidence for reliable person detection)
- **iou**: 0.45 (Standard IoU for person detection)
- **max_dets**: 300 (High detection limit for crowded environments)
- **width**: 416 (Standard input width for person detection)
- **height**: 416 (Standard input height for person detection)

### Tracking Parameters
- **ttl**: 4 (Time-to-live for tracks when person temporarily disappears)
- **sigma_iou**: 0.3 (IoU threshold for associating detections with tracks)
- **sigma_h**: 0.3 (Height similarity threshold for track matching)
- **sigma_l**: 0.1 (Location threshold for track association)
- **t_min**: 2 (Minimum track length before considering valid)
- **iou**: 0.45 (Tracking IoU threshold)

### System Parameters
- **fps**: "1/1" (Standard processing rate for tracking accuracy)
- **use_cuda**: true (GPU acceleration recommended)
- **use_fp16**: true (Half precision for performance)
- **batch_size**: 8 (Standard batch size for object detection)

## Environmental Condition Recommendations

### High Traffic Areas (Malls, Airports, Stations)
```
Object Detection:
- conf: 0.3 (Slightly lower for detecting more people)
- max_dets: 500 (Higher limit for crowded spaces)

Tracking:
- ttl: 6 (Longer persistence for crowded environments)
- sigma_iou: 0.4 (More flexible matching in crowds)
- t_min: 3 (Longer minimum for stable tracks)

System:
- fps: "2/1" (Higher rate for fast-moving crowds)
- batch_size: 16 (Larger batches for efficiency)
```

### Retail Environments
```
Object Detection:
- conf: 0.35 (Higher confidence for customer tracking)
- max_dets: 200 (Moderate crowd handling)

Tracking:
- ttl: 5 (Medium persistence for shopping behavior)
- sigma_h: 0.25 (Stricter height matching for accuracy)

System:
- fps: "3/1" (Higher rate for customer movement analysis)
```

### Office/Corporate Environments
```
Object Detection:
- conf: 0.45 (Higher confidence for controlled environment)
- max_dets: 100 (Lower limit for office spaces)

Tracking:
- ttl: 3 (Shorter persistence for office movement)
- sigma_l: 0.15 (More precise location matching)
- t_min: 1 (Shorter minimum for quick interactions)

System:
- fps: "1/1" (Standard rate for office monitoring)
```

### Outdoor Surveillance
```
Object Detection:
- conf: 0.5 (Higher confidence to reduce false positives)
- width: 640 (Higher resolution for distant people)
- height: 640

Tracking:
- ttl: 8 (Longer persistence for people moving in/out)
- sigma_h: 0.4 (More flexible for perspective changes)
- sigma_l: 0.2 (Adjusted for outdoor movement patterns)

System:
- fps: "1/2" (Lower rate for outdoor monitoring efficiency)
```

## Camera Height Scenarios

### High-Mounted Cameras (8-15m) - Overhead View
```
Object Detection:
- conf: 0.5 (Higher confidence for overhead person detection)
- width: 640 (Higher resolution for smaller person appearance)
- height: 640

Tracking:
- sigma_h: 0.5 (Very flexible height matching for perspective)
- sigma_l: 0.25 (Adjusted for overhead movement patterns)
- ttl: 6 (Longer persistence for perspective challenges)
```

### Standard Height Cameras (3-6m) - Angled View
```
Object Detection:
- conf: 0.4 (Standard confidence for angled views)
- width: 416
- height: 416

Tracking:
- sigma_h: 0.3 (Standard height matching)
- sigma_l: 0.1 (Precise location matching)
- ttl: 4 (Standard persistence)
```

### Low-Mounted Cameras (1-3m) - Eye Level
```
Object Detection:
- conf: 0.35 (Good confidence for eye-level detection)
- max_dets: 50 (Lower limit for limited view)

Tracking:
- ttl: 2 (Shorter persistence for frequent occlusions)
- sigma_h: 0.2 (Stricter height matching at eye level)
- t_min: 1 (Quick track validation)
```

### PTZ Cameras - Dynamic View
```
Object Detection:
- conf: 0.45 (Higher confidence for moving camera)
- max_dets: 150 (Moderate detection limit)

Tracking:
- ttl: 2 (Short persistence due to camera movement)
- sigma_iou: 0.5 (Very flexible matching for PTZ)
- sigma_l: 0.3 (Adjusted for camera movement)
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

Tracking:
- t_min: 3 (Longer validation for accuracy)
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
- conf: 0.5 (Higher confidence to reduce processing)
- max_dets: 100 (Lower detection limit)
- width: 320 (Reduced resolution)
- height: 320

Tracking:
- ttl: 2 (Shorter persistence to save memory)
- t_min: 1 (Quick validation)
```

## Specific Environment Scenarios

### Security Perimeter Monitoring
```
Object Detection:
- conf: 0.5 (High confidence for security accuracy)
- max_dets: 100 (Focus on individual tracking)

Tracking:
- ttl: 10 (Long persistence for perimeter crossing)
- t_min: 5 (Longer validation for security)
- sigma_l: 0.05 (Very precise location tracking)

System:
- fps: "1/1" (Consistent monitoring rate)
```

### People Counting Applications
```
Object Detection:
- conf: 0.3 (Lower confidence to count all people)
- max_dets: 400 (High limit for accurate counting)

Tracking:
- ttl: 3 (Short persistence for counting efficiency)
- t_min: 2 (Standard validation)
- sigma_iou: 0.4 (Flexible for counting accuracy)

System:
- fps: "3/1" (Higher rate for counting accuracy)
```

### Behavior Analysis Systems
```
Object Detection:
- conf: 0.4 (Balanced for behavior detection)
- width: 640 (Higher resolution for behavior details)
- height: 640

Tracking:
- ttl: 8 (Long persistence for behavior analysis)
- t_min: 10 (Long validation for meaningful tracks)
- sigma_h: 0.25 (Precise height matching)

System:
- fps: "2/1" (Moderate rate for behavior analysis)
```

### Access Control Integration
```
Object Detection:
- conf: 0.45 (High confidence for access decisions)
- max_dets: 50 (Limited people in access areas)

Tracking:
- ttl: 5 (Medium persistence for access zones)
- t_min: 3 (Validation for access decisions)
- sigma_l: 0.05 (Very precise for access control)

System:
- fps: "2/1" (Responsive for access control)
```

### Queue Management
```
Object Detection:
- conf: 0.35 (Detect all people in queue)
- max_dets: 200 (Handle queue lengths)

Tracking:
- ttl: 6 (Persistence for queue waiting time)
- t_min: 5 (Longer validation for queue analysis)
- sigma_iou: 0.35 (Flexible for queue movement)

System:
- fps: "1/1" (Standard rate for queue monitoring)
```

## Troubleshooting Common Issues

### Track ID Switching/Fragmentation
```
Tracking:
- sigma_iou: +0.1 (More flexible IoU matching)
- sigma_h: +0.1 (More flexible height matching)
- ttl: +2 (Longer track persistence)
- t_min: -1 (Shorter validation requirement)
```

### Missing Person Detections
```
Object Detection:
- conf: -0.1 (Lower detection confidence)
- max_dets: +100 (Increase detection limit)

System:
- fps: +1 (Higher processing rate)
```

### Too Many False Tracks
```
Object Detection:
- conf: +0.1 (Higher detection confidence)

Tracking:
- t_min: +2 (Longer validation requirement)
- sigma_iou: -0.05 (Stricter IoU matching)
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

### Tracking Failures in Crowds
```
Tracking:
- sigma_iou: +0.15 (Much more flexible matching)
- ttl: +4 (Longer persistence)
- sigma_l: +0.1 (More flexible location matching)

Object Detection:
- max_dets: +200 (Higher detection capacity)
```

## Integration Notes

- Combine with face recognition for identity tracking
- Integrate with access control systems for security
- Use with occupancy counting for capacity management
- Coordinate with behavior analysis for advanced insights
- Link with alert systems for security notifications
- Connect with database systems for track history storage
