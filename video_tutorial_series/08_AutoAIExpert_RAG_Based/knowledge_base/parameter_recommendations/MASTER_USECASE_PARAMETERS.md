# Master Use Case Parameters Configuration

## Overview
This document defines the comprehensive parameter configuration matrix for all computer vision use cases across different environmental conditions and requirements. Each use case can be configured using parameter sets defined in this master document.

## Parameter Configuration Matrix

### 1. DETECTION MODELS

#### 1.1 Object Detection Parameters
```json
{
  "standard": {
    "conf": 0.25,
    "iou": 0.45,
    "max_dets": 300,
    "model_resolution": {"width": 896, "height": 896},
    "decoder": {"width": 896, "height": 608},
    "use_fp16": true,
    "batch_size": 8
  },
  "high_accuracy": {
    "conf": 0.35,
    "iou": 0.5,
    "max_dets": 500,
    "model_resolution": {"width": 1024, "height": 1024},
    "decoder": {"width": 1024, "height": 704},
    "use_fp16": false,
    "batch_size": 4
  },
  "low_light": {
    "conf": 0.15,
    "iou": 0.35,
    "max_dets": 500,
    "model_resolution": {"width": 1024, "height": 1024},
    "decoder": {"width": 1024, "height": 704},
    "use_fp16": false,
    "batch_size": 4
  },
  "far_detection": {
    "conf": 0.2,
    "iou": 0.4,
    "max_dets": 600,
    "model_resolution": {"width": 1280, "height": 1280},
    "decoder": {"width": 1280, "height": 960},
    "use_fp16": false,
    "batch_size": 2
  },
  "large_viewpoint": {
    "conf": 0.3,
    "iou": 0.45,
    "max_dets": 800,
    "model_resolution": {"width": 1024, "height": 1024},
    "decoder": {"width": 1920, "height": 1080},
    "use_fp16": true,
    "batch_size": 6
  },
  "high_throughput": {
    "conf": 0.3,
    "iou": 0.5,
    "max_dets": 200,
    "model_resolution": {"width": 640, "height": 640},
    "decoder": {"width": 640, "height": 360},
    "use_fp16": true,
    "batch_size": 16
  }
}
```

#### 1.2 Face Detection Parameters
```json
{
  "standard": {
    "conf": 0.6,
    "pixel_hthresh": 50,
    "pixel_wthresh": 50,
    "nmsThresh": 0.45,
    "MODEL": "10G_KPS"
  },
  "high_accuracy": {
    "conf": 0.8,
    "pixel_hthresh": 80,
    "pixel_wthresh": 80,
    "nmsThresh": 0.5,
    "MODEL": "10G_KPS"
  },
  "low_light": {
    "conf": 0.4,
    "pixel_hthresh": 40,
    "pixel_wthresh": 40,
    "nmsThresh": 0.35,
    "MODEL": "10G_KPS"
  },
  "far_detection": {
    "conf": 0.5,
    "pixel_hthresh": 30,
    "pixel_wthresh": 30,
    "nmsThresh": 0.4,
    "MODEL": "10G_KPS"
  },
  "large_viewpoint": {
    "conf": 0.65,
    "pixel_hthresh": 60,
    "pixel_wthresh": 60,
    "nmsThresh": 0.45,
    "MODEL": "10G_KPS"
  }
}
```

#### 1.3 Specialized Detection Models
```json
{
  "fire_detection": {
    "standard": {"conf": 0.7, "frameCountThresh": 5},
    "high_accuracy": {"conf": 0.8, "frameCountThresh": 8},
    "low_light": {"conf": 0.5, "frameCountThresh": 8},
    "far_detection": {"conf": 0.6, "frameCountThresh": 10}
  },
  "weapon_detection": {
    "standard": {"conf": 0.7, "frameCountThresh": 5},
    "high_accuracy": {"conf": 0.85, "frameCountThresh": 8},
    "low_light": {"conf": 0.5, "frameCountThresh": 8},
    "far_detection": {"conf": 0.6, "frameCountThresh": 12}
  },
  "fall_detection": {
    "standard": {"fallConfidence": 0.7, "personConfidence": 0.5, "fall_time": 15},
    "high_accuracy": {"fallConfidence": 0.85, "personConfidence": 0.7, "fall_time": 20},
    "low_light": {"fallConfidence": 0.6, "personConfidence": 0.4, "fall_time": 30},
    "sensitive": {"fallConfidence": 0.6, "personConfidence": 0.4, "fall_time": 10}
  }
}
```

