# ScaleLayout

## Introduction

In AIOS, there are two layout terms used frequently: **AppLayout** and **ScaleLayout**.

---

## AppLayout

- AppLayout is a pipeline structure (Directed Acyclic Graph) that creates a plan for running a use case with AI models (algorithms), policy, and use case blocks, along with necessary sidecars for data manipulation.
- **Example:**  
  To run a Loitering Usecase:  
  `Object Detection → Policy → Tracker → Policy → Usecase`
- **Explanation:**  
  - General Object detection detects people.
  - Policy block filters only persons inside a zone of interest.
  - Filtered persons are tracked.
  - Another policy controls objects tracked for a few seconds.
  - The use case logic sends alerts upon loitering threshold.

---

## ScaleLayout

- ScaleLayout describes how to deploy pods on real hardware (which node, which GPU).
- Multiple cameras/sources can share the same blocks; ScaleLayout defines this sharing.
- **Optimizing ScaleLayout** is crucial for reducing hardware requirements.
- Optimization involves understanding:
  - Model throughput vs. GPU & CPU utilization
  - Hardware (CPU, RAM, GPU utility, GPU RAM)
  - Camera/source grouping

---

## Application

With ScaleLayout and AppLayout, you can:
1. **Evaluate hardware requirements** for the project in optimized mode.
2. **Plan deployment** effectively by consuming calculated hardware.

> **Note:**  
> This document focuses mainly on ScaleLayout optimization, deployment planning, and understanding use cases with respect to hardware requirements.

---

## Concept

Before diving into ScaleLayout optimization, it's important to understand several concepts, based on live project deployments.

### 1. GStreamer Pipeline

- **Input:** RTSP streams or recorded videos.
- **Library:** GStreamer is used to break input feeds into frames for the DAG pipeline.
- **Hardware:** Nvidia GPUs with hardware encoder/decoder (Nvidia Video Codec SDK).
- **Deployment:** GStreamer-based decoder runs as a Docker REST service per GPU. Each GPU in a node will be used for decoding the stream, model also will be deployed in same GPU
- **Function:** Decodes RTSP/video feed to raw data, handles resolution changes and converts to jpeg image, and limits input frames for the pipeline.
- **Frame Control:** Not all use cases require the same FPS; controlling frames reduces hardware requirements.
- **Resizing:** GStreamer resizes frames as needed by algorithms. Differnt algorithm registration files will give frame size requirement
- **Decoding:** Each cameraID decodes only once, even if used in multiple DAGs. Sometime Same camera is registered with different cameraID(rare case)

#### Hardware Decoding Capacity

