# Group Running Detection Pipeline Documentation

## Overview
This document provides a comprehensive analysis of the `0001_groupRunning_camera_55_53_13.json` blueprint, which defines a complete end-to-end computer vision pipeline for detecting groups of people running together. The pipeline combines object detection, multi-class association, tracking, and speed estimation to identify coordinated group running behavior, useful for security monitoring and crowd behavior analysis.

## Pipeline Identity

### Component Information
- **Component ID**: `groupRunning_camera_55_53_13`
- **Component Type**: `node.algorithm.pipeline`
- **Parser Version**: `Parser/V1`
- **Pipeline UID**: `groupRunning_camera_55_53_13`
- **Version**: `v0.0.1`
- **Release Tag**: `stable`

### Template Configuration
- **Template Type**: `template.vdag.app-layout.sample-vdag:v0.0.1-beta`
- **Runtime ID**: `default-mdag`
- **Database Location**: `framequeues-1`

## Source Configuration

### Camera Input Settings
- **Assignment Type**: `source`
- **Source ID**: `camera_55_53_13`
- **Controller Node**: `framequeues-1`

### Stream Parameters
- **Frame Rate**: 5 FPS (`"5/1"`)
- **Actuation Frequency**: 1
- **GPU ID**: 0
- **GPU Enabled**: Yes
- **Allocation Node**: `framequeues-1`
- **Mode**: Memory-based processing
- **Loop Video**: Enabled (for testing)
- **Live Stream**: Enabled
- **Frame Quality**: 90%
- **Color Format**: BGR

### Global Settings
- **Alert URL**: `http://test-alerts.io`
- **Alert ID URL**: `http://serverip:serverport/getalertid`
- **Test Configuration**: Custom parameters for pipeline testing

## Pipeline Components Analysis

### 1. Object Detection Node (`obj-det-1`)

#### Component Details
- **Component URI**: `node.algorithm.objdet.general7Detection_360h_640:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Detects people and vehicles for group analysis

#### Configuration
- **Hardware**: GPU-accelerated with FP16 precision
- **Batch Processing**: Enabled (batch size 8)
- **Decoder**: DALI with Gaussian interpolation
- **Input Resolution**: 416×416
- **Decoder Resolution**: 640×360 (wide-angle optimized)
- **Full Image**: Enabled
- **Stretch Image**: Disabled
- **Block ROI**: Disabled

#### Parameters
- **Confidence Threshold**: 0.2 (low threshold for comprehensive detection)
- **IoU Threshold**: 0.45
- **Max Detections**: 300 (handles dense crowds)
- **MJPEG Output**: Disabled
- **Alerts**: Disabled

#### Scale Specification
- **Cluster ID**: `default-cluster`
- **Machine ID**: `framequeues-1`
- **GPU ID**: 0
- **Drawing Component**: `node.utils.drawing.drawing:v0.0.1-stable`
- **Output Resolution**: 1920×1080

### 2. Multi-Class Policy Filtering Node (`policy-1`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Policy
- **Purpose**: Filter and associate multiple object classes within zones

#### Filter Configuration

##### Class Filtering
```json
{
  "allowed_classes": [
    "person", "bicycle", "car", "truck", "bus", "motorcycle", "auto_rickshaw"
  ]
}
```

##### Zone Filtering
```json
{
  "zone": ["ZoneRunning"],
  "pivotPoint": "bottomPoint"
}
```

##### Multi-Class Association
```json
{
  "type": "pixel2d",
  "sort": "descending",
  "selection": ["many", "many", "many", "many", "many", "many"],
  "comparisons": [
    ["person", "bicycle"],
    ["person", "car"],
    ["person", "truck"],
    ["person", "bus"],
    ["person", "motorcycle"],
    ["person", "auto_rickshaw"]
  ]
}
```

### 3. Person-Specific Policy Node (`policy-2`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Policy
- **Purpose**: Focus on person detections with higher confidence

#### Filter Configuration
```json
{
  "class_conf_filter": {
    "score": 0.5,
    "allowed_classes": ["person"]
  }
}
```

### 4. Advanced Object Tracking Node (`tracker-1`)

#### Component Details
- **Component URI**: `node.algorithm.tracker.trackerlitefast_960x540:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: High-performance multi-object tracking for group analysis

