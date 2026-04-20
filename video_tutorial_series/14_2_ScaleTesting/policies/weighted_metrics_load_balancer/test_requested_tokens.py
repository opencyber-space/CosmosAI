#!/usr/bin/env python3
"""
Test script for the requested tokens/second feature in weighted metrics load balancer.

This demonstrates how the policy routes requests based on user preferences for response speed.
"""

import json
import os
import sys

# Add the code directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from function import AIOSv1PolicyRule

def test_requested_tokens_preference():
    """Test the requested tokens/second preference matching."""

    # Mock settings with get_metrics function
    def mock_get_metrics():
        return {
            "block_metrics": [
                {
                    "instanceId": "fast-instance",
                    "llm_tokens_per_second": 80,  # Fast instance
                    "llm_active_sessions": 2,
                    "queue_length": {"average_1m": 5},
                    "latency": {"average_1m": 1000}
                },
                {
                    "instanceId": "balanced-instance",
                    "llm_tokens_per_second": 35,  # Balanced instance
                    "llm_active_sessions": 3,
                    "queue_length": {"average_1m": 3},
                    "latency": {"average_1m": 1500}
                },
                {
                    "instanceId": "thoughtful-instance",
                    "llm_tokens_per_second": 15,  # Thoughtful instance
                    "llm_active_sessions": 1,
                    "queue_length": {"average_1m": 8},
                    "latency": {"average_1m": 2000}
                }
            ]
        }

    settings = {"get_metrics": mock_get_metrics}

    # Policy parameters with requested_tokens_per_second weight
    parameters = {
        "weights": {
            "active_sessions": 0.2,
            "queue_length": 0.3,
            "latency": 0.2,
            "requested_tokens_per_second": 0.3  # Give weight to user preference
        },
        "user_preference_config": {
            "response_speed_preference": "balanced",
            "fast_threshold": 50,
            "thoughtful_threshold": 20
        }
    }

    policy = AIOSv1PolicyRule("test-rule", settings, parameters)

    # Test cases
    test_cases = [
        {
            "name": "Fast Response Preference",
            "input_data": {
                "instances": ["fast-instance", "balanced-instance", "thoughtful-instance"],
                "request": {"response_preference": "fast"}
            },
            "expected_instance": "fast-instance"
        },
        {
            "name": "Thoughtful Response Preference",
            "input_data": {
                "instances": ["fast-instance", "balanced-instance", "thoughtful-instance"],
                "request": {"response_preference": "thoughtful"}
            },
            "expected_instance": "thoughtful-instance"
        },
        {
            "name": "Balanced Response Preference",
            "input_data": {
                "instances": ["fast-instance", "balanced-instance", "thoughtful-instance"],
                "request": {"response_preference": "balanced"}
            },
            "expected_instance": "balanced-instance"
        },
        {
            "name": "Exact Tokens/Second Request",
            "input_data": {
                "instances": ["fast-instance", "balanced-instance", "thoughtful-instance"],
                "request": {"requested_tokens_per_second": 40}
            },
            "expected_instance": "balanced-instance"  # Closest to 40 tokens/sec
        }
    ]

    input_data = {
        "instances": ["fast-instance", "balanced-instance", "thoughtful-instance", "overloaded-instance"]
    }

    print("🧪 Testing Requested Tokens/Second Preference Matching")
    print("=" * 60)

    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        print(f"Request: {test_case['input_data']['request']}")

        result = policy.eval({}, test_case['input_data'], {})

        print(f"Selected Instance: {result['instance_id']}")
        if 'reason' in result:
            print(f"Reason: {result['reason']}")
        weighted_score = result.get('weighted_score')
        if weighted_score is not None:
            print(f"Weighted Score: {weighted_score:.4f}")
        else:
            print(f"Weighted Score: N/A")

if __name__ == "__main__":
    test_requested_tokens_preference()
