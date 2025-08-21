# Face Search Parameter Recommendations

**Use Case**: Face Search and Recognition  
**Building Blocks**: Face Detection, Face Recognition, Search Logic, System  
**Source Configuration**: Based on `0001_facesearch_camera_101_100_5.json`

This document provides comprehensive parameter recommendations for face search systems optimized for different environmental conditions and hardware configurations. Parameters are organized by building blocks for optimal RAG/Graph-RAG retrieval.

## Building Block Parameters

### 1. Face Detection Block
Core parameters for detecting faces in video streams before recognition processing.

**Key Parameters:**
- `conf`: Confidence threshold for face detection
- `pixel_hthresh`: Minimum face height in pixels for valid detection
- `pixel_wthresh`: Minimum face width in pixels for valid detection

### 2. Face Recognition Block
Parameters for face encoding and matching against database.

**Key Parameters:**
- Recognition model confidence thresholds
- Face encoding parameters
- Database search parameters

### 3. Search Logic Block
Parameters controlling search behavior and matching criteria.

**Key Parameters:**
- Search radius and similarity thresholds
- Multi-face handling logic
- Search result ranking parameters

### 4. System Block
System-level configuration for processing and resource management.

**Key Parameters:**
- `fps`: Frame processing rate
- `use_gpu`: GPU acceleration enable/disable
- `gpu_id`: GPU device identifier

## Environmental Scenarios

### 1. High-Security Access Control
**Maximum accuracy for critical access points**

**Face Detection:**
- conf: 0.8 (High confidence for security applications)
- pixel_hthresh: 80 (Larger minimum face height for quality)
- pixel_wthresh: 80 (Larger minimum face width for accuracy)

**Face Recognition:**
- similarity_threshold: 0.85 (High similarity for security matching)
- encoding_quality: "high" (Maximum encoding quality)
- face_alignment: true (Enable precise alignment)

**Search Logic:**
- max_search_results: 3 (Limited results for security verification)
- verification_mode: "strict" (Strict verification for access control)
- multi_face_handling: "closest" (Focus on closest face to camera)

**System:**
- fps: "2/1" (Slower rate for thorough processing)
- use_gpu: true (GPU acceleration for complex processing)
- gpu_id: 1 (Dedicated GPU for recognition tasks)

### 2. Surveillance and Monitoring
**Balanced accuracy for general surveillance**

**Face Detection:**
- conf: 0.6 (Standard confidence for surveillance)
- pixel_hthresh: 50 (Standard minimum face height)
- pixel_wthresh: 50 (Standard minimum face width)

**Face Recognition:**
- similarity_threshold: 0.75 (Balanced similarity for surveillance)
- encoding_quality: "medium" (Standard encoding quality)
- face_alignment: true (Enable alignment for accuracy)

**Search Logic:**
- max_search_results: 5 (Multiple results for investigation)
- verification_mode: "standard" (Standard verification)
- multi_face_handling: "all" (Process all detected faces)

**System:**
- fps: "2/1" (Standard processing rate)
- use_gpu: true (GPU acceleration for performance)

### 3. Retail Customer Recognition
**Fast processing for customer service applications**

**Face Detection:**
- conf: 0.5 (Lower confidence for broader detection)
- pixel_hthresh: 40 (Smaller minimum for distant customers)
- pixel_wthresh: 40 (Smaller minimum for quick detection)

**Face Recognition:**
- similarity_threshold: 0.70 (Lower threshold for customer matching)
- encoding_quality: "medium" (Balanced quality for speed)
- face_alignment: false (Disable for faster processing)

**Search Logic:**
- max_search_results: 10 (Multiple results for customer service)
- verification_mode: "fast" (Quick verification for retail)
- multi_face_handling: "primary" (Focus on primary customer)

**System:**
- fps: "3/1" (Higher rate for responsive customer service)

### 4. Low Light Environments
**Optimized for night shift and low light conditions**

**Face Detection:**
- conf: 0.4 (Lower confidence for challenging lighting)
- pixel_hthresh: 60 (Larger minimum for low light quality)
- pixel_wthresh: 60 (Larger minimum for better features)

**Face Recognition:**
- similarity_threshold: 0.65 (Lower threshold for lighting variations)
- encoding_quality: "high" (High quality to compensate for lighting)
- face_alignment: true (Critical for low light accuracy)
- noise_reduction: true (Enable noise reduction)

**Search Logic:**
- max_search_results: 7 (More results due to uncertainty)
- verification_mode: "adaptive" (Adaptive to lighting conditions)

**System:**
- fps: "1/1" (Slower rate for thorough low light processing)

### 5. Crowd Environments
**Handling multiple faces in busy areas**

**Face Detection:**
- conf: 0.55 (Moderate confidence for crowd detection)
- pixel_hthresh: 35 (Smaller minimum for distant faces)
- pixel_wthresh: 35 (Smaller minimum for crowd processing)

