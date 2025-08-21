# Dwell Time Policy Card Documentation

**File**: `dwell_time_policy.json`  
**Component Type**: `node.algorithm.policy`  
**Policy Name**: Dwell Time Policy  

## Overview

The Dwell Time Policy is a sophisticated temporal filtering component that tracks object persistence over time and triggers events based on loitering or dwell time thresholds. This policy is essential for surveillance applications requiring detection of prolonged presence, abandoned objects, or persistent activities in monitored areas.

## Component Structure

### Component Identity
- **Component ID**: `dwell_time`
- **Policy ID**: `pol-dwell-time`
- **Category**: temporal_filter
- **Framework**: Python
- **License**: MIT

### Policy Purpose
- **Primary Function**: Temporal state tracking and loitering detection
- **Intended Use**: Detect prolonged presence, abandoned objects, persistent activities
- **Computational Complexity**: O(n) where n = number of tracked objects
- **Processing Type**: Temporal state tracking with memory persistence

### Input/Output Configuration
- **Input Formats**: OD1
- **Output Formats**: OD1
- **Consumes**: Tracked detections with timestamps
- **Produces**: Loitering alerts, dwell time metadata, temporal state

## Configuration Parameters

### Core Temporal Settings
1. **Loitering Threshold (`loiteringThresholdSeconds`)**
   - **Type**: Integer
   - **Required**: Yes
   - **Default**: 300 seconds (5 minutes)
   - **Range**: 10 - 3600 seconds
   - **Description**: Time threshold after which objects are considered loitering
   - **Use Cases**: Security (5-15 min), retail (2-5 min), airports (10-30 min)

2. **Reset Timeout (`resetSeconds`)**
   - **Type**: Integer
   - **Required**: Yes
   - **Default**: 30 seconds
   - **Range**: 5 - 300 seconds
   - **Description**: Time after which tracking state is reset if object disappears
   - **Purpose**: Handle temporary occlusions without losing tracking state

### Tracking Configuration
3. **Track ID Field (`track_id_field`)**
   - **Type**: String
   - **Default**: "track_id"
   - **Description**: Field name containing the tracking ID in detection objects
   - **Requirements**: Must be consistent with tracker output format

4. **Minimum Detection Confidence (`min_detection_confidence`)**
   - **Type**: Float
   - **Default**: 0.5
   - **Range**: 0.0 - 1.0
   - **Description**: Minimum confidence to count towards dwell time
   - **Purpose**: Filter out low-quality detections from time calculations

### Zone-Based Configuration
5. **Zone Specific (`zone_specific`)**
   - **Type**: Boolean
   - **Default**: False
   - **Description**: Whether to apply different thresholds per zone
   - **Use Cases**: Different sensitivities for restricted vs. public areas

6. **Zone Thresholds (`zone_thresholds`)**
   - **Type**: Dictionary
   - **Format**: `{"zone_name": threshold_seconds}`
   - **Default**: {} (empty)
   - **Example**: `{"restricted_area": 60, "lobby": 600, "entrance": 120}`
   - **Purpose**: Zone-specific loitering thresholds

### Dynamic Configuration
- **Runtime Updates**: Supported
- **Updateable Parameters**: loiteringThresholdSeconds, resetSeconds, zone_thresholds, min_detection_confidence
- **Update Latency**: 15ms
- **API Endpoints**:
  - `/api/v1/policies/dwell_time/update_parameters`
  - `/api/v1/policies/dwell_time/update_zone_thresholds`

## Performance Characteristics

### Processing Performance
- **Objects Tracked Simultaneously**: 1,000+
- **State Updates per Second**: 10,000
- **Memory per Tracked Object**: 2KB
- **CPU Intensive**: No
- **GPU Required**: No

### Temporal Accuracy
- **Timing Precision**: 100ms
- **State Persistence**: 99.9%
- **False Positive Rate**: <1%
- **Memory Growth**: Linear with unique track IDs

## System Requirements

### Hardware Requirements
- **CPU**: Any modern CPU
- **RAM**: 200MB minimum (grows with tracked objects)
- **GPU**: Not required
- **Storage**: Minimal

### Software Environment
- **Python Version**: 3.6+
- **Dependencies**: Python standard library (collections)
- **Framework**: Pure Python implementation

## Algorithm Logic

### State Tracking Process
1. **Object Detection**: Receive tracked objects with timestamps
2. **State Initialization**: Create new tracking state for unseen track IDs
3. **Time Accumulation**: Update dwell time for existing objects
4. **Confidence Filtering**: Only count high-confidence detections
5. **Threshold Evaluation**: Check against loitering thresholds
6. **Alert Generation**: Trigger alerts when thresholds exceeded
7. **State Cleanup**: Reset states for disappeared objects

### Temporal State Management
- **First Seen**: Record initial detection timestamp
- **Last Seen**: Update with most recent detection
- **Accumulated Time**: Total time object has been present
- **Alert Status**: Whether loitering alert has been triggered
- **Zone Context**: Current zone for zone-specific thresholds

