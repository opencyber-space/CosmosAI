# Crowd Gathering Detection Usecase Documentation

## Overview
This document describes the `crowd_gathering_detection_simple.json` usecase card, which defines a crowd gathering detection algorithm for monitoring crowd density and preventing overcrowding in public spaces. This usecase identifies when the number of people in an area exceeds configurable thresholds.

## Usecase Identity

### Component Information
- **Component ID**: `crowd_gathering`
- **Component Type**: `node.algorithm.usecase` (Business Logic Usecase Node)
- **ID**: `uc-crowd-gathering`
- **Label**: Usecase
- **Name**: Crowd Gathering Detection
- **Category**: Security Usecase
- **Framework**: AIOS Pipeline
- **License**: MIT

## Model Details

### Description
Detects crowd formation events that exceed predefined thresholds with configurable alert management.

### Intended Use
Monitor crowd density and prevent overcrowding in public spaces, retail, and transportation hubs.

### Limitations
- **Dense Crowd Accuracy**: Accuracy decreases in extremely dense crowds due to occlusion
- **Camera Requirements**: Requires clear camera view with minimal obstructions
- **Environmental Factors**: Performance affected by lighting conditions and camera angle

### Ethical Considerations
- Ensure crowd monitoring respects privacy and does not target specific groups
- Implement fair counting algorithms that work across all demographic groups
- Respect local regulations regarding surveillance and crowd monitoring
- Consider data retention and deletion policies for crowd analytics

## Technical Parameters

### Computational Characteristics
- **Computational Complexity**: O(n) where n = detected objects per frame
- **Memory Footprint**: Medium
- **Processing Type**: Spatial counting with temporal filtering
- **Dependencies**: 
  - Object detection (upstream)
  - Counting algorithm (internal logic)
  - Zone filtering (internal/upstream)

## Configuration Parameters

### Count Threshold (`countThreshold`)
- **Description**: Raise alerts if the object count exceeds the specified threshold
- **Type**: Integer
- **Default**: 20 people
- **Range**: 5 - 200 people
- **Purpose**: Defines when crowd density becomes concerning
- **Tuning Guidelines**:
  - **Small Retail Spaces**: 10-20 people
  - **Public Transportation**: 30-50 people
  - **Event Venues**: 100-200 people
  - **Emergency Exits**: 5-15 people

### Violation Frame Count (`ViolationFrameCount`)
- **Description**: Number of consecutive frames count threshold must be exceeded
- **Type**: Integer
- **Default**: 10 frames
- **Range**: 3 - 30 frames
- **Unit**: Frames
- **Purpose**: Prevents false alarms from brief count spikes
- **Behavior**: Requires sustained crowd density before triggering alerts

### Alert Interval (`alert_interval`)
- **Description**: Frequency of repeated alerts for continuing crowd gathering
- **Type**: Integer
- **Default**: 60 seconds
- **Range**: 30 - 300 seconds
- **Unit**: Seconds
- **Purpose**: Prevents alert fatigue by controlling notification frequency
- **Behavior**: Alerts at initial detection, then every interval while crowd persists

### Severity Level (`severity`)
- **Description**: Impact level of the detected crowd gathering event
- **Type**: String
- **Allowed Values**: 
  - `"low"`: Minimal impact or urgency
  - `"medium"`: Moderate impact requiring attention
  - `"high"`: Critical impact requiring immediate action
- **Default**: "medium"
- **Use Cases**:
  - **Low**: Retail foot traffic analysis
  - **Medium**: Public space monitoring
  - **High**: Emergency evacuation scenarios

## Runtime Requirements

### Hardware Requirements
- **CPU Intensive**: No (lightweight counting logic)
- **GPU Required**: Yes (for object detection dependency)
- **Minimum RAM**: 150 MB
- **Recommended CPU**: Multi-core CPU for concurrent counting

### Software Dependencies
- **Python Version**: 3.8+
- **Required Libraries**:
  - `opencv-python >= 4.5.0` (for geometric calculations)
  - `numpy >= 1.20.0` (for numerical operations)

## Performance Benchmarks

### Throughput Metrics
- **Max Objects per Frame**: 200 detected objects
- **Counting Accuracy**: ±5% for crowds up to 50 people
- **Alert Generation Latency**: 1000 ms
- **Frame Processing**: Real-time at typical surveillance frame rates

### Accuracy Characteristics
- **Small Crowds (5-20)**: >95% accuracy
- **Medium Crowds (20-50)**: 90-95% accuracy
- **Large Crowds (50+)**: 85-90% accuracy (limited by occlusion)

## Data Contract

### Input Requirements
- **Consumes**: 
  - `["detected_objects"]`: Object detection results from upstream
  - `["zone_definitions"]`: Area definitions for crowd monitoring zones
- **Input Formats**: `["OD1"]` (Object Detection format 1)

### Required Input Data Structure
```json
{
  "detected_objects": {
    "frame_id": "unique_frame_identifier",
    "detections": [
      {
        "bbox": [x, y, width, height],
        "class": "person",
        "confidence": 0.8,
        "zone_membership": "zone_id"
      }
    ]
  },
  "zone_definitions": {
    "zone_id": "zone_identifier",
    "polygon": "zone_boundary_points",
    "crowd_monitoring_enabled": true,
    "capacity_limit": 50
  }
}
```

### Output Specifications
- **Produces**: 
  - `["crowd_alerts"]`: Alert notifications with crowd metrics
  - `["count_metadata"]`: Current crowd count information
  - `["severity_metadata"]`: Additional context for alerts
- **Output Formats**: `["OD1"]` (Object Detection format 1)

