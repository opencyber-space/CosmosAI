# OD1 Input Format Card Documentation

**File**: `od1_format.json`  
**Component Type**: `node.algorithm.format`  
**Format Name**: OD1 Bounding-Box Input  

## Overview

The OD1 (Object Detection Format 1) is the standardized input format used throughout the computer vision pipeline for representing detected objects, their properties, and associated metadata. This schema provides a comprehensive, extensible structure for passing object information between different components in the processing pipeline.

## Format Structure

### Component Identity
- **Component ID**: `od1_input_format`
- **Format ID**: `fmt-od1-in`
- **Schema Version**: 1.1
- **Domain**: Generic vision applications

### Core Schema
The OD1 format is structured as a list of lists, where each inner list represents a detected object with 9 standardized fields:

```python
[class, score, zone, path, id, roi, polygon, timestamp, props]
```

## Field Specifications

### 1. Class (`str`)
- **Description**: Object classification label
- **Format**: String
- **Examples**: "person", "car", "bicycle", "bag"
- **Use Cases**: Object filtering, category-based processing

### 2. Score (`float`)
- **Description**: Detection confidence score
- **Format**: Float (0.0 - 1.0)
- **Examples**: 0.92, 0.75, 0.88
- **Use Cases**: Confidence filtering, quality assessment

### 3. Zone (`str`)
- **Description**: Current ROI/zone name where object is located
- **Format**: String
- **Examples**: "entrance_zone", "parking_area", "restricted_zone"
- **Use Cases**: Zone-based filtering, spatial analysis

### 4. Path (`str`)
- **Description**: Comma-separated lineage of zones/streams
- **Format**: String (comma-separated)
- **Examples**: "cam01,rtsp://surveillance_stream", "zone1,zone2,zone3"
- **Use Cases**: Object trajectory tracking, source identification

### 5. ID (`str`)
- **Description**: Tracker-assigned unique identifier
- **Format**: String (empty if not yet assigned)
- **Examples**: "person_001", "vehicle_042", ""
- **Use Cases**: Multi-object tracking, identity consistency

### 6. ROI (`list`)
- **Description**: Bounding box coordinates
- **Format**: [x1, y1, x2, y2] - top-left and bottom-right corners
- **Examples**: [150, 200, 300, 500]
- **Use Cases**: Object localization, spatial analysis

### 7. Polygon (`list`)
- **Description**: Polygon representation of object region
- **Format**: [[x,y], [x,y], ...] - list of coordinate pairs
- **Examples**: [[150,200],[300,200],[300,500],[150,500]]
- **Use Cases**: Precise object boundaries, overlap analysis

### 8. Timestamp (`float`)
- **Description**: Detection timestamp in epoch milliseconds
- **Format**: Float (epoch-ms)
- **Examples**: 1718263400.123
- **Use Cases**: Temporal analysis, event sequencing

### 9. Props (`dict`)
- **Description**: Arbitrary key-value pairs for extended properties
- **Format**: Dictionary
- **Use Cases**: Algorithm-specific metadata, analysis results

## Properties Specifications

The `props` field supports various standardized extensions:

### Pose Analysis
- **pose_keypoints**: 17-point COCO keypoints with confidence
- **Format**: `[[x, y, confidence], ...]` for each keypoint
- **Order**: nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles
- **Use Cases**: Activity recognition, interaction detection

### Temporal Analysis
- **dwell_time**: Seconds spent in current zone
- **Format**: Float (seconds)
- **Example**: 45.2
- **Use Cases**: Loitering detection, dwell analysis

### Appearance Analysis
- **color**: Dominant color information
- **Format**: `{"clothing_item": "color"}`
- **Example**: `{"shirt": "blue", "pants": "black"}`
- **Use Cases**: Person re-identification, appearance matching

### Demographic Analysis
- **age**: Age estimation with confidence
- **Format**: `{"estimated_age": int, "age_range": str, "confidence": float}`
- **Example**: `{"estimated_age": 35, "age_range": "30-40", "confidence": 0.82}`

- **gender**: Gender classification with confidence
- **Format**: `{"gender": str, "confidence": float}`
- **Example**: `{"gender": "male", "confidence": 0.87}`

