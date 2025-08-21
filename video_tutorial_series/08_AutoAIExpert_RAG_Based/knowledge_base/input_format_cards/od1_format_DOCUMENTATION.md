# OD1 Format Documentation

## Overview
This document describes the `od1_format.json` specification, which defines the OD1 (Object Detection format 1) - the standard data structure used throughout computer vision pipelines for object detection, tracking, and analysis.

## Format Identity

### Component Information
- **Component ID**: `od1_input_format`
- **Component Type**: `node.algorithm.format`
- **Format ID**: `fmt-od1-in`
- **Name**: OD1 Bounding-Box Input
- **Domain**: Generic Vision
- **Schema Version**: 1.1

### Description
Standard OD1 list-of-lists schema used as INPUT to CV modules (detectors, filters, trackers, etc.). This format serves as the universal data interchange format for object-based computer vision pipelines.

## Schema Structure

### Field Organization
The OD1 format consists of 9 core fields arranged in a specific order:

```json
[
  "class",      // Object classification
  "score",      // Confidence score
  "zone",       // Current zone/ROI
  "path",       // Data lineage
  "id",         // Tracking identifier
  "roi",        // Bounding box coordinates
  "polygon",    // Detailed shape
  "timestamp",  // Temporal information
  "props"       // Extended properties
]
```

## Field Specifications

### 1. Class (`class`)
- **Type**: String
- **Description**: Object classification label
- **Examples**: `"person"`, `"car"`, `"bicycle"`, `"Fall"`, `"luggage"`
- **Usage**: Primary object category for filtering and logic

### 2. Score (`score`)
- **Type**: Float
- **Range**: 0.0 - 1.0
- **Description**: Detection confidence score
- **Example**: `0.92`
- **Usage**: Quality filtering, threshold-based decisions

### 3. Zone (`zone`)
- **Type**: String
- **Description**: Current ROI/zone name where object is located
- **Examples**: `"entrance_zone"`, `"ZoneSnatch"`, `"parking_area"`
- **Usage**: Spatial filtering, zone-based policies

### 4. Path (`path`)
- **Type**: String
- **Format**: Comma-separated lineage
- **Description**: Complete data lineage from source to current stage
- **Example**: `"cam01,rtsp://surveillance_stream"`
- **Usage**: Traceability, multi-camera systems

### 5. ID (`id`)
- **Type**: String
- **Description**: Unique tracker identifier
- **Note**: Empty string if tracking ID not yet assigned
- **Examples**: `"person_001"`, `"vehicle_042"`, `""`
- **Usage**: Object tracking, temporal analysis

### 6. ROI (`roi`)
- **Type**: List of integers
- **Format**: `[x1, y1, x2, y2]`
- **Description**: Bounding box coordinates (top-left, bottom-right)
- **Example**: `[150, 200, 300, 500]`
- **Usage**: Spatial analysis, overlap detection

### 7. Polygon (`polygon`)
- **Type**: List of coordinate pairs
- **Format**: `[[x,y], [x,y], ...]`
- **Description**: Detailed object boundary polygon
- **Example**: `[[150,200],[300,200],[300,500],[150,500]]`
- **Usage**: Precise shape analysis, advanced spatial operations

### 8. Timestamp (`timestamp`)
- **Type**: Float
- **Format**: Epoch milliseconds
- **Description**: Detection time
- **Example**: `1718263400.123`
- **Usage**: Temporal analysis, sequence detection

### 9. Props (`props`)
- **Type**: Dictionary
- **Description**: Extended properties and metadata
- **Usage**: Rich contextual information

## Extended Properties Specifications

### Pose Keypoints (`pose_keypoints`)
- **Format**: List of `[x, y, confidence]` for each keypoint
- **Keypoint Order**: 
  ```
  ["nose", "left_eye", "right_eye", "left_ear", "right_ear", 
   "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", 
   "left_wrist", "right_wrist", "left_hip", "right_hip", 
   "left_knee", "right_knee", "left_ankle", "right_ankle"]
  ```
- **Example**: `[[320, 240, 0.9], [315, 235, 0.8], ...]`
- **Use Cases**: Pose analysis, interaction detection, activity recognition

### Dwell Time (`dwell_time`)
- **Format**: Float (seconds)
- **Description**: Time spent in current zone
- **Example**: `45.2`
- **Use Cases**: Loitering detection, dwell analysis

### Color Information (`color`)
- **Format**: Dictionary with dominant colors
- **Example**: `{"shirt": "blue", "pants": "black"}`
- **Use Cases**: Person re-identification, appearance matching

### Age Estimation (`age`)
- **Format**: Dictionary with age analysis
- **Example**: 
  ```json
  {
    "estimated_age": 25, 
    "age_range": "20-30", 
    "confidence": 0.8
  }
  ```
- **Use Cases**: Demographic analysis, age verification

### Gender Classification (`gender`)
- **Format**: Dictionary with gender information
- **Example**: `{"gender": "female", "confidence": 0.9}`
- **Use Cases**: Demographic analysis, gender-specific policies

### Action Recognition (`actions`)
- **Format**: List of detected actions
- **Example**: `["walking", "waving"]`
- **Use Cases**: Activity recognition, behavior analysis

### Speed Measurement (`speed_kph`)
- **Format**: Float (kilometers per hour)
- **Example**: `18.5`
- **Use Cases**: Speed monitoring, traffic analysis

### Movement Direction (`direction`)
- **Format**: Dictionary with directional information
- **Example**: `{"angle": 45, "direction": "northeast"}`
- **Use Cases**: Flow analysis, directional filtering

### Facial Features (`facial_features`)
- **Format**: Dictionary with facial analysis
- **Example**: 
  ```json
  {
    "emotion": "happy", 
    "mask_wearing": true, 
    "facial_landmarks": [[x1,y1], ...]
  }
  ```
- **Use Cases**: Emotion detection, mask compliance, face recognition

## Complete Example

```json
[
  "person",                                    // Class
  0.92,                                       // Score
  "entrance_zone",                            // Zone
  "cam01,rtsp://surveillance_stream",         // Path
  "person_001",                               // ID
  [150, 200, 300, 500],                      // ROI
  [[150,200],[300,200],[300,500],[150,500]], // Polygon
  1718263400.123,                            // Timestamp
  {                                          // Props
    "pose_keypoints": [
      [250, 220, 0.9], [245, 215, 0.8], [255, 215, 0.85],
      [240, 210, 0.7], [260, 210, 0.75], [230, 250, 0.95],
      [270, 250, 0.93], [220, 280, 0.88], [280, 280, 0.90],
      [210, 310, 0.85], [290, 310, 0.87], [240, 350, 0.92],
      [260, 350, 0.94], [235, 420, 0.89], [265, 420, 0.91],
      [230, 480, 0.86], [270, 480, 0.88]
    ],
    "dwell_time": 12.5,
    "gender": {"gender": "male", "confidence": 0.87},
    "age": {"estimated_age": 35, "age_range": "30-40", "confidence": 0.82},
    "actions": ["standing", "looking_around"],
    "color": {"shirt": "blue", "pants": "black"}
  }
]
```

## Data Contract

### Input Requirements
- **Consumes**: `["od1_list"]`
- **Format Compatibility**: Modules consuming this format should declare `consumes:["od1_list"]`

### Output Specifications
- **Produces**: `[]` (This is an input format specification)
- **Pipeline Role**: Defines the standard for data flowing between pipeline components

## Usage Patterns

### In Object Detection
```json
[
  "car", 0.89, "road_zone", "cam02", "", 
  [400, 300, 600, 450], 
  [[400,300],[600,300],[600,450],[400,450]], 
  1718263401.456, 
  {}
]
```

### In Tracking Systems
```json
[
  "person", 0.85, "corridor", "cam01", "track_123", 
  [200, 150, 350, 400], 
  [[200,150],[350,150],[350,400],[200,400]], 
  1718263402.789, 
  {"dwell_time": 5.2, "speed_kph": 3.1}
]
```

### In Behavior Analysis
```json
[
  "person", 0.93, "loitering_zone", "cam03", "person_456", 
  [100, 100, 250, 350], 
  [[100,100],[250,100],[250,350],[100,350]], 
  1718263403.012, 
  {
    "dwell_time": 125.8,
    "actions": ["standing", "looking_around"],
    "pose_keypoints": [...],
    "age": {"estimated_age": 42, "confidence": 0.75}
  }
]
```

## Pipeline Integration

### Automatic Compatibility
The OD1 format enables automatic pipeline wiring through:
- **Producer/Consumer Matching**: Components declare what they produce/consume
- **Format Validation**: Automatic schema validation
- **Data Transformation**: Automatic format conversion where needed

### Common Pipeline Flows
```
Object Detector → OD1 → Tracker → OD1 → Policy Filter → OD1 → Usecase Logic
```

### Multi-Modal Integration
```
Video → Object Detector → OD1 ┐
                              ├→ Feature Fusion → OD1 → Analytics
Audio → Audio Processor → AD1 ┘
```

## Best Practices

### Performance Optimization
1. **Minimal Props**: Only include necessary properties
2. **Efficient Serialization**: Use appropriate JSON libraries
3. **Batch Processing**: Process multiple OD1 entries together
4. **Memory Management**: Clean up expired tracking data

### Data Quality
1. **Validation**: Verify field types and ranges
2. **Consistency**: Maintain consistent naming conventions
3. **Completeness**: Ensure required fields are populated
4. **Accuracy**: Validate spatial and temporal consistency

### Security & Privacy
1. **Data Sanitization**: Remove sensitive information when appropriate
2. **Access Control**: Implement appropriate data access controls
3. **Retention Policies**: Follow data retention guidelines
4. **Anonymization**: Consider anonymizing tracking IDs when possible

## Error Handling

### Common Issues
- **Missing Fields**: Handle incomplete OD1 entries gracefully
- **Invalid Coordinates**: Validate ROI boundaries
- **Timestamp Issues**: Handle clock synchronization problems
- **Type Mismatches**: Validate data types before processing

### Validation Rules
```python
def validate_od1_entry(entry):
    assert len(entry) == 9, "OD1 must have 9 fields"
    assert isinstance(entry[0], str), "Class must be string"
    assert 0 <= entry[1] <= 1, "Score must be 0-1"
    assert len(entry[5]) == 4, "ROI must be [x1,y1,x2,y2]"
    assert isinstance(entry[8], dict), "Props must be dictionary"
```

## Version History

### Version 1.1 (Current)
- Added extended properties specifications
- Enhanced pose keypoint definitions
- Improved documentation and examples
- Added facial features support

### Version 1.0
- Initial OD1 format specification
- Basic 9-field structure
- Core properties support

## References
- AIOS Pipeline Framework Documentation
- Computer Vision Data Standards
- Object Detection Best Practices
- Tracking Algorithm Integration Guidelines

## Notes
Modules that consume this format should declare `consumes:["od1_list"]` so compatibility edges can be generated automatically for pipeline composition and validation.
