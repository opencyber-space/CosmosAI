#!/usr/bin/env python3
"""
Test script for the _redistribute_sessions method in AIOSv1PolicyRule.
"""

import logging
from collections import defaultdict
from function import AIOSv1PolicyRule  # Assuming function.py is in the same directory
import time
import random

# Disable logging for test
logging.basicConfig(level=logging.DEBUG)

def test_redistribute_sessions():
    # Mock settings and parameters
    settings = {}
    parameters = {}

    # Create an instance of the policy rule
    policy = AIOSv1PolicyRule("test_rule", settings, parameters)

    # Set up initial state
    policy.current_instances = ["inst1", "inst2", "inst3"]
    policy.previous_instances = ["inst1", "inst2"]
    policy.session_ids_cache = {
        "session1": "inst1",
        "session2": "inst1",
        "session3": "inst1",
        "session4": "inst1",
        "session5": "inst2",
        "session6": "inst2",
        "session7": "inst3",
    }
    policy.redistribution_percentage = 0.2

    print("Before redistribution:")
    print(f"Session cache: {policy.session_ids_cache}")
    sessions_by_instance = defaultdict(list)
    for s, i in policy.session_ids_cache.items():
        sessions_by_instance[i].append(s)
    print(f"Sessions per instance: {dict(sessions_by_instance)}")

    # New instances: inst3 is new
    new_instances = ["inst3"]

    # Call redistribute
    policy._redistribute_sessions(new_instances)

    print("\nAfter redistribution:")
    print(f"Session cache: {policy.session_ids_cache}")
    sessions_by_instance_after = defaultdict(list)
    for s, i in policy.session_ids_cache.items():
        sessions_by_instance_after[i].append(s)
    print(f"Sessions per instance: {dict(sessions_by_instance_after)}")

    # Check that some sessions were moved to inst3
    moved_to_new = [s for s, i in policy.session_ids_cache.items() if i == "inst3" and s not in ["session7"]]  # session7 was already there
    print(f"Sessions moved to new instance: {moved_to_new}")

    assert len(moved_to_new) > 0, "No sessions were redistributed to new instance"
    print("Test passed: Sessions redistributed successfully")

def test_periodic_redistribution():
    # Mock settings with get_metrics
    def mock_get_metrics():
        return {
            "block_metrics": [
                {"instanceId": "inst1", "llm_active_sessions": 80, "queue_length": {"average_1m": 100}},
                {"instanceId": "inst2", "llm_active_sessions": 50, "queue_length": {"average_1m": 50}},
                {"instanceId": "inst3", "llm_active_sessions": 40, "queue_length": {"average_1m": 30}},
            ]
        }
    
    settings = {"get_metrics": mock_get_metrics}
    parameters = {"redistribution_interval": 1, "redistribution_selection_mode": "best"}  # 1 second for test

    # Create an instance of the policy rule
    policy = AIOSv1PolicyRule("test_rule", settings, parameters)

    # Set up initial state
    policy.current_instances = ["inst1", "inst2", "inst3"]
    policy.previous_instances = ["inst1", "inst2", "inst3"]  # No new instances
    policy.session_ids_cache = {
        "session1": "inst1",
        "session2": "inst1",
        "session3": "inst1",
        "session4": "inst1",
        "session5": "inst2",
        "session6": "inst2",
        "session7": "inst3",
    }
    policy.redistribution_percentage = 0.2
    policy.last_redistribution_time = time.time() - 2  # Set to 2 seconds ago to trigger periodic

    print("\nBefore periodic redistribution:")
    print(f"Session cache: {policy.session_ids_cache}")
    sessions_by_instance = defaultdict(list)
    for s, i in policy.session_ids_cache.items():
        sessions_by_instance[i].append(s)
    print(f"Sessions per instance: {dict(sessions_by_instance)}")

    # Mock packet for eval
    class MockPacket:
        def __init__(self, session_id):
            self.session_id = session_id

    input_data = {
        "instances": ["inst1", "inst2", "inst3"],
        "packet": MockPacket("session1")
    }

    # Call eval, which should trigger periodic redistribution
    result = policy.eval({}, input_data, {})

    print("\nAfter periodic redistribution:")
    print(f"Session cache: {policy.session_ids_cache}")
    sessions_by_instance_after = defaultdict(list)
    for s, i in policy.session_ids_cache.items():
        sessions_by_instance_after[i].append(s)
    print(f"Sessions per instance: {dict(sessions_by_instance_after)}")

    # Check if redistribution happened (cache should have changed)
    original_cache = {
        "session1": "inst1",
        "session2": "inst1",
        "session3": "inst1",
        "session4": "inst1",
        "session5": "inst2",
        "session6": "inst2",
        "session7": "inst3",
    }
    assert policy.session_ids_cache != original_cache, "Periodic redistribution did not occur"
    print("Test passed: Periodic redistribution triggered successfully")

