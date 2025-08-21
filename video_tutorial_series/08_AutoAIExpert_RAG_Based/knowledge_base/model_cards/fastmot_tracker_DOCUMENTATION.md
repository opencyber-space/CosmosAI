# FastMOT Multi-Object Tracker Documentation

## Overview
This document describes the `fastmot_tracker.json` model card, which defines a FastMOT-based multi-object tracking algorithm with re-identification capabilities optimized for surveillance applications.

## Model Identity

### Component Information
- **Component ID**: `trackerlitefast`
- **Version**: `v0.0.1`
- **Release**: `stable`
- **Component Type**: `node.algorithm.tracker` (Tracking Algorithm Node)
- **Container Image**: `fastskiptrackerallres:latest`

### Model Details
- **Name**: FastMOT Multi-Object Tracker
- **Category**: Tracker
- **Framework**: PyTorch
- **License**: Closed source
- **Repository**: https://github.com/poc.org

## Architecture & Parameters

### Model Architecture
- **Total Parameters**: 2.1 million
- **Backbone**: ResNet50
- **Re-ID Model**: OSNet (Omni-Scale Network)
- **Tracking Algorithm**: FastMOT
- **Motion Model**: Kalman Filter (enabled)

### Training Information
- **Pretrained**: Yes
- **Input Resolution**: 1920×1080 pixels
- **Dataset**: MOT Challenge + Custom Surveillance Data
- **Dataset Type**: Multi-object tracking
- **Scenarios**: General surveillance, crowd tracking
- **Notes**: Optimized for surveillance camera tracking with skip-frame detection

## Hardware Requirements

### GPU Requirements
- **GPU Required**: Yes
- **Minimum GPU Memory**: 4 GB
- **Recommended GPU**: NVIDIA T4
- **CPU Cores**: 4
- **RAM**: 8 GB

### Runtime Environment
- **Docker Image**: `fastskiptrackerallres:latest`
- **Python Version**: 3.8
- **CUDA Version**: 11.0
- **cuDNN Version**: 8.0
- **Operating System**: Ubuntu 20.04

## Configuration Parameters

### Input/Output Configuration
- **Inputs**: `["input_0"]` (object detections + RGB frames)
- **Outputs**: `["output_0"]` (tracked objects with IDs)
- **Batch Size**: Up to 8
- **Supports Batching**: Yes
- **Requires Frames**: Yes
- **Frame Size**: 1920×1080 (configurable)

### Image Processing Settings

#### Resolution Configuration
1. **Input Width (`width`)**
   - Type: Integer
   - Range: 480 - 1920
   - Default: 1920

2. **Input Height (`height`)**
   - Type: Integer
   - Range: 270 - 1080
   - Default: 1080

3. **Decoder Width (`decoder_width`)**
   - Type: Integer
   - Range: 959 - 1921
   - Default: 1920

4. **Decoder Height (`decoder_height`)**
   - Type: Integer
   - Range: 539 - 1081
   - Default: 1080

#### Decoder Settings
1. **Decoder Type (`decoderType`)**
   - Type: String
   - Options: "TURBO", "DALI"
   - Default: "TURBO"

2. **Interpolation Type (`interpolationType`)**
   - Type: String
   - Options: "INTERP_NN", "INTERP_LINEAR", "INTERP_CUBIC", "INTERP_TRIANGULAR", "INTERP_GAUSSIAN", "INTERP_LANCZOS3"
   - Default: "INTERP_GAUSSIAN"

### Tracking Algorithm Parameters

#### Object Management
1. **Object Type (`obj_name`)**
   - Type: String
   - Options: "general", "crowd"
   - Default: "general"
   - Purpose: Tracking scenario optimization

2. **Maximum Age (`max_age`)**
   - Type: Integer
   - Range: 1 - 50
   - Default: 9
   - Purpose: Maximum frames an object can be invisible before deletion

3. **Age Penalty (`age_penalty`)**
   - Type: Integer
   - Range: 1 - 50
   - Default: 2
   - Purpose: Penalty for older tracks in association

4. **Confirm Hits (`confirm_hits`)**
   - Type: Integer
   - Range: 1 - 10
   - Default: 1
   - Purpose: Consecutive detections needed to confirm a track

5. **History Size (`history_size`)**
   - Type: Integer
   - Range: 1 - 50
   - Default: 50
   - Purpose: Number of past positions to remember

#### Association & Matching
1. **Motion Weight (`motion_weight`)**
   - Type: Float
   - Range: 0 - 1
   - Default: 0.4
   - Purpose: Weight for motion prediction in association

2. **Max Association Cost (`max_assoc_cost`)**
   - Type: Float
   - Range: 0 - 1
   - Default: 0.8
   - Purpose: Maximum cost for track-detection association