| GPU Model         | Codec | Resolution      | Max Cameras @ 30FPS |
|-------------------|-------|-----------------|---------------------|
| Nvidia Tesla A10  | H265  | 1920x1080 (FHD) | 79                  | <!-- This row: Tesla A10 can decode 79 Full HD H265 streams at 30FPS -->
| Nvidia Tesla A10  | H265  | 3840x2160 (4K)  | 21                  | <!-- This row: Tesla A10 can decode 21 4K H265 streams at 30FPS -->
| Nvidia Tesla A10  | H264  | 1920x1080 (FHD) | 35                  | <!-- This row: Tesla A10 can decode 35 Full HD H264 streams at 30FPS -->
| Nvidia Tesla A10  | H264  | 3840x2160 (4K)  | 9                   | <!-- This row: Tesla A10 can decode 9 4K H264 streams at 30FPS -->
| Nvidia Tesla A10  | H265  | 2560x1920 (5MP) | 32                  | <!-- This row: Tesla A10 can decode 32 5MP H265 streams at 30FPS -->
| Nvidia Tesla A10  | H265  | 1560x1440 (4K)  | 43                  | <!-- This row: Tesla A10 can decode 43 1560x1440 H265 streams at 30FPS -->
| Nvidia Tesla A10  | H264  | 2560x1920 (5MP) | 13                  | <!-- This row: Tesla A10 can decode 13 5MP H264 streams at 30FPS -->
| Nvidia Tesla A10  | H264  | 1560x1440 (4K)  | 18                  | <!-- This row: Tesla A10 can decode 18 1560x1440 H264 streams at 30FPS -->
| Nvidia Tesla A100 | H265  | 1920x1080 (FHD) | 172                 | <!-- This row: Tesla A100 can decode 172 Full HD H265 streams at 30FPS -->
| Nvidia Tesla A100 | H265  | 3840x2160 (4K)  | 47                  | <!-- This row: Tesla A100 can decode 47 4K H265 streams at 30FPS -->
| Nvidia Tesla A100 | H264  | 1920x1080 (FHD) | 78                  | <!-- This row: Tesla A100 can decode 78 Full HD H264 streams at 30FPS -->
| Nvidia Tesla A100 | H264  | 3840x2160 (4K)  | 21                  | <!-- This row: Tesla A100 can decode 21 4K H264 streams at 30FPS -->
| Nvidia Tesla A100 | H265  | 2560x1920 (5MP) | 71                  | <!-- This row: Tesla A100 can decode 71 5MP H265 streams at 30FPS -->
| Nvidia Tesla A100 | H265  | 1560x1440 (4K)  | 96                  | <!-- This row: Tesla A100 can decode 96 1560x1440 H265 streams at 30FPS -->
| Nvidia Tesla A100 | H264  | 2560x1920 (5MP) | 31                  | <!-- This row: Tesla A100 can decode 31 5MP H264 streams at 30FPS -->
| Nvidia Tesla A100 | H264  | 1560x1440 (4K)  | 43                  | <!-- This row: Tesla A100 can decode 43 1560x1440 H264 streams at 30FPS -->
| Nvidia Tesla T4   | H265  | 1920x1080 (FHD) | 69                  | <!-- This row: Tesla T4 can decode 69 Full HD H265 streams at 30FPS -->
| Nvidia Tesla T4   | H265  | 3840x2160 (4K)  | 18                  | <!-- This row: Tesla T4 can decode 18 4K H265 streams at 30FPS -->
| Nvidia Tesla T4   | H264  | 1920x1080 (FHD) | 32                  | <!-- This row: Tesla T4 can decode 32 Full HD H264 streams at 30FPS -->
| Nvidia Tesla T4   | H264  | 3840x2160 (4K)  | 8                   | <!-- This row: Tesla T4 can decode 8 4K H264 streams at 30FPS -->
| Nvidia Tesla T4   | H265  | 2560x1920 (5MP) | 28                  | <!-- This row: Tesla T4 can decode 28 5MP H265 streams at 30FPS -->
| Nvidia Tesla T4   | H265  | 1560x1440 (4K)  | 38                  | <!-- This row: Tesla T4 can decode 38 1560x1440 H265 streams at 30FPS -->
| Nvidia Tesla T4   | H264  | 2560x1920 (5MP) | 12                  | <!-- This row: Tesla T4 can decode 12 5MP H264 streams at 30FPS -->
| Nvidia Tesla T4   | H264  | 1560x1440 (4K)  | 17                  | <!-- This row: Tesla T4 can decode 17 1560x1440 H264 streams at 30FPS -->

- **FPS Scaling:**
  For lower FPS, multiply the camera supported from above table by (30 / desired FPS).  
  Example: 69 cameras @ 30FPS → 138 cameras @ 15FPS for Full HD H265 in Tesla T4
- **Note:**  
  The Above table should be used to estimate GPUs required for Decoding Stream for different Nvidia GPUs only. FPS Scaling needs to be used if FPS user demand is different from what is available in the table above.

#### CPU Requirement Estimates

| Sources | Codec | Resolution      | vCPU Range      |
|---------|-------|-----------------|-----------------|
| 3500    | H264  | 1920x1080 (FHD) | 1547 - 1867     | <!-- 3500 H264 FullHD sources require 1547-1867 vCPUs.Valid for FullHD 25FPS; same for any FPS. -->
| 3500    | H265  | 1920x1080 (FHD) | 1586 - 1712     | <!-- 3500 H265 FullHD sources require 1586-1712 vCPUs.Valid for FullHD 25FPS; same for any FPS. -->
| 2000    | H264  | 1920x1080 (FHD) | 903 - 1085      | <!-- 2000 H264 FullHD sources require 903-1085 vCPUs.Valid for FullHD 25FPS; same for any FPS. -->
| 2000    | H265  | 1920x1080 (FHD) | 925 - 996       | <!-- 2000 H265 FullHD sources require 925-996 vCPUs.Valid for FullHD 25FPS; same for any FPS. -->
| 1000    | H264  | 1920x1080 (FHD) | 475 - 566       | <!-- 1000 H264 FullHD sources require 475-566 vCPUs.Valid for FullHD 25FPS; same for any FPS. -->
| 1000    | H265  | 1920x1080 (FHD) | 487 - 523       | <!-- 1000 H265 FullHD sources require 487-523 vCPUs.Valid for FullHD 25FPS; same for any FPS. -->