### Output Data Structure
```json
{
  "crowd_alerts": {
    "alert_id": "unique_alert_id",
    "zone_id": "affected_zone",
    "current_count": "actual_person_count",
    "threshold": "configured_threshold",
    "severity": "low|medium|high",
    "timestamp": "alert_time",
    "duration_frames": "violation_frame_count"
  },
  "count_metadata": {
    "zone_id": "zone_identifier",
    "current_count": "real_time_count",
    "average_count": "rolling_average",
    "peak_count": "maximum_observed",
    "trend": "increasing|decreasing|stable"
  },
  "severity_metadata": {
    "crowd_density": "people_per_square_meter",
    "safety_threshold": "emergency_evacuation_limit",
    "occupancy_percentage": "current_vs_capacity"
  }
}
```

## Algorithm Logic

### Processing Flow
1. **Input Processing**: Receive detected objects and zone definitions
2. **Zone-based Counting**: Count objects within each monitored zone
3. **Threshold Comparison**: Check if count exceeds configured threshold
4. **Temporal Filtering**: Validate violation across required frame count
5. **Alert Generation**: Create alerts for sustained crowd gathering
6. **Alert Management**: Handle repeat alerts based on interval configuration
7. **Metadata Generation**: Provide crowd analytics and trends

### Crowd Detection Logic
```python
def detect_crowd_gathering(detections, zones, config):
    for zone in zones:
        current_count = count_objects_in_zone(detections, zone)
        
        if current_count > config.countThreshold:
            violation_frames[zone.id] += 1
            
            if violation_frames[zone.id] >= config.ViolationFrameCount:
                if should_generate_alert(zone, config.alert_interval):
                    return create_crowd_alert(
                        zone, current_count, config.severity, 
                        violation_frames[zone.id]
                    )
        else:
            violation_frames[zone.id] = 0
    
    return None
```

### Temporal Filtering
- **Frame Buffer**: Maintains count history for each zone
- **Violation Tracking**: Counts consecutive frames exceeding threshold
- **Reset Logic**: Clears violation count when below threshold
- **Alert Timing**: Manages alert intervals to prevent spam

## Usage Notes

### Best Use Cases
- **Public Safety**: Overcrowding prevention in transportation hubs
- **Event Management**: Capacity control for concerts, festivals
- **Retail Analytics**: Customer flow management and safety compliance
- **Emergency Management**: Evacuation route monitoring
- **Building Management**: Fire safety and occupancy compliance

### Configuration Guidelines

#### High-Risk Venues (Stadiums, Theaters)
```json
{
  "countThreshold": 100,
  "ViolationFrameCount": 5,
  "alert_interval": 30,
  "severity": "high"
}
```

#### Public Transportation
```json
{
  "countThreshold": 40,
  "ViolationFrameCount": 10,
  "alert_interval": 60,
  "severity": "medium"
}
```

#### Retail Environments
```json
{
  "countThreshold": 25,
  "ViolationFrameCount": 15,
  "alert_interval": 120,
  "severity": "low"
}
```

#### Emergency Situations
```json
{
  "countThreshold": 200,
  "ViolationFrameCount": 3,
  "alert_interval": 15,
  "severity": "high"
}
```

### Integration Requirements

#### Upstream Dependencies
1. **Object Detection**: Provides person detections with bounding boxes
2. **Zone Definition**: Defines areas for crowd monitoring
3. **Calibration**: Camera calibration for accurate counting

#### Downstream Applications
1. **Emergency Response**: Automatic emergency service notification
2. **Public Announcements**: Crowd control messaging systems
3. **Access Control**: Entrance/exit management systems
4. **Analytics Dashboards**: Crowd pattern visualization
5. **Building Management**: HVAC and facility optimization

### Pipeline Integration Example
```
Camera → Object Detection → Zone Filter → Crowd Gathering Detection → Alert System
```

## Advanced Features

### Density Analysis
- **People per Square Meter**: Spatial density calculations
- **Movement Patterns**: Crowd flow direction analysis
- **Bottleneck Detection**: Identification of congestion points
- **Exit Capacity**: Evacuation route analysis

### Predictive Analytics
- **Trend Analysis**: Crowd growth/decline prediction
- **Peak Time Forecasting**: Historical pattern analysis
- **Capacity Planning**: Optimal space utilization
- **Event Impact**: Special event crowd modeling

## Troubleshooting

### Common Issues
1. **False Positives**: Reduce ViolationFrameCount or increase countThreshold
2. **Missed Crowds**: Lower countThreshold or improve object detection
3. **Alert Spam**: Increase alert_interval
4. **Counting Inaccuracy**: Improve camera positioning or detection model

### Performance Optimization
- Use zone-based filtering to reduce processing load
- Optimize counting algorithms for specific camera angles
- Implement adaptive thresholds based on time of day
- Consider multiple detection models for different scenarios

## Emergency Response Integration

### Alert Escalation
- **Low Severity**: Facility management notification
- **Medium Severity**: Security team alert
- **High Severity**: Emergency services and facility lockdown
- **Critical**: Automated emergency response activation

### Response Actions
- **Crowd Control**: Automated public announcements
- **Access Management**: Entrance closure/redirection
- **Emergency Services**: Automatic emergency calls
- **Evacuation**: Integration with building emergency systems

## References
- MIT License: https://opensource.org/licenses/MIT
- AIOS Pipeline Framework Documentation
- Crowd Dynamics and Safety Research

## Notes
Effective for crowd management and safety compliance. ViolationFrameCount prevents false alarms from brief count spikes. Essential for maintaining public safety in high-occupancy environments.
