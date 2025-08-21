# Parking Violation Detection Pipeline Documentation

## Overview
This document provides a comprehensive analysis of the `parking_violation.json` blueprint, which defines a complete end-to-end computer vision pipeline for detecting parking violations in surveillance environments. The pipeline implements a vehicle-focused approach with vehicle detection, zone filtering, tracking, and temporal analysis to identify unauthorized parking.

## Pipeline Identity

### Component Information
- **Component ID**: `parking_violation`
- **Component Type**: `node.algorithm.pipeline`
- **Parser Version**: `Parser/V1`
- **Pipeline UID**: `parkingViolation_camera_100_100`
- **Version**: `v0.0.1`
- **Release Tag**: `stable`

### Template Configuration
- **Template Type**: `template.vdag.app-layout.sample-vdag:v0.0.1-beta`
- **Runtime ID**: `default-mdag`
- **Database Location**: `framequeues-2`

## Source Configuration

### Camera Input Settings
- **Assignment Type**: `source`
- **Source ID**: `camera_100_100`
- **Controller Node**: `framequeues-2`

### Stream Parameters
- **Frame Rate**: 1 FPS (`"1/1"`)
- **Actuation Frequency**: 1
- **GPU ID**: 2
- **GPU Enabled**: Yes
- **Allocation Node**: `framequeues-2`
- **Mode**: Memory-based processing
- **Loop Video**: Enabled (for testing)
- **Live Stream**: Enabled
- **Frame Quality**: 90%
- **Color Format**: BGR

### Global Settings
- **Alert URL**: `http://test-alerts.io`
- **Alert ID URL**: `http://serverip:alertidport/getalertid`
- **Test Configuration**: Custom parameters for pipeline testing

## Pipeline Components Analysis

### 1. Vehicle Detection Node (`obj-det-1`)

#### Component Details
- **Component URI**: `node.algorithm.objdet.vehicles5Detection_360h_640:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Specialized vehicle detection model for parking scenarios

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
- **Machine ID**: `framequeues-2`
- **GPU ID**: 2
- **MJPEG Drawing**: Enabled
- **Drawing Component**: `node.utils.drawing.drawing:v0.0.1-stable`
- **Output Resolution**: 1920×1080

### 2. Vehicle Policy Filter Node (`policy-1`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Filter vehicle detections within parking zones

#### Filter Configuration
```json
{
  "class_filter": {
    "allowed_classes": [
      "car",
      "bus", 
      "truck",
      "auto_rickshaw",
      "bike",
      "motorbike"
    ]
  },
  "inside_zone": {
    "zone": ["ZoneParking"],
    "pivotPoint": "midPoint"
  }
}
```

#### Key Features
- **Vehicle Class Filtering**: Comprehensive vehicle type detection
  - **Four-wheelers**: car, bus, truck, auto_rickshaw
  - **Two-wheelers**: bike, motorbike
- **Zone Filtering**: Restricts detection to "ZoneParking" area
- **Pivot Point**: Uses midpoint of bounding box for zone membership
- **No Confidence Threshold**: Relies on detection model confidence

### 3. Vehicle Tracking Node (`tracker-1`)

#### Component Details
- **Component URI**: `node.algorithm.tracker.trackerlite:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Lightweight tracking for maintaining vehicle identity

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
- **T Min**: 8 (minimum track length - higher than loitering pipeline)

#### Features
- **Drawing**: Comprehensive visualization (zones, ROIs, lines, arrows, trajectories)
- **Calibration**: Enabled for spatial awareness
- **Track Persistence**: 8-frame minimum for stable vehicle tracking

### 4. Dwell Time Policy Node (`policy-2`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Apply dwell time filtering for parking pre-processing

#### Filter Configuration
```json
{
  "dwell": {
    "loiteringThresholdSeconds": 3,
    "resetSeconds": 10
  }
}
```

#### Purpose
- **Pre-filtering**: Initial dwell time check (3 second threshold)
- **Reset Mechanism**: 10-second reset period for track management
- **Performance Optimization**: Reduces data flow to final usecase node
- **Quick Response**: Elimination of very transient vehicles (drive-through traffic)

### 5. Parking Violation Usecase Node (`usecase-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecase:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Final parking violation detection and alert generation

