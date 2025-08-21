# YOLOv7 General COCO Model Documentation

## Overview
This document describes the `yolov7_general_coco.json` model card, which defines a YOLOv7-based object detection model trained on the COCO 2017 dataset for general-purpose object detection.

## Model Identity

### Component Information
- **Component ID**: `general7Detection`
- **Version**: `v0.0.1`
- **Release**: `stable`
- **Component Type**: `node.algorithm.objdet` (Object Detection Algorithm Node)
- **Container Image**: `generalobjdetection:latest`

### Model Details
- **Name**: YOLOv7 General COCO
- **Category**: Object Detector
- **Framework**: PyTorch
- **License**: Closed source
- **Repository**: https://github.com/poc.org

## Architecture & Parameters

### Model Architecture
- **Total Parameters**: 37.2 million
- **Backbone**: E-ELAN (Enhanced Efficient Layer Aggregation Network)
- **Neck**: FPN-PANet (Feature Pyramid Network with Path Aggregation)
- **Head**: Detect(V7) (YOLOv7 detection head)
- **Anchor Configuration**: `[[12,16],[19,36],[40,28],[36,75],[76,55],[72,146],[142,110],[192,243],[459,401]]`

### Training Information
- **Pretrained**: Yes
- **Input Resolution**: 640×640 pixels
- **Dataset**: COCO 2017
- **Dataset Type**: General objects
- **Number of Classes**: 80
- **Object Classes**: 
  - People: person
  - Vehicles: bicycle, car, motorcycle, airplane, bus, train, truck, boat
  - Traffic: traffic light, fire hydrant, stop sign, parking meter
  - Animals: bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe
  - Objects: backpack, umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket
  - Kitchen: bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake
  - Furniture: chair, couch, potted plant, bed, dining table, toilet
  - Electronics: tv, laptop, mouse, remote, keyboard, cell phone, microwave, oven, toaster, sink, refrigerator
  - Miscellaneous: book, clock, vase, scissors, teddy bear, hair drier, toothbrush, bench

## Hardware Requirements

### GPU Requirements
- **GPU Required**: Yes
- **Minimum GPU Memory**: 6 GB
- **Recommended GPU**: NVIDIA RTX 3060
- **CPU Cores**: 4
- **RAM**: 8 GB

### Runtime Environment
- **Docker Image**: `generalobjdetection:latest`
- **Python Version**: 3.8
- **CUDA Version**: 11.0
- **cuDNN Version**: 8.0
- **Operating System**: Ubuntu 20.04

## Configuration Parameters

### Input/Output Configuration
- **Inputs**: `["input_0"]` (single input stream)
- **Outputs**: `["output_0"]` (single output stream)
- **Batch Size**: Up to 8 (configurable 1-8)
- **Supports Batching**: Yes
- **Requires Frames**: Yes
- **Frame Size**: 1920×1080 (configurable)

### Tunable Parameters

#### Detection Parameters
1. **Confidence Threshold (`conf`)**
   - Type: Float
   - Range: 0.1 - 1.0
   - Default: 0.4
   - Purpose: Minimum confidence score for detections

2. **NMS IoU Threshold (`nms_iou`)**
   - Type: Float
   - Range: 0.1 - 1.0
   - Default: 0.4
   - Purpose: IoU threshold for Non-Maximum Suppression

#### Performance Settings
1. **Mixed Precision (`use_fp16`)**
   - Type: Boolean
   - Default: true
   - Purpose: Use 16-bit floating point for faster inference

2. **CUDA Acceleration (`use_cuda`)**
   - Type: Boolean
   - Default: true
   - Purpose: Enable GPU acceleration

3. **Batch Processing (`enable_batching`)**
   - Type: Boolean
   - Default: true
   - Purpose: Process multiple frames simultaneously

#### Image Processing Settings
1. **Input Width (`width`)**
   - Type: Integer
   - Range: 416 - 1280
   - Default: 640
   - Purpose: Model input width

2. **Input Height (`height`)**
   - Type: Integer
   - Range: 416 - 1280
   - Default: 640
   - Purpose: Model input height

3. **Batch Size (`batch_size`)**
   - Type: Integer
   - Range: 1 - 8
   - Default: 8
   - Purpose: Number of frames processed together

4. **ROI Batch Size (`roiBatchSize`)**
   - Type: Integer
   - Range: 1 - 4
   - Default: 1
   - Purpose: Batch size for Region of Interest processing

#### Decoder Settings
1. **Decoder Type (`decoderType`)**
   - Type: String
   - Options: "TURBO", "DALI"
   - Default: "TURBO"
   - Purpose: Image decoding method

2. **Interpolation Type (`interpolationType`)**
   - Type: String
   - Options: "INTERP_NN", "INTERP_LINEAR", "INTERP_CUBIC", "INTERP_TRIANGULAR", "INTERP_GAUSSIAN", "INTERP_LANCZOS3"
   - Default: "INTERP_GAUSSIAN"
   - Purpose: Image resizing interpolation method

3. **Full Image Processing (`FullImage`)**
   - Type: Boolean
   - Default: true
   - Purpose: Process entire image vs. crop/ROI

## Performance Benchmarks

### Test Conditions
- **Hardware**: NVIDIA RTX 3060
- **Input Resolution**: 640×640
- **Decoder**: TURBO
- **Confidence Threshold**: 0.4
- **NMS Threshold**: 0.4
- **Precision**: FP32
- **Evaluation Dataset**: COCO val2017

### Throughput Performance
- **Batch Size 1**: 90 FPS
- **Batch Size 4**: 150 FPS
- **Batch Size 8**: 170 FPS

### Accuracy Metrics
- **mAP@0.5**: 55.4%
- **mAP@0.5:0.95**: 41.6%
- **Precision**: 0.78
- **Recall**: 0.72

## Data Contract

### Input Requirements
- **Consumes**: `["rgb_frames"]` (RGB video frames)
- **Input Formats**: `["OD1"]` (Object Detection format 1)

### Output Specifications
- **Produces**: `["object_bboxes", "object_classifications"]`
- **Output Formats**: `["OD1"]` (Object Detection format 1)

## Usage Notes

### Best Use Cases
- General-purpose object detection across 80 common object classes
- Surveillance and monitoring applications
- Traffic analysis and vehicle detection
- Person detection and tracking preparation
- General computer vision baseline applications

### Limitations
- Limited to 80 COCO classes (cannot detect custom objects)
- Performance may degrade on very high-resolution inputs
- Requires GPU for optimal performance
- Closed-source license limits customization

### Pipeline Integration
This model serves as an excellent starting point for computer vision pipelines requiring general object detection. It can be chained with:
- **Tracking algorithms** for object following
- **Policy filters** for zone-based filtering
- **Usecase logic** for behavior analysis
- **Format converters** for data transformation

## References
1. [YOLOv7: Trainable bag-of-freebies sets new state-of-the-art](https://arxiv.org/abs/2207.02696)
2. [COCO Dataset](https://cocodataset.org/)

## Author Information
- **Author**: poc
- **Email**: poc@ai.org
- **GitHub**: https://github.com/poc.org
- **License**: Closed source
- **Tags**: alert
