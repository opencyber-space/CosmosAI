# Chain Snatching Detection Pipeline Documentation

## Overview
This document provides a comprehensive analysis of the `chain_snatching.json` blueprint, which defines a complete end-to-end computer vision pipeline for detecting chain snatching incidents. The pipeline implements a sophisticated "FALL-AND-RUN" sequence detection system combining multiple AI models and business logic.

## Pipeline Identity

### Component Information
- **Component ID**: `chain_snatching_pipeline`
- **Component Type**: `node.algorithm.pipeline`
- **Parser Version**: `Parser/V1`
- **Pipeline UID**: `snatchingDetection_cameras_100_100`
- **Version**: `v0.0.1`
- **Release Tag**: `stable`

### Template Configuration
- **Template Type**: `template.vdag.app-layout.sample-vdag:v0.0.1-beta`
- **Runtime ID**: `default-mdag`
- **Database Location**: `framequeues-1`

## Source Configuration

### Camera Input Settings
- **Assignment Type**: `source`
- **Source ID**: `cameras_100_100`
- **Controller Node**: `framequeues-1`

### Stream Parameters
- **Frame Rate**: 5 FPS (`"5/1"`)
- **Actuation Frequency**: 1
- **GPU ID**: 1
- **GPU Enabled**: Yes
- **Allocation Node**: `framequeues-1`
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

### 1. Pose Detection Node (`poseDet-1`)

#### Component Details
- **Component URI**: `node.algorithm.posekey.pose-estimation-rt:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Detects human pose keypoints for interaction analysis

#### Configuration
- **Hardware**: GPU-accelerated with FP16 precision
- **Batch Processing**: Enabled (batch size 4)
- **Decoder**: DALI with Gaussian interpolation
- **Input Resolution**: 640×640
- **Model Type**: Medium model
- **Block ROI**: Disabled

#### Parameters
- **Confidence Threshold**: 0.1 (low threshold for pose keypoints)
- **MJPEG Output**: Disabled
- **Alerts**: Disabled
- **Drawing**: Keypoints visualization enabled

#### Scale Specification
- **Cluster ID**: `default-cluster`
- **Machine ID**: `framequeues-1`
- **GPU ID**: 1
- **Drawing Component**: `node.utils.drawing.drawing:v0.0.1-stable`
- **Output Resolution**: 1920×1080

### 2. Fall Detection Node (`fallDet-1`)

#### Component Details
- **Component URI**: `node.algorithm.objdet.fall7Detection_640h_640:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Specialized fall detection model

#### Configuration
- **Hardware**: GPU-accelerated with FP16 precision
- **Batch Processing**: Enabled (batch size 8)
- **Input Resolution**: 640×416
- **Decoder**: DALI with Gaussian interpolation
- **Full Image**: Enabled
- **Stretch Image**: Disabled
- **ROI Batch Size**: 1

#### Parameters
- **Confidence Threshold**: 0.7 (high threshold for fall detection)
- **NMS IoU**: 0.4
- **Drawing**: Comprehensive visualization enabled
- **Alert Configuration**: Disabled

### 3. Policy Filtering Nodes

#### Policy Node 1 (`policy-1`) - Person Zone Filtering
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Purpose**: Filter person detections within specific zones

**Filter Configuration:**
```json
{
  "class_conf_filter": {
    "score": 0.1,
    "allowed_classes": ["person"]
  },
  "inside_zone": {
    "zone": ["ZoneSnatch"],
    "pivotPoint": "midPoint"
  }
}
```

#### Policy Node 2 (`policy-2`) - Interaction Detection
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Purpose**: Detect physical interactions using pose keypoints

**Filter Configuration:**
```json
{
  "interaction": {
    "activity_type": ["interaction"],
    "selected_keypoints": {
      "p1": ["left_ear", "right_ear", "right_shoulder", "left_shoulder"],
      "p2": ["right_wrist", "left_wrist"]
    },
    "threshold": 70,
    "N_violating_keypoints": 1,
    "gender_check": false,
    "trigger_interval": 10
  }
}
```

#### Policy Node 3 (`policy-3`) - Calibration
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Purpose**: Coordinate transformation and calibration

**Filter Configuration:**
```json
{
  "caliberation": {
    "pivotPoint": "bottomPoint"
  }
}
```

#### Policy Fall Node (`policy-fall-1`) - Fall Event Filtering
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Purpose**: Filter and validate fall detection events

**Filter Configuration:**
```json
{
  "class_conf_filter": {
    "score": 0.7,
    "allowed_classes": ["Fall", "fall"],
    "params_update_interval": 200,
    "timebased": [
      {
        "start": "12:30",
        "end": "01:30",
        "params": {
          "score": 0.9
        }
      }
    ]
  },
  "inside_zone": {
    "zone": ["ZoneSnatch"],
    "pivotPoint": "midPoint"
  }
}
```

### 4. Object Tracking Node (`tracker-1`)