#### Parking Violation Configuration
```json
{
  "parkingViolation": {
    "loiteringThresholdSeconds": 120,
    "alert_interval": 600,
    "severity": "medium"
  }
}
```

#### Key Parameters
- **Violation Threshold**: 120 seconds (2 minutes)
- **Alert Interval**: 600 seconds (10 minutes between repeated alerts)
- **Severity Level**: Medium priority alerts

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
Input Stream (Camera: 1 FPS, BGR, 640×360)
       ↓
[obj-det-1]
(Vehicle Detection: cars, buses, trucks, bikes)
       ↓
[policy-1]
(Vehicle Zone Filtering: ZoneParking)
       ↓
[tracker-1]
(Vehicle Tracking: 8-frame min track)
       ↓
[policy-2]
(Dwell Time Pre-filter: 3s + 10s reset)
       ↓
[usecase-1]
(Parking Violation: 120s + Alert Generation)
       ↓
Alert Output (MinIO + MongoDB + Redis)
```

### Detailed Connection Graph

#### Sequential Processing Chain
1. **obj-det-1** → **policy-1**: Vehicle detection feeds into vehicle filtering
2. **policy-1** → **tracker-1**: Filtered vehicles are tracked
3. **tracker-1** → **policy-2**: Tracked vehicles undergo dwell time pre-filtering
4. **policy-2** → **usecase-1**: Final parking violation analysis and alert generation

#### Input/Output Mapping
- **Pipeline Input**: Camera stream at 1 FPS
- **Pipeline Output**: Parking violation alerts with metadata

## Key Configuration Parameters

### Detection Settings
- **Model**: Specialized vehicle detection (5 vehicle classes)
- **Model Resolution**: 416×416 (optimized for speed)
- **Stream Resolution**: 640×360 (balanced quality/performance)
- **Confidence Threshold**: 0.4
- **Processing Rate**: 1 FPS (sufficient for parking analysis)

### Tracking Settings
- **Tracking Type**: Lightweight (no re-identification)
- **Track TTL**: 4 frames
- **IoU Threshold**: 0.45
- **Minimum Track Length**: 8 frames (stable tracking)
- **Batch Size**: 16 (high throughput)

### Parking Logic
- **Pre-filter Threshold**: 3 seconds (quick elimination of drive-through traffic)
- **Reset Period**: 10 seconds (track lifecycle management)
- **Final Threshold**: 120 seconds (2 minutes)
- **Alert Interval**: 600 seconds (10 minutes)
- **Severity Level**: Medium

### Zone Configuration
- **Zone Name**: "ZoneParking"
- **Pivot Point**: Midpoint of bounding box
- **Purpose**: Restrict analysis to designated parking areas

## Performance Characteristics

### Hardware Allocation
- **Node**: `framequeues-2`
- **GPU**: ID 2 (dedicated for parking detection)
- **Cluster**: `default-cluster`

### Processing Features
- **Processing Rate**: 1 FPS for efficient parking monitoring
- **GPU Acceleration**: Used for vehicle detection and tracking
- **Memory Mode**: In-memory processing for low latency
- **Drawing Output**: 1920×1080 for visualization

### Alert Management
- **Storage**: MinIO for alert data and evidence
- **Database**: MongoDB for alert metadata
- **Real-time**: Redis for live alert streaming
- **Visualization**: MJPEG stream for monitoring

## Use Case Applications

### Traffic Management
- **No Parking Zones**: Detect vehicles in restricted areas
- **Fire Lanes**: Ensure emergency access routes remain clear
- **Loading Zones**: Monitor unauthorized parking in commercial areas
- **Bus Stops**: Prevent blocking of public transportation

### Parking Enforcement
- **Time-Limited Parking**: Detect overstay violations
- **Paid Parking Areas**: Monitor unauthorized parking
- **Reserved Parking**: Detect violations in designated spaces
- **Disabled Parking**: Monitor misuse of accessibility spaces

### Security Applications
- **Perimeter Security**: Detect unauthorized vehicles near restricted areas
- **Building Security**: Monitor parking violations near sensitive facilities
- **Event Management**: Control parking during special events

## Algorithm Logic

### Processing Flow
1. **Vehicle Detection**: Identify vehicles in the scene (every second)
2. **Vehicle Filtering**: Keep only vehicles in specified classes
3. **Zone Filtering**: Retain only vehicles within "ZoneParking"
4. **Vehicle Tracking**: Assign and maintain unique IDs for vehicles
5. **Pre-filtering**: Quick elimination of vehicles present < 3 seconds
6. **Parking Analysis**: Detailed analysis for vehicles present > 120 seconds
7. **Alert Generation**: Create alerts for confirmed parking violations

### Parking Detection Algorithm
```python
def detect_parking_violation(tracked_vehicles, config):
    for vehicle in tracked_vehicles:
        if is_in_parking_zone(vehicle.position, "ZoneParking"):
            dwell_time = calculate_dwell_time(vehicle)
            
            # Pre-filter: eliminate drive-through traffic
            if dwell_time < config.pre_filter_threshold:
                continue
            
            # Check for violation
            if dwell_time >= config.violation_threshold:
                if should_generate_alert(vehicle, config.alert_interval):
                    return create_parking_alert(vehicle, dwell_time, config.severity)
    
    return None
