# Zone Filtering Policy Documentation

## Overview

The Zone Filtering Policy is an advanced spatial filtering component that filters object detections based on their presence within predefined zones using multiple intersection methods. This policy enables sophisticated spatial analysis by determining whether objects are located within specific areas of interest, supporting complex surveillance and monitoring applications with configurable intersection criteria.

The policy supports multiple reference points (center, bottom_center, entire_box) and intersection thresholds, making it suitable for various applications from simple area monitoring to complex multi-zone surveillance systems.

## Policy Identity

- **Component ID**: `zone_filtering`
- **Component Type**: `node.algorithm.policy`
- **Policy ID**: `pol-zone-filtering`
- **Policy Name**: Zone Filtering Policy
- **Category**: Spatial Filter
- **Framework**: Shapely + NumPy
- **License**: MIT License

## Model Details

### Description
Advanced spatial filtering policy that filters detections based on their presence within predefined zones using multiple intersection methods for surveillance and monitoring applications.

### Intended Use
- **Area Monitoring**: Filter objects within specific surveillance areas
- **Perimeter Security**: Detect intrusions in restricted zones
- **Zone-based Analytics**: Generate statistics for specific areas
- **Multi-zone Surveillance**: Complex spatial monitoring with multiple areas
- **Access Control**: Monitor authorized vs unauthorized areas

### Limitations
- **Zone Dependency**: Requires predefined zone polygon definitions
- **Complexity Scaling**: Performance scales with zone polygon complexity
- **Shapely Dependency**: Requires Shapely library for geometric calculations
- **Memory Usage**: Zone storage increases with polygon complexity

### Ethical Considerations
Ensure zone definitions do not introduce bias in spatial filtering applications. Be mindful of privacy implications when defining surveillance zones.

## Technical Parameters

### Computational Characteristics
- **Complexity**: O(n×m×k) where n=objects, m=zones, k=polygon vertices
- **Dependencies**: shapely, numpy
- **Memory Footprint**: Medium (scales with zone complexity)
- **Processing Type**: Geometric intersection analysis

### Performance Profile
- **CPU Intensive**: Yes, geometric calculations are CPU-bound
- **GPU Required**: No, CPU-based polygon operations
- **Minimum RAM**: 300MB
- **Recommended CPU**: Multi-core CPU for complex polygon operations

## Configuration Parameters

### Intersection Settings
1. **Intersection Threshold** (`intersection_threshold`)
   - **Type**: Float
   - **Range**: 0.1 - 1.0
   - **Default**: 0.5
   - **Purpose**: Minimum intersection ratio (intersection area / bounding box area)

2. **Reference Point** (`reference_point`)
   - **Type**: String
   - **Options**: 
     - `center`: Use bounding box center point
     - `bottom_center`: Use bottom center of bounding box (good for people)
     - `entire_box`: Use entire bounding box overlap
   - **Default**: `bottom_center`
   - **Purpose**: Determines which part of object to check for zone membership

### Zone Definitions
1. **Include Zones** (`include_zones`)
   - **Type**: List of strings
   - **Default**: [] (empty = include all zones)
   - **Purpose**: Whitelist of zone names to include in filtering

2. **Exclude Zones** (`exclude_zones`)
   - **Type**: List of strings
   - **Default**: [] (empty = exclude no zones)
   - **Purpose**: Blacklist of zone names to exclude from filtering

3. **Zones** (`zones`)
   - **Type**: Dictionary
   - **Format**: `{'zone_name': [[x1,y1], [x2,y2], ...]}`
   - **Dynamic**: Yes (supports runtime updates)
   - **Purpose**: Polygon definitions for each zone

### Zone Definition Example
```json
{
  "zones": {
    "entrance_area": [[100, 100], [300, 100], [300, 200], [100, 200]],
    "restricted_zone": [[400, 150], [600, 150], [650, 300], [350, 300]],
    "parking_lot": [[0, 400], [800, 400], [800, 600], [0, 600]]
  }
}
```

## Dynamic Parameters

### Runtime Configuration
- **Supports Runtime Updates**: Yes
- **Update Latency**: 15ms
- **Updateable Parameters**: 
  - Intersection threshold and reference point
  - Include/exclude zone lists
  - Zone polygon definitions (add, remove, modify)

