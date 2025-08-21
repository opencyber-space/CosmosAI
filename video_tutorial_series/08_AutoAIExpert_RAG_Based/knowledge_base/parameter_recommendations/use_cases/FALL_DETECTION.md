# Fall Detection - Parameter Recommendations

## Use Case Overview
Fall detection identifies when a person has fallen and may need assistance, critical for elderly care facilities, hospitals, workplaces, and home monitoring systems.

## Environmental Condition Parameters

### 1. Low Light Conditions
**Optimized for poor lighting scenarios with infrared or minimal illumination**

conf: 0.3 (Lower confidence threshold to detect people in poor lighting)
confidence: 0.25 (Lower object detection confidence for dim environments)
fallConfidence: 0.6 (Reduced fall confidence threshold for uncertain lighting)
personConfidence: 0.4 (Lower person detection confidence in low light)
fall_time: 90 (Extended observation time to confirm falls in poor visibility)
non_fall_time: 3 (Longer recovery time before clearing fall state)
alert_interval: 450 (Extended alert interval to reduce noise in uncertain conditions)
severity: medium (Medium severity for low-confidence detections)
fps: 0.5 (Reduced frame rate to improve processing in low light)
use_fp16: true (Enable FP16 for better low-light performance)

### 2. High Accuracy Requirements
**Maximum precision for critical care environments**

conf: 0.4 (Balanced confidence for reliable detection)
confidence: 0.35 (Higher confidence for accurate object detection)
fallConfidence: 0.8 (High fall confidence to minimize false positives)
personConfidence: 0.6 (High person confidence for accurate identification)
fall_time: 45 (Shorter observation for faster response in critical situations)
non_fall_time: 2 (Quick recovery time for immediate re-detection)
alert_interval: 180 (Frequent alerts for high-priority environments)
severity: high (High severity for critical care scenarios)
trigger_block: true (Block subsequent triggers during processing)
trigger_interval: 1 (Immediate trigger response)

### 3. Wide Area Coverage
**Optimized for large spaces with distant subjects**

conf: 0.2 (Very low confidence to detect small, distant figures)
confidence: 0.2 (Lower confidence for distant object detection)
fallConfidence: 0.5 (Reduced confidence due to distance uncertainty)
personConfidence: 0.3 (Lower person confidence for distant detection)
fall_time: 120 (Extended observation time for distant fall verification)
non_fall_time: 4 (Longer recovery time for distant subjects)
alert_interval: 300 (Standard alert interval for large area monitoring)
severity: medium (Medium severity due to distance-related uncertainty)
width: 1920 (Higher resolution for distant object clarity)
height: 1080 (Higher resolution for better distant detection)
fps: 0.25 (Reduced frame rate for processing efficiency in wide areas)

### 4. False Positive Reduction
**Minimizing incorrect fall alerts in active environments**

conf: 0.5 (Higher confidence to reduce false detections)
confidence: 0.45 (Increased confidence for reliable object detection)
fallConfidence: 0.85 (Very high fall confidence to minimize false positives)
personConfidence: 0.7 (High person confidence for accurate identification)
fall_time: 30 (Shorter time to quickly distinguish true falls)
non_fall_time: 1 (Quick recovery for active environments)
alert_interval: 600 (Longer interval to reduce alert fatigue)
severity: low (Lower severity to reduce unnecessary escalation)
trigger_block: true (Block rapid successive triggers)
trigger_interval: 2 (Delayed trigger to verify genuine falls)
associate: False (Disable association to reduce processing complexity)

## Camera Height and Positioning Scenarios

### 1. High-Mounted Cameras (12+ meters height)
**Ceiling-mounted cameras in large facilities, warehouses, or atriums**

conf: 0.15 (Very low confidence for small human figures from height)
confidence: 0.15 (Minimal confidence threshold for distant detection)
fallConfidence: 0.4 (Lower fall confidence due to viewing angle challenges)
personConfidence: 0.25 (Reduced person confidence for overhead perspective)
fall_time: 180 (Extended observation due to perspective distortion)
non_fall_time: 5 (Longer recovery time for overhead angle challenges)
alert_interval: 240 (Moderate alert frequency for high-mounted monitoring)
severity: low (Lower severity due to detection uncertainty from height)
width: 1920 (Maximum resolution for distant human detection)
height: 1080 (High resolution for small figure clarity)
fps: 0.2 (Very low frame rate for processing efficiency at height)
iou: 0.3 (Lower IoU threshold for overlapping distant objects)

