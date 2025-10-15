#!/usr/bin/env python3
"""
Queue Length Autoscaler Helper Policy

Scales up/down based on rolling average queue length.
"""
import logging
from typing import Dict, Any
import time
import traceback

logging.basicConfig(level=logging.INFO)

class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters
        self.logger = logging.getLogger(f"QueueLengthAutoscalerPolicy-{self.rule_id}")
        self.logger.info("Initializing Queue Length Autoscaler Policy")
        self.queue_up_threshold = self.parameters.get("queue_up_threshold", 10)
        self.queue_down_threshold = self.parameters.get("queue_down_threshold", 2)
        self.idle_time_downscale_threshold = self.parameters.get("idle_time_downscale_threshold", 600) # New: 5 minutes default
        
        # General parameters
        self.min_replicas = self.parameters.get("min_replicas", 1)
        self.averaging_period = self.parameters.get("averaging_period", "average_1m")
        self.cooldown_seconds = self.parameters.get("cooldown_seconds", 120)
        self.max_replicas = self.parameters.get("max_replicas", 3)
        self.allow_downscale_with_jobs = self.parameters.get("allow_downscale_with_jobs", True)
        self.external_cooldown_until = None
        self.last_action_ts = None
        self.logger.info(f"self.parameters: {self.parameters}")

    def _cooldown_ok(self, now):
        if self.last_action_ts is None:
            return True
        return (now - self.last_action_ts) > self.cooldown_seconds

    def _get_queue_length(self, instance: Dict[str, Any]) -> float:
        """Helper to safely extract queue length from metric payload."""
        queue_length_data = instance.get('queue_length', {})
        if isinstance(queue_length_data, dict):
            return queue_length_data.get(self.averaging_period, 0)
        return float(queue_length_data)

    def eval(self, parameters: Dict[str, Any], input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.logger.info(f"Evaluating policy for rule: {self.rule_id}")
            
            # Log the input parameters for debugging
            # self.logger.info(f"Input parameters: {parameters}")
            self.logger.info(f"Input data: {input_data}")
            self.logger.info(f"Context: {context}")

            metrics_collector = self.settings.get('get_metrics')
            if not metrics_collector:
                self.logger.error("get_metrics function not found in settings")
                return {"skip": True, "reason": "Metrics collector not configured."}
            
            metrics = metrics_collector()
            self.logger.info(f"Metrics received: {metrics}")

            current_instances = list(set(input_data.get("current_instances", [])))
            current_instances = [i for i in current_instances if "executor" not in i]
            if not current_instances:
                self.logger.warning("No current instances found. Skipping evaluation.")
                return {"skip": True, "reason": "No current instances provided."}

            # Check if below min replicas and upscale if needed
            if len(current_instances) < self.min_replicas:
                instances_needed = self.min_replicas - len(current_instances)
                reason = f"Current instances ({len(current_instances)}) below min_replicas ({self.min_replicas}). Upscaling by {instances_needed}."
                self.logger.info(f"Min replicas upscale triggered: {reason}")
                self.last_action_ts = time.time()  # Update cooldown
                return {
                    "skip": False,
                    "operation": "upscale",
                    "instances_count": instances_needed,
                    "reason": reason
                }


            block_metrics = metrics.get("block_metrics", [])
            self.logger.info(f"Processing metrics for instances: {current_instances}")

            instances_to_process = [
                inst for inst in block_metrics
                if inst.get('instanceId') in current_instances
            ]

            
            if len(instances_to_process) < len(current_instances):
                missing_instances = set(current_instances) - {inst.get('instanceId') for inst in instances_to_process}
                self.logger.warning(f"Metrics missing for instances: {missing_instances}")
                return {"skip": True, "reason": f"Metrics missing for instances: {missing_instances}"}

            if not instances_to_process:
                self.logger.warning("No metrics found for the specified current_instances.")
                return {"skip": True, "reason": "No metrics found for the specified instances."}

            now = time.time()

            if not self._cooldown_ok(now):
                self.logger.info(f"Cooldown active. Skipping evaluation. Last action at {self.last_action_ts}")
                return {"skip": True, "reason": "Cooldown active."}

            if self.external_cooldown_until and now < self.external_cooldown_until:
                self.logger.info(f"External cooldown active until {self.external_cooldown_until}. Skipping evaluation.")
                return {"skip": True, "reason": "External cooldown active."}

            total_queue_length = 0
            # Track instance-level queue lengths and find max
            instance_queue_lengths = []
            max_queue_instance = None
            max_queue_length = 0
            
            for instance in instances_to_process:
                queue_length_data = instance.get('queue_length', {})
                instance_queue_length = 0
                
                if isinstance(queue_length_data, dict):
                    instance_queue_length = queue_length_data.get(self.averaging_period, 0)
                else:
                    # For compatibility with older metric formats
                    instance_queue_length = queue_length_data
                
                # Track the instance with max queue length
                if instance_queue_length > max_queue_length:
                    max_queue_length = instance_queue_length
                    max_queue_instance = instance.get('instanceId')
                
                instance_queue_lengths.append({
                    "instanceId": instance.get('instanceId'),
                    "queue_length": instance_queue_length
                })
                total_queue_length += instance_queue_length

            instance_count = len(instances_to_process)
            avg_queue_length = total_queue_length / instance_count if instance_count > 0 else 0
            self.logger.info(f"Average queue length across {instance_count} instances: {avg_queue_length:.2f}")
            self.logger.info(f"Maximum queue length: {max_queue_length} on instance {max_queue_instance}")
            
            # Check if average OR any individual instance exceeds threshold
            upscale_needed = avg_queue_length > self.queue_up_threshold or max_queue_length > self.queue_up_threshold
            
            if upscale_needed and instance_count < self.max_replicas:
                reason = []
                if avg_queue_length > self.queue_up_threshold:
                    reason.append(f"Average queue length ({avg_queue_length:.2f}) exceeds threshold ({self.queue_up_threshold})")
                if max_queue_length > self.queue_up_threshold:
                    reason.append(f"Instance {max_queue_instance} queue length ({max_queue_length}) exceeds threshold ({self.queue_up_threshold})")
                
                self.logger.info(f"Upscale triggered: {', '.join(reason)}")
                self.last_action_ts = now
                return {
                    "skip": False,
                    "operation": "upscale",
                    "instances_count": 1,
                    "reason": " and ".join(reason)
                }
            elif upscale_needed:
                self.logger.info(f"Upscale needed but instance count ({instance_count}) is at or above max_replicas ({self.max_replicas}). Skipping upscale.")
            
            if instance_count > self.min_replicas:
                # Find the best candidate for removal
                instances_to_process.sort(key=lambda x: (self._get_queue_length(x), x.get("timestamp", now)))
                candidate = instances_to_process[0]
                candidate_id = candidate.get('instanceId')
                candidate_queue_length = self._get_queue_length(candidate)

                # Condition 1: Low average queue length
                if avg_queue_length < self.queue_down_threshold:
                    if not self.allow_downscale_with_jobs and candidate_queue_length > 0:
                        self.logger.info(f"Downscale skipped: candidate {candidate_id} has jobs.")
                        return {"skip": True, "reason": "Downscale skipped: candidate has jobs."}
                    
                    reason = f"Avg queue ({avg_queue_length:.2f}) < threshold ({self.queue_down_threshold})."
                    self.logger.info(f"Downscale triggered by low queue length: {reason}")
                    self.last_action_ts = now
                    return {"skip": False, "operation": "downscale", "instances_list": [candidate_id], "reason": reason}

                # Condition 2: Instance has been idle for too long
                last_activity_timestamp = candidate.get("llm_last_processed_time", 0)
                idle_duration = now - last_activity_timestamp
                if last_activity_timestamp > 0 and idle_duration > self.idle_time_downscale_threshold:
                    if not self.allow_downscale_with_jobs and candidate_queue_length > 0:
                        self.logger.info(f"Downscale by idleness skipped: Candidate {candidate_id} still has jobs.")
                        return {"skip": True, "reason": "Downscale by idleness skipped: candidate has jobs."}

                    reason = f"Instance {candidate_id} idle for {idle_duration:.0f}s > threshold ({self.idle_time_downscale_threshold}s)."
                    self.logger.info(f"Downscale triggered by idleness: {reason}")
                    self.last_action_ts = now
                    return {"skip": False, "operation": "downscale", "instances_list": [candidate_id], "reason": reason}

            self.logger.info(f"No action needed. Queue length {avg_queue_length:.2f} is within thresholds.")
            return {"skip": True, "reason": "Queue length is within thresholds."}

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during evaluation: {e}")
            self.logger.error(traceback.format_exc())
            # Log the inputs that caused the error
            self.logger.error(f"Error occurred with inputs - parameters: {parameters}, input_data: {input_data}, context: {context}")
            return {"skip": True, "reason": f"An unexpected error occurred: {str(e)}"}

    def management(self, action: str, data: dict) -> dict:
        self.logger.info(f"Management action '{action}' called.")
        if action == "set_external_cooldown":
            duration = data.get("duration", 300)  # default 5 minutes
            self.external_cooldown_until = time.time() + duration
            self.logger.info(f"External cooldown set until {self.external_cooldown_until}")
            return {"status": "ok", "action": action, "cooldown_until": self.external_cooldown_until}
        elif action == "clear_external_cooldown":
            self.external_cooldown_until = None
            self.logger.info("External cooldown cleared.")
            return {"status": "ok", "action": action}
        else:
            return {"status": "not_implemented", "action": action}
