import random
import logging
from typing import Dict, Any

class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
        """
        Initializes the Token-Based Distribution Policy.

        Args:
            rule_id (str): Unique identifier for the rule.
            settings (dict): Configuration settings for the rule.
            parameters (dict): Parameters defining the rule's behavior.
        """
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters
        self.logger = logging.getLogger(f"TokenBasedDistributionPolicy-{self.rule_id}")

        # Weights for token calculation
        self.output_token_weight = self.parameters.get("output_token_weight", 0.9)
        self.input_token_weight = self.parameters.get("input_token_weight", 0.1)
        self.averaging_period = self.parameters.get("averaging_period", "average_1m")
        self.allow_random_fallback = self.parameters.get("allow_random_fallback", True)

        self.metrics_function = self.settings.get("get_metrics")
        self.block_data = self.settings.get("block_data")
        self.cluster_data = self.settings.get("cluster_data")
        
        self.session_ids_cache = {}
        self.current_instances = []

    def _calculate_weighted_tokens(self, instance_metrics: Dict[str, Any]) -> float:
        """Calculates the weighted token score for an instance."""
        input_tokens_rolling = instance_metrics.get("llm_input_tokens_per_minute_rolling", {})
        output_tokens_rolling = instance_metrics.get("llm_output_tokens_per_minute_rolling", {})

        input_tokens = input_tokens_rolling.get(self.averaging_period, 0)
        output_tokens = output_tokens_rolling.get(self.averaging_period, 0)

        return (self.input_token_weight * input_tokens) + (self.output_token_weight * output_tokens)

    def _select_instance(self) -> str:
        """Selects the best instance based on token metrics."""
        if not self.current_instances:
            self.logger.warning("No instances available for routing.")
            return None

        current_metrics = self.metrics_function()
        block_metrics = current_metrics.get("block_metrics", [])
        
        instance_scores = {}
        if block_metrics:
            self.logger.info(f"Calculating scores for instances with metrics: {self.current_instances}")
            for instance_metric in block_metrics:
                instance_id = instance_metric.get("instanceId")
                if instance_id and instance_id in self.current_instances:
                    score = self._calculate_weighted_tokens(instance_metric)
                    instance_scores[instance_id] = score
                    self.logger.info(f"  - Instance '{instance_id}': score = {score:.2f}")

        if not instance_scores:
            self.logger.warning("No instance scores calculated from metrics.")
            if self.allow_random_fallback and self.current_instances:
                chosen_instance = random.choice(self.current_instances)
                self.logger.info(f"Randomly selected instance: '{chosen_instance}' as fallback is enabled.")
                return chosen_instance
            else:
                self.logger.warning("Cannot select an instance: No scores and random fallback is disabled or no instances available.")
                return None
        else:
            # Choose the instance with the lowest score from the ones that had metrics
            chosen_instance = min(instance_scores, key=instance_scores.get)
            self.logger.info(f"Final scores: {instance_scores}. Chosen instance with lowest score: '{chosen_instance}'")
            return chosen_instance

    def eval(self, parameters: Dict[str, Any], input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates the policy to select an instance based on weighted token metrics.
        """
        self.logger.info(f"Starting token-based distribution evaluation. Input data keys: {list(input_data.keys())}")
        try:
            if not callable(self.metrics_function):
                self.logger.error("'get_metrics' function not found. Cannot determine instances or metrics.")
                return {"instance_id": None, "reason": "Metrics function not configured."}
            
            # The instance list is provided in the input data for load balancing
            latest_instances = input_data.get("instances", [])

            if set(latest_instances) != set(self.current_instances):
                self.logger.info(f"Instance list changed from {self.current_instances} to {latest_instances}. Updating session cache.")
                
                # Instead of clearing the whole cache, remove only stale entries
                stale_sessions = [
                    session_id for session_id, instance_id in self.session_ids_cache.items()
                    if instance_id not in latest_instances
                ]
                
                if stale_sessions:
                    self.logger.info(f"Removing stale sessions from cache: {stale_sessions}")
                    for session_id in stale_sessions:
                        del self.session_ids_cache[session_id]

                self.current_instances = latest_instances

            if not self.current_instances:
                self.logger.warning("No instances available for routing.")
                return {"instance_id": None, "reason": "No available instances."}

            packet = input_data.get("packet")
            if packet:
                session_id = getattr(packet, "session_id", None)
                if session_id and session_id in self.session_ids_cache:
                    cached_instance = self.session_ids_cache[session_id]
                    if cached_instance in self.current_instances:
                        self.logger.info(f"Session '{session_id}' found in cache. Routing to instance '{cached_instance}'.")
                        return {"instance_id": cached_instance}
                    else:
                        self.logger.info(f"Cached instance '{cached_instance}' for session '{session_id}' is no longer active. Removing from cache.")
                        del self.session_ids_cache[session_id]

            # Select the best instance using the refactored helper method
            chosen_instance = self._select_instance()

            if not chosen_instance:
                self.logger.error("Failed to select an instance.")
                return {"instance_id": None, "reason": "Instance selection failed."}

            if packet and getattr(packet, "session_id", None):
                session_id = packet.session_id
                self.logger.info(f"Caching session '{session_id}' to instance '{chosen_instance}'.")
                self.session_ids_cache[session_id] = chosen_instance

            return {"instance_id": chosen_instance}

        except Exception as e:
            self.logger.exception(f"An unexpected error occurred during evaluation: {e}")
            # Fallback to random choice on error to maintain availability
            if self.current_instances and self.allow_random_fallback:
                chosen_instance = random.choice(self.current_instances)
                self.logger.warning(f"Error occurred. Falling back to random instance: {chosen_instance}")
                return {"instance_id": chosen_instance}
            
            return {"instance_id": None, "reason": "An error occurred and random fallback is disabled."}

    def management(self, action: str, data: dict) -> dict:
        """
        Executes a custom management command.
        """
        self.logger.info(f"Management action received: {action} with data: {data}")
        if action == "health_check":
            return {"instances": self.current_instances, "status": "healthy"}
        elif action == "get_current_mapping":
            return {"mapping": self.session_ids_cache}
        elif action == "assign_streaming":
            session_id = data.get("session_id")
            latest_instances = data.get("instances", [])
            if set(latest_instances) != set(self.current_instances):
                self.logger.info(f"Instance list changed from {self.current_instances} to {latest_instances}. Updating session cache.")
                
                # Instead of clearing the whole cache, remove only stale entries
                stale_sessions = [
                    session_id for session_id, instance_id in self.session_ids_cache.items()
                    if instance_id not in latest_instances
                ]
                
                if stale_sessions:
                    self.logger.info(f"Removing stale sessions from cache: {stale_sessions}")
                    for session_id in stale_sessions:
                        del self.session_ids_cache[session_id]

                self.current_instances = latest_instances

            if not session_id:
                self.logger.error("'session_id' not provided for 'assign_streaming' action.")
                return {"status": "error", "reason": "session_id is required."}

            # If session is already cached, return the existing instance
            if session_id in self.session_ids_cache:
                cached_instance = self.session_ids_cache[session_id]
                if cached_instance in self.current_instances:
                    self.logger.info(f"Session '{session_id}' already assigned to '{cached_instance}'.")
                    return {"instance_id": cached_instance, "status": "ok"}
                else:
                    self.logger.info(f"Cached instance '{cached_instance}' for session '{session_id}' is no longer active. Re-assigning.")
                    del self.session_ids_cache[session_id]

            # Select the best available instance
            chosen_instance = self._select_instance()

            if chosen_instance:
                self.logger.info(f"Pre-allocating instance '{chosen_instance}' for streaming session '{session_id}'.")
                self.session_ids_cache[session_id] = chosen_instance
                return {"instance_id": chosen_instance, "status": "ok"}
            else:
                self.logger.error(f"Failed to select an instance for session '{session_id}'.")
                return {"instance_id": None, "status": "error", "reason": "Instance selection failed."}

        self.logger.warning(f"Unknown management action received: {action}")
        return {"status": "unknown_action", "reason": f"Action '{action}' is not supported."}
