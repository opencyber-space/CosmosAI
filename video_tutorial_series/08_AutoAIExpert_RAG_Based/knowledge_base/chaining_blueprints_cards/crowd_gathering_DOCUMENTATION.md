# Crowd Gathering Detection Pipeline Documentation

## Overview
This document provides a comprehensive analysis of the `crowd_gathering.json` blueprint, which defines a complete end-to-end computer vision pipeline for detecting crowd gathering events in surveillance environments. The pipeline implements a streamlined approach focused on counting people in designated zones and triggering alerts when crowd thresholds are exceeded.

## Pipeline Identity

### Component Information
- **Component ID**: `crowd_gathering_pipeline`
- **Component Type**: `node.algorithm.pipeline`
- **Parser Version**: `Parser/V1`
- **Pipeline UID**: `crowdGathering_camera_100_100`
- **Version**: `v0.0.1`
- **Release Tag**: `stable`

### Template Configuration
- **Template Type**: `template.vdag.app-layout.sample-vdag:v0.0.1-beta`
- **Runtime ID**: `default-mdag`
- **Database Location**: `framequeues-10`

## Source Configuration

### Camera Input Settings
- **Assignment Type**: `source`
- **Source ID**: `camera_100_100`
- **Controller Node**: `framequeues-10`

### Stream Parameters
- **Frame Rate**: 0.25 FPS (`"1/4"` - 1 frame every 4 seconds)
- **Actuation Frequency**: 1
- **GPU ID**: 0
- **GPU Enabled**: Yes
- **Allocation Node**: `framequeues-10`
- **Mode**: Memory-based processing
- **Loop Video**: Enabled (for testing)
- **Live Stream**: Enabled
- **Frame Quality**: 90%
- **Color Format**: BGR

### Global Settings
- **Alert ID URL**: `http://serverip:alertidport/getalertid`

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
- **NMS IoU Threshold**: 0.4
- **MJPEG Output**: Disabled
- **Alerts**: Disabled

#### Scale Specification
- **Cluster ID**: `default-cluster`
- **Machine ID**: `framequeues-10`
- **GPU ID**: 0
- **MJPEG Drawing**: Enabled
- **Drawing Component**: `node.utils.drawing.drawing:v0.0.1-stable`
- **Output Resolution**: 1920×1080

### 2. Policy Filter Node (`policy-1`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Filter person detections within crowd gathering zones

#### Filter Configuration
```json
{
  "class_conf_filter": {
    "score": 0.5,
    "allowed_classes": ["person"]
  },
  "inside_zone": {
    "zone": ["ZoneCrowd"],
    "pivotPoint": "midPoint"
  }
}
```

#### Key Features
- **Class Filtering**: Only allows "person" detections
- **Confidence Threshold**: 0.5 (medium confidence)
- **Zone Filtering**: Restricts detection to "ZoneCrowd" area
- **Pivot Point**: Uses midpoint of bounding box for zone membership

### 3. Crowd Gathering Usecase Node (`usecase-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecase:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Analyze crowd density and generate alerts for gathering events

#### Crowd Gathering Configuration
```json
{
  "crowdGathering": {
    "countThreshold": {
      "ZoneCrowd": 20
    },
    "area": {},
    "stampedeThreshold": {},
    "alert_interval": 600,
    "ViolationFrameCount": 5,
    "severity": "medium"
  }
}
```

#### Key Parameters
- **Count Threshold**: 20 people in "ZoneCrowd" triggers alert
- **Alert Interval**: 600 seconds (10 minutes between repeated alerts)
- **Violation Frame Count**: 5 consecutive frames must exceed threshold
- **Severity Level**: Medium priority alerts
- **Area Configuration**: Available for density-based analysis
- **Stampede Threshold**: Available for emergency crowd detection

#### Alert System Integration
- **MJPEG Output**: Enabled for visualization
- **Alert Generation**: Enabled with comprehensive integration

**Storage Configuration:**
```json
{
  "MINIO": {
    "endpoint": "serverip:serverport",
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
    "host": "mongoui",
    "dbname": "CITY_ALERT",
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
Input Stream (Camera: 0.25 FPS, BGR, 640×360)
       ↓
[obj-det-1]
(General Object Detection: 416×416)
       ↓
[policy-1]
(Person Zone Filtering: ZoneCrowd)
       ↓
[usecase-1]
(Crowd Analysis: 20+ people threshold + Alert Generation)
       ↓
Alert Output (MinIO + MongoDB + Redis)
```

### Detailed Connection Graph

#### Sequential Processing Chain
1. **obj-det-1** → **policy-1**: Object detection feeds into person filtering
2. **policy-1** → **usecase-1**: Filtered persons undergo crowd analysis

#### Input/Output Mapping
- **Pipeline Input**: Camera stream at 0.25 FPS (1 frame every 4 seconds)
- **Pipeline Output**: Crowd gathering alerts with metadata

## Key Configuration Parameters

### Detection Settings
- **Model Resolution**: 416×416 (optimized for speed)
- **Stream Resolution**: 640×360 (balanced quality/performance)
- **Confidence Threshold**: 0.4 (detection) → 0.5 (filtering)
- **Processing Rate**: 0.25 FPS (sufficient for crowd analysis)

### Crowd Analysis Settings
- **Count Threshold**: 20 people (configurable per zone)
- **Temporal Filtering**: 5 consecutive frames must violate threshold
- **Alert Frequency**: 10-minute intervals to prevent spam
- **Severity Level**: Medium priority

### Zone Configuration
- **Zone Name**: "ZoneCrowd"
- **Pivot Point**: Midpoint of bounding box
- **Purpose**: Designated area for crowd monitoring

