# YOLOv7 Vehicles5 Model Card Documentation

**File**: `yolov7vehicles5.json`  
**Component Type**: `node.algorithm.objdet`  
**Model Name**: YOLOv7 Vehicles5  

## Overview

The YOLOv7 Vehicles5 model is a specialized vehicle detection system optimized for surveillance applications, focusing on five key vehicle categories commonly found in traffic monitoring and security scenarios. Based on the proven YOLOv7 architecture, this model delivers high-performance vehicle detection with excellent accuracy for cars, buses, trucks, motorbikes, and autorickshaws across diverse surveillance conditions.

## Component Structure

### Component Identity
- **Component ID**: `vehicles5Detection` (v0.0.1, stable release)
- **Container Image**: `vehicles5detection:latest`
- **Framework**: PyTorch
- **License**: Closed source

### Model Architecture
- **Backbone**: E-ELAN (Efficient Layer Aggregation Network)
- **Neck**: FPN-PANet (Feature Pyramid Network with Path Aggregation)
- **Head**: Detect(V7) - YOLOv7 detection head
- **Total Parameters**: 37.2M parameters
- **Anchor Configuration**: 9 anchor boxes optimized for vehicle shapes

### Vehicle Class Detection
The model specializes in detecting 5 vehicle categories:
1. **Car** - Standard passenger vehicles
2. **Bus** - Public transportation buses
3. **Truck** - Commercial trucks and heavy vehicles  
4. **Motorbike** - Motorcycles and scooters
5. **Autorickshaw** - Three-wheeled vehicles (region-specific)

### Input/Output Configuration
- **Input Resolution**: 416×416 to 1280×1280 pixels (configurable)
- **Default Resolution**: 640×640 pixels
- **Batch Support**: Yes (1-8 vehicles per batch)
- **Input Formats**: OD1
- **Output Formats**: OD1
- **Outputs**: Vehicle bounding boxes with class labels and confidence scores

## Configuration Parameters

### Detection Parameters
1. **Confidence Threshold (`conf`)**
   - **Default**: 0.4
   - **Range**: 0.1 - 1.0
   - **Purpose**: Minimum confidence score for vehicle detection acceptance

2. **NMS IoU Threshold (`nms_iou`)**
   - **Default**: 0.4
   - **Range**: 0.1 - 1.0
   - **Purpose**: Non-Maximum Suppression overlap threshold for duplicate removal

### Image Processing Settings
1. **Input Dimensions**
   - **Width**: 416-1280 pixels (default: 640)
   - **Height**: 416-1280 pixels (default: 640)
   - **Aspect Ratio**: Square input preferred

2. **Batch Configuration**
   - **Batch Size**: 1-8 (default: 8)
   - **ROI Batch Size**: 1-4 (default: 1)

3. **Decoder Settings**
   - **Decoder Type**: TURBO (default), DALI
   - **Interpolation**: INTERP_GAUSSIAN (default), plus 5 other options
   - **Full Image**: True (process complete frame)

### Performance Settings
1. **FP16 Precision (`use_fp16`)**
   - **Default**: True
   - **Impact**: 2x faster inference with minimal accuracy loss

2. **CUDA Acceleration (`use_cuda`)**
   - **Default**: True
   - **Purpose**: GPU acceleration enable/disable

## Performance Benchmarks

### Throughput Performance (NVIDIA T4)
- **Batch-4**: 116 FPS
- **Batch-8**: 142 FPS  
- **Batch-16**: 161 FPS (optimal performance)
- **Batch-32**: 156 FPS (performance plateaus)

### Resource Utilization
- **GPU Memory**: 1.47GB (batch-4), 1.95GB (batch-8), 2.29GB (batch-16), 2.91GB (batch-32)
- **GPU Utilization**: 27% (batch-4), 61% (batch-8), 72% (batch-16), 81% (batch-32)

### Optimal Configurations
- **Performance**: Batch size 16 (161 FPS)
- **Efficiency**: Batch size 8 (balanced performance/memory)
- **Memory Constrained**: Batch size 4 (lowest memory usage)

## System Requirements

### Hardware Requirements
- **GPU**: Required (minimum 2GB VRAM)
- **Recommended GPU**: NVIDIA T4 or better
- **CPU**: 4 cores minimum
- **RAM**: 8GB minimum

### Software Environment
- **Python**: 3.8+
- **CUDA**: 11.0+
- **cuDNN**: 8.0+
- **OS**: Ubuntu 20.04

## Training Details

### Training Dataset
- **Dataset**: Custom Vehicles Dataset
- **Collection**: Surveillance cameras across day and night conditions
- **Scenarios**: Real-world traffic monitoring environments
- **Conditions**: Various lighting, weather, and traffic density conditions

