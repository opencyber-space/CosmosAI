# Crowd Gathering Detection - Parameter Recommendations

## Use Case Overview
Crowd gathering detection identifies when groups of people congregate in specific areas, critical for crowd management, event monitoring, and public safety in venues, streets, and gathering spaces.

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
**Optimized for evening events or poorly lit gathering areas**

**Object Detection:**
- conf: 0.25 (Lower confidence to detect people in poor lighting)
- width: 1920 (Higher resolution for crowd detail in low light)
- height: 1080 (High resolution for group visibility)
- iou: 0.5 (Higher IoU for overlapping people in crowds)
- max_dets: 300 (Higher detection limit for crowd scenarios)

**Tracking:**
- ttl: 8 (Extended track persistence for intermittent detections)
- sigma_iou: 0.3 (Moderate IoU matching for crowd tracking)
- sigma_h: 0.3 (Higher confidence bound for uncertain lighting)
- sigma_l: 0.1 (Lower confidence bound for weak detections)
- t_min: 2 (Quick track confirmation for crowd dynamics)

**Use Case Logic:**
- alert_interval: 300 (5-minute alert interval for crowd monitoring)
- severity: medium (Medium severity for crowd management)

### 2. High Accuracy Requirements
**Maximum precision for critical event monitoring**

**Object Detection:**
- conf: 0.4 (Higher confidence for reliable crowd detection)
- width: 1920 (Maximum resolution for detailed crowd analysis)
- height: 1080 (High resolution for accurate crowd counting)
- iou: 0.5 (Standard IoU for crowd overlap handling)
- max_dets: 500 (High detection limit for large crowds)

**Tracking:**
- ttl: 10 (Extended tracking for thorough crowd monitoring)
- sigma_iou: 0.4 (Strict IoU matching for precision)
- sigma_h: 0.4 (Higher confidence for precise tracking)
- sigma_l: 0.15 (Moderate lower bound for accuracy)
- t_min: 3 (Standard confirmation for reliability)

**Use Case Logic:**
- alert_interval: 180 (3-minute alert interval for event management)
- severity: high (High severity for crowd control)

### 3. Large Venue Monitoring
**Optimized for stadiums, concert halls, and large events**

**Object Detection:**
- conf: 0.3 (Balanced confidence for large venue coverage)
- width: 1920 (High resolution for venue-wide monitoring)
- height: 1080 (High resolution for large crowd coverage)
- iou: 0.6 (Higher IoU for dense crowd overlap)
- max_dets: 800 (Very high detection limit for large venues)

**Tracking:**
- ttl: 6 (Standard tracking for venue dynamics)
- sigma_iou: 0.3 (Moderate matching for venue crowd flow)
- sigma_h: 0.3 (Balanced confidence bounds)
- sigma_l: 0.12 (Moderate lower threshold)
- t_min: 2 (Quick confirmation for dynamic crowds)

**Use Case Logic:**
- alert_interval: 600 (10-minute interval for venue management)
- severity: high (High severity for public safety)

### 4. Wide Area Public Space Monitoring
**Coverage of parks, squares, and open public areas**

**Object Detection:**
- conf: 0.2 (Lower confidence for distant crowd detection)
- width: 1920 (High resolution for wide area visibility)
- height: 1080 (High resolution for public space coverage)
- iou: 0.4 (Standard IoU for varied crowd densities)
- max_dets: 400 (High detection limit for public spaces)

**Tracking:**
- ttl: 12 (Extended tracking for wide area challenges)
- sigma_iou: 0.25 (Lenient matching for distance variations)
- sigma_h: 0.25 (Lower confidence bounds for distant tracking)
- sigma_l: 0.1 (Lower threshold for wide area detection)
- t_min: 3 (Standard confirmation for public monitoring)

**Use Case Logic:**
- alert_interval: 300 (Standard interval for public space monitoring)
- severity: medium (Medium severity for public space management)

## Camera Height and Positioning Scenarios

### 1. High-Mounted Venue Cameras (10+ meters)
**Overhead monitoring of large venues and open spaces**

**Object Detection:**
- conf: 0.15 (Lower confidence for overhead crowd detection)
- width: 1920 (High resolution for distant crowd clarity)
- height: 1080 (Maximum resolution for overhead perspective)
- max_dets: 600 (High detection limit for overhead crowd scenes)

**Tracking:**
- ttl: 15 (Extended tracking for overhead challenges)
- sigma_iou: 0.2 (Very lenient matching for perspective distortion)
- sigma_h: 0.2 (Lower confidence for overhead detection)
- t_min: 4 (Extended confirmation for overhead perspective)

**Use Case Logic:**
- alert_interval: 300 (Standard interval for overhead monitoring)
- severity: medium (Medium severity due to overhead limitations)

### 2. Standard Event Cameras (4-8 meters)
**Typical event surveillance camera mounting**

**Object Detection:**
- conf: 0.3 (Standard confidence for event monitoring)
- width: 1280 (Standard resolution for event coverage)
- height: 720 (Efficient resolution for standard height)
- max_dets: 400 (High detection limit for event crowds)

**Tracking:**
- ttl: 8 (Standard tracking persistence)
- sigma_iou: 0.3 (Balanced IoU for event perspective)
- sigma_h: 0.3 (Standard confidence bounds)
- t_min: 3 (Standard confirmation time)

**Use Case Logic:**
- alert_interval: 300 (Standard interval for event management)
- severity: high (High severity for event safety)

