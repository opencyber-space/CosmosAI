# Gesture Waving Detection Parameter Recommendations

## Use Case Overview
Gesture waving detection systems identify when people perform hand waving gestures, typically used for assistance requests, emergency signaling, greeting detection, and interactive applications.

## Core Parameters by Building Block

### Pose Detection Parameters
- **conf**: 0.25 (Lower confidence to detect subtle hand movements)
- **modeltype**: "model_medium" (Balanced accuracy and performance for pose detection)
- **decoder_width**: 640 (High resolution for accurate keypoint detection)
- **decoder_height**: 640 (High resolution for hand movement precision)

### Gesture Analysis Parameters
- **selected_keypoints**: ["left_wrist", "right_wrist", "nose"] (Key points for wave detection)
- **N_moving_keypoints**: 2 (Number of moving keypoints required)
- **stationaryThreshold**: 20 (Pixel threshold for movement detection)
- **historyLength**: 10 (Frame history for gesture analysis)
- **threshold**: 0 (Gesture confidence threshold)
- **N_violating_keypoints**: 0 (Keypoints required for gesture trigger)

### Use Case Specific Parameters
- **waitSecondsForAction**: 20 (Time window to wait for complete gesture)
- **ppl_violating_count**: 1 (Number of people performing gesture to trigger alert)
- **withTracker**: "True" (Enable tracking for gesture continuity)
- **scenario_type**: "individual" (Individual vs group gesture detection)
- **alert_interval**: 120 (Alert frequency in seconds)
- **severity**: "high" (Alert severity level)

### System Parameters
- **fps**: "3/1" (Higher frame rate for gesture capture)
- **use_cuda**: true (GPU acceleration recommended)
- **use_fp16**: true (Half precision for performance)
- **batch_size**: 4 (Smaller batch for pose processing)

## Environmental Condition Recommendations

### Emergency/Assistance Scenarios
```
Pose Detection:
- conf: 0.2 (Very low confidence to catch subtle gestures)
- decoder_width: 640 (High resolution for accuracy)
- decoder_height: 640

Gesture Analysis:
- stationaryThreshold: 15 (More sensitive to movement)
- historyLength: 15 (Longer history for emergency gestures)
- waitSecondsForAction: 10 (Shorter wait for emergency response)

Use Case:
- ppl_violating_count: 1 (Single person can trigger emergency)
- severity: "critical" (Highest priority for emergencies)
- alert_interval: 30 (Immediate alerts for emergencies)

System:
- fps: "5/1" (Higher rate for emergency detection)
```

### Customer Service/Retail
```
Pose Detection:
- conf: 0.3 (Balanced confidence for customer gestures)

Gesture Analysis:
- stationaryThreshold: 25 (Less sensitive to avoid false triggers)
- historyLength: 8 (Shorter history for quick service)
- waitSecondsForAction: 15 (Moderate wait time)

Use Case:
- severity: "medium" (Standard service priority)
- alert_interval: 60 (Reasonable response time)
- scenario_type: "individual" (Personal service requests)

System:
- fps: "3/1" (Standard processing rate)
```

### Interactive Applications/Gaming
```
Pose Detection:
- conf: 0.35 (Higher confidence for intentional gestures)
- decoder_width: 480 (Slightly lower resolution for speed)
- decoder_height: 480

Gesture Analysis:
- stationaryThreshold: 30 (Clear intentional movements)
- historyLength: 5 (Quick gesture response)
- waitSecondsForAction: 5 (Fast interaction response)

Use Case:
- severity: "low" (Entertainment priority)
- alert_interval: 1 (Immediate interaction feedback)

System:
- fps: "6/1" (High rate for interactive response)
- batch_size: 2 (Smaller batch for low latency)
```

### Security/Surveillance
```
Pose Detection:
- conf: 0.4 (Higher confidence to avoid false alarms)

Gesture Analysis:
- stationaryThreshold: 20 (Standard movement threshold)
- historyLength: 12 (Longer validation for security)
- waitSecondsForAction: 25 (Thorough gesture validation)

Use Case:
- ppl_violating_count: 1 (Any person can signal)
- severity: "high" (Security priority)
- alert_interval: 90 (Balanced response time)
- withTracker: "True" (Track gesture performer)

System:
- fps: "2/1" (Consistent monitoring rate)
```

## Camera Height Scenarios

### High-Mounted Cameras (8-15m) - Overhead View
```
Pose Detection:
- conf: 0.4 (Higher confidence for overhead pose detection)
- decoder_width: 640 (High resolution for distant gestures)
- decoder_height: 640

Gesture Analysis:
- stationaryThreshold: 30 (Adjusted for perspective distance)
- selected_keypoints: ["left_wrist", "right_wrist", "head"] (Adjust for overhead view)
- historyLength: 12 (Longer history for perspective challenges)
```

### Standard Height Cameras (3-6m) - Angled View
```
Pose Detection:
- conf: 0.25 (Standard confidence for angled views)
- decoder_width: 640
- decoder_height: 640

Gesture Analysis:
- stationaryThreshold: 20 (Standard movement threshold)
- selected_keypoints: ["left_wrist", "right_wrist", "nose"] (Standard keypoints)
```

