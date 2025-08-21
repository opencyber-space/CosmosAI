# Model Cards Documentation

This directory contains model cards that define AI/ML models used in computer vision pipelines. Each JSON file represents a specific model with its configuration, capabilities, and requirements.

## Structure Overview

Each model card follows a standardized structure:

### Core Components:
- **componentId**: Unique identifier with name, version, and release tag
- **componentType**: Hierarchical type (e.g., `node.algorithm.objdet`, `node.algorithm.tracker`)
- **containerImage**: Docker image containing the model
- **requiresGPU**: Hardware requirements
- **componentConfig**: Detailed configuration including inputs/outputs, parameters, and settings

### Key Sections:
1. **Identity & Metadata**: Basic information about the model
2. **Hardware Requirements**: GPU/CPU requirements and resource specifications
3. **Input/Output Contract**: Data formats the model consumes and produces
4. **Configuration Parameters**: Tunable parameters with ranges and defaults
5. **Performance Characteristics**: Batch size, frame size, processing capabilities
6. **Model-Specific Information**: Architecture details, training data, performance metrics

## Files in this Directory:
