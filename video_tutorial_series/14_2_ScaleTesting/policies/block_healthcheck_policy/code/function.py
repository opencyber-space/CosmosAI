#!/usr/bin/env python3
"""
Block Health Checker Policy

This policy evaluates the health of block instances according to the block.md specification.
It tracks consecutive failures and calls failure policy when threshold is exceeded.
"""

import logging
import time
import requests
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlockHealthCheckerPolicy")

def call_reassign_from_allocator_policy(GATEWAY_URL:str, CLUSTER_ID: str, BLOCK_ID: str, INSTANCE_ID: str):
    """
    Call failure policy server as specified in block.md documentation
    """
    try:
        url = f"http://{GATEWAY_URL}/controller/reassign-instance/{CLUSTER_ID}"
        payload = {
            "blockId": BLOCK_ID,
            "instanceId": INSTANCE_ID,
            "extra_data": {
            }
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return {"success": False, "message": str(e)}
    except Exception as ex:
        logging.error(f"Unexpected error: {ex}")
        return {"success": False, "message": str(ex)}

class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
        """
        Initializes the Block Health Checker Policy
        
        Args:
            rule_id (str): Unique identifier for the rule
            settings (dict): Configuration settings
            parameters (dict): Parameters for the rule
        """
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters
        
        
        self.gateway_url = self.settings.get("GATEWAY_URL", "MANAGEMENTMASTER:30600")
        self.call_dummy_reassign_policy = self.settings.get("call_dummy_reassign_policy", False)

        # Counter to track consecutive failures per instance
        self.counter = {}
        
        # Failure threshold - configurable via parameters
        self.failure_threshold = parameters.get("failure_threshold", 3)
        
        logger.info(f"Block Health Checker Policy initialized: {rule_id}")
        logger.info(f"Failure threshold: {self.failure_threshold}")

    def eval(self, parameters, input_data, context):
        """
        Evaluates the policy rule according to block.md specification
        
        Args:
            parameters (dict): The current parameters
            input_data (dict): Input data containing health_check_data
            context (dict): Context for storing state across runs
            
        Returns:
            dict: Empty dict as per block.md specification
        """
        try:
            logger.warning(f"input_data : {input_data}")
            # Extract health check data as per block.md format
            health_check_data = input_data.get("health_check_data", {})
            # Block and cluster data from settings
            block_data = input_data.get("block_data", {})
            cluster_data = input_data.get("cluster_data", {})
            
            # Process each instance's health status
            for instance, is_healthy in health_check_data.items():
                if not is_healthy:
                    # Increment failure counter for unhealthy instances
                    self.counter[instance] = self.counter.get(instance, 0) + 1
                    
                    logger.warning(f"Instance {instance} unhealthy. Failure count: {self.counter[instance]}")
                    
                    # Check if failure threshold exceeded
                    if self.counter[instance] > self.failure_threshold:
                        logger.error(f"Instance {instance} exceeded failure threshold. Calling failure policy.")
                        
                        # Call failure policy as specified in block.md
                        if not self.call_dummy_reassign_policy:
                            call_reassign_from_allocator_policy(
                                GATEWAY_URL=self.gateway_url, 
                                CLUSTER_ID=cluster_data["id"],
                                BLOCK_ID=block_data["id"],
                                INSTANCE_ID=instance
                            )
                        
                        # Reset counter after calling failure policy
                        self.counter[instance] = 0
                else:
                    # Reset counter for healthy instances
                    if instance in self.counter:
                        self.counter[instance] = 0
            
            # Return empty dict as per block.md specification
            return {}
            
        except Exception as e:
            logger.error(f"Error in health checker policy: {str(e)}")
            return {}

    def management(self, action: str, data: dict = None) -> dict:
        """
        Management interface for the health checker policy
        
        Args:
            action (str): Management action to perform
            data (dict): Optional data for the action
            
        Returns:
            dict: Management result
        """
        data = data or {}
        
        if action == "get_status":
            # Return basic status information
            unhealthy_instances = [instance for instance, count in self.counter.items() if count > 0]
            
            return {
                "rule_id": self.rule_id,
                "failure_threshold": self.failure_threshold,
                "total_instances": len(self.counter),
                "unhealthy_instances": unhealthy_instances,
                "failure_counts": dict(self.counter)
            }
        
        elif action == "reset_counters":
            # Reset all failure counters
            self.counter = {}
            return {
                "success": True,
                "message": "All failure counters reset"
            }
        
        elif action == "reset_instance":
            # Reset specific instance counter
            instance_id = data.get("instance_id")
            if instance_id and instance_id in self.counter:
                self.counter[instance_id] = 0
                return {
                    "success": True,
                    "message": f"Counter reset for instance {instance_id}"
                }
            return {
                "success": False,
                "error": "Instance not found or invalid instance_id"
            }
        
        else:
            return {
                "success": False,
                "error": f"Unknown management action: {action}"
            }
