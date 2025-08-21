# Abandoned Bag Detection Pipeline Documentation

## Overview
This document provides a comprehensive analysis of the `0001_AbandonedBag_camera_70_10.json` blueprint, which defines a complete end-to-end computer vision pipeline for detecting abandoned bags and luggage. The pipeline combines multi-model object detection, association logic, and temporal tracking to identify luggage that has been left unattended for extended periods.

## Pipeline Identity

### Component Information
- **Component ID**: `abandonedBag_camera_100_100`
- **Component Type**: `node.algorithm.pipeline`
- **Parser Version**: `Parser/V1`
- **Pipeline UID**: `abandonedBag_camera_100_100`
- **Version**: `v0.0.1`
- **Release Tag**: `stable`

### Template Configuration
- **Template Type**: `template.vdag.app-layout.sample-vdag:v0.0.1-beta`
- **Runtime ID**: `default-mdag`
- **Database Location**: `framequeues-6`

## Source Configuration

### Camera Input Settings
- **Assignment Type**: `source`
- **Source ID**: `camera_100_100`
- **Controller Node**: `framequeues-6`

### Stream Parameters
- **Frame Rate**: 4 FPS (`"4/1"`)
- **Actuation Frequency**: 1
- **GPU ID**: 0
- **GPU Enabled**: Yes
- **Allocation Node**: `framequeues-6`
- **Mode**: Memory-based processing
- **Loop Video**: Enabled (for testing)
- **Live Stream**: Enabled
- **Frame Quality**: 90%
- **Color Format**: BGR
- **Camera Retry Interval**: 30 seconds

### Global Settings
- **Alert URL**: `http://test-alerts.io`
- **Alert ID URL**: `http://serverip:serverport/getalertid`
- **Test Configuration**: Custom parameters for pipeline testing

## Pipeline Components Analysis

### 1. General Object Detection Node (`obj-det-1`)

#### Component Details
- **Component URI**: `node.algorithm.objdet.general7Detection_1080_1920:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Detects general objects including persons and various items

#### Configuration
- **Hardware**: GPU-accelerated with FP16 precision
- **Batch Processing**: Enabled (batch size 8)
- **Decoder**: DALI with Gaussian interpolation
- **Input Resolution**: 896×896
- **Decoder Resolution**: 1920×1080
- **Full Image**: Enabled
- **Stretch Image**: Disabled
- **Block ROI**: Disabled

#### Parameters
- **Confidence Threshold**: 0.4
- **NMS IoU**: 0.4
- **MJPEG Output**: Disabled
- **Alerts**: Disabled
- **Drawing**: Zone and ROI visualization enabled

#### Scale Specification
- **Cluster ID**: `default-cluster`
- **Machine ID**: `framequeues-6`
- **GPU ID**: 0
- **Drawing Component**: `node.utils.drawing.drawing:v0.0.1-stable`
- **Output Resolution**: 1920×1080

### 2. Luggage Detection Node (`luggage-det-1`)

#### Component Details
- **Component URI**: `node.algorithm.objdet.luggage7Detection_1080_1920:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Specialized luggage and bag detection model

#### Configuration
- **Hardware**: GPU-accelerated with FP16 precision
- **Batch Processing**: Enabled (batch size 8)
- **Decoder**: DALI with Gaussian interpolation
- **Input Resolution**: 896×896
- **Decoder Resolution**: 1920×1080
- **Full Image**: Enabled
- **Stretch Image**: Disabled
- **Block ROI**: Disabled

#### Parameters
- **Confidence Threshold**: 0.7 (higher threshold for luggage specificity)
- **NMS IoU**: 0.4
- **MJPEG Output**: Disabled
- **Alerts**: Disabled
- **Drawing**: Zone and ROI visualization enabled

### 3. Policy Filtering Node (`policy-obj-1`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Policy
- **Purpose**: Multi-stage filtering and association logic

#### Filter Configuration

##### Class Confidence Filter
```json
{
  "score": 0.1,
  "allowed_classes": [
    "person",
    "luggage", 
    "suitcase",
    "backpack",
    "handbag"
  ]
}
```

##### Zone Filtering
```json
{
  "zone": ["ZoneAbandoned"],
  "pivotPoint": "bottomPoint"
}
```

##### Class Replacement Logic
```json
{
  "class_replace_tuples": [
    ["suitcase", "luggage"],
    ["backpack", "luggage"], 
    ["handbag", "luggage"]
  ]
}
```

##### Person-Luggage Association
- **Type**: `pixel2d`
- **Distance Threshold**: 250 pixels
- **Selection**: Many objects
- **Comparison**: Person to luggage proximity
- **Primary**: Person (groups luggage with nearby persons)
- **Policy**: Group association

##### Duplicate Elimination
- **Type**: `pixel2d`
- **Distance Threshold**: 5 pixels
- **Selection**: Many-to-many comparison
- **Comparison**: Luggage-to-luggage and person-to-person
- **Primary**: Both luggage and person
- **Policy**: Keep1 (eliminate duplicates)

### 4. Object Tracking Node (`tracker-det-1`)

#### Component Details
- **Component URI**: `node.algorithm.tracker.trackerlite:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Multi-object tracking for maintaining object identity over time

#### Configuration
- **TTL**: 4 frames (time-to-live for lost tracks)
- **Tracker Type**: NONE (basic tracking without advanced features)
- **Batch Processing**: Enabled (batch size 8)

### 5. Abandoned Object Detection Engine (`usecase-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecase:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Final abandoned object detection logic

#### Configuration
```json
{
  "abandonedObjectDetection": {
    "alert_interval": 300,
    "severity": "medium",
    "timeThreshold": 60,
    "selected_objects": ["luggage"],
    "distance_ratio": 2,
    "resetSeconds": 5
  }
}
```

#### Alert System Integration
- **MongoDB Integration**: `VIP_ALERT` database
- **Redis Integration**: Real-time data push
- **MinIO Storage**: Alert data storage
- **Component URI**: `node.utils.alert.alert:v0.0.1-stable`

## Pipeline Data Flow Architecture

### Flow Diagram
```
Input Stream (Camera: 4 FPS, BGR, 1920×1080)
       ↓
   ┌─────────────────────────────────────┐
   │ Parallel Object Detection           │
   │                                     │
   │ [obj-det-1] ──────┐                │
   │ (General Objects)  │                │
   │                    ↓                │
   │ [luggage-det-1] ──→ [policy-obj-1]  │
   │ (Luggage Specific) (Multi-Filter)   │
   └─────────────────────┼───────────────┘
                         ↓
                  [tracker-det-1]
               (Multi-Object Tracking)
                         ↓
                   [usecase-1]
            (Abandoned Object Detection)
                         ↓
               Abandoned Bag Alert
```

### Detailed Connection Graph

#### Input Connections
- **obj-det-1**: Receives camera input stream
- **luggage-det-1**: Receives camera input stream (parallel processing)

#### Processing Chain
1. **obj-det-1** + **luggage-det-1** → **policy-obj-1** (Dual-input filtering)
2. **policy-obj-1** → **tracker-det-1** (Object tracking)
3. **tracker-det-1** → **usecase-1** (Abandoned detection)

#### Multi-Input Processing
- **policy-obj-1** receives inputs from both detection models
- **usecase-1** processes tracked objects for abandonment analysis

## Abandoned Bag Detection Logic

### Multi-Model Detection Strategy

The pipeline employs a dual-detection approach:

#### 1. General Object Detection Path
- Detects persons and general objects with moderate confidence (0.4)
- Provides context for person-luggage associations
- Establishes baseline object presence

#### 2. Specialized Luggage Detection Path
- Uses dedicated luggage detection model with higher confidence (0.7)
- Specifically trained for bags, suitcases, backpacks, and handbags
- Provides precise luggage identification

#### 3. Policy-Based Association
- **Zone Filtering**: Only processes objects within "ZoneAbandoned"
- **Class Normalization**: Converts all bag types to "luggage" class
- **Proximity Analysis**: Associates luggage with nearby persons (250-pixel threshold)
- **Duplicate Removal**: Eliminates overlapping detections (5-pixel threshold)

#### 4. Temporal Tracking
- Maintains object identity across frames
- Tracks movement patterns
- Monitors person-luggage relationships over time

#### 5. Abandonment Detection
- **Time Threshold**: 60 seconds without associated person
- **Distance Analysis**: Uses 2:1 distance ratio for separation detection
- **Reset Logic**: 5-second reset period for re-association
- **Alert Interval**: 300 seconds between repeated alerts

### Alert Generation

#### Alert Characteristics
- **Severity**: Medium (security concern)
- **Database Storage**: MongoDB with full metadata
- **Real-time Notification**: Redis pub/sub
- **Evidence Storage**: MinIO with video clips
- **Drawing Overlay**: Real-time visualization

#### Alert Data Structure
```json
{
  "alert_type": "abandoned_bag",
  "severity": "medium", 
  "time_threshold": 60,
  "abandon_duration": "calculated_seconds",
  "object_details": {
    "class": "luggage",
    "confidence": "detection_confidence",
    "last_person_association": "timestamp"
  },
  "location": "ZoneAbandoned",
  "timestamp": "unix_timestamp",
  "evidence": {
    "video_clip": "minio_url",
    "detection_sequence": "tracking_data"
  }
}
```

## Hardware & Performance Specifications

### Hardware Requirements
- **GPU**: Required (NVIDIA with CUDA 11.0+)
- **GPU Memory**: Minimum 6GB (dual models + tracking)
- **CPU**: Multi-core for parallel processing
- **RAM**: 12GB recommended
- **Storage**: SSD for real-time video processing

### Performance Characteristics
- **Input FPS**: 4 FPS (optimized for accuracy and resource efficiency)
- **Processing Latency**: ~300-600ms per frame
- **Alert Latency**: 60-65 seconds (detection + threshold)
- **Concurrent Streams**: Single stream per pipeline instance
- **Resource Utilization**: Medium-High (dual AI models)

