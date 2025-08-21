# Camera Tampering Detection Parameter Recommendations

**Use Case**: Camera Tampering Detection  
**Building Blocks**: Tampering Detection, System Monitoring, Alert Management  
**Source Configuration**: Based on `0001_cameraTampering_camera_55_70_11.json`

This document provides comprehensive parameter recommendations for camera tampering detection systems optimized for different environmental conditions and hardware configurations. Parameters are organized by building blocks for optimal RAG/Graph-RAG retrieval.

## Building Block Parameters

### 1. Tampering Detection Block
Core parameters for camera tampering analysis including scene change, blur, brightness, and darkness detection.

**Key Parameters:**
- `scenechange_threshold`: Sensitivity threshold for scene change detection
- `scenechange_min_scene_len`: Minimum frames to confirm scene change
- `blurThreshold`: Threshold for detecting image blur
- `blurnessFrameCountThresh`: Consecutive blur frames to trigger alert
- `brightPixelRatio`: Ratio of bright pixels to detect overexposure
- `brightnessFrameCountThresh`: Consecutive bright frames for alert
- `darknessThresh`: Darkness detection threshold
- `darknessFrameCountThresh`: Consecutive dark frames for alert
- `dimDark`: Darkness intensity parameter

### 2. Video Processing Block
Image decoding and preprocessing parameters for tampering analysis.

**Key Parameters:**
- `decoder_width`: Video decoder width resolution
- `decoder_height`: Video decoder height resolution
- `batch_size`: Processing batch size for efficiency
- `decoderType`: Decoder type (DALI for GPU acceleration)
- `interpolationType`: Image interpolation method

### 3. Alert Management Block
Alert generation and notification parameters.

**Key Parameters:**
- `alert_interval`: Time interval between alerts (seconds)
- `severity`: Alert severity level (high/medium/low)

### 4. System Block
System-level configuration for processing and resource management.

**Key Parameters:**
- `fps`: Frame processing rate (frames per second)
- `use_gpu`: Enable GPU acceleration
- `gpu_id`: GPU device identifier

## Environmental Scenarios

### 1. Indoor Surveillance (Standard)
**Controlled lighting environment with minimal ambient changes**

**Tampering Detection:**
- scenechange_threshold: 70 (Standard sensitivity for controlled environment)
- scenechange_min_scene_len: 12 (Standard confirmation time)
- blurThreshold: 100 (Moderate blur detection for indoor conditions)
- blurnessFrameCountThresh: 12 (Standard frame count for blur confirmation)
- brightPixelRatio: 0.18 (Balanced bright pixel detection)
- brightnessFrameCountThresh: 12 (Standard frame count for brightness)
- darknessThresh: 0.2 (Standard darkness detection)
- darknessFrameCountThresh: 12 (Standard frame count for darkness)
- dimDark: 10 (Standard darkness intensity)

**Video Processing:**
- decoder_width: 640 (Standard resolution for indoor monitoring)
- decoder_height: 360 (Optimized for processing efficiency)
- batch_size: 8 (Efficient batch processing)
- decoderType: "DALI" (GPU-accelerated decoding)
- interpolationType: "INTERP_GAUSSIAN" (Standard interpolation)

**Alert Management:**
- alert_interval: 300 (5-minute alert interval for standard monitoring)
- severity: "high" (High severity for security critical areas)

**System:**
- fps: "4/1" (Standard frame rate for tampering detection)
- use_gpu: true (Enable GPU acceleration)
- gpu_id: 0 (Primary GPU device)

### 2. Outdoor Security Cameras
**Variable lighting conditions with environmental changes**

**Tampering Detection:**
- scenechange_threshold: 85 (Higher threshold for outdoor environmental changes)
- scenechange_min_scene_len: 15 (Extended confirmation for weather variations)
- blurThreshold: 120 (Higher threshold for outdoor conditions)
- blurnessFrameCountThresh: 15 (Extended frame count for outdoor blur)
- brightPixelRatio: 0.25 (Higher ratio for outdoor brightness variations)
- brightnessFrameCountThresh: 18 (Extended frame count for sun exposure)
- darknessThresh: 0.15 (Lower threshold for natural darkness)
- darknessFrameCountThresh: 15 (Extended frame count for natural darkness)
- dimDark: 8 (Lower intensity for outdoor darkness)

**Video Processing:**
- decoder_width: 1280 (Higher resolution for outdoor monitoring)
- decoder_height: 720 (HD resolution for detailed analysis)
- batch_size: 6 (Moderate batch size for higher resolution)