3. **Max Re-ID Cost (`max_reid_cost`)**
   - Type: Float
   - Range: 0 - 1
   - Default: 0.6
   - Purpose: Maximum cost for re-identification matching

4. **IoU Threshold (`iou_thresh`)**
   - Type: Float
   - Range: 0 - 1
   - Default: 0.4
   - Purpose: IoU threshold for spatial overlap

5. **Duplicate Threshold (`duplicate_thresh`)**
   - Type: Float
   - Range: 0 - 1
   - Default: 0.5
   - Purpose: Threshold for detecting duplicate tracks

6. **Occlusion Threshold (`occlusion_thresh`)**
   - Type: Float
   - Range: 0 - 1
   - Default: 0.4
   - Purpose: Threshold for handling occluded objects

7. **Confidence Threshold (`conf_thresh`)**
   - Type: Float
   - Range: 0 - 1
   - Default: 0.15 (parameters) / 0.5 (settings)
   - Purpose: Minimum confidence for track maintenance

#### Performance Optimization
1. **Detector Skip Frame (`detector_skip_frame`)**
   - Type: Integer
   - Range: 1 - 10
   - Default: 2
   - Purpose: Number of frames to skip between detections (performance optimization)

## Performance Benchmarks

### Test Conditions
- **Hardware**: NVIDIA T4
- **Input Resolution**: 1920×1080
- **Decoder**: TURBO
- **Interpolation**: INTERP_GAUSSIAN
- **Max Age**: 9
- **Detector Skip Frame**: 2
- **Precision**: FP32

### Tracking Performance Metrics
- **MOTA (Multi-Object Tracking Accuracy)**: 0.75
- **MOTP (Multi-Object Tracking Precision)**: 0.82
- **ID Switches**: Low
- **False Positives**: Minimal
- **False Negatives**: Low

### Throughput Performance
- **1080p General Tracking**: 30 FPS
- **1080p Crowd Tracking**: 25 FPS
- **720p General Tracking**: 45 FPS
- **720p Crowd Tracking**: 35 FPS

### Resource Utilization
#### GPU Utilization
- **1080p Tracking**: 65%
- **720p Tracking**: 45%

#### GPU Memory Usage
- **1080p Tracking**: 3200 MB
- **720p Tracking**: 2400 MB

### Tracking Accuracy
- **ID Consistency**: 0.92
- **Occlusion Handling**: 0.85
- **Re-identification**: 0.88

## Data Contract

### Input Requirements
- **Consumes**: `["od1_list", "rgb_frames"]`
  - Object detection results from previous pipeline stage
  - RGB video frames for re-identification
- **Input Formats**: `["OD1"]`

### Output Specifications
- **Produces**: `["od1_list", "tracking_metadata"]`
  - Tracked objects with unique IDs
  - Tracking metadata (trajectories, confidence, etc.)
- **Output Formats**: `["OD1"]`

## Usage Notes

### Best Use Cases
- **Surveillance Applications**: Multi-camera tracking systems
- **Crowd Monitoring**: Tracking people in crowded scenarios
- **Traffic Analysis**: Vehicle tracking and behavior analysis
- **Security Systems**: Long-term object tracking with re-identification
- **Analytics Pipelines**: Feeding tracking data to behavior analysis modules

### Key Features
- **Skip-Frame Detection**: Optimizes performance by tracking between detections
- **Re-identification**: Maintains identity across occlusions and camera handoffs
- **Kalman Filtering**: Robust motion prediction for smooth trajectories
- **Occlusion Handling**: Continues tracking through temporary occlusions
- **Dual Mode**: Optimized for both general and crowded scenarios

### Configuration Recommendations

#### For General Surveillance
- `obj_name`: "general"
- `max_age`: 9
- `detector_skip_frame`: 2
- `conf_thresh`: 0.15

#### For Crowd Scenarios
- `obj_name`: "crowd"
- `max_age`: 6
- `detector_skip_frame`: 1
- `conf_thresh`: 0.3

### Pipeline Integration
This tracker is designed to work in computer vision pipelines:

**Typical Pipeline Flow:**
```
Object Detection → FastMOT Tracker → Behavior Analysis → Alert Generation
```

**Input Requirements:**
- Object detection results (bounding boxes, classifications)
- RGB frames for visual feature extraction

**Output Applications:**
- Behavior analysis (loitering, speed detection)
- Zone-based filtering with persistent IDs
- Multi-camera handoff systems
- Long-term trajectory analysis

## References
1. [FastMOT: High-Performance Multiple Object Tracking](https://arxiv.org/abs/2105.14205)
2. Internal tracking performance benchmarks

## Author Information
- **Author**: poc
- **Email**: poc@ai.org
- **GitHub**: https://github.com/poc.org
- **License**: Closed source
- **Tags**: alert
