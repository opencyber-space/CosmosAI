# README: Input Format Cards

## Overview

Input Format Cards define the standardized data formats used throughout the computer vision pipeline for representing and exchanging object information between different components. These format specifications ensure compatibility and enable automatic pipeline composition.

## Purpose

Input Format Cards serve several critical functions:

1. **Data Standardization**: Define consistent data structures across all pipeline components
2. **Component Compatibility**: Enable automatic detection of compatible components
3. **Pipeline Validation**: Ensure data flow integrity throughout processing chains
4. **Documentation**: Provide comprehensive field specifications and usage guidelines

## Format Structure

Each Input Format Card includes:

### Core Specifications
- **Component Identity**: Unique format identifier and versioning
- **Schema Definition**: Detailed field structure and data types
- **Field Specifications**: Comprehensive documentation of each field
- **Extension Support**: Standardized extension mechanisms (props field)

### Integration Information
- **Compatibility Mapping**: Component consumption/production declarations
- **Validation Rules**: Data integrity and type checking requirements
- **Performance Characteristics**: Memory and processing implications

## Available Formats

### OD1 (Object Detection Format 1)
- **Primary Use**: Standard object representation throughout pipeline
- **Schema Version**: 1.1
- **Core Fields**: 9 standardized fields (class, score, zone, path, id, roi, polygon, timestamp, props)
- **Extensions**: Comprehensive props specifications for pose, demographics, behavior

## Usage Guidelines

### For Component Developers
1. **Consumption Declaration**: Declare input format requirements in component specs
2. **Production Declaration**: Specify output format capabilities
3. **Field Validation**: Implement proper field validation and type checking
4. **Extension Handling**: Support standard extension fields appropriately

### For Pipeline Designers
1. **Format Matching**: Ensure producer/consumer format compatibility
2. **Data Flow Planning**: Design data transformations between incompatible formats
3. **Performance Optimization**: Consider format complexity in performance planning
4. **Validation Integration**: Include format validation in pipeline testing

## Best Practices

### Data Integrity
- Always validate input data against format specifications
- Handle missing or malformed fields gracefully
- Maintain consistent coordinate systems and units
- Use appropriate data types for all fields

### Performance Optimization
- Minimize unnecessary field copying between components
- Use efficient serialization for network transmission
- Consider memory impact of large extension objects
- Implement lazy loading for optional fields

### Extensibility
- Use the props field for algorithm-specific extensions
- Document custom props fields clearly
- Maintain backward compatibility when extending formats
- Follow naming conventions for new fields

## Integration with AIOS

Input Format Cards integrate with the AIOS ecosystem through:

1. **Automatic Component Discovery**: Format compatibility enables automatic pipeline composition
2. **Runtime Validation**: Format specifications support runtime data validation
3. **Performance Optimization**: Format awareness enables optimization decisions
4. **Documentation Generation**: Automatic pipeline documentation from format specs

## Future Extensions

Planned extensions to Input Format Cards include:

1. **Additional Formats**: Support for video, audio, and multimodal data
2. **Version Migration**: Automatic format version conversion
3. **Schema Evolution**: Backward-compatible schema updates
4. **Performance Profiling**: Format-specific performance characteristics

This README provides the foundation for understanding and using Input Format Cards in computer vision pipeline development and deployment.
