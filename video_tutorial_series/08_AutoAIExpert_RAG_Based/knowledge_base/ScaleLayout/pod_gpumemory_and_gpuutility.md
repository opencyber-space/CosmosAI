# GPU Memory and Utilization Metrics for Models
**NOTE** Use this for Deployment Planning in Scalelayout.
**Important** Dont use this file for estimating GPU RAM for Stream decoding

This table provides observed GPU memory usage and average GPU utility for each block(running the model) across different nodes and GPUs.  
You can use the relationship between `used_gpu_memory` and `avg_gpu_util` versus the planned workload (such as number of streams or events per tick) to estimate the required GPU RAM and GPU utilization for any expected deployment scenario.  
This is especially useful during ScaleLayout planning and Set Creation, where you need to predict GPU hardware requirements for new or scaled workloads.

**How to use:**  
- Analyze the data below to understand how each block's workload impacts GPU RAM and utilization.
- For any planned workload (from your ScaleLayout set), use these values to estimate the required GPU RAM (`used_gpu_memory`) and GPU utilization (`avg_gpu_util`).
- This enables accurate GPU resource allocation and helps prevent over-provisioning or under-provisioning during deployment.
- For example, say the Block ID is `block-375ec`, you would look at the following values:
    - **Used GPU Memory:** 1649 MiB
    - **Avg GPU Utilization:** 21.26% (this utility is sum of all blocks in this GPU Index(0) of this node(gpunode1) i.e sum of gpuutility of (`block-375ec`,`block-3493d`,`block-e8baa`,`block-6b146`,`block-4a2a7`) as they belong to GPU=0 in gpunode1).
    - Get the eventsReceivedPerTick(60seconds) for this block, from `pod_metrics/*` for this block(which is present in `pod_metrics/reidbaselineallres.md`), which is 304 and divide it by 60 to get number of frames per second. Which is 5.07(Frames/sec). And also get its GPU RAM which is 1649MB
    - similarly for other blocks in the same GPU of the node.
        `block-3493d` from `pod_metrics/general7Detection_360h_640.md` with 301 eventsReceivedPerTick(60seconds) gives 5.02(Frames/sec). And also get its GPU RAM which is 2295MB
        `block-e8baa` from `pod_metrics/firesmoke7Det_512h_896w.md` with 240 eventsReceivedPerTick(60seconds) gives 4(Frames/sec). And also get its GPU RAM which is 2841MB
        `block-6b146` from `pod_metrics/camTamp_360h_640w.md` with 180 eventsReceivedPerTick(60seconds) gives 3(Frames/sec). And also get its GPU RAM which is 463MB
        `block-4a2a7` from `pod_metrics/vehicles5Detection_360h_640.md` with 421 eventsReceivedPerTick(60seconds) gives 7.01(Frames/sec). And also get its GPU RAM which is 1991MB

