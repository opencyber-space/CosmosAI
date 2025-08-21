# Social Distance Monitoring Pipeline Documentation

## Overview
This document provides analysis of the `0001_socialDistance_camera_54_13_13.json` blueprint for social distance monitoring. The pipeline detects people and monitors compliance with social distancing guidelines using real-world distance measurements.

## Pipeline Identity
- **Component ID**: `socialDistance_camera_54_13_13`
- **Version**: `v0.0.1`
- **Frame Rate**: 2 FPS (optimized for distance analysis)
- **GPU ID**: 2

## Pipeline Architecture
```
Input Stream (2 FPS) → Object Detection → Policy Filtering → Tracking → Social Distance Analysis → Alerts
```

## Key Components

### Social Distance Detection Engine
```json
{
  "socialDistance": {
    "window": 30,
    "min_people": 5,
    "distance_realworld": 1.8,
    "violation_percentage": 50,
    "alert_type": "zone",
    "alert_interval": 120,
    "severity": "medium"
  }
}
```

### Detection Logic
- **Minimum Distance**: 1.8 meters (standard social distancing)
- **Analysis Window**: 30 frames for violation assessment
- **Minimum People**: 5 people required for analysis
- **Violation Threshold**: 50% violation rate triggers alert
- **Alert Interval**: 120 seconds between alerts

### Alert System
- **Database**: MongoDB (`PROJECT_ALERT`)
- **Real-time**: Redis pub/sub
- **Storage**: MinIO for video evidence
- **Severity**: Medium priority

## Use Cases
- **COVID-19 Compliance**: Pandemic safety monitoring
- **Workplace Safety**: Office and factory monitoring
- **Public Spaces**: Mall and venue compliance
- **Event Management**: Crowd density control
- **Healthcare**: Hospital and clinic monitoring

## Performance
- **Input FPS**: 2 FPS (efficient for distance analysis)
- **Real-world Calibration**: Accurate distance measurements
- **Zone-based Alerts**: Focused monitoring areas
- **Configurable Thresholds**: Adaptable to different scenarios

This pipeline provides reliable social distance monitoring with configurable parameters suitable for various compliance and safety applications.
