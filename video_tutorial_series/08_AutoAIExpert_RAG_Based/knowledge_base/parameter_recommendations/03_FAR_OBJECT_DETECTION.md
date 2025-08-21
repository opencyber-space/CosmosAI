# Far Object Detection Parameter Recommendations

## Overview
Parameter tuning recommendations for computer vision pipelines designed to detect objects at long distances, such as perimeter security, border monitoring, airport surveillance, and wide-area coverage scenarios.

**Reference**: See `MASTER_USECASE_PARAMETERS.md` for complete parameter definitions.

## Configuration Profiles Used

### Base Profile: `far_detection`
All parameters in this document reference the `far_detection` profile from the master configuration.

## Distance Characteristics
- **Detection Range**: 100m - 1000m+ from camera
- **Object Size**: Objects appear as 10-50 pixels in height
- **Challenge**: Maintaining detection accuracy with minimal visual information

## Detection Model Parameters

### Object Detection (Long Range)
**Profile Used**: `detection_models.object_detection.far_detection`
```json
{
  "conf": 0.2,                     // Lower confidence for far objects
  "iou": 0.4,                      // Moderate IoU for smaller overlaps
  "max_dets": 600,                 // Increase max detections
  "model_resolution": {
    "width": 1280,                 // Very high resolution for far detection
    "height": 1280
  },
  "decoder": {
    "width": 1280,                 // High resolution decoding
    "height": 960
  },
  "use_fp16": false,               // FP32 for better precision
  "batch_size": 2,                 // Smaller batches for large images
  "enable_batching": true
}
```

### Alternative High-Resolution Model
```json
{
  "model_resolution": {
    "width": 1536,                 // Ultra-high resolution
    "height": 1536
  },
  "decoder": {
    "width": 2560,                 // Ultra-high decoder resolution
    "height": 1440
  },
  "multi_scale_inference": true,   // Enable multi-scale detection
  "small_object_enhancement": true
}
```

### Face Detection (Long Range)
```json
{
  "conf": 0.3,                     // Lower confidence for far faces
  "pixel_hthresh": 20,             // Very small minimum face size
  "pixel_wthresh": 20,
  "nmsThresh": 0.3,                // Lower NMS for small detections
  "MODEL": "10G_KPS",              // Use largest model for detail
  "enhancement_preprocessing": true
}
```

### Fire Detection (Long Range)
```json
{
  "conf": 0.6,                     // Moderate confidence
  "frameCountThresh": 20,          // More frames for far object confirmation
  "model_resolution": {
    "width": 1280,
    "height": 1280
  },
  "smoke_detection_enabled": true, // Enable smoke detection for early warning
  "temporal_analysis": true        // Use temporal patterns
}
```

### Weapon Detection (Long Range)
```json
{
  "conf": 0.5,                     // Moderate confidence
  "frameCountThresh": 15,          // Multiple frame confirmation
  "model_resolution": {
    "width": 1280,
    "height": 1280
  },
  "zoom_enhancement": true,        // Digital zoom on detection areas
  "silhouette_analysis": true      // Analyze object silhouettes
}
```

## Tracking Parameters

### Long Range Tracking
```json
{
  "ttl": 10,                       // Longer track persistence (from 4)
  "iou": 0.2,                      // Very low IoU for small objects
  "sigma_iou": 0.5,                // High uncertainty tolerance
  "sigma_h": 0.6,                  // High height uncertainty
  "sigma_l": 0.4,                  // High location uncertainty
  "t_min": 2,                      // Lower minimum track length
  "conf_thresh": 0.1,              // Very low confidence threshold
  "motion_prediction": true,       // Enable motion prediction
  "interpolation": "kalman"        // Use Kalman filtering
}
```

### FastMOT Tracker (Long Range)
```json
{
  "max_age": 20,                   // Very long track age
  "age_penalty": 1,                // Low age penalty
  "motion_weight": 0.7,            // High motion weight
  "max_assoc_cost": 0.95,          // Very lenient association
  "max_reid_cost": 0.9,            // Lenient re-identification
  "iou_thresh": 0.2,               // Very low IoU threshold
  "duplicate_thresh": 0.7,         // High duplicate threshold
  "occlusion_thresh": 0.6,         // High occlusion tolerance
  "conf_thresh": 0.05,             // Very low confidence
  "history_size": 100,             // Large history for long tracks
  "motion_model": "constant_velocity"
}
```

## Processing Parameters

### Frame Rate and Processing
```json
{
  "fps": "2/1",                    // Lower FPS for processing intensive tasks
  "actuation_frequency": 1,
  "processing_mode": "thorough"
}
```

### Image Enhancement
```json
{
  "frame_quality": 100,            // Maximum quality
  "color_format": "BGR",
  "stretch_image": false,
  "interpolationType": "INTERP_LANCZOS4",
  "sharpening": true,              // Enable image sharpening
  "contrast_enhancement": true,    // Enhance contrast for far objects
  "noise_reduction": "moderate"    // Balance noise vs detail
}
```

## Use Case Specific Adjustments

### Loitering Detection (Long Range)
```json
{
  "loiteringThresholdSeconds": 120, // Longer threshold for far objects
  "alert_interval": 180,           // Longer alert intervals
  "fps": "1/1",                    // Slower processing
  "minimum_movement": 5,           // Pixels for movement detection
  "zone_expansion": 1.2            // Expand zones for far detection
}
```

### Abandoned Object Detection (Long Range)
```json
{
  "timeThreshold": 600,            // 10 minutes for far objects
  "distance_ratio": 3.0,           // Very lenient distance matching
  "associate_conf": 0.3,           // Lower association confidence
  "object_persistence": 120,       // Long persistence requirement
  "size_tolerance": 0.5            // High size variation tolerance
}
```

### Intrusion Detection (Perimeter)
```json
{
  "line_crossing": {
    "buffer_distance": 20,         // Larger buffer for far detection
    "confirmation_frames": 10,     // Multiple frame confirmation
    "direction_sensitivity": 0.7   // Less strict direction requirements
  },
  "approach_detection": {
    "distance_zones": [500, 300, 100], // Multiple distance zones
    "size_progression": true       // Track size increase
  }
}
```

### Crowd Detection (Wide Area)
```json
{
  "countThreshold": {
    "ZoneCrowd": 50               // Higher threshold for wide areas
  },
  "density_estimation": true,     // Use density instead of counting
  "heatmap_analysis": true,       // Generate crowd heatmaps
  "fps": "1/2"                    // Very slow processing
}
```

## Advanced Detection Techniques

### Multi-Scale Processing
```json
{
  "pyramid_levels": 5,             // Multiple scale levels
  "scale_factors": [0.5, 0.75, 1.0, 1.25, 1.5],
  "fusion_method": "weighted_average",
  "confidence_weighting": true
}
```

### Region of Interest (ROI) Enhancement
```json
{
  "roi_detection": true,
  "roi_enhancement": {
    "zoom_factor": 2.0,           // Digital zoom on ROIs
    "separate_processing": true,   // Process ROIs separately
    "overlap_handling": "merge"
  }
}
```

### Temporal Analysis
```json
{
  "background_subtraction": true,
  "motion_analysis": {
    "optical_flow": true,
    "change_detection": true,
    "temporal_window": 30         // 30 frame analysis window
  }
}
```

## Camera Configuration

### Lens and Optical Settings
```json
{
  "focal_length": "telephoto",     // Use telephoto lenses
  "aperture": "f/8",              // Optimal aperture for sharpness
  "image_stabilization": true,    // Enable stabilization
  "auto_focus": "infinity",       // Focus at infinity
  "zoom_capability": "optical"    // Use optical zoom when available
}
```

