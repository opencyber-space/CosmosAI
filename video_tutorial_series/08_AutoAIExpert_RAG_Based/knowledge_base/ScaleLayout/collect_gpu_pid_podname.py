import subprocess
import re
import os
import csv
import sys
import GPUtil
import time

def get_gpu_bus_id_to_index_map():
    """
    Creates a mapping from GPU Bus ID to its numerical GPU Index (0, 1, 2...).
    Returns a dictionary: {gpu_bus_id: gpu_index}
    """
    bus_id_to_index_map = {}
    try:
        command = "nvidia-smi --query-gpu=index,gpu_bus_id --format=csv,noheader"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.strip():
                try:
                    index_str, bus_id = line.split(', ')
                    bus_id_to_index_map[bus_id.strip()] = int(index_str.strip())
                except ValueError as e:
                    sys.stderr.write(f"Warning: Could not parse GPU index/bus_id line '{line}': {e}\n")
        return bus_id_to_index_map
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error running nvidia-smi for GPU index map: {e}\n")
        sys.stderr.write(f"Stderr: {e.stderr}\n")
        return {}
    except FileNotFoundError:
        sys.stderr.write("Error: nvidia-smi not found. Is NVIDIA driver installed and in PATH?\n")
        return {}

def get_nvidia_smi_processes(gpu_bus_id_map):
    """
    Parses nvidia-smi output using the specified query fields.
    Maps gpu_bus_id to gpu_index using the provided map.
    Returns a list of dictionaries: [{'pid': int, 'process_name': str, 'gpu_index': int, 'gpu_name': str, 'used_gpu_memory': str}]
    """
    gpu_processes = []
    try:
        # Use the query fields provided by the user
        command = "nvidia-smi --query-compute-apps=pid,process_name,gpu_bus_id,used_gpu_memory,gpu_name --format=csv,noheader"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if line.strip():
                try:
                    # Parse the comma-separated output
                    # Example line: 12345, python3, 00000000:01:00.0, 123MiB, NVIDIA GeForce RTX 3080
                    parts = [p.strip() for p in line.split(',')]
                    
                    if len(parts) == 5:
                        pid_str, process_name, gpu_bus_id, used_gpu_memory, gpu_name = parts
                        pid = int(pid_str)
                        
                        # Only add if PID is not 0 (nvidia-smi returns 0 for unused entries)
                        if pid > 0:
                            gpu_index = gpu_bus_id_map.get(gpu_bus_id, -1) # Get index from map, default -1 if not found
                            gpu_processes.append({
                                'pid': pid,
                                'process_name': process_name,
                                'gpu_index': gpu_index,
                                'gpu_name': gpu_name,
                                'used_gpu_memory': used_gpu_memory
                            })
                    else:
                        sys.stderr.write(f"Warning: Could not parse nvidia-smi process line (unexpected format, {len(parts)} parts): '{line}'\n")

                except ValueError as e:
                    sys.stderr.write(f"Warning: Could not parse nvidia-smi process line (data conversion error): '{line}' - {e}\n")
        return gpu_processes
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error running nvidia-smi for processes: {e}\n")
        sys.stderr.write(f"Stderr: {e.stderr}\n")
        return []
    except FileNotFoundError:
        sys.stderr.write("Error: nvidia-smi not found. Is NVIDIA driver installed and in PATH?\n")
        return []

def get_container_id_from_cgroup(pid):
    """
    Reads /proc/<pid>/cgroup to find the Docker container ID.
    Returns the full container ID string if found, otherwise None.
    """
    cgroup_file = f"/proc/{pid}/cgroup"
    try:
        with open(cgroup_file, 'r') as f:
            for line in f:
                # Optimized regex to capture either direct Docker ID or ID within kubepods path
                match = re.search(r'(?:/docker/([0-9a-f]{64}))|(?:/kubepods/[^/]+/[^/]+/([0-9a-f]{64}))|(?:[0-9a-f]{64})', line)
                if match:
                    if match.group(1): # Direct /docker/ match
                        return match.group(1)
                    elif match.group(2): # /kubepods/.../docker/ match
                        return match.group(2)
                    elif match.group(0) and re.match(r'^[0-9a-f]{64}$', match.group(0)): # Fallback for just a 64-char hex string
                        return match.group(0)
        return None
    except FileNotFoundError:
        return None
    except Exception as e:
        # sys.stderr.write(f"Error reading cgroup for PID {pid}: {e}\n") # Suppress errors for non-container PIDs to avoid clutter
        return None

