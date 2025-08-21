#!/usr/bin/env python3
"""
Input/Output Tokens Autoscaler Helper Policy

Scales up/down based on rolling average input/output tokens per minute.
"""
import logging
import time
from typing import Dict, Any

# Configure logger
logging.basicConfig(level=logging.INFO)

class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters
        self.logger = logging.getLogger(f"TokensAutoscalerPolicy-{self.rule_id}")
        self.logger.info("Initializing Tokens Autoscaler Policy")
        
        self.input_up_threshold = self.parameters.get("input_tokens_up_threshold", 500)
        self.output_up_threshold = self.parameters.get("output_tokens_up_threshold", 300)
        self.input_down_threshold = self.parameters.get("input_tokens_down_threshold", 100)
        self.output_down_threshold = self.parameters.get("output_tokens_down_threshold", 50)
        
        self.min_replicas = self.parameters.get("min_replicas", 1)
        self.averaging_period = self.parameters.get("averaging_period", "average_1m")
        self.cooldown_seconds = self.parameters.get("cooldown_seconds", 120)
        self.last_action_ts = None
        
    def _cooldown_ok(self, now):
        if self.last_action_ts is None:
            return True
        return (now - self.last_action_ts) > self.cooldown_seconds

    def eval(self, parameters: Dict[str, Any], input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.logger.info(f"Evaluating policy with parameters: {self.parameters}")

            metrics_collector = self.settings.get('get_metrics')
            if not callable(metrics_collector):
                self.logger.error("get_metrics function not found in settings")
                return {"skip": True, "reason": "Metrics collector not configured."}

            metrics = metrics_collector()
            self.logger.info(f"Metrics received: {metrics}")

            current_instances = input_data.get("current_instances")
            if not current_instances:
                self.logger.warning("No current instances provided. Skipping evaluation.")
                return {"skip": True, "reason": "No current instances provided."}

            self.logger.info(f"Processing metrics for instances: {current_instances}")
            
            block_metrics = metrics.get("block_metrics", [])
            now = time.time()

            # Filter metrics for current instances
            instances_to_process = [
                inst for inst in block_metrics
                if inst.get('instanceId') in current_instances
            ]

            if not instances_to_process:
                self.logger.warning("No metrics found for the specified current_instances.")
                return {"skip": True, "reason": "No metrics found for the specified instances."}

            total_input_tokens = 0
            total_output_tokens = 0
            
            for instance in instances_to_process:
                input_tokens_metrics = instance.get('llm_input_tokens_per_minute_rolling', {})
                output_tokens_metrics = instance.get('llm_output_tokens_per_minute_rolling', {})
                
                total_input_tokens += input_tokens_metrics.get(self.averaging_period, 0)
                total_output_tokens += output_tokens_metrics.get(self.averaging_period, 0)

            instance_count = len(instances_to_process)
            avg_input_tokens = total_input_tokens / instance_count
            avg_output_tokens = total_output_tokens / instance_count
            
            self.logger.info(f"Average Input Tokens: {avg_input_tokens}, Average Output Tokens: {avg_output_tokens}")

            if not self._cooldown_ok(now):
                self.logger.info(f"Cooldown active. Skipping evaluation. Last action at {self.last_action_ts}")
                return {"skip": True, "reason": "Cooldown active."}

            # Upscale logic
            if avg_input_tokens > self.input_up_threshold or avg_output_tokens > self.output_up_threshold:
                self.last_action_ts = now
                reason = f"Token rate exceeded threshold (Input: {avg_input_tokens:.2f}, Output: {avg_output_tokens:.2f})"
                self.logger.info(f"{reason}. Scaling up.")
                return {
                    "skip": False,
                    "operation": "upscale",
                    "instances_count": 1,
                    "reason": reason
                }
            
            # Downscale logic
            if avg_input_tokens < self.input_down_threshold and avg_output_tokens < self.output_down_threshold:
                if instance_count > self.min_replicas:
                    self.last_action_ts = now
                    
                    # Find the instance with the lowest combined token rate to remove
                    instances_to_process.sort(key=lambda x: 
                        x.get('llm_input_tokens_per_minute_rolling', {}).get(self.averaging_period, 0) +
                        x.get('llm_output_tokens_per_minute_rolling', {}).get(self.averaging_period, 0)
                    )
                    
                    instance_to_remove = instances_to_process[0].get('instanceId') if instances_to_process else None
                    
                    if instance_to_remove:
                        reason = f"Token rate below threshold (Input: {avg_input_tokens:.2f}, Output: {avg_output_tokens:.2f})"
                        self.logger.info(f"{reason}. Scaling down. Removing instance {instance_to_remove}")
                        return {
                            "skip": False,
                            "operation": "downscale",
                            "instances_list": [instance_to_remove],
                            "reason": reason
                        }

            self.logger.info("No scaling action required at this time.")
            return {"skip": True, "reason": "No scaling action required."}

        except Exception as e:
            self.logger.exception(f"An unexpected error occurred during evaluation: {e}")
            return {"skip": True, "reason": f"An error occurred: {e}"}

    def management(self, action: str, data: dict) -> dict:
        self.logger.info(f"Management action received: {action} with data: {data}")
        try:
            if action == "update_thresholds":
                updated = False
                if "input_up_threshold" in data:
                    self.input_up_threshold = data["input_up_threshold"]
                    updated = True
                if "output_up_threshold" in data:
                    self.output_up_threshold = data["output_up_threshold"]
                    updated = True
                if "input_down_threshold" in data:
                    self.input_down_threshold = data["input_down_threshold"]
                    updated = True
                if "output_down_threshold" in data:
                    self.output_down_threshold = data["output_down_threshold"]
                    updated = True
                if "min_replicas" in data:
                    self.min_replicas = max(1, data["min_replicas"])
                    updated = True
                if "cooldown_seconds" in data:
                    self.cooldown_seconds = max(0, data["cooldown_seconds"])
                    updated = True
                
                if updated:
                    self.logger.info(f"Thresholds updated: {data}")
                    return {
                        "status": "ok",
                        "message": "Thresholds updated successfully",
                        "current_config": {
                            "input_up_threshold": self.input_up_threshold,
                            "output_up_threshold": self.output_up_threshold,
                            "input_down_threshold": self.input_down_threshold,
                            "output_down_threshold": self.output_down_threshold,
                            "min_replicas": self.min_replicas,
                            "cooldown_seconds": self.cooldown_seconds
                        }
                    }
                else:
                    return {"status": "error", "reason": "No valid threshold parameters provided"}
            
            elif action == "reset_cooldown":
                self.last_action_ts = None
                self.logger.info("Cooldown timer reset")
                return {"status": "ok", "message": "Cooldown timer reset successfully"}
        except Exception as e:
            self.logger.exception(f"Error in management action '{action}': {e}")
            return {"status": "not_implemented", "action": action}