#### Configuration
- **Input Resolution**: 960×540
- **Decoder Resolution**: 960×540
- **Object Type**: General
- **Batch Processing**: Enabled (batch size 8)

#### Advanced Tracking Parameters
- **Max Age**: 9 frames
- **Age Penalty**: 2
- **Motion Weight**: 0.4
- **Max Association Cost**: 0.8
- **Max Re-ID Cost**: 0.6
- **IoU Threshold**: 0.4
- **Duplicate Threshold**: 0.5
- **Occlusion Threshold**: 0.4
- **Confidence Threshold**: 0.15
- **Confirm Hits**: 1
- **History Size**: 50 frames
- **Detector Skip Frame**: 1

### 5. Group Running Detection Engine (`usecase-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecase:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Speed estimation and group running behavior analysis

#### Configuration
```json
{
  "speedEstimation": {
    "source_fps": 25,
    "include_speed": false,
    "min_distance": 1,
    "speedThreshold": 10,
    "speedviolation_counter": 2,
    "stationary_counter": 10,
    "stationary_distance": 3,
    "max_possible_speed": 13,
    "clear_past_ids_sec": 60,
    "valid_points_realworld": 2,
    "stationary_frames": 10,
    "group_count": 3,
    "group_running_interval": 15,
    "alert_interval": 300,
    "severity": "medium"
  }
}
```

#### Alert System Integration
- **MongoDB Integration**: `PROJECT_ALERT` database
- **Redis Integration**: Real-time data push
- **MinIO Storage**: Alert data storage
- **Component URI**: `node.utils.alert.alert:v0.0.1-stable`

## Pipeline Data Flow Architecture

### Flow Diagram
```
Input Stream (Camera: 5 FPS, BGR, 640×360)
       ↓
   [obj-det-1]
   (Multi-Class Detection)
       ↓
   [policy-1]
   (Multi-Class Association + Zone Filtering)
       ↓
   [policy-2]
   (Person-Specific Filtering)
       ↓
   [tracker-1]
   (Advanced Multi-Object Tracking)
       ↓
   [usecase-1]
   (Group Running Analysis)
       ↓
   Group Running Alert
```

### Detailed Connection Graph

#### Input Connections
- **obj-det-1**: Receives camera input stream

#### Processing Chain
1. **obj-det-1** → **policy-1** (Multi-class filtering and association)
2. **policy-1** → **policy-2** (Person-specific filtering)
3. **policy-2** → **tracker-1** (Advanced tracking)
4. **tracker-1** → **usecase-1** (Group analysis)

#### Sequential Processing
- Linear pipeline optimized for group behavior analysis
- Each stage refines the detection and tracking quality

## Group Running Detection Logic

### Multi-Stage Group Analysis System

The pipeline implements a sophisticated group running detection system:

#### 1. Multi-Class Object Detection
- **Primary Focus**: Person detection with vehicle context
- **Associated Objects**: Bicycles, cars, trucks, buses, motorcycles, auto-rickshaws
- **Dense Detection**: Up to 300 objects per frame
- **Low Threshold**: 0.2 confidence for comprehensive coverage

#### 2. Contextual Association
- **Person-Vehicle Proximity**: Associates people with nearby vehicles
- **Pixel-Based Distance**: 2D proximity analysis
- **Multi-Class Support**: Handles various transportation modes
- **Zone-Based**: Only within "ZoneRunning" area

#### 3. Person-Centric Filtering
- **Higher Confidence**: 0.5 threshold for person classification
- **Focus Refinement**: Eliminates low-confidence person detections
- **Quality Enhancement**: Improves tracking stability

