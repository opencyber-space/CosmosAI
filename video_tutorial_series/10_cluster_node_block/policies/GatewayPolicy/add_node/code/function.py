from typing import Dict, Any, List
from datetime import datetime

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
            "allowed_tags": parameters.get("allowed_tags", []),
            #"required_tags": parameters.get("required_tags", ["production"]),
            "min_network_interfaces": parameters.get("min_network_interfaces", 1),
            "min_tx_bandwidth": parameters.get("min_tx_bandwidth", 1000),
            "min_rx_bandwidth": parameters.get("min_rx_bandwidth", 1000)
        }
        self.current_time = datetime.utcnow().isoformat()
        
    def _validate_node_hardware(self, node_data: Dict) -> tuple[bool, str]:
        print(f"Validating node hardware with parameters: {self.parameters} --- {node_data} ---")
        if node_data.get("vcpus", {}).get("count", 0) < self.parameters["min_node_cpu"]:
            return False, f"Insufficient vCPU. Required: {self.parameters['min_node_cpu']}"

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

    def _update_tags(self, data: dict) -> dict:
        """Update tag requirements."""
        try:
            # if not isinstance(data.get("allowed_tags", []), list) or \
            #    not isinstance(data.get("required_tags", []), list):
            #     raise ValueError("Tags must be provided as lists")
            if not isinstance(data.get("allowed_tags", []), list):
                raise ValueError("Allowed tags must be provided as a list")

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
            for key in ["min_network_interfaces", "min_tx_bandwidth", "min_rx_bandwidth"]:
                if key in data:
                    self.parameters[key] = int(data[key])
            return {
                "status": "success",
                "updated_parameters": {
                    key: self.parameters[key] 
                    for key in ["min_network_interfaces", "min_tx_bandwidth", "min_rx_bandwidth"]
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
            self._validate_tags(node_data)
        ]

        for is_valid, message in validations:
            if not is_valid:
                print(f"Validation failed: {message}")
                return {
                    "allowed": False,
                    "input_data": {
                        "error": message,
                        "timestamp": self.current_time
                    }
                }

        return {
            "allowed": True,
            "input_data": input_data
            # "input_data": {
            #     "message": "Node addition approved",
            #     "node_data": node_data,
            #     "timestamp": self.current_time
            # }
        }