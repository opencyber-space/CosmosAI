import logging
import json
import uuid
from io import StringIO
from kubernetes import client, config, utils
from kubernetes.client import CustomObjectsApi
from kubernetes.client.rest import ApiException
from init_container_sdk import execute_init_container
import yaml

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
        self.init_id = f"init-{uuid.uuid4().hex[:8]}"
        self.init_label_key = "vllm-init"
        self.label_selector = f"{self.init_label_key}={self.init_id}"

        self.allocation_data = None
        self.gpu_ids = None
        self.worker_gpu_ids = None

        if operating_mode == "creation":
          self.allocation_data = json.loads(envs.get("allocation_data"))
          self.allocation_data = self.allocation_data['data']

          self.gpu_ids = self.allocation_data.get('gpus', 'all')
          self.worker_gpu_ids = self.allocation_data.get('worker_gpus', 'all')

          if type(self.gpu_ids) == list:
            workers = [str(x) for x in self.gpu_ids]
            self.gpu_ids = ",".join(workers)
        
          if type(self.worker_gpu_ids) == list:
            workers = [str(x) for x in self.worker_gpu_ids]
            self.worker_gpu_ids = ",".join(workers)
      

        self.block_init_data = block_data.get("blockInitData", {})

        # BlockInitData parameters
        self.lws_name = self.block_init_data.get("lws_name", "vllm")
        self.replicas = int(self.block_init_data.get("replicas", 1))
        self.group_size = int(self.block_init_data.get("group_size", 2))
        self.image = self.block_init_data.get(
            "image", "docker.io/vllm/vllm-openai:latest")
        self.model = self.block_init_data.get(
            "model", "Qwen/Qwen1.5-0.5B-Chat")
        self.max_model_len = int(
            self.block_init_data.get("max_model_len", 8192))
        self.tensor_parallel = int(
            self.block_init_data.get("tensor_parallel_size", 2))
        self.pipeline_parallel = int(
            self.block_init_data.get("pipeline_parallel_size", 1))
        self.api_port = int(self.block_init_data.get("api_port", 8080))
        self.shm_size = self.block_init_data.get("shm_size", "15Gi")
        self.service_name = self.block_init_data.get(
            "service_name", "vllm-leader")
        self.namespace = self.block_init_data.get("namespace", "default")

    def _label_nodes(self):
        for nodeID in self.allocation_data["nodes"]:
            node = self.core_api.read_node(nodeID)
            labels = node.metadata.labels or {}
            labels[self.init_label_key] = self.init_id
            body = {"metadata": {"labels": labels}}
            self.core_api.patch_node(nodeID, body)

    def _unlabel_nodes(self):
        try:
            node_list = self.core_api.list_node().items
        except Exception as e:
            logging.error(f"Failed to list Kubernetes nodes: {e}")
            return

        for node in node_list:
            node_name = node.metadata.name
            try:
                labels = node.metadata.labels or {}
                if self.init_label_key in labels:
                    del labels[self.init_label_key]
                    body = {"metadata": {"labels": labels}}
                    self.core_api.patch_node(node_name, body)
                    logging.info(f"Removed label '{self.init_label_key}' from node: {node_name}")
                else:
                    logging.debug(f"Label '{self.init_label_key}' not present on node: {node_name}")
            except Exception as e:
                logging.warning(f"Failed to remove label from {node_name}: {e}")

    def _generate_yaml(self):
        return f"""
apiVersion: leaderworkerset.x-k8s.io/v1
kind: LeaderWorkerSet
metadata:
  name: {self.lws_name}
  namespace: {self.namespace}
spec:
  replicas: {self.replicas}
  leaderWorkerTemplate:
    size: {self.group_size}
    restartPolicy: RecreateGroupOnPodRestart
    leaderTemplate:
      metadata:
        labels:
          role: leader
      spec:
        nodeSelector:
          {self.init_label_key}: "{self.init_id}"
        containers:
          - name: vllm-leader
            env:
              - name: NVIDIA_VISIBLE_DEVICES
                value: '{self.gpu_ids}'
              - name: NVIDIA_DRIVER_CAPABILITIES
                value: 'all'
            image: {self.image}
            command:
              - sh
              - -c
              - >
                bash /vllm-workspace/examples/online_serving/multi-node-serving.sh leader --ray_cluster_size=$(LWS_GROUP_SIZE);
                python3 -m vllm.entrypoints.openai.api_server --port {self.api_port} --model {self.model} --max-model-len {self.max_model_len} --tensor-parallel-size {self.tensor_parallel} --pipeline-parallel-size {self.pipeline_parallel}
            ports:
              - containerPort: {self.api_port}
            volumeMounts:
              - mountPath: /dev/shm
                name: dshm
        volumes:
          - name: dshm
            emptyDir:
              medium: Memory
              sizeLimit: {self.shm_size}
    workerTemplate:
      metadata:
        labels:
          role: worker
      spec:
        nodeSelector:
          {self.init_label_key}: "{self.init_id}"
        containers:
          - name: vllm-worker
            env:
              - name: NVIDIA_VISIBLE_DEVICES
                value: '{self.worker_gpu_ids}'
              - name: NVIDIA_DRIVER_CAPABILITIES
                value: 'all'
            image: {self.image}
            command:
              - sh
              - -c
              - >
                bash /vllm-workspace/examples/online_serving/multi-node-serving.sh worker --ray_address=$(LWS_LEADER_ADDRESS)
            volumeMounts:
              - mountPath: /dev/shm
                name: dshm
        volumes:
          - name: dshm
            emptyDir:
              medium: Memory
              sizeLimit: {self.shm_size}"""

    def _generate_svc(self):
      try:
        return f"""
apiVersion: v1
kind: Service
metadata:
  name: {self.service_name}
  namespace: {self.namespace}
spec:
  ports:
    - name: http
      port: {self.api_port}
      protocol: TCP
      targetPort: {self.api_port}
  selector:
    leaderworkerset.sigs.k8s.io/name: {self.lws_name}
    role: leader
  type: NodePort"""

      except Exception as e:
        raise e

    def begin(self):
        logging.info("[VLLMInitExecutor] Begin stage")
        if self.operating_mode == "creation":
            self._label_nodes()
            return True, {"message": "Nodes labeled"}
        return True, {"message": "Cleanup init"}
    

    def _ensure_namespace_exists(self):
        try:
            self.core_api.read_namespace(self.namespace)
            logging.info(f"Namespace '{self.namespace}' already exists.")
        except ApiException as e:
            if e.status == 404:
                # Namespace does not exist, so create it
                namespace_body = client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=self.namespace)
                )
                self.core_api.create_namespace(namespace_body)
                logging.info(f"Namespace '{self.namespace}' created.")
            else:
                logging.error(f"Error checking namespace '{self.namespace}': {e}")
                raise

    def main(self):
        logging.info(f"[VLLMInitExecutor] Main stage: {self.operating_mode}")
        if self.operating_mode == "remove":
            try:
                client.CustomObjectsApi().delete_namespaced_custom_object(
                    group="leaderworkerset.x-k8s.io",
                    version="v1",
                    namespace=self.namespace,
                    plural="leaderworkersets",
                    name=self.lws_name,
                )
            except Exception as e:
                logging.warning(f"Failed to delete LWS: {e}")
            try:
                self.core_api.delete_namespaced_service(
                    self.service_name, self.namespace)
            except Exception as e:
                logging.warning(f"Failed to delete service: {e}")
            self._unlabel_nodes()
            return True, {"message": "Resources deleted"}

        self._ensure_namespace_exists()

        yaml_str = self._generate_yaml()
        svc_str = self._generate_svc()

        logging.info(f"YAML string: {yaml_str}")

        try:
            lws_obj = yaml.safe_load(yaml_str)
            svc_obj = yaml.safe_load(svc_str)
            co_api = CustomObjectsApi(self.api_client)
            co_api.create_namespaced_custom_object(
                group="leaderworkerset.x-k8s.io",
                version="v1",
                namespace=self.namespace,
                plural="leaderworkersets",
                body=lws_obj,
            )

            # Apply Service using CoreV1Api
            utils.create_from_yaml(
                self.api_client,
                yaml_objects=[svc_obj],
                namespace=self.namespace,
            )
            return True, {"message": "Resources created"}
        except Exception as e:
            return False, f"Failed to apply YAML: {e}"

    def finish(self):
        if self.operating_mode == "creation":
            url = f"http://{self.service_name}.{self.namespace}.svc.cluster.local:{self.api_port}"
            return True, {"inference_url": url}
        return True, {"message": "Removed"}


if __name__ == "__main__":
  execute_init_container(VLLMInitExecutor)