```

### Optimization Features
- **Two-stage Thresholding**: 3s pre-filter + 120s violation threshold
- **Vehicle-specific Tracking**: Optimized for vehicle movement patterns
- **Zone-based Processing**: Reduces computational load
- **Reset Mechanism**: Handles intermittent occlusions

## Configuration Guidelines

### High-Security Areas (Fire Lanes, Emergency Access)
```json
{
  "loiteringThresholdSeconds": 30,
  "alert_interval": 180,
  "severity": "high",
  "pre_filter": 1
}
```

### Commercial Loading Zones
```json
{
  "loiteringThresholdSeconds": 300,
  "alert_interval": 600,
  "severity": "medium",
  "pre_filter": 5
}
```

### Public Parking Areas
```json
{
  "loiteringThresholdSeconds": 600,
  "alert_interval": 1800,
  "severity": "low",
  "pre_filter": 10
}
```

### Time-Limited Parking (e.g., 15-minute parking)
```json
{
  "loiteringThresholdSeconds": 900,
  "alert_interval": 300,
  "severity": "medium",
  "pre_filter": 3
}
```

## Technical Notes

### Strengths
- **Vehicle-Specific Detection**: Specialized model for vehicle types
- **Comprehensive Vehicle Coverage**: Supports cars, trucks, buses, bikes
- **Robust Tracking**: 8-frame minimum reduces false positives
- **Two-stage Filtering**: Efficient elimination of transient traffic
- **Flexible Thresholds**: Configurable for different parking scenarios

### Limitations
- **No License Plate Recognition**: Cannot identify specific vehicles
- **Basic Tracking**: No re-identification across occlusions
- **Single Zone**: Limited to one parking area
- **Fixed Thresholds**: Limited adaptability to traffic patterns

### Advanced Features Potential
- **License Plate Integration**: Vehicle identification for enforcement
- **Multi-zone Support**: Monitor multiple parking areas
- **Dynamic Thresholds**: Time-based violation periods
- **Payment Integration**: Connect with parking payment systems

## Integration Requirements

### Upstream Dependencies
- Camera with clear view of parking area
- Zone definitions for "ZoneParking" area
- Network connectivity for alert delivery
- Stable lighting conditions for vehicle detection

### Downstream Integrations
- Parking enforcement systems
- Traffic management centers
- Municipal citation systems
- Revenue collection systems
- Security monitoring platforms

### Calibration Requirements
- Zone boundary definition based on parking space layout
- Threshold tuning based on typical parking patterns
- Alert interval adjustment based on enforcement capacity
- Vehicle type filtering based on local regulations

## Enforcement Integration

### Alert Processing
- **Immediate Alerts**: Security personnel notification
- **Citation Generation**: Automatic violation documentation
- **Evidence Collection**: Image/video capture for enforcement
- **Appeal Management**: Evidence preservation for disputes

### Compliance Monitoring
- **Violation Statistics**: Track violation patterns by time/location
- **Enforcement Effectiveness**: Monitor response times and resolution
- **Revenue Tracking**: Monitor citation and payment processing
- **Pattern Analysis**: Identify repeat violators and problem areas

This parking violation detection pipeline provides an efficient solution for automated parking enforcement, with specialized vehicle detection and configurable violation thresholds suitable for various parking management scenarios.