| Block ID   | PID      | GPU Index | GPU Name | Used GPU Memory | Avg GPU Util (%) | Node Name | Block Mapping |
|------------|----------|-----------|----------|-----------------|------------------|-----------|---------------|
| block-375ec | 3490407 | 0         | Tesla T4 | 1649 MiB        | 21.26            | gpunode1  | reidbaselineallres |
| block-3493d | 3490599 | 0         | Tesla T4 | 2295 MiB        | 21.26            | gpunode1  | general7Detection_360h_640 |
| block-e8baa | 3500102 | 0         | Tesla T4 | 2841 MiB        | 21.26            | gpunode1  | firesmoke7Det_512h_896w |
| block-6b146 | 3507704 | 0         | Tesla T4 | 463 MiB         | 21.26            | gpunode1  | camTamp_360h_640w |
| block-4a2a7 | 3516836 | 0         | Tesla T4 | 1991 MiB        | 21.26            | gpunode1  | vehicles5Detection_360h_640 |
| block-e877a | 2183828 | 4         | Tesla T4 | 1699 MiB        | 42.62            | gpunode1  | pose-estimation-rt |
| block-ee5f0 | 2186682 | 4         | Tesla T4 | 379 MiB         | 42.62            | gpunode1  | trackerlitefast_960x540 |
| block-bfc4c | 2182589 | 4         | Tesla T4 | 2489 MiB        | 42.62            | gpunode1  | fall7Detection_640h_640 |
| block-7944f | 2198329 | 4         | Tesla T4 | 379 MiB         | 42.62            | gpunode1  | trackerlitefast_960x540 |
| block-97744 | 2196077 | 4         | Tesla T4 | 1769 MiB        | 42.62            | gpunode1  | fight3Det |
| block-4beea | 2275298 | 4         | Tesla T4 | 1699 MiB        | 42.62            | gpunode1  | pose-estimation-rt |
| block-5b38e | 2275857 | 4         | Tesla T4 | 379 MiB         | 42.62            | gpunode1  | trackerlitefast_960x540 |
| block-e4aff | 2285393 | 4         | Tesla T4 | 379 MiB         | 42.62            | gpunode1  | trackerlitefast_960x540 |
| block-bc797 | 2209942 | 0         | Tesla T4 | 1649 MiB        | 14.03            | gpunode2  | reidbaselineallres |
| block-22462 | 2210152 | 0         | Tesla T4 | 2295 MiB        | 14.03            | gpunode2  | general7Detection_360h_640 |
| block-0e430 | 2216285 | 0         | Tesla T4 | 2841 MiB        | 14.03            | gpunode2  | firesmoke7Det_512h_896w |
| block-20e99 | 2221335 | 0         | Tesla T4 | 463 MiB         | 14.03            | gpunode2  | camTamp_360h_640w |
| block-36f06 | 1626735 | 1         | Tesla T4 | 1577 MiB        | 39.66            | gpunode2  | custbodygend75 |
| block-22b2a | 1626645 | 1         | Tesla T4 | 2295 MiB        | 39.66            | gpunode2  | general7Detection_360h_640 |
| block-054e9 | 1634520 | 1         | Tesla T4 | 379 MiB         | 39.66            | gpunode2  | trackerlitefast_960x540 |
| block-1dd2a | 1642616 | 1         | Tesla T4 | 463 MiB         | 39.66            | gpunode2  | camTamp_360h_640w |
| block-b2df9 | 4035537 | 1         | Tesla T4 | 463 MiB         | 39.66            | gpunode2  | camTamp_360h_640w |
| block-0747e | 2507819 | 1         | Tesla T4 | 1577 MiB        | 39.66            | gpunode2  | custbodygend75 |
| block-d7acb | 2507828 | 1         | Tesla T4 | 2295 MiB        | 39.66            | gpunode2  | general7Detection_360h_640 |
| block-89530 | 2517754 | 1         | Tesla T4 | 379 MiB         | 39.66            | gpunode2  | trackerlitefast_960x540 |
| block-e2b72 | 2546305 | 1         | Tesla T4 | 463 MiB         | 39.66            | gpunode2  | camTamp_360h_640w |
| block-c4434 | 7963    | 4         | Tesla T4 | 1699 MiB        | 54.85            | gpunode2  | pose-estimation-rt |
| block-7fbb0 | 10355   | 4         | Tesla T4 | 379 MiB         | 54.85            | gpunode2  | trackerlitefast_960x540 |
| block-15f51 | 6108    | 4         | Tesla T4 | 2489 MiB        | 54.85            | gpunode2  | fall7Detection_640h_640 |
| block-48148 | 19164   | 4         | Tesla T4 | 379 MiB         | 54.85            | gpunode2  | trackerlitefast_960x540 |
| block-e3009 | 17292   | 4         | Tesla T4 | 1769 MiB        | 54.85            | gpunode2  | fight3Det |
| block-dd842 | 61042   | 4         | Tesla T4 | 1699 MiB        | 54.85            | gpunode2  | pose-estimation-rt |
| block-cdecf | 61379   | 4         | Tesla T4 | 379 MiB         | 54.85            | gpunode2  | trackerlitefast_960x540 |
| block-72006 | 66867   | 4         | Tesla T4 | 379 MiB         | 54.85            | gpunode2  | trackerlitefast_960x540 |
| block-771a0 | 376882  | 0         | Tesla T4 | 1991 MiB        | 58.6             | gpunode3  | vehicles5Detection_360h_640 |
| block-92e75 | 4017124 | 0         | Tesla T4 | 1991 MiB        | 58.6             | gpunode3  | vehicles5Detection_360h_640 |
| block-c8169 | 4028398 | 0         | Tesla T4 | 2841 MiB        | 58.6             | gpunode3  | firesmoke7Det_512h_896w |
| block-09584 | 3036007 | 0         | Tesla T4 | 463 MiB         | 58.6             | gpunode3  | camTamp_360h_640w |
| block-ba87e | 3075866 | 0         | Tesla T4 | 463 MiB         | 58.6             | gpunode3  | camTamp_360h_640w |
| block-d4568 | 3104568 | 0         | Tesla T4 | 463 MiB         | 58.6             | gpunode3  | camTamp_360h_640w |
| block-1bb12 | 186714  | 0         | Tesla T4 | 463 MiB         | 58.6             | gpunode3  | camTamp_360h_640w |
| block-fc59c | 203754  | 0         | Tesla T4 | 463 MiB         | 58.6             | gpunode3  | camTamp_360h_640w |
| block-ad038 | 750761  | 1         | Tesla T4 | 1577 MiB        | 24.32            | gpunode3  | custbodygend75 |
| block-66099 | 750762  | 1         | Tesla T4 | 2295 MiB        | 24.32            | gpunode3  | general7Detection_360h_640 |
| block-1e07c | 763926  | 1         | Tesla T4 | 1991 MiB        | 24.32            | gpunode3  | vehicles5Detection_360h_640 |
| block-4ea83 | 1085908 | 2         | Tesla T4 | 2295 MiB        | 24.54            | gpunode3  | general7Detection_360h_640 |
| block-fdecf | 1097972 | 2         | Tesla T4 | 3209 MiB        | 24.54            | gpunode3  | luggage7Detection_1080_1920 |
| block-bda3e | 1121692 | 2         | Tesla T4 | 463 MiB         | 24.54            | gpunode3  | camTamp_360h_640w |
| block-ba99e | 1704736 | 4         | Tesla T4 | 1699 MiB        | 26.39            | gpunode3  | pose-estimation-rt |
| block-97bba | 1706736 | 4         | Tesla T4 | 379 MiB         | 26.39            | gpunode3  | trackerlitefast_960x540 |
| block-f498b | 1703594 | 4         | Tesla T4 | 2489 MiB        | 26.39            | gpunode3  | fall7Detection_640h_640 |
| block-57fae | 1713421 | 4         | Tesla T4 | 1769 MiB        | 26.39            | gpunode3  | fight3Det |
| block-10f98 | 1714955 | 4         | Tesla T4 | 379 MiB         | 26.39            | gpunode3  | trackerlitefast_960x540 |
| block-431b8 | 318897  | 0         | Tesla T4 | 1577 MiB        | 71.91            | gpunode4  | custbodygend75 |
| block-5edfd | 318890  | 0         | Tesla T4 | 2295 MiB        | 71.91            | gpunode4  | general7Detection_360h_640 |
| block-8e5f9 | 331272  | 0         | Tesla T4 | 1991 MiB        | 71.91            | gpunode4  | vehicles5Detection_360h_640 |
| block-23940 | 490556  | 0         | Tesla T4 | 379 MiB         | 71.91            | gpunode4  | trackerlitefast_960x540 |
| block-5d21a | 504201  | 0         | Tesla T4 | 3209 MiB        | 71.91            | gpunode4  | luggage7Detection_1080_1920 |
| block-b8cbe | 1247125 | 1         | Tesla T4 | 2295 MiB        | 46.01            | gpunode4  | general7Detection_360h_640 |
| block-55ce5 | 3260105 | 1         | Tesla T4 | 379 MiB         | 46.01            | gpunode4  | trackerlitefast_960x540 |
| block-271be | 2883222 | 1         | Tesla T4 | 463 MiB         | 46.01            | gpunode4  | camTamp_360h_640w |
| block-6f2b7 | 3751034 | 1         | Tesla T4 | 463 MiB         | 46.01            | gpunode4  | camTamp_360h_640w |
| block-dd22d | 811753  | 1         | Tesla T4 | 2295 MiB        | 46.01            | gpunode4  | general7Detection_360h_640 |
| block-2a1c8 | 811752  | 1         | Tesla T4 | 1577 MiB        | 46.01            | gpunode4  | custbodygend75 |
| block-d7948 | 825546  | 1         | Tesla T4 | 379 MiB         | 46.01            | gpunode4  | trackerlitefast_960x540 |
| block-c8fc5 | 876436  | 1         | Tesla T4 | 463 MiB         | 46.01            | gpunode4  | camTamp_360h_640w |
| block-bfbcf | 31085   | 1         | Tesla T4 | 379 MiB         | 46.01            | gpunode4  | trackerlitefast_960x540 |
| block-21f2b | 1370009 | 2         | Tesla T4 | 2295 MiB        | 61.87            | gpunode4  | general7Detection_360h_640 |
| block-68036 | 2528433 | 2         | Tesla T4 | 1577 MiB        | 61.87            | gpunode4  | custbodygend75 |
| block-4616c | 2528434 | 2         | Tesla T4 | 2295 MiB        | 61.87            | gpunode4  | general7Detection_360h_640 |
| block-0048f | 2541409 | 2         | Tesla T4 | 1991 MiB        | 61.87            | gpunode4  | vehicles5Detection_360h_640 |
| block-891c9 | 2608245 | 2         | Tesla T4 | 3209 MiB        | 61.87            | gpunode4  | luggage7Detection_1080_1920 |
| block-830e1 | 2658922 | 2         | Tesla T4 | 315 MiB         | 61.87            | gpunode4  | trackerlitefast_960x540 |
| block-ac890 | 222482  | 2         | Tesla T4 | 463 MiB         | 61.87            | gpunode4  | camTamp_360h_640w |
| block-e970c | 307334  | 0         | Tesla T4 | 463 MiB         | 26.19            | gpunode5  | camTamp_360h_640w |
| block-b066f | 280836  | 0         | Tesla T4 | 1649 MiB        | 26.19            | gpunode5  | reidbaselineallres |
| block-75dd4 | 281086  | 0         | Tesla T4 | 2295 MiB        | 26.19            | gpunode5  | general7Detection_360h_640 |
| block-6ee8c | 391659  | 0         | Tesla T4 | 1649 MiB        | 26.19            | gpunode5  | reidbaselineallres |
| block-a4f42 | 391678  | 0         | Tesla T4 | 2295 MiB        | 26.19            | gpunode5  | general7Detection_360h_640 |
| block-d7697 | 421473  | 0         | Tesla T4 | 2841 MiB        | 26.19            | gpunode5  | firesmoke7Det_512h_896w |
| block-4ae0e | 355026  | 1         | Tesla T4 | 3209 MiB        | 12.69            | gpunode5  | luggage7Detection_1080_1920 |
| block-46ba2 | 355047  | 1         | Tesla T4 | 2295 MiB        | 12.69            | gpunode5  | general7Detection_360h_640 |
| block-4e7a5 | 361687  | 1         | Tesla T4 | 463 MiB         | 12.69            | gpunode5  | camTamp_360h_640w |
| block-e24d0 | 2644311 | 4         | Tesla T4 | 1699 MiB        | 26.63            | gpunode5  | pose-estimation-rt |
| block-84dc7 | 2643276 | 4         | Tesla T4 | 1769 MiB        | 26.63            | gpunode5  | fight3Det |
| block-afdc4 | 2646726 | 4         | Tesla T4 | 379 MiB         | 26.63            | gpunode5  | trackerlitefast_960x540 |
| block-17c5b | 2656532 | 4         | Tesla T4 | 2489 MiB        | 26.63            | gpunode5  | fall7Detection_640h_640 |
| block-ba8d9 | 2505574 | 0         | Tesla T4 | 1649 MiB        | 16.64            | gpunode6  | reidbaselineallres |
| block-a3337 | 2505715 | 0         | Tesla T4 | 2295 MiB        | 16.64            | gpunode6  | general7Detection_360h_640 |
| block-75ff5 | 1688633 | 1         | Tesla T4 | 463 MiB         | 28.14            | gpunode6  | camTamp_360h_640w |
| block-989fd | 959524  | 1         | Tesla T4 | 1649 MiB        | 28.14            | gpunode6  | reidbaselineallres |
| block-87fa2 | 959678  | 1         | Tesla T4 | 2295 MiB        | 28.14            | gpunode6  | general7Detection_360h_640 |
| block-0638c | 970970  | 1         | Tesla T4 | 463 MiB         | 28.14            | gpunode6  | camTamp_360h_640w |
| block-dcc2a | 1073733 | 1         | Tesla T4 | 463 MiB         | 28.14            | gpunode6  | camTamp_360h_640w |
| block-61486 | 2534315 | 3         | Tesla T4 | 1699 MiB        | 13.88            | gpunode6  | pose-estimation-rt |
| block-0c31b | 2535645 | 3         | Tesla T4 | 379 MiB         | 13.88            | gpunode6  | trackerlitefast_960x540 |
| block-aad9b | 2531711 | 3         | Tesla T4 | 2489 MiB        | 13.88            | gpunode6  | fall7Detection_640h_640 |
| block-46bb9 | 2543613 | 3         | Tesla T4 | 1769 MiB        | 13.88            | gpunode6  | fight3Det |
| block-05996 | 2546191 | 3         | Tesla T4 | 379 MiB         | 13.88            | gpunode6  | trackerlitefast_960x540 |
| block-efa44 | 45020   | 4         | Tesla T4 | 1699 MiB        | 40.36            | gpunode6  | pose-estimation-rt |
| block-92951 | 46377   | 4         | Tesla T4 | 379 MiB         | 40.36            | gpunode6  | trackerlitefast_960x540 |
| block-f6e43 | 43481   | 4         | Tesla T4 | 2489 MiB        | 40.36            | gpunode6  | fall7Detection_640h_640 |
| block-e6cbc | 56629   | 4         | Tesla T4 | 379 MiB         | 40.36            | gpunode6  | trackerlitefast_960x540 |
| block-a69a5 | 54521   | 4         | Tesla T4 | 1769 MiB        | 40.36            | gpunode6  | fight3Det |
| block-822a5 | 2442949 | 4         | Tesla T4 | 1699 MiB        | 40.36            | gpunode6  | pose-estimation-rt |
| block-e1fe6 | 2443751 | 4         | Tesla T4 | 379 MiB         | 40.36            | gpunode6  | trackerlitefast_960x540 |
| block-7ddbb | 2448777 | 4         | Tesla T4 | 379 MiB         | 40.36            | gpunode6  | trackerlitefast_960x540 |
| block-76754 | 4633    | 0         | Tesla T4 | 2295 MiB        | 13.69            | gpunode7  | general7Detection_360h_640 |
| block-b1aa0 | 4623    | 0         | Tesla T4 | 3211 MiB        | 13.69            | gpunode7  | weapon7Detection_896_896 |
| block-a2f80 | 11135   | 0         | Tesla T4 | 463 MiB         | 13.69            | gpunode7  | camTamp_360h_640w |
| block-1b49d | 23500   | 0         | Tesla T4 | 1649 MiB        | 13.69            | gpunode7  | reidbaselineallres |
| block-22228 | 42302   | 0         | Tesla T4 | 3209 MiB        | 13.69            | gpunode7  | luggage7Detection_1080_1920 |
| block-074ef | 3944620 | 1         | Tesla T4 | 1991 MiB        | 0.0              | gpunode7  | vehicles5Detection_360h_640 |
| block-8f492 | 3953944 | 1         | Tesla T4 | 463 MiB         | 0.0              | gpunode7  | camTamp_360h_640w |
| block-8298c | 173765  | 4         | Tesla T4 | 1699 MiB        | 57.81            | gpunode7  | pose-estimation-rt |
| block-732a9 | 171523  | 4         | Tesla T4 | 2489 MiB        | 57.81            | gpunode7  | fall7Detection_640h_640 |
| block-3d353 | 175691  | 4         | Tesla T4 | 379 MiB         | 57.81            | gpunode7  | trackerlitefast_960x540 |
| block-51000 | 183604  | 4         | Tesla T4 | 1769 MiB        | 57.81            | gpunode7  | fight3Det |
| block-000a9 | 186470  | 4         | Tesla T4 | 379 MiB         | 57.81            | gpunode7  | trackerlitefast_960x540 |
| block-8888b | 243780  | 4         | Tesla T4 | 1699 MiB        | 57.81            | gpunode7  | pose-estimation-rt |
| block-246c4 | 244211  | 4         | Tesla T4 | 379 MiB         | 57.81            | gpunode7  | trackerlitefast_960x540 |
| block-0ce19 | 251729  | 4         | Tesla T4 | 379 MiB         | 57.81            | gpunode7  | trackerlitefast_960x540 |

---

## Example Insights

- **Block resource usage:** Each block instance can be tracked for its GPU memory and utilization, aiding in resource planning.
- **GPU balancing:** Use this data to distribute workloads across GPUs and nodes to avoid overloading a single resource.
- **Optimization:** Identify blocks with high memory or utilization for optimization or scaling.
- **Node awareness:** The `Node Name` column helps in understanding resource distribution across the cluster.
- **Model GPU RAM:** It would be difficult to predict the exact GPU Utility but RAM is predictable from above table. GPU utility is clubbed for all blocks in a GPU Index of a node.  
  For example, if you have 5 blocks in GPU Index 0 of gpunode1, then the GPU utility is sum of all blocks in that GPU Index(0) of that node(gpunode1).  
  So, it is not possible to predict exact GPU utility for a block but can be predicted for a GPU Index of a node.
- **Deployment planning:** Use this table to estimate GPU requirements for new deployments based on GPU RAM.

---

