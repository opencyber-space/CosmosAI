# OD1 Output Format Documentation

## Overview

The OD1 (Object Detection 1) Output Format is the standardized output schema used throughout the computer vision pipeline ecosystem for emitting detection, tracking, and analysis results. This comprehensive format supports rich metadata through an extensible props system, enabling complex multi-stage pipelines to progressively enrich detection data with pose estimation, demographic analysis, tracking information, and behavioral insights.

The OD1 output format serves as the universal data contract between pipeline components, allowing seamless integration of detectors, trackers, and post-processors while maintaining compatibility across different analysis modules.

## Format Identity

- **Component ID**: `od1_output_format`
- **Component Type**: `node.algorithm.format`
- **Format ID**: `fmt-od1-out`
- **Format Name**: OD1 Bounding-Box Output
- **Schema Version**: 1.1
- **Domain**: Generic Vision
- **Category**: Output Format Specification

## Core Data Structure

### Standard OD1 List Format
```python
[
  [class, score, zone, path, id, roi, polygon, timestamp, props],
  [class, score, zone, path, id, roi, polygon, timestamp, props],
  # ... additional detections
]
```

### Field Specifications

#### 1. Class (`class`)
- **Type**: String
- **Description**: Object classification label
- **Examples**: `"person"`, `"car"`, `"truck"`, `"suitcase"`
- **Source**: Object detection models (YOLOv7, YOLOv8, etc.)

#### 2. Score (`score`)
- **Type**: Float
- **Range**: 0.0 - 1.0
- **Description**: Detection confidence score
- **Usage**: Quality filtering and decision thresholds

#### 3. Zone (`zone`)
- **Type**: String
- **Description**: Current ROI/zone name where object is detected
- **Examples**: `"entrance_zone"`, `"restricted_area"`, `"parking_lot"`
- **Source**: Zone filtering policies

#### 4. Path (`path`)
- **Type**: String
- **Description**: Comma-separated lineage of zones/streams
- **Format**: `"camera_id,stream_url,zone_history"`
- **Example**: `"cam01,rtsp://surveillance_stream"`
- **Usage**: Tracking object movement through pipeline stages

#### 5. ID (`id`)
- **Type**: String
- **Description**: Tracker-assigned unique identifier
- **Note**: **Empty string if not yet assigned by tracker**
- **Examples**: `"person_001"`, `"vehicle_123"`, `""`
- **Source**: Object tracking algorithms (ByteTrack, FastMOT, V-IOU)

#### 6. ROI (`roi`)
- **Type**: List of integers
- **Format**: `[x1, y1, x2, y2]`
- **Description**: Bounding box coordinates (top-left and bottom-right)
- **Coordinate System**: Pixel coordinates in source image
- **Example**: `[150, 200, 300, 500]`

#### 7. Polygon (`polygon`)
- **Type**: List of coordinate pairs
- **Format**: `[[x1, y1], [x2, y2], [x3, y3], [x4, y4]]`
- **Description**: Polygon representation of detection region
- **Usage**: More precise spatial representation than bounding box
- **Example**: `[[150,200],[300,200],[300,500],[150,500]]`

#### 8. Timestamp (`timestamp`)
- **Type**: Float
- **Description**: Detection timestamp in epoch milliseconds
- **Example**: `1718263400.123`
- **Usage**: Temporal analysis and synchronization

#### 9. Props (`props`)
- **Type**: Dictionary
- **Description**: Extensible metadata container for analysis results
- **Usage**: Rich data enrichment from various pipeline components

## Props Specifications

### Pose Analysis Props

#### Pose Keypoints (`pose_keypoints`)
- **Format**: List of `[x, y, confidence]` for each keypoint
- **Keypoint Order**: 17 COCO keypoints
  1. `nose`, `left_eye`, `right_eye`, `left_ear`, `right_ear`
  2. `left_shoulder`, `right_shoulder`, `left_elbow`, `right_elbow`
  3. `left_wrist`, `right_wrist`, `left_hip`, `right_hip`
  4. `left_knee`, `right_knee`, `left_ankle`, `right_ankle`
- **Example**: `[[320, 240, 0.9], [315, 235, 0.8], ...]`
- **Produced By**: `pose_estimation_models`, `yolov7_pose`
- **Use Cases**: Pose analysis, interaction detection, activity recognition

### Temporal Analysis Props

#### Dwell Time (`dwell_time`)
- **Format**: Float (seconds spent in current zone)
- **Example**: `45.2`
- **Produced By**: `dwell_time_policy`, `loitering_detection`
- **Use Cases**: Loitering detection, presence analysis

### Appearance Analysis Props

#### Color Analysis (`color`)
- **Format**: Dictionary with dominant colors
- **Example**: `{"shirt": "blue", "pants": "black"}`
- **Produced By**: `color_analysis_models`, `appearance_extractors`
- **Use Cases**: Person re-identification, appearance matching

### Demographic Analysis Props

#### Age Estimation (`age`)
- **Format**: Dictionary with age estimation
- **Example**: `{"estimated_age": 25, "age_range": "20-30", "confidence": 0.8}`
- **Produced By**: `age_estimation_models`, `demographic_analyzers`
- **Use Cases**: Demographic analysis, age verification

#### Gender Classification (`gender`)
- **Format**: Dictionary with gender classification
- **Example**: `{"gender": "female", "confidence": 0.9}`
- **Produced By**: `gender_classification_models`, `demographic_analyzers`
- **Use Cases**: Demographic analysis, gender-specific policies

### Motion Analysis Props

#### Speed Calculation (`speed_kph`)
- **Format**: Float (speed in kilometers per hour)
- **Example**: `18.5`
- **Produced By**: `tracking_models`, `speed_calculation_policies`
- **Use Cases**: Speed monitoring, traffic analysis

