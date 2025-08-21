# Stone Throwing Detection Parameter Recommendations

## Use Case Overview
Stone throwing detection systems identify throwing motions and projectile behaviors, typically used for public safety, riot control, property protection, and security monitoring in high-risk areas.

## Core Parameters by Building Block

### Pose Detection Parameters
- **conf**: 0.25 (Lower confidence to detect throwing motions)
- **modeltype**: "model_medium" (Balanced accuracy for pose tracking)
- **decoder_width**: 640 (High resolution for throwing motion detail)
- **decoder_height**: 640 (High resolution for arm movement precision)

### Stone Throwing Specific Parameters
- **window**: 30 (Time window in seconds for throwing analysis)
- **violation_window**: 20 (Time window for violation detection)
- **violation_percentage**: 80 (Percentage of violation actions to trigger alert)
- **ppl_count**: 3 (Number of people performing throwing actions)
- **angle_ranges**: Arm angle analysis for throwing motion detection
  - **right_wrist_elbow**: [] (Wrist to elbow angle ranges)
  - **right_elbow_shoulder**: [] (Elbow to shoulder angle ranges)
- **alert_interval**: 300 (Alert frequency in seconds - 5 minutes)
- **severity**: "high" (High priority for public safety)

### System Parameters
- **fps**: "5/1" (Higher frame rate for motion capture)
- **use_cuda**: true (GPU acceleration recommended)
- **use_fp16**: true (Half precision for performance)
- **batch_size**: 4 (Smaller batch for pose processing)

## Environmental Condition Recommendations

### Riot/Protest Areas
```
Pose Detection:
- conf: 0.2 (Very sensitive to catch all throwing motions)
- decoder_width: 640 (High resolution for crowd monitoring)
- decoder_height: 640

Stone Throwing:
- window: 15 (Shorter window for rapid response)
- violation_window: 10 (Quick violation detection)
- violation_percentage: 60 (Lower threshold for riot situations)
- ppl_count: 2 (Lower threshold for immediate response)
- alert_interval: 60 (Immediate alerts - 1 minute)
- severity: "critical" (Highest priority for public safety)

System:
- fps: "6/1" (Higher rate for dynamic crowd situations)
- batch_size: 8 (Larger batch for crowd processing)
```

### School/Educational Premises
```
Pose Detection:
- conf: 0.3 (Balanced confidence for school environment)

Stone Throwing:
- window: 45 (Longer observation for school context)
- violation_window: 30 (Moderate validation time)
- violation_percentage: 70 (Moderate threshold for educational setting)
- ppl_count: 1 (Single student can trigger alert)
- alert_interval: 120 (School response time - 2 minutes)
- severity: "high" (Educational safety priority)

System:
- fps: "4/1" (Standard school monitoring rate)
```

### Public Transportation Areas
```
Pose Detection:
- conf: 0.35 (Higher confidence for busy transport areas)

Stone Throwing:
- window: 20 (Quick detection for transport safety)
- violation_window: 15 (Rapid validation)
- violation_percentage: 75 (Moderate threshold for crowded areas)
- ppl_count: 3 (Group threshold for transport incidents)
- alert_interval: 90 (Transport security response time)
- severity: "critical" (Transport safety priority)

System:
- fps: "5/1" (Active transport monitoring)
```

### Private Property/Construction Sites
```
Pose Detection:
- conf: 0.4 (Higher confidence to avoid false alarms)

Stone Throwing:
- window: 60 (Longer observation for property context)
- violation_window: 40 (Extended validation)
- violation_percentage: 85 (Higher threshold for precision)
- ppl_count: 2 (Small group threshold)
- alert_interval: 180 (Property response time - 3 minutes)
- severity: "medium" (Property protection priority)

System:
- fps: "3/1" (Standard property monitoring)
```

## Camera Height Scenarios

### High-Mounted Cameras (8-15m) - Overhead Surveillance
```
Pose Detection:
- conf: 0.4 (Higher confidence for overhead throwing detection)
- decoder_width: 640 (High resolution for distant throwing motions)
- decoder_height: 640

Stone Throwing:
- violation_percentage: 70 (Adjusted for overhead perspective challenges)
- window: 40 (Longer window for overhead validation)
- angle_ranges: [adjusted for overhead perspective]
```

### Standard Height Cameras (3-6m) - Angled Monitoring
```
Pose Detection:
- conf: 0.25 (Standard confidence for angled views)
- decoder_width: 640
- decoder_height: 640

Stone Throwing:
- window: 30 (Standard observation window)
- violation_percentage: 80 (Standard threshold)
```

### Low-Mounted Cameras (1-3m) - Close Range
```
Pose Detection:
- conf: 0.3 (Good confidence for close-range detection)
- decoder_width: 480 (Lower resolution acceptable at close range)
- decoder_height: 480

Stone Throwing:
- window: 20 (Shorter window for close interaction)
- violation_window: 15 (Quick validation at close range)
- ppl_count: 1 (Single person threshold for close monitoring)
```

