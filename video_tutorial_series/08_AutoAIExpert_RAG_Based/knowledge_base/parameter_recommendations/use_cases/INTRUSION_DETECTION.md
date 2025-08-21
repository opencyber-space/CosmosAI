# Intrusion Detection - Parameter Recommendations

## Use Case Overview
Intrusion detection identifies unauthorized entry into restricted areas, critical for perimeter security, building protection, and area monitoring applications.

## Environmental Condition Parameters

### 1. Low Light Conditions
**Optimized for nighttime perimeter monitoring or poorly lit areas**

conf: 0.2 (Lower confidence to detect intruders in poor lighting)
iou: 0.4 (Standard IoU threshold for overlapping objects)
width: 1920 (Higher resolution for intruder detail in low light)
height: 1080 (High resolution for clarity in dark environments)
max_dets: 100 (Higher detection limit for low light scenarios)
fps: 1 (Reduced frame rate for better processing in low light)
use_fp16: true (Enable FP16 for performance optimization)
severity: high (High severity for security intrusion detection)
alert_interval: 180 (Moderate alert frequency for intrusion monitoring)

### 2. High Accuracy Requirements
**Maximum precision for critical security perimeters**

conf: 0.4 (Higher confidence for reliable intrusion detection)
iou: 0.3 (Lower IoU for better object separation)
width: 1920 (Maximum resolution for detailed intrusion analysis)
height: 1080 (High resolution for accurate intrusion identification)
max_dets: 150 (Moderate detection limit for high accuracy)
fps: 2 (Higher frame rate for real-time intrusion detection)
use_cuda: true (Enable CUDA for high-performance processing)
severity: high (Maximum severity for intrusion threats)
alert_interval: 120 (Frequent alerts for critical security)

### 3. Wide Area Coverage
**Optimized for large perimeters, campuses, or facility monitoring**

conf: 0.15 (Lower confidence for distant intrusion detection)
iou: 0.5 (Higher IoU for overlapping distant objects)
width: 1920 (Maximum resolution for distant intrusion visibility)
height: 1080 (High resolution for wide area monitoring)
max_dets: 200 (Higher detection limit for large areas)
fps: 0.5 (Reduced frame rate for processing efficiency)
severity: medium (Medium severity due to distance uncertainty)
alert_interval: 300 (Standard alert interval for wide area monitoring)

### 4. False Positive Reduction
**Minimizing incorrect intrusion alerts from animals or environmental factors**

conf: 0.35 (Higher confidence to reduce false intrusion detections)
iou: 0.3 (Lower IoU for better object separation)
width: 1280 (Standard resolution for balanced processing)
height: 720 (Standard resolution for efficient false positive reduction)
max_dets: 100 (Limited detections to reduce false positives)
fps: 1 (Standard frame rate for thorough analysis)
severity: medium (Medium severity to balance security and false alarms)
alert_interval: 600 (Longer interval to reduce false alert frequency)

## Camera Height and Positioning Scenarios

### 1. High-Mounted Perimeter Cameras (10+ meters height)
**Elevated cameras for wide perimeter coverage**

conf: 0.1 (Very low confidence for small figures from height)
iou: 0.5 (Higher IoU for overlapping overhead objects)
width: 1920 (Maximum resolution for distant intrusion detection)
height: 1080 (High resolution for elevated perspective)
max_dets: 150 (Higher detection limit for overhead perspective)
fps: 0.3 (Low frame rate for processing efficiency at height)
severity: medium (Medium severity due to height detection challenges)
alert_interval: 240 (Moderate alert frequency for elevated monitoring)

### 2. Standard Height Security Cameras (3-6 meters)
**Wall-mounted cameras for fence lines and building perimeters**

conf: 0.25 (Standard confidence for typical security monitoring)
iou: 0.4 (Standard IoU threshold for intrusion separation)
width: 1280 (Standard resolution for typical security monitoring)
height: 720 (Standard resolution for efficient processing)
max_dets: 100 (Standard detection limit for perimeter scenarios)
fps: 1 (Standard frame rate for real-time monitoring)
severity: high (High severity for standard security applications)
alert_interval: 180 (Frequent alerts for perimeter security)