**Important Notes:**
- These values are for FullHD (1920x1080) streams at 25FPS.
- According to our understanding, the vCPU requirement remains the same for any other FPS (e.g., 15FPS, 30FPS, etc.).
- For any query about vCPU requirements at different FPS, this table should be used as-is.
- For intermediate numbers of sources/streams/cameras, use linear approximation between the table values.

**Explanation:**
- Each row estimates the number of virtual CPUs (vCPUs) needed to decode a given number of video sources (cameras), for a specific codec and resolution.
- Example: 3500 sources, H264, 1920x1080: Requires between 1547 and 1867 vCPUs.

- **Note:** Data is for FullHD only(same for any FPS). Linear approxmiation can be done for any other number of Sources.
  The Above table should be used to estimate vCPU required for Decoding Stream for different number of source/camera

#### GPU RAM Usage (Example: Nvidia Tesla T4)

| Stream Type                   | FPS | GPU RAM per Stream |
|-------------------------------|-----|---------------|
| H265, 1920x1080 (FHD)         | 15  | 169 MB        | <!-- H265 FullHD at 15FPS uses 169MB GPU RAM per stream, will vary for other resolution -->
| MJPEG, 1920x1080 (FHD)        | 25  | 155 MB        | <!-- MJPEG FullHD at 25FPS uses 155MB GPU RAM per stream, will vary for other resolution -->
| H264, 1920x1080 (FHD)         | 25  | 177 MB        | <!-- H264 FullHD at 25FPS uses 177MB GPU RAM per stream, will vary for other resolution -->

**Explanation:**
- Each row shows how much GPU RAM is used per stream for a given codec, resolution on a Tesla T4 GPU.
- Example: H265, 1920x1080 : Each stream uses 169 MB of GPU RAM. FPS Doesnt matter for RAM usage. Only Codec and and Resolution of Stream matters.

- **Note:**  
  The Above table should be used to estimate GPUs with respect to GPU RAM in persepctive for Decoding Stream for different Nvidia GPUs only. 
- number of GPUs for decoding =  maximum of [( number of GPUs from Hardware Decoding Capacity table estimate), (numbers of GPUs from GPU RAM Usage table estimate)]

- **GPU RAM per GPU:**
  - Tesla T4: 16GB
  - Tesla A10: 24GB
  - Tesla A100: 80GB
  - Tesla V100: 16GB

- **Note:**  
  The Above table should be used to understand GPU RAM vs Nvidia GPUs. Say total GPU RAM required is 300GB , then for Tesla A10, 300/24 = 12.5 ~= 13 Nvidia Tesla A10 GPUs needed with respect to GPU RAM considerations.  

#### Therotical vs Practical for vCPU and RAM usage
  Till now from above table we can get therotical estimations for number of GPUs and vCPU and CPU RAM. But to give Practical Data related to number vCPU and CPU RAM below table cann be used. We can always provide vCPU and CPU RAM with respect Practical and Therotical to Users. 

#### Practical CPU RAM and vCPU Data Points (K8s Dashboard) for Stream Decoding

| Streams | CPU RAM Usage | CPU Cores Usage |
|---------|--------------|-----------------|
| 2       | 278 MB       | 73.00m          | <!-- 2 streams: 278MB CPU RAM, 73 millicores CPU -->
| 6       | 1.17 GB      | 516.00m         | <!-- 6 streams: 1.17GB CPU RAM, 516 millicores CPU -->
| 13      | 2.71 GB      | 1.22            | <!-- 13 streams: 2.71GB CPU RAM, 1.22 CPU cores -->
| 17      | 3.44 GB      | 2.86            | <!-- 17 streams: 3.44GB CPU RAM, 2.86 CPU cores -->

**Explanation:**
- Each row shows real-world measurements of CPU RAM and CPU core usage for a given number of video streams, as observed in a Kubernetes deployment.
- Use multiple data points for any estimation as multiple data points can give better accuracy.
- Example: 2 streams: Use 278 MB RAM and 73 millicores of CPU.