### 2. TRACKING PARAMETERS

#### 2.1 General Tracking
```json
{
  "standard": {
    "ttl": 4,
    "iou": 0.45,
    "sigma_iou": 0.3,
    "sigma_h": 0.3,
    "sigma_l": 0.1,
    "t_min": 2,
    "conf_thresh": 0.15
  },
  "high_accuracy": {
    "ttl": 6,
    "iou": 0.5,
    "sigma_iou": 0.25,
    "sigma_h": 0.25,
    "sigma_l": 0.05,
    "t_min": 3,
    "conf_thresh": 0.2
  },
  "low_light": {
    "ttl": 6,
    "iou": 0.3,
    "sigma_iou": 0.4,
    "sigma_h": 0.4,
    "sigma_l": 0.2,
    "t_min": 3,
    "conf_thresh": 0.1
  },
  "fast_moving": {
    "ttl": 8,
    "iou": 0.25,
    "sigma_iou": 0.4,
    "sigma_h": 0.4,
    "sigma_l": 0.15,
    "t_min": 1,
    "conf_thresh": 0.1
  },
  "stationary": {
    "ttl": 2,
    "iou": 0.7,
    "sigma_iou": 0.2,
    "sigma_h": 0.2,
    "sigma_l": 0.05,
    "t_min": 1,
    "conf_thresh": 0.2
  }
}
```

#### 2.2 FastMOT Tracking
```json
{
  "standard": {
    "max_age": 9,
    "age_penalty": 2,
    "motion_weight": 0.4,
    "max_assoc_cost": 0.8,
    "max_reid_cost": 0.6,
    "conf_thresh": 0.15
  },
  "high_accuracy": {
    "max_age": 12,
    "age_penalty": 1,
    "motion_weight": 0.3,
    "max_assoc_cost": 0.7,
    "max_reid_cost": 0.5,
    "conf_thresh": 0.2
  },
  "low_light": {
    "max_age": 12,
    "age_penalty": 1,
    "motion_weight": 0.6,
    "max_assoc_cost": 0.9,
    "max_reid_cost": 0.8,
    "conf_thresh": 0.08
  },
  "fast_moving": {
    "max_age": 15,
    "age_penalty": 1,
    "motion_weight": 0.7,
    "max_assoc_cost": 0.9,
    "max_reid_cost": 0.7,
    "conf_thresh": 0.1
  }
}
```

### 3. USE CASE SPECIFIC PARAMETERS

#### 3.1 Loitering Detection
```json
{
  "standard": {
    "loiteringThresholdSeconds": 20,
    "alert_interval": 40,
    "fps": "5/1"
  },
  "high_accuracy": {
    "loiteringThresholdSeconds": 30,
    "alert_interval": 60,
    "fps": "5/1"
  },
  "low_light": {
    "loiteringThresholdSeconds": 30,
    "alert_interval": 60,
    "fps": "2/1"
  },
  "large_viewpoint": {
    "loiteringThresholdSeconds": 40,
    "alert_interval": 80,
    "fps": "3/1"
  },
  "sensitive": {
    "loiteringThresholdSeconds": 15,
    "alert_interval": 30,
    "fps": "8/1"
  }
}
```

#### 3.2 Crowd Detection
```json
{
  "standard": {
    "countThreshold": 10,
    "ViolationFrameCount": 15,
    "alert_interval": 150,
    "fps": "1/4"
  },
  "high_accuracy": {
    "countThreshold": 8,
    "ViolationFrameCount": 20,
    "alert_interval": 120,
    "fps": "1/3"
  },
  "sensitive": {
    "countThreshold": 15,
    "ViolationFrameCount": 10,
    "alert_interval": 60,
    "fps": "1/2"
  },
  "large_viewpoint": {
    "countThreshold": 20,
    "ViolationFrameCount": 20,
    "alert_interval": 180,
    "fps": "1/5"
  }
}
```