#### 4. Advanced Tracking
- **Long-Term Tracking**: 9-frame maximum age with history
- **Motion Analysis**: Weight-based motion prediction
- **Occlusion Handling**: Robust tracking through partial occlusion
- **Re-identification**: Maintains identity across brief disappearances

#### 5. Group Running Analysis
- **Speed Threshold**: 10 units minimum for "running" classification
- **Group Count**: Minimum 3 people for group behavior
- **Temporal Validation**: 15-second interval for group confirmation
- **Spatial Proximity**: Coordinated movement analysis

### Speed Estimation Logic

#### Movement Analysis
- **Source FPS**: 25 (high temporal resolution)
- **Minimum Distance**: 1 unit movement threshold
- **Speed Calculation**: Real-world coordinate mapping
- **Stationary Detection**: 3-unit distance threshold over 10 frames

#### Group Coordination
- **Group Size**: 3+ people minimum
- **Running Interval**: 15-second confirmation window
- **Speed Synchronization**: Coordinated movement detection
- **Alert Interval**: 300 seconds between repeated alerts

### Alert Generation

#### Alert Characteristics
- **Severity**: Medium (potential security concern)
- **Database Storage**: MongoDB with full metadata
- **Real-time Notification**: Redis pub/sub
- **Evidence Storage**: MinIO with video clips
- **Drawing Overlay**: Real-time visualization

#### Alert Data Structure
```json
{
  "alert_type": "group_running",
  "severity": "medium",
  "group_analysis": {
    "group_count": "detected_count",
    "average_speed": "calculated_speed",
    "coordination_level": "movement_correlation",
    "duration": "running_duration"
  },
  "location": "ZoneRunning",
  "timestamp": "unix_timestamp",
  "evidence": {
    "video_clip": "minio_url",
    "tracking_data": "trajectory_info",
    "speed_analysis": "movement_data"
  }
}
```

## Hardware & Performance Specifications

### Hardware Requirements
- **GPU**: Required (NVIDIA with CUDA 11.0+)
- **GPU Memory**: Minimum 6GB (detection + advanced tracking)
- **CPU**: Multi-core for complex tracking algorithms
- **RAM**: 12GB recommended
- **Storage**: SSD for real-time video processing

### Performance Characteristics
- **Input FPS**: 5 FPS (optimized for accuracy)
- **Processing Latency**: ~300-600ms per frame
- **Alert Latency**: 15-315 seconds (confirmation + interval)
- **Concurrent Streams**: Single stream per pipeline instance
- **Resource Utilization**: High (complex tracking + analysis)

### Scalability
- **Horizontal Scaling**: Deploy multiple pipeline instances
- **Multi-Camera Support**: Independent pipeline per camera
- **Database Scaling**: MongoDB clustering for alerts
- **Real-time Dashboard**: Redis-based live updates

## Configuration Tuning Guidelines

### High-Security Areas (Stadiums, Airports)
```json
{
  "detection_confidence": 0.3,
  "speed_threshold": 8,
  "group_count": 2,
  "alert_interval": 180
}
```

### Public Spaces (Streets, Parks)
```json
{
  "detection_confidence": 0.2,
  "speed_threshold": 10,
  "group_count": 3,
  "alert_interval": 300
}
```

### Low-Priority Areas (Recreational Areas)
```json
{
  "detection_confidence": 0.4,
  "speed_threshold": 12,
  "group_count": 4,
  "alert_interval": 600
}
```

## Integration & Deployment

### Prerequisites
1. **Camera System**: RTSP stream or video file
2. **GPU Infrastructure**: CUDA-compatible GPU
3. **Database Systems**: MongoDB, Redis, MinIO
4. **Zone Configuration**: Define "ZoneRunning" areas
5. **Calibration**: Real-world coordinate mapping

