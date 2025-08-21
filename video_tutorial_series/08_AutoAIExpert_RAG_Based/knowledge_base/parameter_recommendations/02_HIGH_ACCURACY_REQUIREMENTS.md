# High Accuracy Requirements Parameter Recommendations

## Overview
Parameter tuning recommendations for computer vision pipelines where accuracy is the primary concern, typically used in critical security applications, legal evidence collection, or high-stakes monitoring scenarios.

**Reference**: See `MASTER_USECASE_PARAMETERS.md` for complete parameter definitions.

## Configuration Profiles Used

### Base Profile: `high_accuracy`
All parameters in this document reference the `high_accuracy` profile from the master configuration.

## Accuracy Requirements
- **False Positive Rate**: < 1%
- **False Negative Rate**: < 5%
- **Precision**: > 95%
- **Recall**: > 90%

## Detection Model Parameters

### Object Detection
**Profile Used**: `detection_models.object_detection.high_accuracy`
```json
{
  "conf": 0.35,                    // Higher confidence threshold (from 0.25)
  "iou": 0.5,                      // Stricter IoU for precise detections
  "max_dets": 500,                 // Allow more detections for completeness
  "model_resolution": {
    "width": 1024,                 // Higher resolution for detail
    "height": 1024
  },
  "decoder": {
    "width": 1920,                 // Full resolution decoding
    "height": 1080
  },
  "use_fp16": false,               // Use FP32 for maximum precision
  "batch_size": 1,                 // Single image processing for consistency
  "enable_batching": false         // Disable batching for deterministic results
}
```

### Face Detection
```json
{
  "conf": 0.85,                    // Very high confidence (from 0.6)
  "pixel_hthresh": 80,             // Larger minimum face size
  "pixel_wthresh": 80,
  "nmsThresh": 0.5,                // Standard NMS for precision
  "MODEL": "10G_KPS",              // Use largest model available
  "computeType": "GPU"
}
```

### Fire Detection
```json
{
  "conf": 0.85,                    // Very high confidence (from 0.7)
  "frameCountThresh": 15,          // Require many frames for confirmation
  "alert_interval": 60,            // Longer intervals between alerts
  "model_resolution": {
    "width": 1024,
    "height": 1024
  }
}
```

### Weapon Detection
```json
{
  "conf": 0.85,                    // Very high confidence
  "frameCountThresh": 10,          // Multiple frame confirmation
  "withoutAssociationObjectsNeeded": "False",
  "alert_interval": 60             // Conservative alert timing
}
```

## Tracking Parameters

### General Tracking (High Precision)
```json
{
  "ttl": 8,                        // Longer track persistence
  "iou": 0.6,                      // High IoU for precise matching
  "sigma_iou": 0.2,                // Low uncertainty tolerance
  "sigma_h": 0.2,
  "sigma_l": 0.05,
  "t_min": 5,                      // Require many frames for track establishment
  "conf_thresh": 0.3               // Higher confidence for tracks
}
```

### FastMOT Tracker (Precision Mode)
```json
{
  "max_age": 15,                   // Long track persistence
  "age_penalty": 3,                // Higher age penalty for precision
  "motion_weight": 0.3,            // Lower motion weight, higher appearance weight
  "max_assoc_cost": 0.6,           // Strict association cost
  "max_reid_cost": 0.4,            // Strict re-identification
  "iou_thresh": 0.5,               // High IoU threshold
  "duplicate_thresh": 0.3,         // Strict duplicate detection
  "conf_thresh": 0.25,             // Higher confidence threshold
  "confirm_hits": 3                // Require multiple confirmations
}
```

## Processing Parameters

### Frame Rate Settings
```json
{
  "fps": "10/1",                   // Higher FPS for better temporal resolution
  "actuation_frequency": 1
}
```

### Image Quality
```json
{
  "frame_quality": 100,            // Maximum quality
  "color_format": "BGR",
  "stretch_image": false,
  "interpolationType": "INTERP_LANCZOS4"  // Highest quality interpolation
}
```

## Use Case Specific High-Accuracy Adjustments

### Loitering Detection
```json
{
  "loiteringThresholdSeconds": 60, // Longer threshold for certainty
  "alert_interval": 120,           // Conservative alert timing
  "fps": "5/1",
  "minimum_track_length": 30       // Require long tracks
}
```

### Abandoned Object Detection
```json
{
  "timeThreshold": 300,            // 5 minutes for high certainty
  "distance_ratio": 1.2,           // Strict distance matching
  "associate_conf": 0.8,           // High association confidence
  "object_persistence": 60         // Object must persist longer
}
```

### Fall Detection
```json
{
  "fallConfidence": 0.9,           // Very high confidence
  "personConfidence": 0.7,         // High person confidence
  "fall_time": 30,                 // Shorter time but high confidence
  "non_fall_time": 5,              // Longer recovery period
  "alert_interval": 600,           // Conservative alerting
  "multi_angle_verification": true // Use multiple camera angles if available
}
```

### Fight Detection
```json
{
  "min_fight_duration": 10,        // Longer duration requirement
  "frameCountThresh": 150,         // Many frames for confirmation
  "pplInteractionRequired": "True", // Require person interaction
  "conf": 0.4,                     // Higher confidence for fight detection
  "strict": true                   // Enable strict mode
}
```