#### 3.3 Abandoned Object Detection
```json
{
  "standard": {
    "timeThreshold": 120,
    "distance_ratio": 1.5,
    "alert_interval": 30,
    "fps": "5/1"
  },
  "high_accuracy": {
    "timeThreshold": 180,
    "distance_ratio": 1.0,
    "alert_interval": 60,
    "fps": "3/1"
  },
  "low_light": {
    "timeThreshold": 180,
    "distance_ratio": 2.5,
    "alert_interval": 45,
    "fps": "2/1"
  },
  "sensitive": {
    "timeThreshold": 60,
    "distance_ratio": 2.0,
    "alert_interval": 20,
    "fps": "8/1"
  }
}
```

#### 3.4 Face Recognition System
```json
{
  "standard": {
    "match_score": 0.95,
    "minimum_reco_count": 15,
    "alert_interval": 600,
    "logger_interval": 60
  },
  "high_accuracy": {
    "match_score": 0.98,
    "minimum_reco_count": 20,
    "alert_interval": 300,
    "logger_interval": 30
  },
  "low_light": {
    "match_score": 0.90,
    "minimum_reco_count": 20,
    "alert_interval": 900,
    "logger_interval": 90
  },
  "sensitive": {
    "match_score": 0.85,
    "minimum_reco_count": 10,
    "alert_interval": 300,
    "logger_interval": 30
  }
}
```

### 4. FRAME PROCESSING PARAMETERS

#### 4.1 FPS Configurations
```json
{
  "real_time": "30/1",
  "high_performance": "15/1",
  "standard": "5/1",
  "balanced": "3/1",
  "conservative": "2/1",
  "low_power": "1/1",
  "periodic": "1/2",
  "slow_monitoring": "1/4",
  "very_slow": "1/5"
}
```

#### 4.2 Quality Settings
```json
{
  "standard": {
    "frame_quality": 90,
    "color_format": "BGR",
    "interpolationType": "INTERP_GAUSSIAN"
  },
  "high_quality": {
    "frame_quality": 95,
    "color_format": "BGR",
    "interpolationType": "INTERP_CUBIC"
  },
  "low_bandwidth": {
    "frame_quality": 75,
    "color_format": "BGR",
    "interpolationType": "INTERP_LINEAR"
  }
}
```

### 5. POLICY CONFIGURATIONS

#### 5.1 Zone Filtering
```json
{
  "standard": {
    "pivotPoint": "midPoint",
    "zone_margin": 0
  },
  "strict": {
    "pivotPoint": "centerPoint",
    "zone_margin": -5
  },
  "lenient": {
    "pivotPoint": "bottomPoint",
    "zone_margin": 10
  }
}
```

#### 5.2 Scale Filtering
```json
{
  "standard": {
    "frame_h_obj_h": {"value": 21.6, "op": "<"},
    "frame_w_obj_w": {"value": 38.4, "op": "<"}
  },
  "strict": {
    "frame_h_obj_h": {"value": 15.0, "op": "<"},
    "frame_w_obj_w": {"value": 25.0, "op": "<"}
  },
  "lenient": {
    "frame_h_obj_h": {"value": 30.0, "op": "<"},
    "frame_w_obj_w": {"value": 50.0, "op": "<"}
  }
}
```

### 6. ALERT CONFIGURATIONS

#### 6.1 Alert Intervals (seconds)
```json
{
  "immediate": 5,
  "urgent": 15,
  "standard": 30,
  "moderate": 60,
  "relaxed": 300,
  "periodic": 600,
  "hourly": 3600
}
```

#### 6.2 Severity Levels
```json
{
  "critical": {
    "severity": "critical",
    "priority": 1,
    "escalation": true
  },
  "high": {
    "severity": "high",
    "priority": 2,
    "escalation": true
  },
  "medium": {
    "severity": "medium",
    "priority": 3,
    "escalation": false
  },
  "low": {
    "severity": "low",
    "priority": 4,
    "escalation": false
  }
}
```

### 7. HARDWARE OPTIMIZATION

#### 7.1 GPU Configurations
```json
{
  "high_end": {
    "batch_size": 16,
    "use_fp16": true,
    "enable_batching": true,
    "parallel_streams": 4
  },
  "mid_range": {
    "batch_size": 8,
    "use_fp16": true,
    "enable_batching": true,
    "parallel_streams": 2
  },
  "low_end": {
    "batch_size": 4,
    "use_fp16": false,
    "enable_batching": true,
    "parallel_streams": 1
  },
  "edge_device": {
    "batch_size": 1,
    "use_fp16": true,
    "enable_batching": false,
    "parallel_streams": 1
  }
}
```

