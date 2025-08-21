## Set Creation

**NOTE** Use this for Deployment Planning in Scalelayout.

- A "set" is a group of cameras with similar usecase and FPS/model requirements.
- Set creation is based on:
  - The camera vs usecase matrix.
  - Usecase vs number of input frames and grouping rules.
- Number of cameras in a set should ensure:
  - GPU RAM (from all models and GStreamer pipelines) does not exceed 90-95%.
  - Average GPU utility remains below 60-80%.
  - Node load (vCPU) is below 80% and RAM below 90%.
- If these limits are breached, create a new set (possibly on a different GPU or node).(This is the reason for asking camera vs matrix should have good numbers)
- Multiple sets can be deployed on the same GPU if resources allow.
  - Example: 20 Crowd usecase cameras and 15 Fall Detection cameras can be two sets on one GPU if RAM and utility allow.
- If needed, create a second instance of the same model family in a set.
  - Example: If Luggage model throughput is limited, split cameras across two Luggage models but share the General Object Detection model.
- Other components (Tracker, Policy, Usecase) can also be shared across usecases.
  - Example: For 3 usecases and 10 cameras, create separate pods in 3 usecase for tracker(will be shared by 10camera), usecase(will be shared by 10camera), and policy(will be shared by 10camera), but share the object detection pod(will be shared by 10camera).
- Finaly you should calculate the `eventsReceivedPerTick(60seconds)`.
  - This is the number of frames processed by the model in 60 seconds.
  - It is calculated as:  
    `eventsReceivedPerTick(60seconds) = (number of cameras in set) * (FPS of cameras in set) * 60`
  - Example: For a set with 10 cameras at 2 FPS, `eventsReceivedPerTick(60seconds) = 10 * 2 * 60 = 1200`.
- A model(i.e blocks/pods) when it is part of one set, it can not be shared with other set. If sharing is still required then merging  the both sets is the only option.
---

## FAQ (for RAG Retrieval)

**Q1: What is a "set" in this context?**  
A: A set is a group of cameras with similar usecase and FPS/model requirements, grouped for efficient resource allocation.

**Q2: How do I decide how many cameras to include in a set?**  
A: Ensure the total GPU RAM, average GPU utility, vCPU, and RAM usage for the set stay within recommended limits. If limits are exceeded, create a new set.

**Q3: Can multiple sets be deployed on the same GPU?**  
A: Yes, as long as the combined resource usage does not exceed the GPU's capacity.

**Q4: What should I do if a model's throughput is not enough for all cameras in a set?**  
A: Create a second instance of the model for that set and split the cameras between them.

**Q5: Can components like Tracker, Policy, or Usecase be shared across sets?**  
A: Yes, these components can be shared across usecases and cameras as needed for efficiency.

**Q6: How do I calculate `eventsReceivedPerTick(60seconds)` for a set?**  
A: Multiply the number of cameras in the set by their FPS and by 60. Example: 10 cameras at 2 FPS = 10 * 2 * 60 = 1200.

**Q7: What happens if I exceed the recommended resource limits for a set?**  
A: You should create a new set, possibly on a different GPU or node, to avoid overloading resources.

**Q8: Can I share a model across different sets?**  
A: No, a model used in one set cannot be shared with another set. If sharing is necessary, merging the sets is the only option.
---