from kubernetes import client, config
import openpyxl
import requests
import json
import time
from datetime import datetime, timedelta, timezone

#pip install kubernetes openpyxl

#kubectl get pods -n my-namespace -o jsonpath="{range .items[*]}{.metadata.name}:{.metadata.labels.baseComponent}{'\n'}{end}"


PROMETHEUS_URL = "http://172.16.9.13:32090/api/v1/query"
NAMESPACE = "dag-space-default-mdag"
LABEL_SELECTOR = "baseComponent=node.algorithm.objdet.general7Detection_360h_640-v0.0.1-stable"

# Function to check if current timezone is IST
def is_ist():
	# Get the current timezone
	#current_tz = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Z')
	current_tz = datetime.now(timezone(timedelta(0))).astimezone().strftime('%Z')
	# Check if the timezone is IST
	return current_tz == 'IST'

IS_TIMING_IST = is_ist()

def fetch_instance_queues(endPoint, headers):
    retryTimes = 5
    data_json = { "mdagID": "default-mdag"}
    for j in range(retryTimes):
        try:
            resp = requests.post(endPoint, data=json.dumps(data_json), headers=headers, timeout=5)
        except Exception:
            if j == (retryTimes-1):
                return {}
            time.sleep(1)
            continue
        if resp.status_code != 200:
            if j == (retryTimes-1):
                return {}
            time.sleep(1)
            continue
        result = resp.json()
        if result.get("error"):
            if j == (retryTimes-1):
                return {}
            time.sleep(1)
            continue
        payload = result.get("payload", [])
        #print(payload[0])
        # Build a dict: podname -> instanceQueue
        return {i.get("blockID"): (i.get("instanceQueue"),i.get("eventsReceivedPerTick"),i.get("updateTime")) for i in payload}
    return {}

def get_pod_metrics(label_selector, instance_queue_map):
    api = client.CustomObjectsApi()
    metrics = api.list_cluster_custom_object(
        group="metrics.k8s.io",
        version="v1beta1",
        plural="pods",
        label_selector=label_selector
    )
    pod_data = []
    for item in metrics['items']:
        pod_name = item['metadata']['name']
        containers = item['containers']
        cpu_total = 0
        mem_total = 0
        for c in containers:
            cpu = c['usage']['cpu']
            mem = c['usage']['memory']
            # Convert cpu to millicores
            if cpu.endswith('n'):
                cpu_val = int(cpu[:-1]) / 1_000_000
            elif cpu.endswith('u'):
                cpu_val = int(cpu[:-1]) / 1_000
            elif cpu.endswith('m'):
                cpu_val = int(cpu[:-1])
            else:
                cpu_val = int(cpu)
            cpu_total += cpu_val
            # Convert memory to GB
            if mem.endswith('Ki'):
                mem_val = int(mem[:-2]) * 1024
            elif mem.endswith('Mi'):
                mem_val = int(mem[:-2]) * 1024 * 1024
            elif mem.endswith('Gi'):
                mem_val = int(mem[:-2]) * 1024 * 1024 * 1024
            else:
                mem_val = int(mem)
            mem_total += mem_val
        # Lookup instanceQueue for this pod
        instance_queue = instance_queue_map.get(pod_name,"N/A")
        pod_data.append({
            "podname": pod_name,
            "cpu_data": cpu_total,  # in millicores
            "mem_data": round(mem_total / (1024 ** 3), 3),  # in GB
            "instanceQueue": instance_queue[0],
            "eventsReceivedPerTick": instance_queue[1],
            "updateTime": instance_queue[2]
        })
    return pod_data

