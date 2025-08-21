# YOLO to OD1 Converter Documentation

## Overview
This document describes the `yolo_to_od1_converter.json` specification, which defines a format converter that transforms YOLO detection format into the standardized OD1 format used throughout AIOS computer vision pipelines.

## Converter Identity

### Component Information
- **Component ID**: `yolo_to_od1_converter`
- **Component Type**: `node.algorithm.converter`
- **Converter ID**: `cnv-yolo-to-od1`
- **Label**: Converter
- **Name**: YOLO to OD1 Format Converter
- **Category**: Format Converter

### Description
Converts YOLO detection format to OD1 format with zone assignment capabilities. This converter bridges the gap between YOLO-based object detectors and zone-aware tracking and analysis systems.

## Format Mapping

### Input Format
- **Consumes**: `["yolo_format"]`
- **Input Formats**: `["yolo_format"]`

### Output Format
- **Produces**: `["od1_format"]`
- **Output Formats**: `["od1_format"]`

### Conversion Mapping
- **From**: `yolo_format`
- **To**: `od1_format`
- **Transform**: `bbox + confidence + class_id → bbox + confidence + zone_name`

## Conversion Process

### Input: YOLO Format
Typical YOLO detection output structure:
```python
{
  "detections": [
    {
      "bbox": [x_center, y_center, width, height],  # Normalized coordinates
      "confidence": 0.89,
      "class_id": 0,                                # Class index
      "class_name": "person"
    }
  ]
}
```

### Output: OD1 Format
Converted OD1 structure:
```python
[
  [
    "person",                    # class (string)
    0.89,                       # score (float)
    "entrance_zone",            # zone (string)
    "cam01,yolo_detector",      # path (string)
    "",                         # id (empty for new detections)
    [150, 200, 300, 500],      # roi [x1,y1,x2,y2] (absolute coords)
    [[150,200],[300,200],[300,500],[150,500]], # polygon
    1718263400.123,            # timestamp (epoch ms)
    {}                         # props (dict)
  ]
]
```

## Capabilities

### Core Conversion Features
1. **Format Conversion**: YOLO → OD1 structure transformation
2. **Zone Assignment**: Spatial zone mapping based on detection location
3. **Confidence Filtering**: Remove low-confidence detections
4. **Class Filtering**: Include only specified object classes

### Coordinate Transformation
- **Input**: Normalized YOLO coordinates (0-1 range)
- **Output**: Absolute pixel coordinates for OD1
- **Conversion**: 
  ```python
  x1 = (x_center - width/2) * image_width
  y1 = (y_center - height/2) * image_height
  x2 = (x_center + width/2) * image_width
  y2 = (y_center + height/2) * image_height
  ```

### Zone Assignment Logic
1. **Zone Detection**: Check if detection center falls within defined zones
2. **Zone Priority**: Assign to smallest enclosing zone (most specific)
3. **Default Zone**: Assign default zone if no specific zone matches
4. **Multi-Zone**: Handle overlapping zones with priority rules

## Configuration Parameters

### Confidence Threshold (`confidence_threshold`)
- **Type**: Float
- **Default**: 0.25
- **Range**: 0.0 - 1.0
- **Description**: Minimum confidence score to include detection
- **Usage**: Filter out low-quality detections

### Class Filter (`class_filter`)
- **Type**: List of integers
- **Default**: `[]` (empty = all classes)
- **Description**: List of YOLO class IDs to include in conversion
- **Example**: `[0, 2, 5]` (person, car, bus)
- **Usage**: Focus on specific object types

### Zone Definitions (`zones`)
- **Type**: Dictionary
- **Description**: Zone definitions with polygon coordinates
- **Format**:
  ```json
  {
    "zone_name": {
      "polygon": [[x1,y1], [x2,y2], [x3,y3], ...],
      "priority": 1
    }
  }
  ```
- **Example**:
  ```json
  {
    "entrance_zone": {
      "polygon": [[100,100], [500,100], [500,400], [100,400]],
      "priority": 1
    },
    "lobby_area": {
      "polygon": [[0,0], [800,0], [800,600], [0,600]],
      "priority": 2
    }
  }
  ```

## Use Cases

### 1. Converting YOLO Detections for Zone-Based Analysis
```python
# Input: YOLO detections
yolo_output = {
  "detections": [
    {"bbox": [0.3, 0.4, 0.2, 0.3], "confidence": 0.89, "class_id": 0}
  ]
}

# Output: Zone-aware OD1 format
od1_output = [
  ["person", 0.89, "entrance_zone", "cam01,yolo", "", 
   [200, 250, 400, 450], [...], timestamp, {}]
]
```

### 2. Preparing Detections for Tracking Systems
```python
# Chain: YOLO Detector → Converter → Tracker → Analytics
pipeline = [
  yolo_detector,          # Produces: yolo_format
  yolo_to_od1_converter,  # Converts: yolo_format → od1_format
  multi_object_tracker,   # Consumes: od1_format, Produces: od1_format
  behavior_analysis       # Consumes: od1_format
]
```