**Alert Management:**
- alert_interval: 600 (10-minute interval for outdoor environment)
- severity: "medium" (Balanced severity for outdoor conditions)

**System:**
- fps: "3/1" (Moderate frame rate for outdoor monitoring)

### 3. Critical Infrastructure
**Maximum sensitivity for high-security areas**

**Tampering Detection:**
- scenechange_threshold: 50 (Low threshold for maximum sensitivity)
- scenechange_min_scene_len: 8 (Quick confirmation for immediate response)
- blurThreshold: 80 (Lower threshold for sensitive blur detection)
- blurnessFrameCountThresh: 8 (Quick blur confirmation)
- brightPixelRatio: 0.12 (Lower ratio for sensitive brightness detection)
- brightnessFrameCountThresh: 8 (Quick brightness confirmation)
- darknessThresh: 0.25 (Higher threshold for sensitive darkness detection)
- darknessFrameCountThresh: 8 (Quick darkness confirmation)
- dimDark: 12 (Higher intensity for sensitive darkness)

**Alert Management:**
- alert_interval: 120 (2-minute immediate alert interval)
- severity: "high" (Maximum severity for critical areas)

**System:**
- fps: "6/1" (Higher frame rate for maximum monitoring)

### 4. Low Light Environments
**Optimized for night vision and low light conditions**

**Tampering Detection:**
- scenechange_threshold: 60 (Moderate threshold for low light changes)
- scenechange_min_scene_len: 10 (Standard confirmation time)
- blurThreshold: 90 (Lower threshold for low light blur detection)
- blurnessFrameCountThresh: 10 (Standard frame count)
- brightPixelRatio: 0.08 (Very low ratio for low light conditions)
- brightnessFrameCountThresh: 20 (Extended frame count for rare brightness)
- darknessThresh: 0.35 (Higher threshold adapted for low light)
- darknessFrameCountThresh: 8 (Quick confirmation for darkness changes)
- dimDark: 15 (Higher intensity for low light environments)

**Video Processing:**
- decoder_width: 896 (Moderate resolution for low light processing)
- decoder_height: 504 (Optimized for low light analysis)

**System:**
- fps: "5/1" (Higher frame rate for low light monitoring)

### 5. High Traffic Areas
**Reduced false positives in busy environments**

**Tampering Detection:**
- scenechange_threshold: 90 (Higher threshold to reduce false positives)
- scenechange_min_scene_len: 20 (Extended confirmation for busy areas)
- blurThreshold: 130 (Higher threshold for motion blur tolerance)
- blurnessFrameCountThresh: 18 (Extended frame count for motion tolerance)
- brightPixelRatio: 0.22 (Higher ratio for varied lighting)
- brightnessFrameCountThresh: 15 (Standard frame count)
- darknessThresh: 0.18 (Moderate threshold for crowd shadows)
- darknessFrameCountThresh: 15 (Standard frame count)
- dimDark: 8 (Lower intensity for crowd environments)

**Alert Management:**
- alert_interval: 900 (15-minute interval for busy areas)
- severity: "medium" (Balanced severity to reduce alert noise)

### 6. Weather-Resistant Monitoring
**Adapted for harsh weather conditions**

**Tampering Detection:**
- scenechange_threshold: 95 (Very high threshold for weather changes)
- scenechange_min_scene_len: 25 (Extended confirmation for weather events)
- blurThreshold: 140 (High threshold for rain/snow blur)
- blurnessFrameCountThresh: 20 (Extended frame count for weather blur)
- brightPixelRatio: 0.30 (High ratio for weather reflections)
- brightnessFrameCountThresh: 25 (Extended frame count for weather glare)
- darknessThresh: 0.12 (Lower threshold for storm darkness)
- darknessFrameCountThresh: 20 (Extended frame count for weather darkness)
- dimDark: 6 (Lower intensity for natural weather darkness)

**System:**
- fps: "2/1" (Lower frame rate for weather stability)

## Hardware-Specific Optimizations

### High-End GPU Systems (RTX 4090/A100)
**Maximum performance configurations**

**Video Processing:**
- decoder_width: 1920 (Maximum resolution for detailed analysis)
- decoder_height: 1080 (Full HD processing)
- batch_size: 16 (High batch size for efficient GPU utilization)

**System:**
- fps: "8/1" (High frame rate for real-time monitoring)
- use_gpu: true (Enable maximum GPU acceleration)

### Mid-Range GPU Systems (GTX 1660/RTX 3060)
**Balanced performance configurations**