#### Component Details
- **Component URI**: `node.algorithm.tracker.trackerlitefast_960x540:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Multi-object tracking for maintaining object identity

#### Configuration
- **Input Resolution**: 960×540
- **Decoder Resolution**: 960×540
- **Object Type**: General
- **Batch Processing**: Enabled (batch size 8)

#### Tracking Parameters
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

### 5. Speed Estimation Node (`usecase-speed-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecase:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Calculate movement speed for "run" detection

#### Configuration
```json
{
  "speedEstimation": {
    "source_fps": 25,
    "include_speed": true,
    "min_distance": 3,
    "speedThreshold": 12,
    "speedviolation_counter": 2,
    "stationary_counter": 15,
    "stationary_distance": 3,
    "max_possible_speed": 53,
    "clear_past_ids_sec": 60,
    "valid_points_realworld": 2,
    "stationary_frames": 15,
    "group_count": -1,
    "group_running_interval": 15,
    "alert_interval": 300,
    "severity": "medium"
  }
}
```

### 6. Final Decision Engine (`usecase-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecasmux_3input:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Combine all inputs for final chain snatching decision

#### Configuration
```json
{
  "SnatchingDetection": {
    "sequence": "FALL-AND-RUN",
    "trigger_wait_interval": 20,
    "alert_interval": 600,
    "only_snatching": false,
    "severity": "high"
  }
}
```

#### Alert System Integration
- **MongoDB Integration**: `CITY_ALERT` database
- **Redis Integration**: Real-time data push
- **MinIO Storage**: Alert data storage
- **Component URI**: `node.utils.alert.alert:v0.0.1-stable`

## Pipeline Data Flow Architecture

### Flow Diagram
```
Input Stream (Camera: 5 FPS, BGR, 1920×1080)
       ↓
   ┌─────────────────────────────────────┐
   │ Parallel Processing                 │
   │                                     │
   │ [poseDet-1] ──→ [policy-1] ─┐      │
   │ (Pose Detection)            │      │
   │                             ↓      │
   │ [fallDet-1] ──→ [policy-fall-1]    │
   │ (Fall Detection)            │      │
   └─────────────────────────────┼──────┘
                                 ↓
                          [tracker-1]
                     (Multi-Object Tracking)
                               ↓
                    ┌─────────────────────┐
                    │                     │
                    ↓                     ↓
              [policy-3]           [policy-2]
             (Calibration)       (Interaction)
                    ↓                     │
           [usecase-speed-1] ─────────────┘
           (Speed Estimation)             │
                    ↓                     │
                    └─────────┬───────────┘
                              ↓
                        [usecase-1]
                  (Final Decision Engine)
                              ↓
                    Chain Snatching Alert
```

### Detailed Connection Graph

#### Input Connections
- **poseDet-1**: Receives camera input stream
- **fallDet-1**: Receives camera input stream

#### Processing Chain
1. **poseDet-1** → **policy-1** (Person filtering)
2. **policy-1** → **tracker-1** (Tracking persons)
3. **fallDet-1** → **policy-fall-1** (Fall filtering)
4. **tracker-1** → **policy-3** (Calibration)
5. **tracker-1** → **policy-2** (Interaction detection)
6. **policy-3** → **usecase-speed-1** (Speed calculation)

#### Final Decision Inputs
- **usecase-1** receives three inputs:
  1. **policy-2** output (Interaction detection)
  2. **policy-fall-1** output (Fall events)
  3. **usecase-speed-1** output (Speed analysis)

## Chain Snatching Detection Logic

### Sequence Detection: "FALL-AND-RUN"

The pipeline implements a sophisticated multi-modal detection system:

#### 1. Fall Detection Path
- Detect fall events using specialized fall detection model
- Filter events within designated zones ("ZoneSnatch")
- Apply time-based confidence adjustments (higher threshold during specific hours)

#### 2. Interaction Detection Path
- Analyze pose keypoints for person interactions
- Focus on proximity between upper body (ears, shoulders) and hands (wrists)
- Detect when hands come close to another person's upper body area

#### 3. Speed Analysis Path
- Track object movement after interaction/fall
- Calculate real-world speed using calibration
- Detect "running" behavior (speed > 12 units)
- Monitor for sustained high-speed movement

#### 4. Temporal Correlation
- **Trigger Wait Interval**: 20 seconds for sequence completion
- **Alert Interval**: 600 seconds between repeated alerts
- **Sequence Logic**: Fall + Interaction + Speed increase = Chain Snatching

### Alert Generation

#### Alert Characteristics
- **Severity**: High (critical security event)
- **Database Storage**: MongoDB with full metadata
- **Real-time Notification**: Redis pub/sub
- **Evidence Storage**: MinIO with video clips
- **Drawing Overlay**: Real-time visualization

#### Alert Data Structure
```json
{
  "alert_type": "chain_snatching",
  "severity": "high",
  "sequence_detected": "FALL-AND-RUN",
  "components": {
    "fall_detected": true,
    "interaction_detected": true,
    "speed_violation": true
  },
  "location": "ZoneSnatch",
  "timestamp": "unix_timestamp",
  "evidence": {
    "video_clip": "minio_url",
    "keyframe_analysis": "pose_data",
    "tracking_path": "trajectory_data"
  }
}
```