- **Note:**  
  The Above table should be used to understand CPU RAM and vCPU used for number of Streams(or Source or Cameras). To estimate any other numbers we can use linear approximations. That is fit a best fit line from above table and calculate what could be the CPU RAM and vCPU with respect to any number of Source/Stream/Camera.  

---

### 2. Model Requirement

- All AI models are hosted inside Docker containers, along with their sidecars.
- Each model requires both GPU and CPU hardware for inference.
- Models receive frames as input from different camera stream pipelines and perform batched inference; batching increases throughput.
- Different batch sizes result in different throughput and hardware resource usage.
- Models and GStreamer pipelines are generally run on the same GPUs to maximize use of Nvidia GPU codec hardware and CUDA cores.
- When planning deployment, GPU RAM and GPU utilization must be considered for each GPU family (T4, V100, A10, A100, etc.).
- To understand the various models in deployment, refer to the `model_cards` directory.
- **Key parameters affecting throughput, GPU utilization, and GPU RAM usage:**  
  - `batch_size`
  - `decoderType` (DALI/TURBO)
  - Model resolution (width and height)
  - Input image resolution (frameSize)
- Model resolution and input image resolution also affect model accuracy.
- To maximize GPU effectiveness, use both codec hardware and CUDA cores efficiently without exceeding GPU RAM limits.
- GPU utilization and GPU RAM are scarce resources and must be planned carefully.

- **Additional practical notes:**
  - Plan to keep average CUDA core usage at 60-80% for stability.
  - For estimating CPU (millicores) and RAM (GB), refer to `pod_metrics/*.md` (multiple sheets, named after algorithms, policies, use cases).
  - For practical GPU usage, see `pod_gpumemory_and_gpuutility.csv` and map with `pod_metrics/*.md` for blockID, algorithm, and eventsReceivedPerTick.
  - Both files are time-synchronized.

#### Practical Node Requirements

| GPUs per Node | CPU RAM (GB) | vCPUs   |
|---------------|--------------|---------|
| 5             | 256          | 96-108  | <!-- 5 GPUs/node: 256GB RAM, 96-108 vCPUs -->
| 3             | 128-152      | 64-72   | <!-- 3 GPUs/node: 128-152GB RAM, 64-72 vCPUs -->

**Explanation:**
- Each row gives a recommended node configuration for a given number of GPUs, including total RAM and vCPUs.
- Example: 5 GPUs per node: Recommend 256 GB RAM and 96–108 vCPUs.

#### Model Metrics

- For estimating CPU (millicores) and RAM (GB), refer to `pod_metrics/*.md` (multiple sheets, named after algorithms, policies, use cases).
- Sheet columns:
  - `pod_name` (ignore)
  - `cpu_data` (millicores)
  - `mem_data` (GB)
  - `instanceQueue` (ignore)
  - `eventsReceivedPerTick(60seconds)` (frames per 60s)
  - `updateTime` (ignore)
- **Analysis Tips:**
  - Ignore rows with 0 events.
  - Start with linear regression for estimating CPU/RAM vs. events per tick.
  - Visualize data; use R², MAE, RMSE for model selection.

#### GPU Utilization and RAM

- For practical GPU usage, see `pod_gpumemory_and_gpuutility.csv`.
- Map this with `pod_metrics.xlsx` for blockID, algorithm, and eventsReceivedPerTick.
- `pod_gpumemory_and_gpuutility.csv` columns: block_id, pid, gpu_index, gpu_name, used_gpu_memory, avg_gpu_util, nodename.
- Both files are time-synchronized.

---

## Deep Dive into Application

- The metadata above is sufficient for Application.1 (hardware evaluation).
- The following sections focus on Application.2 (deployment planning).

---

### Application.2: Deployment Planning

#### For Understanding Camera vs Usecase Matrix
  - Refer to `CameraVsUsecaseMatrixs.md` for the matrix.

#### For Understanding Usecase vs Number of Input Frames.
  - Refer to `UsecaseVsNumberOfInputFrames.md` for the table.

#### For Understanding Usecase Grouping Rules.
  - Refer to `UsecaseGroupingRules.md` for the rules.

