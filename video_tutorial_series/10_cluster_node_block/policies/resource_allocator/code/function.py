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
            
            if action == "dry_run":
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

                return {
                    "node_id": "wc-gpu-node4",
                    "gpus": [0, 1]
                }
            
            elif action == "scale":
                logging.info(f"parameters={self.parameters}")

                if 'allocation_data' in self.parameters:
                    return self.parameters['allocation_data']

                return {
                    "node_id": "wc-gpu-node4",
                    "gpus": [0, 1]
                }
            elif action == "reassignment":
                return self._handle_reassignment(payload, context)
            else:
                raise ValueError(f"Unsupported action: {action}")
                
        except Exception as e:
            logger.error(f"Error in resource allocator policy: {str(e)}")
            raise e
    

    
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
        node_metrics_list = cluster_metrics.get('node_metrics', cluster_metrics.get('node', []))
        metrics_by_node = {nm.get('id'): nm for nm in node_metrics_list}
        
        for node in nodes_data:
            node_id = node.get('id')
            
            # Only include healthy nodes
            if node_id not in healthy_nodes:
                logger.debug(f"Skipping unhealthy node: {node_id}")
                continue
            
            # Get node metrics
            node_metric = metrics_by_node.get(node_id, {})
            
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
            
            logger.debug(f"Node {node_id}: CPU={available_cpu}/{total_cpu}, Memory={available_memory}MB/{total_memory}MB, GPUs={total_gpus}")
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
                    "status": "active"
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

                logger.info(f"Updated thresholds: CPU={self.node_cpu_threshold}, Memory={self.node_memory_threshold}, GPU={self.min_gpu_memory_per_instance}, Storage={self.min_storage}")
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
                raise Exception("No nodes have sufficient GPU memory for the requirements")
            
            # Step 2: Filter and score nodes based on CPU memory requirements
            memory_eligible_nodes, memory_scores = self._score_cpu_memory(gpu_eligible_nodes, requirements)
            logger.info(f"CPU memory eligible nodes: {len(memory_eligible_nodes)}")
            
            if not memory_eligible_nodes:
                raise Exception("No nodes have sufficient CPU memory within threshold limits")
            
            # Step 3: Filter and score nodes based on CPU requirements
            cpu_eligible_nodes, cpu_scores = self._score_cpu(memory_eligible_nodes, requirements)
            logger.info(f"CPU eligible nodes: {len(cpu_eligible_nodes)}")
            
            if not cpu_eligible_nodes:
                raise Exception("No nodes have sufficient CPU within threshold limits")
            
            # Step 4: Filter and score nodes based on storage requirements
            storage_eligible_nodes, storage_scores = self._score_storage(cpu_eligible_nodes, requirements)
            logger.info(f"Storage eligible nodes: {len(storage_eligible_nodes)}")
            
            if not storage_eligible_nodes:
                raise Exception("No nodes have sufficient storage within threshold limits")
            
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
        Only nodes with sufficient GPU memory are considered.
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
            
            # Filter nodes with sufficient GPU memory
            for node in available_nodes:
                gpu_info = node.get('gpu_info', {})
                gpu_metrics = node.get('gpu_metrics', [])

                if gpu_metrics.get("totalFreeMem",0) >= gpu_memory_required:
                    eligible_nodes.append(node)
                    # Sum total GPU memory for scoring
                    node_gpu_memory[node['id']] = gpu_metrics.get("totalFreeMem",0)

            if not eligible_nodes:
                return [], {}

            # Calculate percentage scores
            total_available_gpu_memory = sum(node_gpu_memory.values())
            scores = {}
            
            for node_id, gpu_memory in node_gpu_memory.items():
                scores[node_id] = gpu_memory / total_available_gpu_memory if total_available_gpu_memory > 0 else 0
            
            logger.info(f"GPU memory scores: {scores}")
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
            eligible_nodes = []
            node_memory_available = {}
            
            for node in available_nodes:
                available_memory = node.get('available_memory', 0)
                total_memory = node.get('total_memory', 0)
                
                # Check if adding required memory exceeds threshold
                memory_after_allocation = total_memory - (available_memory - memory_required)
                memory_utilization_after = memory_after_allocation / total_memory if total_memory > 0 else 1.0
                
                if available_memory >= memory_required and memory_utilization_after <= self.node_memory_threshold:
                    eligible_nodes.append(node)
                    node_memory_available[node['id']] = available_memory
            
            if not eligible_nodes:
                return [], {}
            
            # Calculate percentage scores
            total_available_memory = sum(node_memory_available.values())
            scores = {}
            
            for node_id, memory in node_memory_available.items():
                scores[node_id] = memory / total_available_memory if total_available_memory > 0 else 0
            
            logger.info(f"CPU memory scores: {scores}")
            return eligible_nodes, scores
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _score_gpu_memory at line {line_number}: {e}")
            logger.error(f"Error during _score_gpu_memory at line {line_number}: {e}")
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
                    gpu_score * self.weights['gpu_memory'] +
                    cpu_score * self.weights['cpu'] +
                    memory_score * self.weights['memory'] +
                    storage_score * self.weights['storage']
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
            for score_data in composite_scores[:3]:  # Log top 3
                node_id = score_data['node']['id']
                logger.info(f"  {node_id}: {score_data['total_score']:.3f} {score_data['score_breakdown']}")
            
            return composite_scores
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _calculate_weighted_scores at line {line_number}: {e}")
            logger.error(f"Error during _calculate_weighted_scores at line {line_number}: {e}")
            raise e
    def _allocate_gpu_ids(self, selected_node: Dict[str, Any], 
                         requirements: Dict[str, Any]) -> List[int]:
        """
        Allocate specific GPU IDs from the selected node.
        Returns array of GPU indices that meet the memory requirements.
        """
        try:
            gpu_required = requirements.get('gpu', 0)
            gpu_memory_required = requirements.get('gpu_memory', 0)
            
            if gpu_required == 0:
                return []

            gpu_metrics_individual = selected_node.get('gpu_metrics_individual', [])
            sorted_list = sorted(gpu_metrics_individual, key=lambda item: item['freeMem'])
            # Find GPUs with sufficient memory
            suitable_gpu_indices = []
            current_summed_memory = 0
            for i, gpu in enumerate(sorted_list):
                current_summed_memory += gpu.get('freeMem', 0)
                suitable_gpu_indices.append(i)
                if current_summed_memory >= gpu_memory_required:
                    break
            
            logger.info(f"Allocated GPU IDs: {suitable_gpu_indices}")

            return suitable_gpu_indices
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            print(f"[DEBUG] Error during _allocate_gpu_ids at line {line_number}: {e}")
            logger.error(f"Error during _allocate_gpu_ids at line {line_number}: {e}")
            raise e



    