### PTZ Cameras - Active Tracking
```
Pose Detection:
- conf: 0.45 (Higher confidence for moving camera)

Stone Throwing:
- violation_percentage: 75 (Adjusted for camera movement)
- window: 25 (Shorter window for PTZ dynamics)
- alert_interval: 120 (Quick PTZ response)

System:
- fps: "6/1" (Higher rate for PTZ responsiveness)
```

## Hardware-Specific Optimizations

### High-End GPU (RTX 3080+, A100)
```
System:
- batch_size: 8 (Larger batches for pose processing)
- use_fp16: true
- fps: "8/1" (Higher processing rate)

Pose Detection:
- decoder_width: 640 (High resolution processing)
- decoder_height: 640
- modeltype: "model_large" (Use larger model if available)

Stone Throwing:
- window: 45 (Longer analysis window for accuracy)
- violation_window: 30 (Extended validation)
```

### Mid-Range GPU (RTX 2060, GTX 1080)
```
System:
- batch_size: 4 (Balanced batch size)
- use_fp16: true
- fps: "5/1"

Pose Detection:
- decoder_width: 640
- decoder_height: 640
- modeltype: "model_medium"
```

### Edge/CPU-Only Devices
```
System:
- batch_size: 1 (Single frame processing)
- use_cuda: false
- use_fp16: false
- fps: "2/1" (Lower processing rate)

Pose Detection:
- conf: 0.4 (Higher confidence to reduce processing)
- decoder_width: 320 (Reduced resolution)
- decoder_height: 320
- modeltype: "model_small" (Use smaller model if available)

Stone Throwing:
- window: 20 (Shorter window to reduce computation)
- violation_window: 15 (Quick validation)
- ppl_count: 5 (Higher threshold to reduce computation)
```

## Specific Environment Scenarios

### Border Security Areas
```
Pose Detection:
- conf: 0.3 (Balanced for border monitoring)

Stone Throwing:
- window: 25 (Quick detection for border incidents)
- violation_percentage: 70 (Sensitive for security)
- ppl_count: 1 (Single person can create incident)
- alert_interval: 30 (Immediate border response)
- severity: "critical" (Border security priority)

System:
- fps: "6/1" (High monitoring rate for security)
```

### Sports Venues/Stadiums
```
Pose Detection:
- conf: 0.35 (Balanced for crowd environment)

Stone Throwing:
- window: 20 (Quick detection for crowd safety)
- violation_percentage: 75 (Moderate for stadium crowds)
- ppl_count: 5 (Higher threshold for stadium context)
- alert_interval: 60 (Quick stadium response)
- severity: "high" (Crowd safety priority)

System:
- fps: "5/1" (Active stadium monitoring)
```

### Correctional Facilities
```
Pose Detection:
- conf: 0.4 (High confidence for institutional accuracy)

Stone Throwing:
- window: 30 (Standard institutional observation)
- violation_percentage: 85 (High threshold for precision)
- ppl_count: 1 (Any individual can create incident)
- alert_interval: 45 (Institutional response time)
- severity: "critical" (Institutional safety priority)

System:
- fps: "4/1" (Consistent institutional monitoring)
```

### Public Parks/Recreation Areas
```
Pose Detection:
- conf: 0.25 (Sensitive for public safety)

Stone Throwing:
- window: 40 (Longer observation for recreation context)
- violation_percentage: 80 (Standard threshold)
- ppl_count: 3 (Group threshold for park incidents)
- alert_interval: 150 (Park response time)
- severity: "medium" (Public recreation priority)

System:
- fps: "3/1" (Standard park monitoring)
```

## Troubleshooting Common Issues

### Too Many False Throwing Alerts
```
Pose Detection:
- conf: +0.1 (Higher pose confidence)

Stone Throwing:
- violation_percentage: +10 (Higher threshold)
- window: +10 (Longer validation window)
- ppl_count: +1 (More people required)
- alert_interval: +60 (Less frequent alerts)
```

### Missing Real Stone Throwing
```
Pose Detection:
- conf: -0.1 (Lower pose confidence)

Stone Throwing:
- violation_percentage: -10 (Lower threshold)
- window: -5 (Shorter validation)
- violation_window: -5 (Quicker detection)
- ppl_count: -1 (Fewer people required)
```

### Poor Performance
```
System:
- batch_size: /2 (Reduce batch size)
- fps: /2 (Lower processing rate)

Pose Detection:
- decoder_width: -160 (Reduce resolution)
- decoder_height: -160
```

### Inconsistent Motion Detection
```
Stone Throwing:
- window: +10 (Longer observation window)
- violation_window: +5 (Extended validation)

System:
- fps: +1 (Higher sampling rate for consistency)
```

### Angle Detection Issues
```
Stone Throwing:
- angle_ranges: [expand range tolerances] (More flexible angle matching)
- violation_percentage: -5 (More sensitive to motion patterns)
```

## Integration Notes

- Combine with audio detection for comprehensive threat assessment
- Integrate with crowd counting for context-aware sensitivity
- Use with perimeter security for coordinated response
- Coordinate with emergency response systems for immediate action
- Link with video analytics for trajectory analysis
- Connect with law enforcement systems for incident documentation
- Integrate with public address systems for crowd dispersal instructions
