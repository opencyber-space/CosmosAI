#!/usr/bin/env python3
"""
Comprehensive test script for the Weighted Metrics Load Balancer Policy.

Tests all features including:
- Basic multi-metric load balancing
- Requested tokens/second preference matching
- Edge cases and error handling
- Weighted scoring validation
"""

import json
import sys
import os
from typing import Dict, Any

# Add the code directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from function import AIOSv1PolicyRule

class TestWeightedMetricsLoadBalancer:
    """Test class for the weighted metrics load balancer policy."""

    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.total_tests = 0

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"

        self.test_results.append(result)
        print(result)

    def create_mock_metrics(self):
        """Create mock metrics data for testing."""
        return {
            "block_metrics": [
                {
                    "instanceId": "fast-instance",
                    "llm_active_sessions": 2,
                    "queue_length": {"average_1m": 5, "average_5m": 7, "average_15m": 10},
                    "latency": {"average_1m": 800, "average_5m": 900, "average_15m": 1000},
                    "llm_tokens_per_second": 80,  # Fast instance
                    "hardware": {
                        "memory": {"averageUtil": 60},
                        "cpu": {"percent": 45},
                        "gpus": [{"utilization": 30}]
                    }
                },
                {
                    "instanceId": "balanced-instance",
                    "llm_active_sessions": 3,
                    "queue_length": {"average_1m": 3, "average_5m": 4, "average_15m": 6},
                    "latency": {"average_1m": 1200, "average_5m": 1300, "average_15m": 1400},
                    "llm_tokens_per_second": 35,  # Balanced instance
                    "hardware": {
                        "memory": {"averageUtil": 50},
                        "cpu": {"percent": 55},
                        "gpus": [{"utilization": 50}]
                    }
                },
                {
                    "instanceId": "thoughtful-instance",
                    "llm_active_sessions": 1,
                    "queue_length": {"average_1m": 8, "average_5m": 12, "average_15m": 15},
                    "latency": {"average_1m": 2000, "average_5m": 2200, "average_15m": 2500},
                    "llm_tokens_per_second": 15,  # Thoughtful instance
                    "hardware": {
                        "memory": {"averageUtil": 70},
                        "cpu": {"percent": 65},
                        "gpus": [{"utilization": 70}]
                    }
                },
                {
                    "instanceId": "overloaded-instance",
                    "llm_active_sessions": 8,
                    "queue_length": {"average_1m": 25, "average_5m": 30, "average_15m": 35},
                    "latency": {"average_1m": 5000, "average_5m": 5500, "average_15m": 6000},
                    "llm_tokens_per_second": 5,  # Very slow
                    "hardware": {
                        "memory": {"averageUtil": 95},
                        "cpu": {"percent": 90},
                        "gpus": [{"utilization": 95}]
                    }
                }
            ]
        }

    def test_basic_load_balancing(self):
        """Test basic multi-metric load balancing without user preferences."""
        print("\n🧪 Testing Basic Load Balancing")
        print("=" * 50)

        # Mock settings
        settings = {"get_metrics": lambda: self.create_mock_metrics()}

        # Policy parameters focusing on traditional metrics
        parameters = {
            "weights": {
                "active_sessions": 0.3,
                "queue_length": 0.4,
                "latency": 0.3
            },
            "averaging_period": "average_1m"
        }

        policy = AIOSv1PolicyRule("test-basic", settings, parameters)

        input_data = {
            "instances": ["fast-instance", "balanced-instance", "thoughtful-instance", "overloaded-instance"]
        }

        result = policy.eval({}, input_data, {})

        # Should select the best instance (likely balanced-instance due to good balance of metrics)
        selected = result["instance_id"]
        self.log_test("Basic Load Balancing", selected in ["fast-instance", "balanced-instance", "thoughtful-instance"],
                     f"Selected: {selected}")

        # Verify result structure
        required_fields = ["instance_id", "reason", "weighted_score", "metrics_used"]
        has_all_fields = all(field in result for field in required_fields)
        self.log_test("Result Structure", has_all_fields, f"Fields: {list(result.keys())}")

    def test_requested_tokens_preference(self):
        """Test the requested tokens/second preference matching."""
        print("\n🎯 Testing Requested Tokens/Second Preferences")
        print("=" * 50)

        settings = {"get_metrics": lambda: self.create_mock_metrics()}

        # Policy parameters with requested_tokens_per_second weight
        parameters = {
            "weights": {
                "active_sessions": 0.2,
                "queue_length": 0.2,
                "latency": 0.2,
                "requested_tokens_per_second": 0.4  # High weight for user preference
            },
            "user_preference_config": {
                "response_speed_preference": "balanced",
                "fast_threshold": 50,
                "thoughtful_threshold": 20
            }
        }

        policy = AIOSv1PolicyRule("test-preference", settings, parameters)

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

        for test_case in test_cases:
            result = policy.eval({}, test_case["input_data"], {})
            selected = result["instance_id"]
            passed = selected == test_case["expected_instance"]
            self.log_test(test_case["name"], passed,
                         f"Expected: {test_case['expected_instance']}, Got: {selected}")

    def test_weight_validation(self):
        """Test weight normalization and validation."""
        print("\n⚖️ Testing Weight Validation")
        print("=" * 50)

        settings = {"get_metrics": lambda: self.create_mock_metrics()}

        # Test weights that don't sum to 1.0
        parameters = {
            "weights": {
                "active_sessions": 0.5,
                "queue_length": 0.3,
                "latency": 0.3
            }  # Sums to 1.1, should be normalized
        }

        policy = AIOSv1PolicyRule("test-weights", settings, parameters)

        # Check if weights were normalized
        total_weight = sum(policy.weights.values())
        normalized = abs(total_weight - 1.0) < 0.01
        self.log_test("Weight Normalization", normalized, f"Total weight: {total_weight:.3f}")

    def test_error_handling(self):
        """Test error handling and fallback scenarios."""
        print("\n🚨 Testing Error Handling")
        print("=" * 50)

        # Test with no metrics collector
        settings = {}
        parameters = {"weights": {"active_sessions": 1.0}}
        policy = AIOSv1PolicyRule("test-error", settings, parameters)

        input_data = {"instances": ["instance1"]}
        result = policy.eval({}, input_data, {})

        # Should use fallback
        fallback_used = result.get("instance_id") is None and "not configured" in result.get("reason", "").lower()
        self.log_test("Fallback Selection", fallback_used, f"Result: {result}")

        # Test with no available instances
        input_data = {"instances": []}
        result = policy.eval({}, input_data, {})
        no_instances_handled = result.get("instance_id") is None
        self.log_test("No Instances Handling", no_instances_handled, f"Result: {result}")

    def test_metric_extraction(self):
        """Test individual metric extraction."""
        print("\n📊 Testing Metric Extraction")
        print("=" * 50)

        settings = {"get_metrics": lambda: self.create_mock_metrics()}
        parameters = {
            "weights": {
                "active_sessions": 0.25,
                "queue_length": 0.25,
                "latency": 0.25,
                "tokens_per_second": 0.25
            }
        }

        policy = AIOSv1PolicyRule("test-metrics", settings, parameters)

        # Test metric extraction for fast-instance
        instance = self.create_mock_metrics()["block_metrics"][0]

        active_sessions = policy._get_metric_value(instance, "active_sessions")
        self.log_test("Active Sessions Extraction", active_sessions == 2, f"Got: {active_sessions}")

        queue_length = policy._get_metric_value(instance, "queue_length")
        self.log_test("Queue Length Extraction", queue_length == 5, f"Got: {queue_length}")

        tokens_per_sec = policy._get_metric_value(instance, "tokens_per_second")
        self.log_test("Tokens/Second Extraction", tokens_per_sec == 80, f"Got: {tokens_per_sec}")

    def test_scoring_functions(self):
        """Test the scoring functions for requested tokens/second."""
        print("\n🎯 Testing Scoring Functions")
        print("=" * 50)

        settings = {"get_metrics": lambda: self.create_mock_metrics()}
        parameters = {
            "weights": {"requested_tokens_per_second": 1.0},
            "user_preference_config": {
                "fast_threshold": 50,
                "thoughtful_threshold": 20
            }
        }

        policy = AIOSv1PolicyRule("test-scoring", settings, parameters)

        # Test categorical scoring
        fast_score = policy._score_categorical_preference(80, "fast")
        self.log_test("Fast Preference Scoring", fast_score == 1.0, f"Score: {fast_score}")

        thoughtful_score = policy._score_categorical_preference(15, "thoughtful")
        self.log_test("Thoughtful Preference Scoring", thoughtful_score == 1.0, f"Score: {thoughtful_score}")

        balanced_score = policy._score_categorical_preference(35, "balanced")
        self.log_test("Balanced Preference Scoring", balanced_score == 1.0, f"Score: {balanced_score}")

        # Test exact scoring
        exact_score = policy._score_exact_tokens_preference(40, 35)
        self.log_test("Exact Tokens Scoring", 0.8 <= exact_score <= 1.0, f"Score: {exact_score}")

    def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting Weighted Metrics Load Balancer Tests")
        print("=" * 60)

        self.test_basic_load_balancing()
        self.test_requested_tokens_preference()
        self.test_weight_validation()
        self.test_error_handling()
        self.test_metric_extraction()
        self.test_scoring_functions()

        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.passed_tests}/{self.total_tests} tests passed")

        if self.passed_tests == self.total_tests:
            print("🎉 All tests passed!")
            return True
        else:
            print("❌ Some tests failed. Check the output above.")
            return False

def main():
    """Main test runner."""
    tester = TestWeightedMetricsLoadBalancer()
    success = tester.run_all_tests()

    # Print detailed results
    print("\n📋 Detailed Test Results:")
    for result in tester.test_results:
        print(f"  {result}")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