### 3. Ground-Level Detection Cameras (1-2 meters height)
**Low-mounted cameras for detailed intrusion analysis**

conf: 0.3 (Higher confidence for clear, close-range detection)
iou: 0.3 (Lower IoU for detailed object separation)
width: 1280 (Standard resolution sufficient for close range)
height: 720 (Standard resolution for efficient close monitoring)
max_dets: 80 (Moderate detection limit for close-range scenarios)
fps: 2 (Higher frame rate for detailed close-range analysis)
use_cuda: true (Enable CUDA for responsive close-range processing)
severity: high (High severity for close-range intrusion detection)
alert_interval: 120 (Frequent alerts for close-range security)

### 4. PTZ Security Cameras (Pan-Tilt-Zoom)
**Motorized cameras for focused intrusion tracking**

conf: 0.4 (Higher confidence during zoom for detailed analysis)
iou: 0.3 (Lower IoU for detailed zoomed intrusion detection)
width: 1920 (High resolution for zoom detail)
height: 1080 (High resolution for tracked intrusion clarity)
max_dets: 50 (Limited detections for focused tracking)
fps: 3 (High frame rate for smooth intrusion tracking)
severity: high (Maximum severity for focused intrusion tracking)
alert_interval: 60 (Frequent alerts during active tracking)

## Hardware-Specific Optimizations

### High-End Security Systems (RTX 4090/A100)
**Maximum performance for critical security infrastructure**

conf: 0.25 (Balanced confidence with processing power)
use_cuda: true (Enable CUDA for maximum security performance)
use_fp16: false (Disable FP16 for maximum detection accuracy)
batch_size: 8 (High batch size for efficient GPU utilization)
width: 1920 (Maximum resolution for detailed analysis)
height: 1080 (High resolution for comprehensive monitoring)
fps: 4 (High frame rate for real-time security response)
max_dets: 200 (High detection limit for complex scenes)
iou: 0.4 (Standard IoU with processing headroom)

### Mid-Range Security Systems (GTX 1660/RTX 3060)
**Balanced performance for standard security deployments**

conf: 0.25 (Standard confidence for mid-range security)
use_cuda: true (Enable CUDA for available GPU acceleration)
use_fp16: true (Enable FP16 for performance optimization)
batch_size: 4 (Moderate batch size for balanced processing)
width: 1280 (Moderate resolution for balanced monitoring)
height: 720 (Standard resolution for efficient performance)
fps: 2 (Moderate frame rate for balanced processing)
max_dets: 100 (Moderate detection limit for standard scenes)
iou: 0.4 (Standard IoU for balanced performance)

### Edge Devices/CPU-Only
**Optimized for distributed security nodes**

conf: 0.3 (Higher confidence to reduce CPU processing load)
use_cuda: false (Disable CUDA for CPU-only systems)
use_fp16: false (Disable FP16 for CPU compatibility)
batch_size: 1 (Single batch for CPU efficiency)
width: 640 (Lower resolution for CPU processing)
height: 480 (Reduced resolution for CPU performance)
fps: 0.5 (Low frame rate for CPU processing capability)
max_dets: 50 (Limited detections for CPU efficiency)
iou: 0.4 (Standard IoU for CPU processing)
alert_interval: 600 (Longer intervals to reduce CPU load)

## Distance-Based Parameter Adjustments

### Close Range (0-5 meters)
**Detailed intrusion monitoring for immediate perimeter**

conf: 0.35 (Higher confidence for clear close-range detection)
iou: 0.3 (Lower IoU for detailed close object separation)
max_dets: 80 (Moderate detection limit for close-range scenarios)
fps: 2 (Higher frame rate for detailed close-range monitoring)
severity: high (High severity for close-range intrusion)
alert_interval: 120 (Frequent alerts for immediate perimeter)

### Medium Range (5-15 meters)
**Standard intrusion monitoring for facility perimeters**

conf: 0.25 (Standard confidence for typical monitoring range)
iou: 0.4 (Standard IoU for balanced detection)
max_dets: 100 (Standard detection limit for typical scenarios)
fps: 1 (Standard frame rate for medium-range monitoring)
severity: high (High severity for facility security)
alert_interval: 180 (Standard alert interval for perimeter monitoring)