### Mount and Positioning
```json
{
  "mount_stability": "high",      // Stable mounting required
  "vibration_compensation": true,
  "pan_tilt_integration": true,   // PTZ camera support
  "field_of_view": "narrow"       // Narrow FOV for far detection
}
```

## Environmental Compensation

### Atmospheric Conditions
```json
{
  "haze_compensation": true,
  "heat_shimmer_reduction": true,
  "atmospheric_correction": {
    "visibility_estimation": true,
    "contrast_enhancement": "adaptive"
  }
}
```

### Lighting Adaptation
```json
{
  "sun_glare_reduction": true,
  "shadow_analysis": true,
  "backlight_compensation": true,
  "dynamic_range_optimization": true
}
```

## Alert Configuration

### Long Range Alerting
```json
{
  "confidence_threshold": 0.6,    // Higher threshold for alerts
  "spatial_verification": true,   // Verify spatial consistency
  "size_progression_check": true, // Check object size changes
  "alert_zones": {
    "far": {"distance": ">500m", "confidence": 0.4},
    "medium": {"distance": "200-500m", "confidence": 0.5},
    "near": {"distance": "<200m", "confidence": 0.7}
  }
}
```

## Hardware Requirements

### GPU Configuration
```json
{
  "min_gpu_memory": "12GB",       // High memory for large images
  "recommended_gpu": "RTX 4080",  // High-end GPU recommended
  "batch_processing": "limited",  // Small batches due to memory
  "memory_optimization": true
}
```

### Storage Requirements
```json
{
  "high_resolution_storage": true,
  "compression": "lossless",      // Maintain detail for far objects
  "archival_policy": "extended"   // Keep data longer for analysis
}
```

## Performance Optimization

### Processing Pipeline
```json
{
  "pre_processing": {
    "roi_extraction": true,       // Extract ROIs first
    "resolution_adaptation": true, // Adapt based on object distance
    "parallel_processing": true   // Process multiple scales in parallel
  },
  "post_processing": {
    "confidence_calibration": true,
    "spatial_consistency": true,
    "temporal_smoothing": true
  }
}
```

### Caching Strategy
```json
{
  "background_cache": true,       // Cache background model
  "roi_cache": true,             // Cache ROI information
  "model_cache": "multiple_scales" // Cache models for different scales
}
```

## Quality Metrics

### Distance-Based Metrics
```json
{
  "metrics_by_distance": {
    "0-100m": {"min_precision": 0.9, "min_recall": 0.8},
    "100-300m": {"min_precision": 0.7, "min_recall": 0.6},
    "300-500m": {"min_precision": 0.5, "min_recall": 0.4},
    ">500m": {"min_precision": 0.3, "min_recall": 0.2}
  }
}
```

### Size-Based Thresholds
```json
{
  "object_size_categories": {
    "large": {">100px": {"conf": 0.7}},
    "medium": {"50-100px": {"conf": 0.5}},
    "small": {"20-50px": {"conf": 0.3}},
    "tiny": {"<20px": {"conf": 0.2}}
  }
}
```

## Implementation Considerations

### Deployment Strategy
1. **Camera Positioning**: Optimize camera placement for maximum coverage
2. **Lens Selection**: Use appropriate focal length for target distances
3. **Processing Power**: Ensure adequate GPU resources
4. **Network Bandwidth**: Plan for high-resolution data transmission
5. **Storage Capacity**: Account for large image sizes and long retention

### Performance Expectations
- **Detection Range**: Up to 1000m depending on object size
- **Processing Speed**: 50-70% reduction due to high resolution
- **Accuracy**: Distance-dependent, declining with range
- **Resource Usage**: 2-3x normal GPU memory and processing power

### Limitations
- **Weather Dependency**: Performance affected by atmospheric conditions
- **Object Size**: Minimum detectable size depends on distance
- **Processing Latency**: Higher latency due to complex processing
- **False Positives**: May increase at extreme distances

This parameter set optimizes for maximum detection range while managing the trade-offs in processing requirements and accuracy degradation with distance.
