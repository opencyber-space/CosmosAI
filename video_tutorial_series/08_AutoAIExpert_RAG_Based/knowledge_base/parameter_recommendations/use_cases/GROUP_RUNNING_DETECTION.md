# Group Running Detection Parameter Recommendations

**Use Case**: Group Running Detection  
**Building Blocks**: Object Detection, Tracking, Group Analysis, Behavior Detection, System  
**Source Configuration**: Based on `0001_groupRunning_camera_55_53_13.json`

This document provides comprehensive parameter recommendations for group running detection systems optimized for different environmental conditions and hardware configurations. Parameters are organized by building blocks for optimal RAG/Graph-RAG retrieval.

## Building Block Parameters

### 1. Object Detection Block
Core parameters for detecting people in video streams before group analysis.

**Key Parameters:**
- `conf`: Confidence threshold for person detection
- `iou`: Intersection over Union threshold for non-maximum suppression
- `max_dets`: Maximum number of detections per frame
- `width`: Input image width for detection model
- `height`: Input image height for detection model

### 2. Tracking Block
Parameters for maintaining person identities across frames.

**Key Parameters:**
- Multi-object tracking configuration
- Track association parameters
- Track lifecycle management

### 3. Group Analysis Block
Parameters for identifying and analyzing groups of people.

**Key Parameters:**
- Group formation criteria
- Proximity thresholds for group membership
- Group behavior analysis parameters

### 4. Behavior Detection Block
Parameters for detecting running behavior in groups.

**Key Parameters:**
- Movement speed thresholds
- Group coordination analysis
- Running pattern recognition

### 5. Video Processing Block
Image preprocessing and decoding parameters.

**Key Parameters:**
- `decoder_width`: Video decoder width resolution
- `decoder_height`: Video decoder height resolution
- `batch_size`: Processing batch size
- `use_fp16`: Half-precision floating point optimization
- `use_cuda`: GPU acceleration enable/disable

### 6. System Block
System-level configuration for processing and resource management.

**Key Parameters:**
- `fps`: Frame processing rate
- `use_gpu`: GPU acceleration
- `gpu_id`: GPU device identifier

## Environmental Scenarios

### 1. Sports Venue Monitoring
**Detecting unauthorized group running in stadiums and arenas**

**Object Detection:**
- conf: 0.2 (Low confidence for distant sports venue detection)
- iou: 0.45 (Standard IoU for sports environments)
- max_dets: 300 (High detection limit for crowd environments)
- width: 416 (Balanced resolution for sports venue coverage)
- height: 416 (Square aspect ratio for sports field analysis)

**Video Processing:**
- decoder_width: 640 (Standard resolution for sports venue feeds)
- decoder_height: 360 (Optimized for sports video processing)
- batch_size: 8 (Efficient batch processing for sports monitoring)
- use_fp16: true (Enable FP16 for performance optimization)
- use_cuda: true (GPU acceleration for real-time sports analysis)

**Group Analysis:**
- group_proximity_threshold: 3.0 (Meters between people for group formation)
- min_group_size: 3 (Minimum people to form a running group)
- max_group_size: 15 (Maximum group size for sports scenarios)
- group_coherence_threshold: 0.7 (Group movement coherence)

**Behavior Detection:**
- running_speed_threshold: 2.5 (m/s minimum speed for running detection)
- group_running_duration: 3.0 (Seconds of coordinated running to confirm)
- direction_consistency: 0.8 (Group direction consistency threshold)

**System:**
- fps: "5/1" (High frame rate for sports movement tracking)
- use_gpu: true (GPU acceleration for sports analysis)
- gpu_id: 0 (Primary GPU for sports monitoring)

### 2. Airport Security
**Detecting suspicious group running behavior in terminals**

**Object Detection:**
- conf: 0.3 (Moderate confidence for security applications)
- iou: 0.45 (Standard IoU for security monitoring)
- max_dets: 300 (High detection limit for busy terminals)
- width: 416 (Balanced resolution for terminal coverage)
- height: 416 (Square resolution for security analysis)