### 2. Standard Height Cameras (3-4 meters)
**Wall-mounted cameras in corridors, rooms, and care facilities**

conf: 0.25 (Standard confidence for typical mounting height)
confidence: 0.3 (Balanced confidence for clear human detection)
fallConfidence: 0.7 (Standard fall confidence for optimal viewing angle)
personConfidence: 0.5 (Standard person confidence for clear visibility)
fall_time: 60 (Standard observation time for reliable fall detection)
non_fall_time: 2 (Standard recovery time for typical scenarios)
alert_interval: 300 (Standard alert interval for care environments)
severity: medium (Medium severity for balanced response)
width: 1280 (Standard resolution for typical monitoring)
height: 720 (Standard resolution for efficient processing)
fps: 1 (Standard frame rate for real-time monitoring)
trigger_block: true (Enable trigger blocking for clean alerts)
trigger_interval: 1 (Immediate response for critical fall events)

### 3. Low-Mounted Cameras (1-2 meters height)
**Bedside cameras, wheelchair-accessible mounting, or room-level monitoring**

conf: 0.35 (Higher confidence for close-range, clear detection)
confidence: 0.4 (Higher confidence for detailed close-range detection)
fallConfidence: 0.8 (High fall confidence for clear, close-range falls)
personConfidence: 0.6 (High person confidence for detailed visibility)
fall_time: 45 (Shorter observation time for clear, close falls)
non_fall_time: 2 (Standard recovery time for close monitoring)
alert_interval: 180 (Frequent alerts for close-range critical monitoring)
severity: high (High severity for close-range, high-confidence detection)
width: 1280 (Standard resolution sufficient for close range)
height: 720 (Standard resolution for efficient close monitoring)
fps: 2 (Higher frame rate for detailed close-range analysis)
associate: False (Disable association for simpler close-range processing)

### 4. Angled Cameras (30-45 degree tilt)
**Wall-mounted cameras with downward angle for corner coverage**

conf: 0.3 (Moderate confidence for angled perspective challenges)
confidence: 0.32 (Balanced confidence for perspective distortion)
fallConfidence: 0.65 (Moderate fall confidence accounting for angle distortion)
personConfidence: 0.45 (Reduced confidence due to perspective challenges)
fall_time: 75 (Extended time to account for angle-induced uncertainty)
non_fall_time: 3 (Longer recovery for perspective-related false positives)
alert_interval: 300 (Standard alert interval for angled monitoring)
severity: medium (Medium severity for perspective-challenged detection)
width: 1280 (Standard resolution for angled perspective)
height: 720 (Standard resolution for efficient angled processing)
fps: 1 (Standard frame rate for angled perspective analysis)
iou: 0.4 (Higher IoU threshold for angled object overlap)

### 5. PTZ Camera (Pan-Tilt-Zoom) Tracking
**Motorized cameras that can follow and zoom on subjects**

conf: 0.4 (Higher confidence during zoom for detailed analysis)
confidence: 0.45 (Higher confidence when zoomed for clear detection)
fallConfidence: 0.75 (High fall confidence during focused tracking)
personConfidence: 0.65 (High person confidence during zoom tracking)
fall_time: 30 (Shorter time due to focused, detailed view)
non_fall_time: 1 (Quick recovery for continuous tracking)
alert_interval: 120 (Frequent alerts during active tracking)
severity: high (High severity for focused, high-detail monitoring)
width: 1920 (High resolution for zoom detail)
height: 1080 (High resolution for tracked subject clarity)
fps: 2 (Higher frame rate for smooth tracking analysis)
trigger_block: false (Allow continuous triggers during tracking)
trigger_interval: 1 (Immediate response during focused tracking)

## Hardware-Specific Optimizations

### High-End GPU Systems (RTX 4090/A100)
**Maximum performance configurations for powerful hardware**

