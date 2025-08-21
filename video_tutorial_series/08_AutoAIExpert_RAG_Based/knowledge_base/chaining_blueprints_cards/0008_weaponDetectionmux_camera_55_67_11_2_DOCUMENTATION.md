# Weapon Detection Pipeline Documentation

## Overview
This document analyzes the `0008_weaponDetectionmux_camera_55_67_11_2.json` blueprint for detecting various weapons and firearms using advanced object detection and association.

## Pipeline Identity
- **Component ID**: `weaponDetectionmux_camera_55_67_11_2`
- **Version**: `v0.0.1`
- **Frame Rate**: 5 FPS
- **GPU ID**: 0

## Pipeline Architecture
```
Input Stream → Multi-Object Detection → Policy Filtering → Person-Weapon Association → Weapon Detection Analysis → Critical Alerts
```

## Key Components

### Weapon Detection Engine
```json
{
  "weaponDetection": {
    "classes": [
      "Gun", "Rifle", "gun", "rifle", "knife", "pistol", "Pistol"
    ],
    "withoutAssociationObjectsNeeded": "False",
    "percentage_of_violation": 50,
    "window": 10,
    "alert_interval": 300,
    "severity": "high"
  }
}
```

### Detection Logic
- **Multi-Weapon Support**: Guns, rifles, knives, pistols
- **Case-Insensitive**: Handles various class naming conventions
- **Person Association**: Links weapons to detected persons
- **Violation Threshold**: 50% confidence for weapon detection
- **Analysis Window**: 10-frame confirmation window
- **Alert Interval**: 300 seconds between critical alerts
- **Severity**: High priority security threat

### Advanced Features
- **Person-Weapon Association**: Links weapons to individuals
- **Zone-Based Filtering**: Focused detection within security zones
- **Multi-Class Detection**: Comprehensive weapon type coverage
- **Confidence Filtering**: High-accuracy weapon identification

## Use Cases
- **Airport Security**: Terminal and checkpoint monitoring
- **School Safety**: Campus security and threat prevention
- **Public Events**: Crowd security and threat detection
- **Government Buildings**: Facility security monitoring
- **Law Enforcement**: Evidence collection and threat assessment
- **Border Security**: Checkpoint weapon screening

## Performance
- **Real-time Detection**: 5 FPS weapon monitoring
- **High Accuracy**: 50% confidence threshold
- **Fast Response**: 10-frame confirmation
- **Critical Alerts**: Immediate security notifications
- **Multi-Weapon Support**: Comprehensive threat coverage

This pipeline provides critical weapon detection capabilities with person association, suitable for high-security environments and threat prevention applications.
