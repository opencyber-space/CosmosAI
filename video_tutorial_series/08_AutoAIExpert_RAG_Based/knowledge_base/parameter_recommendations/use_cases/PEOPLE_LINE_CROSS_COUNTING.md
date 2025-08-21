# People Line Cross Counting Parameter Recommendations

## Use Case Overview
People line cross counting systems track individuals crossing defined lines or boundaries, typically used for footfall analysis, access control, occupancy monitoring, and traffic flow measurement in various environments.

## Core Parameters by Building Block

### Object Detection Parameters
- **conf**: 0.4 (Balanced confidence for reliable person detection)
- **nms_iou**: 0.4 (Non-maximum suppression IoU for clean detections)
- **width**: 416 (Standard input width for person detection)
- **height**: 416 (Standard input height for person detection)

### Tracking Parameters
- **ttl**: 4 (Time-to-live for tracks crossing lines)
- **sigma_iou**: 0.3 (IoU threshold for track association)
- **sigma_h**: 0.3 (Height similarity for track matching)
- **sigma_l**: 0.1 (Location threshold for line crossing precision)
- **t_min**: 2 (Minimum track length for valid crossing)
- **iou**: 0.45 (Tracking IoU threshold)

### Line Crossing Specific Parameters
- **zone**: ["Zone1", "Zone2"] (Entry and exit zones for counting)
- **roiPoint**: "mid" (Reference point for crossing detection)
- **position**: "mid" (Midpoint crossing detection)

### System Parameters
- **fps**: "5/1" (Higher frame rate for accurate crossing detection)
- **use_cuda**: true (GPU acceleration recommended)
- **batch_size**: 8 (Standard batch size for object detection)

## Environmental Condition Recommendations

### High Traffic Areas (Malls, Stations, Airports)
```
Object Detection:
- conf: 0.3 (Lower confidence to count all people)
- nms_iou: 0.3 (Aggressive NMS for crowded areas)

Tracking:
- ttl: 6 (Longer persistence for crowded crossings)
- sigma_iou: 0.4 (More flexible matching in crowds)
- t_min: 3 (Longer validation for stable counts)

System:
- fps: "6/1" (Higher rate for fast-moving crowds)
- batch_size: 16 (Larger batches for high throughput)
```

### Retail Store Entrances
```
Object Detection:
- conf: 0.35 (Balanced for customer counting)
- nms_iou: 0.4 (Standard NMS for retail)

Tracking:
- ttl: 5 (Medium persistence for shopping behavior)
- sigma_h: 0.25 (Stricter height matching for accuracy)
- sigma_l: 0.08 (Precise location for entrance counting)

System:
- fps: "4/1" (Good rate for customer flow)
```

### Office/Corporate Buildings
```
Object Detection:
- conf: 0.4 (Higher confidence for controlled environment)

Tracking:
- ttl: 3 (Shorter persistence for office movement)
- sigma_l: 0.05 (Very precise for access control)
- t_min: 1 (Quick validation for office flow)

System:
- fps: "3/1" (Standard rate for office monitoring)
```

### Transportation Gates/Turnstiles
```
Object Detection:
- conf: 0.45 (High confidence for gate accuracy)
- nms_iou: 0.5 (Conservative NMS for precise counting)

Tracking:
- ttl: 2 (Short persistence for gate crossing)
- sigma_l: 0.05 (Very precise for gate validation)
- t_min: 1 (Quick crossing validation)

Line Crossing:
- position: "entry" (Entry point specific detection)

System:
- fps: "5/1" (Responsive for gate control)
```

## Camera Height Scenarios

### High-Mounted Cameras (8-15m) - Overhead Counting
```
Object Detection:
- conf: 0.5 (Higher confidence for overhead person detection)
- width: 640 (Higher resolution for smaller person appearance)
- height: 640

Tracking:
- sigma_h: 0.5 (Very flexible height matching for perspective)
- sigma_l: 0.15 (Adjusted for overhead crossing detection)
- ttl: 8 (Longer persistence for perspective challenges)

Line Crossing:
- roiPoint: "head" (Use head for overhead crossing)
```

### Standard Height Cameras (3-6m) - Angled Counting
```
Object Detection:
- conf: 0.4 (Standard confidence for angled views)
- width: 416
- height: 416

Tracking:
- sigma_h: 0.3 (Standard height matching)
- sigma_l: 0.1 (Standard location precision)
- ttl: 4 (Standard persistence)

Line Crossing:
- roiPoint: "mid" (Midpoint crossing detection)
```

### Low-Mounted Cameras (1-3m) - Eye Level
```
Object Detection:
- conf: 0.35 (Good confidence for eye-level detection)

Tracking:
- ttl: 2 (Shorter persistence for close crossings)
- sigma_h: 0.2 (Stricter height matching at eye level)
- sigma_l: 0.05 (Very precise for close counting)

Line Crossing:
- roiPoint: "center" (Center body mass for eye level)
```