### 3. Ground-Level Monitoring Cameras (2-4 meters)
**Close monitoring of entry points and gathering areas**

**Object Detection:**
- conf: 0.4 (Higher confidence for close-range crowd detection)
- width: 1280 (Sufficient resolution for close monitoring)
- height: 720 (Standard resolution for detailed analysis)
- max_dets: 200 (Moderate detection limit for close areas)

**Tracking:**
- ttl: 6 (Shorter tracking for close monitoring)
- sigma_iou: 0.4 (Precise matching for clear visibility)
- sigma_h: 0.4 (Higher confidence for close detection)
- t_min: 2 (Quick confirmation for close-range crowd formation)

**Use Case Logic:**
- alert_interval: 180 (Frequent alerts for close monitoring)
- severity: high (High severity for close-range crowd management)

## Hardware-Specific Optimizations

### High-End Event Systems (RTX 4090/A100)
**Maximum performance for large-scale event monitoring**

**Object Detection:**
- conf: 0.3 (Balanced confidence with processing power)
- width: 1920 (Maximum resolution for detailed crowd analysis)
- height: 1080 (High resolution for comprehensive monitoring)
- max_dets: 1000 (Very high detection limit for massive crowds)

**System:**
- use_cuda: true (Enable CUDA for maximum performance)
- use_fp16: false (Full precision for crowd counting accuracy)
- batch_size: 8 (High batch size for efficient processing)
- fps: 4 (High frame rate for crowd dynamics tracking)

### Mid-Range Event Systems (GTX 1660/RTX 3060)
**Balanced performance for standard event monitoring**

**Object Detection:**
- conf: 0.3 (Standard confidence for balanced processing)
- width: 1280 (Moderate resolution for efficiency)
- height: 720 (Standard resolution for balanced performance)
- max_dets: 500 (High detection limit for crowd scenes)

**System:**
- use_cuda: true (Enable available GPU acceleration)
- use_fp16: true (Enable FP16 for optimization)
- batch_size: 4 (Balanced batch processing)
- fps: 2 (Moderate frame rate for real-time processing)

### Edge Monitoring Devices/CPU-Only
**Optimized for distributed crowd monitoring**

**Object Detection:**
- conf: 0.4 (Higher confidence to reduce processing load)
- width: 640 (Lower resolution for CPU efficiency)
- height: 480 (Reduced resolution for performance)
- max_dets: 100 (Limited detections for efficiency)

**System:**
- use_cuda: false (CPU-only processing)
- use_fp16: false (CPU compatibility)
- batch_size: 1 (Single batch for CPU efficiency)
- fps: 1 (Low frame rate for CPU processing)

## Specific Environment Scenarios

### Concert Venues and Music Festivals
**Entertainment event crowd monitoring**

**Object Detection:**
- conf: 0.25 (Lower confidence for energetic crowd detection)
- max_dets: 800 (Very high detection limit for concert crowds)

**Use Case Logic:**
- alert_interval: 300 (Standard interval for entertainment events)
- severity: high (High severity for concert safety)

### Sports Stadiums and Arenas
**Athletic event crowd management**

**Object Detection:**
- conf: 0.3 (Balanced confidence for sports crowd monitoring)
- max_dets: 1000 (Maximum detection limit for stadium crowds)

**Use Case Logic:**
- alert_interval: 180 (Frequent alerts for sports event management)
- severity: high (High severity for sports venue safety)

### Public Squares and Demonstration Areas
**Political gathering and protest monitoring**

**Object Detection:**
- conf: 0.2 (Lower confidence for varied crowd behavior)
- max_dets: 600 (High detection limit for public gatherings)

**Use Case Logic:**
- alert_interval: 120 (Frequent alerts for public safety)
- severity: high (High severity for public order management)

### Shopping Centers and Malls
**Commercial venue crowd monitoring**

**Object Detection:**
- conf: 0.35 (Higher confidence for retail crowd management)
- max_dets: 300 (Moderate detection limit for commercial areas)

**Use Case Logic:**
- alert_interval: 600 (Longer interval for commercial crowd management)
- severity: medium (Medium severity for retail environments)

## Common Issues and Parameter Solutions

### False Positives (Incorrect Crowd Alerts)
**Parameter adjustments to reduce false crowd alarms**

- **Increase conf**: Raise to 0.4-0.5 for stricter person detection
- **Extend t_min**: Increase to 4-6 frames for crowd verification
- **Adjust alert_interval**: Extend to 600-900 seconds
- **Tune sigma_h**: Increase to 0.4-0.5 for stricter tracking

### Missing Crowds (False Negatives)
**Parameter adjustments to catch more gathering events**

- **Decrease conf**: Lower to 0.15-0.25 for sensitivity
- **Reduce t_min**: Decrease to 1-2 frames for quick detection
- **Increase max_dets**: Raise to 800-1000 for more detections
- **Lower sigma_l**: Reduce to 0.05-0.1 for weak detection inclusion

### Performance Optimization Issues
**Parameter adjustments for resource constraints**

- **Reduce resolution**: Lower width/height to 640x480
- **Enable use_fp16**: Activate for performance improvement
- **Decrease batch_size**: Reduce to 1-2 for memory efficiency
- **Lower fps**: Reduce to 0.5-1 for processing capability

This comprehensive crowd gathering detection parameter guide ensures optimal crowd management performance while balancing detection accuracy with system efficiency across diverse event and public space environments.