### API Endpoints
- **Update Zones**: `/api/v1/policies/zone_filtering/update_zones`
- **Update Thresholds**: `/api/v1/policies/zone_filtering/update_thresholds`

## Runtime Requirements

### System Requirements
- **Operating System**: Cross-platform (Linux, Windows, macOS)
- **Python Version**: 3.7+
- **CPU**: Multi-core recommended for complex polygons
- **Memory**: 300MB minimum, scales with zone complexity

### Dependencies
- **Shapely**: >=1.7.0 (geometric operations and polygon intersection)
- **NumPy**: >=1.18.0 (numerical computations and array operations)

## Performance Benchmarks

### Throughput Performance
- **Objects per Second**: 2,000
- **Maximum Zones Supported**: 50 zones
- **Latency**: 25ms per 100 objects

### Accuracy Metrics
- **Intersection Precision**: 98% (accurate area calculations)
- **Point-in-Polygon Accuracy**: ±1 pixel
- **Zone Membership Accuracy**: 99%

### Scaling Characteristics
| Objects | Zones | Vertices/Zone | Processing Time |
|---------|-------|---------------|-----------------|
| 10      | 5     | 4-6          | ~2ms           |
| 50      | 10    | 4-6          | ~8ms           |
| 100     | 20    | 4-6          | ~25ms          |
| 500     | 50    | 4-6          | ~125ms         |

## Data Contract

### Input Requirements
- **Format**: OD1 format with positioned detections
- **Data Types**:
  - `positioned_detections`: Object detections with bounding box coordinates
  - `zone_definitions`: Polygon zone definitions (can be embedded in config)

### Output Specifications
- **Format**: OD1 format with filtered results
- **Data Types**:
  - `filtered_detections`: Objects that meet zone criteria
  - `zone_metadata`: Zone intersection information
  - `zone_counts`: Object count per zone

### Zone Output Structure
```json
{
  "filtered_detections": [
    {
      "object_id": 123,
      "bbox": [x, y, width, height],
      "class": "person",
      "zones": ["entrance_area"],
      "intersection_ratios": {"entrance_area": 0.85}
    }
  ],
  "zone_metadata": {
    "total_zones": 3,
    "active_zones": 2,
    "processing_time_ms": 12
  },
  "zone_counts": {
    "entrance_area": 5,
    "restricted_zone": 0,
    "parking_lot": 8
  }
}
```

## Algorithm Logic

### Zone Filtering Process Flow
1. **Input Validation**: Verify detection format and zone definitions
2. **Zone Preprocessing**: Parse and validate polygon geometries
3. **Reference Point Calculation**: Compute reference points based on configuration
4. **Intersection Analysis**: Calculate zone membership for each object
5. **Threshold Filtering**: Apply intersection threshold criteria
6. **Output Generation**: Format filtered results with metadata

### Intersection Methods

#### Center Point Method
```python
def center_point_intersection(bbox, zone_polygon):
    center_x = bbox.x + bbox.width / 2
    center_y = bbox.y + bbox.height / 2
    center_point = Point(center_x, center_y)
    return zone_polygon.contains(center_point)
```

#### Bottom Center Method
```python
def bottom_center_intersection(bbox, zone_polygon):
    bottom_center_x = bbox.x + bbox.width / 2
    bottom_center_y = bbox.y + bbox.height
    bottom_point = Point(bottom_center_x, bottom_center_y)
    return zone_polygon.contains(bottom_point)
```

#### Entire Box Method
```python
def entire_box_intersection(bbox, zone_polygon):
    bbox_polygon = box(bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height)
    intersection_area = bbox_polygon.intersection(zone_polygon).area
    bbox_area = bbox_polygon.area
    return intersection_area / bbox_area
```

## Usage Notes

### Best Practices
1. **Reference Point Selection**:
   - Use `bottom_center` for people (feet on ground)
   - Use `center` for vehicles or general objects
   - Use `entire_box` when object overlap matters

2. **Zone Design**:
   - Keep polygons simple (4-8 vertices) for better performance
   - Avoid self-intersecting polygons
   - Ensure zones don't overlap unless intentional

3. **Threshold Tuning**:
   - Use 0.5-0.8 for partial inclusion tolerance
   - Use 0.9-1.0 for strict zone membership
   - Use 0.1-0.3 for edge detection scenarios