### Vehicle Categories
1. **Car**: Passenger vehicles, sedans, SUVs, hatchbacks
2. **Bus**: Public buses, coaches, minibuses
3. **Truck**: Commercial trucks, delivery vehicles, heavy transport
4. **Motorbike**: Motorcycles, scooters, two-wheelers
5. **Autorickshaw**: Three-wheeled vehicles (tuk-tuks, auto-rickshaws)

### Optimization Focus
- **Surveillance Scenarios**: Optimized for security camera perspectives
- **Day/Night Performance**: Robust across lighting conditions
- **Multi-Scale Detection**: Handles vehicles at various distances
- **Occlusion Handling**: Performs well with partially visible vehicles

## Use Case Applications

### Primary Applications
1. **Traffic Monitoring**: Highway and intersection vehicle counting
2. **Parking Management**: Vehicle type classification in parking areas
3. **Security Surveillance**: Vehicle identification in restricted areas
4. **Toll Collection**: Vehicle classification for toll systems
5. **Smart City**: Urban traffic analytics and planning
6. **Border Control**: Vehicle monitoring at checkpoints

### Regional Applications
- **Urban India**: Autorickshaw detection for local transportation
- **Highway Monitoring**: Truck and bus detection for commercial traffic
- **Airport Security**: Vehicle classification in restricted zones
- **Industrial Sites**: Commercial vehicle monitoring

## Configuration Examples

#### Highway Traffic Monitoring (High Throughput)
```json
{
  "conf": 0.5,
  "nms_iou": 0.4,
  "batch_size": 16,
  "width": 640,
  "height": 640,
  "use_fp16": true,
  "decoderType": "DALI"
}
```

#### Security Surveillance (High Accuracy)
```json
{
  "conf": 0.3,
  "nms_iou": 0.3,
  "batch_size": 4,
  "width": 1024,
  "height": 1024,
  "use_fp16": false,
  "decoderType": "TURBO"
}
```

#### Real-Time Monitoring (Balanced)
```json
{
  "conf": 0.4,
  "nms_iou": 0.4,
  "batch_size": 8,
  "width": 640,
  "height": 640,
  "use_fp16": true,
  "decoderType": "DALI"
}
```

#### Edge Deployment (Resource Constrained)
```json
{
  "conf": 0.6,
  "nms_iou": 0.5,
  "batch_size": 2,
  "width": 416,
  "height": 416,
  "use_fp16": true,
  "decoderType": "TURBO"
}
```

## Integration Guidelines

### Pipeline Integration
- **Input**: RGB frames from traffic cameras or surveillance systems
- **Processing**: Vehicle detection with 5-class classification
- **Output**: Vehicle bounding boxes with class labels and confidence scores
- **Chaining**: Compatible with tracking, counting, and analytics components

### Performance Optimization
1. **Batch Size**: Use 16 for maximum throughput, 8 for balanced performance
2. **Resolution**: 640×640 for balanced accuracy/speed, 416×416 for speed priority
3. **FP16 Precision**: Enable for significant performance improvement
4. **Memory Management**: Monitor GPU memory usage with larger batch sizes

## Technical Notes

### Model Advantages
- **Specialized Classes**: Optimized for 5 common vehicle types
- **High Performance**: 161 FPS at optimal batch size
- **Real-World Training**: Trained on surveillance camera data
- **Day/Night Robust**: Performs well across lighting conditions
- **Regional Adaptation**: Includes autorickshaw for specific markets

### Limitations
- **Limited Classes**: Only 5 vehicle types (no pedestrians, bicycles)
- **Resolution Dependency**: Performance optimized for specific input sizes
- **Surveillance Focus**: May not generalize to other camera perspectives
- **Regional Bias**: Autorickshaw class specific to certain regions

### Quality Considerations
- **False Positives**: May detect stationary objects as vehicles
- **Small Vehicles**: Performance may degrade for very distant vehicles
- **Occlusion**: Partially hidden vehicles may be missed
- **Weather**: Performance may vary in extreme weather conditions

### Best Practices
1. **Camera Placement**: Optimize camera angles for vehicle visibility
2. **Lighting**: Ensure adequate lighting for night-time detection
3. **Threshold Tuning**: Adjust confidence based on precision/recall requirements
4. **Batch Processing**: Use optimal batch sizes for hardware efficiency
5. **Monitoring**: Track detection rates and classification accuracy

### Vehicle-Specific Considerations
- **Car Detection**: Most reliable class with highest accuracy
- **Bus/Truck**: Good detection for large vehicles
- **Motorbike**: May require lower confidence thresholds
- **Autorickshaw**: Region-specific performance variation

This YOLOv7 Vehicles5 model provides specialized vehicle detection capabilities essential for traffic monitoring, surveillance, and smart city applications, offering excellent performance with region-specific vehicle class support.
