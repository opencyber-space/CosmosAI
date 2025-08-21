# Weapon Detection - Parameter Recommendations

## Use Case Overview
Weapon detection identifies firearms, knives, and other dangerous weapons in surveillance footage, critical for security applications in schools, airports, government buildings, and public spaces.

## Environmental Condition Parameters

### 1. Low Light Conditions
**Optimized for poor lighting in parking lots, nighttime monitoring, or dimly lit areas**

conf: 0.1 (Very low confidence to detect concealed weapons in poor lighting)
nms_iou: 0.4 (Standard IoU threshold for non-maximum suppression)
width: 1920 (Higher resolution for detailed weapon detection in low light)
height: 1080 (High resolution for weapon clarity in dark environments)
window: 10 (Extended observation window for low-light confirmation)
percentage_of_violation: 50 (50% violation threshold for low-confidence environments)
alert_interval: 300 (Extended alert interval to reduce noise in uncertain conditions)
severity: high (High severity despite low confidence due to weapon threat)
fps: 1 (Reduced frame rate for better processing in low light)
use_fp16: true (Enable FP16 for performance optimization)

### 2. High Accuracy Requirements
**Maximum precision for critical security areas like airports or government buildings**

conf: 0.2 (Balanced confidence for reliable weapon detection)
nms_iou: 0.3 (Lower IoU for better weapon separation)
width: 1920 (Maximum resolution for detailed weapon analysis)
height: 1080 (High resolution for accurate weapon identification)
window: 5 (Shorter window for rapid threat response)
percentage_of_violation: 30 (Lower threshold for high-security areas)
alert_interval: 120 (Frequent alerts for critical security zones)
severity: high (Maximum severity for weapon threats)
withoutAssociationObjectsNeeded: False (Require person association for accuracy)
fps: 2 (Higher frame rate for real-time threat detection)
use_cuda: true (Enable CUDA for high-performance processing)

### 3. Wide Area Coverage
**Optimized for large spaces like stadiums, campuses, or public squares**

conf: 0.05 (Very low confidence for distant weapon detection)
nms_iou: 0.5 (Higher IoU for overlapping distant objects)
width: 1920 (Maximum resolution for distant weapon visibility)
height: 1080 (High resolution for wide area monitoring)
window: 15 (Extended window for distant weapon confirmation)
percentage_of_violation: 60 (Higher threshold due to distance uncertainty)
alert_interval: 240 (Moderate alert frequency for wide area monitoring)
severity: medium (Medium severity due to distance-related uncertainty)
fps: 0.5 (Reduced frame rate for processing efficiency in wide areas)
max_dets: 100 (Higher detection limit for crowded areas)

### 4. False Positive Reduction
**Minimizing incorrect weapon alerts in environments with tool-like objects**

conf: 0.15 (Higher confidence to reduce false weapon detections)
nms_iou: 0.3 (Lower IoU for better object separation)
width: 1280 (Standard resolution for balanced processing)
height: 720 (Standard resolution for efficient false positive reduction)
window: 20 (Extended observation to verify genuine weapons)
percentage_of_violation: 40 (Moderate threshold to reduce false alarms)
alert_interval: 600 (Longer interval to reduce alert fatigue)
severity: medium (Medium severity to balance security and false alarms)
withoutAssociationObjectsNeeded: False (Require person association to reduce false positives)
fps: 1 (Standard frame rate for thorough analysis)

## Camera Height and Positioning Scenarios

### 1. High-Mounted Security Cameras (8+ meters height)
**Overhead security cameras in large facilities or outdoor areas**

conf: 0.05 (Very low confidence for small weapons viewed from above)
nms_iou: 0.5 (Higher IoU for overlapping overhead objects)
width: 1920 (Maximum resolution for distant overhead weapon detection)
height: 1080 (High resolution for small weapon visibility from height)
window: 25 (Extended window due to overhead perspective challenges)
percentage_of_violation: 70 (Higher threshold for overhead detection uncertainty)
alert_interval: 300 (Standard alert interval for overhead monitoring)
severity: medium (Medium severity due to overhead detection challenges)
fps: 0.3 (Low frame rate for processing efficiency at height)
max_dets: 50 (Moderate detection limit for overhead perspective)

### 2. Standard Height Security Cameras (3-5 meters)
**Wall-mounted cameras in corridors, entrances, and security checkpoints**

conf: 0.1 (Standard low confidence for reliable weapon detection)
nms_iou: 0.4 (Standard IoU threshold for weapon separation)
width: 1280 (Standard resolution for typical security monitoring)
height: 720 (Standard resolution for efficient processing)
window: 10 (Standard observation window for weapon confirmation)
percentage_of_violation: 50 (Balanced threshold for standard mounting)
alert_interval: 300 (Standard alert interval for security monitoring)
severity: high (High severity for standard security applications)
withoutAssociationObjectsNeeded: False (Standard person association requirement)
fps: 1 (Standard frame rate for real-time monitoring)

### 3. Eye-Level Security Cameras (1.5-2 meters height)
**Close-range monitoring for detailed weapon analysis**