conf: 0.25 (Balanced confidence for high-performance processing)
confidence: 0.3 (Standard confidence with processing headroom)
fallConfidence: 0.7 (Standard fall confidence with processing power)
personConfidence: 0.5 (Standard person confidence for reliable detection)
use_cuda: true (Enable CUDA acceleration for GPU processing)
use_fp16: false (Disable FP16 for maximum accuracy on powerful GPU)
batch_size: 4 (Higher batch size for efficient GPU utilization)
width: 1920 (Maximum resolution for detailed analysis)
height: 1080 (High resolution for comprehensive detection)
fps: 4 (High frame rate for real-time detailed monitoring)
max_dets: 100 (High detection limit for complex scenes)

### Mid-Range GPU Systems (GTX 1660/RTX 3060)
**Balanced performance for moderate hardware**

conf: 0.3 (Moderate confidence for balanced processing)
confidence: 0.32 (Balanced confidence for mid-range performance)
fallConfidence: 0.7 (Standard fall confidence for reliable detection)
personConfidence: 0.5 (Standard person confidence for balanced processing)
use_cuda: true (Enable CUDA for available GPU acceleration)
use_fp16: true (Enable FP16 for performance optimization)
batch_size: 2 (Moderate batch size for balanced performance)
width: 1280 (Moderate resolution for balanced processing)
height: 720 (Standard resolution for efficient performance)
fps: 2 (Moderate frame rate for balanced real-time processing)
max_dets: 50 (Moderate detection limit for balanced performance)

### Edge Devices/CPU-Only Systems
**Optimized for low-power, embedded, or CPU-only deployments**

conf: 0.4 (Higher confidence to reduce processing load)
confidence: 0.4 (Higher confidence for efficient CPU processing)
fallConfidence: 0.8 (High fall confidence to reduce false processing)
personConfidence: 0.6 (Higher confidence to minimize CPU overhead)
use_cuda: false (Disable CUDA for CPU-only systems)
use_fp16: false (Disable FP16 for CPU compatibility)
batch_size: 1 (Single batch for CPU efficiency)
width: 640 (Lower resolution for CPU processing efficiency)
height: 480 (Reduced resolution for CPU performance)
fps: 0.5 (Low frame rate for CPU processing capability)
max_dets: 20 (Limited detections for CPU efficiency)
fall_time: 90 (Extended time to reduce CPU processing frequency)
alert_interval: 600 (Longer intervals to reduce CPU load)

## Distance-Based Parameter Adjustments

### Close Range (0-3 meters)
**Detailed monitoring for bedside, wheelchair, or close personal care**

conf: 0.4 (Higher confidence for clear, close-range detection)
confidence: 0.4 (High confidence for detailed close visibility)
fallConfidence: 0.8 (High fall confidence for clear close-range falls)
personConfidence: 0.6 (High person confidence for detailed close analysis)
fall_time: 30 (Quick response for close-range critical falls)
non_fall_time: 1 (Immediate recovery for close monitoring)
alert_interval: 120 (Frequent alerts for close-range critical care)
severity: high (High severity for close-range monitoring)

### Medium Range (3-8 meters)
**Standard room monitoring, hallways, common areas**

conf: 0.25 (Standard confidence for typical monitoring range)
confidence: 0.3 (Balanced confidence for standard room monitoring)
fallConfidence: 0.7 (Standard fall confidence for optimal range)
personConfidence: 0.5 (Standard person confidence for clear visibility)
fall_time: 60 (Standard observation time for reliable detection)
non_fall_time: 2 (Standard recovery time for typical scenarios)
alert_interval: 300 (Standard alert interval for room monitoring)
severity: medium (Medium severity for balanced room monitoring)

### Long Range (8+ meters)
**Large hall monitoring, auditoriums, or wide area coverage**

conf: 0.15 (Lower confidence for distant figure detection)
confidence: 0.2 (Reduced confidence for distant object detection)
fallConfidence: 0.5 (Lower fall confidence due to distance uncertainty)
personConfidence: 0.3 (Reduced person confidence for distant subjects)
fall_time: 120 (Extended observation for distant fall verification)
non_fall_time: 4 (Longer recovery for distant detection challenges)
alert_interval: 300 (Standard alert interval for wide area monitoring)
severity: medium (Medium severity due to distance limitations)
width: 1920 (Higher resolution for distant object clarity)
height: 1080 (High resolution for distant detection capability)

