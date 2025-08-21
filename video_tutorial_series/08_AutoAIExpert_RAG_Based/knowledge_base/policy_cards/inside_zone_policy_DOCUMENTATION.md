# Inside Zone Policy Documentation

## Overview
This document describes the `inside_zone_policy.json` policy card, which defines a spatial filtering policy using the Shapely library to check whether objects are located within predefined zones. This policy is fundamental for region-of-interest (ROI) based analysis in computer vision pipelines.

## Policy Identity

### Component Information
- **Component ID**: `inside_zone`
- **Component Type**: `node.algorithm.policy` (Policy Processing Node)
- **ID**: `pol-inside-zone`
- **Label**: Policy
- **Name**: Inside Zone
- **Category**: Spatial Filter
- **Framework**: Shapely
- **License**: MIT
- **Repository**: https://shapely.readthedocs.io/

## Model Details

### Description
Spatial filtering policy that uses Shapely library to check whether the pivot point of bounding boxes is within predefined zones.

### Intended Use
Filter objects based on their spatial location within defined zones or regions of interest.

### Limitations
- **2D Spatial Only**: Only supports 2D spatial filtering (no height/depth considerations)
- **Predefined Zones**: Requires predefined zone polygons for filtering
- **Pivot Point Based**: Filtering decision based on single pivot point, not entire bounding box
- **Static Shapes**: Zone shapes must be defined as polygons

### Ethical Considerations
- Ensure zone definitions do not introduce bias in surveillance applications
- Consider privacy implications when defining monitoring zones
- Avoid discriminatory zone placement that could disproportionately affect specific groups
- Maintain transparency in zone definition criteria

## Technical Parameters

### Computational Characteristics
- **Computational Complexity**: O(n*m) where n = objects, m = zones
- **Memory Footprint**: Low
- **Processing Type**: Geometric operations
- **Dependencies**: 
  - Shapely (geometric operations)
  - NumPy (numerical computations)

## Configuration Parameters

### Pivot Point (`pivotPoint`)
- **Description**: Pivot point to use for bounding box zone checking
- **Type**: String
- **Allowed Values**: 
  - `"top"`: Top center of bounding box
  - `"mid"`: Middle center of bounding box (geometric center)
  - `"bottom"`: Bottom center of bounding box
- **Default**: "mid"
- **Purpose**: Determines which point of the object is used for zone membership testing

### Zone Names (`zone_names`)
- **Description**: List of zone names to filter objects within
- **Type**: List
- **Default**: [] (empty list)
- **Dynamic**: Yes (supplied at runtime)
- **Purpose**: Specifies which zones to apply filtering to
- **Example**: `["Zone1", "RestrictedArea", "MonitoringZone"]`

### Zones (`zones`)
- **Description**: Dictionary of zone definitions with polygon coordinates
- **Type**: Dictionary
- **Format**: `{'zone_name': [[x1,y1], [x2,y2], ...]}`
- **Dynamic**: Yes (updated at runtime)
- **Purpose**: Defines the actual geometric boundaries of zones
- **Example**: 
```json
{
  "Zone1": [[100, 100], [200, 100], [200, 200], [100, 200]],
  "RestrictedArea": [[300, 150], [400, 120], [450, 250], [320, 280]]
}
```

## Dynamic Parameters

### Runtime Updates
- **Supports Runtime Updates**: Yes
- **Updateable Parameters**: `["zone_names", "zones", "pivotPoint"]`
- **Update Latency**: 10 ms
- **Update Method**: API endpoints

### API Endpoints
- **Update Zones**: `/api/v1/policies/inside_zone/update_zones`
- **Update Parameters**: `/api/v1/policies/inside_zone/update_parameters`

### Dynamic Capabilities
- **Real-time Zone Modification**: Change zone boundaries during pipeline execution
- **Zone Addition/Removal**: Add or remove zones without pipeline restart
- **Pivot Point Adjustment**: Change pivot point calculation method
- **Configuration Persistence**: Changes can be saved for future sessions

## Runtime Requirements

