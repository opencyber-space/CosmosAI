# People Line Cross Counting Pipeline Documentation

## Overview
This document provides a comprehensive analysis of the `0001_PeopleLineCrossCounting_camera_34_29_11.json` blueprint, which defines a complete end-to-end computer vision pipeline for counting people crossing designated lines or boundaries. The pipeline combines object detection, tracking, and spatial analysis to monitor pedestrian traffic flow across multiple zones.

## Pipeline Identity

### Component Information
- **Component ID**: `peopleLineCrossCounting_camera_34_29_11`
- **Component Type**: `node.algorithm.pipeline`
- **Parser Version**: `Parser/V1`
- **Pipeline UID**: `peopleLineCrossCounting_camera_34_29_11`
- **Version**: `v0.0.1`
- **Release Tag**: `stable`

### Template Configuration
- **Template Type**: `template.vdag.app-layout.sample-vdag:v0.0.1-beta`
- **Runtime ID**: `default-mdag`
- **Database Location**: `framequeues-5`

## Source Configuration

### Camera Input Settings
- **Assignment Type**: `source`
- **Source ID**: `camera_34_29_11`
- **Controller Node**: `framequeues-5`

### Stream Parameters
- **Frame Rate**: 5 FPS (`"5/1"`)
- **Actuation Frequency**: 1
- **GPU ID**: 2
- **GPU Enabled**: Yes
- **Allocation Node**: `framequeues-5`
- **Mode**: Memory-based processing
- **Loop Video**: Enabled (for testing)
- **Live Stream**: Enabled
- **Frame Quality**: 90%
- **Color Format**: BGR

### Global Settings
- **Alert URL**: `http://test-alerts.io`
- **Alert ID URL**: `http://serverip:serverport/getalertid`
- **Database Storage**: MongoDB (`VIP_DATA` database)
- **Test Configuration**: Custom parameters for pipeline testing

## Pipeline Components Analysis

### 1. Object Detection Node (`obj-det-1`)

#### Component Details
- **Component URI**: `node.algorithm.objdet.general7Detection_360h_640:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Detects people in lower resolution for efficient processing

#### Configuration
- **Hardware**: GPU-accelerated with FP16 precision
- **Batch Processing**: Enabled (batch size 8)
- **Decoder**: DALI with Gaussian interpolation
- **Input Resolution**: 416×416
- **Decoder Resolution**: 640×360 (lower resolution for speed)
- **Full Image**: Enabled
- **Stretch Image**: Disabled
- **Block ROI**: Disabled

#### Parameters
- **Confidence Threshold**: 0.3 (moderate threshold for person detection)
- **NMS IoU**: 0.4
- **MJPEG Output**: Disabled
- **Alerts**: Disabled
- **Drawing**: Zone, ROI, line, and arrow visualization enabled

#### Scale Specification
- **Cluster ID**: `default-cluster`
- **Machine ID**: `framequeues-5`
- **GPU ID**: 2
- **Drawing Component**: `node.utils.drawing.drawing:v0.0.1-stable`
- **Output Resolution**: 1920×1080

### 2. Policy Filtering Node (`policy-1`)

#### Component Details
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Filter detected persons within designated counting zones

#### Filter Configuration

##### Class Confidence Filter
```json
{
  "score": 0.3,
  "allowed_classes": ["person"]
}
```

##### Zone Filtering
```json
{
  "zone": ["Zone1", "Zone2"],
  "pivotPoint": "bottomPoint"
}
```

### 3. Object Tracking Node (`tracker-1`)

#### Component Details
- **Component URI**: `node.algorithm.tracker.trackerlite:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Multi-object tracking for maintaining person identity across frames

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
- **Minimum Time**: 2 frames

### 4. Line Crossing Counter (`usecase-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecase:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Analyze tracked persons for line crossing events

#### Configuration
```json
{
  "peoplecountingLineCrossing": {
    "alert_interval": 30,
    "severity": "medium",
    "arrows": [
      {"zone": "Zone1"},
      {"zone": "Zone2"}
    ],
    "lines": [
      {"zone": "Zone1"},
      {"zone": "Zone2"}
    ],
    "roiPoint": [
      {"zone": "Zone1", "position": "mid"},
      {"zone": "Zone2", "position": "mid"}
    ]
  }
}
```

#### Alert System Integration
- **MongoDB Integration**: 
  - Alert Database: `VIP_ALERT` (alerts collection)
  - Data Database: `VIP_DATA` (counting data)