def test_redistribution_with_many_sessions():
    # Mock settings with get_metrics for best selection
    def mock_get_metrics():
        return {
            "block_metrics": [
                {"instanceId": "inst1", "llm_active_sessions": 10, "queue_length": {"average_1m": 10}},
                {"instanceId": "inst2", "llm_active_sessions": 5, "queue_length": {"average_1m": 5}},
                {"instanceId": "inst3", "llm_active_sessions": 5, "queue_length": {"average_1m": 5}},
            ]
        }
    
    settings = {"get_metrics": mock_get_metrics}
    
    # Test both modes
    for mode in ["equal", "weighted"]:
        print(f"\n=== Testing redistribution with {mode} mode ===")
        parameters = {"redistribution_percentage": 1, "redistribution_selection_mode": "least_loaded", "selection_mode": mode}
        if mode == "weighted":
            parameters["weights"] = {"active_sessions": 0.5, "queue_length": 0.5}
        
        # Create an instance of the policy rule
        policy = AIOSv1PolicyRule("test_rule", settings, parameters)

        # Set up initial state: 1 instance with 1000 sessions
        policy.current_instances = ["inst1"]
        policy.previous_instances = []
        policy.session_ids_cache = {f"session{i}": "inst1" for i in range(1000)}
        policy.session_task_counts = {f"session{i}": 1 for i in range(1000)}  # Each session has 1 task

        print("Before adding new instances:")
        print(f"Total sessions: {len(policy.session_ids_cache)}")
        print(f"Sessions on inst1: {len([s for s in policy.session_ids_cache.values() if s == 'inst1'])}")

        # Simulate adding 2 new instances
        new_instances = ["inst2", "inst3"]
        policy.current_instances = ["inst1", "inst2", "inst3"]
        policy.previous_instances = ["inst1"]

        # Call redistribute
        policy._redistribute_sessions(new_instances)

        print("After redistribution:")
        print(f"Session cache size: {len(policy.session_ids_cache)}")
        sessions_by_instance = defaultdict(list)
        for s, i in policy.session_ids_cache.items():
            sessions_by_instance[i].append(s)
        print(f"Sessions per instance: { {k: len(v) for k, v in sessions_by_instance.items()} }")

        # Check that sessions were distributed to new instances
        sessions_on_inst1 = len(sessions_by_instance["inst1"])
        sessions_on_inst2 = len(sessions_by_instance["inst2"])
        sessions_on_inst3 = len(sessions_by_instance["inst3"])

        print(f"Sessions on inst1: {sessions_on_inst1}")
        print(f"Sessions on inst2: {sessions_on_inst2}")
        print(f"Sessions on inst3: {sessions_on_inst3}")

        # Assert that some sessions were moved to new instances
        assert sessions_on_inst2 > 0 or sessions_on_inst3 > 0, "No sessions redistributed to new instances"
        assert sessions_on_inst1 < 1000, "No sessions moved from inst1"

        # Check if load is balanced (roughly)
        total_sessions = len(policy.session_ids_cache)
        avg_sessions = total_sessions / 3
        print(f"Average sessions per instance: {avg_sessions:.2f}")
        print(f"Distribution: inst1={sessions_on_inst1}, inst2={sessions_on_inst2}, inst3={sessions_on_inst3}")

        # Now simulate new session routing
        print(f"\nSimulating new session routing with {mode} mode:")
        class MockPacket:
            def __init__(self, session_id):
                self.session_id = session_id
        
        input_data = {"instances": ["inst1", "inst2", "inst3"], "packet": MockPacket("new_session")}
        
        # Simulate 10 new sessions
        new_session_counts = defaultdict(int)
        for i in range(10):
            input_data["packet"].session_id = f"new_session_{i}"
            result = policy.eval({}, input_data, {})
            selected_instance = result['instance_id']
            new_session_counts[selected_instance] += 1
            print(f"New session {i} routed to: {selected_instance}")
        
        print(f"New sessions distribution: {dict(new_session_counts)}")
        
        print(f"Test passed for {mode}: Load redistributed and new sessions routed successfully")