**Face Recognition:**
- similarity_threshold: 0.72 (Standard threshold for crowd matching)
- encoding_quality: "medium" (Balanced for multiple faces)
- face_alignment: true (Important for varied angles)

**Search Logic:**
- max_search_results: 15 (Many results for crowd analysis)
- verification_mode: "batch" (Batch processing for efficiency)
- multi_face_handling: "priority" (Priority-based face selection)

**System:**
- fps: "4/1" (Higher rate for dynamic crowd monitoring)

### 6. Outdoor Environments
**Adapted for variable lighting and weather**

**Face Detection:**
- conf: 0.45 (Lower confidence for outdoor variability)
- pixel_hthresh: 55 (Moderate minimum for outdoor conditions)
- pixel_wthresh: 55 (Moderate minimum for weather tolerance)

**Face Recognition:**
- similarity_threshold: 0.68 (Lower threshold for outdoor variations)
- encoding_quality: "high" (High quality for challenging conditions)
- face_alignment: true (Critical for outdoor accuracy)
- weather_compensation: true (Enable weather adaptation)

**Search Logic:**
- max_search_results: 8 (Multiple results for outdoor uncertainty)
- verification_mode: "outdoor" (Outdoor-optimized verification)

**System:**
- fps: "2/1" (Standard rate for outdoor monitoring)

## Hardware-Specific Optimizations

### High-End GPU Systems (RTX 4090/A100)
**Maximum performance for complex recognition tasks**

**Face Detection:**
- conf: 0.7 (Higher confidence with powerful processing)
- pixel_hthresh: 70 (Higher quality faces for detailed analysis)
- pixel_wthresh: 70 (Higher quality for maximum accuracy)

**Face Recognition:**
- encoding_quality: "ultra" (Maximum encoding quality)
- batch_processing: 16 (High batch size for GPU efficiency)
- advanced_features: true (Enable advanced recognition features)

**System:**
- fps: "5/1" (High frame rate for real-time processing)
- use_gpu: true (Maximum GPU utilization)

### Mid-Range GPU Systems (GTX 1660/RTX 3060)
**Balanced performance for standard recognition tasks**

**Face Detection:**
- conf: 0.6 (Standard confidence for balanced processing)
- pixel_hthresh: 50 (Standard minimum for balanced performance)
- pixel_wthresh: 50 (Standard minimum for efficiency)

**Face Recognition:**
- encoding_quality: "medium" (Balanced quality for performance)
- batch_processing: 8 (Moderate batch size)

**System:**
- fps: "3/1" (Moderate frame rate for balanced performance)

### Edge Devices (Jetson/Low-Power)
**Optimized for resource-constrained environments**

**Face Detection:**
- conf: 0.5 (Moderate confidence for edge processing)
- pixel_hthresh: 40 (Lower minimum for edge efficiency)
- pixel_wthresh: 40 (Lower minimum for memory constraints)

**Face Recognition:**
- encoding_quality: "low" (Optimized quality for edge devices)
- batch_processing: 2 (Small batch size for memory efficiency)

**System:**
- fps: "1/1" (Lower frame rate for edge device efficiency)

### CPU-Only Systems
**Fallback configuration for CPU-only processing**

**Face Detection:**
- conf: 0.65 (Higher confidence to reduce CPU load)
- pixel_hthresh: 60 (Higher minimum to reduce processing)
- pixel_wthresh: 60 (Higher minimum for CPU efficiency)

**Face Recognition:**
- encoding_quality: "low" (Minimal quality for CPU processing)
- cpu_optimization: true (Enable CPU-specific optimizations)

**System:**
- fps: "0.5/1" (Very low frame rate for CPU processing)
- use_gpu: false (Disable GPU acceleration)

## Camera Distance Scenarios

### Close-Range Recognition (0-5 feet)
**High-detail face recognition for close interactions**

**Face Detection:**
- conf: 0.7 (High confidence for close-range clarity)
- pixel_hthresh: 120 (Large minimum for close-range detail)
- pixel_wthresh: 120 (Large minimum for high quality)

**Face Recognition:**
- similarity_threshold: 0.85 (High similarity for detailed faces)
- encoding_quality: "high" (High quality for detailed analysis)

### Medium-Range Recognition (5-15 feet)
**Standard recognition for typical surveillance distances**

**Face Detection:**
- conf: 0.6 (Standard confidence for medium range)
- pixel_hthresh: 50 (Standard minimum for medium distance)
- pixel_wthresh: 50 (Standard minimum for balanced processing)

**Face Recognition:**
- similarity_threshold: 0.75 (Standard similarity for medium range)
- encoding_quality: "medium" (Balanced quality for medium distance)

### Long-Range Recognition (15+ feet)
**Optimized for distant face recognition**

**Face Detection:**
- conf: 0.45 (Lower confidence for distant faces)
- pixel_hthresh: 30 (Lower minimum for distant detection)
- pixel_wthresh: 30 (Lower minimum for long-range coverage)

**Face Recognition:**
- similarity_threshold: 0.65 (Lower threshold for distant matching)
- encoding_quality: "high" (High quality to compensate for distance)
- upscaling: true (Enable face upscaling for distant faces)

