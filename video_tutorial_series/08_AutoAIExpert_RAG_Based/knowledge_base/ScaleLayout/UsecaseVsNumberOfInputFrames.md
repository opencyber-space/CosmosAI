## Usecase vs Number of Input Frames

**NOTE** Use this for Deployment Planning in Scalelayout.


- **Important Note:** This table is used to determine the possible input FPS (frames per second) for each usecase. When multiple usecases are assigned to a camera, the final FPS for the camera should be the minimum of the overlapping FPS values from all assigned usecases.

| Assigned Usecase Name             | Possible Input FPS Requirement      |
|-----------------------------------|------------------------------|
| Camera Tampering                  | 1,2,3,4,5...                 | <!-- Camera Tampering: FPS can be 1,2,3,4,5... -->
| Parking Violation                 | 0.5,1,2,3,4,5...             | <!-- Parking Violation: FPS can be 0.5,1,2,3,4,5... -->
| Loitering                         | 3,4,5,6...                   | <!-- Loitering: FPS can be 3,4,5,6... -->
| Unidentified and suspicious object| 1,2,3,4,5...                 | <!-- Unidentified and suspicious object: FPS can be 1,2,3,4,5... -->
| Fire Detection                    | 0.5,1,2,3,4,5...             | <!-- Fire Detection: FPS can be 0.5,1,2,3,4,5... -->
| Crowd Gathering                   | 0.25,0.5,1,2,3,4,5...        | <!-- Crowd Gathering: FPS can be 0.25,0.5,1,2,3,4,5... -->
| Lone Woman Detection              | 2,3,4,5...                   | <!-- Lone Woman Detection: FPS can be 2,3,4,5... -->
| Men in Women only area            | 2,3,4,5...                   | <!-- Men in Women only area: FPS can be 2,3,4,5... -->
| Chain Snatching                   | 5,6,7,8...                   | <!-- Chain Snatching: FPS can be 5,6,7,8... -->
| Age and gender via faces          | 2,3,4,5...                   | <!-- Age and gender via faces: FPS can be 2,3,4,5... -->
| Congestion Detection              | 2,3,4,5...                   | <!-- Congestion Detection: FPS can be 2,3,4,5... -->
| Multi Camera Tracking             | 1,2,3,4,5...                 | <!-- Multi Camera Tracking: FPS can be 1,2,3,4,5... -->
| Assault-Fight Detection           | 5,6,7,8                      | <!-- Assault-Fight Detection: FPS can be 5,6,7,8 -->
| Face Presence and Face Frequency  | 1,2,3,4,5...                 | <!-- Face Presence and Face Frequency: FPS can be 1,2,3,4,5... -->
| Indicative Object Search          | 1,2,3,4,5...                 | <!-- Indicative Object Search: FPS can be 1,2,3,4,5... -->
| Weapon detection                  | 2,3,4,5...                   | <!-- Weapon detection: FPS can be 2,3,4,5... -->
| Lying                             | 1,2,3,4,5                    | <!-- Lying: FPS can be 1,2,3,4,5 -->
| Leaning                           | 1,2,3,4,5                    | <!-- Leaning: FPS can be 1,2,3,4,5 -->

**Explanation:**
- Each row lists a usecase and the possible FPS (frames per second) requirements for that usecase.
- Example: Camera Tampering: FPS can be 1, 2, 3, 4, or 5.

- **FPS Finalization for Camera(camera with multiple usecase scenario)** Example 1:
        - Say `Crowd` possible input FPS: 0.25,0.5,1,2,3,4,5 and
        - Say `Camera Tampering` possible input FPS: 1,2,3,4,5
        - Final FPS is minimum of (overlapping fps) = minimum of (overlapping((0.25,0.5,1,2,3,4,5),(1,2,3,4,5))) = minimum of (1,2,3,4,5) = 1 FPS -> should be the input FPS of this cameras where `Crowd` and  `Camera Tampering`
      - Example 2:
        - Say `Crowd` possible input FPS: 0.25,0.5,1,2,3,4,5 and
        - Say `Lone Woman Detection` possible input FPS: 2,3,4,5
        - Final FPS is minimum of (overlapping fps) = minimum of (overlapping((0.25,0.5,1,2,3,4,5),(2,3,4,5))) = minimum of (2,3,4,5) = 2 FPS -> should be the input FPS of this cameras where `Crowd` and  `Lone Woman Detection`

---

## FAQ (for RAG Retrieval)

**Q1: What does the table show?**
A: It lists each usecase and the possible input FPS (frames per second) requirements for that usecase.

**Q2: How do I determine the FPS to use when multiple usecases are assigned to a camera?**
A: Find the overlapping FPS values for all assigned usecases and select the minimum of the overlapping FPS values.

**Q3: Why do some usecases have a lower minimum FPS than others?**
A: Some usecases (like Crowd Gathering) can work with lower FPS to save resources, while others (like Chain Snatching) require higher FPS for accurate detection.

**Q4: What happens if there is no overlap in FPS requirements between usecases?**
A: You may need to adjust usecase assignments or consult with the deployment team to find a feasible compromise.

**Q5: Can I assign any FPS from the list to a usecase?**
A: Yes, but you should consider resource constraints and detection accuracy. Lower FPS saves resources but may reduce detection performance.

**Q6: How do I use this table for planning deployments?**
A: Use it to check FPS compatibility when grouping usecases on a camera and to ensure resource-efficient, accurate deployments.

**Q7: Should Cameras in a set must share the same FPS?**
A: Need not be, it is recommended that all cameras in a set should have FPS needed based one Usecases assigned to it.

---