## Pod Metrics General Information
**NOTE** Use this for Deployment Planning in Scalelayout.
### Estimating CPU and Memory Requirements for all the  Pods mentioned in /pod_metrics/*.md directory. Usefull for Scallayout estimation of CPU and RAM for any event rate.

**IMPORTANT**: Dont miss the estimating CPU and RAM requirement for blocks/pods like `policy`, `policy_mux`, `usecase`, `usecase-frames`, `usecasmux_3input`, `trackerlite` blocks a can also add CPU and RAM requirement for the usecase pipeline.

You can use the relationship between `cpu_data (millicores)` and `mem_data (GB)` versus `eventsReceivedPerTick(60seconds)` to estimate the required vCPU and RAM for any expected event rate.  
This is especially useful during ScaleLayout planning and Set Creation, where you need to predict hardware requirements for new deployments.

**How to use:**  
- Use multiple Data points from the pod_metrics/*.md files.
- Fit a regression or trend line to the data below (e.g., linear regression).
- For any planned `eventsReceivedPerTick(60seconds)` (from your ScaleLayout set), use the fitted model to estimate the required vCPU (`cpu_data`) and RAM (`mem_data`).
- This enables accurate resource allocation for new or scaled workloads.

### How to Estimate CPU and Memory for Any Event Rate

To estimate the required CPU (millicores) and memory (GB) for a given `eventsReceivedPerTick(60seconds)`, follow these steps:

1. **Find the closest data points:**
   - Look for rows in the table where `eventsReceivedPerTick(60seconds)` is just below and just above your target value.
   - If your value matches a row exactly, use the corresponding `cpu_data` and `mem_data` directly.
   - always use multiple data points for better accuracy.

2. **Interpolate if needed:**
   - If your target value falls between two rows, perform linear interpolation between those rows to estimate the required CPU and memory.
   - Formula for interpolation:
     
     For two points (x1, y1) and (x2, y2), and a target x:
     
     y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)

3. **Example:**
   - Suppose you want to estimate for `eventsReceivedPerTick(60seconds) = 200`.
   - Find two rows: one with value just below (e.g., 187) and one just above (e.g., 250).
   - Use their `cpu_data` and `mem_data` to interpolate and get the estimate for 200.

4. **Automated Calculation:**
   - You can use a script (Python, Excel, etc.) to automate this lookup and interpolation.
   - See below for a sample Python snippet:

```python
import pandas as pd

def estimate_resources(event_rate, df):
    df = df[df['eventsReceivedPerTick(60seconds)'] > 0].sort_values('eventsReceivedPerTick(60seconds)')
    lower = df[df['eventsReceivedPerTick(60seconds)'] <= event_rate].tail(1)
    upper = df[df['eventsReceivedPerTick(60seconds)'] >= event_rate].head(1)
    if lower.empty:
        return upper['cpu_data (millicores)'].values[0], upper['mem_data (GB)'].values[0]
    if upper.empty:
        return lower['cpu_data (millicores)'].values[0], lower['mem_data (GB)'].values[0]
    if lower['eventsReceivedPerTick(60seconds)'].values[0] == upper['eventsReceivedPerTick(60seconds)'].values[0]:
        return lower['cpu_data (millicores)'].values[0], lower['mem_data (GB)'].values[0]
    # Linear interpolation
    x1, y1_cpu, y1_mem = lower['eventsReceivedPerTick(60seconds)'].values[0], lower['cpu_data (millicores)'].values[0], lower['mem_data (GB)'].values[0]
    x2, y2_cpu, y2_mem = upper['eventsReceivedPerTick(60seconds)'].values[0], upper['cpu_data (millicores)'].values[0], upper['mem_data (GB)'].values[0]
    cpu = y1_cpu + (y2_cpu - y1_cpu) * (event_rate - x1) / (x2 - x1)
    mem = y1_mem + (y2_mem - y1_mem) * (event_rate - x1) / (x2 - x1)
    return cpu, mem

# Usage:
# df = pd.read_csv('camTamp_360h_640w.csv')
# cpu, mem = estimate_resources(200, df)
# print(f"Estimated CPU: {cpu:.2f} millicores, Memory: {mem:.3f} GB")
```

5. **Note:**
   - For best accuracy, use as many data points as possible and avoid extrapolating far outside the observed range.
   - If you have a new event rate not in the table, always interpolate between the nearest two rows.

---