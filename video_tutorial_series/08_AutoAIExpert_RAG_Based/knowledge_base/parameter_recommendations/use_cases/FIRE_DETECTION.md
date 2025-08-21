# Fire Detection Parameter Recommendations

This document provides comprehensive parameter recommendations for fire detection use cases across different environmental conditions and requirements.

## Use Case Overview

Fire detection identifies flames, smoke, and fire-related hazards in surveillance footage. It's critical for early warning systems in buildings, forests, industrial facilities, and public spaces.

## Core Parameters

### Object Detection Parameters
- **conf**: Detection confidence threshold (0.0-1.0)
- **width**: Model input width in pixels
- **height**: Model input height in pixels
- **decoder_width**: Frame decoder width
- **decoder_height**: Frame decoder height
- **iou**: Intersection over Union threshold for NMS
- **max_dets**: Maximum number of detections per frame

### Use Case Specific Parameters
- **alert_interval**: Interval between repeated fire alerts (seconds)
- **severity**: Alert severity level ("low", "medium", "high", "critical")

### System Parameters
- **fps**: Frames per second for processing
- **batch_size**: Processing batch size
- **use_fp16**: Enable half-precision inference
- **use_cuda**: Enable GPU acceleration

## Environmental Condition Profiles

### 1. Low Light Conditions
**Optimized for fire detection in poor lighting conditions**

**Detection Model Parameters:**
- conf: 0.15 (Very low confidence to detect faint flames and smoke)
- width: 1024 (High resolution for better feature extraction)
- height: 1024 (High resolution to capture subtle fire signatures)
- decoder_width: 1024 (Match input size for optimal preprocessing)
- decoder_height: 704 (Maintain aspect ratio for video streams)
- use_fp16: true (Memory optimization for larger images)
- batch_size: 4 (Smaller batches for higher resolution processing)

**Fire Detection Logic Parameters:**
- alert_interval: 30 (Quick alerts for fire emergencies)
- severity: critical (Maximum severity for fire safety)

**System Parameters:**
- fps: 2/1 (Slower processing for thorough analysis)
- use_cuda: true (GPU acceleration essential for complex processing)
### 2. High Accuracy Requirements
**Maximum precision for critical safety areas**

**Detection Model Parameters:**
- conf: 0.6 (Balanced confidence to avoid false positives)
- width: 1280 (Ultra-high resolution for detailed analysis)
- height: 1280 (Ultra-high resolution for accurate detection)
- decoder_width: 1280 (Match input resolution)
- decoder_height: 720 (High definition video processing)
- use_fp16: false (Full precision for maximum accuracy)
- batch_size: 2 (Small batches for precision processing)
- max_dets: 500 (Allow detection of multiple fire sources)

**Fire Detection Logic Parameters:**
- alert_interval: 15 (Very quick alerts for critical areas)
- severity: critical (Maximum severity for safety)

**System Parameters:**
- fps: 5/1 (Higher processing rate for quick detection)
- use_cuda: true (GPU acceleration for performance)

### 3. Outdoor Forest Fire Detection
**Optimized for distant fire and smoke detection in large areas**

**Detection Model Parameters:**
- conf: 0.2 (Low confidence for distant smoke plumes)
- width: 1920 (Maximum resolution for distant object clarity)
- height: 1920 (Ultra-high resolution for small fire detection)
- decoder_width: 1920 (Maximum decoder resolution for fine details)
- decoder_height: 1080 (High definition video processing)
- use_fp16: true (Memory optimization for large resolution)
- batch_size: 1 (Single batch to handle maximum resolution)
- max_dets: 100 (Detect multiple fire spots across landscape)

**Fire Detection Logic Parameters:**
- alert_interval: 60 (Moderate alert interval for forest monitoring)
- severity: high (High severity for forest fire prevention)

