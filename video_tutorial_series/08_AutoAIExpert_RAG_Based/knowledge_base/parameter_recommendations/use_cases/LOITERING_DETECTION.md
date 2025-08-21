# Loitering Detection Parameter Recommendations

This document provides comprehensive parameter recommendations for loitering detection use cases across different environmental conditions and requirements.

## Use Case Overview

Loitering detection identifies when individuals remain in a specific area for an extended period beyond normal transit or activity patterns. The system tracks person movement and triggers alerts when dwell time exceeds defined thresholds.

## Core Parameters

### Object Detection Parameters
- **conf**: Detection confidence threshold (0.0-1.0)
- **width**: Model input width in pixels  
- **height**: Model input height in pixels
- **decoder_width**: Frame decoder width
- **decoder_height**: Frame decoder height
- **iou**: Intersection over Union threshold for NMS
- **max_dets**: Maximum number of detections per frame

### Tracking Parameters
- **ttl**: Time-to-live for tracks in frames
- **sigma_iou**: IoU weight for Hungarian matching
- **sigma_h**: Upper bound object detection confidence for ViOu tracker
- **sigma_l**: Lower bound object detection confidence for ViOu tracker
- **t_min**: Minimum track length before confirmation

### Use Case Specific Parameters
- **loiteringThresholdSeconds**: Time threshold for loitering detection
- **alert_interval**: Interval between repeated alerts (seconds)
- **severity**: Alert severity level ("low", "medium", "high")

### System Parameters
- **fps**: Frames per second for processing
- **batch_size**: Processing batch size
- **use_fp16**: Enable half-precision inference
- **use_cuda**: Enable GPU acceleration

## Environmental Condition Profiles

### 1. Low Light Conditions
**Optimized for detection in poor lighting conditions**

**Detection Model Parameters:**
- conf: 0.25 (Lower confidence to detect more objects in poor lighting)
- width: 1024 (Higher resolution for better feature extraction)
- height: 1024 (Higher resolution to capture subtle details)
- decoder_width: 1024 (Match input size for optimal preprocessing)
- decoder_height: 704 (Maintain aspect ratio for video streams)
- use_fp16: true (Use half precision to save memory for larger images)
- batch_size: 4 (Smaller batches for higher resolution processing)

**Tracking Parameters:**
- ttl: 6 (Longer track persistence for intermittent detections)
- sigma_iou: 0.25 (More lenient IoU matching for noisy detections)
- sigma_h: 0.25 (Higher upper bound confidence for accepting uncertain detections)
- sigma_l: 0.15 (Lower bound confidence threshold for track association)
- t_min: 2 (Shorter confirmation time for quick track creation)

**Loitering Logic Parameters:**
- loiteringThresholdSeconds: 30 (Shorter threshold to compensate for detection gaps)
- alert_interval: 600 (Standard alert interval)
- severity: medium (Medium severity for balanced alerting)

**System Parameters:**
- fps: 2/1 (Slower processing to allow more analysis time)
- use_cuda: true (GPU acceleration essential for complex processing)

### 2. High Accuracy Requirements
**Maximum precision for critical security areas**

**Detection Model Parameters:**
- conf: 0.8 (High confidence threshold for precision)
- width: 1024 (High resolution for detailed analysis)
- height: 1024 (High resolution for accurate detection)
- decoder_width: 1024 (Match input resolution)
- decoder_height: 704 (Standard video aspect ratio)
- use_fp16: false (Full precision for maximum accuracy)
- batch_size: 4 (Smaller batches for precision processing)
- max_dets: 300 (Standard detection limit)

**Tracking Parameters:**
- ttl: 8 (Longer track persistence for stable tracking)
- sigma_iou: 0.4 (Strict IoU matching for accuracy)
- sigma_h: 0.4 (Higher upper bound confidence for precise tracking)
- sigma_l: 0.1 (Lower bound confidence for rejecting weak detections)
- t_min: 3 (Minimum 3 frames for track confirmation)

**Loitering Logic Parameters:**
- loiteringThresholdSeconds: 120 (Standard 2-minute threshold)
- alert_interval: 600 (10-minute alert interval)
- severity: high (High severity for critical areas)

**System Parameters:**
- fps: 5/1 (Standard processing rate)
- use_cuda: true (GPU acceleration for performance)

### 3. Far Object Detection
**Optimized for distant subject monitoring**

