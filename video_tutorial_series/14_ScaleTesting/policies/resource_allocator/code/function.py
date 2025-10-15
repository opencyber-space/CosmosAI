#!/usr/bin/env python3
"""
Block Resource Allocator Policy (Core Implementation)

This policy handles resource allocation for block instances within a selected cluster.
It implements four core actions:
1. "dry_run" - Simulates allocation and returns feasibility score
2. "allocation" - Performs actual resource allocation for new blocks  
3. "scale" - Allocates resources for scaling existing blocks
4. "reassignment" - Handles resource reallocation for reassigned instances

The policy integrates with helper policies for specialized allocation logic:
- Node Selection Helper: Optimal node selection based on requirements
- GPU Allocation Helper: GPU assignment and memory allocation
- Resource Scoring Helper: Feasibility score calculation
- Affinity Rules Helper: Placement constraints and rules

Input Format: {"action": "<action_type>", "payload": {...}}
Actions: dry_run, allocation, scale, reassignment
"""

import logging,sys
from typing import Dict, Any, List, Optional
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIOSv1PolicyRule:
    """
    Core Block Resource Allocator Policy
    
    Handles granular resource allocation within a cluster for block instances.
    Integrates with helper policies for specialized allocation logic.
    """
    
    def __init__(self, rule_id: str, settings: Dict[str, Any], parameters: Dict[str, Any]):
        """
        Initialize the Block Resource Allocator Policy.
        
        Args:
            rule_id (str): Unique identifier for the rule
            settings (dict): Configuration settings including database clients
            parameters (dict): Parameters for customizing allocation behavior
        """
        self.rule_id = rule_id
        self.settings = settings or {}
        self.parameters = parameters or {}
        
        # Core allocation parameters
        self.min_cpu_per_instance = parameters.get("min_cpu_per_instance", 1)
        self.min_memory_per_instance = parameters.get("min_memory_per_instance", 1024)  # MB
        self.min_gpu_memory_per_instance = parameters.get("min_gpu_memory_per_instance", 1024)  # MB
        self.min_storage = parameters.get("min_storage", 1024)  # MB
        self.gpu_memory_buffer = parameters.get("gpu_memory_buffer", 0.1)  # 10% buffer
        self.node_cpu_threshold = parameters.get("node_cpu_threshold", 0.8)  # 80% max utilization
        self.node_memory_threshold = parameters.get("node_memory_threshold", 0.8)  # 80% max utilization
        self.node_storage_threshold = parameters.get("node_storage_threshold", 0.8)  # 80% max utilization
        #self.max_models_per_gpu = parameters.get("max_models_per_gpu", 2)  # Max models per GPU

        self.min_threshold_gpu_mem_non_model = parameters.get("min_threshold_gpu_mem_non_model", 512)  # MB
        self.max_model_per_gpu = parameters.get("max_model_per_gpu", 2)  # Max models per GPU

        self.skip_nodes = parameters.get("skip_nodes", [])  # List of node IDs to skip

        # Helper policy integration points (will be populated by helper policies)
        self.weights = parameters.get("weights", {
            'gpu_memory': 0.4,
            'cpu': 0.3,
            'memory': 0.2,
            'storage': 0.1
        })
        
        logger.info(f"Initialized Block Resource Allocator Policy: {rule_id}")
        
    def eval(self, parameters: Dict[str, Any], input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the resource allocator policy based on the action type.
        
        Args:
            parameters (dict): Runtime parameters
            input_data (dict): Input data with action, payload
            context (dict): Context for stateful operations
            
        Returns:
            dict: Action-specific allocation result
        """
        try:
            action = input_data.get('action')
            payload = input_data.get('payload', {})
            
            logger.info(f"Processing resource allocation action: {action}")

            if action == 'third_party_allocate':
                logging.info(f"parameters={self.parameters}")

                if 'third_party_allocation_data' in self.parameters:
                    return self.parameters['third_party_allocation_data']
            elif action == "dry_run":
                return {
                        "selection_score_data": {
                            "score": 0.9,
                            "node_info": {
                                
                            }
                        }
                    }
            elif action == "allocation":
                logging.info(f"parameters={self.parameters}")

                if 'allocation_data' in self.parameters:
                    return self.parameters['allocation_data']

                res = self._handle_allocation(payload, context)
                logging.info(f"Allocation Result={res}")
                return res
            
            elif action == "scale":
                logging.info(f"parameters={self.parameters}")

                if 'allocation_data' in self.parameters:
                    return self.parameters['allocation_data']

                res = self._handle_scale(payload, context)
                logging.info(f"Scaling Result={res}")
                return res
            elif action == "reassignment":
                res = self._handle_reassignment(payload, context)
                logging.info(f"Reassignment Result={res}")
                return res
            else:
                raise ValueError(f"Unsupported action: {action}")
                
        except Exception as e:
            logger.error(f"Error in resource allocator policy: {str(e)}")
            raise e
    
    def _handle_allocation(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle allocation action: allocate resources for a new instance.

        Args:
            payload (dict): Contains block, cluster, cluster_metrics, block_metrics, 
                          healthy_nodes, instance_id, pod_name
            context (dict): Context data
            
        Returns:
            dict: New node ID and GPU IDs for allocation
        """
        logger.info("Handling Alocation resource allocation")

        block = payload.get('block', {})
        cluster = payload.get('cluster', {})
        cluster_metrics = payload.get('cluster_metrics', {})
        healthy_nodes = payload.get('healthy_nodes', [])
        
        # Extract resource requirements
        requirements = self._extract_resource_requirements(block)
        logger.info(f"Requirements of the instance: {requirements}")

        # Get available nodes (excluding current placement for Allocation)
        available_nodes = self._get_available_nodes(cluster, cluster_metrics, healthy_nodes)
        
        if not available_nodes:
            raise Exception("No suitable nodes available for Allocation")

        # Orchestrate helper policies using consensus-based decision making
        allocation_result = self._orchestrate_allocation_helpers(
            available_nodes, requirements, payload
        )
        
        if "error" in  allocation_result:
            return allocation_result

        selected_node_id = allocation_result['node_id']
        allocated_gpus = allocation_result['gpus']
        
        result = {
            "node_id": selected_node_id,
            "gpus": allocated_gpus
        }
        
        logger.info(f"Allocation completed: node={selected_node_id}, gpus={len(allocated_gpus)}")
        return result

    def _handle_scale(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle scale action: scale resources for an existing instance.

        Args:
            payload (dict): Contains block, cluster, cluster_metrics, block_metrics, 
                          healthy_nodes, instance_id, pod_name
            context (dict): Context data
            
        Returns:
            dict: New node ID and GPU IDs for allocation
        """
        logger.info("Handling Alocation resource allocation")

        block = payload.get('block', {})
        cluster = payload.get('cluster', {})
        cluster_metrics = payload.get('cluster_metrics', {})
        block_metrics = payload.get('block_metrics', [])
        healthy_nodes = payload.get('healthy_nodes', [])
        #pod_name = payload.get('pod_name')
        logger.info(f"block_metrics: {block_metrics}")
        
        # Extract resource requirements
        requirements = self._extract_resource_requirements(block)
        logger.info(f"Requirements of the instance: {requirements}")

        # Get available nodes (excluding current placement for Scaling)
        available_nodes = self._get_available_nodes(cluster, cluster_metrics, healthy_nodes)
        
        if not available_nodes:
            raise Exception("No suitable nodes available for Scaling")

        # Orchestrate helper policies using consensus-based decision making
        allocation_result = self._orchestrate_allocation_helpers(
            available_nodes, requirements, payload
        )

        if "error" in  allocation_result:
            return allocation_result
        
        selected_node_id = allocation_result['node_id']
        allocated_gpus = allocation_result['gpus']
        
        result = {
            "node_id": selected_node_id,
            "gpus": allocated_gpus
        }
        
        logger.info(f"Scaling completed: node={selected_node_id}, #gpus={len(allocated_gpus)} gpus id={allocated_gpus}")
        return result

    
    def _handle_reassignment(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle reassignment action: reallocate resources for existing instance.
        
        Args:
            payload (dict): Contains block, cluster, cluster_metrics, block_metrics, 
                          healthy_nodes, instance_id, pod_name
            context (dict): Context data
            
        Returns:
            dict: New node ID and GPU IDs for reassignment
        """
        logger.info("Handling reassignment resource allocation")

        block = payload.get('block', {})
        cluster = payload.get('cluster', {})
        cluster_metrics = payload.get('cluster_metrics', {})
        block_metrics = payload.get('block_metrics', [])
        healthy_nodes = payload.get('healthy_nodes', [])
        instance_id = payload.get('instance_id')
        pod_name = payload.get('pod_name')
        logger.info(f"block_metrics: {block_metrics}")
        logger.info(f"Reassigning instance: {instance_id}, pod: {pod_name}")
        
        # Extract resource requirements
        requirements = self._extract_resource_requirements(block)
        logger.info(f"Requirements of the instance: {requirements}")

        # Analyze current placement to avoid reassigning to same location
        current_placement = self._get_current_placement(instance_id, block_metrics)
        logger.info(f"Current placement: {current_placement}")
        
        # Get available nodes (excluding current placement for reassignment)
        all_available_nodes = self._get_available_nodes(cluster, cluster_metrics, healthy_nodes)
        
        # For reassignment, exclude current node if possible
        if current_placement and len(all_available_nodes) > 1:
            current_node_id = current_placement.get('node_id')
            available_nodes = [node for node in all_available_nodes if node['id'] != current_node_id]
            logger.info(f"Excluding current node {current_node_id} for reassignment")
        else:
            available_nodes = all_available_nodes
            logger.info("Using all available nodes (current node will be considered)")
        
        if not available_nodes:
            raise Exception("No suitable nodes available for reassignment")
        
        # Orchestrate helper policies using consensus-based decision making
        allocation_result = self._orchestrate_allocation_helpers(
            available_nodes, requirements, payload
        )

        if "error" in  allocation_result:
            return allocation_result
        
        selected_node_id = allocation_result['node_id']
        allocated_gpus = allocation_result['gpus']
        
        result = {
            "node_id": selected_node_id,
            "gpus": allocated_gpus
        }
        
        logger.info(f"Reassignment completed: node={selected_node_id}, gpus={len(allocated_gpus)}")
        return result

    def _extract_resource_requirements(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """Extract resource requirements from block data."""
        # Default requirements
        requirements = {
            "cpu": self.min_cpu_per_instance,
            "memory": self.min_memory_per_instance,
            "gpu": 1 if self.min_gpu_memory_per_instance > 0 else 0,
            "gpu_memory": self.min_gpu_memory_per_instance,
            "storage": self.min_storage
        }
        return requirements
    
    def _get_available_nodes(self, cluster: Dict[str, Any], cluster_metrics: Dict[str, Any], 
                           healthy_nodes: List[str]) -> List[Dict[str, Any]]:
        """Get list of available nodes with their resource information."""
        available_nodes = []
        
        # Extract node data from cluster
        nodes_data = cluster.get('nodes', {}).get('nodeData', [])
        
        # Get node metrics (handle both 'node_metrics' and 'node' keys)
        node_metrics_list = cluster_metrics.get('node_metrics', cluster_metrics.get('nodes', []))
        metrics_by_node = {nm.get('id'): nm for nm in node_metrics_list}
        
        logging.info(f"Total nodes in cluster: {len(nodes_data)}")
        logging.info(f"nodes_data: {nodes_data}")
        logging.info(f"Healthy nodes: {healthy_nodes}")
        logging.info(f"metrics_by_node keys: {list(metrics_by_node.keys())}")
        for node in nodes_data:
            node_id = node.get('id')
            logging.info(f"Processing node: {node_id}")

            # Only include healthy nodes
            if node_id not in healthy_nodes:
                logger.info(f"Skipping unhealthy node: {node_id}")
                continue

            if node_id in self.skip_nodes:
                logger.info(f"Skipping node as per configuration: {node_id} is in skip_nodes={self.skip_nodes}")
                continue
            
            # Get node metrics
            node_metric = metrics_by_node.get(node_id, {})
            logger.info(f"Node metrics for {node_id}: {node_metric}")
            
            # Calculate CPU information
            total_cpu = node.get('vcpus', {}).get('count', 0)
            cpu_load = node_metric.get('vcpu', {}).get('load_1m', 0.0)
            # Estimate available CPU (total - load, but ensure non-negative)
            available_cpu = max(0, total_cpu - cpu_load)
            cpu_util = cpu_load / total_cpu if total_cpu > 0 else 0.0
            
            # Calculate memory information
            total_memory = node.get('memory', 0)
            free_memory = node_metric.get('memory', {}).get('freeMem', 0)
            memory_util = node_metric.get('memory', {}).get('averageUtil', 0.0) / 100.0
            available_memory = free_memory
            
            # Calculate GPU information
            gpu_data = node.get('gpus', {})
            total_gpus = gpu_data.get('count', 0)
            gpu_info = gpu_data.get('gpus', [])
            
            # Get GPU metrics from node metrics
            gpu_metrics = node_metric.get('gpu', {})
            if not gpu_metrics:
                node_info = {
                    "id": node_id,
                    "total_cpu": total_cpu,
                    "available_cpu": available_cpu,
                    "cpu_utilization": cpu_util,
                    "total_memory": total_memory,
                    "available_memory": available_memory,
                    "memory_utilization": memory_util,
                    "total_gpus": total_gpus,
                    "gpu_info": gpu_info,
                    "gpu_metrics_individual": [],
                    "gpu_metrics": {},
                    "raw_node_data": node,
                    "raw_metrics": node_metric
                }
                
                logger.info(f"Node {node_id}: CPU={available_cpu}/{total_cpu}, Memory={available_memory}MB/{total_memory}MB, GPUs={total_gpus}")
                available_nodes.append(node_info)
                logger.info(f"Missing GPU metrics for node {node_id}")
                continue
                #raise Exception(f"Missing GPU metrics for node {node_id}")
            gpu_metrics_individual = node_metric.get('gpus', [])
            
            # If no individual GPU metrics, create based on total GPU info
            if not gpu_metrics_individual and total_gpus > 0:
                gpu_metrics_individual = []
                for i, gpu in enumerate(gpu_info):
                    gpu_memory = gpu.get('memory', 0)
                    gpu_metrics_individual.append({
                        'id': i,
                        'modelName': gpu.get('modelName', 'Unknown'),
                        'freeMem': gpu_memory,  # Assume all memory is free for testing
                        'totalMem': gpu_memory
                    })
            
            # Calculate total GPU memory metrics
            if not gpu_metrics and gpu_metrics_individual:
                total_gpu_mem = sum(gpu.get('totalMem', 0) for gpu in gpu_metrics_individual)
                free_gpu_mem = sum(gpu.get('freeMem', 0) for gpu in gpu_metrics_individual)
                gpu_metrics = {
                    'totalFreeMem': free_gpu_mem,
                    'totalMem': total_gpu_mem
                }
            
            node_info = {
                "id": node_id,
                "total_cpu": total_cpu,
                "available_cpu": available_cpu,
                "cpu_utilization": cpu_util,
                "total_memory": total_memory,
                "available_memory": available_memory,
                "memory_utilization": memory_util,
                "total_gpus": total_gpus,
                "gpu_info": gpu_info,
                "gpu_metrics_individual": gpu_metrics_individual,
                "gpu_metrics": gpu_metrics,
                "raw_node_data": node,
                "raw_metrics": node_metric
            }

            logger.info(f"Node {node_id}: CPU={available_cpu}/{total_cpu}, Memory={available_memory}MB/{total_memory}MB, GPUs={total_gpus}")
            available_nodes.append(node_info)
        
        logger.info(f"Found {len(available_nodes)} available healthy nodes")
        return available_nodes
    
    
    def _get_current_placement(self, instance_id: str, 
                             block_metrics: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get current placement info for an instance."""
        try:
            for instance in block_metrics:
                if instance.get('instanceId') == instance_id:
                    return {
                        "node_id": instance.get('nodeId'),
                        "nodeKey": instance.get('nodeKey')
                    }
            return None
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _get_current_placement at line {line_number}: {e}")
            logger.error(f"Error during _get_current_placement at line {line_number}: {e}")
            return None

    def management(self, action: str, data: dict = None) -> dict:
        """
        Management interface for the resource allocator policy.
        
        Args:
            action (str): Management action to perform
            data (dict): Optional data for the action
            
        Returns:
            dict: Management result
        """
        try:
            data = data or {}
            
            if action == "get_status":
                return {
                    "rule_id": self.rule_id,
                    "min_cpu_per_instance": self.min_cpu_per_instance,
                    "min_memory_per_instance": self.min_memory_per_instance,
                    "min_gpu_memory_per_instance": self.min_gpu_memory_per_instance,
                    "min_storage": self.min_storage,
                    "gpu_memory_buffer": self.gpu_memory_buffer,
                    "node_cpu_threshold": self.node_cpu_threshold,
                    "node_memory_threshold": self.node_memory_threshold,
                    "node_storage_threshold": self.node_storage_threshold,
                    #"max_models_per_gpu": self.max_models_per_gpu,
                    "status": "active",
                    "min_threshold_gpu_mem_non_model": self.min_threshold_gpu_mem_non_model,
                    "max_models_per_gpu": self.max_model_per_gpu,
                    "skip_nodes": self.skip_nodes
                }
            
            elif action == "update_thresholds":
                if "min_cpu_per_instance" in data:
                    self.min_cpu_per_instance = data["min_cpu_per_instance"]
                if "min_memory_per_instance" in data:
                    self.min_memory_per_instance = data["min_memory_per_instance"]
                if "min_gpu_memory_per_instance" in data:
                    self.min_gpu_memory_per_instance = data["min_gpu_memory_per_instance"]
                if "min_storage" in data:
                    self.min_storage = data["min_storage"]
                if "gpu_memory_buffer" in data:
                    self.gpu_memory_buffer = data["gpu_memory_buffer"]
                if "node_cpu_threshold" in data:
                    self.node_cpu_threshold = data["node_cpu_threshold"]
                if "node_memory_threshold" in data:
                    self.node_memory_threshold = data["node_memory_threshold"]
                if "node_storage_threshold" in data:
                    self.node_storage_threshold = data["node_storage_threshold"]
                if "weights" in data:
                    self.weights = data["weights"]
                if "max_models_per_gpu" in data:
                    self.max_models_per_gpu = data["max_models_per_gpu"]
                if "skip_nodes" in data:    
                    self.skip_nodes = data["skip_nodes"]
                if "min_threshold_gpu_mem_non_model" in data:
                    self.min_threshold_gpu_mem_non_model = data["min_threshold_gpu_mem_non_model"]

                logger.info(f"Updated thresholds: CPU={self.node_cpu_threshold}, Memory={self.node_memory_threshold}, GPU={self.min_gpu_memory_per_instance}, Storage={self.min_storage}, Max Models per GPU={self.max_models_per_gpu}")
                return {
                    "success": True,
                    "message": "Resource thresholds updated successfully"
                }
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown management action: {action}"
                }
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during management at line {line_number}: {e}")
            logger.error(f"Error during management at line {line_number}: {e}")
            return {
                "success": False,
                "error": f"Error during management at line {line_number}: {e}"
            }
    
    def _orchestrate_allocation_helpers(self, available_nodes: List[Dict[str, Any]], 
                                       requirements: Dict[str, Any],  
                                       payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate resource allocation using consensus-based scoring.
        
        This implements a multi-criteria scoring system for:
        1. GPU Memory (40% weight) - Nodes with sufficient GPU memory
        2. CPU (30% weight) - CPU availability within threshold limits
        3. Memory (20% weight) - CPU memory availability within threshold limits  
        4. Storage (10% weight) - Storage availability within threshold limits
        
        Args:
            available_nodes: List of candidate nodes with resource information
            requirements: Resource requirements dictionary
            payload: Full payload data
            
        Returns:
            dict: Allocation result with selected node and GPU IDs
        """
        try:
            logger.info("Starting consensus-based resource allocation")
            logger.info(f"Requirements: {requirements}")
            logger.info(f"Available nodes: {len(available_nodes)}")
            
            # Step 1: Filter and score nodes based on GPU memory requirements
            gpu_eligible_nodes, gpu_scores = self._score_gpu_memory(available_nodes, requirements)
            logger.info(f"GPU memory eligible nodes: {len(gpu_eligible_nodes)}")
            
            if not gpu_eligible_nodes:
                #raise Exception("No nodes have sufficient GPU memory for the requirements")
                message = "No nodes have sufficient GPU memory for the requirements"
                logger.warning(message)
                return {"error": message, "gpus": []}
            # Step 2: Filter and score nodes based on CPU memory requirements
            memory_eligible_nodes, memory_scores = self._score_cpu_memory(gpu_eligible_nodes, requirements)
            logger.info(f"CPU memory eligible nodes: {len(memory_eligible_nodes)}")
            
            if not memory_eligible_nodes:
                #raise Exception("No nodes have sufficient CPU memory within threshold limits")
                message = "No nodes have sufficient CPU memory within threshold limits"
                logger.warning(message)
                return {"error": message, "gpus": []}

            # Step 3: Filter and score nodes based on CPU requirements
            cpu_eligible_nodes, cpu_scores = self._score_cpu(memory_eligible_nodes, requirements)
            logger.info(f"CPU eligible nodes: {len(cpu_eligible_nodes)}")
            
            if not cpu_eligible_nodes:
                #raise Exception("No nodes have sufficient CPU within threshold limits")
                message = "No nodes have sufficient CPU within threshold limits"
                logger.warning(message)
                return {"error": message, "gpus": []}

            # Step 4: Filter and score nodes based on storage requirements
            storage_eligible_nodes, storage_scores = self._score_storage(cpu_eligible_nodes, requirements)
            logger.info(f"Storage eligible nodes: {len(storage_eligible_nodes)}")
            
            if not storage_eligible_nodes:
                #raise Exception("No nodes have sufficient storage within threshold limits")
                message = "No nodes have sufficient storage within threshold limits"
                logger.warning(message)
                return {"error": message, "gpus": []}

            # Step 5: Calculate composite scores with weights
            composite_scores = self._calculate_weighted_scores(
                storage_eligible_nodes, gpu_scores, memory_scores, cpu_scores, storage_scores
            )
            
            # Step 6: Select best node
            best_node = max(composite_scores, key=lambda x: x['total_score'])
            selected_node = best_node['node']
            node_id = selected_node['id']
            
            logger.info(f"Selected node: {node_id} with total score: {best_node['total_score']:.3f}")
            
            # Step 7: Allocate GPUs on selected node
            allocated_gpus = self._allocate_gpu_ids(selected_node, requirements)
            
            result = {
                "node_id": selected_node['id'],
                "gpus": allocated_gpus
            }
            
            logger.info(f"Final allocation: {result}")
            return result
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _orchestrate_allocation_helper at line {line_number}: {e}")
            logger.error(f"Error during _orchestrate_allocation_helper at line {line_number}: {e}")
            raise e

    def _score_gpu_memory(self, available_nodes: List[Dict[str, Any]], 
                     requirements: Dict[str, Any]) -> tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Score nodes based on GPU memory availability.
        First tries single GPU allocation, then tries multi-GPU pooling within the same node.
        """
        try:
            gpu_memory_required = requirements.get('gpu_memory', 0)
            gpu_required = requirements.get('gpu', 0)
            
            if gpu_required == 0 or gpu_memory_required == 0:
                # If no GPU required, all nodes get equal score
                scores = {node['id']: 1.0 for node in available_nodes}
                return available_nodes, scores
            
            eligible_nodes = []
            node_gpu_memory = {}
            node_gpu_memory_free_utilization = {}
            
            # First pass: Check for single GPU allocation
            for node in available_nodes:
                gpu_metrics = node.get('gpu_metrics', {})
                gpu_metrics_individual = node.get('gpu_metrics_individual', [])
                logger.info(f"Node {node['id']}: GPU metrics individual: {gpu_metrics_individual}")
                logger.info(f"Node {node['id']}: GPU metrics: {gpu_metrics}")
                logger.info(f"Node {node['id']}: Required GPU memory: {gpu_memory_required}MB")

                node_gpu_memory_free_utilization[node['id']] = []

                for gpu in gpu_metrics_individual:
                    #logger.info(f"Node {node['id']}: GPU {gpu.get('id', 'unknown')} free memory: {gpu.get('freeMem', 0)}MB")
                    totalMem = gpu.get("totalMem", 0)
                    freeMem = gpu.get("freeMem", 0)
                    free_utilization = freeMem / totalMem if totalMem > 0 else 0
                    node_gpu_memory_free_utilization[node['id']].append(free_utilization)

                filtered_gpus = []
                filtered_gpus_ids = []
                for gpu in gpu_metrics_individual:
                    model_count = sum(
                        1 for inst in gpu.get('instances', [])
                        if inst.get('totalUsedMem', 0) > self.min_threshold_gpu_mem_non_model
                    )
                    if model_count < self.max_model_per_gpu:
                        filtered_gpus.append(gpu)
                        filtered_gpus_ids.append(gpu.get('gpu_id', 'dummy'))
                    else:
                        logger.info(f"Skipping GPU {gpu.get('gpu_id', 'unknown')} on node {node['id']} due to max model count ({model_count})")
                    
                        

                # Check if any single GPU has enough memory
                single_gpu_sufficient = False
                for gpu in gpu_metrics_individual:
                    if gpu.get("freeMem", 0) >= gpu_memory_required and gpu.get('gpu_id', 'unknown') in filtered_gpus_ids:
                        single_gpu_sufficient = True
                        break
            
                if single_gpu_sufficient:
                    node_gpu_memory[node['id']] = gpu_metrics.get("totalFreeMem", 0)
                    # Mark this node as using single GPU allocation
                    node['allocation_strategy'] = 'single_gpu'
                    logger.info(f"Node {node['id']}: Single GPU allocation possible")
                    eligible_nodes.append(node)
            
            # If no nodes found with single GPU, try multi-GPU pooling
            if not eligible_nodes:
                logger.info("No single GPU can handle the memory requirement. Trying multi-GPU pooling...")
                
                for node in available_nodes:
                    gpu_metrics_individual = node.get('gpu_metrics_individual', [])
                    
                    if not gpu_metrics_individual:
                        continue

                    
                    # Sort GPUs by available memory (descending)
                    sorted_gpus = sorted(filtered_gpus, key=lambda x: x.get('freeMem', 0), reverse=True)
                    total_gpus = len(sorted_gpus)
                    
                    # Try pooling with 2^n up to total available GPUs
                    # Right now 2^n formula applied which is needed by any Tensor Parallelism based GPU Sharing is needed
                    pooling_successful = False
                    optimal_gpu_count = 0

                    if total_gpus >= 2:
                        # Only consider gpu_count values that are multiples of 2 and <= total_gpus+1
                        for gpu_count in range(2, total_gpus +1, 2):
                            # Calculate memory needed per GPU with buffer
                            memory_per_gpu = gpu_memory_required / gpu_count
                            memory_per_gpu_with_buffer = memory_per_gpu * (1 + self.gpu_memory_buffer)
                            logger.info(f"Node {node['id']}: Trying multi-GPU pooling with {gpu_count} GPUs "
                                         f"({memory_per_gpu_with_buffer:.1f}GB per GPU with {self.gpu_memory_buffer*100:.1f}% buffer)")
                            # Check if we have enough GPUs with required memory
                            suitable_gpus = []
                            for gpu in sorted_gpus:
                                if gpu.get('freeMem', 0) >= memory_per_gpu_with_buffer:
                                    suitable_gpus.append(gpu)
                            
                            if len(suitable_gpus) >= gpu_count:
                                pooling_successful = True
                                optimal_gpu_count = gpu_count
                                logger.info(f"Node {node['id']}: Multi-GPU pooling possible with {gpu_count} GPUs "
                                        f"({memory_per_gpu_with_buffer:.1f}GB per GPU with {self.gpu_memory_buffer*100:.1f}% buffer)")
                                break
                            else:
                                logger.info(f"Node {node['id']}: Not enough GPUs with required memory for {gpu_count} GPU pooling")
                    
                    if pooling_successful:
                        # For multi-GPU, use total available GPU memory for scoring
                        total_available_gpu_memory = sum(gpu.get('freeMem', 0) for gpu in gpu_metrics_individual)
                        node_gpu_memory[node['id']] = total_available_gpu_memory
                        # Mark this node as using multi-GPU allocation
                        node['allocation_strategy'] = 'multi_gpu'
                        node['optimal_gpu_count'] = optimal_gpu_count
                        node['memory_per_gpu_required'] = gpu_memory_required / optimal_gpu_count
                        node['memory_per_gpu_with_buffer'] = (gpu_memory_required / optimal_gpu_count) * (1 + self.gpu_memory_buffer)
                        eligible_nodes.append(node)
            if not eligible_nodes:
                logger.warning("No nodes found with sufficient GPU memory (single or multi-GPU)")
                return [], {}

            # Calculate percentage scores foreach node i.e gpu memory available in node / total gpu memory available in all eligible nodes
            total_available_gpu_memory = sum(node_gpu_memory.values())
            scores = {}
            
            for node_id, gpu_memory in node_gpu_memory.items():
                scores[node_id] = gpu_memory / total_available_gpu_memory if total_available_gpu_memory > 0 else 0
            logger.info(f"GPU memory scores with Combined RAM of ALL Node: {scores}")

            # Alternative scoring: Use product of individual GPU free memory utilizations
            # This favors nodes where all GPUs have high free memory utilization
            # Say Node1 with 1 GPU has 100% free memory utilization
            # Node2 with 2 GPUs has 50%, 50% free memory utilization
            # Node3 with 4 GPUs has 25%, 25%, 25%, 25% free memory utilization
            # Node 4 with 1 GPU has 90% free memory utilization
            # Using product scoring: Node1=1.0, Node2=0.5*0.5=0.25, Node3=0.25*0.25*0.25*0.25=0.0039, Node4=0.9
            # then normalized scores: Node1=0.526, Node2=0.131, Node3=0.002, Node4=0.342
            # This way we favor nodes where all GPUs are relatively free rather than just one GPU being free

            free_gpu_ram_util_score = {}
            for node_id, free_utils in node_gpu_memory_free_utilization.items():
                if not free_utils:
                    free_gpu_ram_util_score[node_id] = 0
                    logger.info(f"Node {node_id}: Average GPU free memory utilization: {0*100:.1f}%")
                    continue
                total_free_util_score = math.prod(free_utils)
                free_gpu_ram_util_score[node_id] = total_free_util_score
                logger.info(f"Node {node_id}: Average GPU free memory utilization: {total_free_util_score*100:.1f}%")
            sum_all_score = sum(free_gpu_ram_util_score.values())
            for node_id, util_score in free_gpu_ram_util_score.items():
                if sum_all_score > 0:
                    free_gpu_ram_util_score[node_id] = util_score / sum_all_score
                else:
                    free_gpu_ram_util_score[node_id] = 0
            logger.info(f"GPU memory scores with Individual GPUs in Node: {free_gpu_ram_util_score}")
            scores = free_gpu_ram_util_score
            logger.info(f"Final GPU memory score: {scores}")

            # Log allocation strategies
            for node in eligible_nodes:
                strategy = node.get('allocation_strategy', 'unknown')
                if strategy == 'single_gpu':
                    logger.info(f"Node {node['id']}: Single GPU allocation strategy")
                elif strategy == 'multi_gpu':
                    gpu_count = node.get('optimal_gpu_count', 0)
                    mem_per_gpu = node.get('memory_per_gpu_with_buffer', 0)
                    logger.info(f"Node {node['id']}: Multi-GPU allocation strategy ({gpu_count} GPUs, {mem_per_gpu:.1f}GB per GPU)")
            
            return eligible_nodes, scores
            
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _score_gpu_memory at line {line_number}: {e}")
            logger.error(f"Error during _score_gpu_memory at line {line_number}: {e}")
            raise e
    
    def _score_cpu_memory(self, available_nodes: List[Dict[str, Any]], 
                         requirements: Dict[str, Any]) -> tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Score nodes based on CPU memory (RAM) availability within threshold limits.
        """
        try:
            memory_required = requirements.get('memory', 0)
            #print("memory_required:",memory_required)
            eligible_nodes = []
            node_memory_available = {}
            #print("available_nodes:",available_nodes)
            for node in available_nodes:
                #print(node)
                available_memory = node.get('available_memory', 0)
                total_memory = node.get('total_memory', 0)
                #print("available_memory:",available_memory)
                #print("total_memory:",total_memory)
                # Check if adding required memory exceeds threshold
                memory_after_allocation = total_memory - (available_memory - memory_required)
                #print("memory_after_allocation:",memory_after_allocation)
                memory_utilization_after = memory_after_allocation / total_memory if total_memory > 0 else 1.0
                #print("memory_utilization_after:",memory_utilization_after)
                if available_memory >= memory_required and memory_utilization_after <= self.node_memory_threshold:
                    eligible_nodes.append(node)
                    node_memory_available[node['id']] = available_memory
                    #print("node_memory_available:",node_memory_available)
                    #print("eligible_nodes:",eligible_nodes)
            
            if not eligible_nodes:
                #print("No eligible nodes found in _score_cpu_memory")
                return [], {}
            
            # Calculate percentage scores
            total_available_memory = sum(node_memory_available.values())
            scores = {}
            
            for node_id, memory in node_memory_available.items():
                #print(node_id, memory, total_available_memory)
                scores[node_id] = memory / total_available_memory if total_available_memory > 0 else 0
                #print("scores:",scores)
            logger.info(f"CPU memory scores: {scores}")
            return eligible_nodes, scores
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _score_cpu_memory at line {line_number}: {e}")
            logger.error(f"Error during _score_cpu_memory at line {line_number}: {e}")
            raise e

    def _score_cpu(self, available_nodes: List[Dict[str, Any]], 
                  requirements: Dict[str, Any]) -> tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Score nodes based on CPU availability within threshold limits.
        """
        try:
            cpu_required = requirements.get('cpu', 0)
            eligible_nodes = []
            node_cpu_available = {}
            
            for node in available_nodes:
                available_cpu = node.get('available_cpu', 0)
                total_cpu = node.get('total_cpu', 0)
                
                # Check if we have enough CPU and won't exceed threshold
                if available_cpu >= cpu_required and total_cpu > 0:
                    cpu_utilization_after = (total_cpu - (available_cpu - cpu_required)) / total_cpu
                    
                    if cpu_utilization_after <= self.node_cpu_threshold:
                        eligible_nodes.append(node)
                        node_cpu_available[node['id']] = available_cpu
            
            if not eligible_nodes:
                return [], {}
            
            # Calculate percentage scores
            total_available_cpu = sum(node_cpu_available.values())
            scores = {}
            
            for node_id, cpu in node_cpu_available.items():
                scores[node_id] = cpu / total_available_cpu if total_available_cpu > 0 else 0
            
            logger.info(f"CPU scores: {scores}")
            return eligible_nodes, scores
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _score_cpu at line {line_number}: {e}")
            logger.error(f"Error during _score_cpu at line {line_number}: {e}")
            raise e

    def _score_storage(self, available_nodes: List[Dict[str, Any]], 
                      requirements: Dict[str, Any]) -> tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Score nodes based on storage availability within threshold limits.
        """
        try:
            storage_required = requirements.get('storage', 0)
            eligible_nodes = []
            node_storage_available = {}
            
            for node in available_nodes:
                # Get storage info from raw node data
                raw_node = node.get('raw_node_data', {})
                storage_info = raw_node.get('storage', {})
                total_storage = storage_info.get('size', 0)
                
                # For simplicity, assume available storage is total storage
                # In real implementation, this would come from metrics
                available_storage = total_storage * 0.9  # Assume 90% available
                
                # Check if we have enough storage and won't exceed threshold
                if available_storage >= storage_required and total_storage > 0:
                    storage_utilization_after = (total_storage - (available_storage - storage_required)) / total_storage
                    
                    if storage_utilization_after <= self.node_storage_threshold:
                        eligible_nodes.append(node)
                        node_storage_available[node['id']] = available_storage
            
            if not eligible_nodes:
                return [], {}
            
            # Calculate percentage scores
            total_available_storage = sum(node_storage_available.values())
            scores = {}
            
            for node_id, storage in node_storage_available.items():
                scores[node_id] = storage / total_available_storage if total_available_storage > 0 else 0
            
            logger.info(f"Storage scores: {scores}")
            return eligible_nodes, scores
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _score_storage at line {line_number}: {e}")
            logger.error(f"Error during _score_storage at line {line_number}: {e}")
            raise e
    
    def _calculate_weighted_scores(self, eligible_nodes: List[Dict[str, Any]], 
                                  gpu_scores: Dict[str, float], 
                                  memory_scores: Dict[str, float], 
                                  cpu_scores: Dict[str, float], 
                                  storage_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Calculate weighted composite scores for final node selection.
        Weights: GPU Memory (40%), CPU (30%), Memory (20%), Storage (10%)
        """
        # weights = {
        #     'gpu_memory': 0.4,
        #     'cpu': 0.3,
        #     'memory': 0.2,
        #     'storage': 0.1
        # }
        try:
            composite_scores = []
            
            for node in eligible_nodes:
                node_id = node['id']
                
                gpu_score = gpu_scores.get(node_id, 0)
                memory_score = memory_scores.get(node_id, 0)
                cpu_score = cpu_scores.get(node_id, 0)
                storage_score = storage_scores.get(node_id, 0)
                
                total_score = (
                    (gpu_score * self.weights['gpu_memory']) +
                    (cpu_score * self.weights['cpu']) +
                    (memory_score * self.weights['memory']) +
                    (storage_score * self.weights['storage'])
                )
                
                composite_scores.append({
                    'node': node,
                    'total_score': total_score,
                    'score_breakdown': {
                        'gpu_memory': gpu_score,
                        'cpu': cpu_score,
                        'memory': memory_score,
                        'storage': storage_score
                    }
                })
            
            # Sort by total score (descending)
            composite_scores.sort(key=lambda x: x['total_score'], reverse=True)
            
            logger.info("Composite scores calculated:")
            for score_data in composite_scores:
                node_id = score_data['node']['id']
                #logger.info(f"Only Top 3 nodes shown for brevity")
                logger.info(f"  {node_id}: {score_data['total_score']:.3f} {score_data['score_breakdown']}")
            
            return composite_scores
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _calculate_weighted_scores at line {line_number}: {e}")
            logger.error(f"Error during _calculate_weighted_scores at line {line_number}: {e}")
            raise e
    def _allocate_gpu_ids(self, selected_node: Dict[str, Any], requirements: Dict[str, Any]) -> List[int]:
        """
        Allocate specific GPU IDs from the selected node.
        Handles both single GPU and multi-GPU pooling strategies.
        """
        try:
            gpu_required = requirements.get('gpu', 0)
            gpu_memory_required = requirements.get('gpu_memory', 0)
            
            if gpu_required == 0:
                return []

            gpu_metrics_individual = selected_node.get('gpu_metrics_individual', [])
            # Filter GPUs based on model count
            filtered_gpus = []
            for gpu in gpu_metrics_individual:
                model_count = sum(
                    1 for inst in gpu.get('instances', [])
                    if inst.get('totalUsedMem', 0) > self.min_threshold_gpu_mem_non_model
                )
                if model_count < self.max_model_per_gpu:
                    filtered_gpus.append(gpu)
                else:
                    logger.info(f"Skipping GPU {gpu.get('gpu_id', 'unknown')} on node {selected_node['id']} due to max model count ({model_count})")
            # Use filtered_gpus for allocation
            allocation_strategy = selected_node.get('allocation_strategy', 'single_gpu')
            if allocation_strategy == 'single_gpu':
                sorted_list = sorted(filtered_gpus, key=lambda item: item['freeMem'], reverse=True)
                for gpu in sorted_list:
                    if gpu.get('freeMem', 0) >= gpu_memory_required:
                        original_index = gpu_metrics_individual.index(gpu)
                        logger.info(f"Allocated single GPU ID (filtered): {original_index}")
                        return [original_index]
            elif allocation_strategy == 'multi_gpu':
                # Multi-GPU allocation
                optimal_gpu_count = selected_node.get('optimal_gpu_count', 2)
                memory_per_gpu_with_buffer = selected_node.get('memory_per_gpu_with_buffer', 0)
                sorted_gpus = sorted(enumerate(filtered_gpus), key=lambda x: x[1].get('freeMem', 0), reverse=True)
                allocated_gpu_ids = []
                for i, gpu in sorted_gpus:
                    if gpu.get('freeMem', 0) >= memory_per_gpu_with_buffer:
                        # Find original index
                        original_index = gpu_metrics_individual.index(gpu)
                        allocated_gpu_ids.append(original_index)
                        if len(allocated_gpu_ids) >= optimal_gpu_count:
                            break
                logger.info(f"Allocated multi-GPU IDs (filtered): {allocated_gpu_ids} ({len(allocated_gpu_ids)} GPUs for pooling)")
                return allocated_gpu_ids
            
            # If we reach here, something went wrong
            logger.error("No suitable GPU allocation found")
            return []
        
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _allocate_gpu_ids at line {line_number}: {e}")
            logger.error(f"Error during _allocate_gpu_ids at line {line_number}: {e}")
            raise e




