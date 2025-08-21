# Input Format Cards Documentation

This directory contains input format cards that define standardized data structures used throughout computer vision pipelines. Each JSON file represents a specific data format specification with schema definitions, field descriptions, and usage examples.

## Structure Overview

Each input format card follows this structure:

### Core Components:
- **componentId**: Unique identifier for the format
- **componentType**: Always `node.algorithm.format`
- **name**: Human-readable format name
- **description**: Purpose and usage context
- **schema_version**: Format specification version
- **structure**: Ordered list of required fields
- **field_specs**: Detailed specifications for each field
- **props_specifications**: Extended properties and their formats

### Key Sections:
1. **Format Identity**: Basic information about the data format
2. **Schema Structure**: Field definitions and data types
3. **Properties Specifications**: Extended metadata fields
4. **Examples**: Concrete usage examples
5. **Data Contract**: Input/output compatibility information

## Files in this Directory:

These format cards ensure data compatibility and enable automatic pipeline wiring based on data format requirements.