### Deployment Steps
1. **Infrastructure Setup**: Deploy database services
2. **Model Deployment**: Load detection model on GPU nodes
3. **Zone Definition**: Configure running detection zones
4. **Camera Integration**: Configure video streams
5. **Calibration**: Set up real-world coordinate mapping
6. **Alert System**: Connect security notification endpoints

### Monitoring & Maintenance
- **Group Accuracy**: Validate against manual observations
- **Performance Metrics**: FPS, GPU utilization, memory usage
- **False Positives**: Monitor non-running group movements
- **System Health**: Component status monitoring

## Use Cases & Applications

### Primary Applications
- **Security Monitoring**: Crowd control and riot detection
- **Sports Events**: Athletic performance analysis
- **Public Safety**: Emergency evacuation monitoring
- **Traffic Management**: Pedestrian flow analysis
- **Event Security**: Concert and festival monitoring
- **Campus Safety**: School and university security

### Detection Scenarios
- **Security Threats**: Coordinated suspicious behavior
- **Emergency Situations**: Panic or evacuation responses
- **Sports Analysis**: Group training and performance
- **Crowd Dynamics**: Mass movement patterns
- **Safety Monitoring**: Dangerous group behaviors

## Limitations & Considerations

### Technical Limitations
- **Camera Angle**: Requires clear view for accurate speed estimation
- **Lighting Conditions**: Performance may degrade in low light
- **Crowd Density**: Very dense crowds may affect tracking accuracy
- **Weather Conditions**: Rain or snow may impact detection

### Group Detection Challenges
- **Coordination Definition**: Distinguishing coordinated vs. coincidental movement
- **Speed Variation**: Individual speed differences within groups
- **Temporary Grouping**: Short-term vs. sustained group behavior
- **Context Sensitivity**: Different running contexts (emergency vs. exercise)

### Ethical Considerations
- **Privacy**: Ensure compliance with surveillance regulations
- **Context Awareness**: Consider legitimate running activities
- **False Alarms**: Balance sensitivity with operational efficiency
- **Bias Monitoring**: Ensure fair detection across demographics

## Future Enhancements

### Potential Improvements
1. **Behavior Classification**: Distinguish between different running contexts
2. **Emotion Recognition**: Add stress or panic detection
3. **Multi-Camera Fusion**: Coordinate analysis across multiple views
4. **Predictive Analytics**: Anticipate group formation and movement
5. **Integration APIs**: Connect with crowd management systems
6. **ML-Based Calibration**: Automatic real-world coordinate mapping

### Advanced Features
- **Formation Analysis**: Detect specific group formations
- **Direction Prediction**: Anticipate group movement direction
- **Density Mapping**: Heat maps of group running patterns
- **Social Distance**: Pandemic-era group spacing analysis

## References & Documentation

### Algorithm References
- YOLOv7 Object Detection: https://arxiv.org/abs/2207.02696
- Multi-Object Tracking: FastMOT and similar algorithms
- Speed Estimation: Computer vision motion analysis methods

### System Documentation
- AIOS Pipeline Framework
- Docker Container Specifications
- Database Schema Documentation
- Security Alert Integration Guide

## Troubleshooting Guide

### Common Issues
1. **Missed Groups**: Lower speed threshold and group count requirements
2. **False Positives**: Increase confidence thresholds and validation time
3. **Tracking Failures**: Optimize tracking parameters for crowd density
4. **Performance Issues**: Balance batch sizes and tracking complexity

### Performance Optimization
- **Detection Tuning**: Balance confidence vs. coverage
- **Tracking Optimization**: Adjust parameters for environment
- **Speed Calculation**: Calibrate for accurate real-world mapping
- **Alert Tuning**: Balance response time with false alarm rates

This comprehensive pipeline provides reliable group running detection capabilities suitable for security monitoring, crowd management, and behavioral analysis applications, combining advanced object detection with sophisticated tracking and group behavior analysis algorithms.