### Wide Angle Cameras - Panoramic Counting
```
Object Detection:
- conf: 0.4 (Balanced for wide area coverage)
- width: 640 (Higher resolution for wide area)
- height: 640

Tracking:
- ttl: 6 (Longer persistence for wide area tracking)
- sigma_l: 0.2 (More flexible for wide angle distortion)

Line Crossing:
- zone: ["Multiple_Zones"] (Multiple crossing points)
```

## Hardware-Specific Optimizations

### High-End GPU (RTX 3080+, A100)
```
System:
- batch_size: 16 (Large batches for high throughput)
- fps: "8/1" (Higher processing rate)

Object Detection:
- width: 640 (Higher resolution processing)
- height: 640

Tracking:
- t_min: 3 (Longer validation for accuracy)
```

### Mid-Range GPU (RTX 2060, GTX 1080)
```
System:
- batch_size: 8 (Balanced batch size)
- fps: "5/1"

Object Detection:
- width: 416 (Standard resolution)
- height: 416
```

### Edge/CPU-Only Devices
```
System:
- batch_size: 1 (Single frame processing)
- use_cuda: false
- fps: "2/1" (Lower processing rate)

Object Detection:
- conf: 0.5 (Higher confidence to reduce processing)
- width: 320 (Reduced resolution)
- height: 320

Tracking:
- ttl: 2 (Shorter persistence to save memory)
- t_min: 1 (Quick validation)
```

## Specific Environment Scenarios

### Event Venues/Stadiums
```
Object Detection:
- conf: 0.3 (Lower confidence for crowd counting)
- nms_iou: 0.35 (Aggressive NMS for crowds)

Tracking:
- ttl: 8 (Long persistence for crowd flow)
- sigma_iou: 0.4 (Flexible for crowd density)

System:
- fps: "6/1" (High rate for crowd management)
```

### Healthcare Facilities
```
Object Detection:
- conf: 0.4 (Balanced for healthcare accuracy)

Tracking:
- ttl: 4 (Standard persistence for patient flow)
- sigma_l: 0.08 (Precise for healthcare compliance)

Line Crossing:
- position: "entry_exit" (Bidirectional healthcare counting)

System:
- fps: "4/1" (Healthcare monitoring rate)
```

### Educational Institutions
```
Object Detection:
- conf: 0.35 (Balanced for student counting)

Tracking:
- ttl: 5 (Medium persistence for student movement)
- t_min: 2 (Standard validation for accuracy)

System:
- fps: "4/1" (School monitoring rate)
```

### Manufacturing/Warehouses
```
Object Detection:
- conf: 0.45 (Higher confidence for industrial accuracy)

Tracking:
- ttl: 3 (Shorter persistence for work flow)
- sigma_l: 0.1 (Precise for industrial counting)

System:
- fps: "3/1" (Industrial monitoring rate)
```

### Public Transportation
```
Object Detection:
- conf: 0.4 (Balanced for transport counting)
- nms_iou: 0.4 (Standard NMS for transport)

Tracking:
- ttl: 4 (Standard persistence for passenger flow)
- sigma_l: 0.1 (Precise for fare control)

Line Crossing:
- zone: ["Platform", "Train"] (Transport specific zones)

System:
- fps: "5/1" (Transport monitoring rate)
```

## Troubleshooting Common Issues

### Inaccurate Counting (Over/Under Counting)
```
Object Detection:
- conf: ±0.05 (Adjust confidence for detection balance)
- nms_iou: ±0.05 (Adjust NMS for cleaner detections)

Tracking:
- sigma_l: -0.02 (More precise location matching)
- t_min: +1 (Longer validation for stability)
```

### Double Counting Issues
```
Tracking:
- ttl: -1 (Shorter track persistence)
- sigma_iou: -0.05 (Stricter track matching)
- sigma_h: -0.05 (Stricter height matching)

Line Crossing:
- position: "precise" (More precise crossing detection)
```

### Missing Crossings
```
Object Detection:
- conf: -0.05 (Lower detection confidence)

Tracking:
- ttl: +2 (Longer track persistence)
- sigma_l: +0.02 (More flexible location matching)
- t_min: -1 (Shorter validation requirement)

System:
- fps: +1 (Higher sampling rate)
```

### Poor Performance
```
System:
- batch_size: /2 (Reduce batch size)
- fps: /2 (Lower processing rate)

Object Detection:
- width: -96 (Reduce resolution)
- height: -96
```

### Crowded Area Tracking Issues
```
Tracking:
- sigma_iou: +0.1 (More flexible IoU matching)
- ttl: +2 (Longer persistence)
- sigma_l: +0.05 (More flexible location matching)

Object Detection:
- nms_iou: -0.05 (Less aggressive NMS)
```

## Integration Notes

- Combine with face recognition for demographic analysis
- Integrate with access control systems for security
- Use with occupancy management for capacity control
- Coordinate with business intelligence for analytics
- Link with alert systems for threshold notifications
- Connect with HVAC systems for occupancy-based control
- Integrate with digital signage for real-time information
