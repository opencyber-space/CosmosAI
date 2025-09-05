import logging
import json
import uuid
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException
from init_container_sdk import execute_init_container
import yaml,time

class VLLMInitExecutor:
    def __init__(self, envs, block_data, cluster_data, _unused_k8s, operating_mode="creation"):
        self.envs = envs
        self.block_data = block_data
        self.cluster_data = cluster_data
        self.operating_mode = operating_mode

        # Load Kubernetes config
        try:
            config.load_incluster_config()
        except Exception:
            config.load_kube_config()

        self.core_api = client.CoreV1Api()
        self.api_client = client.ApiClient()
        
        self.pod_specifications = []
        if operating_mode == "creation":
            allocation_data = json.loads(envs.get("allocation_data"))
            logging.info(f"[__init__] allocation_data: {allocation_data}")
            # The new allocation data is expected to be a list of dictionaries
            # e.g., [{"node_id": "node1", "gpu_id": 0}, {"node_id": "node2", "gpu_id": 1}]
            raw_allocations = allocation_data['data']
            raw_allocations = raw_allocations.get("allocation",[])
            if not isinstance(raw_allocations, list):
                raise ValueError("Allocation data must be a list of node/GPU specifications.")
            
            self.pod_specifications = raw_allocations
            if not self.pod_specifications:
                raise ValueError("Allocation data cannot be empty for creation.")
      
        self.block_init_data = block_data.get("blockInitData", {})
        self.initSettings = block_data.get("initSettings", {})
        self.hf_token = self.initSettings.get("hf_token", "")

        # BlockInitData parameters
        self.deployment_name = self.block_init_data.get("deployment_name", "vllm")
        
        # The number of replicas is now determined by the allocation data.
        original_replicas = int(self.block_init_data.get("replicas", 1))
        self.replicas = len(self.pod_specifications) if self.pod_specifications else original_replicas
        if self.operating_mode == "creation" and self.replicas != original_replicas:
            logging.warning(f"Overriding 'replicas' from {original_replicas} to {self.replicas} based on allocation data length.")

        self.image = self.block_init_data.get(
            "image", "docker.io/vllm/vllm-openai:latest")
        self.model = self.block_init_data.get(
            "model", "Qwen/Qwen1.5-0.5B-Chat")
        self.max_model_len = int(
            self.block_init_data.get("max_model_len", 8192))
        self.tensor_parallel = int(
            self.block_init_data.get("tensor_parallel_size", self.replicas))
        self.pipeline_parallel = int(
            self.block_init_data.get("pipeline_parallel_size", 1))
        self.api_port = int(self.block_init_data.get("api_port", 8080))
        self.ray_port = int(self.block_init_data.get("ray_port", 6379))
        self.shm_size = self.block_init_data.get("shm_size", "15Gi")
        self.namespace = self.block_init_data.get("namespace", "default")
        self.gpu_memory_utilization = self.block_init_data.get("gpu_memory_utilization", 0.90)

        # Internally generated names
        self.leader_service_name = f"{self.deployment_name}-leader-svc"

    def _generate_resource_definitions(self):
        """Generates the definitions for all Kubernetes resources."""
        if not self.pod_specifications:
             raise ValueError("Cannot generate resources without pod specifications.")

        labels = {"app": self.deployment_name}
        leader_labels = {"app": self.deployment_name, "role": "leader"}
        worker_labels = {"app": self.deployment_name, "role": "worker"}
        
        # --- 1. Leader Service Definition ---
        leader_service = {
            "apiVersion": "v1", "kind": "Service",
            "metadata": {"name": self.leader_service_name, "namespace": self.namespace, "labels": labels},
            "spec": {
                "selector": leader_labels,
                "ports": [
                    {"name": "http-api", "port": self.api_port, "targetPort": self.api_port},
                    {"name": "ray-head", "port": self.ray_port, "targetPort": self.ray_port}
                ]
            }
        }

        # --- Shared Pod Spec components ---
        shared_volume = {"name": "dshm", "emptyDir": {"medium": "Memory", "sizeLimit": self.shm_size}}
        shared_volume_mount = {"mountPath": "/dev/shm", "name": "dshm"}
        cache_volume = {"name": "model-cache", "hostPath": {"path": "/home/ubuntu/models", "type": "DirectoryOrCreate"}}
        cache_volume_mount = {"mountPath": "/root/.cache", "name": "model-cache"}
        shared_env = [
            {"name": "NVIDIA_DRIVER_CAPABILITIES", "value": "all"},
            {"name": "HUGGING_FACE_HUB_TOKEN", "value": self.hf_token},
            {"name": "HF_TOKEN", "value": self.hf_token}
        ]

        # --- 2. Leader Pod Definition ---
        leader_spec = self.pod_specifications[0]
        leader_command = (
            f"bash /vllm-workspace/examples/online_serving/multi-node-serving.sh leader --ray_cluster_size={self.replicas}; "
            f"python3 -m vllm.entrypoints.openai.api_server --port {self.api_port} --model {self.model} "
            f"--max-model-len {self.max_model_len} --tensor-parallel-size {self.tensor_parallel} "
            f"--pipeline-parallel-size {self.pipeline_parallel} --gpu-memory-utilization {self.gpu_memory_utilization} "
            f"--download-dir /root/.cache"
        )
        leader_pod = {
            "apiVersion": "v1", "kind": "Pod",
            "metadata": {"name": f"{self.deployment_name}-leader", "namespace": self.namespace, "labels": leader_labels},
            "spec": {
                "nodeName": leader_spec['node_id'], 
                "volumes": [shared_volume, cache_volume],
                "containers": [{
                    "name": "vllm-leader", "image": self.image,
                    "env": shared_env + [{"name": "NVIDIA_VISIBLE_DEVICES", "value": str(leader_spec['gpu_id'])}],
                    "command": ["sh", "-c", leader_command],
                    "ports": [{"containerPort": self.api_port}, {"containerPort": self.ray_port}],
                    "volumeMounts": [shared_volume_mount, cache_volume_mount]
                }]
            }
        }

        # --- 3. Worker Pods Definition ---
        worker_pods = []
        #ray_address = f"{self.leader_service_name}" #:{self.ray_port}"
        ray_address = f"{self.leader_service_name}.vllm-blocks.svc.cluster.local"
        worker_command = f"sleep 5; bash /vllm-workspace/examples/online_serving/multi-node-serving.sh worker --ray_address={ray_address}"
        logging.info(f"[VLLMInitExecutor] ray_address: {ray_address}")
        for i, worker_spec in enumerate(self.pod_specifications[1:]):
            worker_pod = {
                "apiVersion": "v1", "kind": "Pod",
                "metadata": {"name": f"{self.deployment_name}-worker-{i}", "namespace": self.namespace, "labels": worker_labels},
                "spec": {
                    "nodeName": worker_spec['node_id'], 
                    "volumes": [shared_volume, cache_volume],
                    "containers": [{
                        "name": "vllm-worker", "image": self.image,
                        "env": shared_env + [{"name": "NVIDIA_VISIBLE_DEVICES", "value": str(worker_spec['gpu_id'])}],
                        "command": ["sh", "-c", worker_command],
                        "volumeMounts": [shared_volume_mount, cache_volume_mount]
                    }]
                }
            }
            worker_pods.append(worker_pod)
        time.sleep(60)
        return [leader_service, leader_pod] + worker_pods

    def begin(self):
        logging.info("[VLLMInitExecutor] Begin stage")
        # Node labeling is no longer needed as we use direct nodeName scheduling
        if self.operating_mode == "creation":
            return True, {"message": "Begin creation"}
        return True, {"message": "Begin cleanup"}

    def _ensure_namespace_exists(self):
        try:
            self.core_api.read_namespace(self.namespace)
            logging.info(f"Namespace '{self.namespace}' already exists.")
        except ApiException as e:
            if e.status == 404:
                namespace_body = client.V1Namespace(metadata=client.V1ObjectMeta(name=self.namespace))
                self.core_api.create_namespace(namespace_body)
                logging.info(f"Namespace '{self.namespace}' created.")
            else:
                logging.error(f"Error checking namespace '{self.namespace}': {e}")
                raise

    def main(self):
        logging.info(f"[VLLMInitExecutor] Main stage: {self.operating_mode}")
        app_label_selector = f"app={self.deployment_name}"

        if self.operating_mode == "remove":
            # Delete service
            try:
                self.core_api.delete_namespaced_service(name=self.leader_service_name, namespace=self.namespace)
                logging.info(f"Service '{self.leader_service_name}' deleted.")
            except ApiException as e:
                if e.status != 404:
                    logging.warning(f"Failed to delete service: {e}")
            
            # Delete pods
            try:
                self.core_api.delete_collection_namespaced_pod(namespace=self.namespace, label_selector=app_label_selector)
                logging.info(f"Pods with label '{app_label_selector}' deleted.")
            except ApiException as e:
                logging.warning(f"Failed to delete pods: {e}")

            return True, {"message": "Resources deleted"}

        self._ensure_namespace_exists()
        resource_definitions = self._generate_resource_definitions()

        logging.info(f"Applying {len(resource_definitions)} resource definitions.")
        
        try:
            # Use the utils function to apply all definitions from the list of dicts
            utils.create_from_yaml(
                self.api_client,
                yaml_objects=resource_definitions,
                namespace=self.namespace,
            )
            return True, {"message": "Resources created"}
        except Exception as e:
            return False, f"Failed to apply YAML: {e}"

    def finish(self):
        if self.operating_mode == "creation":
            url = f"http://{self.leader_service_name}.{self.namespace}.svc.cluster.local:{self.api_port}"
            return True, {"inference_url": url}
        return True, {"message": "Removed"}

if __name__ == "__main__":
    execute_init_container(VLLMInitExecutor)