def test_selection_modes():
    # Mock settings with get_metrics
    def mock_get_metrics():
        return {
            "block_metrics": [
                {"instanceId": "inst1", "llm_active_sessions": 10, "queue_length": {"average_1m": 10}},
                {"instanceId": "inst2", "llm_active_sessions": 5, "queue_length": {"average_1m": 5}},
                {"instanceId": "inst3", "llm_active_sessions": 5, "queue_length": {"average_1m": 5}},
            ]
        }
    
    settings = {"get_metrics": mock_get_metrics}
    
    # Test weighted mode
    parameters_weighted = {"selection_mode": "weighted", "weights": {"active_sessions": 0.5, "queue_length": 0.5}}
    policy_weighted = AIOSv1PolicyRule("test_rule", settings, parameters_weighted)
    policy_weighted.current_instances = ["inst1", "inst2", "inst3"]
    policy_weighted.session_ids_cache = {"session1": "inst1", "session2": "inst2"}  # Inst1 has 1, Inst2 has 1, Inst3 has 0
    
    class MockPacket:
        def __init__(self, session_id):
            self.session_id = session_id
    
    input_data = {"instances": ["inst1", "inst2", "inst3"], "packet": MockPacket("new_session")}
    result_weighted = policy_weighted.eval({}, input_data, {})
    print(f"Weighted mode selected: {result_weighted['instance_id']}")
    
    # Test equal mode
    parameters_equal = {"selection_mode": "equal"}
    policy_equal = AIOSv1PolicyRule("test_rule", settings, parameters_equal)
    policy_equal.current_instances = ["inst1", "inst2", "inst3"]
    policy_equal.session_ids_cache = {"session1": "inst1", "session2": "inst2"}  # Same as above
    
    result_equal = policy_equal.eval({}, input_data, {})
    print(f"Equal mode selected: {result_equal['instance_id']}")
    
    print("Selection test completed")

