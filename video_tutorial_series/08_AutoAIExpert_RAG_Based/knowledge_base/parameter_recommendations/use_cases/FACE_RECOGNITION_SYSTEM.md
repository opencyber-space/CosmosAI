# Face Recognition System (FRS) - Parameter Recommendations

## Use Case Overview
Face recognition identifies and verifies individuals in surveillance footage, critical for access control, security systems, attendance tracking, and identity verification applications.

## Environmental Condition Parameters

### 1. Low Light Conditions
**Optimized for poor lighting in nighttime monitoring or dimly lit environments**

conf: 0.25 (Lower confidence threshold for face detection in poor lighting)
pixel_hthresh: 40 (Reduced minimum face height for low light detection)
pixel_wthresh: 40 (Reduced minimum face width for low light detection)
iou: 0.45 (Standard IoU threshold for face overlapping)
max_dets: 300 (Higher detection limit for low light scenarios)
dist2d_threshold: 1 (Standard distance threshold for face-person association)
width: 1920 (Higher resolution for face detail in low light)
height: 1080 (High resolution for face clarity in dark environments)
fps: 1 (Reduced frame rate for better processing in low light)
use_fp16: true (Enable FP16 for performance optimization)
severity: medium (Medium severity for low-confidence face recognition)

### 2. High Accuracy Requirements
**Maximum precision for critical security areas like banks or government facilities**

conf: 0.6 (Higher confidence for reliable face detection)
pixel_hthresh: 60 (Higher minimum face height for accuracy)
pixel_wthresh: 60 (Higher minimum face width for accuracy)
iou: 0.4 (Lower IoU for better face separation)
max_dets: 200 (Moderate detection limit for high accuracy)
dist2d_threshold: 0.8 (Stricter distance threshold for accuracy)
width: 1920 (Maximum resolution for detailed face analysis)
height: 1080 (High resolution for accurate face identification)
fps: 2 (Higher frame rate for real-time accurate recognition)
use_cuda: true (Enable CUDA for high-performance processing)
severity: high (High severity for accurate face recognition)

### 3. Wide Area Coverage
**Optimized for large spaces like lobbies, campuses, or public areas**

conf: 0.2 (Lower confidence for distant face detection)
pixel_hthresh: 30 (Reduced minimum face height for distant faces)
pixel_wthresh: 30 (Reduced minimum face width for distant faces)
iou: 0.5 (Higher IoU for overlapping distant faces)
max_dets: 400 (Higher detection limit for crowded areas)
dist2d_threshold: 1.5 (Relaxed distance threshold for wide area coverage)
width: 1920 (Maximum resolution for distant face visibility)
height: 1080 (High resolution for wide area monitoring)
fps: 0.5 (Reduced frame rate for processing efficiency in wide areas)
severity: medium (Medium severity due to distance-related uncertainty)

### 4. False Positive Reduction
**Minimizing incorrect face recognition in crowded environments**

conf: 0.5 (Higher confidence to reduce false face detections)
pixel_hthresh: 70 (Higher minimum face height to filter small faces)
pixel_wthresh: 70 (Higher minimum face width to filter small faces)
iou: 0.3 (Lower IoU for better face separation)
max_dets: 150 (Limited detections to reduce false positives)
dist2d_threshold: 0.6 (Stricter distance threshold for accuracy)
width: 1280 (Standard resolution for balanced processing)
height: 720 (Standard resolution for efficient false positive reduction)
fps: 1 (Standard frame rate for thorough analysis)
severity: medium (Medium severity to balance recognition and false alarms)

## Camera Height and Positioning Scenarios

### 1. High-Mounted Cameras (6+ meters height)
**Overhead cameras for wide area face monitoring**

conf: 0.15 (Very low confidence for small faces viewed from above)
pixel_hthresh: 25 (Very small minimum face height for overhead perspective)
pixel_wthresh: 25 (Very small minimum face width for overhead perspective)
iou: 0.5 (Higher IoU for overlapping overhead faces)
max_dets: 300 (Higher detection limit for overhead perspective)
dist2d_threshold: 2 (Relaxed distance threshold for overhead challenges)
width: 1920 (Maximum resolution for distant overhead face detection)
height: 1080 (High resolution for small face visibility from height)
fps: 0.3 (Low frame rate for processing efficiency at height)
severity: low (Lower severity due to overhead detection challenges)