### Behavioral Analysis
- **actions**: List of detected activities
- **Format**: List of strings
- **Example**: `["walking", "waving", "standing"]`
- **Use Cases**: Activity recognition, behavior analysis

### Motion Analysis
- **speed_kph**: Object speed in kilometers per hour
- **Format**: Float
- **Example**: 18.5
- **Use Cases**: Speed monitoring, traffic analysis

- **direction**: Movement direction information
- **Format**: `{"angle": float, "direction": str}`
- **Example**: `{"angle": 45, "direction": "northeast"}`

### Facial Analysis
- **facial_features**: Comprehensive facial analysis
- **Format**: Dictionary with multiple facial attributes
- **Example**: `{"emotion": "happy", "mask_wearing": true, "facial_landmarks": [[x1,y1], ...]}`
- **Use Cases**: Emotion detection, mask compliance, face recognition

## Example Object

```json
[
  "person",
  0.92,
  "entrance_zone",
  "cam01,rtsp://surveillance_stream",
  "person_001",
  [150, 200, 300, 500],
  [[150,200],[300,200],[300,500],[150,500]],
  1718263400.123,
  { 
    "pose_keypoints": [[250, 220, 0.9], [245, 215, 0.8], ...],
    "dwell_time": 12.5,
    "gender": {"gender": "male", "confidence": 0.87},
    "age": {"estimated_age": 35, "age_range": "30-40", "confidence": 0.82},
    "actions": ["standing", "looking_around"],
    "color": {"shirt": "blue", "pants": "black"}
  }
]
```

## Integration Guidelines

### Component Compatibility
- **Consumers**: Components that process OD1 lists should declare `consumes: ["od1_list"]`
- **Producers**: Components that output OD1 format should declare `produces: ["od1_list"]`
- **Compatibility**: Automatic edge generation based on format compatibility

### Data Flow
1. **Input**: Raw detection results from object detection models
2. **Processing**: Various pipeline components add/modify fields
3. **Enhancement**: Components enrich props with analysis results
4. **Output**: Comprehensive object information for downstream processing

### Field Handling
- **Mandatory Fields**: All 9 core fields must be present
- **Optional Props**: Props field can be empty dictionary
- **Empty Values**: Use appropriate empty values (empty string for ID, empty dict for props)
- **Type Safety**: Maintain strict type consistency across pipeline

## Use Case Applications

### Surveillance Systems
- **Object Tracking**: Use ID field for consistent tracking
- **Zone Monitoring**: Use zone field for area-based alerts
- **Behavioral Analysis**: Use props for activity detection

### Traffic Monitoring
- **Vehicle Detection**: Class field for vehicle types
- **Speed Analysis**: Props.speed_kph for speed monitoring
- **Direction Analysis**: Props.direction for traffic flow

### Retail Analytics
- **Customer Tracking**: ID field for shopping behavior
- **Demographics**: Props.age/gender for customer analysis
- **Dwell Time**: Props.dwell_time for engagement metrics

### Security Applications
- **Person Detection**: Class field for person identification
- **Facial Analysis**: Props.facial_features for identity verification
- **Pose Analysis**: Props.pose_keypoints for activity recognition

## Technical Notes

### Performance Considerations
- **Memory Efficiency**: Compact representation for high-throughput scenarios
- **Serialization**: JSON-compatible for network transmission
- **Extensibility**: Props field allows for domain-specific extensions
- **Compatibility**: Backward compatible across schema versions

### Quality Assurance
- **Validation**: Implement schema validation for data integrity
- **Type Checking**: Ensure proper data types for all fields
- **Completeness**: Verify all mandatory fields are present
- **Consistency**: Maintain consistent coordinate systems and units

### Best Practices
1. **Coordinate System**: Use consistent pixel coordinates
2. **Timestamp Precision**: Use epoch milliseconds for temporal accuracy
3. **ID Management**: Ensure unique IDs within tracking sessions
4. **Props Organization**: Group related properties logically
5. **Documentation**: Document custom props extensions

This OD1 format provides the foundation for all object information exchange in the computer vision pipeline, enabling seamless integration between detection, tracking, analysis, and downstream processing components.