def get_docker_container_details():
    """
    Gets details of running Docker containers, mapping full IDs to names and short IDs.
    Returns a dictionary: {full_id: {'name': str, 'short_id': str}}
    """
    try:
        command = "docker ps --no-trunc --format '{{.ID}}\t{{.Names}}'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        container_details = {}
        for line in lines:
            if line.strip():
                try:
                    full_id, name = line.split('\t')
                    container_details[full_id.strip()] = {
                        'name': name.strip(),
                        'short_id': full_id.strip()[:12]
                    }
                except ValueError as e:
                    sys.stderr.write(f"Warning: Could not parse docker ps line '{line}': {e}\n")
        return container_details
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error running docker ps: {e}\n")
        sys.stderr.write(f"Stderr: {e.stderr}\n")
        return {}
    except FileNotFoundError:
        sys.stderr.write("Error: docker not found. Is Docker installed and running?\n")
        return {}

def extract_block_name(container_name):
    """
    Extracts the 'block-b8cbe' like string from a Kubernetes container name.
    Assumes the format k8s_something_block-XXXXX_something.
    """
    match = re.search(r'block-([0-9a-f]+)', container_name)
    if match:
        return f"block-{match.group(1)}"
    return None

def get_average_gpu_util(num_samples=100, interval=0.25):
    """
    Returns a list of average GPU utilization percentages for each GPU.
    Collects num_samples samples for each GPU.
    """
    gpuutildata = []
    for cnt in range(num_samples):
        GPUs = GPUtil.getGPUs()
        if len(GPUs) != len(gpuutildata):
            for i in range(len(GPUs) - len(gpuutildata)):
                gpuutildata.append([])
        for i, gpu in enumerate(GPUs):
            gpuutildata[i].append(gpu.load * 100)
        time.sleep(interval)
    avg_utils = []
    for gpudata in gpuutildata:
        avgval = sum(gpudata) / len(gpudata) if gpudata else 0.0
        avg_utils.append(avgval)
    return avg_utils

def main():
    # Step 1: Get mapping from GPU Bus ID to GPU Index
    gpu_bus_id_map = get_gpu_bus_id_to_index_map()
    if not gpu_bus_id_map:
        sys.stderr.write("Warning: Could not retrieve GPU Bus ID to Index mapping. GPU Index might be -1.\n")

    # Step 2: Get GPU processes using the user-provided query and the GPU ID map
    gpu_processes = get_nvidia_smi_processes(gpu_bus_id_map)
    if not gpu_processes:
        sys.stderr.write("No GPU processes found or error retrieving them.\n")
        return

    # Step 3: Get Docker container details
    docker_containers = get_docker_container_details()
    if not docker_containers:
        sys.stderr.write("No Docker containers found or error retrieving them. Mapping to containers might be incomplete.\n")

    # Step 4: Get average GPU utilization for each GPU index
    avg_gpu_utils = get_average_gpu_util(num_samples=100, interval=0.25)

    # Define CSV header based on the requested output
    csv_headers = ["block_id", "pid", "gpu_index", "gpu_name", "used_gpu_memory", "avg_gpu_util"]

    # Write CSV output to file
    with open("block_gpu_processes.csv", mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(csv_headers) # Write header row

        for proc in gpu_processes:
            pid = proc['pid']
            proc_name = proc['process_name']
            gpu_index = proc['gpu_index']
            gpu_name = proc['gpu_name']
            used_gpu_memory = proc['used_gpu_memory']

            # Filter for python3 or python3.8 as requested
            if "python3" not in proc_name and "python3.8" not in proc_name:
                continue

            container_full_id = get_container_id_from_cgroup(pid)
            
            block_id = "N/A" # Default
            
            if container_full_id:
                container_found = False
                if container_full_id in docker_containers:
                    container_info = docker_containers[container_full_id]
                    block_id = extract_block_name(container_info['name'])
                    container_found = True
                else:
                    # Attempt to match by short ID if full ID doesn't directly match
                    for full_id_key, info in docker_containers.items():
                        if info['short_id'] == container_full_id[:12]:
                            block_id = extract_block_name(info['name'])
                            container_found = True
                            break
                
                if not container_found:
                    # If still not found, indicate it was an unmatched ID
                    block_id = f"Unmatched (cgroup ID: {container_full_id[:12]}...)"

            # Get average GPU util for this gpu_index
            avg_gpu_util = avg_gpu_utils[gpu_index] if 0 <= gpu_index < len(avg_gpu_utils) else None

            # Write the data row to CSV
            csv_writer.writerow([
                block_id,
                pid,
                gpu_index,
                gpu_name,
                used_gpu_memory,
                avg_gpu_util
            ])

if __name__ == "__main__":
    main()