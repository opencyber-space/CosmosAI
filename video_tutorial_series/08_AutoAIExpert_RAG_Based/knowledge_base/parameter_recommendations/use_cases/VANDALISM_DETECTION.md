# Vandalism Detection Parameter Recommendations

## Use Case Overview
Vandalism detection systems identify destructive or malicious activities such as property damage, graffiti creation, object throwing, and aggressive behaviors, typically used for public property protection, facility security, and incident prevention.

## Core Parameters by Building Block

### Pose Detection Parameters
- **conf**: 0.25 (Lower confidence to detect subtle vandalism actions)
- **modeltype**: "model_medium" (Balanced accuracy for action detection)
- **decoder_width**: 640 (High resolution for action detail detection)
- **decoder_height**: 640 (High resolution for precise movement analysis)

### Action Detection Parameters
- **activity_type**: "action" (Action-based detection mode)
- **actions**: ["wave", "hand_raise"] (Detectable vandalism-related actions)
- **pivot**: "nose" (Central reference point for action analysis)
- **selected_keypoints**: ["left_wrist", "nose", "right_wrist"] (Key body points for action detection)
- **threshold**: 0 (Action confidence threshold)
- **N_violating_keypoints**: 0 (Keypoints required for action trigger)
- **score**: 0.25 (Person detection confidence for action analysis)

### Use Case Specific Parameters
- **waitSecondsForAction**: 1 (Quick action detection for vandalism)
- **ppl_violating_count**: 10 (Group-based vandalism detection threshold)
- **withTracker**: "True" (Track vandalism perpetrators)
- **scenario_type**: "group" (Group vandalism detection)
- **alert_interval**: 1 (Immediate alerts for vandalism)
- **severity**: "high" (High priority for property protection)

### System Parameters
- **fps**: "4/1" (Higher frame rate for action capture)
- **use_cuda**: true (GPU acceleration recommended)
- **use_fp16**: true (Half precision for performance)
- **batch_size**: 4 (Smaller batch for pose processing)

## Environmental Condition Recommendations

### Public Property/Parks
```
Pose Detection:
- conf: 0.2 (Very sensitive to catch all potential vandalism)
- decoder_width: 640 (High resolution for outdoor monitoring)
- decoder_height: 640

Action Detection:
- actions: ["wave", "hand_raise", "throw"] (Extended action set)
- threshold: -0.1 (More sensitive action detection)
- score: 0.2 (Lower person confidence for public areas)

Use Case:
- ppl_violating_count: 5 (Lower group threshold for parks)
- waitSecondsForAction: 2 (Quick detection for property protection)
- severity: "critical" (High priority for public property)
- alert_interval: 30 (Quick response time)

System:
- fps: "5/1" (Higher monitoring rate for public areas)
```

### School Property/Educational Facilities
```
Pose Detection:
- conf: 0.3 (Balanced confidence for school environment)

Action Detection:
- actions: ["wave", "hand_raise"] (Conservative action set for schools)
- threshold: 0 (Standard action sensitivity)
- score: 0.3 (Higher confidence for controlled environment)

Use Case:
- ppl_violating_count: 3 (Lower threshold for student groups)
- waitSecondsForAction: 3 (Moderate validation time)
- scenario_type: "individual" (Individual accountability)
- severity: "high" (Educational priority)
- alert_interval: 60 (Reasonable response time)

System:
- fps: "3/1" (Standard school monitoring rate)
```

### Transportation Infrastructure
```
Pose Detection:
- conf: 0.35 (Higher confidence for busy transport areas)
- decoder_width: 640 (High resolution for infrastructure detail)
- decoder_height: 640

Action Detection:
- actions: ["wave", "hand_raise", "throw", "kick"] (Extended for infrastructure vandalism)
- score: 0.3 (Balanced for transport crowds)

Use Case:
- ppl_violating_count: 8 (Higher threshold for crowded areas)
- waitSecondsForAction: 1 (Quick detection for safety)
- severity: "critical" (Infrastructure safety priority)
- alert_interval: 15 (Immediate response for transport safety)

System:
- fps: "4/1" (Active monitoring for transport security)
```

### Private Property/Commercial
```
Pose Detection:
- conf: 0.4 (Higher confidence to avoid false alarms)

Action Detection:
- threshold: 0.1 (Slightly higher threshold for precision)
- score: 0.35 (Higher confidence for commercial accuracy)

Use Case:
- ppl_violating_count: 2 (Lower threshold for private property)
- scenario_type": "individual" (Individual property damage)
- severity: "high" (Property protection priority)
- alert_interval: 45 (Balanced commercial response)

System:
- fps: "3/1" (Standard commercial monitoring)
```

## Camera Height Scenarios

### High-Mounted Cameras (8-15m) - Overhead Surveillance
```
Pose Detection:
- conf: 0.4 (Higher confidence for overhead action detection)
- decoder_width: 640 (High resolution for distant actions)
- decoder_height: 640

Action Detection:
- selected_keypoints: ["left_wrist", "right_wrist", "head"] (Adjust for overhead perspective)
- threshold: -0.1 (More sensitive for overhead challenges)

Use Case:
- waitSecondsForAction: 3 (Longer validation for perspective)
```