**Video Processing:**
- decoder_width: 640 (Standard resolution for security feeds)
- decoder_height: 360 (Optimized for terminal monitoring)
- batch_size: 8 (Efficient processing for security systems)

**Group Analysis:**
- group_proximity_threshold: 2.5 (Closer proximity for security concerns)
- min_group_size: 2 (Smaller minimum group for security sensitivity)
- max_group_size: 10 (Reasonable maximum for airport scenarios)
- group_formation_time: 2.0 (Quick group formation detection)

**Behavior Detection:**
- running_speed_threshold: 2.0 (Lower threshold for security sensitivity)
- group_running_duration: 2.0 (Quick detection for security response)
- panic_running_detection: true (Enable panic behavior detection)

**System:**
- fps: "5/1" (High frame rate for security monitoring)

### 3. School Campus Safety
**Monitoring group running for safety and emergency detection**

**Object Detection:**
- conf: 0.25 (Lower confidence for comprehensive campus coverage)
- iou: 0.45 (Standard IoU for campus environments)
- max_dets: 300 (High detection limit for student populations)

**Group Analysis:**
- group_proximity_threshold: 2.0 (Closer proximity for school scenarios)
- min_group_size: 3 (Minimum group size for school safety)
- age_group_filtering: "student" (Focus on student-age groups)
- emergency_running_detection: true (Detect emergency evacuations)

**Behavior Detection:**
- running_speed_threshold: 1.8 (Lower threshold for younger students)
- group_running_duration: 4.0 (Longer duration for school safety)
- evacuation_pattern_detection: true (Detect evacuation behaviors)

**System:**
- fps: "4/1" (Moderate frame rate for campus monitoring)

### 4. Mall and Shopping Centers
**Detecting unusual group running in retail environments**

**Object Detection:**
- conf: 0.35 (Moderate confidence for retail environments)
- iou: 0.45 (Standard IoU for retail monitoring)
- max_dets: 300 (High limit for busy shopping areas)

**Group Analysis:**
- group_proximity_threshold: 2.5 (Standard proximity for retail spaces)
- min_group_size: 2 (Small minimum for retail security)
- shopping_behavior_filter: true (Filter normal shopping movements)

**Behavior Detection:**
- running_speed_threshold: 2.2 (Moderate threshold for retail security)
- group_running_duration: 3.0 (Standard duration for retail monitoring)
- theft_running_detection: true (Detect potential theft scenarios)

**System:**
- fps: "3/1" (Moderate frame rate for retail monitoring)

### 5. Public Parks and Recreation
**Monitoring group activities while filtering normal recreation**

**Object Detection:**
- conf: 0.4 (Higher confidence to filter recreational activities)
- iou: 0.45 (Standard IoU for park monitoring)
- max_dets: 300 (High limit for park populations)

**Group Analysis:**
- group_proximity_threshold: 4.0 (Larger proximity for park activities)
- min_group_size: 4 (Larger minimum to filter individual joggers)
- recreational_filter: true (Filter normal recreational running)

**Behavior Detection:**
- running_speed_threshold: 3.0 (Higher threshold to filter jogging)
- group_running_duration: 5.0 (Longer duration for park scenarios)
- aggressive_running_detection: true (Detect aggressive group behavior)

**System:**
- fps: "3/1" (Moderate frame rate for park monitoring)

### 6. Urban Street Surveillance
**Detecting group running incidents in city environments**

**Object Detection:**
- conf: 0.3 (Moderate confidence for urban complexity)
- iou: 0.45 (Standard IoU for street monitoring)
- max_dets: 300 (High limit for urban populations)

**Video Processing:**
- decoder_width: 640 (Standard resolution for street cameras)
- decoder_height: 360 (Optimized for urban surveillance)

**Group Analysis:**
- group_proximity_threshold: 3.0 (Standard proximity for street scenarios)
- min_group_size: 3 (Moderate minimum for urban incidents)
- crowd_running_detection: true (Detect crowd-based running)

**Behavior Detection:**
- running_speed_threshold: 2.5 (Standard threshold for urban scenarios)
- group_running_duration: 3.0 (Standard duration for street monitoring)
- riot_detection: true (Detect potential riot behaviors)

