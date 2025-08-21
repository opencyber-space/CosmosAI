# Complete Computer Vision Pipeline Architectures

This document provides complete pipeline compositions for common computer vision use cases, showing the full architecture from input to output with specific component connections.

## Loitering Detection Pipeline Architecture

### Standard Loitering Detection Pipeline
```
Camera Input → Object Detection → Zone Filtering → Tracking → Loitering Use Case Logic → Alert System
```

### Complete Component Flow
```json
{
  "pipeline_name": "loitering_detection_complete",
  "architecture": [
    {
      "stage": 1,
      "component_type": "source",
      "component_name": "camera_input",
      "description": "RTSP camera stream input",
      "outputs": ["video_frames"],
      "parameters": {
        "fps": "5/1",
        "resolution": "1024x1024",
        "format": "BGR"
      }
    },
    {
      "stage": 2,
      "component_type": "detection",
      "component_name": "object_detection",
      "model": "yolov8_person_detector",
      "description": "Person detection using YOLO",
      "inputs": ["video_frames"],
      "outputs": ["person_detections"],
      "parameters": {
        "conf": 0.4,
        "width": 1024,
        "height": 1024,
        "max_dets": 100,
        "classes": ["person"]
      }
    },
    {
      "stage": 3,
      "component_type": "policy",
      "component_name": "zone_filtering",
      "description": "Filter detections within loitering zones",
      "inputs": ["person_detections"],
      "outputs": ["zone_filtered_detections"],
      "parameters": {
        "zones": ["ZoneLoitering"],
        "filter_type": "inside_zone",
        "classes": ["person"]
      }
    },
    {
      "stage": 4,
      "component_type": "tracking",
      "component_name": "multi_object_tracking",
      "model": "bytetrack_or_viou",
      "description": "Track persons across frames",
      "inputs": ["zone_filtered_detections"],
      "outputs": ["tracked_persons"],
      "parameters": {
        "ttl": 8,
        "sigma_iou": 0.3,
        "sigma_h": 0.3,
        "sigma_l": 0.1,
        "t_min": 3
      }
    },
    {
      "stage": 5,
      "component_type": "usecase",
      "component_name": "loitering_detection",
      "description": "Detect loitering behavior based on dwell time",
      "inputs": ["tracked_persons"],
      "outputs": ["loitering_alerts"],
      "parameters": {
        "loiteringThresholdSeconds": 120,
        "alert_interval": 600,
        "severity": "high"
      }
    },
    {
      "stage": 6,
      "component_type": "output",
      "component_name": "alert_system",
      "description": "Send alerts to security system",
      "inputs": ["loitering_alerts"],
      "outputs": ["notifications"],
      "parameters": {
        "alert_url": "http://security-system/alerts",
        "storage": "mongodb",
        "real_time": true
      }
    }
  ]
}
```

## ATM Surveillance Loitering Pipeline

### Specialized ATM Configuration
```json
{
  "pipeline_name": "atm_loitering_surveillance",
  "use_case": "ATM security monitoring",
  "architecture": [
    {
      "stage": 1,
      "component": "camera_input",
      "parameters": {
        "fps": "3/1",
        "resolution": "1024x1024",
        "night_vision": true
      }
    },
    {
      "stage": 2, 
      "component": "person_detection",
      "model": "yolov8m_person",
      "parameters": {
        "conf": 0.6,
        "width": 1024,
        "height": 1024,
        "max_dets": 50
      }
    },
    {
      "stage": 3,
      "component": "atm_zone_filter",
      "parameters": {
        "zones": ["ATMPerimeter", "QueueArea"],
        "buffer_distance": 2.0
      }
    },
    {
      "stage": 4,
      "component": "person_tracking",
      "parameters": {
        "ttl": 10,
        "sigma_iou": 0.4,
        "t_min": 5
      }
    },
    {
      "stage": 5,
      "component": "loitering_detection",
      "parameters": {
        "loiteringThresholdSeconds": 180,
        "alert_interval": 300,
        "severity": "high"
      }
    }
  ]
}
```

## Intrusion Detection Pipeline Architecture

### Complete Intrusion Pipeline
```
Camera Input → Object Detection → Zone Filtering → Tracking → Line Crossing Detection → Intrusion Alerts
```

