# Policy Cards Documentation

This directory contains policy cards that define filtering, processing, and business logic policies used in computer vision pipelines. Each JSON file represents a specific policy that can be applied to object detection results, tracking data, or other pipeline components.

## Structure Overview

Each policy card follows a standardized structure:

### Core Components:
- **componentId**: Unique identifier for the policy
- **componentType**: Always `node.algorithm.policy`
- **modelDetails**: Description, intended use, limitations, and ethical considerations
- **parameters**: Computational characteristics and dependencies
- **configuration**: Policy-specific parameters and settings
- **dynamic_parameters**: Runtime update capabilities and API endpoints

### Key Sections:
1. **Identity & Metadata**: Basic information about the policy
2. **Model Details**: Purpose, limitations, and ethical considerations
3. **Configuration Parameters**: Policy logic parameters with types and defaults
4. **Dynamic Parameters**: Runtime update capabilities and APIs
5. **Runtime Requirements**: Resource needs and software dependencies
6. **Performance Benchmarks**: Throughput and accuracy metrics
7. **Data Contract**: Input/output specifications

## Policy Categories:

### Spatial Filters
- **inside_zone_policy**: Filter objects based on zone membership
- **zone_filtering_policy**: Advanced zone-based filtering

### Classification Filters
- **class_filter_policy**: Filter by object class
- **class_conf_filter_policy**: Filter by class and confidence
- **confidence_filter_policy**: Filter by confidence threshold

### Temporal Filters
- **dwell_time_policy**: Filter based on object dwell time
- **association_policy**: Object association and tracking policies

### Data Processing
- **class_replacer_policy**: Replace or modify object classifications
- **interaction_policy**: Detect and analyze object interactions

## Files in this Directory:
