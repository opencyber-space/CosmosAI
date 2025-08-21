# YOLOv8 Nano Model Card Documentation

**File**: `yolov8n.json`  
**Component Type**: `node.algorithm.detection`  
**Model Name**: YOLOv8 Nano Object Detection  

## Overview

YOLOv8 Nano represents the ultra-lightweight variant of the YOLOv8 family, specifically engineered for edge devices and real-time applications where computational resources are constrained. With only 3.2 million parameters, it delivers exceptional speed-accuracy balance, making it ideal for surveillance systems, IoT devices, and automotive applications.

## Component Structure

### Component Identity
- **Component ID**: `yolov8n` (v8.0.0, stable release)
- **Container Image**: `yolov8n:latest`
- **Framework**: PyTorch
- **License**: AGPL-3.0

### Model Architecture
- **Backbone**: CSPDarknet - Cross Stage Partial Darknet for feature extraction
- **Neck**: C2f - Cross Stage Partial with 2 Convolutions for feature fusion
- **Head**: Detect - Detection head for object localization and classification
- **Activation**: SiLU (Swish) activation function
- **Total Parameters**: 3.2M (optimized for minimal memory footprint)
- **FLOPs**: 8.7G (computationally efficient)

### Input/Output Configuration
- **Input Resolution**: 640×640 pixels (single fixed size)
- **Batch Support**: Yes (up to 32 images per batch)
- **Input Formats**: OD1
- **Output Formats**: OD1
- **Outputs**: Bounding boxes, class IDs, confidence scores, detection count

## Configuration Parameters

### Detection Parameters
1. **Confidence Threshold (`conf`)**
   - Default: 0.25
   - Range: 0.01 - 1.0
   - Purpose: Minimum confidence score for detection acceptance

2. **IoU Threshold (`iou`)**
   - Default: 0.45
   - Range: 0.01 - 1.0
   - Purpose: Non-Maximum Suppression overlap threshold

3. **Maximum Detections (`max_det`)**
   - Default: 300
   - Range: 1 - 1000
   - Purpose: Maximum number of detections per image

### Performance Settings
1. **FP16 Precision (`use_fp16`)**
   - Default: True
   - Options: True/False
   - Impact: 2x faster inference with minimal accuracy loss

2. **Batching (`enable_batching`)**
   - Default: True
   - Options: True/False
   - Impact: Improves throughput for multiple images

3. **Decoder Type (`decoderType`)**
   - Default: DALI
   - Options: TURBO, DALI
   - Impact: DALI provides optimized image preprocessing

## Performance Benchmarks

### COCO Dataset Performance (val2017)
- **mAP@0.5**: 37.1% (IoU threshold 0.5)
- **mAP@0.5-0.95**: 26.5% (IoU range 0.5-0.95)
- **Precision**: 75%
- **Recall**: 68%

### Throughput Performance (NVIDIA T4)
- **Single Image (640×640)**: 180 FPS
- **Batch-16**: 320 FPS
- **Batch-32**: 280 FPS
- **CPU (Intel Xeon)**: 25 FPS

### Resource Utilization
- **GPU Memory**: 1.2GB (single), 2.8GB (batch-16), 4.0GB (batch-32)
- **GPU Utilization**: 35% (single), 75% (batch-16), 95% (batch-32)
- **Total Latency**: 6.0ms (preprocessing: 1.2ms, inference: 4.2ms, postprocessing: 0.6ms)

## System Requirements

### Hardware Requirements
- **GPU**: Required (minimum 2GB VRAM)
- **Recommended GPU**: NVIDIA T4 or better
- **CPU**: 4 cores minimum
- **RAM**: 4GB minimum

### Software Environment
- **Python**: 3.8+
- **PyTorch**: 1.13+
- **CUDA**: 11.0+
- **cuDNN**: 8.0+
- **OS**: Ubuntu 20.04

## Training Details

### Dataset
- **Training Dataset**: COCO 2017
- **Classes**: 80 object categories
- **Training Images**: 118,287
- **Scenarios**: General purpose, surveillance, automotive
- **Object Classes**: Person, vehicles, animals, everyday objects

### Optimization Features
- **Pretrained**: Yes (COCO weights available)
- **Transfer Learning**: Supported for custom datasets
- **Data Augmentation**: Mosaic, copy-paste, mixup
- **Optimization**: AdamW optimizer with cosine learning rate scheduling

## Use Case Applications

### Primary Applications
1. **Surveillance Systems**: Real-time person and vehicle detection
2. **Edge Computing**: IoT devices with limited computational resources
3. **Automotive**: Driver assistance systems and traffic monitoring
4. **Mobile Applications**: Smartphone-based object detection
5. **Robotics**: Autonomous navigation and object recognition

### Configuration Examples

#### High-Speed Surveillance (FPS Priority)
```json
{
  "conf": 0.3,
  "iou": 0.5,
  "max_det": 100,
  "use_fp16": true,
  "enable_batching": true,
  "decoderType": "DALI"
}
```

#### High-Accuracy Detection (Precision Priority)
```json
{
  "conf": 0.15,
  "iou": 0.4,
  "max_det": 500,
  "use_fp16": false,
  "enable_batching": false,
  "decoderType": "TURBO"
}
```

#### Edge Device Deployment (Resource Constrained)
```json
{
  "conf": 0.4,
  "iou": 0.6,
  "max_det": 50,
  "use_fp16": true,
  "enable_batching": false,
  "decoderType": "DALI"
}
```

## Integration Guidelines

### Pipeline Integration
- **Input**: RGB frames from video streams or image sources
- **Processing**: Real-time object detection with bounding box regression
- **Output**: Structured detection results in OD1 format
- **Chaining**: Compatible with tracking, filtering, and analysis components

### Performance Optimization
1. **Batch Processing**: Use batch sizes 8-16 for optimal throughput
2. **FP16 Precision**: Enable for 2x speed improvement
3. **DALI Decoder**: Use for optimized preprocessing pipeline
4. **GPU Memory**: Monitor usage to prevent OOM errors

### Quality Assurance
- **Confidence Tuning**: Adjust based on false positive tolerance
- **IoU Threshold**: Balance between duplicate detection elimination and recall
- **Max Detections**: Set based on expected object density in scenes

## Technical Notes

### Model Advantages
- **Ultra-Lightweight**: Only 3.2M parameters for minimal memory footprint
- **Real-Time Performance**: 180+ FPS on modern GPUs
- **Edge Deployment**: Optimized for resource-constrained environments
- **Broad Compatibility**: Supports 80 COCO object classes
- **Production Ready**: Stable release with comprehensive benchmarks

### Limitations
- **Fixed Input Size**: Single resolution (640×640) requirement
- **Limited Classes**: Restricted to 80 COCO categories
- **Small Object Detection**: May struggle with very small objects
- **Complex Scenes**: Performance degrades in highly cluttered environments

### Version Information
- **Model Version**: v8.0.0 (stable)
- **Release Status**: Production ready
- **Update Frequency**: Regular updates available from Ultralytics
- **Compatibility**: Backward compatible with YOLOv5 pipelines

This model card provides the foundation for high-performance, real-time object detection in resource-constrained environments while maintaining good accuracy for general-purpose applications.
