# Gesture Waving Detection Pipeline Documentation

## Overview
This document provides a comprehensive analysis of the `0001_gestureWaving_camera_31_10_14.json` blueprint, which defines a complete end-to-end computer vision pipeline for detecting hand waving gestures. The pipeline combines pose estimation, tracking, and action recognition to identify when people perform waving motions, useful for SOS signals, greetings, or attention-seeking behaviors.

## Pipeline Identity

### Component Information
- **Component ID**: `wavehandraise_camera_31_10_14`
- **Component Type**: `node.algorithm.pipeline`
- **Parser Version**: `Parser/V1`
- **Pipeline UID**: `wavehandraise_camera_31_10_14`
- **Version**: `v0.0.1`
- **Release Tag**: `stable`

### Template Configuration
- **Template Type**: `template.vdag.app-layout.sample-vdag:v0.0.1-beta`
- **Runtime ID**: `default-mdag`
- **Database Location**: `framequeues-3`

## Source Configuration

### Camera Input Settings
- **Assignment Type**: `source`
- **Source ID**: `camera_31_10_14`
- **Controller Node**: `framequeues-3`

### Stream Parameters
- **Frame Rate**: 3 FPS (`"3/1"`) - optimized for gesture analysis
- **Actuation Frequency**: 1
- **GPU ID**: 0
- **GPU Enabled**: Yes
- **Allocation Node**: `framequeues-3`
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

### 1. Pose Detection Node (`poseDet-1`)

#### Component Details
- **Component URI**: `node.algorithm.posekey.pose-estimation-rt:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Detects human pose keypoints for gesture analysis

#### Configuration
- **Hardware**: GPU-accelerated with FP16 precision
- **Batch Processing**: Enabled (batch size 4)
- **Decoder**: DALI with Gaussian interpolation
- **Decoder Resolution**: 640×640
- **Model Type**: Medium model (balance of accuracy and speed)
- **Block ROI**: Disabled

#### Parameters
- **Confidence Threshold**: 0.25 (low threshold for sensitive gesture detection)
- **MJPEG Output**: Enabled with keypoint visualization
- **Alerts**: Disabled
- **Drawing**: Zone, ROI, and keypoints visualization enabled

#### Scale Specification
- **Cluster ID**: `default-cluster`
- **Machine ID**: `framequeues-3`
- **GPU ID**: 0
- **Drawing Component**: `node.utils.drawing.drawing:v0.0.1-stable`
- **Output Resolution**: 1920×1080

### 2. Primary Policy Filtering Node (`policy-1`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Policy
- **Purpose**: Filter persons within gesture detection zones

#### Filter Configuration

##### Class Confidence Filter
```json
{
  "score": 0.25,
  "allowed_classes": ["person"]
}
```

##### Zone Filtering
```json
{
  "zone": ["ZoneSoS"],
  "pivotPoint": "midPoint"
}
```

#### Visualization Settings
- **MJPEG Output**: Enabled with comprehensive visualization
- **Drawing**: Zone, ROI, alert highlighting, and keypoints enabled
- **Alerts**: Disabled at policy level

### 3. Object Tracking Node (`tracker-1`)

#### Component Details
- **Component URI**: `node.algorithm.tracker.trackerlite:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Multi-object tracking for maintaining person identity

#### Configuration
- **TTL**: 4 frames (time-to-live for lost tracks)
- **Tracker Type**: NONE (basic tracking)
- **Keep Upper Height Ratio**: 1.0
- **Decoder**: DALI with Gaussian interpolation
- **Batch Processing**: Enabled (batch size 16)

#### Tracking Parameters
- **IoU Threshold**: 0.45
- **Sigma IoU**: 0.3
- **Sigma Height**: 0.3
- **Sigma Length**: 0.1
- **Minimum Track Length**: 2 frames
- **Log Level**: Info
- **Drawing**: Full visualization including keypoints and calibration

### 4. Action Detection Policy Node (`policy-2`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Policy
- **Purpose**: Advanced action detection and temporal filtering

#### Filter Configuration

##### Movement Detection
```json
{
  "key": "movement_stationary",
  "params": {
    "params_update_interval": 100,
    "timebased": [
      {
        "start": "18:30",
        "end": "19:00", 
        "params": {
          "allow": "moving"
        }
      }
    ],
    "stationaryThreshold": 20,
    "historyLength": 10,
    "allow": "moving"
  }
}
```

##### Gesture Interaction Detection
```json
{
  "key": "interaction",
  "params": {
    "activity_type": "action",
    "actions": ["wave"],
    "pivot": "nose",
    "selected_keypoints": {
      "p1": ["left_wrist", "nose", "right_wrist"]
    },
    "threshold": 0,
    "N_violating_keypoints": 0,
    "gender_check": false
  }
}
```