### Component Configuration
```json
{
  "pipeline_name": "intrusion_detection_complete",
  "architecture": [
    {
      "stage": 1,
      "component": "camera_input",
      "parameters": {
        "fps": "5/1",
        "resolution": "1920x1080"
      }
    },
    {
      "stage": 2,
      "component": "object_detection",
      "model": "yolov8_person_detector",
      "parameters": {
        "conf": 0.5,
        "width": 1024,
        "height": 1024
      }
    },
    {
      "stage": 3,
      "component": "zone_filtering",
      "parameters": {
        "zones": ["ZoneIntrusion1", "ZoneIntrusion2"],
        "filter_type": "inside_zone"
      }
    },
    {
      "stage": 4,
      "component": "tracking",
      "parameters": {
        "ttl": 6,
        "sigma_iou": 0.3
      }
    },
    {
      "stage": 5,
      "component": "line_crossing_detection",
      "parameters": {
        "lines": ["IntrustionLine1", "IntrusionLine2"],
        "direction": "bidirectional",
        "alert_interval": 60,
        "severity": "medium"
      }
    }
  ]
}
```

## Multi-Camera Tracking Pipeline

### Cross-Camera Person Tracking
```
Multiple Cameras → Person Detection → Individual Tracking → Cross-Camera Association → Global Tracking
```

### Complete Architecture
```json
{
  "pipeline_name": "multi_camera_tracking",
  "architecture": [
    {
      "stage": 1,
      "component": "multi_camera_input",
      "parameters": {
        "camera_count": 4,
        "fps": "5/1",
        "sync_mode": true
      }
    },
    {
      "stage": 2,
      "component": "person_detection",
      "model": "yolov8_person",
      "parameters": {
        "conf": 0.4,
        "per_camera": true
      }
    },
    {
      "stage": 3,
      "component": "single_camera_tracking",
      "parameters": {
        "tracker_per_camera": true,
        "ttl": 8
      }
    },
    {
      "stage": 4,
      "component": "person_re_identification",
      "model": "person_reid_model",
      "parameters": {
        "feature_extraction": true,
        "similarity_threshold": 0.7
      }
    },
    {
      "stage": 5,
      "component": "cross_camera_association",
      "parameters": {
        "temporal_window": 30,
        "spatial_constraints": true
      }
    },
    {
      "stage": 6,
      "component": "global_tracking",
      "parameters": {
        "alert_interval": 600,
        "severity": "medium"
      }
    }
  ]
}
```

## Weapon Detection Pipeline

### Security Threat Detection
```
Camera Input → Multi-Object Detection → Person-Weapon Association → Threat Analysis → Critical Alerts
```

### Complete Configuration
```json
{
  "pipeline_name": "weapon_detection_security",
  "architecture": [
    {
      "stage": 1,
      "component": "camera_input",
      "parameters": {
        "fps": "5/1",
        "high_resolution": true
      }
    },
    {
      "stage": 2,
      "component": "multi_object_detection",
      "models": ["person_detector", "weapon_detector"],
      "parameters": {
        "person_conf": 0.4,
        "weapon_conf": 0.7,
        "classes": ["person", "gun", "knife", "rifle"]
      }
    },
    {
      "stage": 3,
      "component": "object_association",
      "parameters": {
        "association_distance": 100,
        "confidence_threshold": 0.5
      }
    },
    {
      "stage": 4,
      "component": "tracking",
      "parameters": {
        "ttl": 10,
        "strict_matching": true
      }
    },
    {
      "stage": 5,
      "component": "weapon_detection_logic",
      "parameters": {
        "alert_interval": 300,
        "severity": "high",
        "immediate_alert": true
      }
    }
  ]
}
```

## Pipeline Composition Guidelines

### Standard Component Flow
1. **Input Stage**: Camera/video source with stream parameters
2. **Detection Stage**: Object detection with confidence and resolution settings
3. **Filtering Stage**: Zone/policy filtering to focus on relevant areas
4. **Tracking Stage**: Multi-object tracking to maintain object identity
5. **Use Case Logic**: Business logic for specific use case (loitering, intrusion, etc.)
6. **Output Stage**: Alert generation and notification system

### Parameter Inheritance
- **Resolution flows through**: Input resolution affects detection and tracking
- **Confidence cascades**: Detection confidence affects tracking quality
- **Frame rate impacts**: Higher FPS improves tracking but increases compute cost
- **Zone definitions**: Must be consistent across filtering and use case stages

### Hardware Scaling
- **High-end GPU**: Higher resolution, more detections, complex models
- **Mid-range GPU**: Balanced parameters for performance
- **Edge devices**: Reduced resolution, simplified models, optimized parameters

### Environmental Adaptation
- **Low light**: Lower confidence thresholds, longer tracking TTL
- **High traffic**: Higher detection limits, stricter filtering
- **Outdoor**: Weather-resistant parameters, wider zones
- **Indoor**: Precise zones, higher accuracy requirements

This architecture guide ensures complete pipeline designs that can be directly implemented in AIOS systems.