- **Redis Integration**: Real-time data push
- **MinIO Storage**: Alert data and evidence storage
- **Component URI**: `node.utils.alert.alert:v0.0.1-stable`

## Pipeline Data Flow Architecture

### Flow Diagram
```
Input Stream (Camera: 5 FPS, BGR, 640×360)
       ↓
   [obj-det-1]
  (Person Detection)
       ↓
   [policy-1]
  (Zone Filtering)
       ↓
   [tracker-1]
  (Person Tracking)
       ↓
   [usecase-1]
(Line Cross Counting)
       ↓
   Counting Data & Alerts
```

### Detailed Connection Graph

#### Input Connections
- **obj-det-1**: Receives camera input stream

#### Processing Chain
1. **obj-det-1** → **policy-1** (Person filtering)
2. **policy-1** → **tracker-1** (Person tracking)
3. **tracker-1** → **usecase-1** (Line crossing analysis)

#### Single-Stream Processing
- Linear pipeline with sequential processing
- Each component receives single input from previous stage

## People Line Cross Counting Logic

### Detection Strategy

#### 1. Person Detection Path
- Detects persons using general object detection model
- Optimized for lower resolution (640×360) for faster processing
- Moderate confidence threshold (0.3) to catch most persons

#### 2. Zone-Based Filtering
- **Multi-Zone Support**: Monitors both "Zone1" and "Zone2"
- **Pivot Point**: Uses bottom point of bounding box for accurate positioning
- **Person-Only Filter**: Exclusively focuses on person class detections

#### 3. Tracking and Identity Maintenance
- Maintains person identity across multiple frames
- Tracks movement trajectories
- Handles occlusions and temporary disappearances

#### 4. Line Crossing Analysis
- **Directional Counting**: Supports bi-directional counting
- **Zone-Based Logic**: Uses predefined zones and lines
- **ROI Points**: Mid-point positioning for accurate crossing detection
- **Alert Generation**: 30-second intervals between counting alerts

### Counting Methodology

#### Line Definition
- **Zone1 and Zone2**: Two counting areas with associated lines
- **Arrow Visualization**: Shows counting direction
- **Line Visualization**: Clear boundary markers
- **ROI Positioning**: Mid-point detection for crossing events

#### Crossing Detection Logic
1. **Track Initialization**: Person enters monitoring zone
2. **Position Monitoring**: Continuous tracking of person location
3. **Line Intersection**: Detection of trajectory crossing line boundary
4. **Direction Analysis**: Determination of crossing direction
5. **Count Increment**: Addition to appropriate directional counter
6. **Data Storage**: Persistent counting data in database

### Alert and Data Generation

#### Counting Data Structure
```json
{
  "event_type": "line_crossing",
  "zone": "Zone1|Zone2",
  "direction": "forward|backward",
  "count_increment": 1,
  "timestamp": "unix_timestamp",
  "person_id": "track_id",
  "crossing_point": {
    "x": "pixel_x",
    "y": "pixel_y"
  },
  "trajectory": "movement_path"
}
```

#### Alert Characteristics
- **Severity**: Medium (informational counting event)
- **Database Storage**: Dual storage (alerts + data)
- **Real-time Notification**: Redis pub/sub
- **Evidence Storage**: MinIO with video clips
- **Alert Interval**: 30 seconds between notifications

## Hardware & Performance Specifications

### Hardware Requirements
- **GPU**: Required (NVIDIA with CUDA 11.0+)
- **GPU Memory**: Minimum 4GB (single model + tracking)
- **CPU**: Multi-core for tracking computations
- **RAM**: 8GB recommended
- **Storage**: SSD for real-time video processing

### Performance Characteristics
- **Input FPS**: 5 FPS (balanced for accuracy and performance)
- **Processing Latency**: ~100-200ms per frame
- **Counting Accuracy**: High for clear line crossings
- **Concurrent Streams**: Single stream per pipeline instance
- **Resource Utilization**: Medium (single AI model + tracking)

### Scalability
- **Horizontal Scaling**: Deploy multiple pipeline instances
- **Load Balancing**: Distribute camera feeds across instances
- **GPU Sharing**: Efficient batch processing
- **Database Scaling**: MongoDB sharding for large datasets

## Configuration Tuning Guidelines

### High-Traffic Areas (Malls, Stations)
```json
{
  "detection_confidence": 0.2,
  "tracking_ttl": 6,
  "alert_interval": 10,
  "batch_size": 16
}
```

