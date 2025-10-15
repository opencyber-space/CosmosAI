#!/usr/bin/env python3
"""
Debug script for the consensus allocation test.
"""
import sys
import traceback

try:
    from test_consensus_allocation import TestConsensusAllocation
    
    print("Creating test instance...")
    test = TestConsensusAllocation()
    
    print("Test scenarios created:")
    for i, scenario in enumerate(test.test_scenarios):
        print(f"  {i}: {scenario['name']}")
    
    print("\nRunning Resource Constrained Scenario...")
    scenario = test.test_scenarios[1]  # Resource Constrained Scenario
    
    print("Input data:", scenario['input_data']['action'])
    
    result = test._run_scenario(scenario)
    print("Result:", result['status'])
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
