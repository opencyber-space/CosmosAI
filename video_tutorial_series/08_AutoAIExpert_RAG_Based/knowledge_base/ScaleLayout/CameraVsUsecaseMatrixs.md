## Camera vs Usecase Matrix


| Camera ID        | Usecase1 | Usecase2 | UsecaseX |
|------------------|----------|----------|----------|
| camera_100_100   | 1        | 0        | 1        | <!-- camera_100_100: assigned to Usecase1 and UsecaseX -->
| camera_105_10    | 0        | 1        | 1        | <!-- camera_105_10: assigned to Usecase2 and UsecaseX -->

**Explanation:**
- Each row maps a camera to the usecases it is assigned to. 1 means the usecase is assigned to that camera; 0 means it is not.
- Example: camera_100_100: Assigned to Usecase1 and UsecaseX.

**Note:**
  Say we have asked with 1700 Usecases(Licences) for 605 cameras as example.
  Then we shal break how to plan 1,2,3 or 4 usecase cameras in 605
  licenses/camera = 1700/605 = 2.8 usecase (licences) per camera
      so we should have 2 to 3 usecase per camera on an average. It doesnt mean that you should not deploy 1 and 4 usecase cameras. But they might be less in number.
      So let us check how to calculate 2 and 3 usecase camera number with formula.
      x*2+(605-x)*3 = 1700 => x(2 usecase cameras) = 115  and 3 usecase cameras: 490
      So ask the user to plan like this before giving matrix of camera vs Usecase.If any 1 or 4 usecase is given, that is also acceptable.Going beyond 4 can be avoided until stressing requirement.

---

## FAQ (for RAG Retrieval)

**Q1: What does a '1' or '0' mean in the matrix?**  
A: '1' means the camera is assigned to that usecase; '0' means it is not assigned.

**Q2: How do I interpret the matrix for a specific camera?**  
A: Find the camera row. Each column with '1' indicates an assigned usecase for that camera.

**Q3: How many usecases should be assigned per camera?**  
A: On average, plan for 2 to 3 usecases per camera, based on your total licenses and camera count. 1 or 4 usecases per camera is allowed but less common.

**Q4: Is it okay to assign more than 4 usecases to a camera?**  
A: Avoid assigning more than 4 usecases per camera unless there is a strong requirement.

**Q5: How do I calculate the number of cameras with 2 or 3 usecases?**  
A: Use the formula: x*2 + (total_cameras-x)*3 = total_licenses. Solve for x (number of cameras with 2 usecases).

**Q6: Can I use this matrix for planning deployments?**  
A: Yes, use this matrix to plan and validate your camera-to-usecase assignments before deployment. But If User provides camera vs usecase matrix, then it is already grouped.

---