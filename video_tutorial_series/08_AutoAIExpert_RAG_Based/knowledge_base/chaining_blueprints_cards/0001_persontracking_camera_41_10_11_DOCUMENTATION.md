# Person Tracking Pipeline Documentation

## Overview
This document provides a comprehensive analysis of the `0001_persontracking_camera_41_10_11.json` blueprint, which defines a complete end-to-end computer vision pipeline for tracking people across video frames. The pipeline combines object detection, policy filtering, tracking, and comprehensive logging to maintain person identity and movement history, useful for security monitoring and analytics.

## Pipeline Identity

### Component Information
- **Component ID**: `persontracking_camera_41_10_11`
- **Component Type**: `node.algorithm.pipeline`
- **Parser Version**: `Parser/V1`
- **Pipeline UID**: `persontracking_camera_41_10_11`
- **Version**: `v0.0.1`
- **Release Tag**: `stable`

### Template Configuration
- **Template Type**: `template.vdag.app-layout.sample-vdag:v0.0.1-beta`
- **Runtime ID**: `default-mdag`
- **Database Location**: `framequeues-3`

## Source Configuration

### Camera Input Settings
- **Assignment Type**: `source`
- **Source ID**: `camera_41_10_11`
- **Controller Node**: `framequeues-3`

### Stream Parameters
- **Frame Rate**: 1 FPS (`"1/1"`) - optimized for tracking accuracy
- **Actuation Frequency**: 1
- **GPU ID**: 1
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

### 1. Object Detection Node (`obj-det-1`)

#### Component Details
- **Component URI**: `node.algorithm.objdet.general7Detection_360h_640:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Detects people and objects for tracking analysis

#### Configuration
- **Hardware**: GPU-accelerated with FP16 precision
- **Batch Processing**: Enabled (batch size 8)
- **Decoder**: DALI with Gaussian interpolation
- **Input Resolution**: 416×416
- **Decoder Resolution**: 640×360
- **Full Image**: Enabled
- **Max Detections**: 300
- **Confidence Threshold**: 0.4
- **IoU Threshold**: 0.45

### 2. Policy Filtering Node (`policy-1`)
- **Component URI**: `node.utils.policy.policy:v0.0.1-stable`
- **Purpose**: Filters detected persons for tracking

### 3. Object Tracking Node (`tracker-1`)
- **Component URI**: `node.algorithm.tracker.trackerlite:v0.0.1-stable`
- **Purpose**: Multi-object tracking for maintaining person identity

### 4. Person Tracking Engine (`usecase-1`)

#### Component Details
- **Component URI**: `node.utils.usecase.usecase:v0.0.1-stable`
- **Node Type**: Algorithm
- **Purpose**: Person tracking analytics and logging

#### Configuration
```json
{
  "personTracking": {
    "taillength": 20,
    "dbpush_interval": 5,
    "alert_interval": 600,
    "severity": "medium"
  }
}
```

#### Logging System
- **Enabled**: Comprehensive tracking data logging
- **Database**: `PROJECT_LOG.persontrackingdb` (MongoDB)
- **Push Interval**: 5 seconds
- **Data Fields**: Camera ID, Object ID, Confidence, Timestamp, ROI, Zone, Entry/Exit times

#### Data Storage
- **MongoDB**: Tracking logs and alerts
- **Redis**: Real-time data streaming
- **MinIO**: Video evidence storage

## Pipeline Data Flow Architecture

### Flow Diagram
```
Input Stream (Camera: 1 FPS, BGR, 640×360)
       ↓
   [obj-det-1]
   (Object Detection)
       ↓
   [policy-1]
   (Person Filtering)
       ↓
   [tracker-1]
   (Multi-Object Tracking)
       ↓
   [usecase-1]
   (Person Tracking Analytics + Logging)
       ↓
   Tracking Data + Logs
```

### Processing Chain
1. **obj-det-1** → **policy-1** (Person filtering)
2. **policy-1** → **tracker-1** (Object tracking)  
3. **tracker-1** → **usecase-1** (Analytics and logging)

## Person Tracking Logic

### Tracking Features
- **Tail Length**: 20-frame trajectory history
- **Identity Maintenance**: Consistent tracking across frames
- **Zone Analysis**: Entry/exit detection for defined areas
- **Movement Analytics**: Speed and direction analysis

### Data Logging
- **Real-time Updates**: 5-second database push intervals
- **Comprehensive Metrics**: Full tracking metadata
- **Historical Data**: Complete person journey records
- **Analytics Ready**: Structured data for analysis

## Use Cases & Applications

### Primary Applications
- **Security Monitoring**: Person movement tracking
- **Retail Analytics**: Customer journey analysis  
- **Facility Management**: Occupancy and flow monitoring
- **Safety Compliance**: Emergency evacuation tracking
- **Behavioral Analytics**: Movement pattern analysis

## Hardware Requirements
- **GPU**: NVIDIA with CUDA 11.0+
- **GPU Memory**: 4GB minimum
- **RAM**: 8GB recommended
- **Storage**: SSD for logging

## Performance Characteristics
- **Input FPS**: 1 FPS (optimized for accuracy)
- **Processing Latency**: ~200-400ms per frame
- **Logging Frequency**: 5-second intervals
- **Resource Utilization**: Low-Medium

This pipeline provides reliable person tracking with comprehensive logging capabilities, suitable for security monitoring and analytics applications requiring detailed movement history and identity maintenance.