def test_imbalance_threshold():
    # Mock settings
    settings = {}
    parameters = {"imbalance_threshold": 1}  # Threshold of 1, so imbalance of 1 or less skips redistribution

    # Create an instance of the policy rule
    policy = AIOSv1PolicyRule("test_rule", settings, parameters)

    # Set up initial state with small imbalance: 334, 333, 333
    policy.current_instances = ["inst1", "inst2", "inst3"]
    policy.previous_instances = ["inst1", "inst2", "inst3"]
    policy.session_ids_cache = {}
    for i in range(334):
        policy.session_ids_cache[f"session{i}"] = "inst1"
    for i in range(334, 667):
        policy.session_ids_cache[f"session{i}"] = "inst2"
    for i in range(667, 1000):
        policy.session_ids_cache[f"session{i}"] = "inst3"

    print("\nBefore redistribution (small imbalance):")
    sessions_by_instance = defaultdict(list)
    for s, i in policy.session_ids_cache.items():
        sessions_by_instance[i].append(s)
    print(f"Sessions per instance: { {k: len(v) for k, v in sessions_by_instance.items()} }")

    # Call redistribute (should skip due to small imbalance)
    policy._redistribute_sessions([])  # Periodic redistribution

    print("After redistribution:")
    sessions_by_instance_after = defaultdict(list)
    for s, i in policy.session_ids_cache.items():
        sessions_by_instance_after[i].append(s)
    print(f"Sessions per instance: { {k: len(v) for k, v in sessions_by_instance_after.items()} }")

    # Check that no redistribution occurred
    assert sessions_by_instance == sessions_by_instance_after, "Redistribution occurred despite small imbalance"
    print("Test passed: Redistribution skipped for small imbalance")

    # Now test with larger imbalance
    parameters["imbalance_threshold"] = 0  # Threshold 0, so any imbalance triggers
    policy2 = AIOSv1PolicyRule("test_rule2", settings, parameters)
    policy2.current_instances = ["inst1", "inst2", "inst3"]
    policy2.previous_instances = ["inst1", "inst2", "inst3"]
    policy2.session_ids_cache = policy.session_ids_cache.copy()  # Same as above
    policy2.redistribution_percentage = 0.1  # Small percentage to see change

    print("\nBefore redistribution (threshold 0):")
    print(f"Sessions per instance: { {k: len(v) for k, v in sessions_by_instance.items()} }")

    # Call redistribute (should trigger)
    policy2._redistribute_sessions(policy2.current_instances)

    print("After redistribution:")
    sessions_by_instance_after2 = defaultdict(list)
    for s, i in policy2.session_ids_cache.items():
        sessions_by_instance_after2[i].append(s)
    print(f"Sessions per instance: { {k: len(v) for k, v in sessions_by_instance_after2.items()} }")

    # Check that redistribution occurred
    assert sessions_by_instance != sessions_by_instance_after2, "Redistribution did not occur with threshold 0"
    print("Test passed: Redistribution occurred with threshold 0")

def test_tie_breaker_round_robin():
    # Mock settings with get_metrics where inst2 and inst3 have identical scores
    def mock_get_metrics():
        return {
            "block_metrics": [
                {"instanceId": "inst1", "llm_active_sessions": 10, "queue_length": {"average_1m": 10}},
                {"instanceId": "inst2", "llm_active_sessions": 5, "queue_length": {"average_1m": 5}},
                {"instanceId": "inst3", "llm_active_sessions": 5, "queue_length": {"average_1m": 5}},
            ]
        }
    
    settings = {"get_metrics": mock_get_metrics}
    
    # Test round_robin tiebreaker in weighted mode
    parameters = {"selection_mode": "weighted", "weights": {"active_sessions": 0.5, "queue_length": 0.5}, "tie_breaker": "round_robin"}
    policy = AIOSv1PolicyRule("test_rule", settings, parameters)
    policy.current_instances = ["inst1", "inst2", "inst3"]
    policy.session_ids_cache = {"session1": "inst1"}  # Inst1 has 1, others 0
    
    class MockPacket:
        def __init__(self, session_id):
            self.session_id = session_id
    
    input_data = {"instances": ["inst1", "inst2", "inst3"], "packet": MockPacket("new_session")}
    
    # Simulate multiple selections to see round_robin cycling
    selections = []
    for i in range(10):
        input_data["packet"].session_id = f"new_session_{i}"
        result = policy.eval({}, input_data, {})
        selected_instance = result['instance_id']
        selections.append(selected_instance)
        print(f"Selection {i}: {selected_instance}")
    
    print(f"Round-robin selections: {selections}")
    
    # Check that it cycles between inst2 and inst3 (since they have equal scores, inst1 has lower score)
    # Assuming inst2 and inst3 tie, and round_robin alternates
    # Note: Depending on initial index, it might start with one or the other
    inst2_count = selections.count("inst2")
    inst3_count = selections.count("inst3")
    print(f"inst2 selected {inst2_count} times, inst3 selected {inst3_count} times")
    
    # Should be roughly equal, but since 10 selections and 2 instances, 5 each
    assert abs(inst2_count - inst3_count) <= 1, f"Round-robin not balanced: inst2={inst2_count}, inst3={inst3_count}"
    print("Test passed: Round-robin tiebreaker working")

if __name__ == "__main__":
    test_redistribute_sessions()
    test_periodic_redistribution()
    test_redistribution_with_many_sessions()
    test_selection_modes()
    test_imbalance_threshold()
    test_tie_breaker_round_robin()
