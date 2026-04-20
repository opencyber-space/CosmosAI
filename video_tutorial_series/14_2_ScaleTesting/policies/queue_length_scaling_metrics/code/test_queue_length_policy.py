import json
import pytest
import copy
import os
import sys
import time
from unittest.mock import MagicMock

# Add the function's directory to the python path
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path)

from function import AIOSv1PolicyRule

@pytest.fixture
def mock_metrics_data():
    # Construct path to the JSON file relative to this test file
    with open(os.path.join(dir_path, 'block_metrics.json')) as f:
        return json.load(f)

@pytest.mark.parametrize("queue_lengths, min_replicas, averaging_period, expected_op, expected_skip, expected_instance_to_remove", [
    # Upscale
    ([15, 12], 1, "average_1m", "upscale", False, None),
    # Downscale
    ([1, 0.5], 1, "average_5m", "downscale", False, "in-pb9x"),
    # No action
    ([5, 6], 1, "average_15m", None, True, None),
    # Downscale prevented by min_replicas
    ([1, 0.5], 2, "average_1m", None, True, None),
])
def test_queue_length_policy(mock_metrics_data, queue_lengths, min_replicas, averaging_period, expected_op, expected_skip, expected_instance_to_remove):
    metrics_data = copy.deepcopy(mock_metrics_data['block_metrics'])
    
    num_instances = len(queue_lengths)
    instances_for_test = metrics_data[1:1+num_instances]  # Skip 'executor' instance
    current_instances = [inst['instanceId'] for inst in instances_for_test]

    # Adjust instance IDs for the downscale test to be deterministic
    if expected_instance_to_remove:
        instance_ids = [inst['instanceId'] for inst in instances_for_test]
        if expected_instance_to_remove not in instance_ids:
            instances_for_test[-1]['instanceId'] = expected_instance_to_remove
            current_instances[-1] = expected_instance_to_remove
        
        queue_lengths.sort()
        for inst in instances_for_test:
            if inst['instanceId'] == expected_instance_to_remove:
                inst['queue_length_to_assign'] = queue_lengths[0]
            else:
                inst['queue_length_to_assign'] = queue_lengths[1]

    for i, instance in enumerate(instances_for_test):
        instance.setdefault('queue_length', {})
        queue_length_to_set = instance.pop('queue_length_to_assign', queue_lengths[i])
        instance['queue_length'][averaging_period] = queue_length_to_set
        instance['timestamp'] = time.time()  # Set recent timestamp to prevent idle downscale

    get_metrics_mock = MagicMock(return_value={"block_metrics": instances_for_test})

    policy = AIOSv1PolicyRule("test", {'get_metrics': get_metrics_mock}, {
        "queue_up_threshold": 10, 
        "queue_down_threshold": 2,
        "averaging_period": averaging_period,
        "min_replicas": min_replicas
    })
    
    input_data = {"current_instances": current_instances}
    result = policy.eval({}, input_data, {})

    assert result["skip"] == expected_skip
    if not expected_skip:
        assert result["operation"] == expected_op
        if expected_op == "downscale":
            assert result["instances_list"] == [expected_instance_to_remove]
        assert "reason" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