### Long Range (15+ meters)
**Wide area intrusion monitoring for large perimeters**

conf: 0.15 (Lower confidence for distant intrusion detection)
iou: 0.5 (Higher IoU for distant overlapping objects)
max_dets: 150 (Higher detection limit for wide area scenarios)
width: 1920 (Higher resolution for distant visibility)
height: 1080 (High resolution for long-range detection)
fps: 0.5 (Reduced frame rate for long-range processing efficiency)
severity: medium (Medium severity due to distance limitations)
alert_interval: 300 (Standard alert interval for wide area monitoring)

## Specific Security Environment Scenarios

### Industrial Facility Perimeter
**High-security monitoring for manufacturing and processing facilities**

conf: 0.3 (Moderate confidence for industrial environment balance)
iou: 0.4 (Standard IoU for industrial monitoring)
max_dets: 120 (Moderate detection limit for industrial scenarios)
fps: 1 (Standard frame rate for industrial monitoring)
severity: high (High severity for industrial security)
alert_interval: 180 (Moderate alert frequency for industrial facilities)
use_cuda: true (Enable high-performance processing)

### Residential Property Security
**Balanced detection for home and residential area protection**

conf: 0.25 (Lower confidence for residential privacy balance)
iou: 0.4 (Standard IoU for residential monitoring)
max_dets: 80 (Moderate detection limit for residential scenarios)
fps: 1 (Standard frame rate for residential monitoring)
severity: medium (Medium severity for residential applications)
alert_interval: 300 (Standard alert interval for residential security)

### Government/Military Facilities
**Maximum security for sensitive installations**

conf: 0.4 (Higher confidence for government security accuracy)
iou: 0.3 (Lower IoU for detailed government facility monitoring)
max_dets: 100 (Moderate detection limit for focused security)
fps: 2 (Higher frame rate for government security responsiveness)
severity: high (Maximum severity for government security)
alert_interval: 120 (Frequent alerts for government facilities)
use_cuda: true (Enable maximum performance for government)

### Public Space Monitoring
**Area protection for parks, plazas, and public facilities**

conf: 0.2 (Lower confidence for public space complexity)
iou: 0.5 (Higher IoU for crowded public overlapping objects)
max_dets: 150 (Higher detection limit for public crowds)
fps: 1 (Standard frame rate for public space processing)
severity: medium (Medium severity for public space monitoring)
alert_interval: 240 (Moderate alert frequency for public spaces)

## Common Issues and Parameter Solutions

### False Positives (Incorrect Intrusion Alerts)
**Parameter adjustments to reduce false alarms from animals or environmental factors**

conf: 0.4 (Increase confidence threshold for intrusions)
iou: 0.3 (Lower IoU for better object separation)
max_dets: 50 (Limit detections to reduce false positives)
alert_interval: 600 (Increase interval to reduce false alert frequency)
severity: medium (Reduce severity to minimize false escalation)

### Missing Intrusions (False Negatives)
**Parameter adjustments to catch more subtle intrusion attempts**

conf: 0.15 (Decrease confidence threshold for intrusion detection)
iou: 0.5 (Higher IoU to capture edge cases)
max_dets: 200 (Increase detection limit for comprehensive coverage)
fps: 2 (Increase frame rate for better intrusion capture)
width: 1920 (Higher resolution for intrusion detail)
height: 1080 (High resolution for intrusion visibility)
alert_interval: 120 (Decrease interval for more frequent checks)

### Performance Issues in Security Systems
**Parameter adjustments for resource-constrained security deployments**

width: 640 (Reduce resolution for security system performance)
height: 480 (Lower resolution for processing efficiency)
use_fp16: true (Enable FP16 for security system performance)
batch_size: 1 (Reduce batch size for memory efficiency)
fps: 0.5 (Lower frame rate for processing capability)
max_dets: 50 (Limit detections for security system efficiency)
alert_interval: 600 (Longer intervals to reduce processing load)

This comprehensive intrusion detection parameter guide ensures optimal security performance while balancing threat detection accuracy with system efficiency across diverse security environments.
