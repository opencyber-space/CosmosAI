# Chain Snatching Detection - Parameter Recommendations

## Use Case Overview
Chain snatching detection identifies theft incidents involving grabbing of jewelry or bags from individuals, critical for personal safety monitoring in public areas, streets, and commercial zones.

## Building Block Parameters

### Object Detection Parameters
- **conf**: Detection confidence threshold (0.0-1.0)
- **width**: Model input width in pixels
- **height**: Model input height in pixels
- **iou**: Intersection over Union threshold for NMS
- **max_dets**: Maximum number of detections per frame

### Tracking Parameters
- **ttl**: Time-to-live for tracks in frames
- **sigma_iou**: IoU weight for Hungarian matching  
- **sigma_h**: Upper bound object detection confidence for ViOu tracker
- **sigma_l**: Lower bound object detection confidence for ViOu tracker
- **t_min**: Minimum track length before confirmation

### Use Case Specific Parameters
- **alert_interval**: Interval between repeated alerts (seconds)
- **severity**: Alert severity level ("low", "medium", "high")

## Environmental Condition Parameters

### 1. Low Light Conditions
**Optimized for evening or poorly lit street monitoring**

**Object Detection:**
- conf: 0.2 (Lower confidence to detect people and actions in poor lighting)
- width: 1920 (Higher resolution for person detail in low light)
- height: 1080 (High resolution for action clarity)
- iou: 0.4 (Standard IoU for overlapping detection)
- max_dets: 150 (Higher detection limit for challenging conditions)

**Tracking:**
- ttl: 10 (Extended track persistence for intermittent detections)
- sigma_iou: 0.25 (Lenient IoU matching for low light tracking)
- sigma_h: 0.25 (Higher confidence bound for uncertain lighting)
- sigma_l: 0.1 (Lower confidence bound for weak detections)
- t_min: 2 (Quick track confirmation for security events)

**Use Case Logic:**
- alert_interval: 300 (5-minute alert interval for incident monitoring)
- severity: high (High severity for theft incidents)

### 2. High Accuracy Requirements
**Maximum precision for critical security zones**

**Object Detection:**
- conf: 0.4 (Higher confidence for reliable person and action detection)
- width: 1920 (Maximum resolution for detailed analysis)
- height: 1080 (High resolution for accurate identification)
- iou: 0.3 (Lower IoU for better person separation)
- max_dets: 200 (Higher detection limit for complex scenes)

**Tracking:**
- ttl: 8 (Standard tracking for reliable monitoring)
- sigma_iou: 0.4 (Strict IoU matching for precision)
- sigma_h: 0.4 (Higher confidence for precise tracking)
- sigma_l: 0.15 (Moderate lower bound for accuracy)
- t_min: 3 (Standard confirmation for reliability)

**Use Case Logic:**
- alert_interval: 180 (3-minute alert interval for security incidents)
- severity: high (Maximum severity for theft threats)

### 3. Crowded Area Monitoring
**Optimized for busy streets and commercial areas**

**Object Detection:**
- conf: 0.3 (Balanced confidence for crowded environments)
- width: 1280 (Standard resolution for processing efficiency)
- height: 720 (Moderate resolution for crowd coverage)
- iou: 0.5 (Higher IoU to handle overlapping people)
- max_dets: 300 (Higher detection limit for crowded scenes)

**Tracking:**
- ttl: 6 (Standard tracking for dynamic crowds)
- sigma_iou: 0.3 (Moderate matching for crowd dynamics)
- sigma_h: 0.3 (Balanced confidence bounds)
- sigma_l: 0.12 (Moderate lower threshold)
- t_min: 2 (Quick confirmation for dynamic environments)

**Use Case Logic:**
- alert_interval: 600 (10-minute interval to reduce crowd noise)
- severity: high (High severity for public safety)

### 4. Wide Area Street Monitoring
**Coverage of large street sections and intersections**

**Object Detection:**
- conf: 0.25 (Lower confidence for distant person detection)
- width: 1920 (High resolution for distant visibility)
- height: 1080 (High resolution for wide area coverage)
- iou: 0.4 (Standard IoU for varied distances)
- max_dets: 250 (High detection limit for wide coverage)

**Tracking:**
- ttl: 12 (Extended tracking for wide area challenges)
- sigma_iou: 0.2 (Lenient matching for distance variations)
- sigma_h: 0.2 (Lower confidence bounds for distant tracking)
- sigma_l: 0.15 (Moderate threshold for wide area detection)
- t_min: 3 (Standard confirmation for wide monitoring)

**Use Case Logic:**
- alert_interval: 300 (Standard interval for street monitoring)
- severity: high (High severity for public safety incidents)

## Camera Height and Positioning Scenarios

### 1. High-Mounted Street Cameras (8+ meters)
**Overhead monitoring of streets and intersections**

**Object Detection:**
- conf: 0.15 (Lower confidence for overhead person detection)
- width: 1920 (High resolution for distant person clarity)
- height: 1080 (Maximum resolution for overhead perspective)
- max_dets: 200 (Higher detection limit for overhead scenes)

**Tracking:**
- ttl: 15 (Extended tracking for overhead challenges)
- sigma_iou: 0.2 (Very lenient matching for perspective distortion)
- sigma_h: 0.2 (Lower confidence for overhead detection)
- t_min: 4 (Extended confirmation for overhead perspective)

**Use Case Logic:**
- alert_interval: 300 (Standard interval for overhead monitoring)
- severity: medium (Medium severity due to overhead limitations)

### 2. Standard Street Cameras (4-6 meters)
**Typical street surveillance camera mounting**

**Object Detection:**
- conf: 0.25 (Standard confidence for street monitoring)
- width: 1280 (Standard resolution for street coverage)
- height: 720 (Efficient resolution for standard height)
- max_dets: 150 (Moderate detection limit for street scenes)

