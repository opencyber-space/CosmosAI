# Intrusion Detection Pipeline Documentation

## Overview
This document analyzes the `0002_intrusion_camera_56_3_10.json` blueprint for detecting intrusion through line crossing analysis across multiple zones.

## Pipeline Identity
- **Component ID**: `intrusion_camera_56_3_10`
- **Version**: `v0.0.1`
- **Frame Rate**: 5 FPS
- **GPU ID**: 0

## Pipeline Architecture
```
Input Stream → Object Detection → Policy Filtering → Tracking → Intrusion Line Crossing Detection → Alerts
```

## Key Components

### Intrusion Detection Engine
```json
{
  "intrusionLineCrossing": {
    "alert_interval": 60,
    "severity": "medium",
    "arrows": [
      {"zone": "ZoneIntrusion1"},
      {"zone": "ZoneIntrusion2"}
    ],
    "lines": [
      {"zone": "ZoneIntrusion1"},
      {"zone": "ZoneIntrusion2"}
    ]
  }
}
```

### Detection Logic
- **Multi-Zone Monitoring**: ZoneIntrusion1 and ZoneIntrusion2
- **Line Crossing**: Directional intrusion detection
- **Arrow Indicators**: Visual direction markers
- **Alert Interval**: 60 seconds between alerts
- **Severity**: Medium priority security event

### Zone-Based Filtering
- **Person Detection**: High confidence threshold
- **Zone Boundaries**: Defined intrusion perimeters
- **Line Crossing**: Unauthorized boundary crossings

## Use Cases
- **Perimeter Security**: Property boundary monitoring
- **Restricted Areas**: Unauthorized access detection
- **Building Security**: Entry point monitoring
- **Industrial Safety**: Hazardous area protection
- **Border Control**: Boundary crossing detection

## Performance
- **Multi-Zone Support**: Dual zone monitoring
- **Fast Response**: 60-second alert intervals
- **Directional Detection**: Crossing direction analysis
- **Real-time Alerts**: Immediate security notifications

This pipeline provides reliable intrusion detection through line crossing analysis suitable for perimeter security and access control applications.