#### For Understanding Set Creation Rules.
  - Refer to `SetCreationRules.md` for the rules.
  - **Important:**  this has to be an iterative process where you need to go through all rows of given input `camera vs usecase matrix` and create sets based on the rules. Find best sets possible based on the rules.
  - **Important:**  All cameras in a set need not be running with same FPS. For example, a set has 2 cmeras with Crowd in one camera and Crowd+ParkingViolation in other camera, then FPS of first camera can be 0.25 where as for 2nd camer it can be 1 FPS.
  - **Important:** - A model when it is part of one set, it can not be shared with other set. If sharing is still required then merging the both sets is the only option.

#### For Understanding Pod Metrics
  - Use multiple data points for any estimation as multiple data points can give better accuracy.
  - Refer to `PodMetrics_general_info.md` for general information about pod metrics.
  - Refer to `pod_metrics/*.md` for specific pod metrics of each block in the pipeline.
  - **Important:**  `PodMetrics_general_info.md` file has special instructions on how to read the data in `pod_metrics/*.md` files. Make sure to read them carefully.
  - **IMPORTANT**: Dont miss the estimating CPU and RAM requirement for blocks/pods like `policy`, `policy_mux`, `usecase`, `usecase-frames`, `usecasmux_3input`, `trackerlite` blocks a can also add CPU and RAM requirement for the usecase pipeline.

#### For Understanding Node and GPU Assignment
  - Refer to `NodeAndGPUAssignementRules.md` for the rules.

#### Step by Step Complete process walkthrough for Deployment Planning:
  - **Step1** Once User provide the `camera vs usecase matrix`,
    - Asses the usecase distribution from shared `camera vs usecase matrix` and `Usecase vs Number of Input Frames` , and estimate at what FPS each camera has to process all the usecase of camera by taking the minimum of comman fps of the usecase.
      - `Rules for Usecase Grouping` understand this as well - but dont derive usecase grouping from this. Because camera vs usecase matrix is already grouped which should be result of `Rules for Usecase Grouping`.
  - **Step2** In a Loop for optimization:
    - Iterate Step2 with result of Step2(if result of Step2 available i.e Step2.1,Step2.2,Step2.3) so as to get optimized result and let the user know about each stages of optimzation.
      - **Step2.1** Understand the `Set Creation` rules.
        - Create sets based on the above understanding. This is an iterative process. Try to iterate 1 or 2 times once set created, whether created set can be clubbed with other sets or not **Important**.
        - Each set should have cameras with similar usecase(doesnt mean that all camera should have same usecase).
        -  **Important:** by clubbing FPS of cameras in a set, you can get the `eventsReceivedPerTick(60seconds)` for that set.
        -  **Important:** getting `eventsReceivedPerTick(60seconds)` is important to understand how many frames are processed by the model in 60 seconds.

      - **Step2.2** To get the vCPU and CPU RAM for each block in the set:
        - check the `PodMetrics_general_info.md` and files present in `pod_metrics/*` for each block/pod of the pipline/applayout. Dont miss any block/pod from the pipeline.
          - For example, if the set has `Object Detection` as `general7Detection_360h_640`, `Policy` as a `policy`, and `Usecase` blocks as a `usecase`, check the corresponding sheets in `pod_metrics/general7Detection_360h_640.md`, `pod_metrics/policy.md`, and `pod_metrics/usecase.md`.
          - **Important:** For each block, sum the CPU RAM and vCPU usage to get the total for the set.
          - **Important:** Don't forget to read the special instructions in `PodMetrics_general_info.md` files, which will give you the information about how to read the data of `pod_metrics/*.md` files.
      - **Step2.3** For GPU RAM  **Important:**:
          - Check `pod_gpumemory_and_gpuutility.md` for GPU RAM usage.
          - Sum the GPU RAM usage for all models in the set.
          - Sum the GPU RAM used by GStreamer pipeline for all cameras in the set.
          - For each model, GPU RAM usage is given in `pod_gpumemory_and_gpuutility.md`. Use this to estimate GPU RAM usage(Easy to do) with respect to algorithm name i.e `general7Detection_360h_640` or `pose-estimation-rt` etc
    
  - **Step3** Once sets are created, assign them to nodes and GPUs.
    - Ensure GPU RAM, GPU utility, node load, and CPU RAM are within limits.
    - Understand the `Node and GPU Assignment` rules.