**Tracking:**
- ttl: 8 (Standard tracking persistence)
- sigma_iou: 0.3 (Balanced IoU for street perspective)
- sigma_h: 0.3 (Standard confidence bounds)
- t_min: 3 (Standard confirmation time)

**Use Case Logic:**
- alert_interval: 300 (Standard interval for street security)
- severity: high (High severity for street incidents)

### 3. Low-Mounted Security Cameras (2-3 meters)
**Close monitoring of walkways and entry points**

**Object Detection:**
- conf: 0.35 (Higher confidence for close-range clarity)
- width: 1280 (Sufficient resolution for close monitoring)
- height: 720 (Standard resolution for detailed analysis)
- max_dets: 100 (Moderate detection limit for close areas)

**Tracking:**
- ttl: 6 (Shorter tracking for close monitoring)
- sigma_iou: 0.4 (Precise matching for clear visibility)
- sigma_h: 0.4 (Higher confidence for close detection)
- t_min: 2 (Quick confirmation for close-range incidents)

**Use Case Logic:**
- alert_interval: 180 (Frequent alerts for close monitoring)
- severity: high (High severity for close-range incidents)

## Hardware-Specific Optimizations

### High-End Security Systems (RTX 4090/A100)
**Maximum performance for critical public safety**

**Object Detection:**
- conf: 0.3 (Balanced confidence with processing power)
- width: 1920 (Maximum resolution for detailed analysis)
- height: 1080 (High resolution for comprehensive monitoring)
- max_dets: 400 (High detection limit for complex street scenes)

**System:**
- use_cuda: true (Enable CUDA for maximum performance)
- use_fp16: false (Full precision for safety accuracy)
- batch_size: 8 (High batch size for efficient processing)
- fps: 4 (High frame rate for incident detection)

### Mid-Range Security Systems (GTX 1660/RTX 3060)
**Balanced performance for street monitoring**

**Object Detection:**
- conf: 0.3 (Standard confidence for balanced processing)
- width: 1280 (Moderate resolution for efficiency)
- height: 720 (Standard resolution for balanced performance)
- max_dets: 200 (Moderate detection limit)

**System:**
- use_cuda: true (Enable available GPU acceleration)
- use_fp16: true (Enable FP16 for optimization)
- batch_size: 4 (Balanced batch processing)
- fps: 2 (Moderate frame rate for real-time processing)

### Edge Security Devices/CPU-Only
**Optimized for distributed street monitoring**

**Object Detection:**
- conf: 0.4 (Higher confidence to reduce processing load)
- width: 640 (Lower resolution for CPU efficiency)
- height: 480 (Reduced resolution for performance)
- max_dets: 50 (Limited detections for efficiency)

**System:**
- use_cuda: false (CPU-only processing)
- use_fp16: false (CPU compatibility)
- batch_size: 1 (Single batch for CPU efficiency)
- fps: 1 (Low frame rate for CPU processing)

## Specific Environment Scenarios

### Commercial Shopping Streets
**Retail area safety monitoring**

**Object Detection:**
- conf: 0.3 (Balanced confidence for commercial areas)
- max_dets: 200 (Higher detection limit for busy commercial areas)

**Use Case Logic:**
- alert_interval: 300 (Standard interval for commercial security)
- severity: high (High severity for customer safety)

### Residential Areas and Neighborhoods
**Community safety monitoring**

**Object Detection:**
- conf: 0.25 (Moderate confidence for residential monitoring)
- max_dets: 100 (Lower detection limit for quieter areas)

**Use Case Logic:**
- alert_interval: 600 (Longer interval for residential areas)
- severity: high (High severity for resident safety)

### Public Transportation Areas
**Transit hub and station monitoring**

**Object Detection:**
- conf: 0.35 (Higher confidence for transit security)
- max_dets: 250 (High detection limit for busy transit areas)

**Use Case Logic:**
- alert_interval: 180 (Frequent alerts for transit security)
- severity: high (High severity for public transportation safety)

### ATM and Banking Areas
**Financial facility security monitoring**

**Object Detection:**
- conf: 0.4 (High confidence for financial security)
- width: 1920 (Maximum resolution for detailed monitoring)
- height: 1080 (High resolution for security accuracy)

**Use Case Logic:**
- alert_interval: 120 (Frequent alerts for financial security)
- severity: high (Maximum severity for financial facilities)

## Common Issues and Parameter Solutions

### False Positives (Incorrect Incident Alerts)
**Parameter adjustments to reduce false alarms**

- **Increase conf**: Raise to 0.4-0.5 for stricter person detection
- **Extend t_min**: Increase to 4-6 frames for incident verification
- **Adjust alert_interval**: Extend to 600-900 seconds
- **Tune sigma_h**: Increase to 0.4-0.5 for stricter tracking

### Missing Incidents (False Negatives)
**Parameter adjustments to catch more theft events**

- **Decrease conf**: Lower to 0.15-0.25 for sensitivity
- **Reduce t_min**: Decrease to 1-2 frames for quick detection
- **Increase max_dets**: Raise to 300-400 for more detections
- **Lower sigma_l**: Reduce to 0.05-0.1 for weak detection inclusion

### Performance Optimization Issues
**Parameter adjustments for resource constraints**

- **Reduce resolution**: Lower width/height to 640x480
- **Enable use_fp16**: Activate for performance improvement
- **Decrease batch_size**: Reduce to 1-2 for memory efficiency
- **Lower fps**: Reduce to 0.5-1 for processing capability

This comprehensive chain snatching detection parameter guide ensures optimal public safety performance while balancing incident detection accuracy with system efficiency across diverse urban environments.
