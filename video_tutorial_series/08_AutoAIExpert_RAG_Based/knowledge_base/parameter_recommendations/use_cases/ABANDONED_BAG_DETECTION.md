# Abandoned Bag Detection - Parameter Recommendations

## Use Case Overview
Abandoned bag detection identifies unattended objects in public spaces, critical for security monitoring in airports, train stations, public venues, and high-security areas.

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
**Optimized for indoor areas with minimal lighting**

**Object Detection:**
- conf: 0.3 (Lower confidence to detect bags in poor lighting)
- width: 1920 (Higher resolution for bag detail in low light)
- height: 1080 (High resolution for object clarity)
- iou: 0.4 (Standard IoU for overlapping objects)
- max_dets: 100 (Higher detection limit for challenging conditions)

**Tracking:**
- ttl: 8 (Extended track persistence for intermittent detections)
- sigma_iou: 0.3 (Moderate IoU matching for stable tracking)
- sigma_h: 0.3 (Higher confidence bound for uncertain lighting)
- sigma_l: 0.1 (Lower confidence bound for weak detections)
- t_min: 3 (Minimum frames for track confirmation)

**Use Case Logic:**
- alert_interval: 300 (5-minute alert interval for security monitoring)
- severity: high (High severity for security threat)

### 2. High Accuracy Requirements
**Maximum precision for critical security areas like airports**

**Object Detection:**
- conf: 0.5 (Higher confidence for reliable bag detection)
- width: 1920 (Maximum resolution for detailed analysis)
- height: 1080 (High resolution for accurate identification)
- iou: 0.3 (Lower IoU for better object separation)
- max_dets: 150 (Moderate detection limit for accuracy)

**Tracking:**
- ttl: 10 (Extended tracking for thorough monitoring)
- sigma_iou: 0.4 (Strict IoU matching for precision)
- sigma_h: 0.4 (Higher confidence for precise tracking)
- sigma_l: 0.2 (Moderate lower bound for accuracy)
- t_min: 5 (Extended confirmation for reliability)

**Use Case Logic:**
- alert_interval: 180 (3-minute alert interval for critical areas)
- severity: high (Maximum severity for security threats)

### 3. Crowded Area Monitoring
**Optimized for busy public spaces with many objects**

**Object Detection:**
- conf: 0.4 (Balanced confidence for crowded environments)
- width: 1280 (Standard resolution for processing efficiency)
- height: 720 (Moderate resolution for crowded area coverage)
- iou: 0.5 (Higher IoU to handle overlapping objects)
- max_dets: 200 (Higher detection limit for crowded scenes)

**Tracking:**
- ttl: 6 (Standard tracking persistence)
- sigma_iou: 0.3 (Moderate matching for crowd dynamics)
- sigma_h: 0.3 (Balanced confidence bounds)
- sigma_l: 0.15 (Moderate lower threshold)
- t_min: 2 (Quick confirmation for dynamic environments)

**Use Case Logic:**
- alert_interval: 600 (10-minute interval to reduce noise)
- severity: medium (Balanced severity for public areas)

## Camera Height and Positioning Scenarios

### 1. High-Mounted Security Cameras (6+ meters)
**Overhead monitoring in large public spaces**

**Object Detection:**
- conf: 0.25 (Lower confidence for overhead bag detection)
- width: 1920 (High resolution for distant object clarity)
- height: 1080 (Maximum resolution for overhead perspective)

**Tracking:**
- ttl: 12 (Extended tracking for overhead challenges)
- sigma_iou: 0.2 (Lenient matching for perspective distortion)
- t_min: 4 (Extended confirmation for overhead detection)

### 2. Standard Security Cameras (2-4 meters)
**Typical surveillance camera mounting height**

**Object Detection:**
- conf: 0.4 (Standard confidence for clear detection)
- width: 1280 (Standard resolution for typical monitoring)
- height: 720 (Efficient resolution for standard height)

**Tracking:**
- ttl: 8 (Standard tracking persistence)
- sigma_iou: 0.3 (Balanced IoU for standard perspective)
- t_min: 3 (Standard confirmation time)

### 3. Close-Range Monitoring (1-2 meters)
**Detailed monitoring for entry points or specific zones**

**Object Detection:**
- conf: 0.5 (Higher confidence for close-range clarity)
- width: 1280 (Sufficient resolution for close monitoring)
- height: 720 (Standard resolution for detailed analysis)

**Tracking:**
- ttl: 6 (Shorter tracking for close monitoring)
- sigma_iou: 0.4 (Precise matching for clear visibility)
- t_min: 2 (Quick confirmation for close-range detection)