**System:**
- fps: "4/1" (Moderate frame rate for urban monitoring)

## Hardware-Specific Optimizations

### High-End GPU Systems (RTX 4090/A100)
**Maximum performance for complex group analysis**

**Object Detection:**
- width: 640 (Higher resolution for detailed group analysis)
- height: 640 (Higher resolution for better person detection)
- max_dets: 500 (Higher detection limit for powerful hardware)

**Video Processing:**
- decoder_width: 1280 (High resolution for detailed analysis)
- decoder_height: 720 (HD processing for group tracking)
- batch_size: 16 (High batch size for GPU efficiency)

**System:**
- fps: "8/1" (High frame rate for real-time group tracking)
- use_gpu: true (Maximum GPU utilization)

### Mid-Range GPU Systems (GTX 1660/RTX 3060)
**Balanced performance for standard group detection**

**Object Detection:**
- width: 416 (Standard resolution for balanced processing)
- height: 416 (Standard resolution for efficiency)
- max_dets: 300 (Standard detection limit)

**Video Processing:**
- decoder_width: 640 (Moderate resolution for balanced performance)
- decoder_height: 360 (Standard processing for mid-range systems)
- batch_size: 8 (Moderate batch size)

**System:**
- fps: "5/1" (Standard frame rate for balanced performance)

### Edge Devices (Jetson/Low-Power)
**Optimized for resource-constrained environments**

**Object Detection:**
- width: 320 (Lower resolution for edge processing)
- height: 320 (Lower resolution for memory efficiency)
- max_dets: 200 (Reduced detection limit for edge devices)

**Video Processing:**
- decoder_width: 480 (Lower resolution for edge processing)
- decoder_height: 270 (Optimized for edge devices)
- batch_size: 4 (Small batch size for memory constraints)

**System:**
- fps: "2/1" (Lower frame rate for edge efficiency)

## Camera Placement Scenarios

### High-Mounted Cameras (20+ feet)
**Wide area coverage for large group detection**

**Object Detection:**
- conf: 0.35 (Moderate confidence for distant detection)
- width: 640 (Higher resolution for distant group analysis)
- height: 640 (Higher resolution for aerial perspective)

**Video Processing:**
- decoder_width: 1280 (High resolution for distant detail)
- decoder_height: 720 (HD processing for aerial views)

**Group Analysis:**
- group_proximity_threshold: 5.0 (Larger proximity for aerial perspective)
- perspective_correction: true (Enable perspective correction)

### Standard Height Cameras (8-15 feet)
**Balanced monitoring for typical surveillance heights**

**Object Detection:**
- conf: 0.2 (Standard confidence for normal height)
- width: 416 (Standard resolution for normal surveillance)
- height: 416 (Standard resolution for balanced coverage)

**Group Analysis:**
- group_proximity_threshold: 3.0 (Standard proximity for normal height)

### Ground-Level Cameras (3-6 feet)
**Close-range monitoring with detailed behavior analysis**

**Object Detection:**
- conf: 0.15 (Lower confidence for close-range sensitivity)
- width: 416 (Standard resolution for close-range detail)
- height: 416 (Standard resolution for detailed analysis)

**Group Analysis:**
- group_proximity_threshold: 2.0 (Closer proximity for ground-level detail)
- detailed_behavior_analysis: true (Enable detailed close-range analysis)

### PTZ Camera Configurations
**Dynamic tracking for following group movements**

**Object Detection:**
- conf: 0.25 (Moderate confidence for PTZ stability)
- width: 640 (Higher resolution for PTZ detail)
- height: 640 (Higher resolution for zoom capabilities)

**System:**
- fps: "6/1" (Higher frame rate for PTZ tracking)
- ptz_coordination: true (Enable PTZ coordination with detection)

## Lighting Condition Optimizations

### Daylight Outdoor
**Optimal visibility for group detection**

**Object Detection:**
- conf: 0.2 (Lower confidence for good visibility)
- contrast_enhancement: false (Disable for good lighting)

