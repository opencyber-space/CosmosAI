## Rules for Usecase Grouping

**NOTE** Use this for Deployment Planning in Scalelayout.

- Group usecases with the same FPS requirements.
  - Example: Parking + Camera Tampering + Fire Detection: 3 usecase which can run with 1 FPS.
- Group usecases that use similar models.
  - Example: Chain Snatching + Assault + Leaning + Lying: 4 usecase which can run with 5 FPS.
- If two usecases with different FPS are grouped, use the minimum of common FPS of the usecases assigned. Check `UsecaseVsNumberOfInputFrames.md` for more examples
  - Example: Chain Snatching + Lying → overall FPS is 5.
- Maximize model utilization by increasing the number of cameras in each set.
- Avoid adding new usecases (with new models) to a group if only 1 or 2 cameras will use them.
  - Example: If only 2 cameras need Loitering in addition to Parking Violation, consider creating a new cameraID for Loitering.
- Creating new cameraIDs increases resource usage (new GStreamer pipeline, more CPU/GPU).
- Monitor image resolution requirements for each model.
  - Example: Luggage Detection needs 1920x1080 images; restrict FPS to 1 or 2.
  - Example: Gender Detection needs 1440x810 images; restrict FPS to 2 or 3.
- If customers request different usecase combinations, analyze hardware, GPU utility, and GPU RAM impact.
- If Chain Snatching or Fight Detection usecases are present:
  - Lying and Leaning can be run on the same cameras.
  - Maximum of 5 such cameras per GPU (Tesla T4) before reaching 50-80% GPU utility.
  - Two pose models may be needed; avoid adding more if performance drops.

---

## FAQ (for RAG Retrieval)

**Q1: How should I group usecases for deployment?**  
A: Group usecases with similar FPS and model requirements to maximize resource efficiency and simplify deployment.

**Q2: What FPS should I use if grouped usecases have different FPS requirements?**  
A: Use the minimum of common FPS among the grouped usecases as the cameras FPS.

**Q3: Is it efficient to add a usecase for only 1 or 2 cameras in a group?**  
A: No, avoid adding new usecases with new models for just 1 or 2 cameras; consider creating a separate camera group instead with separate cameraID for that usecase alone.

**Q4: How do image resolution requirements affect grouping?**  
A: Some models require higher image resolutions and may need lower FPS to avoid overloading resources. Always check model requirements.

**Q5: What is the impact of creating new cameraIDs?**  
A: It increases resource usage by adding new GStreamer pipelines and consuming more CPU/GPU.

**Q6: How many high-compute usecases (like Chain Snatching or Fight Detection) can I run per GPU?**  
A: Typically, up to 5 such cameras per GPU (Tesla T4) before reaching 50-80% GPU utility. More may require additional pose models or hardware.

**Q7: What should I do if customers request unique usecase combinations?**  
A: Analyze the impact on hardware, GPU utility, and RAM before deployment, and adjust grouping as needed.

---