**Video Processing:**
- decoder_width: 1280 (Moderate resolution for balanced processing)
- decoder_height: 720 (HD resolution for efficient performance)
- batch_size: 8 (Moderate batch size for balanced performance)

**System:**
- fps: "4/1" (Standard frame rate for balanced monitoring)

### Edge Devices (Jetson/Low-Power)
**Optimized for resource-constrained environments**

**Video Processing:**
- decoder_width: 640 (Lower resolution for edge processing)
- decoder_height: 360 (Optimized for edge devices)
- batch_size: 4 (Small batch size for memory efficiency)

**System:**
- fps: "2/1" (Lower frame rate for edge device efficiency)

## Camera Height Scenarios

### High-Mounted Cameras (15+ feet)
**Wide area coverage with distant tampering detection**

**Tampering Detection:**
- scenechange_threshold: 75 (Moderate threshold for distant changes)
- blurThreshold: 110 (Higher threshold for distance blur)

**Video Processing:**
- decoder_width: 1280 (Higher resolution for distant detail)
- decoder_height: 720 (HD resolution for distant analysis)

### Standard Height Cameras (8-12 feet)
**Balanced monitoring for typical security heights**

**Tampering Detection:**
- scenechange_threshold: 70 (Standard threshold for normal height)
- blurThreshold: 100 (Standard blur detection)

**Video Processing:**
- decoder_width: 640 (Standard resolution for normal height)
- decoder_height: 360 (Optimized for standard monitoring)

### Low-Mounted Cameras (4-6 feet)
**Close-range monitoring with detailed tampering detection**

**Tampering Detection:**
- scenechange_threshold: 65 (Lower threshold for close-range sensitivity)
- blurThreshold: 90 (Lower threshold for close-range blur detection)

**Video Processing:**
- decoder_width: 896 (Moderate resolution for close-range detail)
- decoder_height: 504 (Optimized for close-range analysis)

### PTZ Camera Configurations
**Pan-tilt-zoom cameras with dynamic positioning**

**Tampering Detection:**
- scenechange_threshold: 80 (Higher threshold for PTZ movement)
- scenechange_min_scene_len: 18 (Extended confirmation for PTZ stabilization)

**System:**
- fps: "6/1" (Higher frame rate for PTZ tracking)

## Troubleshooting Parameters

### High False Positive Rate
**When system generates too many false alerts**

**Increase Thresholds:**
- scenechange_threshold: +15 (Reduce scene change sensitivity)
- blurThreshold: +20 (Reduce blur sensitivity)
- brightPixelRatio: +0.05 (Reduce brightness sensitivity)
- alert_interval: +300 (Increase alert spacing)

### Missing Real Tampering Events
**When system fails to detect actual tampering**

**Decrease Thresholds:**
- scenechange_threshold: -10 (Increase scene change sensitivity)
- blurThreshold: -15 (Increase blur sensitivity)
- scenechange_min_scene_len: -3 (Reduce confirmation time)
- alert_interval: -120 (Decrease alert spacing)

### Performance Optimization
**When system performance is inadequate**

**Optimize Processing:**
- batch_size: increase by 2-4 (Better GPU utilization)
- decoder_width/height: reduce by 20% (Lower processing load)
- fps: reduce by 1-2 (Lower processing frequency)

## Integration Guidelines

### Database Integration
**Parameters for alert storage and retrieval**

**MongoDB Configuration:**
- Collection: "tampering_alerts"
- Index fields: ["timestamp", "camera_id", "severity"]
- Retention policy: 90 days for high severity, 30 days for others

### MINIO Storage
**Parameters for evidence storage**

**Storage Configuration:**
- Bucket: "tampering-evidence"
- Retention: 30 days for video clips
- Compression: H.264 for storage efficiency

### Redis Integration
**Parameters for real-time data streaming**

**Redis Configuration:**
- TTL: 3600 seconds for real-time data
- Channel: "tampering_alerts_live"
- Batch size: 10 for efficient streaming

## Validation Parameters
*All parameters in this document have been validated against the source JSON file: `0001_cameraTampering_camera_55_70_11.json`*

**Parameter Sources:**
- Tampering detection parameters: Node algorithm configuration
- Video processing parameters: Node settings configuration  
- Alert parameters: Node parameters configuration
- System parameters: Source parameters configuration

**Building Block Organization:**
- ✅ Tampering Detection Block: Core tampering analysis parameters
- ✅ Video Processing Block: Image processing and decoding parameters
- ✅ Alert Management Block: Alert generation and notification parameters
- ✅ System Block: Resource management and processing parameters
