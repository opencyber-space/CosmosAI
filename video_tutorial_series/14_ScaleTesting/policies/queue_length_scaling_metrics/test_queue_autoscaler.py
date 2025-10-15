#!/usr/bin/env python3
"""
Test script for Queue Length Autoscaler Helper Policy

This script tests the autoscaler policy with different queue length scenarios 
to verify that scaling decisions are made correctly based on both average 
and per-instance metrics.
"""
import logging
import json
import sys
import os
# Add the code directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))
from function import AIOSv1PolicyRule

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_queue_autoscaler')

def test_scenario(scenario_name, instances_data, expected_operation):
    """Test a specific scaling scenario"""
    logger.info(f"===== TESTING SCENARIO: {scenario_name} =====")
    
    # Create mock metrics
    block_metrics = []
    for i, queue_length in enumerate(instances_data):
        instance_id = f"instance-{i}"
        block_metrics.append({
            "instanceId": instance_id,
            "queue_length": {
                "average_1m": queue_length,
                "average_5m": queue_length,
                "average_15m": queue_length,
                "current": queue_length
            }
        })
    
    # Mock input data
    input_data = {
        "current_instances": [instance["instanceId"] for instance in block_metrics]
    }
    
    # Create mock metrics collector
    def mock_metrics_collector():
        return {"block_metrics": block_metrics}
    
    # Initialize the policy with test parameters
    policy = AIOSv1PolicyRule(
        rule_id="test-policy",
        settings={"get_metrics": mock_metrics_collector},
        parameters={
            "queue_up_threshold": 10,
            "queue_down_threshold": 2,
            "min_replicas": 1,
            "averaging_period": "average_1m"
        }
    )
    
    # Evaluate the policy
    result = policy.eval(None, input_data, {})
    
    # Check if the result matches expectations
    actual_operation = result.get("operation") if not result.get("skip", True) else "none"
    success = actual_operation == expected_operation
    
    # Print the result
    logger.info(f"Queue lengths: {instances_data}")
    logger.info(f"Expected operation: {expected_operation}")
    logger.info(f"Actual operation: {actual_operation}")
    logger.info(f"Result details: {json.dumps(result, indent=2)}")
    logger.info(f"Test {'PASSED' if success else 'FAILED'}")
    logger.info("=" * 50)
    
    return success

def run_all_tests():
    """Run all test scenarios"""
    test_scenarios = [
        # Test 1: Average queue length is below thresholds - no scaling
        {
            "name": "Normal Load - No Scaling",
            "instances_data": [5, 5, 5],  # All instances have normal queue length
            "expected_operation": "none"
        },
        
        # Test 2: Average queue length exceeds upscale threshold - should scale up
        {
            "name": "High Average Load - Upscale",
            "instances_data": [12, 12, 12],  # Average is 12, above upscale threshold (10)
            "expected_operation": "upscale"
        },
        
        # Test 3: One instance exceeds upscale threshold - should scale up
        {
            "name": "Single Instance High Load - Upscale",
            "instances_data": [5, 5, 15],  # One instance has high queue length
            "expected_operation": "upscale"
        },
        
        # Test 4: Average is low but individual is high - should scale up
        {
            "name": "Low Average, One High Instance - Upscale",
            "instances_data": [1, 1, 20],  # Average is ~7.3, below threshold, but one instance is high
            "expected_operation": "upscale"
        },
        
        # Test 5: Low queue lengths - should scale down
        {
            "name": "Low Load - Downscale",
            "instances_data": [1, 1, 1],  # All instances have low queue length
            "expected_operation": "downscale"
        },
        
        # Test 6: Low queue lengths but only one instance - should not scale down
        {
            "name": "Low Load, Min Replicas - No Downscale",
            "instances_data": [1],  # Only one instance, at min_replicas
            "expected_operation": "none"
        }
    ]
    
    # Run all tests and collect results
    results = []
    for scenario in test_scenarios:
        result = test_scenario(
            scenario["name"], 
            scenario["instances_data"], 
            scenario["expected_operation"]
        )
        results.append(result)
    
    # Summarize results
    passed = results.count(True)
    total = len(results)
    logger.info(f"TEST SUMMARY: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