## Use Case Applications

### Primary Applications
1. **Security Surveillance**: Detect loitering in restricted areas
2. **Retail Analytics**: Monitor customer dwell times in store sections
3. **Airport Security**: Identify abandoned luggage or prolonged presence
4. **Public Spaces**: Monitor suspicious lingering behavior
5. **Parking Enforcement**: Detect overstaying in time-limited zones
6. **Manufacturing**: Monitor worker presence in safety-critical areas

### Domain-Specific Scenarios
- **Bank ATMs**: Detect prolonged presence near ATMs
- **School Grounds**: Monitor unauthorized presence after hours
- **Hospital Areas**: Track patient/visitor dwell times
- **Transportation Hubs**: Abandoned object detection
- **Corporate Buildings**: Monitor access control compliance

## Configuration Examples

#### High-Security Area (Short Threshold)
```json
{
  "loiteringThresholdSeconds": 60,
  "resetSeconds": 15,
  "zone_specific": true,
  "zone_thresholds": {
    "restricted_area": 30,
    "secure_entrance": 45
  },
  "min_detection_confidence": 0.7
}
```

#### Retail Store (Moderate Threshold)
```json
{
  "loiteringThresholdSeconds": 300,
  "resetSeconds": 30,
  "zone_specific": true,
  "zone_thresholds": {
    "electronics": 180,
    "jewelry": 120,
    "general": 300
  },
  "min_detection_confidence": 0.5
}
```

#### Public Space (Long Threshold)
```json
{
  "loiteringThresholdSeconds": 900,
  "resetSeconds": 60,
  "zone_specific": false,
  "zone_thresholds": {},
  "min_detection_confidence": 0.4
}
```

#### Airport Terminal (Zone-Specific)
```json
{
  "loiteringThresholdSeconds": 600,
  "resetSeconds": 45,
  "zone_specific": true,
  "zone_thresholds": {
    "departure_gate": 1800,
    "security_checkpoint": 300,
    "baggage_claim": 1200,
    "customs": 600
  },
  "min_detection_confidence": 0.6
}
```

## Integration Guidelines

### Pipeline Placement
- **Position**: After object tracking, before alert generation
- **Before**: Alert systems, notification services
- **After**: Object detection, tracking, zone filtering
- **Dependencies**: Requires consistent tracking IDs

### Data Flow Architecture
1. **Input**: Tracked objects with timestamps and IDs
2. **State Management**: Maintain temporal state for each track ID
3. **Time Calculation**: Accumulate presence time per object
4. **Threshold Evaluation**: Compare against configured thresholds
5. **Alert Generation**: Trigger loitering alerts when thresholds exceeded
6. **Output**: Enhanced objects with dwell time metadata and alerts

### Performance Optimization
1. **Memory Management**: Implement periodic cleanup of old states
2. **Batch Processing**: Process multiple objects efficiently
3. **Zone Optimization**: Use zone-specific thresholds for different sensitivities
4. **Confidence Filtering**: Filter low-quality detections early

## Technical Notes

### Implementation Details
- **State Storage**: In-memory dictionary with track ID keys
- **Time Calculation**: Epoch-based timestamp arithmetic
- **Thread Safety**: Requires synchronization for concurrent access
- **Memory Growth**: Linear with number of unique track IDs

### Quality Considerations
- **Clock Synchronization**: Ensure consistent timestamps across system
- **Tracking Quality**: Depends on upstream tracker reliability
- **False Positives**: Can occur with tracker ID switches
- **Memory Leaks**: Implement cleanup for disappeared objects

### Limitations
- **Tracker Dependency**: Requires consistent track IDs from upstream
- **Memory Growth**: State grows with number of unique objects
- **Clock Dependency**: Requires synchronized system clocks
- **ID Switches**: Tracker ID changes reset dwell time

### Best Practices
1. **Threshold Tuning**: Adjust based on specific use case requirements
2. **Zone Configuration**: Use zone-specific thresholds for different areas
3. **Confidence Filtering**: Set appropriate confidence thresholds
4. **Memory Management**: Implement periodic state cleanup
5. **Testing**: Validate timing accuracy with known test scenarios

### Ethical Considerations
- **Privacy**: Loitering detection may raise privacy concerns
- **Bias**: Ensure fair application across different demographics
- **Transparency**: Document usage policies and thresholds
- **Proportionality**: Use appropriate thresholds for context

### Common Use Patterns
- **Security Applications**: Short thresholds (30-120 seconds)
- **Retail Analytics**: Medium thresholds (2-10 minutes)
- **Public Spaces**: Long thresholds (10-30 minutes)
- **Transportation**: Variable thresholds by area type

This Dwell Time Policy provides essential temporal analysis capabilities for surveillance and monitoring applications, enabling sophisticated loitering detection and presence analysis while maintaining high performance and configurability.