### 3. Adding Spatial Context to Raw Detection Outputs
```python
# Before conversion: Raw YOLO bbox
{"bbox": [0.5, 0.5, 0.3, 0.4], "class": "person"}

# After conversion: Contextualized OD1
["person", 0.89, "restricted_area", "cam02,yolo", "", 
 [350, 300, 650, 600], [...], timestamp, {}]
```

## Performance Characteristics

### Runtime Metrics
- **Latency**: 1.5 ms per detection
- **Memory Usage**: 10 MB (base memory footprint)
- **CPU Usage**: Low (primarily coordinate transformation)

### Scalability
- **Throughput**: 1000+ detections per second
- **Batch Processing**: Supports batch conversion
- **Memory Scaling**: Linear with number of detections

## Implementation Details

### Conversion Algorithm
```python
def convert_yolo_to_od1(yolo_detections, config):
    od1_list = []
    
    for detection in yolo_detections:
        # Filter by confidence
        if detection['confidence'] < config['confidence_threshold']:
            continue
            
        # Filter by class
        if config['class_filter'] and detection['class_id'] not in config['class_filter']:
            continue
            
        # Convert coordinates
        bbox_abs = yolo_to_absolute_coords(
            detection['bbox'], 
            config['image_width'], 
            config['image_height']
        )
        
        # Assign zone
        zone = assign_zone(bbox_abs, config['zones'])
        
        # Create OD1 entry
        od1_entry = [
            detection['class_name'],     # class
            detection['confidence'],     # score
            zone,                       # zone
            config['path'],             # path
            "",                         # id (empty)
            bbox_abs,                   # roi
            bbox_to_polygon(bbox_abs),  # polygon
            get_timestamp(),            # timestamp
            {}                          # props
        ]
        
        od1_list.append(od1_entry)
    
    return od1_list
```

### Zone Assignment Logic
```python
def assign_zone(bbox, zones):
    center_x = (bbox[0] + bbox[2]) / 2
    center_y = (bbox[1] + bbox[3]) / 2
    
    best_zone = "default_zone"
    best_priority = float('inf')
    
    for zone_name, zone_config in zones.items():
        if point_in_polygon([center_x, center_y], zone_config['polygon']):
            if zone_config.get('priority', 1) < best_priority:
                best_zone = zone_name
                best_priority = zone_config['priority']
    
    return best_zone
```

## Pipeline Integration

### Automatic Wiring
The converter enables automatic pipeline wiring:
```python
# Pipeline components declare their formats
yolo_detector.produces = ["yolo_format"]
od1_tracker.consumes = ["od1_format"]

# System automatically inserts converter
pipeline = [
    yolo_detector,
    auto_insert_converter(yolo_detector.produces, od1_tracker.consumes),
    od1_tracker
]
```

### Configuration Example
```json
{
  "converter": "yolo_to_od1_converter",
  "parameters": {
    "confidence_threshold": 0.3,
    "class_filter": [0, 2, 3, 5, 7],  // person, car, motorcycle, bus, truck
    "zones": {
      "parking_zone": {
        "polygon": [[100,200], [700,200], [700,500], [100,500]],
        "priority": 1
      },
      "entrance_zone": {
        "polygon": [[0,0], [200,0], [200,150], [0,150]],
        "priority": 2
      }
    }
  }
}
```

## Error Handling

### Common Issues
- **Invalid Coordinates**: Handle out-of-bounds YOLO coordinates
- **Missing Classes**: Handle unknown class IDs gracefully
- **Zone Overlap**: Resolve conflicting zone assignments
- **Performance**: Optimize for high-throughput scenarios

### Validation
```python
def validate_yolo_input(detection):
    assert 'bbox' in detection, "Missing bbox"
    assert 'confidence' in detection, "Missing confidence"
    assert 0 <= detection['confidence'] <= 1, "Invalid confidence range"
    assert len(detection['bbox']) == 4, "Bbox must have 4 coordinates"
```

## Best Practices

### Configuration
1. **Threshold Tuning**: Adjust confidence threshold based on downstream requirements
2. **Zone Design**: Create non-overlapping zones when possible
3. **Class Selection**: Filter to relevant classes for performance
4. **Priority Assignment**: Use zone priorities for clear hierarchy

### Performance Optimization
1. **Batch Processing**: Process multiple detections together
2. **Zone Caching**: Cache zone lookup calculations
3. **Coordinate Optimization**: Use efficient coordinate transformation
4. **Memory Management**: Reuse objects where possible

### Integration
1. **Format Validation**: Verify input/output format compatibility
2. **Pipeline Testing**: Test converter in complete pipeline context
3. **Monitoring**: Track conversion accuracy and performance
4. **Documentation**: Document zone definitions and class mappings

## Troubleshooting

### Common Problems
1. **Missing Detections**: Check confidence threshold and class filter
2. **Wrong Zones**: Verify zone polygon definitions
3. **Performance Issues**: Optimize zone lookup algorithms
4. **Coordinate Errors**: Validate coordinate transformation logic

## References
- YOLO Object Detection Documentation
- OD1 Format Specification
- AIOS Pipeline Framework
- Computer Vision Coordinate Systems

## Notes
Essential converter for bridging YOLO-based detectors with zone-aware tracking and analysis systems. Enables seamless integration of popular YOLO models into sophisticated computer vision pipelines requiring spatial context and standardized data formats.