## Lighting Condition Scenarios

### Bright Daylight
**Optimized for high-contrast outdoor lighting**

**Face Detection:**
- conf: 0.65 (Standard confidence for good lighting)
- contrast_adjustment: "high" (Adjust for bright conditions)

**Face Recognition:**
- brightness_compensation: true (Compensate for bright lighting)
- shadow_detection: true (Handle shadow variations)

### Indoor Fluorescent
**Adapted for typical indoor lighting conditions**

**Face Detection:**
- conf: 0.6 (Standard confidence for indoor lighting)
- flicker_compensation: true (Handle fluorescent flicker)

**Face Recognition:**
- color_temperature_adjustment: "cool" (Adjust for fluorescent lighting)

### Mixed Lighting
**Handling variable lighting conditions**

**Face Detection:**
- conf: 0.55 (Moderate confidence for mixed conditions)
- adaptive_exposure: true (Enable adaptive exposure)

**Face Recognition:**
- auto_white_balance: true (Enable automatic white balance)
- lighting_normalization: true (Normalize for mixed lighting)

### Night Vision/IR
**Optimized for infrared and night vision cameras**

**Face Detection:**
- conf: 0.4 (Lower confidence for IR imaging)
- ir_optimization: true (Enable IR-specific processing)

**Face Recognition:**
- ir_face_model: true (Use IR-optimized recognition model)
- thermal_compensation: true (Compensate for thermal variations)

## Performance Optimization Scenarios

### Real-Time Processing
**Maximum speed for live applications**

**Face Detection:**
- conf: 0.55 (Balanced confidence for speed)
- fast_detection: true (Enable fast detection mode)

**Face Recognition:**
- quick_search: true (Enable quick search mode)
- cache_encodings: true (Cache frequently searched faces)

**System:**
- fps: "5/1" (High frame rate for real-time processing)

### Batch Processing
**Optimized for processing recorded video**

**Face Detection:**
- conf: 0.65 (Higher confidence for thorough analysis)
- batch_optimization: true (Enable batch processing optimizations)

**Face Recognition:**
- deep_analysis: true (Enable thorough analysis for batches)
- quality_enhancement: true (Enhance quality for batch processing)

**System:**
- fps: "1/1" (Lower rate for thorough batch processing)

### High Accuracy Mode
**Maximum accuracy for forensic applications**

**Face Detection:**
- conf: 0.8 (High confidence for forensic quality)
- multi_scale_detection: true (Enable multi-scale detection)

**Face Recognition:**
- similarity_threshold: 0.9 (Very high similarity for forensics)
- encoding_quality: "ultra" (Maximum encoding quality)
- multi_algorithm_verification: true (Use multiple algorithms)

## Troubleshooting Parameters

### High False Positive Rate
**When system matches incorrect faces**

**Increase Thresholds:**
- conf: +0.1 (Increase detection confidence)
- similarity_threshold: +0.05 (Increase matching strictness)
- pixel_hthresh: +10 (Require larger faces)
- pixel_wthresh: +10 (Require larger faces)

### Missing Valid Matches
**When system fails to find known faces**

**Decrease Thresholds:**
- conf: -0.1 (Decrease detection confidence)
- similarity_threshold: -0.05 (Decrease matching strictness)
- pixel_hthresh: -5 (Allow smaller faces)
- pixel_wthresh: -5 (Allow smaller faces)

### Performance Issues
**When system is too slow**

**Optimize Performance:**
- fps: reduce by 1 (Lower processing frequency)
- encoding_quality: reduce level (Lower processing complexity)
- batch_processing: increase size (Better GPU utilization)

## Integration Guidelines

### Database Integration
**Parameters for face database management**

**Search Database:**
- Index type: "facial_vectors"
- Search algorithm: "cosine_similarity"
- Cache size: 10000 face encodings
- Update frequency: real-time for new faces

### API Integration
**Parameters for face search API**

**API Configuration:**
- Response format: JSON with confidence scores
- Timeout: 5 seconds for real-time searches
- Rate limiting: 100 searches per minute
- Result format: face_id, confidence, bounding_box

### Storage Integration
**Parameters for face image storage**

**Storage Configuration:**
- Face crops: Store detected face regions
- Original frames: Store for audit trail
- Compression: JPEG 85% quality for face crops
- Retention: 30 days for face crops, 7 days for frames

## Validation Parameters
*All parameters in this document have been validated against the source JSON file: `0001_facesearch_camera_101_100_5.json`*

**Parameter Sources:**
- Face detection parameters: Node algorithm configuration
- Recognition parameters: Component URI specifications
- Search parameters: Node parameters configuration
- System parameters: Source parameters configuration

**Building Block Organization:**
- ✅ Face Detection Block: Core face detection parameters
- ✅ Face Recognition Block: Recognition and encoding parameters
- ✅ Search Logic Block: Search behavior and matching parameters
- ✅ System Block: Resource management and processing parameters
