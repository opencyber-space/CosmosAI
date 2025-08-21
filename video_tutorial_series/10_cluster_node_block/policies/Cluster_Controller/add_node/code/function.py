from typing import Dict, Any, List
from datetime import datetime
import logging

class AIOSv1PolicyRule:
    def __init__(self, rule_id: str, settings: Dict, parameters: Dict):
        # All fields can be updated via management functions, so settings is empty
        self.settings = {}
        
        # All configurable parameters
        self.parameters = {
            "min_node_cpu": parameters.get("min_node_cpu", 4),
            "min_node_memory": parameters.get("min_node_memory", 8192),
            "min_node_storage": parameters.get("min_node_storage", 102400),
            "required_gpu_models": parameters.get("required_gpu_models", []),
            "min_gpu_memory": parameters.get("min_gpu_memory", 8192),
            "max_nodes_per_cluster": parameters.get("max_nodes_per_cluster", 100),
            "max_gpus_per_cluster": parameters.get("max_gpus_per_cluster", 32),
            "allowed_tags": parameters.get("allowed_tags", []),
            #"required_tags": parameters.get("required_tags", ["production"]),
            "min_network_interfaces": parameters.get("min_network_interfaces", 1),
            "min_tx_bandwidth": parameters.get("min_tx_bandwidth", 1000),
            "min_rx_bandwidth": parameters.get("min_rx_bandwidth", 1000),

            #add KPI based check if needed
            "threshold_cluster_vcpu_utilization_for_add_node": parameters.get("threshold_cluster_vcpu_utilization_for_add_node", 0.5)
        }
        self.current_time = datetime.utcnow().isoformat()
        
    def _validate_node_hardware(self, node_data: Dict) -> tuple[bool, str]:
        if node_data.get("vcpus", {}).get("count", 0) < self.parameters["min_node_cpu"]:
            return False, f"Insufficient CPU cores. Required: {self.parameters['min_node_cpu']}"

        if node_data.get("memory", 0) < self.parameters["min_node_memory"]:
            return False, f"Insufficient memory. Required: {self.parameters['min_node_memory']}MB"

        if node_data.get("storage", {}).get("size", 0) < self.parameters["min_node_storage"]:
            return False, f"Insufficient storage. Required: {self.parameters['min_node_storage']}MB"

        gpus = node_data.get("gpus", {})
        if self.parameters["required_gpu_models"]:
            gpu_models = gpus.get("modelNames", [])
            if not all(model in self.parameters["required_gpu_models"] for model in gpu_models):
                unauthorized_models = [model for model in gpu_models if model not in self.parameters["required_gpu_models"]]
                return False, f"Unauthorized GPU models found: {unauthorized_models}. Allowed models: {self.parameters['required_gpu_models']}"

        if self.parameters["min_gpu_memory"] > 0:
            gpu_array = gpus.get("gpus", [])
            if not all(onegpuDict.get("memory", 0) > self.parameters["min_gpu_memory"] for onegpuDict in gpu_array):
                return False, f"Insufficient GPU memory. Required: {self.parameters['min_gpu_memory']}MB"
        
        if node_data.get("network", {}).get("interfaces", 0) < self.parameters["min_network_interfaces"]:
            return False, f"Insufficient network interfaces. Required: {self.parameters['min_network_interfaces']}"

        if node_data.get("network", {}).get("txBandwidth", 0) < self.parameters["min_tx_bandwidth"]:
            return False, f"Insufficient TX bandwidth. Required: {self.parameters['min_tx_bandwidth']}Mbps"

        if node_data.get("network", {}).get("rxBandwidth", 0) < self.parameters["min_rx_bandwidth"]:
            return False, f"Insufficient RX bandwidth. Required: {self.parameters['min_rx_bandwidth']}Mbps"


        return True, "Hardware validation successful"

    def _validate_cluster_capacity(self, cluster_data: Dict, cluster_metrics: Dict, node_data: Dict) -> tuple[bool, str]:
        logging.info(f"Validating cluster capacity with parameters: {self.parameters} --- {cluster_data} --- {node_data} ---")
        current_nodes = len(cluster_data.get("nodes", {}).get("nodeData", [])) + 1  # +1 for the new node being added
        logging.info(f"current_nodes: {current_nodes}")
        if current_nodes > self.parameters["max_nodes_per_cluster"]:
            return False, f"Cluster node limit will be reached: {self.parameters['max_nodes_per_cluster']}"

        total_cluster_gpus = sum(node.get("gpus", {}).get("count", 0) 
                        for node in cluster_data.get("nodes", {}).get("nodeData", []))
        current_node_gpus = node_data.get("gpus", {}).get("count", 0)
        logging.info(f"total_cluster_gpus: {total_cluster_gpus} current_node_gpus: {current_node_gpus}")
        if (total_cluster_gpus + current_node_gpus) > self.parameters["max_gpus_per_cluster"]:
            return False, f"Cluster GPU limit will be reached: {self.parameters['max_gpus_per_cluster']}"


        #KPI based rule for adding a node
        cluster_vcpu = cluster_metrics.get("cluster_metrics", {}).get("vcpu", {})
        if "load5m" in cluster_vcpu:
            cluster_load5m = cluster_vcpu["load5m"]
            cluster_vcpu_count = cluster_data.get("vcpus", {}).get("count", 0)
            perc = cluster_load5m / cluster_vcpu_count if cluster_vcpu_count > 0 else 0
            if perc < self.parameters["threshold_cluster_vcpu_utilization_for_add_node"]:
                return False, f"Cluster vCPU utilization is below the threshold: {self.parameters['threshold_cluster_vcpu_utilization_for_add_node']} and cluster_load5m={cluster_load5m} and perc={perc}"

        return True, "Cluster capacity validation successful"
    
    def _validate_tags(self, node_data: Dict) -> tuple[bool, str]:
        # if not all(tag in node_data.get("tags", []) for tag in self.parameters["required_tags"]):
        #     return False, f"Missing required tags: {self.parameters['required_tags']}"

        if not any(tag in node_data.get("tags", []) for tag in self.parameters["allowed_tags"]):
            return False, f"Node must have at least one allowed tag: {self.parameters['allowed_tags']}"

        return True, "Tag validation successful"

    def management(self, action: str, data: dict) -> dict:
        """Handle management actions for policy parameters."""
        actions = {
            "update_min_resources": self._update_min_resources,
            "update_cluster_limits": self._update_cluster_limits,
            "update_tags": self._update_tags,
            "update_network_requirements": self._update_network_requirements,
            "update_gpu_requirements": self._update_gpu_requirements
        }
        
        if action not in actions:
            return {
                "status": "error", 
                "message": f"Unknown action '{action}'",
                "timestamp": self.current_time,
                
            }
            
        return actions[action](data)

    def _update_min_resources(self, data: dict) -> dict:
        """Update minimum resource requirements."""
        try:
            for key in ["min_node_cpu", "min_node_memory", "min_node_storage"]:
                if key in data:
                    self.parameters[key] = int(data[key])
            return {
                "status": "success",
                "updated_parameters": {
                    key: self.parameters[key] 
                    for key in ["min_node_cpu", "min_node_memory", "min_node_storage"]
                },
                "timestamp": self.current_time,
                
            }
        except ValueError as e:
            return {
                "status": "error", 
                "message": str(e),
                "timestamp": self.current_time,
                
            }

    def _update_cluster_limits(self, data: dict) -> dict:
        """Update cluster capacity limits."""
        try:
            for key in ["max_nodes_per_cluster", "max_gpus_per_cluster"]:
                if key in data:
                    self.parameters[key] = int(data[key])
            return {
                "status": "success",
                "updated_parameters": {
                    key: self.parameters[key] 
                    for key in ["max_nodes_per_cluster", "max_gpus_per_cluster"]
                },
                "timestamp": self.current_time,
                
            }
        except ValueError as e:
            return {
                "status": "error", 
                "message": str(e),
                "timestamp": self.current_time,
                
            }

    def _update_tags(self, data: dict) -> dict:
        """Update tag requirements."""
        try:
            # if not isinstance(data.get("allowed_tags", []), list) or \
            #    not isinstance(data.get("required_tags", []), list):
            #     raise ValueError("Tags must be provided as lists")
            if not isinstance(data.get("allowed_tags", []), list):
                raise ValueError("Tags must be provided as lists")

            if "allowed_tags" in data:
                self.parameters["allowed_tags"] = data["allowed_tags"]
            # if "required_tags" in data:
            #     self.parameters["required_tags"] = data["required_tags"]

            return {
                "status": "success",
                "updated_parameters": {
                    "allowed_tags": self.parameters["allowed_tags"]
                    #"required_tags": self.parameters["required_tags"]
                },
                "timestamp": self.current_time,
                
            }
        except ValueError as e:
            return {
                "status": "error", 
                "message": str(e),
                "timestamp": self.current_time,
                
            }

    def _update_network_requirements(self, data: dict) -> dict:
        """Update network requirements."""
        try:
            for key in ["min_network_interfaces", "min_tx_bandwidth","min_rx_bandwidth"]:
                if key in data:
                    self.parameters[key] = int(data[key])
            return {
                "status": "success",
                "updated_parameters": {
                    key: self.parameters[key] 
                    for key in ["min_network_interfaces", "min_tx_bandwidth","min_rx_bandwidth"]
                },
                "timestamp": self.current_time,
                
            }
        except ValueError as e:
            return {
                "status": "error", 
                "message": str(e),
                "timestamp": self.current_time,
                
            }

    def _update_gpu_requirements(self, data: dict) -> dict:
        """Update GPU requirements."""
        try:
            if "required_gpu_models" in data:
                if not isinstance(data["required_gpu_models"], list):
                    raise ValueError("GPU models must be provided as a list")
                self.parameters["required_gpu_models"] = data["required_gpu_models"]
            
            if "min_gpu_memory" in data:
                self.parameters["min_gpu_memory"] = int(data["min_gpu_memory"])

            return {
                "status": "success",
                "updated_parameters": {
                    "required_gpu_models": self.parameters["required_gpu_models"],
                    "min_gpu_memory": self.parameters["min_gpu_memory"]
                },
                "timestamp": self.current_time,
                
            }
        except ValueError as e:
            return {
                "status": "error", 
                "message": str(e),
                "timestamp": self.current_time,
                
            }

    def eval(self, parameters: Dict, input_data: Dict, context: Dict) -> Dict:
        node_data = input_data.get("node_data", {})
        cluster_data = input_data.get("cluster_data", {})
        cluster_metrics = input_data.get("cluster_metrics", {})
        
        validations = [
            self._validate_node_hardware(node_data),
            self._validate_cluster_capacity(cluster_data, cluster_metrics, node_data),
            self._validate_tags(node_data)
        ]

        for is_valid, message in validations:
            if not is_valid:
                return {
                    "allowed": False,
                    "input_data": {
                        "error": message,
                        "timestamp": self.current_time
                    }
                }

        return {
            "allowed": True,
            "input_data": node_data
            # "input_data": {
            #     "message": "Node addition approved",
            #     "node_data": node_data,
            #     "timestamp": self.current_time
            # }
        }