### 2. Standard Height Cameras (2-4 meters)
**Wall-mounted cameras for entrances, corridors, and access points**

conf: 0.25 (Standard confidence for typical face recognition)
pixel_hthresh: 50 (Standard minimum face height for clear detection)
pixel_wthresh: 50 (Standard minimum face width for clear detection)
iou: 0.45 (Standard IoU threshold for face separation)
max_dets: 300 (Standard detection limit for typical scenarios)
dist2d_threshold: 1 (Standard distance threshold for face-person association)
width: 1280 (Standard resolution for typical face recognition)
height: 720 (Standard resolution for efficient processing)
fps: 1 (Standard frame rate for real-time recognition)
severity: medium (Medium severity for standard face recognition)

### 3. Eye-Level Cameras (1.5-2 meters height)
**Close-range face recognition for detailed access control**

conf: 0.4 (Higher confidence for clear, close-range face detection)
pixel_hthresh: 60 (Higher minimum face height for detailed recognition)
pixel_wthresh: 60 (Higher minimum face width for detailed recognition)
iou: 0.4 (Lower IoU for detailed face separation)
max_dets: 200 (Moderate detection limit for close-range scenarios)
dist2d_threshold: 0.8 (Stricter distance threshold for close-range accuracy)
width: 1280 (Standard resolution sufficient for close-range recognition)
height: 720 (Standard resolution for efficient close monitoring)
fps: 2 (Higher frame rate for detailed close-range analysis)
use_cuda: true (Enable CUDA for responsive close-range processing)
severity: high (High severity for close-range face recognition)

### 4. Angled Cameras (30-45 degree tilt)
**Cameras positioned for specific zone coverage with angle challenges**

conf: 0.3 (Moderate confidence accounting for angle distortion)
pixel_hthresh: 45 (Slightly reduced minimum face height for angle challenges)
pixel_wthresh: 45 (Slightly reduced minimum face width for angle challenges)
iou: 0.45 (Standard IoU for angled perspective)
max_dets: 250 (Moderate detection limit for angled scenarios)
dist2d_threshold: 1.2 (Relaxed distance threshold for perspective challenges)
width: 1280 (Standard resolution for angled monitoring)
height: 720 (Standard resolution for efficient angled processing)
fps: 1 (Standard frame rate for angled perspective analysis)
severity: medium (Medium severity for angled face recognition)

### 5. PTZ Cameras (Pan-Tilt-Zoom)
**Motorized cameras for focused face tracking and recognition**

conf: 0.5 (Higher confidence during zoom for detailed face analysis)
pixel_hthresh: 80 (Higher minimum face height for zoom detail)
pixel_wthresh: 80 (Higher minimum face width for zoom detail)
iou: 0.3 (Lower IoU for detailed zoomed face detection)
max_dets: 100 (Limited detections for focused tracking)
dist2d_threshold: 0.6 (Stricter distance threshold during focused tracking)
width: 1920 (High resolution for zoom face detail)
height: 1080 (High resolution for tracked face clarity)
fps: 3 (High frame rate for smooth face tracking)
severity: high (High severity for focused face tracking)

## Hardware-Specific Optimizations

### High-End Systems (RTX 4090/A100)
**Maximum performance for critical face recognition infrastructure**

conf: 0.25 (Balanced confidence with processing power)
pixel_hthresh: 50 (Standard minimum face dimensions)
pixel_wthresh: 50 (Standard minimum face dimensions)
use_cuda: true (Enable CUDA for maximum face recognition performance)
use_fp16: false (Disable FP16 for maximum face recognition accuracy)
batch_size: 8 (High batch size for efficient GPU utilization)
width: 1920 (Maximum resolution for detailed face analysis)
height: 1080 (High resolution for comprehensive face recognition)
fps: 4 (High frame rate for real-time face recognition)
max_dets: 400 (High detection limit for complex scenes)
iou: 0.45 (Standard IoU with processing headroom)

### Mid-Range Systems (GTX 1660/RTX 3060)
**Balanced performance for standard face recognition deployments**

conf: 0.25 (Standard confidence for mid-range systems)
pixel_hthresh: 50 (Standard minimum face dimensions)
pixel_wthresh: 50 (Standard minimum face dimensions)
use_cuda: true (Enable CUDA for available GPU acceleration)
use_fp16: true (Enable FP16 for performance optimization)
batch_size: 4 (Moderate batch size for balanced processing)
width: 1280 (Moderate resolution for balanced face recognition)
height: 720 (Standard resolution for efficient performance)
fps: 2 (Moderate frame rate for balanced face processing)
max_dets: 200 (Moderate detection limit for standard scenes)
iou: 0.45 (Standard IoU for balanced performance)

### Edge Devices/CPU-Only
**Optimized for distributed face recognition nodes or budget deployments**

conf: 0.3 (Higher confidence to reduce CPU processing load)
pixel_hthresh: 60 (Higher minimum face dimensions for CPU efficiency)
pixel_wthresh: 60 (Higher minimum face dimensions for CPU efficiency)
use_cuda: false (Disable CUDA for CPU-only systems)
use_fp16: false (Disable FP16 for CPU compatibility)
batch_size: 1 (Single batch for CPU efficiency)
width: 640 (Lower resolution for CPU face processing)
height: 480 (Reduced resolution for CPU performance)
fps: 0.5 (Low frame rate for CPU processing capability)
max_dets: 50 (Limited detections for CPU efficiency)
iou: 0.4 (Standard IoU for CPU processing)

## Distance-Based Parameter Adjustments

### Close Range (0-3 meters)
**Detailed face recognition for access control and security checkpoints**

conf: 0.4 (Higher confidence for clear close-range face detection)
pixel_hthresh: 70 (Higher minimum face height for detailed recognition)
pixel_wthresh: 70 (Higher minimum face width for detailed recognition)
iou: 0.4 (Lower IoU for detailed close face separation)
max_dets: 150 (Moderate detection limit for close-range scenarios)
dist2d_threshold: 0.8 (Strict distance threshold for close-range accuracy)
fps: 2 (Higher frame rate for detailed close-range recognition)
severity: high (High severity for close-range face recognition)

### Medium Range (3-8 meters)
**Standard face recognition for lobbies, corridors, and monitoring areas**

conf: 0.25 (Standard confidence for typical face recognition range)
pixel_hthresh: 50 (Standard minimum face height)
pixel_wthresh: 50 (Standard minimum face width)
iou: 0.45 (Standard IoU for balanced face detection)
max_dets: 300 (Standard detection limit for typical scenarios)
dist2d_threshold: 1 (Standard distance threshold for face-person association)
fps: 1 (Standard frame rate for medium-range recognition)
severity: medium (Medium severity for standard face recognition)

### Long Range (8+ meters)
**Wide area face recognition for large spaces and perimeter monitoring**

conf: 0.15 (Lower confidence for distant face detection)
pixel_hthresh: 30 (Reduced minimum face height for distant faces)
pixel_wthresh: 30 (Reduced minimum face width for distant faces)
iou: 0.5 (Higher IoU for distant overlapping faces)
max_dets: 400 (Higher detection limit for wide area scenarios)
dist2d_threshold: 1.5 (Relaxed distance threshold for distance uncertainty)
width: 1920 (Higher resolution for distant face visibility)
height: 1080 (High resolution for long-range face detection)
fps: 0.5 (Reduced frame rate for long-range processing efficiency)
severity: medium (Medium severity due to distance limitations)

## Specific Application Environment Scenarios

### Access Control Systems
**High-accuracy face recognition for building entry and secure areas**

conf: 0.5 (Higher confidence for security access control)
pixel_hthresh: 60 (Higher minimum face height for security accuracy)
pixel_wthresh: 60 (Higher minimum face width for security accuracy)
iou: 0.4 (Lower IoU for detailed access control recognition)
max_dets: 100 (Limited detections for focused access control)
dist2d_threshold: 0.7 (Strict distance threshold for access accuracy)
fps: 2 (Higher frame rate for access control responsiveness)
use_cuda: true (Enable high-performance processing for security)
severity: high (High severity for access control systems)

