# Class Filter Policy Card Documentation

**File**: `class_filter_policy.json`  
**Component Type**: `node.algorithm.policy`  
**Policy Name**: Class Filter  

## Overview

The Class Filter Policy is a fundamental filtering component that selectively passes only objects belonging to specified classes while discarding all others. This lightweight, high-performance policy is essential for pipeline optimization, reducing computational load on downstream components by filtering out irrelevant object classes early in the processing chain.

## Component Structure

### Component Identity
- **Component ID**: `class_filter`
- **Policy ID**: `pol-class-filter`
- **Framework**: Python
- **License**: MIT

### Policy Purpose
- **Primary Function**: Object class-based filtering
- **Intended Use**: Focus processing on specific object classes of interest
- **Computational Complexity**: O(n) where n = number of objects
- **Processing Type**: List filtering operation

### Input/Output Configuration
- **Input Formats**: OD1
- **Output Formats**: OD1
- **Consumes**: Classified detections (objects with class labels)
- **Produces**: Filtered detections (subset based on allowed classes)

## Configuration Parameters

### Core Configuration
1. **Allowed Classes (`allowed_classes`)**
   - **Type**: List of strings
   - **Required**: Yes
   - **Description**: List of class names to keep in the pipeline
   - **Example**: `["person", "vehicle", "bicycle"]`
   - **Use Cases**: Define specific object types for processing

2. **Case Sensitivity (`case_sensitive`)**
   - **Type**: Boolean
   - **Default**: True
   - **Description**: Whether class matching should be case-sensitive
   - **Impact**: True = "Person" ≠ "person", False = "Person" = "person"

3. **Pass Unknown (`pass_unknown`)**
   - **Type**: Boolean
   - **Default**: False
   - **Description**: Whether to pass objects with unknown/unrecognized classes
   - **Use Cases**: Handle edge cases with unexpected class labels

### Dynamic Configuration
- **Runtime Updates**: Supported
- **Updateable Parameters**: allowed_classes, case_sensitive, pass_unknown
- **Update Latency**: 5ms
- **API Endpoint**: `/api/v1/policies/class_filter/update_parameters`

## Performance Characteristics

### Processing Performance
- **Throughput**: 100,000 objects/second
- **Latency**: 0.01ms per object
- **Memory per Object**: 8 bytes
- **CPU Intensive**: No (minimal CPU usage)
- **GPU Required**: No

### Filtering Accuracy
- **Precision**: 100% (exact string matching)
- **Recall**: 100% (no false negatives)
- **Edge Case Handling**: Robust with empty lists and null values

## System Requirements

### Hardware Requirements
- **CPU**: Any CPU (not performance-critical)
- **RAM**: 50MB minimum
- **GPU**: Not required
- **Storage**: Minimal footprint

### Software Environment
- **Python Version**: 3.6+
- **Dependencies**: Python standard library only
- **Framework**: Pure Python implementation

## Use Case Applications

### Primary Applications
1. **Surveillance Systems**: Filter for "person" and "vehicle" classes only
2. **Traffic Monitoring**: Focus on vehicle-related classes ("car", "truck", "bus")
3. **Retail Analytics**: Filter for "person" in customer tracking scenarios
4. **Security Applications**: Remove non-threat objects from analysis
5. **Wildlife Monitoring**: Focus on specific animal species
6. **Industrial Inspection**: Filter for defect-related object classes

### Pipeline Optimization
- **Early Filtering**: Reduce computational load on expensive downstream components
- **Memory Efficiency**: Lower memory usage by removing irrelevant objects
- **Network Efficiency**: Reduce data transmission in distributed systems
- **Cost Reduction**: Focus expensive GPU processing on relevant objects only

## Configuration Examples

#### Surveillance System (People and Vehicles)
```json
{
  "allowed_classes": ["person", "car", "truck", "bus", "bicycle", "motorcycle"],
  "case_sensitive": false,
  "pass_unknown": false
}
```

#### Pedestrian-Only Tracking
```json
{
  "allowed_classes": ["person"],
  "case_sensitive": true,
  "pass_unknown": false
}
```

#### Traffic Monitoring (Vehicles Only)
```json
{
  "allowed_classes": ["car", "truck", "bus", "van", "motorcycle"],
  "case_sensitive": false,
  "pass_unknown": false
}
```

#### Development/Testing (Permissive Filtering)
```json
{
  "allowed_classes": ["person", "vehicle"],
  "case_sensitive": false,
  "pass_unknown": true
}
```

#### Retail Analytics (Customer Focus)
```json
{
  "allowed_classes": ["person"],
  "case_sensitive": false,
  "pass_unknown": false
}
```

## Integration Guidelines

### Pipeline Placement
- **Optimal Position**: Immediately after object detection
- **Before**: Expensive processing components (tracking, analysis)
- **After**: Object detection and classification
- **Chaining**: Compatible with all downstream components

### Data Flow
1. **Input**: Detection results with class labels
2. **Processing**: String matching against allowed_classes list
3. **Filtering**: Keep matching objects, discard others
4. **Output**: Filtered object list for downstream processing

### Performance Optimization
1. **Class List Size**: Minimize allowed_classes for faster processing
2. **Case Sensitivity**: Set to False for more flexible matching
3. **Runtime Updates**: Use for dynamic scenario adaptation
4. **Early Placement**: Position early in pipeline for maximum efficiency

## Technical Notes

### Implementation Details
- **Algorithm**: Simple list comprehension with string matching
- **Memory Management**: Minimal memory allocation
- **Thread Safety**: Stateless operation (thread-safe)
- **Error Handling**: Graceful handling of malformed inputs

### Quality Considerations
- **Exact Matching**: Only exact string matches are filtered
- **Class Name Consistency**: Ensure consistency with detection model classes
- **Null Handling**: Robust against null or missing class labels
- **Empty Lists**: Handles empty detection lists gracefully

### Limitations
- **String Matching Only**: No fuzzy matching or semantic similarity
- **Case Sensitivity**: Requires exact case matching when enabled
- **No Hierarchical Filtering**: Cannot filter by class hierarchies
- **Static Configuration**: Runtime updates require API calls

### Best Practices
1. **Class Name Verification**: Verify class names match detection model output
2. **Documentation**: Document allowed classes for each deployment
3. **Monitoring**: Track filtering ratios for performance analysis
4. **Testing**: Test with various class combinations and edge cases

### Common Patterns
- **Security Pipeline**: `["person", "vehicle"]` for general surveillance
- **Traffic Analysis**: Vehicle classes only for traffic monitoring
- **People Counting**: `["person"]` for crowd analytics
- **Multi-Class Filtering**: Multiple classes for complex scenarios

This Class Filter Policy provides essential pipeline optimization capabilities by enabling precise control over which object classes are processed by downstream components, significantly improving system efficiency and reducing computational costs.
