# FAQ: Conflict Resolution for LLM in ScaleLayout Analysis and Estimation

This FAQ is designed to help LLMs resolve common conflicts and ambiguities encountered during ScaleLayout analysis, resource estimation, and assignment. It is intended to improve retrieval and ensure the LLM makes robust, context-aware decisions.

---

**Q1: What should the LLM do if Context doest provide data LLM looking for?**
A1: The LLM should use clearly say the unavailability of data clearly and dont hallucinate or make assumptions. If the data is critical, it should flag this as a limitation and suggest alternative approaches or data sources.

**Q2: How should the LLM handle if FPS are decided by AppLayout**
A2: The LLM should always estimate the FPS based on ScaleLayout's `UsecaseVsNumberOfInputFrames.md` file as this will give good controll when more than one usecase is present in the camera/source/stream. Even if only one usecase is present, the LLM should still refer to this file for FPS estimation.

**Q3: How should LLM Optimze the resource usage for Given set of camera vs usecas matrix for deployment?**
A3: Iteration is key to optimzation. The LLM should start understand giving optmized deployment is what user prefferes. So dont settle with what is predicted in first iteration. Provide muliple iterations of deployment plan and provide advantages and disadvantages of each iteration. This will help the user to choose the best deployment plan.

**Q4: How many points should LLM consider whenever it does estimation of resource like CPU RAM, vCPU , GPU RAM, etc?**
A4: The LLM should consider at least 2-3 points of data for each resource type, so that estimate can be better and more accurate.



**Q1: What should the LLM do if two blocks require more resources than are available on a single node?**
A1: The LLM should recommend splitting the blocks across multiple nodes or suggest scaling up the node resources if possible. Prioritize critical workloads and ensure no node is overcommitted.

**Q2: If a block's observed resource usage varies significantly across event rates, which value should be used for estimation?**
A2: Use the value corresponding to the expected or planned event rate. If the event rate is unknown, use the average or the value at the 75th percentile to ensure headroom for spikes.

**Q3: How should the LLM resolve conflicts between CPU and memory requirements when both cannot be satisfied on a single node?**
A3: Prioritize the more restrictive resource (usually memory). Recommend splitting the workload or using a node type that satisfies the higher requirement.

**Q4: What if two blocks have conflicting affinity/anti-affinity rules?**
A4: The LLM should respect anti-affinity rules first to avoid resource contention. If affinity is required for performance, suggest alternative placements or node types.

**Q5: How should the LLM handle missing or incomplete pod_metrics data?**
A5: Use interpolation or fallback to similar blocks' data. If no data is available, use conservative estimates and flag the uncertainty in the output.

**Q6: If the event rate for a block is not specified, what should the LLM assume?**
A6: Assume a default event rate based on historical averages or the most common value in the dataset. Clearly state the assumption in the output.

**Q7: How should the LLM handle conflicting user constraints (e.g., must fit on 2 nodes, but resource usage suggests 3)?**
A7: Explain the conflict, provide the best possible solution (e.g., minimal overcommitment), and recommend revisiting the constraints if possible.

---

*Add more FAQs below as new conflict scenarios are encountered.*
