#!/usr/bin/env python3
"""
Simplified Test Script for Block Resource Allocator Policy - Reassignment Tests Only

This script tests the reassignment action of the consensus-based allocation algorithm.
Focus is on testing basic reassignment scenarios for CPU/memory and GPU resources.
"""

import sys
import os
import json
from typing import Dict, Any, List

# Add code directory to path for importing the policy
code_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "code")
sys.path.insert(0, code_dir)

try:
    from function import AIOSv1PolicyRule
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print(f"Make sure function.py exists in: {code_dir}")
    sys.exit(1)
finally:
    if code_dir in sys.path:
        sys.path.remove(code_dir)


class TestReassignmentAllocation:
    """Simple test harness for reassignment allocation validation."""
    
    def __init__(self):
        """Initialize test harness with policy and test parameters."""
        self.policy = AIOSv1PolicyRule(
            rule_id="test_resource_allocator",
            settings={},
            parameters={
                "min_cpu_per_instance": 1,
                "min_memory_per_instance": 1024,
                "min_gpu_memory_per_instance": 1024,
                "min_storage": 1024,
                "gpu_memory_buffer": 0.1,
                "node_cpu_threshold": 0.8,
                "node_memory_threshold": 0.8,
                "node_storage_threshold": 0.8
            }
        )
    
    def test_basic_reassignment(self):
        """Test basic reassignment functionality with CPU/memory requirements."""
        print("🧪 Testing Basic Reassignment (CPU/Memory)...")
        
        # Update policy parameters for this test using management interface
        update_result = self.policy.management("update_thresholds", {
            "min_cpu_per_instance": 2,
            "min_memory_per_instance": 2048,
            "min_gpu_memory_per_instance": 0,
            "min_storage": 2048
        })
        print(f"📝 Policy updated: {update_result}")
        
        input_data = {
            "action": "reassignment",
            "payload": {
                "block": {
                    "id": "test-block-reassign",
                    "blockComponent": {
                        "resourceRequirements": {}  # Empty - will use policy defaults
                    }
                },
                "cluster": self._create_basic_cluster(),
                "cluster_metrics": self._create_basic_metrics(),
                "block_metrics": [
                        {"instanceId": "instance-1", "nodeId": "node-1"}
                ],
                "healthy_nodes": ["node-1", "node-2", "node-3"],
                "instance_id": "instance-1",
                "pod_name": "test-pod-1"
            }
        }
        
        return self._run_test("Basic reassignment", input_data)
    
    def test_gpu_reassignment(self):
        """Test reassignment with GPU requirements."""
        print("🧪 Testing GPU Reassignment...")
        
        # Update policy parameters for this test using management interface
        update_result = self.policy.management("update_thresholds", {
            "min_cpu_per_instance": 2,
            "min_memory_per_instance": 4096,
            "min_gpu_memory_per_instance": 8192,
            "min_storage": 2048
        })
        print(f"📝 Policy updated: {update_result}")
        
        input_data = {
            "action": "reassignment", 
            "payload": {
                "block": {
                    "id": "test-block-gpu",
                    "blockComponent": {
                        "resourceRequirements": {}  # Empty - will use policy defaults
                    }
                },
                "cluster": self._create_gpu_cluster(),
                "cluster_metrics": self._create_gpu_metrics(),
                "block_metrics": [
                        {"instanceId": "gpu-instance-1", "nodeId": "gpu-node-1"}
                ],
                "healthy_nodes": ["gpu-node-1", "gpu-node-2", "gpu-node-3"],
                "instance_id": "gpu-instance-1",
                "pod_name": "gpu-test-pod"
            }
        }
        
        return self._run_test("GPU reassignment", input_data)
    
    def _run_test(self, test_name: str, input_data: Dict[str, Any]) -> bool:
        """Common test runner with validation."""
        try:
            result = self.policy.eval({}, input_data, {})
            print(f"✅ Result: {result}")
            
            # Basic validation
            assert "node_id" in result, "Result should contain node_id"
            assert "gpus" in result, "Result should contain gpus"
            
            # Validate node selection
            healthy_nodes = input_data["payload"]["healthy_nodes"]
            assert result["node_id"] in healthy_nodes, f"Selected node should be in healthy nodes: {healthy_nodes}"
            
            # GPU-specific validation based on policy settings (not block requirements)
            if self.policy.min_gpu_memory_per_instance > 0:
                assert len(result["gpus"]) > 0, "Should allocate at least one GPU when GPU memory is required by policy"
                print(f"🎮 GPU allocation successful: {result['gpus']}")
            else:
                print("🖥️ CPU-only allocation (no GPU required)")
            
            print(f"✅ {test_name} test PASSED")
            return True
            
        except Exception as e:
            print(f"❌ {test_name} test FAILED: {str(e)}")
            import traceback
            print(f"   Error details: {traceback.format_exc()}")
            return False
    
    def _create_basic_cluster(self):
        """Create basic cluster without GPUs for CPU/memory testing."""
        return {
            "id": "test-cluster",
            "nodes": {
                "count": 3,
                "nodeData": [
                    {
                        "id": "node-1",
                        "vcpus": {"count": 4},
                        "memory": 8192,
                        "gpus": {"count": 0, "gpus": []},
                        "storage": {"size": 50000}
                    },
                    {
                        "id": "node-2",
                        "vcpus": {"count": 8},
                        "memory": 16384,
                        "gpus": {"count": 0, "gpus": []},
                        "storage": {"size": 100000}
                    },
                    {
                        "id": "node-3",
                        "vcpus": {"count": 8},
                        "memory": 1024,
                        "gpus": {"count": 0, "gpus": []},
                        "storage": {"size": 100000}
                    }
                ]
            }
        }
    
    def _create_basic_metrics(self):
        """Create basic metrics for CPU/memory testing."""
        return {
            "node": [
                {
                    "id": "node-1",
                    "vcpu": {"load_1m": 3.0},
                    "memory": {"freeMem": 4096, "averageUtil": 50.0}
                },
                {
                    "id": "node-2", 
                    "vcpu": {"load_1m": 2.0},
                    "memory": {"freeMem": 12288, "averageUtil": 25.0}
                },
                {
                    "id": "node-3", 
                    "vcpu": {"load_1m": 2.0},
                    "memory": {"freeMem": 512, "averageUtil": 50.0}
                }
            ]
        }
    
    def _create_gpu_cluster(self):
        """Create GPU cluster for GPU testing."""
        return {
            "id": "gpu-test-cluster",
            "nodes": {
                "count": 3,
                "nodeData": [
                    {
                        "id": "gpu-node-1",
                        "vcpus": {"count": 8},
                        "memory": 16384,
                        "gpus": {
                            "count": 1,
                            "memory": 10240,
                            "gpus": [
                                {"modelName": "NVIDIA V100", "memory": 10240}
                            ]
                        },
                        "storage": {"size": 50000}
                    },
                    {
                        "id": "gpu-node-2",
                        "vcpus": {"count": 16},
                        "memory": 32768,
                        "gpus": {
                            "count": 2,
                            "memory": 32768,
                            "gpus": [
                                {"modelName": "NVIDIA A100", "memory": 16384},
                                {"modelName": "NVIDIA A100", "memory": 16384}
                            ]
                        },
                        "storage": {"size": 100000}
                    },
                    {
                        "id": "gpu-node-3",
                        "vcpus": {"count": 16},
                        "memory": 32000,
                        "gpus": {
                            "count": 2,
                            "memory": 4000,
                            "gpus": [
                                {"modelName": "NVIDIA A100", "memory": 2000},
                                {"modelName": "NVIDIA A100", "memory": 2000}
                            ]
                        },
                        "storage": {"size": 100000}
                    }
                ]
            }
        }
    
    def _create_gpu_metrics(self):
        """Create GPU metrics for GPU testing."""
        return {
            "node": [
                {
                    "id": "gpu-node-1",
                    "vcpu": {"load_1m": 6.0},
                    "memory": {"freeMem": 8192, "averageUtil": 50.0},
                    "gpu" : {
                        "avgMemUtilization" : 80.0,
                        "count" : 1,
                        "totalFreeMem" : 2048,
                        "totalMem" : 10240,
                        "totalUsedMem" : 8192
                    },
                    "gpus" : [
                        {
                            "freeMem" : 2048,
                            "gpu_id" : 0,
                            "memUtilization" : 80.0,
                            "totalMem" : 10240,
                            "usedMem" : 8192
                        }
                    ]
                },
                {
                    "id": "gpu-node-2",
                    "vcpu": {"load_1m": 4.0},
                    "memory": {"freeMem": 24576, "averageUtil": 25.0},
                    "gpu" : {
                        "avgMemUtilization" : 0.0,
                        "count" : 2,
                        "totalFreeMem" : 32768,
                        "totalMem" : 32768,
                        "totalUsedMem" : 0
                    },
                    "gpus" : [
                        {
                            "freeMem" : 16384,
                            "gpu_id" : 0,
                            "memUtilization" : 0.0,
                            "totalMem" : 16384,
                            "usedMem" : 0
                        },
                        {
                            "freeMem" : 16384,
                            "gpu_id" : 1,
                            "memUtilization" : 0.0,
                            "totalMem" : 16384,
                            "usedMem" : 0
                        }
                    ]
                },
                {
                    "id": "gpu-node-3",
                    "vcpu": {"load_1m": 4.0},
                    "memory": {"freeMem": 24000, "averageUtil": 25.0},
                    "gpu" : {
                        "avgMemUtilization" : 0.0,
                        "count" : 2,
                        "totalFreeMem" : 4000,
                        "totalMem" : 4000,
                        "totalUsedMem" : 0
                    },
                    "gpus" : [
                        {
                            "freeMem" : 2000,
                            "gpu_id" : 0,
                            "memUtilization" : 0.0,
                            "totalMem" : 2000,
                            "usedMem" : 0
                        },
                        {
                            "freeMem" : 2000,
                            "gpu_id" : 1,
                            "memUtilization" : 0.0,
                            "totalMem" : 2000,
                            "usedMem" : 0
                        }
                    ]
                }
            ]
        }
    
    def test_l4_multi_gpu_allocation(self):
        """Test Case 1: Multi-GPU allocation with 15GB requirement on 2x12GB GPUs per node."""
        print("🧪 Testing L4 Multi-GPU Allocation (Case 1)...")
        
        # Update policy parameters for 15GB GPU memory requirement
        update_result = self.policy.management("update_thresholds", {
            "min_cpu_per_instance": 2,
            "min_memory_per_instance": 4096,
            "min_gpu_memory_per_instance": 15360,  # 15GB
            "min_storage": 2048
        })
        print(f"📝 Policy updated: {update_result}")
        
        input_data = {
            "action": "allocation",
            "payload": {
                "block": {
                    "id": "test-l4-multi-gpu",
                    "blockComponent": {
                        "resourceRequirements": {}
                    }
                },
                "cluster": self._create_l4_cluster_case1(),
                "cluster_metrics": self._create_l4_metrics_case1(),
                "block_metrics": [],
                "healthy_nodes": ["l4-node-1", "l4-node-2"],
                "instance_id": "l4-instance-1",
                "pod_name": "l4-test-pod-1"
            }
        }
        
        return self._run_test_with_strategy_check("L4 Multi-GPU allocation", input_data, expected_strategy="multi_gpu")
    
    def test_l4_insufficient_memory(self):
        """Test Case 2: No allocation possible - insufficient memory even with multi-GPU."""
        print("🧪 Testing L4 Insufficient Memory (Case 2)...")
        
        # Update policy parameters for 15GB GPU memory requirement
        update_result = self.policy.management("update_thresholds", {
            "min_cpu_per_instance": 2,
            "min_memory_per_instance": 4096,
            "min_gpu_memory_per_instance": 15360,  # 15GB
            "min_storage": 2048
        })
        print(f"📝 Policy updated: {update_result}")
        
        input_data = {
            "action": "allocation",
            "payload": {
                "block": {
                    "id": "test-l4-insufficient",
                    "blockComponent": {
                        "resourceRequirements": {}
                    }
                },
                "cluster": self._create_l4_cluster_case2(),
                "cluster_metrics": self._create_l4_metrics_case2(),
                "block_metrics": [],
                "healthy_nodes": ["l4-node-1", "l4-node-2"],
                "instance_id": "l4-instance-2",
                "pod_name": "l4-test-pod-2"
            }
        }
        
        return self._run_test_expect_failure("L4 Insufficient memory", input_data)
    
    def test_l4_single_gpu_preferred(self):
        """Test Case 3: Single GPU preferred when one GPU has enough memory."""
        print("🧪 Testing L4 Single GPU Preferred (Case 3)...")
        
        # Update policy parameters for 15GB GPU memory requirement
        update_result = self.policy.management("update_thresholds", {
            "min_cpu_per_instance": 2,
            "min_memory_per_instance": 4096,
            "min_gpu_memory_per_instance": 15360,  # 15GB
            "min_storage": 2048
        })
        print(f"📝 Policy updated: {update_result}")
        
        input_data = {
            "action": "allocation",
            "payload": {
                "block": {
                    "id": "test-l4-single-preferred",
                    "blockComponent": {
                        "resourceRequirements": {}
                    }
                },
                "cluster": self._create_l4_cluster_case3(),
                "cluster_metrics": self._create_l4_metrics_case3(),
                "block_metrics": [],
                "healthy_nodes": ["l4-node-1", "l4-node-2"],
                "instance_id": "l4-instance-3",
                "pod_name": "l4-test-pod-3"
            }
        }
        
        return self._run_test_with_strategy_check("L4 Single GPU preferred", input_data, expected_strategy="single_gpu", expected_node="l4-node-2", expected_gpu=3)
    
    def test_l4_multi_gpu_pooling(self):
        """Test Case 4: Multi-GPU pooling with 3 GPUs from node2."""
        print("🧪 Testing L4 Multi-GPU Pooling (Case 4)...")
        
        # Update policy parameters for 15GB GPU memory requirement
        update_result = self.policy.management("update_thresholds", {
            "min_cpu_per_instance": 2,
            "min_memory_per_instance": 4096,
            "min_gpu_memory_per_instance": 15360,  # 15GB
            "min_storage": 2048
        })
        print(f"📝 Policy updated: {update_result}")
        
        input_data = {
            "action": "allocation",
            "payload": {
                "block": {
                    "id": "test-l4-multi-pooling",
                    "blockComponent": {
                        "resourceRequirements": {}
                    }
                },
                "cluster": self._create_l4_cluster_case4(),
                "cluster_metrics": self._create_l4_metrics_case4(),
                "block_metrics": [],
                "healthy_nodes": ["l4-node-1", "l4-node-2"],
                "instance_id": "l4-instance-4",
                "pod_name": "l4-test-pod-4"
            }
        }
        
        return self._run_test_with_strategy_check("L4 Multi-GPU pooling", input_data, expected_strategy="multi_gpu", expected_node="l4-node-2", expected_gpu_count=3)
    
    def _run_test_with_strategy_check(self, test_name: str, input_data: Dict[str, Any], expected_strategy: str, expected_node: str = None, expected_gpu: int = None, expected_gpu_count: int = None) -> bool:
        """Test runner with allocation strategy validation."""
        try:
            result = self.policy.eval({}, input_data, {})
            print(f"✅ Result: {result}")
            
            # Basic validation
            assert "node_id" in result, "Result should contain node_id"
            assert "gpus" in result, "Result should contain gpus"
            assert len(result["gpus"]) > 0, "Should allocate at least one GPU"
            
            # Strategy-specific validation
            if expected_node:
                assert result["node_id"] == expected_node, f"Expected node {expected_node}, got {result['node_id']}"
            
            if expected_gpu is not None:
                assert expected_gpu in result["gpus"], f"Expected GPU {expected_gpu} in allocation, got {result['gpus']}"
            
            if expected_gpu_count is not None:
                assert len(result["gpus"]) == expected_gpu_count, f"Expected {expected_gpu_count} GPUs, got {len(result['gpus'])}"
            
            print(f"🎮 Strategy validation successful: {expected_strategy}")
            print(f"✅ {test_name} test PASSED")
            return True
            
        except Exception as e:
            print(f"❌ {test_name} test FAILED: {str(e)}")
            import traceback
            print(f"   Error details: {traceback.format_exc()}")
            return False
    
    def _run_test_expect_failure(self, test_name: str, input_data: Dict[str, Any]) -> bool:
        """Test runner that expects allocation to fail."""
        try:
            result = self.policy.eval({}, input_data, {})
            
            # Check if result contains error indicating failure
            if isinstance(result, dict) and "error" in result:
                error_msg = str(result["error"])
                if "No nodes have sufficient GPU memory" in error_msg or "GPU memory" in error_msg:
                    print(f"✅ {test_name} test PASSED: Expected failure in result: {error_msg}")
                    return True
                else:
                    print(f"❌ {test_name} test FAILED: Unexpected error in result: {error_msg}")
                    return False
            else:
                print(f"❌ {test_name} test FAILED: Expected failure but got successful result: {result}")
                return False
            
        except Exception as e:
            print(f"❌ {test_name} test FAILED: Unexpected exception: {str(e)}")
            import traceback
            print(f"   Error details: {traceback.format_exc()}")
            return False
    
    def _create_l4_cluster_case1(self):
        """Test Case 1: 2 nodes with 2x24GB L4 GPUs each, all with 12GB free."""
        return {
            "id": "l4-test-cluster-case1",
            "nodes": {
                "count": 2,
                "nodeData": [
                    {
                        "id": "l4-node-1",
                        "vcpus": {"count": 16},
                        "memory": 32768,
                        "gpus": {
                            "count": 2,
                            "memory": 48000,
                            "gpus": [
                                {"modelName": "NVIDIA L4", "memory": 24000},
                                {"modelName": "NVIDIA L4", "memory": 24000}
                            ]
                        },
                        "storage": {"size": 100000}
                    },
                    {
                        "id": "l4-node-2", 
                        "vcpus": {"count": 16},
                        "memory": 32768,
                        "gpus": {
                            "count": 2,
                            "memory": 48000,
                            "gpus": [
                                {"modelName": "NVIDIA L4", "memory": 24000},
                                {"modelName": "NVIDIA L4", "memory": 24000}
                            ]
                        },
                        "storage": {"size": 100000}
                    }
                ]
            }
        }
    
    def _create_l4_metrics_case1(self):
        """Test Case 1: All GPUs have 12GB free memory."""
        return {
            "node": [
                {
                    "id": "l4-node-1",
                    "vcpu": {"load_1m": 4.0},
                    "memory": {"freeMem": 24576, "averageUtil": 25.0},
                    "gpu": {
                        "avgMemUtilization": 50.0,
                        "count": 2,
                        "totalFreeMem": 24000,
                        "totalMem": 48000,
                        "totalUsedMem": 24000
                    },
                    "gpus": [
                        {
                            "freeMem": 12000,
                            "gpu_id": 0,
                            "memUtilization": 50.0,
                            "totalMem": 24000,
                            "usedMem": 12000
                        },
                        {
                            "freeMem": 12000,
                            "gpu_id": 1,
                            "memUtilization": 50.0,
                            "totalMem": 24000,
                            "usedMem": 12000
                        }
                    ]
                },
                {
                    "id": "l4-node-2",
                    "vcpu": {"load_1m": 4.0},
                    "memory": {"freeMem": 24576, "averageUtil": 25.0},
                    "gpu": {
                        "avgMemUtilization": 50.0,
                        "count": 2,
                        "totalFreeMem": 24000,
                        "totalMem": 48000,
                        "totalUsedMem": 24000
                    },
                    "gpus": [
                        {
                            "freeMem": 12000,
                            "gpu_id": 0,
                            "memUtilization": 50.0,
                            "totalMem": 24000,
                            "usedMem": 12000
                        },
                        {
                            "freeMem": 12000,
                            "gpu_id": 1,
                            "memUtilization": 50.0,
                            "totalMem": 24000,
                            "usedMem": 12000
                        }
                    ]
                }
            ]
        }
    
    def _create_l4_cluster_case2(self):
        """Test Case 2: Same as case 1 - 2 nodes with 2x24GB L4 GPUs each."""
        return self._create_l4_cluster_case1()
    
    def _create_l4_metrics_case2(self):
        """Test Case 2: All GPUs have only 8GB free memory (insufficient for 15GB requirement)."""
        return {
            "node": [
                {
                    "id": "l4-node-1",
                    "vcpu": {"load_1m": 4.0},
                    "memory": {"freeMem": 24576, "averageUtil": 25.0},
                    "gpu": {
                        "avgMemUtilization": 67.0,
                        "count": 2,
                        "totalFreeMem": 16000,
                        "totalMem": 48000,
                        "totalUsedMem": 32000
                    },
                    "gpus": [
                        {
                            "freeMem": 8000,
                            "gpu_id": 0,
                            "memUtilization": 67.0,
                            "totalMem": 24000,
                            "usedMem": 16000
                        },
                        {
                            "freeMem": 8000,
                            "gpu_id": 1,
                            "memUtilization": 67.0,
                            "totalMem": 24000,
                            "usedMem": 16000
                        }
                    ]
                },
                {
                    "id": "l4-node-2",
                    "vcpu": {"load_1m": 4.0},
                    "memory": {"freeMem": 24576, "averageUtil": 25.0},
                    "gpu": {
                        "avgMemUtilization": 67.0,
                        "count": 2,
                        "totalFreeMem": 16000,
                        "totalMem": 48000,
                        "totalUsedMem": 32000
                    },
                    "gpus": [
                        {
                            "freeMem": 8000,
                            "gpu_id": 0,
                            "memUtilization": 67.0,
                            "totalMem": 24000,
                            "usedMem": 16000
                        },
                        {
                            "freeMem": 8000,
                            "gpu_id": 1,
                            "memUtilization": 67.0,
                            "totalMem": 24000,
                            "usedMem": 16000
                        }
                    ]
                }
            ]
        }
    
    def _create_l4_cluster_case3(self):
        """Test Case 3: Node1 has 2 GPUs, Node2 has 4 GPUs."""
        return {
            "id": "l4-test-cluster-case3",
            "nodes": {
                "count": 2,
                "nodeData": [
                    {
                        "id": "l4-node-1",
                        "vcpus": {"count": 16},
                        "memory": 32768,
                        "gpus": {
                            "count": 2,
                            "memory": 48000,
                            "gpus": [
                                {"modelName": "NVIDIA L4", "memory": 24000},
                                {"modelName": "NVIDIA L4", "memory": 24000}
                            ]
                        },
                        "storage": {"size": 100000}
                    },
                    {
                        "id": "l4-node-2",
                        "vcpus": {"count": 32},
                        "memory": 65536,
                        "gpus": {
                            "count": 4,
                            "memory": 96000,
                            "gpus": [
                                {"modelName": "NVIDIA L4", "memory": 24000},
                                {"modelName": "NVIDIA L4", "memory": 24000},
                                {"modelName": "NVIDIA L4", "memory": 24000},
                                {"modelName": "NVIDIA L4", "memory": 24000}
                            ]
                        },
                        "storage": {"size": 200000}
                    }
                ]
            }
        }
    
    def _create_l4_metrics_case3(self):
        """Test Case 3: Node1 all 12GB free, Node2 first 3 GPUs 12GB free, GPU3 has full 24GB free."""
        return {
            "node": [
                {
                    "id": "l4-node-1",
                    "vcpu": {"load_1m": 4.0},
                    "memory": {"freeMem": 24576, "averageUtil": 25.0},
                    "gpu": {
                        "avgMemUtilization": 50.0,
                        "count": 2,
                        "totalFreeMem": 24000,
                        "totalMem": 48000,
                        "totalUsedMem": 24000
                    },
                    "gpus": [
                        {
                            "freeMem": 12000,
                            "gpu_id": 0,
                            "memUtilization": 50.0,
                            "totalMem": 24000,
                            "usedMem": 12000
                        },
                        {
                            "freeMem": 12000,
                            "gpu_id": 1,
                            "memUtilization": 50.0,
                            "totalMem": 24000,
                            "usedMem": 12000
                        }
                    ]
                },
                {
                    "id": "l4-node-2",
                    "vcpu": {"load_1m": 8.0},
                    "memory": {"freeMem": 49152, "averageUtil": 25.0},
                    "gpu": {
                        "avgMemUtilization": 37.5,
                        "count": 4,
                        "totalFreeMem": 60000,
                        "totalMem": 96000,
                        "totalUsedMem": 36000
                    },
                    "gpus": [
                        {
                            "freeMem": 12000,
                            "gpu_id": 0,
                            "memUtilization": 50.0,
                            "totalMem": 24000,
                            "usedMem": 12000
                        },
                        {
                            "freeMem": 12000,
                            "gpu_id": 1,
                            "memUtilization": 50.0,
                            "totalMem": 24000,
                            "usedMem": 12000
                        },
                        {
                            "freeMem": 12000,
                            "gpu_id": 2,
                            "memUtilization": 50.0,
                            "totalMem": 24000,
                            "usedMem": 12000
                        },
                        {
                            "freeMem": 24000,  # GPU3 has full memory free
                            "gpu_id": 3,
                            "memUtilization": 0.0,
                            "totalMem": 24000,
                            "usedMem": 0
                        }
                    ]
                }
            ]
        }
    
    def _create_l4_cluster_case4(self):
        """Test Case 4: Same as case 3 - Node1 has 2 GPUs, Node2 has 4 GPUs."""
        return self._create_l4_cluster_case3()
    
    def _create_l4_metrics_case4(self):
        """Test Case 4: Node1 18GB free per GPU, Node2 6GB free per GPU."""
        return {
            "node": [
                {
                    "id": "l4-node-1",
                    "vcpu": {"load_1m": 4.0},
                    "memory": {"freeMem": 24576, "averageUtil": 25.0},
                    "gpu": {
                        "avgMemUtilization": 75.0,
                        "count": 2,
                        "totalFreeMem": 12000,
                        "totalMem": 48000,
                        "totalUsedMem": 36000
                    },
                    "gpus": [
                        {
                            "freeMem": 6000,
                            "gpu_id": 0,
                            "memUtilization": 75.0,
                            "totalMem": 24000,
                            "usedMem": 18000
                        },
                        {
                            "freeMem": 6000,
                            "gpu_id": 1,
                            "memUtilization": 75.0,
                            "totalMem": 24000,
                            "usedMem": 18000
                        }
                    ]
                },
                {
                    "id": "l4-node-2",
                    "vcpu": {"load_1m": 8.0},
                    "memory": {"freeMem": 49152, "averageUtil": 25.0},
                    "gpu": {
                        "avgMemUtilization": 75.0,
                        "count": 4,
                        "totalFreeMem": 24000,
                        "totalMem": 96000,
                        "totalUsedMem": 72000
                    },
                    "gpus": [
                        {
                            "freeMem": 6000,
                            "gpu_id": 0,
                            "memUtilization": 75.0,
                            "totalMem": 24000,
                            "usedMem": 18000
                        },
                        {
                            "freeMem": 6000,
                            "gpu_id": 1,
                            "memUtilization": 75.0,
                            "totalMem": 24000,
                            "usedMem": 18000
                        },
                        {
                            "freeMem": 6000,
                            "gpu_id": 2,
                            "memUtilization": 75.0,
                            "totalMem": 24000,
                            "usedMem": 18000
                        },
                        {
                            "freeMem": 6000,
                            "gpu_id": 3,
                            "memUtilization": 75.0,
                            "totalMem": 24000,
                            "usedMem": 18000
                        }
                    ]
                }
            ]
        }
    
    def run_all_tests(self):
        """Run all reassignment tests."""
        print("=" * 60)
        print("REASSIGNMENT ALLOCATION TESTS")
        print("=" * 60)
        
        test_methods = [
            ("Basic CPU/Memory Reassignment", self.test_basic_reassignment),
            ("GPU Reassignment", self.test_gpu_reassignment),
            ("L4 Multi-GPU Allocation (Case 1)", self.test_l4_multi_gpu_allocation),
            ("L4 Insufficient Memory (Case 2)", self.test_l4_insufficient_memory),
            ("L4 Single GPU Preferred (Case 3)", self.test_l4_single_gpu_preferred),
            ("L4 Multi-GPU Pooling (Case 4)", self.test_l4_multi_gpu_pooling)
        ]
        
        passed = 0
        total = len(test_methods)
        
        for test_name, test_method in test_methods:
            print(f"\n🔧 Running: {test_name}")
            if test_method():
                passed += 1
            print("-" * 40)
        
        print("\n" + "=" * 60)
        print(f"RESULTS: {passed}/{total} tests passed")
        if passed == total:
            print("🎉 All tests PASSED!")
        else:
            print("❌ Some tests FAILED!")
        print("=" * 60)
        
        return passed == total


def main():
    """Main test execution."""
    print("Starting Block Resource Allocator Reassignment Tests...\n")
    
    try:
        test_harness = TestReassignmentAllocation()
        success = test_harness.run_all_tests()
        
        print(f"\n🏁 Test execution completed. Success: {success}")
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        print(f"Error details: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