### Medium-Traffic Areas (Offices, Retail)
```json
{
  "detection_confidence": 0.3,
  "tracking_ttl": 4,
  "alert_interval": 30,
  "batch_size": 8
}
```

### Low-Traffic Areas (Residential, Parks)
```json
{
  "detection_confidence": 0.4,
  "tracking_ttl": 3,
  "alert_interval": 60,
  "batch_size": 4
}
```

## Integration & Deployment

### Prerequisites
1. **Camera System**: RTSP stream with clear line-of-sight
2. **GPU Infrastructure**: CUDA-compatible GPU
3. **Database Systems**: MongoDB, Redis, MinIO
4. **Network**: Moderate bandwidth for 5 FPS streaming
5. **Zone Configuration**: Define counting zones and lines

### Deployment Steps
1. **Infrastructure Setup**: Deploy database services
2. **Model Deployment**: Load person detection model on GPU
3. **Zone Definition**: Configure counting zones and line boundaries
4. **Camera Integration**: Configure video streams
5. **Counting Logic**: Set up directional counting parameters
6. **Data Pipeline**: Connect to analytics databases

### Monitoring & Maintenance
- **Performance Metrics**: FPS, detection accuracy, tracking quality
- **Counting Accuracy**: Validation against manual counts
- **System Health**: Component status monitoring
- **Data Quality**: Database performance and storage

## Use Cases & Applications

### Primary Applications
- **Retail Analytics**: Customer traffic flow analysis
- **Transportation**: Passenger counting in stations and vehicles
- **Event Management**: Crowd flow monitoring
- **Security**: Perimeter monitoring and access control
- **Urban Planning**: Pedestrian traffic studies
- **Building Management**: Occupancy monitoring

### Counting Scenarios
- **Bi-directional Counting**: In/out traffic analysis
- **Zone Transitions**: Movement between areas
- **Peak Hour Analysis**: Traffic pattern identification
- **Capacity Management**: Real-time occupancy tracking
- **Flow Optimization**: Bottleneck identification

## Limitations & Considerations

### Technical Limitations
- **Camera Angle**: Requires optimal viewing angle for line crossing
- **Occlusion**: Dense crowds may affect tracking accuracy
- **Lighting Conditions**: Performance varies with lighting quality
- **False Positives**: Non-person objects may be miscounted

### Environmental Factors
- **Crowd Density**: High density reduces tracking accuracy
- **Movement Speed**: Very fast movement may be missed
- **Line Definition**: Clear line boundaries required
- **Camera Position**: Overhead views provide best results

### Ethical Considerations
- **Privacy**: Ensure compliance with surveillance regulations
- **Data Retention**: Implement appropriate data lifecycle policies
- **Anonymization**: Count data without personal identification
- **Transparency**: Document counting methodology and limitations

## Future Enhancements

### Potential Improvements
1. **Multi-Camera Fusion**: Coordinate counting across multiple views
2. **Advanced Tracking**: Deep learning-based person re-identification
3. **Demographic Analysis**: Age and gender-based counting
4. **Real-time Analytics**: Live dashboard and reporting
5. **Mobile Integration**: Field monitoring via mobile applications
6. **AI-Based Calibration**: Automatic zone and line optimization

### Advanced Features
- **Dwell Time Analysis**: Time spent in zones
- **Heat Map Generation**: Popular pathway visualization
- **Predictive Analytics**: Traffic pattern forecasting
- **Integration APIs**: Connect with facility management systems

## References & Documentation

### Algorithm References
- YOLOv7 Object Detection: https://arxiv.org/abs/2207.02696
- Multi-Object Tracking: SORT and DeepSORT algorithms
- Line Crossing Detection: Computer vision geometric analysis

### System Documentation
- AIOS Pipeline Framework
- Docker Container Specifications
- Database Schema Documentation
- Analytics Integration Guide

## Troubleshooting Guide

### Common Issues
1. **Missed Counts**: Adjust detection confidence and tracking parameters
2. **False Counts**: Improve line definition and zone configuration
3. **Performance Issues**: Optimize batch sizes and resolution
4. **Tracking Failures**: Tune tracking parameters for environment

### Performance Optimization
- **GPU Utilization**: Balance batch sizes for optimal throughput
- **Memory Management**: Monitor tracking memory usage
- **Network Optimization**: Ensure sufficient bandwidth
- **Database Tuning**: Optimize counting data storage and queries

This comprehensive pipeline provides an efficient and scalable solution for people counting applications, combining accurate detection with robust tracking to deliver reliable traffic flow analytics across various environments.