### Face Recognition System (FRS)
```json
{
  "match_score": 0.98,             // Very high match score (from 0.95)
  "minimum_reco_count": 25,        // More recognitions for voting
  "topks": 1,                      // Only top match
  "recog_allowed_h": 80,           // Larger face requirements
  "recog_allowed_w": 80,
  "voting_window": 60              // Longer voting window
}
```

## Policy Configurations

### Zone-based Filtering
```json
{
  "zone_coverage": 0.8,            // Require 80% object within zone
  "pivotPoint": "centerPoint",     // Use center for precise positioning
  "zone_margin": -5                // Negative margin for strict zone adherence
}
```

### Scale Filtering
```json
{
  "frame_h_obj_h": {
    "value": 15.0,                 // Strict size requirements
    "op": "<"
  },
  "frame_w_obj_w": {
    "value": 25.0,
    "op": "<"
  },
  "min_object_area": 2000          // Minimum pixel area
}
```

### Class Filtering
```json
{
  "allowed_classes": ["specific"],  // Restrict to specific classes only
  "confidence_per_class": {
    "person": 0.8,
    "vehicle": 0.85,
    "weapon": 0.9
  }
}
```

## Multi-Stage Verification

### Cascade Filtering
```json
{
  "stage_1": {
    "conf": 0.6,                   // Initial detection
    "verification": "quick"
  },
  "stage_2": {
    "conf": 0.8,                   // Detailed analysis
    "verification": "thorough"
  },
  "stage_3": {
    "conf": 0.9,                   // Final confirmation
    "verification": "comprehensive"
  }
}
```

### Temporal Validation
```json
{
  "temporal_consistency": {
    "window_size": 30,             // 30 frame window
    "consistency_threshold": 0.8,  // 80% consistency required
    "smoothing": "gaussian"
  }
}
```

## Alert System Configuration

### High-Accuracy Alerting
```json
{
  "alert_confidence_threshold": 0.95,
  "multi_frame_confirmation": 15,
  "human_verification_required": true,
  "alert_interval": 300,           // 5 minutes between alerts
  "severity": "critical",
  "include_evidence": {
    "video_clip": true,
    "confidence_scores": true,
    "detection_history": true,
    "spatial_information": true
  }
}
```

### Evidence Collection
```json
{
  "pre_event_buffer": 30,          // 30 seconds before event
  "post_event_buffer": 30,         // 30 seconds after event
  "full_resolution_storage": true,
  "metadata_logging": "comprehensive",
  "chain_of_custody": true
}
```

## Hardware Optimization for Accuracy

### GPU Configuration
```json
{
  "use_fp16": false,               // Use FP32 for maximum precision
  "batch_size": 1,                 // Single inference for consistency
  "memory_optimization": false,    // Prioritize accuracy over memory
  "deterministic_operations": true // Ensure reproducible results
}
```

### Model Selection
```json
{
  "model_size": "largest_available",
  "ensemble_methods": true,        // Use model ensembles if available
  "model_validation": "strict"
}
```

## Quality Assurance Parameters

### Performance Monitoring
```json
{
  "accuracy_monitoring": {
    "sample_rate": 0.1,            // Monitor 10% of detections
    "ground_truth_comparison": true,
    "performance_alerts": true
  },
  "calibration_schedule": "weekly",
  "benchmark_testing": "monthly"
}
```

### Validation Metrics
```json
{
  "required_metrics": {
    "precision": 0.95,
    "recall": 0.90,
    "f1_score": 0.92,
    "accuracy": 0.93
  }
}
```

## Environmental Considerations

### Lighting Adaptation
```json
{
  "auto_exposure": false,          // Manual exposure control
  "lighting_normalization": true,
  "shadow_compensation": true,
  "glare_reduction": true
}
```

### Weather Compensation
```json
{
  "weather_detection": true,
  "adaptive_thresholds": {
    "rain": {"conf_adjustment": +0.1},
    "fog": {"conf_adjustment": +0.15},
    "snow": {"conf_adjustment": +0.1}
  }
}
```

## Implementation Guidelines

### Deployment Strategy
1. **Staged Rollout**: Implement in test environment first
2. **Baseline Establishment**: Record current performance metrics
3. **Gradual Parameter Adjustment**: Change one parameter category at a time
4. **Continuous Monitoring**: Track accuracy metrics continuously
5. **Regular Validation**: Compare against ground truth data

### Performance Expectations
- **Processing Speed**: 30-50% reduction in throughput
- **Memory Usage**: 40-60% increase in memory requirements
- **Storage Requirements**: 2-3x increase due to evidence collection
- **Accuracy Improvement**: 10-25% improvement in precision/recall

### Risk Mitigation
- **Backup Systems**: Maintain fallback to standard parameters
- **Human Oversight**: Require human validation for critical decisions
- **Regular Audits**: Monthly accuracy assessments
- **Parameter Versioning**: Track all parameter changes

This high-accuracy parameter set prioritizes precision and reliability over speed and resource efficiency, suitable for mission-critical applications where accuracy is paramount.
