import unittest
from datetime import datetime
import os,sys
sys.path.insert(0,os.path.join(os.path.dirname(os.path.realpath(__file__)),"code"))
from function import AIOSv1PolicyRule
sys.path.remove(os.path.join(os.path.dirname(os.path.realpath(__file__)),"code"))

class TestAddNodePolicy(unittest.TestCase):
    def setUp(self):
        self.policy = AIOSv1PolicyRule(
            rule_id="test-add-node",
            settings={},  # Empty settings as all fields are parameters
            parameters={
                "min_node_cpu": 4,
                "min_node_memory": 8192,
                "required_gpu_models": ["NVIDIA A100"],
                "allowed_tags": ["gpu", "production","demo", "development"],
                "min_node_storage": 1024,
                "min_gpu_memory": 4096,
                "min_network_interfaces": 1,
                "min_tx_bandwidth": 10,
                "min_rx_bandwidth": 10

            }
        )

    def test_valid_node_addition(self):
        input_data = {
            "node_data": {
                "vcpus": {"count": 8},
                "memory": 16384,
                "storage": {"size": 102400},
                "gpus": {
                    "count": 2,
                    "modelNames": ["NVIDIA A100"],
                    "memory": 16384
                },
                "network": {
                    "interfaces": 2,
                    "txBandwidth": 1000,
                    "rxBandwidth": 1000
                },
                "tags": ["gpu", "production"]
            },
            "cluster_data": {
                "nodes": [{"id": "node-1"}, {"id": "node-2"}]
            },
            "cluster_metrics": {
                "cpu_usage_percentage": 60
            }
        }
        
        result = self.policy.eval({}, input_data, {})
        self.assertTrue(result["allowed"])
        self.policy.current_time =  datetime.utcnow().isoformat()

    def test_insufficient_resources(self):
        input_data = {
            "node_data": {
                "vcpus": {"count": 2},  # Below minimum
                "memory": 4096,  # Below minimum
                "storage": {"size": 102400},
                "gpus": {
                    "count": 2,
                    "modelNames": ["NVIDIA A100"],
                    "memory": 16384
                }
            },
            "cluster_data": {"nodes": []},
            "cluster_metrics": {}
        }
        
        result = self.policy.eval({}, input_data, {})
        self.assertFalse(result["allowed"])

    def test_management_functions(self):
        # Test updating resource requirements
        result = self.policy.management("update_min_resources", {
            "min_node_cpu": 8,
            "min_node_memory": 16384
        })
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.policy.parameters["min_node_cpu"], 8)
        
        # Test invalid management action
        result = self.policy.management("invalid_action", {})
        self.assertEqual(result["status"], "error")


    def test_update_tags(self):
        """Test updating tags."""
        result = self.policy.management("update_tags", {
            "allowed_tags": ["gpu", "production", "development"],
            "required_tags": ["production"]
        })
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.policy.parameters["allowed_tags"], 
                        ["gpu", "production", "development"])
        # self.assertEqual(result["timestamp"], "2025-05-21 07:06:35")

    def test_update_network_requirements(self):
        """Test updating network requirements."""
        result = self.policy.management("update_network_requirements", {
            "min_network_interfaces": 2,
            "min_tx_bandwidth": 2000
        })
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.policy.parameters["min_network_interfaces"], 2)
        self.assertEqual(self.policy.parameters["min_tx_bandwidth"], 2000)

    def test_update_gpu_requirements(self):
        """Test updating GPU requirements."""
        result = self.policy.management("update_gpu_requirements", {
            "required_gpu_models": ["NVIDIA A100", "NVIDIA A6000"],
            "min_gpu_memory": 16384
        })
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.policy.parameters["required_gpu_models"], 
                        ["NVIDIA A100", "NVIDIA A6000"])
        self.assertEqual(self.policy.parameters["min_gpu_memory"], 16384)


if __name__ == '__main__':
    print(f"Running Add Node Policy Tests at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    unittest.main(verbosity=2)