#### Direction Analysis (`direction`)
- **Format**: Dictionary with movement direction
- **Example**: `{"angle": 45, "direction": "northeast"}`
- **Produced By**: `tracking_models`, `directional_analyzers`
- **Use Cases**: Flow analysis, directional filtering

### Behavioral Analysis Props

#### Action Recognition (`actions`)
- **Format**: List of detected actions
- **Example**: `["walking", "waving"]`
- **Produced By**: `action_recognition_models`, `interaction_policy`
- **Use Cases**: Activity recognition, behavior analysis

#### Interaction Detection (`interaction_detected`)
- **Format**: Boolean (whether interaction was detected)
- **Example**: `true`
- **Produced By**: `interaction_policy`, `pose_analysis_policies`
- **Use Cases**: Interaction monitoring, social distancing

#### Activity Confidence (`activity_confidence`)
- **Format**: Float (confidence score for detected activity)
- **Example**: `0.85`
- **Produced By**: `interaction_policy`, `activity_recognition_models`
- **Use Cases**: Activity validation, confidence filtering

### Facial Analysis Props

#### Facial Features (`facial_features`)
- **Format**: Dictionary with facial analysis results
- **Example**: `{"emotion": "happy", "mask_wearing": true, "facial_landmarks": [[x1,y1], ...]}`
- **Produced By**: `facial_recognition_models`, `emotion_detection_models`
- **Use Cases**: Emotion detection, mask compliance, face recognition

## Example Output Structure

```json
[
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
      "color": {"shirt": "blue", "pants": "black"},
      "interaction_detected": false,
      "activity_confidence": 0.78
    }
  ]
]
```

## Data Contract

### Producers
Components that generate OD1 output should declare:
```json
{
  "produces": ["od1_list"]
}
```

### Consumers
Components that process OD1 data typically declare:
```json
{
  "consumes": ["od1_list"]
}
```

### Pipeline Flow
```
Detection → Tracking → Zone Analysis → Pose Estimation → Demographic Analysis → Output
   |           |           |              |                    |
   OD1      OD1+ID    OD1+zone        OD1+pose           OD1+demographics
```

## Usage Guidelines

### Data Enrichment Pattern
1. **Initial Detection**: Basic OD1 with class, score, roi, timestamp
2. **Tracking Enhancement**: Add tracking ID and path information
3. **Spatial Analysis**: Add zone information and polygon data
4. **Feature Extraction**: Add pose, appearance, and demographic props
5. **Behavioral Analysis**: Add interaction and activity analysis

### Props Management Best Practices
1. **Modular Enrichment**: Each component adds specific props
2. **Backward Compatibility**: Preserve existing props when adding new ones
3. **Optional Props**: Handle missing props gracefully
4. **Validation**: Validate props format before processing
5. **Performance**: Consider props size impact on pipeline performance

### Error Handling
```python
# Safe props access pattern
def get_pose_keypoints(detection):
    props = detection[8] if len(detection) > 8 else {}
    return props.get('pose_keypoints', [])

def get_tracker_id(detection):
    return detection[4] if len(detection) > 4 and detection[4] else None
```

## Integration Notes

### Pipeline Component Integration
1. **Detectors**: Produce basic OD1 format with class, score, roi
2. **Trackers**: Enrich with ID and maintain temporal consistency
3. **Policies**: Add zone, path, and filtering results
4. **Analyzers**: Enrich props with specialized analysis results

### Performance Considerations
1. **Memory Usage**: Props can significantly increase memory usage
2. **Serialization**: JSON serialization overhead for complex props
3. **Network Transfer**: Consider props size for distributed pipelines
4. **Processing Speed**: Balance between rich data and processing speed

### Compatibility Guidelines
1. **Version Management**: Handle different schema versions gracefully
2. **Props Evolution**: Add new props without breaking existing consumers
3. **Field Order**: Maintain standard field order for compatibility
4. **Type Consistency**: Ensure consistent data types across components

## Common Integration Patterns

### Detection to Tracking
```python
# Tracker enriches OD1 with ID
def enrich_with_tracking(od1_detection, track_id):
    od1_detection[4] = track_id  # Set tracker ID
    return od1_detection
```

### Zone Analysis
```python
# Zone policy adds zone information
def enrich_with_zone(od1_detection, zone_name):
    od1_detection[2] = zone_name  # Set zone
    return od1_detection
```

### Props Enrichment
```python
# Pose estimation adds keypoints to props
def enrich_with_pose(od1_detection, keypoints):
    props = od1_detection[8] or {}
    props['pose_keypoints'] = keypoints
    od1_detection[8] = props
    return od1_detection
```

## Validation and Quality Assurance

### Format Validation
```python
def validate_od1_format(detection):
    required_fields = 9
    if len(detection) < required_fields:
        return False
    
    # Validate field types
    if not isinstance(detection[0], str):  # class
        return False
    if not isinstance(detection[1], (int, float)):  # score
        return False
    if not isinstance(detection[5], list) or len(detection[5]) != 4:  # roi
        return False
    
    return True
```

### Props Validation
```python
def validate_pose_props(props):
    if 'pose_keypoints' in props:
        keypoints = props['pose_keypoints']
        if len(keypoints) != 17:  # COCO format
            return False
        for kp in keypoints:
            if len(kp) != 3:  # [x, y, confidence]
                return False
    return True
```

This OD1 Output Format provides a comprehensive, extensible framework for computer vision pipeline data exchange, enabling rich multi-stage analysis while maintaining compatibility and performance across diverse pipeline components.