## Hardware-Specific Optimizations

### High-End Security Systems (RTX 4090/A100)
**Maximum performance for critical infrastructure**

**Object Detection:**
- conf: 0.4 (Balanced confidence with processing power)
- width: 1920 (Maximum resolution for detailed analysis)
- height: 1080 (High resolution for comprehensive monitoring)
- max_dets: 300 (High detection limit for complex scenes)

**System:**
- use_cuda: true (Enable CUDA for maximum performance)
- use_fp16: false (Full precision for security accuracy)
- batch_size: 8 (High batch size for efficient processing)
- fps: 4 (High frame rate for real-time monitoring)

### Mid-Range Security Systems (GTX 1660/RTX 3060)
**Balanced performance for standard deployments**

**Object Detection:**
- conf: 0.4 (Standard confidence for balanced processing)
- width: 1280 (Moderate resolution for efficiency)
- height: 720 (Standard resolution for balanced performance)
- max_dets: 150 (Moderate detection limit)

**System:**
- use_cuda: true (Enable available GPU acceleration)
- use_fp16: true (Enable FP16 for optimization)
- batch_size: 4 (Balanced batch processing)
- fps: 2 (Moderate frame rate for real-time processing)

### Edge Security Devices/CPU-Only
**Optimized for distributed security nodes**

**Object Detection:**
- conf: 0.5 (Higher confidence to reduce processing load)
- width: 640 (Lower resolution for CPU efficiency)
- height: 480 (Reduced resolution for performance)
- max_dets: 50 (Limited detections for efficiency)

**System:**
- use_cuda: false (CPU-only processing)
- use_fp16: false (CPU compatibility)
- batch_size: 1 (Single batch for CPU efficiency)
- fps: 1 (Low frame rate for CPU processing)

## Specific Security Environment Scenarios

### Airport Security Areas
**High-security monitoring for aviation environments**

**Object Detection:**
- conf: 0.5 (High confidence for aviation security)
- max_dets: 200 (Higher detection limit for busy areas)

**Use Case Logic:**
- alert_interval: 120 (Frequent alerts for aviation security)
- severity: high (Maximum severity for aviation threats)

### Train Stations and Transit Hubs
**Public transportation security monitoring**

**Object Detection:**
- conf: 0.4 (Balanced confidence for transit environments)
- max_dets: 250 (High detection limit for busy transit areas)

**Use Case Logic:**
- alert_interval: 300 (Standard interval for transit security)
- severity: high (High severity for public transportation)

### Shopping Malls and Retail Areas
**Commercial area security monitoring**

**Object Detection:**
- conf: 0.35 (Moderate confidence for retail environments)
- max_dets: 150 (Moderate detection limit for commercial areas)

**Use Case Logic:**
- alert_interval: 600 (Longer interval for commercial areas)
- severity: medium (Balanced severity for retail security)

### Government Buildings
**High-security facilities monitoring**

**Object Detection:**
- conf: 0.6 (High confidence for government security)
- width: 1920 (Maximum resolution for detailed analysis)
- height: 1080 (High resolution for security accuracy)

**Use Case Logic:**
- alert_interval: 60 (Frequent alerts for government security)
- severity: high (Maximum severity for government facilities)

## Common Issues and Parameter Solutions

### False Positives (Incorrect Bag Alerts)
**Parameter adjustments to reduce false alarms**

- **Increase conf**: Raise to 0.5-0.6 for stricter detection
- **Extend t_min**: Increase to 4-6 frames for verification
- **Adjust alert_interval**: Extend to 600-900 seconds
- **Tune sigma_h**: Increase to 0.4-0.5 for stricter tracking

### Missing Bags (False Negatives)
**Parameter adjustments to catch more abandoned items**

- **Decrease conf**: Lower to 0.2-0.3 for sensitivity
- **Reduce t_min**: Decrease to 1-2 frames for quick detection
- **Increase max_dets**: Raise to 200-300 for more detections
- **Lower sigma_l**: Reduce to 0.05-0.1 for weak detection inclusion

### Performance Optimization Issues
**Parameter adjustments for resource constraints**

- **Reduce resolution**: Lower width/height to 640x480
- **Enable use_fp16**: Activate for performance improvement
- **Decrease batch_size**: Reduce to 1-2 for memory efficiency
- **Lower fps**: Reduce to 0.5-1 for processing capability

This comprehensive abandoned bag detection parameter guide ensures optimal security performance while balancing detection accuracy with system efficiency across diverse security environments.
