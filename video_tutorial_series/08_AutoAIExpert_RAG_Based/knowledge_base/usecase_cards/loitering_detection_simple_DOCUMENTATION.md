# Loitering Detection Usecase Documentation

## Overview
This document describes the `loitering_detection_simple.json` usecase card, which defines a loitering detection algorithm for security monitoring applications. This usecase identifies individuals who remain in an area beyond a configurable time threshold.

## Usecase Identity

### Component Information
- **Component ID**: `loitering_detection`
- **Component Type**: `node.algorithm.usecase` (Business Logic Usecase Node)
- **ID**: `uc-loitering-detection`
- **Label**: Usecase
- **Name**: Loitering Detection
- **Category**: Security Usecase
- **Framework**: AIOS Pipeline
- **License**: MIT

## Model Details

### Description
Detects individuals remaining in an area beyond a threshold time with configurable alert management.

### Intended Use
Security monitoring for suspicious loitering behavior in restricted or monitored areas.

### Limitations
- **Tracking Dependency**: Requires stable object tracking from upstream components
- **Crowd Performance**: Performance depends on crowd density and tracking quality
- **Static Environment**: Works best in environments with minimal camera movement

### Ethical Considerations
- Ensure fair application across all demographic groups
- Respect privacy regulations and local laws
- Consider bias in tracking algorithms that may affect certain populations
- Implement appropriate data retention and deletion policies

## Technical Parameters

### Computational Characteristics
- **Computational Complexity**: O(n) where n = number of tracked objects
- **Memory Footprint**: Medium
- **Processing Type**: Temporal analysis with alerting
- **Dependencies**: 
  - Object detection (upstream)
  - Tracking (upstream) 
  - Zone filtering (upstream)
  - Dwell time policy (internal logic)

## Configuration Parameters

### Loitering Threshold (`loiteringThresholdSeconds`)
- **Description**: Check if objects remain stationary for longer than the specified time
- **Type**: Integer
- **Default**: 60 seconds
- **Range**: 30 - 300 seconds
- **Purpose**: Defines when stationary behavior becomes "loitering"
- **Tuning Guidelines**:
  - **High Security Areas**: 30-60 seconds
  - **Public Areas**: 120-300 seconds
  - **Transit Areas**: 60-120 seconds

### Alert Interval (`alert_interval`)
- **Description**: Frequency of repeated alerts for continuing loitering behavior
- **Type**: Integer
- **Default**: 30 seconds
- **Range**: 10 - 120 seconds
- **Unit**: Seconds
- **Purpose**: Prevents alert fatigue by controlling notification frequency
- **Behavior**: Alerts at initial detection, then every interval while loitering continues

### Severity Level (`severity`)
- **Description**: Impact level of the detected loitering event
- **Type**: String
- **Allowed Values**: 
  - `"low"`: Minimal impact or urgency
  - `"medium"`: Moderate impact requiring attention
  - `"high"`: Critical impact requiring immediate action
- **Default**: "medium"
- **Use Cases**:
  - **Low**: Public benches, waiting areas
  - **Medium**: Retail spaces, office lobbies
  - **High**: Restricted areas, emergency exits

## Runtime Requirements

### Hardware Requirements
- **CPU Intensive**: No (lightweight temporal analysis)
- **GPU Required**: No (pure business logic)
- **Minimum RAM**: 100 MB
- **Recommended CPU**: Multi-core CPU for concurrent object processing

### Software Dependencies
- **Python Version**: 3.8+
- **Required Libraries**:
  - `opencv-python >= 4.5.0` (for geometric calculations)
  - `numpy >= 1.20.0` (for numerical operations)

## Performance Benchmarks

### Throughput Metrics
- **Simultaneous Objects**: Up to 50 tracked objects
- **Alert Generation Latency**: 500 ms
- **Memory per Track**: 10 KB
- **CPU Usage**: Low (< 5% on modern multi-core systems)

### Scalability
- Linear scaling with number of tracked objects
- Memory usage grows proportionally with track count
- Alert processing is asynchronous and non-blocking

## Data Contract

### Input Requirements
- **Consumes**: 
  - `["tracked_detections"]`: Object tracks with temporal information
  - `["zone_definitions"]`: Area definitions for loitering zones
- **Input Formats**: `["OD1"]` (Object Detection format 1)

