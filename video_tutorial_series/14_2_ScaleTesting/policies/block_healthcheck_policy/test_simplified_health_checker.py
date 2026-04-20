#!/usr/bin/env python3
"""
Test script for the simplified Block Health Checker Policy

This script tests the policy according to block.md specification:
- Input: health_check_data with boolean values (instance_id: True/False)
- Output: Empty dict {}
- Behavior: Track consecutive failures, call failure policy when threshold exceeded
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0,os.path.join(os.path.dirname(os.path.realpath(__file__)),"code"))
from function import AIOSv1PolicyRule
sys.path.remove(os.path.join(os.path.dirname(os.path.realpath(__file__)),"code"))


def test_basic_functionality():
    """Test basic health checker functionality"""
    print("=== Testing Basic Functionality ===")
    
    # Initialize policy
    rule_id = "test_health_checker"
    settings = {
        "GATEWAY_URL": "MANAGEMENTMASTER:30600",
        "block_data": {"id": "test_block"},
        "cluster_data": {"id": "test_cluster"},
        "call_dummy_reassign_policy": True
    }
    parameters = {"failure_threshold": 3}
    
    policy = AIOSv1PolicyRule(rule_id, settings, parameters)
    
    # Test healthy instances
    input_data = {
        "health_check_data": {
            "instance-00": True,
            "instance-01": True,
            "instance-02": True
        }
    }
    
    result = policy.eval(parameters, input_data, {})
    print(f"✓ Healthy instances result: {result}")
    assert result == {}, "Should return empty dict for healthy instances"
    
    # Test single unhealthy instance (below threshold)
    input_data = {
        "health_check_data": {
            "instance-00": True,
            "instance-01": False,  # Unhealthy
            "instance-02": True
        }
    }
    
    result = policy.eval(parameters, input_data, {})
    print(f"✓ Single failure result: {result}")
    assert result == {}, "Should return empty dict"
    assert policy.counter.get("instance-01", 0) == 1, "Should increment failure counter"
    
    print("Basic functionality tests passed!\n")

def test_failure_threshold():
    """Test failure threshold behavior"""
    print("=== Testing Failure Threshold ===")
    
    # Initialize policy
    rule_id = "test_health_checker"
    settings = {
        "failure_policy_server_api_url": "http://test-server:8080/api/v1",
        "failure_policy_id": "test_failure_policy",
        "block_data": {"id": "test_block"},
        "cluster_data": {"id": "test_cluster"}
    }
    parameters = {"failure_threshold": 3}
    
    policy = AIOSv1PolicyRule(rule_id, settings, parameters)
    
    # Mock the call_failure_policy function
    with patch('function.call_failure_policy') as mock_call:
        mock_call.return_value = {"success": True}
        
        # Simulate consecutive failures
        for i in range(4):  # 4 failures, threshold is 3
            input_data = {
                "health_check_data": {
                    "instance-01": False  # Consistently unhealthy
                }
            }
            
            result = policy.eval(parameters, input_data, {})
            print(f"Failure {i+1}: counter = {policy.counter.get('instance-01', 0)}")
            
            if i < 3:  # Before threshold
                assert not mock_call.called or mock_call.call_count == 0, f"Should not call failure policy yet at failure {i+1}"
            else:  # After threshold
                assert mock_call.called, "Should call failure policy when threshold exceeded"
                assert policy.counter.get("instance-01", 0) == 0, "Should reset counter after calling failure policy"
    
    print("Failure threshold tests passed!\n")

def test_recovery_behavior():
    """Test recovery behavior when instance becomes healthy"""
    print("=== Testing Recovery Behavior ===")
    
    # Initialize policy
    rule_id = "test_health_checker"
    settings = {
        "failure_policy_server_api_url": "http://test-server:8080/api/v1",
        "failure_policy_id": "test_failure_policy",
        "block_data": {"id": "test_block"},
        "cluster_data": {"id": "test_cluster"}
    }
    parameters = {"failure_threshold": 3}
    
    policy = AIOSv1PolicyRule(rule_id, settings, parameters)
    
    # Simulate 2 failures
    for i in range(2):
        input_data = {
            "health_check_data": {
                "instance-01": False
            }
        }
        policy.eval(parameters, input_data, {})
    
    assert policy.counter.get("instance-01", 0) == 2, "Should have 2 failures"
    
    # Instance becomes healthy
    input_data = {
        "health_check_data": {
            "instance-01": True
        }
    }
    result = policy.eval(parameters, input_data, {})
    
    assert policy.counter.get("instance-01", 0) == 0, "Should reset counter when instance becomes healthy"
    assert result == {}, "Should return empty dict"
    
    print("Recovery behavior tests passed!\n")

def test_management_interface():
    """Test management interface"""
    print("=== Testing Management Interface ===")
    
    # Initialize policy
    rule_id = "test_health_checker"
    settings = {
        "failure_policy_server_api_url": "http://test-server:8080/api/v1",
        "failure_policy_id": "test_failure_policy",
        "block_data": {"id": "test_block"},
        "cluster_data": {"id": "test_cluster"}
    }
    parameters = {"failure_threshold": 3}
    
    policy = AIOSv1PolicyRule(rule_id, settings, parameters)
    
    # Add some failure data
    policy.counter = {"instance-01": 2, "instance-02": 1}
    
    # Test get_status
    status = policy.management("get_status")
    print(f"✓ Status: {json.dumps(status, indent=2)}")
    assert "failure_threshold" in status
    assert "failure_counts" in status
    assert status["failure_counts"]["instance-01"] == 2
    
    # Test reset_instance
    reset_result = policy.management("reset_instance", {"instance_id": "instance-01"})
    print(f"✓ Reset instance result: {reset_result}")
    assert reset_result["success"] == True
    assert policy.counter["instance-01"] == 0
    
    # Test reset_counters
    reset_all = policy.management("reset_counters")
    print(f"✓ Reset all result: {reset_all}")
    assert reset_all["success"] == True
    assert len(policy.counter) == 0
    
    print("Management interface tests passed!\n")

def test_block_md_compliance():
    """Test compliance with block.md specification"""
    print("=== Testing block.md Compliance ===")
    
    # Initialize policy
    rule_id = "test_health_checker"
    settings = {
        "failure_policy_server_api_url": "http://test-server:8080/api/v1",
        "failure_policy_id": "test_failure_policy",
        "block_data": {"id": "test_block"},
        "cluster_data": {"id": "test_cluster"}
    }
    parameters = {"failure_threshold": 3}
    
    policy = AIOSv1PolicyRule(rule_id, settings, parameters)
    
    # Test with block.md specified input format
    input_data = {
        "health_check_data": {
            "instance-00": True,    # Healthy
            "instance-01": False,   # Unhealthy
            "instance-02": True,    # Healthy
            "instance-03": False    # Unhealthy
        }
    }
    
    result = policy.eval(parameters, input_data, {})
    
    # Verify compliance
    assert isinstance(result, dict), "Must return a dict"
    assert result == {}, "Must return empty dict as per block.md"
    assert policy.counter.get("instance-01", 0) == 1, "Should track unhealthy instances"
    assert policy.counter.get("instance-03", 0) == 1, "Should track unhealthy instances"
    assert "instance-00" not in policy.counter or policy.counter["instance-00"] == 0, "Should not track healthy instances"
    assert "instance-02" not in policy.counter or policy.counter["instance-02"] == 0, "Should not track healthy instances"
    
    print("✓ Input format compliance: PASSED")
    print("✓ Output format compliance: PASSED")
    print("✓ Failure tracking compliance: PASSED")
    print("block.md compliance tests passed!\n")

if __name__ == "__main__":
    print("Testing Simplified Block Health Checker Policy")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_failure_threshold()
        test_recovery_behavior()
        test_management_interface()
        test_block_md_compliance()
        
        print("🎉 All tests passed! Policy is ready for use.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