### 8. ENVIRONMENTAL ADAPTATIONS

#### 8.1 Lighting Conditions
```json
{
  "bright_daylight": {
    "exposure_compensation": 0,
    "contrast_boost": 1.0,
    "brightness_adjustment": 0
  },
  "normal_light": {
    "exposure_compensation": 0,
    "contrast_boost": 1.1,
    "brightness_adjustment": 0
  },
  "low_light": {
    "exposure_compensation": 1,
    "contrast_boost": 1.3,
    "brightness_adjustment": 15
  },
  "night_vision": {
    "exposure_compensation": 2,
    "contrast_boost": 1.5,
    "brightness_adjustment": 25
  }
}
```

#### 8.2 Weather Conditions
```json
{
  "clear": {
    "visibility_factor": 1.0,
    "detection_multiplier": 1.0
  },
  "light_rain": {
    "visibility_factor": 0.9,
    "detection_multiplier": 1.1
  },
  "heavy_rain": {
    "visibility_factor": 0.7,
    "detection_multiplier": 1.3
  },
  "fog": {
    "visibility_factor": 0.5,
    "detection_multiplier": 1.5
  },
  "snow": {
    "visibility_factor": 0.6,
    "detection_multiplier": 1.4
  }
}
```

### 9. PERFORMANCE PROFILES

#### 9.1 Accuracy vs Speed Trade-offs
```json
{
  "maximum_accuracy": {
    "model_size": "largest",
    "resolution": "highest",
    "fps": "lowest",
    "confidence_threshold": "highest"
  },
  "balanced": {
    "model_size": "medium",
    "resolution": "standard",
    "fps": "moderate",
    "confidence_threshold": "standard"
  },
  "maximum_speed": {
    "model_size": "smallest",
    "resolution": "lowest",
    "fps": "highest",
    "confidence_threshold": "lowest"
  }
}
```

### 10. USE CASE TEMPLATES

#### 10.1 Security Applications
```json
{
  "perimeter_security": {
    "base_profile": "high_accuracy",
    "tracking": "standard",
    "alerts": "immediate",
    "fps": "standard"
  },
  "access_control": {
    "base_profile": "high_accuracy",
    "tracking": "high_accuracy",
    "alerts": "urgent",
    "fps": "standard"
  },
  "crowd_monitoring": {
    "base_profile": "large_viewpoint",
    "tracking": "fast_moving",
    "alerts": "moderate",
    "fps": "conservative"
  }
}
```

#### 10.2 Safety Applications
```json
{
  "fall_detection": {
    "base_profile": "high_accuracy",
    "tracking": "standard",
    "alerts": "immediate",
    "fps": "standard"
  },
  "fire_detection": {
    "base_profile": "high_accuracy",
    "tracking": "stationary",
    "alerts": "immediate",
    "fps": "conservative"
  },
  "workplace_safety": {
    "base_profile": "balanced",
    "tracking": "standard",
    "alerts": "urgent",
    "fps": "standard"
  }
}
```

## Usage Instructions

### Parameter Selection Process
1. **Identify Primary Requirement**: Choose main optimization goal (accuracy, speed, etc.)
2. **Select Environmental Profile**: Match lighting, weather, viewpoint conditions
3. **Choose Use Case Template**: Select appropriate application template
4. **Apply Hardware Profile**: Match available hardware capabilities
5. **Fine-tune Specific Parameters**: Adjust individual parameters as needed

### Configuration Inheritance
- Parameters inherit from base profiles
- Environmental adaptations override base settings
- Hardware profiles adjust processing parameters
- Alert configurations are independent and additive

### Example Configuration Selection
```json
{
  "use_case": "loitering_detection",
  "environment": "low_light",
  "requirement": "high_accuracy",
  "hardware": "mid_range",
  "resulting_config": {
    "object_detection": "low_light + high_accuracy",
    "tracking": "low_light + high_accuracy",
    "use_case_params": "loitering + high_accuracy + low_light",
    "fps": "conservative",
    "alerts": "standard"
  }
}
```

This master document serves as the single source of truth for all parameter configurations, enabling consistent and maintainable parameter management across all use cases and environmental conditions.