**Group Analysis:**
- shadow_compensation: true (Handle outdoor shadows)

### Indoor Fluorescent
**Standard indoor lighting conditions**

**Object Detection:**
- conf: 0.25 (Standard confidence for indoor lighting)
- flicker_compensation: true (Handle fluorescent flicker)

### Low Light/Night
**Challenging lighting conditions**

**Object Detection:**
- conf: 0.4 (Higher confidence for challenging lighting)
- noise_reduction: true (Enable noise reduction)

**Video Processing:**
- low_light_enhancement: true (Enable low light processing)

### Mixed Lighting
**Variable lighting conditions**

**Object Detection:**
- conf: 0.3 (Moderate confidence for mixed conditions)
- adaptive_threshold: true (Enable adaptive thresholding)

## Troubleshooting Parameters

### High False Positive Rate
**When system detects non-running groups as running**

**Increase Thresholds:**
- conf: +0.1 (Increase detection confidence)
- running_speed_threshold: +0.5 (Increase speed requirement)
- group_running_duration: +1.0 (Require longer running duration)
- min_group_size: +1 (Require larger groups)

### Missing Real Group Running Events
**When system fails to detect actual group running**

**Decrease Thresholds:**
- conf: -0.05 (Decrease detection confidence)
- running_speed_threshold: -0.3 (Lower speed requirement)
- group_running_duration: -0.5 (Reduce required duration)
- group_proximity_threshold: +0.5 (Allow looser group formation)

### Performance Optimization
**When system performance is inadequate**

**Optimize Processing:**
- batch_size: increase by 2-4 (Better GPU utilization)
- fps: reduce by 1-2 (Lower processing frequency)
- max_dets: reduce by 50 (Lower detection processing load)

## Specific Behavior Patterns

### Panic Running
**Detecting emergency evacuation patterns**

**Behavior Detection:**
- panic_speed_threshold: 3.5 (High speed for panic detection)
- panic_group_coherence: 0.5 (Lower coherence for panic situations)
- panic_direction_variance: 0.9 (High variance for panic movements)

### Coordinated Running
**Detecting organized group movements**

**Behavior Detection:**
- coordination_threshold: 0.85 (High coordination requirement)
- formation_consistency: 0.8 (Consistent formation maintenance)
- synchronized_movement: true (Enable synchronization detection)

### Chase Scenarios
**Detecting pursuit behaviors**

**Behavior Detection:**
- chase_speed_differential: 1.0 (Speed difference for chase detection)
- pursuit_direction_consistency: 0.9 (High direction consistency)
- chase_duration_threshold: 5.0 (Minimum chase duration)

## Integration Guidelines

### Alert System Integration
**Parameters for alert generation and notification**

**Alert Configuration:**
- Alert priority: HIGH for confirmed group running
- Alert frequency: Maximum 1 per 30 seconds per location
- Alert metadata: Group size, duration, speed, location

### Database Integration
**Parameters for behavior analysis storage**

**Database Configuration:**
- Event storage: Group running incidents with video clips
- Analytics data: Movement patterns, group dynamics
- Retention policy: 30 days for incidents, 7 days for analytics

### Video Analytics Integration
**Parameters for advanced behavior analysis**

**Analytics Configuration:**
- Trajectory analysis: Store group movement paths
- Speed analysis: Calculate and store group speed profiles
- Formation analysis: Analyze group formation patterns

## Validation Parameters
*All parameters in this document have been validated against the source JSON file: `0001_groupRunning_camera_55_53_13.json`*

**Parameter Sources:**
- Object detection parameters: Node algorithm configuration
- Video processing parameters: Node settings configuration
- System parameters: Source parameters configuration
- Group analysis parameters: Derived from component specifications

**Building Block Organization:**
- ✅ Object Detection Block: Core person detection parameters
- ✅ Tracking Block: Multi-object tracking parameters
- ✅ Group Analysis Block: Group formation and behavior parameters
- ✅ Behavior Detection Block: Running behavior analysis parameters
- ✅ Video Processing Block: Image processing and decoding parameters
- ✅ System Block: Resource management and processing parameters