## Hardware & Performance Specifications

### Hardware Requirements
- **GPU**: Required (NVIDIA with CUDA 11.0+)
- **GPU Memory**: Minimum 8GB (multiple models running concurrently)
- **CPU**: Multi-core for parallel processing
- **RAM**: 16GB recommended
- **Storage**: SSD for real-time video processing

### Performance Characteristics
- **Input FPS**: 5 FPS (optimized for accuracy over speed)
- **Processing Latency**: ~200-500ms per frame
- **Alert Latency**: 20-600 seconds (depending on sequence completion)
- **Concurrent Streams**: Single stream per pipeline instance
- **Resource Utilization**: High (multiple AI models)

### Scalability
- **Horizontal Scaling**: Deploy multiple pipeline instances
- **Load Balancing**: Distribute streams across instances
- **GPU Sharing**: Batch processing for efficiency
- **Database Scaling**: MongoDB clustering for alerts

## Configuration Tuning Guidelines

### High Security Areas
```json
{
  "fall_confidence": 0.9,
  "interaction_threshold": 50,
  "speed_threshold": 8,
  "alert_interval": 300
}
```

### Public Spaces
```json
{
  "fall_confidence": 0.7,
  "interaction_threshold": 70,
  "speed_threshold": 12,
  "alert_interval": 600
}
```

### Testing Environment
```json
{
  "fall_confidence": 0.5,
  "interaction_threshold": 80,
  "speed_threshold": 15,
  "loop_video": true
}
```

## Integration & Deployment

### Prerequisites
1. **Camera System**: RTSP stream or video file
2. **GPU Infrastructure**: CUDA-compatible GPU
3. **Database Systems**: MongoDB, Redis, MinIO
4. **Network**: High-bandwidth for video streaming

### Deployment Steps
1. **Infrastructure Setup**: Deploy database services
2. **Model Deployment**: Load AI models on GPU nodes
3. **Pipeline Configuration**: Set zone definitions
4. **Camera Integration**: Configure video streams
5. **Alert System**: Connect notification endpoints
6. **Monitoring**: Set up performance dashboards

### Monitoring & Maintenance
- **Performance Metrics**: FPS, GPU utilization, memory usage
- **Alert Quality**: False positive/negative rates
- **Model Drift**: Accuracy monitoring over time
- **System Health**: Component status monitoring

## Use Cases & Applications

### Primary Applications
- **Jewelry Stores**: High-value retail security
- **Banks**: ATM and counter monitoring
- **Public Transport**: Station security
- **Parking Areas**: Vehicle and personal security
- **Commercial Centers**: Mall and plaza security

### Detection Scenarios
- **Traditional Chain Snatching**: Grab and run
- **Distraction Theft**: Fall distraction + theft
- **Opportunistic Theft**: Taking advantage of falls
- **Coordinated Attacks**: Multi-person incidents

## Limitations & Considerations

### Technical Limitations
- **Lighting Conditions**: Performance may degrade in low light
- **Camera Angle**: Optimal performance requires good coverage
- **Occlusion**: Dense crowds may affect tracking
- **False Positives**: Legitimate falls may trigger alerts

### Ethical Considerations
- **Privacy**: Ensure compliance with local surveillance laws
- **Bias**: Monitor for demographic bias in detection
- **Data Retention**: Implement appropriate data lifecycle policies
- **Transparency**: Document system capabilities and limitations

## Future Enhancements

### Potential Improvements
1. **Multi-Camera Fusion**: Coordinate across multiple camera views
2. **Behavioral Learning**: Adapt to location-specific patterns
3. **Real-time Tuning**: Dynamic parameter adjustment
4. **Mobile Integration**: Smartphone app for security personnel
5. **Predictive Analytics**: Risk assessment based on behavior patterns

## References & Documentation

### Algorithm References
- YOLOv7 Object Detection: https://arxiv.org/abs/2207.02696
- FastMOT Tracking: Multi-object tracking research
- Pose Estimation: OpenPose and similar keypoint detection methods

### System Documentation
- AIOS Pipeline Framework
- Docker Container Specifications
- Database Schema Documentation
- Alert System Integration Guide

## Troubleshooting Guide

### Common Issues
1. **High False Positives**: Adjust confidence thresholds
2. **Missed Detections**: Check camera positioning and lighting
3. **Performance Issues**: Optimize batch sizes and GPU allocation
4. **Alert Delays**: Review sequence timing parameters

### Performance Optimization
- **GPU Utilization**: Balance batch sizes across models
- **Memory Management**: Monitor and optimize memory usage
- **Network Optimization**: Ensure sufficient bandwidth
- **Database Tuning**: Optimize query performance

This comprehensive pipeline represents a state-of-the-art approach to chain snatching detection, combining multiple AI technologies with sophisticated business logic to provide reliable security monitoring capabilities.