### Scalability
- **Horizontal Scaling**: Deploy multiple pipeline instances
- **Load Balancing**: Distribute streams across instances
- **GPU Sharing**: Efficient batch processing
- **Database Scaling**: MongoDB clustering for alerts

## Configuration Tuning Guidelines

### High Security Areas (Airports, Banks)
```json
{
  "timeThreshold": 30,
  "luggage_confidence": 0.8,
  "distance_ratio": 1.5,
  "alert_interval": 180
}
```

### Public Spaces (Malls, Stations)
```json
{
  "timeThreshold": 60,
  "luggage_confidence": 0.7,
  "distance_ratio": 2,
  "alert_interval": 300
}
```

### Low Security Areas (Parks, Open Spaces)
```json
{
  "timeThreshold": 120,
  "luggage_confidence": 0.6,
  "distance_ratio": 3,
  "alert_interval": 600
}
```

## Integration & Deployment

### Prerequisites
1. **Camera System**: RTSP stream or video file
2. **GPU Infrastructure**: CUDA-compatible GPU
3. **Database Systems**: MongoDB, Redis, MinIO
4. **Network**: Moderate bandwidth for 4 FPS streaming
5. **Zone Configuration**: Define "ZoneAbandoned" areas

### Deployment Steps
1. **Infrastructure Setup**: Deploy database services
2. **Model Deployment**: Load dual AI models on GPU nodes
3. **Zone Definition**: Configure abandonment detection zones
4. **Camera Integration**: Configure video streams
5. **Alert System**: Connect notification endpoints
6. **Threshold Tuning**: Adjust time and distance parameters

### Monitoring & Maintenance
- **Performance Metrics**: FPS, GPU utilization, memory usage
- **Alert Quality**: False positive/negative rates
- **Model Performance**: Detection accuracy monitoring
- **System Health**: Component status monitoring

## Use Cases & Applications

### Primary Applications
- **Airports**: Terminal and gate area monitoring
- **Train Stations**: Platform and waiting area security
- **Shopping Malls**: Common area surveillance
- **Office Buildings**: Lobby and corridor monitoring
- **Public Events**: Crowd gathering security
- **Transportation Hubs**: Bus terminals and metro stations

### Detection Scenarios
- **Forgotten Luggage**: Travelers leaving bags unattended
- **Suspicious Packages**: Deliberately placed objects
- **Lost Property**: Accidentally dropped items
- **Security Threats**: Potential explosive devices
- **Theft Prevention**: Monitoring valuable items

## Limitations & Considerations

### Technical Limitations
- **Lighting Conditions**: Performance may degrade in low light
- **Camera Angle**: Requires clear view of ground level
- **Occlusion**: Dense crowds may affect detection
- **False Positives**: Legitimate temporary placement

### Environmental Factors
- **Crowd Density**: High traffic areas may cause confusion
- **Object Size**: Very small items may be missed
- **Background Clutter**: Busy environments increase complexity
- **Lighting Changes**: Dramatic lighting shifts affect tracking

### Ethical Considerations
- **Privacy**: Ensure compliance with surveillance regulations
- **Data Retention**: Implement appropriate data lifecycle policies
- **Accessibility**: Consider impacts on disabled individuals
- **Transparency**: Document system capabilities and limitations

## Future Enhancements

### Potential Improvements
1. **Multi-Camera Fusion**: Coordinate across multiple camera views
2. **3D Spatial Analysis**: Depth-based distance calculations
3. **Person Re-identification**: Track persons across camera boundaries
4. **Behavioral Analysis**: Analyze suspicious placement patterns
5. **Mobile Integration**: Security personnel mobile alerts
6. **AI-Based Tuning**: Adaptive threshold adjustment

### Advanced Features
- **Owner Recognition**: Associate bags with specific individuals
- **Bag Classification**: Distinguish between bag types and threat levels
- **Predictive Analytics**: Identify high-risk abandonment patterns
- **Integration APIs**: Connect with existing security systems

## References & Documentation

### Algorithm References
- YOLOv7 Object Detection: https://arxiv.org/abs/2207.02696
- Multi-Object Tracking: Deep SORT and similar algorithms
- Policy-Based Filtering: Computer vision pipeline optimization

### System Documentation
- AIOS Pipeline Framework
- Docker Container Specifications
- Database Schema Documentation
- Alert System Integration Guide

## Troubleshooting Guide

### Common Issues
1. **High False Positives**: Adjust time threshold and distance ratio
2. **Missed Detections**: Check camera positioning and model confidence
3. **Performance Issues**: Optimize batch sizes and GPU allocation
4. **Alert Delays**: Review tracking and threshold parameters

### Performance Optimization
- **GPU Utilization**: Balance batch sizes across dual models
- **Memory Management**: Monitor and optimize tracking memory usage
- **Network Optimization**: Ensure sufficient bandwidth for 4 FPS
- **Database Tuning**: Optimize alert storage and retrieval

This comprehensive pipeline represents an advanced approach to abandoned object detection, combining specialized AI models with sophisticated association logic to provide reliable security monitoring capabilities in various environments.