## Performance Characteristics

### Hardware Allocation
- **Node**: `framequeues-10`
- **GPU**: ID 0
- **Cluster**: `default-cluster`

### Processing Features
- **Low Frame Rate**: 0.25 FPS for efficient crowd monitoring
- **GPU Acceleration**: Used for object detection
- **Memory Mode**: In-memory processing for low latency
- **Drawing Output**: 1920×1080 for visualization

### Alert Management
- **Storage**: MinIO for alert data and evidence
- **Database**: MongoDB for alert metadata
- **Real-time**: Redis for live alert streaming
- **Visualization**: MJPEG stream with crowd highlighting

## Use Case Applications

### Public Safety
- **Event Venues**: Monitor for overcrowding at concerts, festivals
- **Transportation Hubs**: Detect dangerous crowd densities in stations
- **Emergency Exits**: Ensure fire safety compliance
- **Public Squares**: Monitor protests or gatherings

### Security Monitoring
- **Restricted Areas**: Detect unauthorized group gatherings
- **Perimeter Security**: Monitor for organized intrusions
- **Building Management**: Occupancy control and fire safety

### Business Analytics
- **Retail Analytics**: Peak hour analysis and space utilization
- **Queue Management**: Monitor waiting area congestion
- **Event Planning**: Capacity management and flow analysis

## Algorithm Logic

### Processing Flow
1. **Object Detection**: Identify all objects in the scene (every 4 seconds)
2. **Person Filtering**: Keep only person detections with confidence > 0.5
3. **Zone Filtering**: Count only persons within "ZoneCrowd"
4. **Temporal Analysis**: Track count over 5 consecutive frames
5. **Threshold Comparison**: Check if count exceeds 20 people
6. **Alert Generation**: Create alerts for confirmed crowd gathering events
7. **Alert Management**: Enforce 10-minute intervals between repeated alerts

### Crowd Detection Algorithm
```python
def detect_crowd_gathering(filtered_persons, config):
    zone_count = count_persons_in_zone(filtered_persons, "ZoneCrowd")
    
    if zone_count >= config.countThreshold["ZoneCrowd"]:
        violation_count += 1
        if violation_count >= config.ViolationFrameCount:
            if time_since_last_alert >= config.alert_interval:
                return create_crowd_alert(zone_count, config.severity)
    else:
        violation_count = 0
    
    return None
```

### Optimization Features
- **Low Frequency Processing**: 0.25 FPS reduces computational load
- **Temporal Filtering**: 5-frame requirement reduces false positives
- **Zone-based Counting**: Focuses analysis on relevant areas
- **Alert Rate Limiting**: Prevents notification fatigue

## Configuration Guidelines

### High-Risk Venues (Stadiums, Concerts)
```json
{
  "countThreshold": {"ZoneCrowd": 50},
  "ViolationFrameCount": 3,
  "alert_interval": 300,
  "severity": "high"
}
```

### Public Transportation
```json
{
  "countThreshold": {"ZoneCrowd": 30},
  "ViolationFrameCount": 5,
  "alert_interval": 600,
  "severity": "medium"
}
```

### Retail Environments
```json
{
  "countThreshold": {"ZoneCrowd": 15},
  "ViolationFrameCount": 7,
  "alert_interval": 900,
  "severity": "low"
}
```

### Emergency Situations
```json
{
  "countThreshold": {"ZoneCrowd": 100},
  "ViolationFrameCount": 1,
  "alert_interval": 60,
  "severity": "critical",
  "stampedeThreshold": {"movement_speed": 5.0}
}
```

## Technical Notes

### Strengths
- **Simplified Pipeline**: Minimal components for efficient crowd counting
- **Low Resource Usage**: 0.25 FPS processing conserves resources
- **Robust Filtering**: Temporal analysis reduces false positives
- **Scalable Thresholds**: Configurable per zone and use case
- **Comprehensive Alerts**: Full integration with monitoring systems

### Limitations
- **No Tracking**: Cannot analyze crowd movement patterns
- **Single Zone**: Limited to one crowd monitoring area
- **Basic Analysis**: No crowd behavior or density analysis
- **Static Thresholds**: Limited adaptability to dynamic conditions

### Advanced Features Available
- **Area-based Analysis**: Density per square meter calculations
- **Stampede Detection**: Movement-based emergency detection
- **Multi-zone Support**: Extension to multiple crowd areas
- **Temporal Patterns**: Historical crowd pattern analysis

## Integration Requirements

### Upstream Dependencies
- Camera with stable positioning for accurate counting
- Zone definitions for "ZoneCrowd" area
- Network connectivity for alert delivery

### Downstream Integrations
- Emergency response systems
- Public address systems for crowd control
- Building management systems
- Analytics dashboards for capacity planning

### Calibration Requirements
- Zone boundary definition based on physical space
- Threshold tuning based on normal occupancy patterns
- Alert interval adjustment based on response capabilities
- Confidence threshold optimization based on lighting conditions

## Emergency Response Integration

### Alert Escalation
- **Low Severity**: Monitoring dashboard notification
- **Medium Severity**: Security team notification
- **High Severity**: Emergency services notification
- **Critical Severity**: Automatic emergency response activation

### Response Actions
- **Public Announcements**: Automated crowd dispersal messages
- **Access Control**: Entrance/exit management
- **Emergency Services**: Automatic 911/emergency calls
- **Evacuation Procedures**: Integration with building safety systems

This crowd gathering detection pipeline provides an efficient solution for monitoring crowd density in designated areas, with flexible thresholds and comprehensive alert management suitable for various public safety and security applications.
