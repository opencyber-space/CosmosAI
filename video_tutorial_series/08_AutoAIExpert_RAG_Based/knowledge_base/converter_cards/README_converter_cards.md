# Converter Cards Documentation

This directory contains converter cards that define data format transformation components. These converters enable interoperability between different data formats used in computer vision pipelines, allowing components with different input/output formats to work together seamlessly.

## Structure Overview

Each converter card follows this structure:

### Core Components:
- **componentId**: Unique identifier for the converter
- **componentType**: Always `node.algorithm.converter`
- **name**: Human-readable converter name
- **category**: Type of conversion (e.g., `format_converter`)
- **conversion_mapping**: Source to target format specification
- **capabilities**: List of conversion features
- **parameters**: Configuration options for the conversion

### Key Sections:
1. **Converter Identity**: Basic information about the converter
2. **Format Mapping**: Input and output format specifications
3. **Conversion Logic**: Transformation rules and capabilities
4. **Configuration Parameters**: Customizable conversion settings
5. **Performance Characteristics**: Runtime requirements and metrics

## Files in this Directory:

These converter cards enable automatic format translation and pipeline compatibility, allowing components with different data format requirements to work together in complex pipelines.