### 5. Action Detection Engine (`usecase-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecase:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Final gesture detection and alert generation

#### Configuration
```json
{
  "ActionDetection": {
    "waitSecondsForAction": 20,
    "ppl_violating_count": 1,
    "withTracker": "True",
    "scenario_type": "individual",
    "alert_interval": 120,
    "severity": "high"
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
Input Stream (Camera: 3 FPS, BGR, 1920×1080)
       ↓
   [poseDet-1]
   (Pose Estimation)
       ↓
   [policy-1]
   (Zone + Person Filtering)
       ↓
   [tracker-1]
   (Multi-Object Tracking)
       ↓
   [policy-2]
   (Action Detection)
       ↓
   [usecase-1]
   (Gesture Recognition)
       ↓
   Waving Gesture Alert
```

### Detailed Connection Graph

#### Input Connections
- **poseDet-1**: Receives camera input stream

#### Processing Chain
1. **poseDet-1** → **policy-1** (Person filtering within zones)
2. **policy-1** → **tracker-1** (Object tracking)
3. **tracker-1** → **policy-2** (Action detection filtering)
4. **policy-2** → **usecase-1** (Final gesture recognition)

#### Linear Processing
- Sequential pipeline optimized for gesture detection accuracy
- Each stage refines and analyzes the pose data further

## Gesture Waving Detection Logic

### Multi-Stage Detection System

The pipeline implements a sophisticated gesture recognition system:

#### 1. Pose-Based Detection
- **Keypoint Analysis**: Focuses on left wrist, nose, and right wrist positions
- **Pivot Point**: Uses nose as reference anchor for wrist movements
- **Low Threshold**: 0.25 confidence for sensitive pose detection
- **Medium Model**: Balanced accuracy and real-time performance

#### 2. Zone-Based Filtering
- **Zone Definition**: "ZoneSoS" (Signal of Distress zone)
- **Pivot Point**: Mid-point of detected persons
- **Zone Filtering**: Only analyzes gestures within designated areas

#### 3. Movement Analysis
- **Stationary Threshold**: 20-pixel movement tolerance
- **History Length**: 10 frames for movement analysis
- **Time-Based Rules**: Special handling during specific hours (18:30-19:00)
- **Movement Requirement**: "moving" persons preferred for gesture detection

#### 4. Action Recognition
- **Action Type**: "wave" gesture specifically
- **Keypoint Selection**: Triangular analysis (both wrists relative to nose)
- **Threshold**: 0 (maximum sensitivity)
- **Gender Check**: Disabled (applies to all persons)

#### 5. Temporal Validation
- **Wait Period**: 20 seconds for gesture completion
- **Tracking Integration**: Uses tracking IDs for continuity
- **Individual Scenario**: Single person gesture detection
- **Alert Interval**: 120 seconds between repeated alerts

### Alert Generation

#### Alert Characteristics
- **Severity**: High (potential emergency signal)
- **Database Storage**: MongoDB with full metadata
- **Real-time Notification**: Redis pub/sub
- **Evidence Storage**: MinIO with video clips
- **Drawing Overlay**: Real-time visualization with keypoints

#### Alert Data Structure
```json
{
  "alert_type": "gesture_waving",
  "severity": "high",
  "action_detected": "wave",
  "gesture_analysis": {
    "keypoints_used": ["left_wrist", "nose", "right_wrist"],
    "movement_pattern": "wave_motion",
    "duration": "detection_seconds"
  },
  "location": "ZoneSoS",
  "timestamp": "unix_timestamp",
  "evidence": {
    "video_clip": "minio_url",
    "pose_sequence": "keypoint_data",
    "tracking_path": "trajectory_data"
  }
}
```

## Hardware & Performance Specifications

### Hardware Requirements
- **GPU**: Required (NVIDIA with CUDA 11.0+)
- **GPU Memory**: Minimum 4GB (pose estimation + tracking)
- **CPU**: Multi-core for pose processing
- **RAM**: 8GB recommended
- **Storage**: SSD for real-time video processing

### Performance Characteristics
- **Input FPS**: 3 FPS (optimized for gesture analysis accuracy)
- **Processing Latency**: ~200-400ms per frame
- **Alert Latency**: 20-140 seconds (detection + validation)
- **Concurrent Streams**: Single stream per pipeline instance
- **Resource Utilization**: Medium (pose estimation focused)

### Scalability
- **Horizontal Scaling**: Deploy multiple pipeline instances
- **Multi-Camera Support**: Independent pipeline per camera
- **Database Scaling**: MongoDB clustering for alerts
- **Real-time Dashboard**: Redis-based live updates

## Configuration Tuning Guidelines

