#!/usr/bin/env python3
"""
Test script for the preprocessing policy for chat history summarization.
This script demonstrates how to use the preprocessing policy.
"""

import sys
import os
import json
from types import SimpleNamespace

# Add the necessary paths
current_dir = os.path.dirname(__file__)
root_dir = os.path.join(current_dir, '..')
code_dir = os.path.join(current_dir, 'code')
sys.path.append(root_dir)
sys.path.append(code_dir)

# Import the policy class directly
from code.function import AIOSv1PolicyRule

def create_test_packet(data):
    """Helper function to create test packet"""
    return SimpleNamespace(data=json.dumps(data))

if __name__ == '__main__':
    
    # Test settings
    settings = {
        "external_llm_addr": "CLUSTER1MASTER:31504",
        "external_llm_model_id": "llama4-scout-17b-block",
        "summarize_prompt": "Summarize the following text in a concise manner:",
        "enable_summarization": True
    }
    
    parameters = {}
    
    # Initialize the policy directly
    policy_rule = AIOSv1PolicyRule("test-rule-id", settings, parameters)
    
    # Test Case 1: Simple short message (should not be summarized)
    print("="*80)
    print("TEST CASE 1: Short message preprocessing (no summarization)")
    print("="*80)
    
    simple_packet_data = {
        "mode": "chat",
        "message": "Hello, can you help me with Python?",
        "session_id": "test_session_1"
    }
    
    input_data_1 = {
        "packet": create_test_packet(simple_packet_data)
    }
    
    result_1 = policy_rule.eval(parameters, input_data_1, None)
    print("Input:", simple_packet_data)
    print("Result processed successfully:", result_1 is not None)
    
    # Parse result to see what changed
    try:
        result_packet = result_1.get("packet")
        if hasattr(result_packet, 'data'):
            processed_data = json.loads(result_packet.data)
            print("Processed message:", processed_data.get("message", "")[:200])
        print()
    except:
        print("Result data:", str(result_1)[:200])
        print()
    
    # Test Case 2: Long message (should be summarized)
    print("="*80)
    print("TEST CASE 2: Long message (should be summarized)")
    print("="*80)
    
    context_packet_data = {
        "mode": "chat", 
        "message": "What is a variable in Python? I need to understand how variables work, how to declare them, what types of variables exist, how to assign values to them, and how they differ from constants. Also explain variable naming conventions, scope, and best practices for variable usage in Python programming. Please provide examples and detailed explanations for beginners learning Python programming fundamentals.",
        "session_id": "test_session_2"
    }
    
    input_data_2 = {
        "packet": create_test_packet(context_packet_data)
    }
    
    result_2 = policy_rule.eval(parameters, input_data_2, None)
    print("Input:", context_packet_data)
    print("Result processed successfully:", result_2 is not None)
    
    try:
        result_packet = result_2.get("packet")
        if hasattr(result_packet, 'data'):
            processed_data = json.loads(result_packet.data)
            print("Processed message:", processed_data.get("message", "")[:200])
        print()
    except:
        print("Result data:", str(result_2)[:200])
        print()
    
    # Test Case 3: Batch input format with long content
    print("="*80)
    print("TEST CASE 3: Batch input format with long content")
    print("="*80)
    
    batch_packet_data = {
        "inputs": [
            {
                "mode": "chat",
                "message": "Explain machine learning basics including supervised learning, unsupervised learning, reinforcement learning, neural networks, deep learning, feature engineering, model training, validation, testing, overfitting, underfitting, cross-validation, hyperparameter tuning, and common algorithms like linear regression, logistic regression, decision trees, random forests, support vector machines, and k-means clustering for comprehensive understanding of ML fundamentals.",
                "session_id": "test_session_3"
            }
        ]
    }
    
    input_data_3 = {
        "packet": create_test_packet(batch_packet_data)
    }
    
    result_3 = policy_rule.eval(parameters, input_data_3, None)
    print("Input:", batch_packet_data)
    print("Result processed successfully:", result_3 is not None)
    
    try:
        result_packet = result_3.get("packet")
        if hasattr(result_packet, 'data'):
            processed_data = json.loads(result_packet.data)
            print("Processed message:", processed_data.get("message", "")[:200])
        print()
    except:
        print("Result data:", str(result_3)[:200])
        print()
    
    # Test Case 4: Non-chat mode (should pass through unchanged)
    print("="*80)
    print("TEST CASE 4: Non-chat mode preprocessing")
    print("="*80)
    
    completion_packet_data = {
        "mode": "completion",
        "prompt": "Write a Python function to calculate factorial"
    }
    
    input_data_4 = {
        "packet": create_test_packet(completion_packet_data)
    }
    
    result_4 = policy_rule.eval(parameters, input_data_4, None)
    print("Input:", completion_packet_data)
    print("Result processed successfully:", result_4 is not None)
    print("Should be unchanged for non-chat mode")
    print()
    
    # Test Case 5: Management commands
    print("="*80)
    print("TEST CASE 5: Management commands")
    print("="*80)
    
    # Test get_config
    config_result = policy_rule.management("get_config", {})
    print("Get Config Result:", config_result)
    
    # Test update
    update_data = {
        "enable_summarization": True,
        "summarize_prompt": "Briefly summarize the following content:"
    }
    update_result = policy_rule.management("update", update_data)
    print("Update Result:", update_result)
    
    # Test connection
    connection_result = policy_rule.management("test_connection", {})
    print("Connection Test Result:", connection_result)
    
    # Verify config was updated
    new_config_result = policy_rule.management("get_config", {})
    print("Updated Config:", new_config_result)
    
    # Test Case 6: Test with completion mode (different text field)
    print("="*80)
    print("TEST CASE 6: Completion mode with long prompt")
    print("="*80)
    
    completion_data = {
        "mode": "completion",
        "prompt": "Write a comprehensive guide on Python web development covering Flask, Django, FastAPI, database integration with SQLAlchemy, RESTful API design, authentication and authorization, deployment strategies, performance optimization, testing methodologies, security best practices, and modern development workflows including containerization with Docker and continuous integration/continuous deployment pipelines."
    }
    
    input_data_6 = {
        "packet": create_test_packet(completion_data)
    }
    
    result_6 = policy_rule.eval(parameters, input_data_6, None)
    print("Input:", completion_data["prompt"][:100] + "...")
    print("Result processed successfully:", result_6 is not None)
    
    try:
        result_packet = result_6.get("packet")
        if hasattr(result_packet, 'data'):
            processed_data = json.loads(result_packet.data)
            if "_summarized" in processed_data:
                print("Text was summarized:", processed_data["_summarized"])
                print("Summary:", processed_data.get("_summary", "")[:200] + "...")
            else:
                print("Text was not summarized")
        print()
    except Exception as e:
        print(f"Error processing result: {e}")
        print()
    
    print("="*80)
    print("All preprocessing policy tests completed!")
    print("="*80)
