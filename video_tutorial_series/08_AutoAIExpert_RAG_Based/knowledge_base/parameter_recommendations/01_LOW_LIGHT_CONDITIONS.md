# Low Light Conditions Parameter Recommendations

## Overview
Parameter tuning recommendations for computer vision pipelines operating in low light environments such as nighttime surveillance, indoor dimly lit areas, or twilight conditions.

**Reference**: See `MASTER_USECASE_PARAMETERS.md` for complete parameter definitions.

## Environmental Characteristics
- **Illumination**: < 50 lux (moonlight to dim indoor lighting)
- **Visibility**: Reduced contrast, increased noise
- **Challenge**: Maintaining detection accuracy with poor visibility

## Configuration Profiles Used

### Base Profile: `low_light`
All parameters in this document reference the `low_light` profile from the master configuration.

## Detection Model Parameters

### Object Detection
**Profile Used**: `detection_models.object_detection.low_light`
```json
{
  "conf": 0.15,                    // Lower confidence threshold (from 0.25)
  "iou": 0.35,                     // Lower IoU to capture more detections
  "max_dets": 500,                 // Increase max detections
  "model_resolution": {
    "width": 1024,                 // Higher resolution for better feature extraction
    "height": 1024
  },
  "decoder": {
    "width": 1024,                 // Match model resolution
    "height": 704
  },
  "use_fp16": false,               // Use FP32 for better precision
  "batch_size": 4                  // Reduce batch size for stability
}
```

### Face Detection
**Profile Used**: `detection_models.face_detection.low_light`
```json
{
  "conf": 0.4,                     // Slightly lower than normal (from 0.6)
  "pixel_hthresh": 40,             // Lower minimum face size
  "pixel_wthresh": 40,
  "nmsThresh": 0.35,               // Lower NMS for more detections
  "MODEL": "10G_KPS"               // Use largest available model
}
```

### Fire Detection
**Profile Used**: `detection_models.fire_detection.low_light`
```json
{
  "conf": 0.5,                     // Lower confidence (from 0.7)
  "frameCountThresh": 8,           // Increase frame count for confirmation
  "model_resolution": {
    "width": 1024,                 // Use highest resolution
    "height": 1024
  }
}
```

## Tracking Parameters

### General Tracking
**Profile Used**: `tracking.general.low_light`
```json
{
  "ttl": 6,                        // Increase track persistence (from 4)
  "iou": 0.3,                      // Lower IoU threshold (from 0.45)
  "sigma_iou": 0.4,                // Increase uncertainty tolerance
  "sigma_h": 0.4,
  "sigma_l": 0.2,
  "t_min": 3,                      // Require more frames for track start
  "conf_thresh": 0.1               // Very low confidence threshold
}
```

### FastMOT Tracker
**Profile Used**: `tracking.fastmot.low_light`
```json
{
  "max_age": 12,                   // Increase track age (from 9)
  "age_penalty": 1,                // Reduce age penalty
  "motion_weight": 0.6,            // Increase motion weight
  "max_assoc_cost": 0.9,           // More lenient association
  "max_reid_cost": 0.8,            // More lenient re-identification
  "conf_thresh": 0.08              // Very low confidence
}
```

## Processing Parameters

### Frame Rate Settings
**Profile Used**: `frame_processing.fps.conservative`
```json
{
  "fps": "3/1",                    // Reduce FPS for better processing (from 5/1)
  "actuation_frequency": 1
}
```

### Image Enhancement
**Profile Used**: `frame_processing.quality.high_quality`
```json
{
  "frame_quality": 95,             // Increase quality (from 90)
  "color_format": "BGR",
  "stretch_image": false,
  "interpolationType": "INTERP_CUBIC"  // Higher quality interpolation
}
```

## Use Case Specific Adjustments

### Loitering Detection
```json
{
  "loiteringThresholdSeconds": 30, // Increase threshold (from 20)
  "alert_interval": 60,            // Increase alert interval (from 40)
  "fps": "2/1"                     // Slower processing
}
```

### Abandoned Object Detection
```json
{
  "timeThreshold": 180,            // Increase time threshold (from 120)
  "distance_ratio": 2.5,           // More lenient distance matching
  "associate_conf": 0.5            // Lower association confidence
}
```

### Weapon Detection
```json
{
  "conf": 0.5,                     // Lower confidence (from 0.7)
  "frameCountThresh": 8,           // More frames for confirmation
  "alert_interval": 45             // Longer alert interval
}
```

### Fall Detection
```json
{
  "fallConfidence": 0.6,           // Lower confidence (from 0.7)
  "personConfidence": 0.4,         // Lower person confidence
  "fall_time": 90,                 // Longer observation time
  "alert_interval": 450            // Longer alert interval
}
```

## Camera Tampering Detection
```json
{
  "blurThreshold": 120,            // Lower blur threshold (from 140)
  "brightnessFrameCountThresh": 15, // More frames for confirmation
  "darknessThresh": 0.4,           // Higher darkness tolerance
  "darknessFrameCountThresh": 8    // More frames for dark detection
}
```

## Policy Adjustments

### Zone-based Filtering
```json
{
  "pivotPoint": "bottomPoint",     // Use bottom point for better low-light tracking
  "zone_margin": 10                // Add margin to zone boundaries
}
```

### Scale Filtering
```json
{
  "frame_h_obj_h": {
    "value": 30.0,                 // More lenient size requirements
    "op": "<"
  },
  "frame_w_obj_w": {
    "value": 50.0,
    "op": "<"
  }
}
```

## Alert System Adjustments

### General Alert Settings
```json
{
  "alert_interval": "1.5x normal", // Increase all alert intervals by 50%
  "severity": "medium",            // Lower severity due to uncertainty
  "confidence_reporting": true     // Include confidence in alerts
}
```

## Hardware Optimization

### GPU Settings
```json
{
  "use_fp16": false,               // Use FP32 for better precision
  "batch_size": "reduce by 50%",   // Smaller batches for stability
  "enable_batching": true
}
```

### Memory Management
```json
{
  "decoder_type": "DALI",          // Use DALI for better preprocessing
  "interpolationType": "INTERP_CUBIC"
}
```

## Monitoring Recommendations

### Key Metrics to Watch
- **False Positive Rate**: Expected to increase in low light
- **Detection Confidence Distribution**: Should be lower than normal
- **Track Persistence**: Monitor for broken tracks
- **Processing Latency**: May increase with higher resolutions

### Adaptive Thresholds
- **Time-based Adjustment**: Lower thresholds during night hours
- **Ambient Light Sensors**: Automatic threshold adjustment
- **Historical Performance**: Learn from past low-light performance

## Implementation Notes

1. **Gradual Adjustment**: Implement changes gradually to monitor impact
2. **A/B Testing**: Compare performance with baseline parameters
3. **Environmental Calibration**: Tune parameters for specific installation sites
4. **Failsafe Mechanisms**: Implement fallback to standard parameters if performance degrades significantly

## Performance Expectations

### Expected Changes
- **Detection Rate**: 15-25% reduction in detection rate
- **False Positives**: 20-40% increase in false positives
- **Processing Time**: 10-20% increase due to higher resolutions
- **Alert Frequency**: May increase due to lower confidence thresholds

### Mitigation Strategies
- **Multi-frame Confirmation**: Require detections across multiple frames
- **Confidence Weighting**: Weight decisions based on detection confidence
- **Temporal Smoothing**: Use track history for decision making
- **Human Verification**: Flag low-confidence alerts for human review

This parameter set optimizes for maintaining detection capability in challenging low-light conditions while managing the trade-off between sensitivity and false positives.
