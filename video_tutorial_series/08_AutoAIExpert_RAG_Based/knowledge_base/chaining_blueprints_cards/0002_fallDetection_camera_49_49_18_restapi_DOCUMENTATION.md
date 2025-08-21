# Fall Detection Pipeline Documentation

## Overview
This document analyzes the `0002_fallDetection_camera_49_49_18_restapi.json` blueprint for detecting fall incidents using REST API integration and dual-stage fall detection.

## Pipeline Identity
- **Component ID**: `fallDetection_camera_49_49_18_restapi`
- **Version**: `v0.0.1`
- **Frame Rate**: 5 FPS
- **GPU ID**: 1

## Pipeline Architecture
```
Input Stream → REST API Detection → Policy Filtering → Dual-Stage Fall Detection → Alerts
```

## Key Components

### REST API Integration
```json
{
  "RESTInference": {
    "url": "http://fall-detection-api:8080/detect",
    "method": "POST",
    "timeout": 5000
  }
}
```

### Fall Detection Engine (Stage 1)
```json
{
  "fallDetection": {
    "fallConfidence": 0.7,
    "personConfidence": 0.5,
    "associate": "False",
    "fall_time": 60,
    "trigger_block": true,
    "trigger_interval": 1,
    "non_fall_time": 2,
    "alert_interval": 300,
    "severity": "medium"
  }
}
```

### Fall Detection Trigger (Stage 2)
```json
{
  "fallDetectionTrigger": {
    "fallConfidence": 0.7,
    "personConfidence": 0.5,
    "associate": "False", 
    "fall_time": 60,
    "non_fall_time": 2,
    "alert_interval": 300,
    "severity": "medium"
  }
}
```

### Detection Logic
- **Dual-Stage Validation**: Two-stage fall confirmation system
- **High Confidence**: 0.7 threshold for fall detection
- **Person Association**: 0.5 confidence for person detection
- **Fall Duration**: 60-second monitoring window
- **Recovery Time**: 2-second non-fall confirmation
- **Alert Interval**: 300 seconds between alerts
- **REST Integration**: External API for enhanced detection

## Use Cases
- **Healthcare Facilities**: Patient monitoring and safety
- **Elderly Care**: Senior living facility monitoring
- **Home Security**: Personal safety systems
- **Workplace Safety**: Industrial accident prevention
- **Public Spaces**: Emergency response systems

## Performance
- **REST API Integration**: External model collaboration
- **Dual-Stage Validation**: Enhanced accuracy through redundancy
- **Real-time Monitoring**: Immediate fall detection
- **Configurable Thresholds**: Adaptable sensitivity settings

This pipeline provides reliable fall detection with REST API integration and dual-stage validation for critical safety monitoring applications.