### Low-Mounted Cameras (1-3m) - Eye Level
```
Pose Detection:
- conf: 0.3 (Good confidence for eye-level detection)
- decoder_width: 480 (Lower resolution acceptable at close range)
- decoder_height: 480

Gesture Analysis:
- stationaryThreshold: 15 (More sensitive at close range)
- historyLength: 8 (Shorter history for close interaction)
- waitSecondsForAction: 15 (Quick response at eye level)
```

### PTZ Cameras - Dynamic View
```
Pose Detection:
- conf: 0.45 (Higher confidence for moving camera)

Gesture Analysis:
- stationaryThreshold: 35 (Compensate for camera movement)
- historyLength: 6 (Shorter history due to camera movement)
- withTracker: "True" (Essential for PTZ tracking)

System:
- fps: "4/1" (Higher rate to compensate for movement)
```

## Hardware-Specific Optimizations

### High-End GPU (RTX 3080+, A100)
```
System:
- batch_size: 8 (Larger batches for pose processing)
- use_fp16: true
- fps: "6/1" (Higher processing rate)

Pose Detection:
- decoder_width: 640 (High resolution processing)
- decoder_height: 640
- modeltype: "model_large" (Use larger model if available)

Gesture Analysis:
- historyLength: 20 (Longer history for better accuracy)
```

### Mid-Range GPU (RTX 2060, GTX 1080)
```
System:
- batch_size: 4 (Balanced batch size)
- use_fp16: true
- fps: "3/1"

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
- fps: "1/1" (Lower processing rate)

Pose Detection:
- conf: 0.4 (Higher confidence to reduce processing)
- decoder_width: 320 (Reduced resolution)
- decoder_height: 320
- modeltype: "model_small" (Use smaller model if available)

Gesture Analysis:
- historyLength: 5 (Shorter history to save memory)
- waitSecondsForAction: 10 (Shorter wait to reduce computation)
```

## Specific Environment Scenarios

### Healthcare Facilities - Patient Assistance
```
Pose Detection:
- conf: 0.2 (Very sensitive for patient needs)

Gesture Analysis:
- stationaryThreshold: 12 (Very sensitive movement detection)
- waitSecondsForAction: 8 (Quick response for patient care)

Use Case:
- severity: "critical" (Patient care priority)
- alert_interval: 15 (Immediate medical response)
- ppl_violating_count: 1 (Any patient can signal)

System:
- fps: "4/1" (High monitoring rate)
```

### Educational Institutions - Student Interaction
```
Pose Detection:
- conf: 0.3 (Balanced for classroom environment)

Gesture Analysis:
- stationaryThreshold: 25 (Avoid false triggers from normal movement)
- waitSecondsForAction: 12 (Reasonable wait for student questions)

Use Case:
- severity: "medium" (Educational priority)
- alert_interval: 45 (Classroom response time)
- scenario_type: "individual" (Individual student attention)

System:
- fps: "2/1" (Classroom monitoring rate)
```

### Transportation Hubs - Assistance Requests
```
Pose Detection:
- conf: 0.35 (Higher confidence in busy environment)

Gesture Analysis:
- stationaryThreshold: 30 (Avoid false triggers from crowd movement)
- historyLength: 10 (Standard validation)
- waitSecondsForAction: 20 (Accommodate crowd noise)

Use Case:
- severity: "medium" (Service priority)
- alert_interval: 90 (Reasonable response in busy area)

System:
- fps: "3/1" (Active monitoring rate)
```

### Manufacturing/Industrial - Safety Signals
```
Pose Detection:
- conf: 0.4 (High confidence for safety accuracy)

Gesture Analysis:
- stationaryThreshold: 25 (Clear intentional movements)
- waitSecondsForAction: 15 (Quick safety response)

Use Case:
- severity: "critical" (Safety priority)
- alert_interval: 30 (Immediate safety response)
- ppl_violating_count: 1 (Any worker can signal)

System:
- fps: "4/1" (High safety monitoring rate)
```

## Troubleshooting Common Issues

### Too Many False Gestures
```
Pose Detection:
- conf: +0.1 (Higher pose confidence)

Gesture Analysis:
- stationaryThreshold: +10 (Less sensitive to movement)
- historyLength: +5 (Longer validation)
- waitSecondsForAction: +5 (More complete gesture requirement)

Use Case:
- ppl_violating_count: +1 (More people required)
```

### Missing Real Gestures
```
Pose Detection:
- conf: -0.1 (Lower pose confidence)

Gesture Analysis:
- stationaryThreshold: -5 (More sensitive to movement)
- historyLength: -3 (Shorter validation)
- waitSecondsForAction: -5 (Quicker gesture detection)
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

### Inconsistent Detection
```
Gesture Analysis:
- historyLength: +5 (Longer validation history)
- stationaryThreshold: -5 (More consistent movement detection)

Use Case:
- withTracker: "True" (Enable tracking for consistency)

System:
- fps: +1 (Higher sampling rate)
```

## Integration Notes

- Combine with face recognition for personalized gesture responses
- Integrate with communication systems for assistance routing
- Use with access control for gesture-based authentication
- Coordinate with lighting systems for optimal gesture visibility
- Link with audio systems for gesture confirmation feedback
- Connect with mobile apps for gesture training and customization
