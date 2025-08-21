# Loitering Detection Pipeline Documentation

## Overview
This document provides a comprehensive analysis of the `loitering.json` blueprint, which defines a complete end-to-end computer vision pipeline for detecting loitering behavior in surveillance environments. The pipeline implements a streamlined approach with object detection, zone filtering, tracking, and temporal analysis.

## Pipeline Identity

### Component Information
- **Component ID**: `loitering_pipeline`
- **Component Type**: `node.algorithm.pipeline`
- **Parser Version**: `Parser/V1`
- **Pipeline UID**: `loitering_camera_100_100`
- **Version**: `v0.0.1`
- **Release Tag**: `stable`

### Template Configuration
- **Template Type**: `template.vdag.app-layout.sample-vdag:v0.0.1-beta`
- **Runtime ID**: `default-mdag`

## Source Configuration

### Camera Input Settings
- **Assignment Type**: `source`
- **Source ID**: `camera_100_100`
- **Controller Node**: `framequeues-2`

### Stream Parameters
- **Frame Rate**: 5 FPS (`"5/1"`)
- **Actuation Frequency**: 1
- **GPU ID**: 1
- **GPU Enabled**: Yes
- **Allocation Node**: `framequeues-2`
- **Mode**: Memory-based processing
- **Loop Video**: Enabled (for testing)
- **Live Stream**: Enabled
- **Frame Quality**: 90%
- **Color Format**: BGR

### Global Settings
- **Alert URL**: `http://test-alerts.io`
- **Alert ID URL**: `http://serverip:alertidpost/getalertid`
- **Test Configuration**: Custom parameters for pipeline testing

## Pipeline Components Analysis

### 1. Object Detection Node (`obj-det-1`)

#### Component Details
- **Component URI**: `node.algorithm.objdet.general7Detection_360h_640:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: General object detection optimized for 360p/640p resolution

#### Configuration
- **Hardware**: GPU-accelerated with FP16 precision
- **Batch Processing**: Enabled (batch size 8)
- **Decoder**: DALI with Gaussian interpolation
- **Input Resolution**: 416×416 (model input)
- **Decoder Resolution**: 640×360 (stream processing)
- **Full Image**: Enabled
- **Stretch Image**: Disabled
- **Block ROI**: Disabled
- **ROI Batch Size**: 1

#### Parameters
- **Confidence Threshold**: 0.4
- **IoU Threshold**: 0.45
- **Max Detections**: 300
- **MJPEG Output**: Disabled
- **Alerts**: Disabled

#### Scale Specification
- **Cluster ID**: `default-cluster`
- **Machine ID**: `framequeues-2`
- **GPU ID**: 1
- **MJPEG Drawing**: Enabled
- **Drawing Component**: `node.utils.drawing.drawing:v0.0.1-stable`
- **Output Resolution**: 1920×1080

### 2. Policy Filter Node (`policy-1`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Filter person detections within loitering zones

#### Filter Configuration
```json
{
  "class_conf_filter": {
    "score": 0.5,
    "allowed_classes": ["person"]
  },
  "inside_zone": {
    "zone": ["ZoneLoitering"],
    "pivotPoint": "bottomPoint"
  }
}
```

#### Key Features
- **Class Filtering**: Only allows "person" detections
- **Confidence Threshold**: 0.5 (medium confidence)
- **Zone Filtering**: Restricts detection to "ZoneLoitering" area
- **Pivot Point**: Uses bottom point of bounding box for zone membership

### 3. Object Tracking Node (`tracker-1`)

#### Component Details
- **Component URI**: `node.algorithm.tracker.trackerlite:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Lightweight tracking for maintaining object identity

#### Configuration
- **TTL (Time to Live)**: 4 frames
- **Tracker Type**: "NONE" (basic tracking without re-identification)
- **Keep Upper Height Ratio**: 1.0
- **Decoder**: DALI with Gaussian interpolation
- **Batch Processing**: Enabled (batch size 16)

#### Tracking Parameters
- **IoU Threshold**: 0.45
- **Sigma IoU**: 0.3
- **Sigma Height**: 0.3
- **Sigma Length**: 0.1
- **T Min**: 2 (minimum track length)

#### Features
- **Drawing**: Comprehensive visualization (zones, ROIs, lines, arrows, trajectories)
- **Calibration**: Enabled for spatial awareness

### 4. Dwell Time Policy Node (`policy-2`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Apply dwell time filtering for loitering pre-processing

#### Filter Configuration
```json
{
  "dwell": {
    "loiteringThresholdSeconds": 1
  }
}
```

#### Purpose
- **Pre-filtering**: Initial dwell time check (1 second threshold)
- **Performance Optimization**: Reduces data flow to final usecase node
- **Fast Response**: Quick elimination of transient objects

### 5. Loitering Usecase Node (`usecase-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecase:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Final loitering detection and alert generation

#### Loitering Configuration
```json
{
  "loitering": {
    "loiteringThresholdSeconds": 120,
    "alert_interval": 600,
    "severity": "medium"
  }
}
```

#### Alert System Integration
- **MJPEG Output**: Enabled for visualization
- **Alert Generation**: Enabled

**Storage Configuration:**
```json
{
  "MINIO": {
    "endpoint": "serverip:32751",
    "access_key": "accesskey",
    "secret_key": "secret_key",
    "MINIOURLREPLACEMENT": ""
  }
}
```

**Database Configuration:**
```json
{
  "MONGO": {
    "host": "mongoip",
    "dbname": "CITYALERT",
    "collection": "alerts"
  }
}
```

**Real-time Data Push:**
```json
{
  "REDIS": {
    "host": "serverip",
    "port": 6379,
    "password": "secret#",
    "db": 0
  }
}
```