### Hardware Requirements
- **CPU Intensive**: No (lightweight geometric operations)
- **GPU Required**: No
- **Minimum RAM**: 100 MB
- **Recommended CPU**: Any modern CPU

### Software Dependencies
- **Python Version**: 3.7+
- **Required Libraries**:
  - `shapely >= 1.8.0` (geometric operations and point-in-polygon testing)
  - `numpy >= 1.20.0` (numerical operations)

## Performance Benchmarks

### Throughput Metrics
- **Objects per Second**: 5,000 objects/second
- **Zones Supported**: Up to 50 zones simultaneously
- **Processing Latency**: 0.2 ms per object
- **Scalability**: Linear scaling with object count

### Accuracy Metrics
- **Spatial Precision**: Pixel-perfect accuracy
- **Edge Case Handling**: Robust handling of boundary conditions
- **Polygon Complexity**: Supports complex, non-convex polygons

## Data Contract

### Input Requirements
- **Consumes**: 
  - `["bboxes"]`: Object bounding boxes with coordinates
  - `["zone_definitions"]`: Zone polygon definitions
- **Input Formats**: `["OD1"]` (Object Detection format 1)

### Required Input Data Structure
```json
{
  "bboxes": [
    {
      "id": "object_id",
      "bbox": [x, y, width, height],
      "class": "object_class",
      "confidence": 0.8
    }
  ],
  "zone_definitions": {
    "zone_name": {
      "polygon": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
      "enabled": true,
      "description": "zone_description"
    }
  }
}
```

### Output Specifications
- **Produces**: 
  - `["filtered_detections"]`: Objects that pass zone filtering
  - `["zone_metadata"]`: Zone membership information
- **Output Formats**: `["OD1"]` (Object Detection format 1)

### Output Data Structure
```json
{
  "filtered_detections": [
    {
      "id": "object_id",
      "bbox": [x, y, width, height],
      "class": "object_class",
      "confidence": 0.8,
      "zone_membership": ["zone1", "zone2"],
      "pivot_point": [x_pivot, y_pivot]
    }
  ],
  "zone_metadata": {
    "zone_name": {
      "object_count": 5,
      "object_ids": ["obj1", "obj2", "obj3"],
      "density": "objects_per_area",
      "last_updated": "timestamp"
    }
  }
}
```

## Algorithm Logic

### Processing Flow
1. **Input Processing**: Receive object bounding boxes and zone definitions
2. **Pivot Point Calculation**: Calculate pivot point for each object based on configuration
3. **Zone Iteration**: For each zone in zone_names list
4. **Point-in-Polygon Test**: Use Shapely to test if pivot point is inside zone polygon
5. **Filtering Decision**: Include/exclude object based on zone membership
6. **Metadata Generation**: Create zone membership and statistics metadata

### Pivot Point Calculation
```python
def calculate_pivot_point(bbox, pivot_type):
    x, y, width, height = bbox
    
    if pivot_type == "top":
        return (x + width/2, y)
    elif pivot_type == "mid":
        return (x + width/2, y + height/2)
    elif pivot_type == "bottom":
        return (x + width/2, y + height)
```

### Zone Filtering Logic
```python
def filter_objects_by_zone(objects, zones, zone_names, pivot_type):
    filtered_objects = []
    
    for obj in objects:
        pivot_point = calculate_pivot_point(obj.bbox, pivot_type)
        obj_zones = []
        
        for zone_name in zone_names:
            if zone_name in zones:
                polygon = Polygon(zones[zone_name])
                point = Point(pivot_point)
                
                if polygon.contains(point):
                    obj_zones.append(zone_name)
        
        if obj_zones:  # Object is in at least one zone
            obj.zone_membership = obj_zones
            filtered_objects.append(obj)
    
    return filtered_objects
```

## Usage Notes

### Best Use Cases
- **Security Monitoring**: Filter objects only in restricted or monitored areas
- **Traffic Analysis**: Monitor vehicles only in specific lanes or areas
- **Retail Analytics**: Analyze customer behavior in specific store sections
- **Safety Compliance**: Monitor for objects in safety-critical zones
- **Privacy Protection**: Exclude objects in privacy-sensitive areas

### Pivot Point Selection Guidelines

#### Top Pivot Point (`"top"`)
- **Best For**: Vehicle detection (license plate area)
- **Use Cases**: Traffic monitoring, parking violation detection
- **Advantage**: Represents vehicle front, useful for direction analysis

#### Mid Pivot Point (`"mid"`)
- **Best For**: General object detection, person detection
- **Use Cases**: General surveillance, crowd monitoring
- **Advantage**: Geometric center, most stable for object representation

#### Bottom Pivot Point (`"bottom"`)
- **Best For**: Person detection (foot position), ground-based analysis
- **Use Cases**: Pedestrian tracking, floor area analysis
- **Advantage**: Represents ground contact point, useful for spatial analysis

### Zone Design Best Practices

#### Simple Rectangular Zones
```json
{
  "entrance": [[100, 100], [300, 100], [300, 200], [100, 200]]
}
```

#### Complex Irregular Zones
```json
{
  "irregular_area": [
    [150, 100], [250, 80], [300, 150], 
    [280, 220], [200, 240], [120, 180]
  ]
}
```

#### Multiple Zone Configuration
```json
{
  "zone_names": ["entrance", "restricted", "monitoring"],
  "zones": {
    "entrance": [[0, 0], [100, 0], [100, 100], [0, 100]],
    "restricted": [[200, 200], [300, 200], [300, 300], [200, 300]],
    "monitoring": [[400, 0], [500, 0], [500, 200], [400, 200]]
  }
}
```

## Integration Requirements

### Upstream Dependencies
1. **Object Detection**: Provides bounding boxes for filtering
2. **Zone Definition System**: Provides zone polygon coordinates
3. **Coordinate System**: Consistent coordinate system between zones and detections

### Downstream Applications
1. **Tracking Systems**: Track only objects in relevant zones
2. **Behavior Analysis**: Analyze behavior within specific areas
3. **Alert Systems**: Generate zone-based alerts
4. **Analytics Dashboards**: Zone-specific analytics and reporting

### Pipeline Integration Example
```
Object Detection → Inside Zone Policy → Tracking → Behavior Analysis
```

## Advanced Features

### Multi-Zone Membership
- Objects can belong to multiple zones simultaneously
- Zone priority handling for overlapping zones
- Hierarchical zone relationships

### Dynamic Zone Updates
- Real-time zone boundary modifications
- API-based zone configuration
- Event-driven zone changes

### Performance Optimization
- Spatial indexing for large numbers of zones
- Bounding box pre-filtering
- Parallel processing for multiple zones

## Troubleshooting

### Common Issues
1. **No Objects Filtered**: Check zone coordinates and pivot point selection
2. **Incorrect Filtering**: Verify zone polygon orientation (clockwise/counterclockwise)
3. **Performance Issues**: Reduce number of zones or simplify zone shapes
4. **Coordinate Misalignment**: Ensure zones and detections use same coordinate system

### Performance Optimization
- Use simpler polygon shapes when possible
- Implement bounding box pre-filtering for complex zones
- Cache zone polygon objects for repeated use
- Consider zone grouping for related areas

## Error Handling

### Common Error Scenarios
- **Invalid Polygon**: Handle malformed zone definitions
- **Empty Zone List**: Graceful handling of empty zone_names
- **Coordinate Out of Bounds**: Handle objects outside image boundaries
- **Invalid Pivot Point**: Fallback to default pivot point type

### Recovery Strategies
- Default zone definitions for missing zones
- Automatic pivot point correction
- Logging and alerting for configuration errors
- Graceful degradation when zones are unavailable

## References
1. [Shapely Documentation](https://shapely.readthedocs.io/)
2. [Point-in-Polygon Algorithm](https://en.wikipedia.org/wiki/Point_in_polygon)
3. MIT License: https://opensource.org/licenses/MIT

## Notes
Highly efficient for real-time applications. Supports complex polygon shapes. Pivot point selection affects filtering behavior significantly. Essential building block for spatial analysis in computer vision pipelines.