conf: 0.15 (Higher confidence for clear, close-range weapon detection)
nms_iou: 0.3 (Lower IoU for detailed weapon separation)
width: 1280 (Standard resolution sufficient for close-range detection)
height: 720 (Standard resolution for efficient close monitoring)
window: 5 (Shorter window for immediate close-range threat response)
percentage_of_violation: 30 (Lower threshold for clear close-range detection)
alert_interval: 180 (Frequent alerts for close-range security monitoring)
severity: high (High severity for close-range weapon threats)
fps: 2 (Higher frame rate for detailed close-range analysis)
use_cuda: true (Enable CUDA for responsive close-range processing)

### 4. Angled Security Cameras (45-60 degree tilt)
**Cameras positioned to monitor specific zones or chokepoints**

conf: 0.12 (Moderate confidence accounting for angle distortion)
nms_iou: 0.4 (Standard IoU for angled perspective)
width: 1280 (Standard resolution for angled monitoring)
height: 720 (Standard resolution for efficient angled processing)
window: 12 (Extended window for angle-induced uncertainty)
percentage_of_violation: 55 (Higher threshold for perspective challenges)
alert_interval: 300 (Standard alert interval for angled monitoring)
severity: high (High severity maintaining security priority)
fps: 1 (Standard frame rate for angled perspective analysis)

### 5. PTZ Security Cameras (Pan-Tilt-Zoom)
**Motorized cameras for focused weapon threat tracking**

conf: 0.2 (Higher confidence during zoom for detailed weapon analysis)
nms_iou: 0.3 (Lower IoU for detailed zoomed weapon detection)
width: 1920 (High resolution for zoom weapon detail)
height: 1080 (High resolution for tracked weapon clarity)
window: 3 (Very short window for immediate zoom threat response)
percentage_of_violation: 25 (Low threshold during focused tracking)
alert_interval: 60 (Frequent alerts during active weapon tracking)
severity: high (Maximum severity for focused weapon tracking)
withoutAssociationObjectsNeeded: False (Require person association during tracking)
fps: 3 (High frame rate for smooth weapon tracking)

## Hardware-Specific Optimizations

### High-End Security Systems (RTX 4090/A100)
**Maximum performance for critical security infrastructure**

conf: 0.1 (Balanced confidence with processing power)
nms_iou: 0.4 (Standard IoU with processing headroom)
use_cuda: true (Enable CUDA for maximum security performance)
use_fp16: false (Disable FP16 for maximum weapon detection accuracy)
batch_size: 8 (High batch size for efficient GPU utilization)
width: 1920 (Maximum resolution for detailed weapon analysis)
height: 1080 (High resolution for comprehensive security monitoring)
fps: 4 (High frame rate for real-time security response)
max_dets: 200 (High detection limit for complex security scenes)
window: 8 (Balanced window with high processing power)

### Mid-Range Security Systems (GTX 1660/RTX 3060)
**Balanced performance for standard security deployments**

conf: 0.1 (Standard confidence for mid-range security)
nms_iou: 0.4 (Standard IoU for balanced performance)
use_cuda: true (Enable CUDA for available GPU acceleration)
use_fp16: true (Enable FP16 for performance optimization)
batch_size: 4 (Moderate batch size for balanced processing)
width: 1280 (Moderate resolution for balanced security monitoring)
height: 720 (Standard resolution for efficient performance)
fps: 2 (Moderate frame rate for balanced security processing)
max_dets: 100 (Moderate detection limit for standard scenes)
window: 10 (Standard window for mid-range systems)

### Edge Security Devices/CPU-Only
**Optimized for distributed security nodes or budget deployments**

conf: 0.15 (Higher confidence to reduce CPU processing load)
nms_iou: 0.4 (Standard IoU for CPU efficiency)
use_cuda: false (Disable CUDA for CPU-only security systems)
use_fp16: false (Disable FP16 for CPU compatibility)
batch_size: 1 (Single batch for CPU efficiency)
width: 640 (Lower resolution for CPU security processing)
height: 480 (Reduced resolution for CPU performance)
fps: 0.5 (Low frame rate for CPU processing capability)
max_dets: 20 (Limited detections for CPU efficiency)
window: 15 (Extended window to reduce CPU processing frequency)
alert_interval: 600 (Longer intervals to reduce CPU load)

## Distance-Based Parameter Adjustments

### Close Range (0-5 meters)
**Detailed weapon monitoring for checkpoints and entry points**

conf: 0.15 (Higher confidence for clear close-range weapon detection)
nms_iou: 0.3 (Lower IoU for detailed close weapon separation)
window: 5 (Short window for immediate close-range threat response)
percentage_of_violation: 30 (Low threshold for clear weapon visibility)
alert_interval: 120 (Frequent alerts for close-range security)
severity: high (High severity for close-range weapon threats)
fps: 2 (Higher frame rate for detailed close-range monitoring)

### Medium Range (5-15 meters)
**Standard security monitoring for corridors and open areas**