### High-Security Areas (Emergency Zones)
```json
{
  "pose_confidence": 0.2,
  "action_wait_time": 15,
  "alert_interval": 60,
  "movement_threshold": 15
}
```

### Public Areas (General Monitoring)
```json
{
  "pose_confidence": 0.25,
  "action_wait_time": 20,
  "alert_interval": 120,
  "movement_threshold": 20
}
```

### Low-Priority Areas (Casual Monitoring)
```json
{
  "pose_confidence": 0.3,
  "action_wait_time": 30,
  "alert_interval": 300,
  "movement_threshold": 30
}
```

## Integration & Deployment

### Prerequisites
1. **Camera System**: RTSP stream or video file
2. **GPU Infrastructure**: CUDA-compatible GPU
3. **Database Systems**: MongoDB, Redis, MinIO
4. **Zone Configuration**: Define "ZoneSoS" gesture detection areas
5. **Pose Model**: Pre-trained pose estimation model

### Deployment Steps
1. **Infrastructure Setup**: Deploy database services
2. **Model Deployment**: Load pose estimation model on GPU nodes
3. **Zone Definition**: Configure gesture detection zones
4. **Camera Integration**: Configure video streams
5. **Alert System**: Connect emergency notification endpoints
6. **Threshold Tuning**: Adjust sensitivity parameters

### Monitoring & Maintenance
- **Gesture Accuracy**: Validate against manual observations
- **Performance Metrics**: FPS, GPU utilization, memory usage
- **False Positives**: Monitor non-gesture movements
- **System Health**: Component status monitoring

## Use Cases & Applications

### Primary Applications
- **Emergency Signaling**: SOS gesture detection
- **Security Monitoring**: Distress signal recognition
- **Accessibility**: Communication aid for hearing impaired
- **Public Safety**: Crowd monitoring for help requests
- **Healthcare**: Patient distress detection
- **Traffic Control**: Manual signal recognition

### Detection Scenarios
- **Emergency Situations**: People signaling for help
- **Communication**: Non-verbal interaction detection
- **Accessibility Support**: Sign language basics
- **Crowd Control**: Attention-seeking gestures
- **Security Alerts**: Suspicious signaling behavior

## Limitations & Considerations

### Technical Limitations
- **Lighting Conditions**: Performance may degrade in low light
- **Camera Angle**: Requires clear view of upper body
- **Occlusion**: Partial blocking may affect keypoint detection
- **Distance**: Effectiveness decreases with camera distance

### Gesture Recognition
- **Motion Speed**: Very fast or slow waves may be missed
- **Arm Position**: Optimal detection with raised arms
- **Background Clutter**: Busy backgrounds may affect accuracy
- **Multiple Persons**: Individual detection in crowded scenes

### Ethical Considerations
- **Privacy**: Ensure compliance with surveillance regulations
- **Emergency Response**: Connect to appropriate response systems
- **False Alarms**: Balance sensitivity with false positive rates
- **Accessibility**: Consider diverse gesture patterns

## Future Enhancements

### Potential Improvements
1. **Multi-Gesture Support**: Add more gesture types (help, stop, etc.)
2. **3D Pose Analysis**: Enhanced spatial gesture understanding
3. **Emotion Recognition**: Combine with facial expression analysis
4. **Sign Language**: Basic sign language recognition
5. **Mobile Integration**: Real-time alerts to security personnel
6. **AI Learning**: Adaptive gesture pattern learning

### Advanced Features
- **Gesture Intensity**: Measure urgency of gestures
- **Context Awareness**: Situational gesture interpretation
- **Multi-Person Coordination**: Group gesture detection
- **Integration APIs**: Connect with emergency response systems

## References & Documentation

### Algorithm References
- OpenPose: Real-time multi-person 2D pose estimation
- MediaPipe: Hand and pose landmark detection
- Action Recognition: Temporal gesture classification methods

### System Documentation
- AIOS Pipeline Framework
- Docker Container Specifications
- Database Schema Documentation
- Emergency Alert Integration Guide

## Troubleshooting Guide

### Common Issues
1. **Missed Gestures**: Adjust pose confidence and keypoint sensitivity
2. **False Positives**: Tune movement thresholds and time validation
3. **Poor Lighting**: Improve camera positioning and lighting
4. **Tracking Failures**: Optimize tracking parameters for environment

### Performance Optimization
- **Pose Detection**: Balance confidence threshold for accuracy
- **Action Recognition**: Adjust gesture validation parameters
- **Zone Configuration**: Optimize detection areas for coverage
- **Alert Tuning**: Balance response time with false alarm rates

This comprehensive pipeline provides reliable gesture waving detection capabilities suitable for emergency signaling, accessibility support, and security monitoring applications, combining advanced pose estimation with sophisticated action recognition algorithms.