### Required Input Data Structure
```json
{
  "tracked_detections": {
    "track_id": "unique_identifier",
    "bbox": [x, y, width, height],
    "timestamp": "unix_timestamp",
    "position_history": "recent_positions",
    "zone_membership": "current_zones"
  },
  "zone_definitions": {
    "zone_id": "zone_identifier",
    "polygon": "zone_boundary_points",
    "loitering_enabled": true
  }
}
```

### Output Specifications
- **Produces**: 
  - `["loitering_alerts"]`: Alert notifications with metadata
  - `["severity_metadata"]`: Additional context for alerts
- **Output Formats**: `["OD1"]` (Object Detection format 1)

### Output Data Structure
```json
{
  "loitering_alerts": {
    "alert_id": "unique_alert_id",
    "track_id": "loitering_object_id",
    "zone_id": "affected_zone",
    "severity": "low|medium|high",
    "duration_seconds": "loitering_duration",
    "timestamp": "alert_time",
    "position": "current_object_position"
  },
  "severity_metadata": {
    "confidence": "detection_confidence",
    "zone_context": "zone_information",
    "historical_behavior": "object_movement_pattern"
  }
}
```

## Algorithm Logic

### Processing Flow
1. **Input Processing**: Receive tracked objects and zone definitions
2. **Zone Analysis**: Determine which objects are in loitering-enabled zones
3. **Temporal Analysis**: Calculate dwell time for each object in zones
4. **Threshold Comparison**: Check if dwell time exceeds threshold
5. **Alert Generation**: Create alerts for new loitering events
6. **Alert Management**: Handle repeat alerts based on interval configuration
7. **Output Generation**: Format and emit alerts with metadata

### State Management
- Maintains object dwell time state across frames
- Tracks alert history to prevent duplicate notifications
- Manages zone entry/exit events for accurate timing

### Loitering Detection Logic
```python
def detect_loitering(track, zones, config):
    for zone in zones:
        if is_object_in_zone(track.position, zone):
            dwell_time = calculate_dwell_time(track, zone)
            if dwell_time > config.loiteringThresholdSeconds:
                if should_generate_alert(track, zone, config.alert_interval):
                    return create_alert(track, zone, config.severity, dwell_time)
    return None
```

## Usage Notes

### Best Use Cases
- **Security Monitoring**: Unauthorized presence detection
- **Retail Analytics**: Customer behavior analysis in restricted areas
- **Traffic Management**: Vehicle loitering in no-parking zones
- **Facility Management**: Monitoring building entrances and restricted areas
- **Public Safety**: Suspicious behavior detection in public spaces

### Configuration Guidelines

#### High Security Environments
```json
{
  "loiteringThresholdSeconds": 30,
  "alert_interval": 15,
  "severity": "high"
}
```

#### Public Spaces
```json
{
  "loiteringThresholdSeconds": 180,
  "alert_interval": 60,
  "severity": "low"
}
```

#### Commercial Areas
```json
{
  "loiteringThresholdSeconds": 90,
  "alert_interval": 30,
  "severity": "medium"
}
```

### Integration Requirements

#### Upstream Dependencies
1. **Object Detection**: Provides initial object bounding boxes
2. **Tracking**: Maintains object identity across frames
3. **Zone Filtering**: Defines areas where loitering detection applies

#### Downstream Applications
1. **Alert Systems**: Security notification systems
2. **Analytics Dashboards**: Loitering pattern visualization
3. **Report Generation**: Security incident reporting
4. **Automated Response**: Camera PTZ control, lighting activation

### Pipeline Integration Example
```
Camera → Object Detection → Tracking → Zone Filter → Loitering Detection → Alert System
```

## Troubleshooting

### Common Issues
1. **False Positives**: Reduce threshold time or adjust zone boundaries
2. **Missed Detection**: Increase zone coverage or improve tracking quality
3. **Alert Spam**: Increase alert interval or adjust severity levels
4. **Performance Issues**: Reduce number of monitored zones or optimize tracking

### Performance Optimization
- Use zone-based filtering to reduce computational load
- Implement object lifecycle management to prevent memory leaks
- Optimize alert generation to avoid redundant processing
- Consider frame skipping for non-critical applications

## References
- MIT License: https://opensource.org/licenses/MIT
- AIOS Pipeline Framework Documentation
- Computer Vision Security Best Practices

## Notes
Essential for security applications. Configurable parameters prevent alert fatigue while maintaining security effectiveness. Designed to work seamlessly with upstream tracking and detection components in AIOS pipelines.