def write_to_excel(label_selectors, filename, instance_queue_map):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for label in label_selectors:
        ws = wb.create_sheet(title=label.replace("baseComponent=node.", "").replace("algorithm.objdet.", "").replace("utils.policy.", "").replace("utils.usecase.", "").replace("algorithm.posekey.", "").replace("algorithm.tracker.", "").replace("algorithm.reid.", "").replace("algorithm.genderRecognition.", "").replace("algorithm.vehicles5Detection.", "").replace("-v0.0.1-stable", "").replace("algorithm.cameraTamper.", ""))
        ws.append(["podname", "cpu_data (millicores)", "mem_data (GB)", "instanceQueue", "eventsReceivedPerTick(60seconds)", "updateTime"])
        pod_metrics = get_pod_metrics(label, instance_queue_map)
        for pod in pod_metrics:
            print(pod["updateTime"])
            utcobj = datetime.fromtimestamp(pod["updateTime"])
            if IS_TIMING_IST:
                istobj = utcobj + timedelta(hours=5,minutes=30)
            else:
                istobj = utcobj
            istStr = istobj.strftime("%Y-%m-%d %H:%M:%S")
            ws.append([pod["podname"], pod["cpu_data"], pod["mem_data"], pod["instanceQueue"], pod["eventsReceivedPerTick"], istStr])
    wb.save(filename)

# def main():
#     pods = get_pod_names()
#     print(f"Found pods: {pods}")
#     for pod in pods:
#         # Average CPU (5 min rate)
#         cpu_query = f'rate(container_cpu_usage_seconds_total{{namespace="{NAMESPACE}", pod="{pod}", container!="POD"}}[5m])'
#         cpu_data = query_prometheus(cpu_query)

#         # RAM in bytes
#         mem_query = f'container_memory_usage_bytes{{namespace="{NAMESPACE}", pod="{pod}", container!="POD"}}'
#         mem_data = query_prometheus(mem_query)

#         # Parse results
#         cpu_val = cpu_data[0]['value'][1] if cpu_data else "N/A"
#         mem_val = mem_data[0]['value'][1] if mem_data else "N/A"

#         print(f"Pod: {pod}")
#         print(f"  CPU (cores, 5m avg): {cpu_val}")
#         print(f"  RAM (bytes): {mem_val}\n")

if __name__ == "__main__":
    config.load_kube_config()
    LABEL_SELECTORS = [
        "baseComponent=node.algorithm.objdet.general7Detection_360h_640-v0.0.1-stable",
        "baseComponent=node.utils.policy.policy-v0.0.1-stable",
        "baseComponent=node.utils.policy.policy_mux-v0.0.1-stable",
        "baseComponent=node.utils.usecase.usecase-v0.0.1-stable",
        "baseComponent=node.algorithm.objdet.luggage7Detection_1080_1920-v0.0.1-stable",
        "baseComponent=node.algorithm.cameraTamper.camTamp_360h_640w-v0.0.1-stable",
        "baseComponent=node.algorithm.objdet.fall7Detection_640h_640-v0.0.1-stable",
        "baseComponent=node.utils.usecase.usecasmux_3input-v0.0.1-stable",
        "baseComponent=node.utils.usecase.usecase-frames-v0.0.1-stable",
        "baseComponent=node.algorithm.posekey.pose-estimation-rt-v0.0.1-stable",
        "baseComponent=node.algorithm.tracker.trackerlitefast_960x540-v0.0.1-stable",
        "baseComponent=node.algorithm.tracker.trackerlite-v0.0.1-stable",
        "baseComponent=node.algorithm.objdet.firesmoke7Det_512h_896w-v0.0.1-stable",
        "baseComponent=node.algorithm.objdet.fight3Det-v0.0.1-stable",
        "baseComponent=node.algorithm.reid.reidbaselineallres-v0.0.1-stable",
        "baseComponent=node.algorithm.objdet.weapon7Detection_896_896-v0.0.1-stable",
        "baseComponent=node.algorithm.genderRecognition.custbodygend75-v0.0.1-stable",
        "baseComponent=node.algorithm.objdet.vehicles5Detection_360h_640-v0.0.1-stable"

        # add more label selectors as needed
    ]
    endPoint = "http://172.16.9.13:32000/dag-actions/api/queryQueueLengths"  # <-- set your endpoint here
    headers = {
        "Content-Type": "application/json",
        # add more headers if needed
    }
    instance_queue_map = fetch_instance_queues(endPoint, headers)
    #print(instance_queue_map)
    write_to_excel(LABEL_SELECTORS, "pod_metrics.xlsx", instance_queue_map)