## Pipeline Data Flow Architecture

### Flow Diagram
```
Input Stream (Camera: 5 FPS, BGR, 640×360)
       ↓
[obj-det-1]
(General Object Detection)
       ↓
[policy-1]
(Person Zone Filtering)
       ↓
[tracker-1]
(Lightweight Tracking)
       ↓
[policy-2]
(Dwell Time Pre-filter: 1s)
       ↓
[usecase-1]
(Loitering Detection: 120s + Alert Generation)
       ↓
Alert Output (MinIO + MongoDB + Redis)
```

### Detailed Connection Graph

#### Sequential Processing Chain
1. **obj-det-1** → **policy-1**: Object detection feeds into person filtering
2. **policy-1** → **tracker-1**: Filtered persons are tracked
3. **tracker-1** → **policy-2**: Tracked objects undergo dwell time pre-filtering
4. **policy-2** → **usecase-1**: Final loitering analysis and alert generation

#### Input/Output Mapping
- **Pipeline Input**: Camera stream at 5 FPS
- **Pipeline Output**: Loitering alerts with metadata

## Key Configuration Parameters

### Detection Settings
- **Model Resolution**: 416×416 (optimized for speed)
- **Stream Resolution**: 640×360 (balanced quality/performance)
- **Confidence Threshold**: 0.4 (detection) → 0.5 (filtering)
- **Max Detections**: 300 objects per frame

### Tracking Settings
- **Tracking Type**: Lightweight (no re-identification)
- **Track TTL**: 4 frames
- **IoU Threshold**: 0.45
- **Batch Size**: 16 (high throughput)

### Loitering Logic
- **Pre-filter Threshold**: 1 second (quick elimination)
- **Final Threshold**: 120 seconds (2 minutes)
- **Alert Interval**: 600 seconds (10 minutes)
- **Severity Level**: Medium

### Zone Configuration
- **Zone Name**: "ZoneLoitering"
- **Pivot Point**: Bottom point of bounding box
- **Purpose**: Restrict analysis to designated areas

## Performance Characteristics

### Hardware Allocation
- **Node**: `framequeues-2`
- **GPU**: ID 1 (shared across all algorithm nodes)
- **Cluster**: `default-cluster`

### Processing Features
- **Batch Processing**: Enabled across all nodes
- **GPU Acceleration**: Used for detection and tracking
- **Memory Mode**: In-memory processing for low latency
- **Drawing Output**: 1920×1080 for visualization

### Alert Management
- **Storage**: MinIO for alert data and evidence
- **Database**: MongoDB for alert metadata
- **Real-time**: Redis for live alert streaming
- **Visualization**: MJPEG stream for monitoring

## Use Case Applications

### Security Monitoring
- **Retail Stores**: Monitor for suspicious loitering near exits or high-value areas
- **Transportation Hubs**: Detect individuals lingering in restricted zones
- **Residential Areas**: Monitor for unauthorized presence in private areas
- **Parking Lots**: Identify potential security threats or theft preparation

### Business Analytics
- **Customer Behavior**: Analyze customer interest in specific store areas
- **Queue Management**: Monitor waiting times in service areas
- **Space Utilization**: Understand how spaces are used over time

## Algorithm Logic

### Processing Flow
1. **Object Detection**: Identify all objects in the scene
2. **Person Filtering**: Keep only person detections with confidence > 0.5
3. **Zone Filtering**: Retain only persons within "ZoneLoitering"
4. **Tracking**: Assign and maintain unique IDs for persons
5. **Pre-filtering**: Quick elimination of objects present < 1 second
6. **Loitering Analysis**: Detailed analysis for objects present > 120 seconds
7. **Alert Generation**: Create alerts for confirmed loitering events

### Optimization Features
- **Two-stage Thresholding**: 1s pre-filter + 120s final threshold
- **Zone-based Processing**: Reduces computational load
- **Lightweight Tracking**: No re-identification for better performance
- **Batch Processing**: Efficient GPU utilization

## Configuration Guidelines

### High Security Areas
```json
{
  "loiteringThresholdSeconds": 60,
  "alert_interval": 300,
  "severity": "high",
  "confidence": 0.6
}
```

### Public Spaces
```json
{
  "loiteringThresholdSeconds": 300,
  "alert_interval": 900,
  "severity": "low",
  "confidence": 0.4
}
```

### Retail Environments
```json
{
  "loiteringThresholdSeconds": 180,
  "alert_interval": 600,
  "severity": "medium",
  "confidence": 0.5
}
```

## Technical Notes

### Strengths
- **Streamlined Pipeline**: Simple, linear flow for efficient processing
- **Optimized Performance**: 360p processing for speed
- **Robust Filtering**: Multi-stage approach reduces false positives
- **Comprehensive Alerts**: Full integration with storage and notification systems

### Limitations
- **Basic Tracking**: No re-identification limits handling of occlusions
- **Single Zone**: Only supports one loitering zone
- **Fixed Thresholds**: Limited adaptability to different scenarios

### Best Practices
- Configure zone boundaries carefully to avoid edge cases
- Adjust confidence thresholds based on lighting conditions
- Monitor alert frequency to prevent notification fatigue
- Regular calibration of loitering thresholds based on usage patterns

## Integration Requirements

### Upstream Dependencies
- Camera stream with stable frame rate
- Zone definitions for "ZoneLoitering"
- Network connectivity for alert delivery

### Downstream Integrations
- Security management systems
- Notification services
- Analytics dashboards
- Evidence management systems

This loitering detection pipeline provides a balanced approach between accuracy and performance, suitable for most surveillance applications requiring basic loitering detection capabilities.