### Attendance Tracking
**Balanced recognition for employee monitoring and time tracking**

conf: 0.3 (Moderate confidence for attendance tracking balance)
pixel_hthresh: 45 (Moderate minimum face height for attendance)
pixel_wthresh: 45 (Moderate minimum face width for attendance)
iou: 0.45 (Standard IoU for attendance monitoring)
max_dets: 200 (Moderate detection limit for attendance scenarios)
dist2d_threshold: 1 (Standard distance threshold for attendance tracking)
fps: 1 (Standard frame rate for attendance monitoring)
severity: medium (Medium severity for attendance applications)

### Retail Customer Recognition
**Privacy-conscious face recognition for customer service enhancement**

conf: 0.25 (Lower confidence for customer privacy balance)
pixel_hthresh: 40 (Lower minimum face height for customer scenarios)
pixel_wthresh: 40 (Lower minimum face width for customer scenarios)
iou: 0.5 (Higher IoU for customer privacy considerations)
max_dets: 300 (Higher detection limit for retail crowds)
dist2d_threshold: 1.2 (Relaxed distance threshold for customer comfort)
fps: 0.5 (Lower frame rate for customer privacy)
severity: low (Lower severity for customer-facing applications)

### VIP Recognition
**High-priority face recognition for important individuals**

conf: 0.6 (High confidence for VIP recognition accuracy)
pixel_hthresh: 70 (High minimum face height for VIP detail)
pixel_wthresh: 70 (High minimum face width for VIP detail)
iou: 0.3 (Lower IoU for detailed VIP face separation)
max_dets: 50 (Limited detections for focused VIP recognition)
dist2d_threshold: 0.6 (Strict distance threshold for VIP accuracy)
fps: 3 (High frame rate for VIP responsiveness)
use_cuda: true (Enable maximum performance for VIP recognition)
severity: high (Maximum severity for VIP applications)

## Common Issues and Parameter Solutions

### False Positives (Incorrect Face Recognition)
**Parameter adjustments to reduce false face identification**

conf: 0.5 (Increase confidence threshold for faces)
pixel_hthresh: 70 (Increase minimum face height)
pixel_wthresh: 70 (Increase minimum face width)
iou: 0.3 (Lower IoU for better face separation)
max_dets: 100 (Limit detections to reduce false matches)
dist2d_threshold: 0.6 (Stricter distance threshold for accuracy)
severity: medium (Reduce severity to minimize false escalation)

### Missing Faces (False Negatives)
**Parameter adjustments to catch more faces in challenging conditions**

conf: 0.15 (Decrease confidence threshold for face detection)
pixel_hthresh: 30 (Reduce minimum face height for small faces)
pixel_wthresh: 30 (Reduce minimum face width for small faces)
iou: 0.5 (Higher IoU to capture edge cases)
max_dets: 400 (Increase detection limit for comprehensive coverage)
dist2d_threshold: 1.5 (Relaxed distance threshold for edge cases)
fps: 2 (Increase frame rate for better face capture)
width: 1920 (Higher resolution for face detail)
height: 1080 (High resolution for face visibility)

### Performance Issues in Face Recognition Systems
**Parameter adjustments for resource-constrained face recognition deployments**

width: 640 (Reduce resolution for face recognition performance)
height: 480 (Lower resolution for processing efficiency)
use_fp16: true (Enable FP16 for face recognition performance)
batch_size: 1 (Reduce batch size for memory efficiency)
fps: 0.5 (Lower frame rate for processing capability)
max_dets: 50 (Limit detections for face recognition efficiency)
pixel_hthresh: 60 (Higher minimum to reduce processing load)
pixel_wthresh: 60 (Higher minimum to reduce processing load)

This comprehensive face recognition parameter guide ensures optimal performance while balancing recognition accuracy with system efficiency across diverse face recognition environments and applications.
