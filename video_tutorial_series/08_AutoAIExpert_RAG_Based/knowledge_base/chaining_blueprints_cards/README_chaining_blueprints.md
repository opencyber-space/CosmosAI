# Chaining Blueprints Cards Documentation

This directory contains chaining blueprint cards that define complete end-to-end computer vision pipelines for specific use cases. Each JSON file represents a full pipeline composition with multiple connected nodes, data flow, and configuration parameters.

## Structure Overview

Each chaining blueprint follows a comprehensive structure:

### Core Components:
- **componentId**: Unique identifier for the complete pipeline
- **componentType**: Always `node.algorithm.pipeline`
- **parser_version**: Pipeline format version
- **body**: Complete pipeline specification including:
  - **header**: Pipeline metadata and versioning
  - **spec**: Complete pipeline configuration with nodes and connections

### Key Sections:
1. **Pipeline Identity**: Basic pipeline information and versioning
2. **Source Configuration**: Input stream setup (cameras, files, etc.)
3. **Nodes Array**: Individual algorithm components in the pipeline
4. **Graph Structure**: Data flow connections between nodes
5. **Settings**: Global pipeline configuration
6. **Scale Specifications**: Hardware allocation and clustering information

### Pipeline Components:
- **Algorithm Nodes**: AI/ML models (detection, tracking, pose estimation)
- **Policy Nodes**: Business logic and filtering
- **Usecase Nodes**: High-level behavior analysis
- **Utility Nodes**: Data transformation and routing

## Files in this Directory:

Each blueprint represents a complete solution for a specific surveillance or monitoring scenario, combining multiple AI models and business logic into a cohesive pipeline.