4. **Performance Optimization**:
   - Minimize polygon complexity
   - Use spatial indexing for many zones
   - Cache zone geometries when possible

### Common Configuration Patterns

#### Entrance Monitoring
```json
{
  "reference_point": "bottom_center",
  "intersection_threshold": 0.3,
  "include_zones": ["entrance_area"],
  "zones": {
    "entrance_area": [[200, 100], [400, 100], [400, 300], [200, 300]]
  }
}
```

#### Restricted Area Security
```json
{
  "reference_point": "center",
  "intersection_threshold": 0.8,
  "include_zones": ["restricted_zone"],
  "zones": {
    "restricted_zone": [[500, 200], [700, 200], [700, 400], [500, 400]]
  }
}
```

#### Multi-Zone Surveillance
```json
{
  "reference_point": "entire_box",
  "intersection_threshold": 0.5,
  "exclude_zones": ["blind_spot"],
  "zones": {
    "zone_1": [[0, 0], [400, 0], [400, 300], [0, 300]],
    "zone_2": [[400, 0], [800, 0], [800, 300], [400, 300]],
    "blind_spot": [[350, 250], [450, 250], [450, 350], [350, 350]]
  }
}
```

### Limitations
1. **Polygon Complexity**: Complex polygons with many vertices reduce performance
2. **Concave Polygons**: Very complex concave shapes may have edge cases
3. **Real-time Constraints**: Large numbers of zones may impact real-time performance
4. **Memory Usage**: Many complex zones increase memory requirements
5. **Configuration Complexity**: Requires careful zone definition and testing

## Pipeline Integration

### Typical Pipeline Position
```
Object Detection → Tracking → Zone Filtering → Zone Analytics → Alert Generation
```

### Common Integration Patterns
1. **Perimeter Security**: Filter intrusions in restricted areas
2. **Traffic Monitoring**: Vehicle counting in specific lanes or areas
3. **Crowd Management**: People density analysis in different zones
4. **Access Control**: Authorization checking based on zone membership

### Upstream Dependencies
- **Object Detection**: Requires positioned bounding boxes
- **Coordinate System**: Consistent pixel coordinate system
- **Zone Configuration**: Predefined area polygon definitions

### Downstream Applications
- **Zone Analytics**: Count objects and generate zone statistics
- **Alert Systems**: Trigger notifications for zone violations
- **Dashboards**: Visualize zone activity and occupancy
- **Recording Systems**: Zone-based video recording triggers

## Configuration Guidelines

### High Security Scenarios
- Use `entire_box` reference point for complete coverage
- Set high intersection threshold (0.8-1.0)
- Define precise zone boundaries
- Use exclude zones for blind spots

### High Throughput Scenarios
- Use `center` or `bottom_center` for faster computation
- Keep zones simple (rectangular or simple polygons)
- Moderate intersection threshold (0.4-0.6)
- Minimize number of zones

### Entrance/Exit Monitoring
- Use `bottom_center` for people tracking
- Lower intersection threshold (0.2-0.4) for edge detection
- Define narrow zone boundaries at thresholds
- Enable runtime zone updates for calibration

### Multi-Area Surveillance
- Use include/exclude lists for flexible zone management
- Moderate intersection threshold (0.5)
- Design non-overlapping zones for clear separation
- Use zone hierarchy for complex layouts

## Technical Notes

### Optimization Strategies
- **Spatial Indexing**: Use R-tree or similar for many zones
- **Geometry Caching**: Cache compiled polygon geometries
- **Batch Processing**: Process multiple objects simultaneously
- **Early Termination**: Skip expensive calculations when possible

### Integration Best Practices
- **Zone Validation**: Validate polygon definitions during configuration
- **Performance Monitoring**: Monitor processing times and adjust complexity
- **Error Handling**: Handle edge cases like degenerate polygons
- **Testing**: Test with various object positions and zone configurations

### Common Issues and Solutions
1. **Performance Degradation**: Simplify polygon shapes, reduce zone count
2. **Inaccurate Filtering**: Adjust reference point and intersection threshold
3. **Edge Cases**: Handle objects at zone boundaries carefully
4. **Memory Issues**: Optimize zone storage and geometry caching

This Zone Filtering Policy provides comprehensive spatial filtering capabilities essential for area-based surveillance and monitoring applications, enabling sophisticated zone-based analytics and security systems.