**System Parameters:**
- fps: 1/2 (Very slow processing for maximum accuracy at distance)
- use_cuda: true (GPU essential for ultra-high resolution processing)
}
```

### 4. Indoor Environments
**Profile Combination**: `detection.indoor + safety.fire_detection`

```json
{
  "detection_model": {
    ### 4. Indoor Building Fire Detection
**Coverage of indoor spaces with multiple rooms and corridors**

**Detection Model Parameters:**
- conf: 0.3 (Moderate confidence for indoor fire detection)
- width: 896 (Standard high resolution for indoor spaces)
- height: 896 (Balanced resolution for room coverage)
- decoder_width: 896 (Standard decoder resolution)
- decoder_height: 608 (Optimized for indoor camera feeds)
- use_fp16: true (Memory efficiency for building-wide coverage)
- batch_size: 6 (Moderate batches for multiple camera processing)

**Fire Detection Logic Parameters:**
- alert_interval: 20 (Quick alerts for building evacuation)
- severity: critical (Maximum severity for building safety)

**System Parameters:**
- fps: 3/1 (Moderate processing rate for building coverage)
- use_cuda: true (GPU acceleration for multi-room processing)

### 5. True Positive Focus (Maximum Sensitivity)
**Minimize missed fire incidents - safety critical**

**Detection Model Parameters:**
- conf: 0.05 (Extremely low confidence to catch any fire signs)
- width: 1024 (High resolution for sensitivity)
- height: 1024 (High resolution for comprehensive detection)
- decoder_width: 1024 (Match input size)
- decoder_height: 704 (Standard video processing)
- use_fp16: true (Efficient processing)
- batch_size: 4 (Balanced batch size)
- max_dets: 1000 (Allow maximum detections for safety)

**Fire Detection Logic Parameters:**
- alert_interval: 10 (Immediate repeated alerts)
- severity: critical (Maximum severity for safety)

**System Parameters:**
- fps: 10/1 (High FPS for quick fire detection)
- use_cuda: true (GPU acceleration for rapid processing)

### 6. False Positive Reduction (Conservative)
**Minimize false alarms in areas with heat sources**

**Detection Model Parameters:**
- conf: 0.8 (Very high confidence to reduce false positives)
- width: 1024 (High resolution for accurate analysis)
- height: 1024 (High resolution for precise detection)
- decoder_width: 1024 (Standard decoder resolution)
- decoder_height: 704 (Standard video processing)
- use_fp16: true (Efficient processing)
- batch_size: 4 (Standard batch size)
- max_dets: 50 (Limit detections to reduce false positives)

**Fire Detection Logic Parameters:**
- alert_interval: 120 (Conservative alert interval)
- severity: medium (Moderate severity to reduce panic)

**System Parameters:**
- fps: 2/1 (Slower processing for careful analysis)
- use_cuda: true (GPU acceleration)

## Camera Height and Distance Scenarios

### 7. High-Mounted Cameras (15+ meters height)
**Objects appear very small due to extreme camera height**

**Detection Model Parameters:**
- conf: 0.1 (Very low confidence for small fire signatures)
- width: 1920 (Maximum resolution to capture small details)
- height: 1920 (Ultra-high resolution for distant detection)
- decoder_width: 1920 (Maximum preprocessing resolution)
- decoder_height: 1080 (High definition processing)
- use_fp16: true (Memory optimization for large images)
- batch_size: 1 (Single batch for maximum resolution)
- max_dets: 200 (Allow detection of multiple small fire sources)

**Fire Detection Logic Parameters:**
- alert_interval: 45 (Extended interval for distant monitoring)
- severity: high (High severity despite distance)

**System Parameters:**
- fps: 1/2 (Very slow processing for small object accuracy)
- use_cuda: true (GPU essential for processing large images)

### 8. Close-Range Cameras (2-5 meters height)
**Objects appear large and detailed**

**Detection Model Parameters:**
- conf: 0.4 (Standard confidence for clear fire detection)
- width: 640 (Lower resolution sufficient for close-range)
- height: 640 (Standard resolution for detailed objects)
- decoder_width: 640 (Match input resolution)
- decoder_height: 480 (Standard video processing)
- use_fp16: true (Efficient processing)
- batch_size: 8 (Larger batches for efficient processing)
- max_dets: 100 (Standard detection limit)

**Fire Detection Logic Parameters:**
- alert_interval: 15 (Quick alerts for immediate danger)
- severity: critical (Maximum severity for close fires)

**System Parameters:**
- fps: 5/1 (Higher FPS for immediate response)
- use_cuda: true (GPU acceleration)

### 9. Angled Cameras (45-60 degree downward angle)
**Perspective distortion affects fire signature appearance**

**Detection Model Parameters:**
- conf: 0.25 (Lower confidence for perspective-distorted flames)
- width: 1024 (High resolution to handle perspective effects)
- height: 1024 (Square resolution for angle compensation)
- decoder_width: 1024 (High preprocessing resolution)
- decoder_height: 704 (Standard video processing)
- use_fp16: true (Memory optimization)
- batch_size: 4 (Standard batch size)

**Fire Detection Logic Parameters:**
- alert_interval: 30 (Standard alert interval)
- severity: high (High severity for fire safety)

**System Parameters:**
- fps: 3/1 (Moderate processing for perspective analysis)
- use_cuda: true (GPU acceleration for complex processing)

## Hardware-Specific Optimizations

### High-End GPU (RTX 4090, A100)
**Maximum resolution and processing speed**
- width: 1920 (Ultra-high resolution)
- height: 1920 (Maximum detail capture)
- batch_size: 8 (Large batches)
- use_fp16: true (Optimal memory usage)
- fps: 10/1 (High processing rate)

### Mid-Range GPU (RTX 3060, RTX 3070)
**Balanced resolution and performance**
- width: 1280 (High resolution)
- height: 1280 (Good detail capture)
- batch_size: 4 (Moderate batches)
- use_fp16: true (Memory efficiency)
- fps: 5/1 (Standard processing rate)

### Edge Devices (Jetson Orin, Xavier)
**Optimized for power efficiency**
- width: 896 (Optimized resolution)
- height: 896 (Efficient processing)
- batch_size: 2 (Small batches)
- use_fp16: true (Essential for edge)
- fps: 2/1 (Conservative processing)

## Deployment Scenarios

### Industrial Facility
**High-risk environment with heat sources**
- conf: 0.6 (Higher confidence to reduce industrial false positives)
- alert_interval: 45 (Moderate interval for industrial setting)
- severity: critical (Maximum severity for safety)
- fps: 3/1 (Balanced processing)

### Residential Building
**Lower fire risk but high safety priority**
- conf: 0.3 (Moderate confidence for residential fires)
- alert_interval: 20 (Quick alerts for evacuation)
- severity: critical (Maximum severity for human safety)
- fps: 2/1 (Conservative processing)

### Forest/Wildland Monitoring
**Large area coverage with distant detection**
- conf: 0.15 (Low confidence for distant smoke detection)
- alert_interval: 180 (Extended interval for forest monitoring)
- severity: high (High severity for fire prevention)
- fps: 1/3 (Very slow processing for distant accuracy)

### Parking Garage
**Confined space with vehicle fire risk**
- conf: 0.4 (Standard confidence for vehicle fires)
- alert_interval: 25 (Quick alerts for confined space)
- severity: critical (Maximum severity for enclosed area)
- fps: 4/1 (Higher processing for quick detection)

## Troubleshooting Guide

### Common Issues and Solutions

#### Missing Fire Events (High False Negatives)
- Decrease conf by 0.1-0.2 (detect weaker fire signatures)
- Increase width and height resolution (capture more detail)
- Reduce fps for more thorough analysis
- Increase max_dets to allow more detections

#### Too Many False Alerts (High False Positives)
- Increase conf by 0.2-0.3 (filter weak detections)
- Increase alert_interval to reduce alarm frequency
- Reduce max_dets to limit spurious detections
- Use higher resolution for better discrimination

#### Performance Issues
- Reduce width and height resolution
- Decrease batch_size to 2-4
- Reduce fps to 1/1 or slower
- Enable use_fp16 if not already enabled

#### Distance Detection Problems
- For distant fires: decrease conf to 0.1-0.15
- For distant fires: increase resolution to maximum
- For close fires: increase conf to 0.4-0.6
- For close fires: reduce resolution to 640x640

## Parameter Validation

All parameters in this document are validated against actual system capabilities:

- **Object Detection**: Uses real parameters from detection models
- **Fire Detection Logic**: Uses validated fire-specific parameters
- **System Settings**: Uses actual system configuration parameters

This ensures all recommendations can be directly applied to fire detection deployments.