**Detection Model Parameters:**
- conf: 0.3 (Lower confidence for small distant objects)
- width: 1280 (Ultra-high resolution for distant object clarity)
- height: 1280 (Ultra-high resolution for small object detection)
- decoder_width: 1920 (Maximum decoder resolution for fine details)
- decoder_height: 1080 (High definition video processing)
- use_fp16: true (Memory optimization for large resolution)
- batch_size: 2 (Small batches to handle high resolution)

**Tracking Parameters:**
- ttl: 10 (Extended track persistence for sporadic detections)
- sigma_iou: 0.2 (Very lenient IoU for small objects)
- sigma_h: 0.2 (Higher upper bound confidence for distant object detections)
- sigma_l: 0.2 (Higher lower bound confidence tolerance for uncertain detections)
- t_min: 2 (Quick track confirmation for distant movement)

**Loitering Logic Parameters:**
- loiteringThresholdSeconds: 150 (Longer threshold for distant observation)
- alert_interval: 800 (Extended alert interval for distant monitoring)
- severity: medium (Balanced severity for distant detection)

**System Parameters:**
- fps: 1/1 (Slower processing for maximum accuracy)
- use_cuda: true (GPU essential for high resolution processing)

### 4. Wide Area Monitoring
**Coverage of large spaces with multiple zones**

**Detection Model Parameters:**
- conf: 0.4 (Balanced confidence for wide area coverage)
- width: 1024 (High resolution for wide area detail)
- height: 1024 (High resolution for comprehensive coverage)
- decoder_width: 1024 (Standard decoder resolution)
- decoder_height: 704 (Optimized for wide area feeds)
- use_fp16: true (Memory efficiency for larger coverage)
- batch_size: 8 (Larger batches for processing efficiency)

**Tracking Parameters:**
- ttl: 6 (Standard track persistence for wide areas)
- sigma_iou: 0.3 (Moderate IoU matching for varied conditions)
- sigma_h: 0.3 (Moderate upper bound confidence across zones)
- sigma_l: 0.1 (Lower bound confidence for precise zone tracking)
- t_min: 2 (Quick track confirmation for active monitoring)
- t_min: 2 (Quick track confirmation for active monitoring)

**Loitering Logic Parameters:**
- loiteringThresholdSeconds: 90 (Moderate threshold for wide area monitoring)
- alert_interval: 600 (Standard alert interval)
- severity: medium (Balanced severity for general monitoring)

**System Parameters:**
- fps: 3/1 (Moderate processing rate for wide coverage)
- use_cuda: true (GPU acceleration for multi-zone processing)

### 5. True Positive Focus (Maximum Sensitivity)
**Minimize missed detections**

**Object Detection:**
- conf: 0.15 (Very low confidence for maximum sensitivity)
- width: 896 (Moderate resolution for sensitivity balance)
- height: 896 (Moderate resolution for processing efficiency)
- decoder_width: 896 (Match input resolution for optimal processing)
- decoder_height: 608 (Optimized decoder resolution)
- use_fp16: true (Enable FP16 for memory efficiency)
- batch_size: 6 (Moderate batch size for sensitivity processing)
- max_dets: 500 (High detection limit for maximum coverage)

**Tracking:**
- ttl: 8 (Extended track persistence for missed detection recovery)
- sigma_iou: 0.2 (Very lenient IoU matching for maximum tracking)
- sigma_h: 0.2 (Lower upper bound confidence for inclusive tracking)
- sigma_l: 0.15 (Higher lower bound for basic track quality)
- t_min: 1 (Minimum confirmation for immediate detection)

**Use Case Logic:**
- loiteringThresholdSeconds: 60 (Shorter threshold for faster detection)
- alert_interval: 300 (Standard alert interval for maximum sensitivity)
- severity: medium (Balanced severity for high sensitivity mode)

**System:**
- fps: 10/1 (High frame rate for maximum temporal coverage)
- use_cuda: true (GPU acceleration for high-frequency processing)

### 6. False Positive Reduction (Conservative)
**Minimize false alerts in high-traffic areas**

**Object Detection:**
- conf: 0.85 (Very high confidence for strict detection)
- width: 1024 (High resolution for accurate analysis)
- height: 1024 (High resolution for precision detection)
- decoder_width: 1024 (Match input resolution for optimal processing)
- decoder_height: 704 (Standard decoder resolution)
- use_fp16: true (Enable FP16 for memory efficiency)
- batch_size: 4 (Moderate batch size for precision processing)
- max_dets: 100 (Lower detection limit for quality focus)