conf: 0.1 (Standard confidence for typical security range)
nms_iou: 0.4 (Standard IoU for balanced weapon detection)
window: 10 (Standard window for medium-range confirmation)
percentage_of_violation: 50 (Balanced threshold for standard range)
alert_interval: 300 (Standard alert interval for security monitoring)
severity: high (High severity for security applications)
fps: 1 (Standard frame rate for medium-range monitoring)

### Long Range (15+ meters)
**Wide area security monitoring for perimeters and large spaces**

conf: 0.05 (Very low confidence for distant weapon detection)
nms_iou: 0.5 (Higher IoU for distant overlapping objects)
window: 20 (Extended window for distant weapon confirmation)
percentage_of_violation: 70 (Higher threshold for distance uncertainty)
alert_interval: 300 (Standard alert interval for long-range monitoring)
severity: medium (Medium severity due to distance limitations)
width: 1920 (Higher resolution for distant weapon visibility)
height: 1080 (High resolution for long-range detection capability)
fps: 0.5 (Reduced frame rate for long-range processing efficiency)

## Specific Security Environment Scenarios

### Airport Security Checkpoints
**High-accuracy weapon detection for aviation security**

conf: 0.2 (Higher confidence for critical aviation security)
nms_iou: 0.3 (Lower IoU for detailed weapon separation)
window: 3 (Very short window for immediate aviation threat response)
percentage_of_violation: 25 (Low threshold for aviation security priority)
alert_interval: 60 (Frequent alerts for aviation security)
severity: high (Maximum severity for aviation threats)
withoutAssociationObjectsNeeded: False (Require person association for accuracy)
fps: 3 (High frame rate for aviation security responsiveness)

### School Security Systems
**Balanced detection to protect students while minimizing false alarms**

conf: 0.12 (Moderate confidence for school environment balance)
nms_iou: 0.4 (Standard IoU for school monitoring)
window: 12 (Extended window to verify threats in school settings)
percentage_of_violation: 45 (Moderate threshold for school environments)
alert_interval: 180 (Moderate alert frequency for school security)
severity: high (High severity for student safety)
withoutAssociationObjectsNeeded: False (Require person association in schools)
fps: 1 (Standard frame rate for school monitoring)

### Government Building Security
**High-accuracy detection for sensitive government facilities**

conf: 0.15 (Higher confidence for government security accuracy)
nms_iou: 0.3 (Lower IoU for detailed government facility monitoring)
window: 5 (Short window for immediate government threat response)
percentage_of_violation: 35 (Lower threshold for government security)
alert_interval: 120 (Frequent alerts for government facilities)
severity: high (Maximum severity for government security)
use_cuda: true (Enable high-performance processing for government)
fps: 2 (Higher frame rate for government security responsiveness)

### Public Event Security
**Wide area monitoring for concerts, festivals, and gatherings**

conf: 0.08 (Lower confidence for crowded public event detection)
nms_iou: 0.5 (Higher IoU for crowded event overlapping objects)
window: 15 (Extended window for crowded event confirmation)
percentage_of_violation: 60 (Higher threshold for crowd uncertainty)
alert_interval: 240 (Moderate alert frequency for public events)
severity: high (High severity for public safety)
max_dets: 150 (Higher detection limit for crowded events)
fps: 1 (Standard frame rate for crowded event processing)

## Common Issues and Parameter Solutions

### False Positives (Incorrect Weapon Alerts)
**Parameter adjustments to reduce false weapon alarms**

conf: 0.2 (Increase confidence threshold for weapons)
window: 20 (Extend observation window for verification)
percentage_of_violation: 30 (Lower threshold to require more certainty)
alert_interval: 600 (Increase interval to reduce false alert frequency)
withoutAssociationObjectsNeeded: False (Require person association)
severity: medium (Reduce severity to minimize false escalation)

### Missing Weapons (False Negatives)
**Parameter adjustments to catch more concealed weapons**

conf: 0.05 (Decrease confidence threshold for weapon detection)
window: 5 (Reduce window for quicker weapon detection)
percentage_of_violation: 70 (Higher threshold to catch edge cases)
alert_interval: 180 (Decrease interval for more frequent weapon checks)
fps: 2 (Increase frame rate for better weapon capture)
width: 1920 (Higher resolution for weapon detail)
height: 1080 (High resolution for weapon visibility)

### Performance Issues in Security Systems
**Parameter adjustments for resource-constrained security deployments**

width: 640 (Reduce resolution for security system performance)
height: 480 (Lower resolution for processing efficiency)
use_fp16: true (Enable FP16 for security system performance)
batch_size: 1 (Reduce batch size for memory efficiency)
fps: 0.5 (Lower frame rate for processing capability)
max_dets: 20 (Limit detections for security system efficiency)
window: 15 (Extend window to reduce processing frequency)
alert_interval: 600 (Longer intervals to reduce processing load)

This comprehensive weapon detection parameter guide ensures optimal security performance while balancing threat detection accuracy with system efficiency across diverse security environments.
