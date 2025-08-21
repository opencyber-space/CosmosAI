# Parking Violation Detection - Parameter Recommendations

## Use Case Overview
Parking violation detection identifies vehicles parked illegally in restricted areas, critical for traffic management, parking enforcement, and urban planning in cities, commercial areas, and restricted zones.

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
**Optimized for nighttime parking enforcement or poorly lit areas**

**Object Detection:**
- conf: 0.3 (Lower confidence to detect vehicles in poor lighting)
- width: 1920 (Higher resolution for vehicle detail in low light)
- height: 1080 (High resolution for license plate visibility)
- iou: 0.4 (Standard IoU for overlapping vehicle detection)
- max_dets: 100 (Higher detection limit for parking areas)

**Tracking:**
- ttl: 12 (Extended track persistence for stationary vehicles)
- sigma_iou: 0.3 (Moderate IoU matching for vehicle tracking)
- sigma_h: 0.3 (Higher confidence bound for uncertain lighting)
- sigma_l: 0.1 (Lower confidence bound for weak detections)
- t_min: 5 (Extended confirmation for stationary detection)

**Use Case Logic:**
- alert_interval: 600 (10-minute alert interval for parking monitoring)
- severity: medium (Medium severity for parking violations)

### 2. High Accuracy Requirements
**Maximum precision for critical enforcement zones**

**Object Detection:**
- conf: 0.4 (Higher confidence for reliable vehicle detection)
- width: 1920 (Maximum resolution for detailed vehicle analysis)
- height: 1080 (High resolution for accurate identification)
- iou: 0.3 (Lower IoU for better vehicle separation)
- max_dets: 150 (Moderate detection limit for accuracy)

**Tracking:**
- ttl: 15 (Extended tracking for thorough monitoring)
- sigma_iou: 0.4 (Strict IoU matching for precision)
- sigma_h: 0.4 (Higher confidence for precise tracking)
- sigma_l: 0.15 (Moderate lower bound for accuracy)
- t_min: 8 (Extended confirmation for reliability)

**Use Case Logic:**
- alert_interval: 300 (5-minute alert interval for enforcement)
- severity: high (High severity for critical zones)

### 3. Busy Parking Area Monitoring
**Optimized for crowded parking lots and street parking**

**Object Detection:**
- conf: 0.35 (Balanced confidence for busy parking areas)
- width: 1280 (Standard resolution for processing efficiency)
- height: 720 (Moderate resolution for parking coverage)
- iou: 0.5 (Higher IoU to handle closely parked vehicles)
- max_dets: 200 (Higher detection limit for busy areas)

**Tracking:**
- ttl: 10 (Standard tracking for parking dynamics)
- sigma_iou: 0.3 (Moderate matching for parking flow)
- sigma_h: 0.3 (Balanced confidence bounds)
- sigma_l: 0.12 (Moderate lower threshold)
- t_min: 6 (Standard confirmation for parking detection)

**Use Case Logic:**
- alert_interval: 900 (15-minute interval for busy area management)
- severity: medium (Balanced severity for busy areas)

### 4. Wide Area Parking Monitoring
**Coverage of large parking facilities and street sections**

**Object Detection:**
- conf: 0.25 (Lower confidence for distant vehicle detection)
- width: 1920 (High resolution for wide area visibility)
- height: 1080 (High resolution for large area coverage)
- iou: 0.4 (Standard IoU for varied parking densities)
- max_dets: 250 (High detection limit for wide coverage)

**Tracking:**
- ttl: 20 (Extended tracking for wide area challenges)
- sigma_iou: 0.25 (Lenient matching for distance variations)
- sigma_h: 0.25 (Lower confidence bounds for distant tracking)
- sigma_l: 0.1 (Lower threshold for wide area detection)
- t_min: 10 (Extended confirmation for wide monitoring)

**Use Case Logic:**
- alert_interval: 600 (Standard interval for wide area monitoring)
- severity: medium (Medium severity for large area management)

## Camera Height and Positioning Scenarios

### 1. High-Mounted Traffic Cameras (8+ meters)
**Overhead monitoring of parking lots and street parking**

**Object Detection:**
- conf: 0.2 (Lower confidence for overhead vehicle detection)
- width: 1920 (High resolution for distant vehicle clarity)
- height: 1080 (Maximum resolution for overhead perspective)
- max_dets: 200 (Higher detection limit for overhead parking scenes)

**Tracking:**
- ttl: 25 (Extended tracking for overhead challenges)
- sigma_iou: 0.2 (Very lenient matching for perspective distortion)
- sigma_h: 0.2 (Lower confidence for overhead detection)
- t_min: 12 (Extended confirmation for overhead perspective)

**Use Case Logic:**
- alert_interval: 600 (Standard interval for overhead monitoring)
- severity: medium (Medium severity due to overhead limitations)

### 2. Standard Parking Cameras (4-6 meters)
**Typical parking surveillance camera mounting**

**Object Detection:**
- conf: 0.3 (Standard confidence for parking monitoring)
- width: 1280 (Standard resolution for parking coverage)
- height: 720 (Efficient resolution for standard height)
- max_dets: 150 (Moderate detection limit for parking areas)

**Tracking:**
- ttl: 15 (Standard tracking persistence)
- sigma_iou: 0.3 (Balanced IoU for parking perspective)
- sigma_h: 0.3 (Standard confidence bounds)
- t_min: 8 (Standard confirmation time)

**Use Case Logic:**
- alert_interval: 600 (Standard interval for parking enforcement)
- severity: medium (Medium severity for parking violations)

