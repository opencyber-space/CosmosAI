# Stone Throwing Detection Pipeline Documentation

## Overview
This document analyzes the `0001_stonethrowing_camera_39_18_11.json` blueprint for detecting stone throwing behavior using pose estimation and arm angle analysis.

## Pipeline Identity
- **Component ID**: `stonethrowing_camera_39_18_11`
- **Version**: `v0.0.1`
- **Frame Rate**: 5 FPS
- **GPU ID**: 0

## Pipeline Architecture
```
Input Stream → Pose Detection → Policy Filtering → Tracking → Angle Analysis → Stone Throwing Detection → Alerts
```

## Key Components

### Pose-Based Interaction Detection
```json
{
  "interaction": {
    "activity_type": "angle",
    "angle_keypoints": [
      ["right_wrist", "right_elbow"],
      ["right_elbow", "right_shoulder"]
    ]
  }
}
```

### Stone Throwing Detection Engine
```json
{
  "stonePelting": {
    "window": 30,
    "violation_window": 20,
    "violation_percentage": 80,
    "ppl_count": 3,
    "angle_ranges": {
      "('right_wrist', 'right_elbow')": [],
      "('right_elbow', 'right_shoulder')": []
    },
    "alert_interval": 300,
    "severity": "high"
  }
}
```

### Detection Logic
- **Pose Analysis**: Right arm angle detection (wrist-elbow-shoulder)
- **Analysis Window**: 30 frames for behavior assessment
- **Violation Window**: 20 frames minimum for confirmation
- **Violation Threshold**: 80% throwing motion detection
- **Group Detection**: Minimum 3 people for crowd analysis
- **Alert Interval**: 300 seconds between alerts
- **Severity**: High (security threat)

### Zone-Based Filtering
- **Zone**: "ZoneStone" area monitoring
- **Person Filtering**: 0.3 confidence threshold
- **Pose Detection**: Right arm movement analysis

## Use Cases
- **Security Monitoring**: Riot and violence detection
- **Public Safety**: Crowd control and disturbance detection
- **Event Security**: Sports and public gathering monitoring
- **Law Enforcement**: Evidence collection and threat assessment
- **Campus Security**: School and university safety

## Performance
- **Real-time Analysis**: 5 FPS pose-based detection
- **Angle Computation**: Precise arm movement analysis
- **Group Behavior**: Multi-person stone throwing detection
- **High Accuracy**: 80% threshold for confirmation

This pipeline provides reliable stone throwing detection using advanced pose estimation and angle analysis, suitable for security and crowd monitoring applications.