### Standard Height Cameras (3-6m) - Angled Monitoring
```
Pose Detection:
- conf: 0.25 (Standard confidence for angled views)
- decoder_width: 640
- decoder_height: 640

Action Detection:
- selected_keypoints: ["left_wrist", "nose", "right_wrist"] (Standard keypoints)
- threshold: 0 (Standard action sensitivity)
```

### Low-Mounted Cameras (1-3m) - Close Range
```
Pose Detection:
- conf: 0.3 (Good confidence for close-range detection)
- decoder_width: 480 (Lower resolution acceptable at close range)
- decoder_height: 480

Action Detection:
- threshold: 0.1 (Slightly higher for close-range precision)
- waitSecondsForAction: 1 (Quick detection at close range)

Use Case:
- ppl_violating_count: 1 (Single person threshold for close monitoring)
```

### PTZ Cameras - Active Tracking
```
Pose Detection:
- conf: 0.45 (Higher confidence for moving camera)

Action Detection:
- threshold: 0.2 (Higher threshold for camera movement compensation)
- selected_keypoints: ["left_wrist", "right_wrist"] (Simplified for PTZ)

Use Case:
- withTracker: "True" (Essential for PTZ tracking)
- waitSecondsForAction: 2 (Quick detection for active tracking)

System:
- fps: "5/1" (Higher rate for PTZ responsiveness)
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

Action Detection:
- actions: ["wave", "hand_raise", "throw", "kick", "punch"] (Extended action set)
```

### Mid-Range GPU (RTX 2060, GTX 1080)
```
System:
- batch_size: 4 (Balanced batch size)
- use_fp16: true
- fps: "4/1"

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

Action Detection:
- actions: ["wave", "hand_raise"] (Limited action set)
- waitSecondsForAction: 1 (Quick processing)

Use Case:
- ppl_violating_count: 5 (Higher threshold to reduce computation)
```

## Specific Environment Scenarios

### Art Installations/Museums
```
Pose Detection:
- conf: 0.45 (High precision for art protection)

Action Detection:
- actions: ["wave", "hand_raise", "touch"] (Specific to art protection)
- threshold: 0.2 (Higher threshold for precision)

Use Case:
- ppl_violating_count: 1 (Any person can damage art)
- severity: "critical" (Art preservation priority)
- alert_interval: 10 (Immediate art protection)
- scenario_type: "individual" (Individual art interaction)

System:
- fps: "3/1" (Consistent art monitoring)
```

### Construction Sites
```
Pose Detection:
- conf: 0.3 (Balanced for construction environment)

Action Detection:
- actions: ["wave", "hand_raise", "throw", "kick"] (Construction vandalism actions)
- score: 0.25 (Lower confidence for hard hat detection challenges)

Use Case:
- ppl_violating_count: 3 (Small group threshold)
- severity: "high" (Construction safety priority)
- alert_interval: 30 (Quick construction response)

System:
- fps: "4/1" (Active construction monitoring)
```

### Parking Facilities
```
Pose Detection:
- conf: 0.35 (Balanced for parking environment)

Action Detection:
- actions: ["wave", "hand_raise", "kick"] (Vehicle vandalism actions)
- threshold: 0.1 (Moderate sensitivity)

Use Case:
- ppl_violating_count: 2 (Small group for vehicle damage)
- scenario_type: "individual" (Individual vehicle damage)
- severity: "high" (Vehicle protection priority)
- alert_interval: 45 (Parking facility response time)

System:
- fps: "3/1" (Standard parking monitoring)
```

### Sports Facilities/Stadiums
```
Pose Detection:
- conf: 0.4 (Higher confidence for crowd environment)

Action Detection:
- actions: ["wave", "hand_raise", "throw"] (Crowd vandalism actions)
- score: 0.3 (Balanced for crowd detection)

Use Case:
- ppl_violating_count: 15 (Higher threshold for stadium crowds)
- scenario_type: "group" (Group vandalism in stadiums)
- severity: "high" (Public safety priority)
- alert_interval: 20 (Quick crowd response)

System:
- fps: "5/1" (High monitoring for crowd safety)
```

## Troubleshooting Common Issues

### Too Many False Vandalism Alerts
```
Pose Detection:
- conf: +0.1 (Higher pose confidence)

Action Detection:
- threshold: +0.2 (Higher action threshold)
- score: +0.1 (Higher person confidence)

Use Case:
- waitSecondsForAction: +2 (Longer validation)
- ppl_violating_count: +3 (More people required)
```

### Missing Real Vandalism Events
```
Pose Detection:
- conf: -0.1 (Lower pose confidence)

Action Detection:
- threshold: -0.1 (Lower action threshold)
- actions: [+additional_actions] (Expand action set)

Use Case:
- waitSecondsForAction: -1 (Quicker detection)
- ppl_violating_count: -2 (Fewer people required)
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

### Inconsistent Action Detection
```
Action Detection:
- threshold: -0.1 (More sensitive action detection)
- selected_keypoints: [+additional_keypoints] (More keypoints for stability)

Use Case:
- withTracker: "True" (Enable tracking for consistency)

System:
- fps: +1 (Higher sampling rate for consistency)
```

## Integration Notes

- Combine with audio detection for comprehensive vandalism monitoring
- Integrate with lighting systems for deterrent activation
- Use with access control to identify vandalism perpetrators
- Coordinate with security response systems for immediate intervention
- Link with property management systems for damage assessment
- Connect with legal systems for evidence collection and documentation