**Tracking:**
- ttl: 6 (Standard track persistence for stable tracking)
- sigma_iou: 0.5 (Strict IoU matching for precision)
- sigma_h: 0.5 (High upper bound confidence for strict tracking)
- sigma_l: 0.05 (Very low lower bound for rejecting weak detections)
- t_min: 5 (Extended confirmation for false positive reduction)

**Use Case Logic:**
- loiteringThresholdSeconds: 180 (Extended threshold for conservative detection)
- alert_interval: 1200 (Long alert interval to reduce false positive noise)
- severity: low (Lower severity for conservative alerting)

**System:**
- fps: 3/1 (Moderate frame rate for thorough analysis)
- use_cuda: true (GPU acceleration for precision processing)

## Hardware-Specific Optimizations

### High-End GPU Systems (RTX 4090/A100)
**Maximum performance configurations for powerful hardware**

**Object Detection:**
- width: 1280 (High resolution for detailed analysis)
- height: 1280 (High resolution for comprehensive detection)
- batch_size: 16 (High batch size for efficient GPU utilization)
- use_fp16: true (Enable FP16 for performance optimization)

**System:**
- fps: 10/1 (High frame rate for real-time detailed monitoring)
- use_cuda: true (Enable CUDA acceleration for maximum performance)

### Mid-Range GPU Systems (GTX 1660/RTX 3060)
**Balanced performance for moderate hardware**

**Object Detection:**
- width: 1024 (Moderate resolution for balanced processing)
- height: 1024 (Moderate resolution for efficient performance)
- batch_size: 8 (Moderate batch size for balanced performance)
- use_fp16: true (Enable FP16 for performance optimization)

**System:**
- fps: 5/1 (Moderate frame rate for balanced real-time processing)
- use_cuda: true (Enable available GPU acceleration)

### Edge Devices/CPU-Only Systems
**Optimized for low-power, embedded, or CPU-only deployments**

**Object Detection:**
  "model_settings": {
    "width": 896, 
    "height": 896,
    "batch_size": 4,
    "use_fp16": true
  },
  "processing": {
    "fps": "2/1"
  }
}
```

## Deployment Scenarios

### Shopping Mall
```json
{
  "loiteringThresholdSeconds": 180,
  "alert_interval": 600,
  "fps": "3/1",
  "conf": 0.6,
  "severity": "medium"
}
```

### Parking Lot
```json
{
  "loiteringThresholdSeconds": 60,
  "alert_interval": 300,
  "fps": "2/1",
  "conf": 0.4,
  "severity": "medium"
}
```

### Airport Terminal
```json
{
  "loiteringThresholdSeconds": 30,
  "alert_interval": 300,
  "fps": "5/1",
  "conf": 0.7,
  "severity": "high"
}
```

### Residential Area
```json
{
  "loiteringThresholdSeconds": 120,
  "alert_interval": 600,
  "fps": "1/1",
  "conf": 0.5,
  "severity": "low"
}
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Missing Loiterers (High False Negatives)
- Decrease `conf` by 0.1-0.2
- Reduce `loiteringThresholdSeconds` by 25%
- Increase `ttl` to 8-10
- Lower tracking thresholds (`sigma_iou`, `sigma_h`)

#### Too Many False Alerts (High False Positives)
- Increase `conf` by 0.1-0.2
- Increase `loiteringThresholdSeconds` by 50%
- Increase `t_min` to 3-5 frames
- Reduce `max_dets` to filter weak detections

#### Performance Issues
- Reduce model resolution (`width`, `height`)
- Decrease `batch_size` to 4-6
- Reduce `fps` to "2/1" or "1/1"
- Enable `use_fp16` if not already enabled

#### Tracking Inconsistencies
- Increase `ttl` to 8-12
- Adjust `sigma_iou` based on object movement (0.2-0.4)
- Tune `sigma_l` for location uncertainty
- Adjust `t_min` for track confirmation

## Parameter Validation

All parameters in this document are validated against the actual JSON structure from `loitering.json`:

- **Object Detection**: Uses real parameters from the detection node
- **Tracking**: Uses actual ViOu tracker parameters 
- **Use Case Logic**: Uses validated loitering-specific parameters
- **System Settings**: Uses actual system configuration parameters

This ensures all recommendations can be directly applied to production deployments.