## Specialized Care Environment Scenarios

### Elderly Care Facilities
**Enhanced sensitivity for slower movements and balance issues**

conf: 0.2 (Very low confidence for slower elderly movements)
confidence: 0.25 (Lower confidence for gradual elderly falls)
fallConfidence: 0.5 (Reduced confidence due to slower fall patterns)
personConfidence: 0.4 (Lower confidence for elderly mobility variations)
fall_time: 120 (Extended observation for gradual elderly falls)
non_fall_time: 6 (Longer recovery time for elderly assistance needs)
alert_interval: 180 (Frequent alerts for elderly care priority)
severity: high (High severity for elderly care criticality)
fps: 1 (Standard frame rate for elderly movement patterns)
trigger_block: false (Allow multiple triggers for elderly assistance)

### Post-Surgery Recovery
**Adapted for limited mobility and medication effects**

conf: 0.3 (Moderate confidence for restricted movement patterns)
confidence: 0.3 (Balanced confidence for post-surgery limitations)
fallConfidence: 0.6 (Moderate fall confidence for medication effects)
personConfidence: 0.5 (Standard confidence for clear patient monitoring)
fall_time: 90 (Extended time for medication-affected responses)
non_fall_time: 4 (Longer recovery accounting for surgical limitations)
alert_interval: 120 (Frequent alerts for post-surgery monitoring)
severity: high (High severity for post-operative care)
trigger_interval: 1 (Immediate response for post-surgery patients)
associate: False (Simplified processing for focused patient care)

### Wheelchair-Accessible Areas
**Specialized detection for wheelchair users and mobility aids**

conf: 0.25 (Balanced confidence for wheelchair fall patterns)
confidence: 0.3 (Standard confidence for wheelchair detection)
fallConfidence: 0.7 (Higher confidence for distinct wheelchair falls)
personConfidence: 0.5 (Standard confidence for wheelchair users)
fall_time: 45 (Shorter time for wheelchair tipping detection)
non_fall_time: 2 (Quick recovery for wheelchair fall scenarios)
alert_interval: 180 (Moderate alert frequency for mobility aid users)
severity: high (High severity for wheelchair user safety)
fps: 1.5 (Slightly higher frame rate for wheelchair movement analysis)
trigger_block: true (Clean alerts for wheelchair incident management)

## Common Issues and Parameter Solutions

### False Positives (Incorrect Fall Alerts)
**Parameter adjustments to reduce false alarms**

fallConfidence: 0.8 (Increase fall confidence threshold)
personConfidence: 0.6 (Increase person detection confidence)
fall_time: 45 (Reduce observation time for quick verification)
alert_interval: 600 (Increase interval to reduce alert frequency)
trigger_block: true (Enable blocking to prevent rapid false alerts)
trigger_interval: 3 (Add delay to verify genuine falls)
severity: medium (Reduce severity to minimize false escalation)

### Missing Falls (False Negatives)
**Parameter adjustments to catch more genuine falls**

conf: 0.15 (Decrease general confidence threshold)
confidence: 0.2 (Lower object detection confidence)
fallConfidence: 0.4 (Decrease fall confidence threshold)
personConfidence: 0.3 (Lower person detection confidence)
fall_time: 120 (Increase observation time for gradual falls)
non_fall_time: 1 (Quick recovery to re-enable detection)
alert_interval: 180 (Decrease interval for more frequent checks)
fps: 2 (Increase frame rate for better fall capture)

### Performance Optimization Issues
**Parameter adjustments for resource-constrained systems**

width: 640 (Reduce resolution for performance)
height: 480 (Lower resolution for processing efficiency)
use_fp16: true (Enable FP16 for performance improvement)
batch_size: 1 (Reduce batch size for memory efficiency)
fps: 0.5 (Lower frame rate for processing capability)
max_dets: 10 (Limit detections for performance)
fall_time: 90 (Extend time to reduce processing frequency)
alert_interval: 600 (Longer intervals to reduce processing load)

This comprehensive fall detection parameter guide ensures optimal performance across diverse care environments while maintaining accuracy and system efficiency.