### 3. Ground-Level Parking Cameras (2-4 meters)
**Close monitoring of specific parking zones**

**Object Detection:**
- conf: 0.4 (Higher confidence for close-range vehicle detection)
- width: 1280 (Sufficient resolution for close monitoring)
- height: 720 (Standard resolution for detailed analysis)
- max_dets: 100 (Moderate detection limit for close areas)

**Tracking:**
- ttl: 12 (Tracking for close monitoring)
- sigma_iou: 0.4 (Precise matching for clear visibility)
- sigma_h: 0.4 (Higher confidence for close detection)
- t_min: 6 (Standard confirmation for close-range parking)

**Use Case Logic:**
- alert_interval: 300 (Frequent alerts for close monitoring)
- severity: high (High severity for close enforcement zones)

## Hardware-Specific Optimizations

### High-End Traffic Systems (RTX 4090/A100)
**Maximum performance for comprehensive parking management**

**Object Detection:**
- conf: 0.3 (Balanced confidence with processing power)
- width: 1920 (Maximum resolution for detailed vehicle analysis)
- height: 1080 (High resolution for comprehensive monitoring)
- max_dets: 400 (High detection limit for complex parking scenes)

**System:**
- use_cuda: true (Enable CUDA for maximum performance)
- use_fp16: false (Full precision for enforcement accuracy)
- batch_size: 8 (High batch size for efficient processing)
- fps: 2 (Moderate frame rate for parking monitoring)

### Mid-Range Traffic Systems (GTX 1660/RTX 3060)
**Balanced performance for standard parking enforcement**

**Object Detection:**
- conf: 0.35 (Standard confidence for balanced processing)
- width: 1280 (Moderate resolution for efficiency)
- height: 720 (Standard resolution for balanced performance)
- max_dets: 200 (Moderate detection limit)

**System:**
- use_cuda: true (Enable available GPU acceleration)
- use_fp16: true (Enable FP16 for optimization)
- batch_size: 4 (Balanced batch processing)
- fps: 1 (Standard frame rate for parking monitoring)

### Edge Traffic Devices/CPU-Only
**Optimized for distributed parking monitoring**

**Object Detection:**
- conf: 0.4 (Higher confidence to reduce processing load)
- width: 640 (Lower resolution for CPU efficiency)
- height: 480 (Reduced resolution for performance)
- max_dets: 50 (Limited detections for efficiency)

**System:**
- use_cuda: false (CPU-only processing)
- use_fp16: false (CPU compatibility)
- batch_size: 1 (Single batch for CPU efficiency)
- fps: 0.5 (Low frame rate for CPU processing)

## Specific Environment Scenarios

### Commercial District Parking
**Business area parking enforcement**

**Object Detection:**
- conf: 0.35 (Balanced confidence for commercial areas)
- max_dets: 200 (Higher detection limit for busy commercial parking)

**Use Case Logic:**
- alert_interval: 300 (Frequent alerts for commercial enforcement)
- severity: high (High severity for business district compliance)

### Residential Area Parking
**Neighborhood parking monitoring**

**Object Detection:**
- conf: 0.3 (Moderate confidence for residential monitoring)
- max_dets: 100 (Lower detection limit for quieter areas)

**Use Case Logic:**
- alert_interval: 900 (Longer interval for residential areas)
- severity: medium (Medium severity for neighborhood compliance)

### Hospital and Emergency Zones
**Critical facility parking enforcement**

**Object Detection:**
- conf: 0.4 (High confidence for emergency zone enforcement)
- width: 1920 (Maximum resolution for critical area monitoring)
- height: 1080 (High resolution for enforcement accuracy)

**Use Case Logic:**
- alert_interval: 180 (Frequent alerts for emergency zone enforcement)
- severity: high (Maximum severity for emergency access)

### Airport and Transit Parking
**Transportation hub parking management**

**Object Detection:**
- conf: 0.3 (Balanced confidence for transit parking)
- max_dets: 300 (High detection limit for busy transit areas)

**Use Case Logic:**
- alert_interval: 600 (Standard interval for transit enforcement)
- severity: high (High severity for transportation facilities)

## Common Issues and Parameter Solutions

### False Positives (Incorrect Violation Alerts)
**Parameter adjustments to reduce false parking alarms**

- **Increase conf**: Raise to 0.4-0.5 for stricter vehicle detection
- **Extend t_min**: Increase to 10-15 frames for violation verification
- **Adjust alert_interval**: Extend to 900-1200 seconds
- **Tune sigma_h**: Increase to 0.4-0.5 for stricter tracking

### Missing Violations (False Negatives)
**Parameter adjustments to catch more parking violations**

- **Decrease conf**: Lower to 0.2-0.3 for sensitivity
- **Reduce t_min**: Decrease to 3-5 frames for quick detection
- **Increase max_dets**: Raise to 300-400 for more detections
- **Lower sigma_l**: Reduce to 0.05-0.1 for weak detection inclusion

### Performance Optimization Issues
**Parameter adjustments for resource constraints**

- **Reduce resolution**: Lower width/height to 640x480
- **Enable use_fp16**: Activate for performance improvement
- **Decrease batch_size**: Reduce to 1-2 for memory efficiency
- **Lower fps**: Reduce to 0.25-0.5 for processing capability

This comprehensive parking violation detection parameter guide ensures optimal traffic management performance while balancing enforcement accuracy with system efficiency across diverse urban and commercial environments.
