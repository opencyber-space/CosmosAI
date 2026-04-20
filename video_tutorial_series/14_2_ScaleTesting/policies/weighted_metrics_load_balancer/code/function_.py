#!/usr/bin/env python3
"""
Weighted Metrics Load Balancer Helper Policy

Routes requests to instances based on weighted combination of multiple metrics:
- Active sessions
- Queue length
- Latency
- Optional: Tokens/second, memory usage, etc.

Uses weighted scoring to select the optimal instance for load balancing.
"""
import logging
from typing import Dict, Any, List
import traceback
import heapq
import random
from collections import defaultdict
import time

logging.basicConfig(level=logging.INFO)

class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters
        self.logger = logging.getLogger(f"WeightedMetricsLBPolicy-{self.rule_id}")
        self.logger.info("Initializing Weighted Metrics Load Balancer Policy")
        self.logger.info(f"Settings: {self.settings}")
        # Configuration parameters
        self.averaging_period = self.parameters.get("averaging_period", "average_1m")
        self.tie_breaker = self.parameters.get("tie_breaker", "round_robin")  # Options: first, round_robin
        self.round_robin_index = 0
        self.selection_mode = self.parameters.get("selection_mode", "weighted")  # Options: weighted, equal

        # Weights for different metrics (should sum to 1.0)
        self.weights = self.parameters.get("weights", {
            "active_sessions": 0.5,
            "queue_length": 0.5,
            "latency": 0.0,
            "requested_tokens_per_second": 0.0  # Disabled for queue/sessions focus
        })

        default_metric_configs = {
            "active_sessions": {"max_threshold": 100, "invert_score": True},
            "queue_length": {"max_threshold": 1000, "invert_score": True},
            "latency": {"max_threshold": 5000, "invert_score": True},
            "tokens_per_second": {"max_threshold": 100, "invert_score": False},
            "requested_tokens_per_second": {"max_threshold": 100, "invert_score": False},
            "memory_usage_percent": {"max_threshold": 90, "invert_score": True}
        }
        
        self.metric_configs = parameters.get("metric_configs", default_metric_configs)
        
        # Ensure all metrics in weights have configs
        for metric_name in self.weights.keys():
            if metric_name not in self.metric_configs:
                self.logger.warning(f"Metric '{metric_name}' not in metric_configs, adding default config")
                self.metric_configs[metric_name] = default_metric_configs.get(metric_name, {
                    "max_threshold": 100, 
                    "invert_score": False
                })

        # User preference settings for response characteristics
        self.user_preference_config = self.parameters.get("user_preference_config", {
            "response_speed_preference": "balanced",  # Options: fast, balanced, thoughtful
            "fast_threshold": 50,      # tokens/sec above this = fast
            "thoughtful_threshold": 20  # tokens/sec below this = thoughtful
        })

        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            self.logger.warning(f"Weights don't sum to 1.0 (current: {total_weight}), normalizing...")
            for key in self.weights:
                self.weights[key] /= total_weight

        self.logger.info(f"Using weights: {self.weights}")

        # Session caching for performance optimization
        self.session_ids_cache = {}
        self.session_task_counts = {}  # Track number of tasks per session
        self.session_timeout_seconds = self.parameters.get("session_timeout_seconds", 3600)  # 1 hour default
        self.session_timestamps = {}  # Track timestamps for session timeout
        self.current_instances = []
        self.previous_instances = []
        self.redistribution_percentage = self.parameters.get("redistribution_percentage", 0.2)
        self.redistribution_interval = self.parameters.get("redistribution_interval", 300)  # 5 minutes default
        self.redistribution_selection_mode = self.parameters.get("redistribution_selection_mode", "least_loaded")  # Options: random, best
        self.imbalance_threshold = self.parameters.get("imbalance_threshold", 10)  # Skip redistribution if max-min sessions <= threshold
        self.overload_threshold_percentage = self.parameters.get("overload_threshold_percentage", 0.2)  # Percentage above average to be overloaded
        self.last_redistribution_time = time.time()
        self.logger.info(f"self.parameters: {self.parameters}")

        # New: metrics polling interval and caching to avoid calling get_metrics on every eval
        self.metrics_interval = self.parameters.get("metrics_interval", 60)  # seconds
        self.task_imbalance_threshold = self.parameters.get("task_imbalance_threshold", 100) # For sessions
        self.last_metrics_time = 0
        self.cached_metrics = None

    def eval(self, parameters: Dict[str, Any], input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            start = time.time()
            self.logger.info(f"Evaluating policy for rule: {self.rule_id}")

            # Log the input parameters for debugging
            # self.logger.info(f"Input parameters: {parameters}")
            self.logger.info(f"Input data: {input_data}")
            self.logger.info(f"Context: {context}")

            # Clean up stale sessions based on timeout
            self._cleanup_stale_sessions()

            # Determine latest instances early so we can decide whether to refresh metrics
            latest_instances = list(set(input_data.get("instances", [])))
            latest_instances = [i for i in latest_instances if "executor" not in i]
            # Check if redistribution is needed to ensure fresh metrics
            current_time = time.time()
            redistribution_needed = False
            if set(latest_instances) != set(self.current_instances):
                redistribution_needed = True
            elif current_time - self.last_redistribution_time > self.redistribution_interval:
                redistribution_needed = True

            metrics_collector = self.settings.get('get_metrics')
            if not metrics_collector:
                self.logger.warning("get_metrics function not found in settings. Using fallback selection.")
                
                # Fallback: Select first available instance
                available_instances = input_data.get("instances", self.current_instances)
                if available_instances:
                    selected_instance = available_instances[0]
                    self.logger.info(f"Fallback selection: {selected_instance} (first available instance)")
                    return {
                        "instance_id": selected_instance,
                        "reason": "Fallback: Metrics collector not configured, selected first instance"
                    }
                else:
                    self.logger.error("No instances available for fallback selection")
                    return {"instance_id": None, "reason": "No instances available"}

            # Decide whether to fetch fresh metrics: if cached missing, interval expired, or instance list changed
            need_fetch = False
            if redistribution_needed:
                need_fetch = True
            if self.cached_metrics is None:
                need_fetch = True
            elif (current_time - self.last_metrics_time) > self.metrics_interval:
                need_fetch = True
            elif set(latest_instances) != set(self.current_instances):
                need_fetch = True

            if need_fetch:
                try:
                    metrics = metrics_collector()
                    if metrics:
                        self.cached_metrics = metrics
                    else:
                        self.logger.warning("Metrics collector returned empty metrics, using cached metrics if available.") 
                    self.last_metrics_time = time.time()
                    self.logger.info("Fetched fresh metrics from metrics_collector")
                except Exception as e:
                    self.logger.warning(f"Failed to fetch metrics: {e}. Using cached metrics if available.")
                    metrics = self.cached_metrics or {}
            else:
                metrics = self.cached_metrics or {}

            temp_time = time.time() - start
            self.logger.info(f"Policy metrics received time taken: {temp_time:.4f} seconds")
            # self.logger.info(f"Metrics received: {metrics}")
            # self.logger.info(f"Metrics received: {metrics_print}")
            # Get block metrics early for redistribution
            block_metrics = metrics.get("block_metrics", [])

            # Get available instances - support both formats for compatibility
            # latest_instances = list(set(input_data.get("instances", [])))
            
            # Update instance list if changed
            if set(latest_instances) != set(self.current_instances):
                new_instances = [inst for inst in latest_instances if inst not in self.previous_instances]
                self.previous_instances = self.current_instances.copy()
                self.current_instances = latest_instances
                self.logger.info(f"Updated current instances to: {self.current_instances}")
                if new_instances:
                    self.logger.info(f"New instances added: {new_instances}, triggering redistribution")
                    start_2 = time.time()
                    self._redistribute_sessions( block_metrics)
                    self.logger.info(f"Redistribution time taken: {time.time() - start_2:.4f} seconds")
                    self.last_redistribution_time = time.time()
            elif current_time - self.last_redistribution_time > self.redistribution_interval:
                self.logger.info("Periodic redistribution triggered")
                start_2 = time.time()
                self._redistribute_sessions( block_metrics)
                self.logger.info(f"Redistribution time taken: {time.time() - start_2:.4f} seconds")
                self.last_redistribution_time = time.time()

            if not self.current_instances:
                self.logger.warning("No instances available for routing.")
                return {"instance_id": None, "reason": "No available instances."}

            # Check for cached session
            packet = input_data.get("packet")
            if packet:
                session_id = getattr(packet, "session_id", None)
                if session_id and session_id in self.session_ids_cache:
                    cached_instance = self.session_ids_cache[session_id]
                    if cached_instance in self.current_instances:
                        self.logger.info(f"Session '{session_id}' found in cache. Routing to instance '{cached_instance}'.")
                        self.session_task_counts[session_id] = self.session_task_counts.get(session_id, 0) + 1
                        self.session_timestamps[session_id] = time.time()
                        return {"instance_id": cached_instance}
                    else:
                        self.logger.info(f"Cached instance '{cached_instance}' for session '{session_id}' is no longer active. Re-assigning.")
                        del self.session_ids_cache[session_id]
                        if session_id in self.session_task_counts:
                            del self.session_task_counts[session_id]
                        if session_id in self.session_timestamps:
                            del self.session_timestamps[session_id]

            # Get available instances for metric calculation
            available_instances = self.current_instances
            if not available_instances:
                self.logger.warning("No available instances found in input_data")
                return {"instance_id": None, "reason": "No available instances"}

            # Get block metrics for available instances
            instances_with_metrics = [
                inst for inst in block_metrics
                if inst.get('instanceId') in available_instances
            ]

            if not instances_with_metrics:
                self.logger.warning("No metrics found for available instances")
                return {"instance_id": None, "reason": "No metrics for instances"}

            if self.selection_mode == "equal":
                start_3 = time.time()
                self.logger.info("Using equal mode for instance selection")
                # Select based on least queue length for equal distribution
                instance_queue_lengths = {}
                for inst in instances_with_metrics:
                    instance_id = inst.get('instanceId')
                    queue_length = self._get_metric_value(inst, 'queue_length', input_data)
                    instance_queue_lengths[instance_id] = queue_length
                
                self.logger.info(f"Queue lengths for selection: {instance_queue_lengths}")
                
                min_queue = min(instance_queue_lengths.values())
                candidates = [inst_id for inst_id, ql in instance_queue_lengths.items() if ql == min_queue]
                
                if len(candidates) > 1:
                    self.logger.info(f"Found {len(candidates)} instances with same queue length ({min_queue}), applying tie-breaking")
                    selected_instance = self._apply_tie_breaker_for_equal(candidates)
                else:
                    selected_instance = candidates[0]
                
                selected_metrics = self._extract_metrics(next(inst for inst in instances_with_metrics if inst['instanceId'] == selected_instance), input_data)
                self.logger.info(f"Selected instance {selected_instance} for equal distribution (queue length: {min_queue})")
                self.logger.info(f"Selected instance metrics: {selected_metrics}")
                self.logger.info(f"Equal mode selection time taken: {time.time() - start_3:.4f} seconds")
            else:
                start_4 = time.time()
                self.logger.info("Using weighted mode for instance selection")
                # Calculate weighted scores for each instance
                instance_scores = []
                for instance in instances_with_metrics:
                    score = self._calculate_weighted_score(instance, input_data)
                    instance_scores.append({
                        "instanceId": instance.get('instanceId'),
                        "weighted_score": score,
                        "metrics": self._extract_metrics(instance, input_data)
                    })

                self.logger.info(f"Instance scores for selection: {[(i['instanceId'], i['weighted_score']) for i in instance_scores]}")
                
                # Select the instance with the highest weighted score (higher is better)
                best_instance_data = max(instance_scores, key=lambda x: x["weighted_score"])
                best_score = best_instance_data["weighted_score"]
                candidates = [i for i in instance_scores if abs(i["weighted_score"] - best_score) < 0.001]

                if len(candidates) > 1:
                    self.logger.info(f"Found {len(candidates)} instances with similar scores ({best_score:.4f}), applying tie-breaking")
                    selected_instance = self._apply_tie_breaker(candidates)
                else:
                    selected_instance = best_instance_data["instanceId"]

                selected_metrics = next(i["metrics"] for i in instance_scores if i["instanceId"] == selected_instance)
                self.logger.info(f"Selected instance {selected_instance} with best weighted score: {best_score:.4f}")
                self.logger.info(f"Selected instance metrics: {selected_metrics}")
                self.logger.info(f"Weighted mode selection time taken: {time.time() - start_4:.4f} seconds")


            # Cache the session if packet has session_id
            if packet and getattr(packet, "session_id", None):
                session_id = packet.session_id
                self.logger.info(f"Caching session '{session_id}' to instance '{selected_instance}'.")
                self.session_ids_cache[session_id] = selected_instance
                self.session_task_counts[session_id] = self.session_task_counts.get(session_id, 0) + 1
                self.session_timestamps[session_id] = time.time()  # Record timestamp for timeout
            time_taken = time.time() - start
            self.logger.info(f"Policy evaluation time taken: {time_taken:.4f} seconds")
            return {"instance_id": selected_instance}

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during evaluation: {e}")
            self.logger.error(traceback.format_exc())
            # Log the inputs that caused the error
            self.logger.error(f"Error occurred with inputs - parameters: {parameters}, input_data: {input_data}, context: {context}")
            return {"instance_id": None, "reason": f"Error: {str(e)}"}

    def _calculate_weighted_score(self, instance: Dict[str, Any], input_data: Dict[str, Any]) -> float:
        """
        Calculate weighted score for an instance based on multiple metrics.
        Lower score is better.
        """
        total_score = 0.0
        instance_id = instance.get('instanceId')

        for metric_name, weight in self.weights.items():
            if metric_name not in self.metric_configs:
                self.logger.warning(f"Metric {metric_name} not configured, skipping")
                continue

            raw_value = self._get_metric_value(instance, metric_name, input_data)
            normalized_score = self._normalize_metric(raw_value, metric_name)
            weighted_contribution = normalized_score * weight

            total_score += weighted_contribution
            self.logger.info(f"Instance {instance_id} - {metric_name}: raw={raw_value}, normalized={normalized_score:.4f}, weighted={weighted_contribution:.4f}")

        return total_score

    def _get_metric_value(self, instance: Dict[str, Any], metric_name: str, input_data: Dict[str, Any] = None) -> float:
        """
        Extract metric value from instance data.
        """
        if input_data is None:
            input_data = {}
        
        if metric_name == "active_sessions":
            return instance.get('llm_active_sessions', 0)
        elif metric_name == "queue_length":
            queue_data = instance.get('queue_length', {})
            if isinstance(queue_data, dict):
                return queue_data.get(self.averaging_period, 0)
            return queue_data
        elif metric_name == "latency":
            latency_data = instance.get('latency', {})
            if isinstance(latency_data, dict):
                return latency_data.get(self.averaging_period, 0)
            return latency_data
        elif metric_name == "tokens_per_second":
            return instance.get('llm_tokens_per_second', 0)
        elif metric_name == "requested_tokens_per_second":
            return self._calculate_requested_tokens_score(instance, input_data)
        elif metric_name == "memory_usage_percent":
            memory_data = instance.get('hardware', {}).get('memory', {})
            return memory_data.get('averageUtil', 0)
        elif metric_name == "cpu_usage_percent":
            cpu_data = instance.get('hardware', {}).get('cpu', {})
            return cpu_data.get('percent', 0)
        elif metric_name == "gpu_usage_percent":
            gpu_data = instance.get('hardware', {}).get('gpus', [])
            if gpu_data:
                return gpu_data[0].get('utilization', 0)
            return 0
        else:
            self.logger.warning(f"Unknown metric: {metric_name}")
            return 0

    def _normalize_metric(self, raw_value: float, metric_name: str) -> float:
        """
        Normalize metric value to 0-1 scale.
        For metrics where lower is better, invert the score.
        """
        config = self.metric_configs.get(metric_name, {})
        max_threshold = config.get("max_threshold", 100)
        invert_score = config.get("invert_score", False)

        # Clamp value to threshold
        clamped_value = min(raw_value, max_threshold)

        # Normalize to 0-1 scale
        if max_threshold > 0:
            normalized = clamped_value / max_threshold
        else:
            normalized = 0.0

        # Invert for metrics where lower is better (higher normalized score = better)
        if invert_score:
            normalized = 1.0 - normalized

        return normalized

    def _extract_metrics(self, instance: Dict[str, Any], input_data: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Extract all relevant metrics for logging/debugging.
        """
        if input_data is None:
            input_data = {}
        metrics = {}
        for metric_name in self.weights.keys():
            metrics[metric_name] = self._get_metric_value(instance, metric_name, input_data)
        return metrics

    def _apply_tie_breaker(self, candidates: List[Dict[str, Any]]) -> str:
        """
        Apply tie-breaking strategy when multiple instances have similar scores.
        """
        if self.tie_breaker == "first":
            selected = candidates[0]["instanceId"]
            self.logger.info(f"Tie breaker (first): selected {selected}")
            return selected

        elif self.tie_breaker == "round_robin":
            candidate_ids = [c["instanceId"] for c in candidates]
            self.round_robin_index = (self.round_robin_index + 1) % len(candidate_ids)
            selected = candidate_ids[self.round_robin_index]
            self.logger.info(f"Tie breaker (round_robin): selected {selected}")
            return selected
        else:
            selected = candidates[0]["instanceId"]
            self.logger.info(f"Tie breaker (default first): selected {selected}")
            return selected

    def _apply_tie_breaker_for_equal(self, candidates: List[str]) -> str:
        """
        Apply tie-breaking for equal distribution when multiple instances have the same queue length.
        """
        if self.tie_breaker == "first":
            selected = candidates[0]
            self.logger.info(f"Tie breaker (first): selected {selected}")
            return selected
        elif self.tie_breaker == "round_robin":
            self.round_robin_index = (self.round_robin_index + 1) % len(candidates)
            selected = candidates[self.round_robin_index]
            self.logger.info(f"Tie breaker (round_robin): selected {selected}")
            return selected
        else:
            selected = candidates[0]
            self.logger.info(f"Tie breaker (default first): selected {selected}")
            return selected

    def _fallback_selection(self, input_data: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """
        Apply fallback strategy when normal selection can't be made.
        """
        available_instances = input_data.get("available_instances", [])
        if not available_instances:
            self.logger.error(f"Fallback failed: No available instances")
            return {"skip": True, "reason": f"Fallback failed: No available instances. Original issue: {reason}"}

        selected = available_instances[0]
        self.logger.info(f"Using fallback selection: {selected}. Reason: {reason}")
        return {
            "skip": False,
            "select_instance": selected,
            "reason": f"Fallback selection due to: {reason}"
        }

    def management(self, action: str, data: dict) -> dict:
        self.logger.info(f"Management action '{action}' called.")
        if action == "health_check":
            return {"instances": self.current_instances, "status": "healthy"}
        elif action == "get_current_mapping":
            return {"mapping": self.session_ids_cache}
        elif action == "assign_streaming":
            session_id = data.get("session_id")
            latest_instances = data.get("instances", [])
            if set(latest_instances) != set(self.current_instances):
                self.logger.info(f"Instance list changed from {self.current_instances} to {latest_instances}. Updating session cache.")
                
                # Remove stale sessions from cache
                stale_sessions = [
                    session_id for session_id, instance_id in self.session_ids_cache.items()
                    if instance_id not in latest_instances
                ]
                
                if stale_sessions:
                    self.logger.info(f"Removing stale sessions from cache: {stale_sessions}")
                    for session_id in stale_sessions:
                        del self.session_ids_cache[session_id]
                        if session_id in self.session_task_counts:
                            del self.session_task_counts[session_id]
                        if session_id in self.session_timestamps:
                            del self.session_timestamps[session_id]

                self.current_instances = latest_instances

            if not session_id:
                self.logger.error("'session_id' not provided for 'assign_streaming' action.")
                return {"status": "error", "reason": "session_id is required."}

            # If session is already cached, return the existing instance
            if session_id in self.session_ids_cache:
                cached_instance = self.session_ids_cache[session_id]
                if cached_instance in self.current_instances:
                    self.logger.info(f"Session '{session_id}' already assigned to '{cached_instance}'.")
                    self.session_timestamps[session_id] = time.time()
                    return {"instance_id": cached_instance, "status": "ok"}
                else:
                    self.logger.info(f"Cached instance '{cached_instance}' for session '{session_id}' is no longer active. Re-assigning.")
                    del self.session_ids_cache[session_id]
                    if session_id in self.session_task_counts:
                        del self.session_task_counts[session_id]
                    if session_id in self.session_timestamps:
                        del self.session_timestamps[session_id]

            # Select the best available instance
            chosen_instance = self._select_best_instance()

            if chosen_instance:
                self.logger.info(f"Pre-allocating instance '{chosen_instance}' for streaming session '{session_id}'.")
                self.session_ids_cache[session_id] = chosen_instance
                self.session_timestamps[session_id] = time.time()  # Record timestamp for timeout
                return {"instance_id": chosen_instance, "status": "ok"}
            else:
                self.logger.error(f"Failed to select an instance for session '{session_id}'.")
                return {"instance_id": None, "status": "error", "reason": "Instance selection failed."}

        self.logger.warning(f"Unknown management action received: {action}")
        return {"status": "unknown_action", "reason": f"Action '{action}' is not supported."}

    def _calculate_requested_tokens_score(self, instance: Dict[str, Any], input_data: Dict[str, Any]) -> float:
        """
        Calculate score based on how well instance matches user's requested tokens/second preference.
        Higher score = better match for user preference.
        """
        # Get instance's actual tokens/second rate
        actual_tokens_per_sec = instance.get('llm_tokens_per_second', 0)
        
        # Get user's preference from request data
        request = input_data.get("request", {})
        user_preference = request.get("response_preference", "balanced")
        
        # Alternative: check for explicit tokens/second preference
        requested_tokens_per_sec = request.get("requested_tokens_per_second")
        
        if requested_tokens_per_sec is not None:
            # User specified exact tokens/second preference
            return self._score_exact_tokens_preference(actual_tokens_per_sec, requested_tokens_per_sec)
        else:
            # Use categorical preference (fast/balanced/thoughtful)
            return self._score_categorical_preference(actual_tokens_per_sec, user_preference)

    def _score_exact_tokens_preference(self, actual: float, requested: float) -> float:
        """
        Score how well actual tokens/sec matches requested tokens/sec.
        Returns 0-1 score where 1.0 = perfect match.
        """
        if requested <= 0:
            return 0.0
            
        # Calculate match score - closer to requested = higher score
        deviation = abs(actual - requested)
        max_deviation = max(requested, 50)  # Allow up to 50 tokens/sec deviation
        
        if deviation >= max_deviation:
            return 0.0
        else:
            return 1.0 - (deviation / max_deviation)

    def _score_categorical_preference(self, actual: float, preference: str) -> float:
        """
        Score based on categorical preference: fast/balanced/thoughtful.
        """
        config = self.user_preference_config
        fast_threshold = config.get("fast_threshold", 50)
        thoughtful_threshold = config.get("thoughtful_threshold", 20)
        
        if preference == "fast":
            # Prefer high tokens/second for quick responses
            if actual >= fast_threshold:
                return 1.0
            elif actual >= thoughtful_threshold:
                return 0.5
            else:
                return 0.0
                
        elif preference == "thoughtful":
            # Prefer low tokens/second for detailed responses
            if actual <= thoughtful_threshold:
                return 1.0
            elif actual <= fast_threshold:
                return 0.5
            else:
                return 0.0
                
        else:  # balanced or default
            # Prefer moderate tokens/second
            if thoughtful_threshold <= actual <= fast_threshold:
                return 1.0
            elif actual < thoughtful_threshold:
                return 0.5
            else:  # actual > fast_threshold
                return 0.5

    def _select_best_instance(self) -> str:
        """Select the best instance based on weighted metrics."""
        if not self.current_instances:
            self.logger.warning("No instances available for routing.")
            return None

        metrics_collector = self.settings.get('get_metrics')
        if not metrics_collector:
            self.logger.error("get_metrics function not found in settings")
            return None
        
        metrics = metrics_collector()
        block_metrics = metrics.get("block_metrics", [])

        instances_with_metrics = [
            inst for inst in block_metrics
            if inst.get('instanceId') in self.current_instances
        ]

        if not instances_with_metrics:
            self.logger.warning("No metrics found for available instances")
            return None

        # Calculate weighted scores for each instance
        instance_scores = []
        for instance in instances_with_metrics:
            score = self._calculate_weighted_score(instance, {})
            instance_scores.append({
                "instanceId": instance.get('instanceId'),
                "weighted_score": score
            })

        # Select the instance with the highest weighted score (higher is better)
        best_instance_data = max(instance_scores, key=lambda x: x["weighted_score"])
        best_score = best_instance_data["weighted_score"]
        candidates = [i for i in instance_scores if abs(i["weighted_score"] - best_score) < 0.001]

        if len(candidates) > 1:
            self.logger.info(f"Found {len(candidates)} instances with similar scores ({best_score:.4f}), applying tie-breaking")
            selected_instance = self._apply_tie_breaker(candidates)
        else:
            selected_instance = best_instance_data["instanceId"]

        self.logger.info(f"Selected instance {selected_instance} with best weighted score: {best_score:.4f}")
        return selected_instance

    def _select_best_instance_from_list(self, instance_list: List[str]) -> str:
        """Select the best instance from a given list based on weighted metrics."""
        if not instance_list:
            self.logger.warning("No instances in the provided list.")
            return None

        metrics_collector = self.settings.get('get_metrics')
        if not metrics_collector:
            self.logger.error("get_metrics function not found in settings")
            return None
        
        metrics = metrics_collector()
        block_metrics = metrics.get("block_metrics", [])

        instances_with_metrics = [
            inst for inst in block_metrics
            if inst.get('instanceId') in instance_list
        ]

        if not instances_with_metrics:
            self.logger.warning("No metrics found for instances in the list")
            return None

        # Calculate weighted scores for each instance in the list
        instance_scores = []
        for instance in instances_with_metrics:
            score = self._calculate_weighted_score(instance, {})
            instance_scores.append({
                "instanceId": instance.get('instanceId'),
                "weighted_score": score
            })

        # Select the instance with the highest weighted score (higher is better)
        best_instance_data = max(instance_scores, key=lambda x: x["weighted_score"])
        best_score = best_instance_data["weighted_score"]
        candidates = [i for i in instance_scores if abs(i["weighted_score"] - best_score) < 0.001]

        if len(candidates) > 1:
            self.logger.info(f"Found {len(candidates)} instances with similar scores ({best_score:.4f}), applying tie-breaking")
            selected_instance = self._apply_tie_breaker(candidates)
        else:
            selected_instance = best_instance_data["instanceId"]

        self.logger.info(f"Selected instance {selected_instance} from list with best weighted score: {best_score:.4f}")
        return selected_instance

    def _build_queue_lengths(self, block_metrics):
        queue_lengths = {}
        for inst in self.current_instances:
            inst_metric = next((m for m in block_metrics if m.get('instanceId') == inst), None)
            if inst_metric:
                queue_length = self._get_metric_value(inst_metric, 'queue_length', {})
                queue_lengths[inst] = queue_length
            else:
                queue_lengths[inst] = float('inf')
        return queue_lengths

    def _calculate_average_queue(self, queue_lengths):
        valid_lengths = [v for v in queue_lengths.values() if v != float('inf')]
        if valid_lengths:
            return sum(valid_lengths) / len(valid_lengths)
        return 0

    def _identify_overloaded_instances(self, queue_lengths, avg_queue):
        overloaded = []
        for inst, ql in queue_lengths.items():
            if ql > avg_queue * (1 + self.overload_threshold_percentage):
                overloaded.append(inst)
        return overloaded

    def _collect_sessions_to_redistribute(self, overloaded_instances, sessions_by_instance, queue_lengths, avg_queue):
        sessions_to_redistribute = []
        for inst in overloaded_instances:
            if queue_lengths is not None:
                queue_length = queue_lengths[inst]
                if queue_length == float('inf'):
                    # If queue_length is infinity, redistribute all sessions from this instance
                    excess = len(sessions_by_instance[inst])
                else:
                    excess = int(queue_length - avg_queue)
                if excess > 0:
                    sessions_sorted = sorted(sessions_by_instance[inst], key=lambda s: self.session_task_counts.get(s, 0))
                    sessions_to_redistribute.extend(sessions_sorted[:min(excess, len(sessions_by_instance[inst]))])
            else:
                num_instances = len(self.current_instances)
                avg_sessions = len(self.session_ids_cache) / num_instances
                excess = len(sessions_by_instance[inst]) - int(avg_sessions)
                if excess > 0:
                    sessions_sorted = sorted(sessions_by_instance[inst], key=lambda s: self.session_task_counts.get(s, 0))
                    sessions_to_redistribute.extend(sessions_sorted[:min(excess, len(sessions_by_instance[inst]))])
        return sessions_to_redistribute

    def _redistribute_sessions(self, block_metrics=None):
            self.logger.info("Redistribution: Starting redistribution process")
            if not self.session_ids_cache or not self.current_instances:
                self.logger.info("Redistribution: Skipping - no session cache or instances")
                return

            sessions_by_instance = defaultdict(list)
            for session, instance in self.session_ids_cache.items():
                if instance in self.current_instances:
                    sessions_by_instance[instance].append(session)
            self.logger.info(f"Redistribution: Grouped {len(self.session_ids_cache)} sessions across {len(self.current_instances)} instances")

            # Initialize task counts for all current instances to handle idle ones
            task_counts_by_instance = {inst: 0 for inst in self.current_instances}
            for inst, sessions in sessions_by_instance.items():
                task_counts_by_instance[inst] = sum(self.session_task_counts.get(s, 0) for s in sessions)
            self.logger.info(f"Redistribution: Task counts by instance: {task_counts_by_instance}")
            
            # Decide if rebalancing is needed
            imbalance_detected = False
            avg_metric = 0  # Initialize to avoid undefined variable
            if block_metrics:
                queue_lengths = self._build_queue_lengths(block_metrics)
                self.logger.info(f"Redistribution: Queue lengths for redistribution: {queue_lengths}")
                healthy_queues = {inst: q for inst, q in queue_lengths.items() if q != float('inf')}
                unhealthy_instances = [inst for inst, q in queue_lengths.items() if q == float('inf')]
                if unhealthy_instances:
                    self.logger.warning(f"Instances with missing metrics: {unhealthy_instances}. Excluding from session redistribution SOURCE for this cycle.")
                if len(healthy_queues) > 1:
                    max_q = max(healthy_queues.values())
                    min_q = min(healthy_queues.values())
                    imbalance_diff = max_q - min_q
                    self.logger.info(f"Redistribution: Queue check - max_q={max_q}, min_q={min_q}, imbalance_diff={imbalance_diff}, threshold={self.imbalance_threshold}")
                    if (imbalance_diff > self.imbalance_threshold):
                        imbalance_detected = True
                        avg_metric = sum(healthy_queues.values()) / len(healthy_queues)
                        self.logger.info(f"Redistribution: Queue imbalance detected ({imbalance_diff} > {self.imbalance_threshold}), proceeding with avg_queue={avg_metric:.2f}")
                    else:
                        self.logger.info(f"Redistribution: Queue imbalance not detected (max_q={max_q}, diff={imbalance_diff} <= {self.imbalance_threshold})")
                else:
                    self.logger.info("Redistribution: Not enough healthy instances to check for queue-based imbalance.")
            else:  # Fallback to task-based check
                self.logger.info(f"Redistribution: Task counts for redistribution: {task_counts_by_instance}")
                if task_counts_by_instance:
                    max_tasks = max(task_counts_by_instance.values())
                    min_tasks = min(task_counts_by_instance.values())
                    imbalance_diff = max_tasks - min_tasks
                    self.logger.info(f"Redistribution: Task check - max_tasks={max_tasks}, min_tasks={min_tasks}, imbalance_diff={imbalance_diff}, threshold={self.task_imbalance_threshold}")
                    if imbalance_diff > self.task_imbalance_threshold:
                        imbalance_detected = True
                        avg_metric = sum(task_counts_by_instance.values()) / len(task_counts_by_instance)
                        self.logger.info(f"Redistribution: Task imbalance detected ({imbalance_diff} > {self.task_imbalance_threshold}), proceeding with avg_tasks={avg_metric:.2f}")
                    else:
                        self.logger.info(f"Redistribution: Task imbalance not detected (diff={imbalance_diff} <= {self.task_imbalance_threshold})")
                else:
                    self.logger.info("Redistribution: Task counts empty, cannot perform task-based check")

            if not imbalance_detected:
                self.logger.info("Redistribution: System is balanced, skipping redistribution")
                return

            healthy_instances = list(healthy_queues.keys()) if block_metrics else self.current_instances

            # Identify overloaded instances
            overloaded_instances = []
            if block_metrics:
                overloaded_instances = self._identify_overloaded_instances(healthy_queues, avg_metric)
                self.logger.info(f"Redistribution: Overloaded instances (above avg queue {avg_metric:.2f}): {overloaded_instances}")
            else: # CORRECTED: Use task average to find overloaded instances
                overload_threshold = avg_metric * (1 + self.overload_threshold_percentage)
                overloaded_instances = [inst for inst, count in task_counts_by_instance.items() if count > overload_threshold]
                self.logger.info(f"Redistribution: Overloaded instances (above avg tasks {avg_metric:.2f}): {overloaded_instances}")

            # Collect sessions to redistribute
            sessions_to_redistribute = []
            if block_metrics:
                sessions_to_redistribute = self._collect_sessions_to_redistribute(overloaded_instances, sessions_by_instance, healthy_queues, avg_metric)
            else: # CORRECTED: Use task counts to determine how many sessions to move
                for inst in overloaded_instances:
                    excess_tasks = task_counts_by_instance[inst] - avg_metric
                    sessions_sorted = sorted(sessions_by_instance.get(inst, []), key=lambda s: self.session_task_counts.get(s, 0))
                    
                    moved_tasks = 0
                    for session in sessions_sorted:
                        if moved_tasks >= excess_tasks:
                            break
                        sessions_to_redistribute.append(session)
                        moved_tasks += self.session_task_counts.get(session, 0)
            
            self.logger.info(f"Redistribution: Collected sessions to redistribute before trimming: {sessions_to_redistribute}")
            num_to_redistribute = min(len(sessions_to_redistribute), int(len(self.session_ids_cache) * self.redistribution_percentage))
            sessions_to_redistribute = sessions_to_redistribute[:num_to_redistribute]
            self.logger.info(f"Redistribution: Identified {len(sessions_to_redistribute)} sessions to redistribute: {sessions_to_redistribute}")

            # Redistribute sessions to the best available targets
            redistributed_count = 0
            adjusted_queue_lengths = queue_lengths.copy() if block_metrics else None 
            adjusted_task_counts_by_instance = task_counts_by_instance.copy() if not block_metrics else None
            round_robin_index = 0
            for session in sessions_to_redistribute:
                old_instance = self.session_ids_cache.get(session)
                if not old_instance:
                    self.logger.warning(f"Redistribution: Session {session} has no cached instance, skipping")
                    continue

                available_targets = [i for i in healthy_instances if i != old_instance and i not in overloaded_instances]
                if not available_targets:
                    self.logger.warning(f"Redistribution: No available targets for session {session} from {old_instance}, skipping")
                    continue

                new_instance = None
                if self.redistribution_selection_mode == "least_loaded":
                    if block_metrics and adjusted_queue_lengths:
                        # target_metrics = {inst: queue_lengths.get(inst, float('inf')) for inst in available_targets}
                        target_metrics = {inst: adjusted_queue_lengths.get(inst, float('inf')) for inst in available_targets}
                        new_instance = min(target_metrics, key=target_metrics.get)
                        self.logger.info(f"Redistribution: Target metrics for session {session}: {target_metrics}")
                        adjusted_queue_lengths[new_instance] = adjusted_queue_lengths.get(new_instance, 0) + 1
                    else: # CORRECTED: Select instance with the least number of tasks
                        target_metrics = {inst: adjusted_task_counts_by_instance.get(inst, 0) for inst in available_targets}
                        self.logger.info(f"Redistribution: Target metrics for session {session}: {target_metrics}")
                        new_instance = min(target_metrics, key=target_metrics.get)
                        adjusted_task_counts_by_instance[new_instance] += 1
                else: # Random or Best selection would go here
                    new_instance = random.choice(available_targets)

                self.logger.info(f"Redistribution: Selected new_instance for session {session}: {new_instance}")
                if new_instance and new_instance != old_instance:
                    self.session_ids_cache[session] = new_instance
                    if not block_metrics:
                        task_count = self.session_task_counts.get(session, 0)
                        task_counts_by_instance[old_instance] -= task_count
                        task_counts_by_instance[new_instance] += task_count
                    self.logger.debug(f"Redistribution: Moved session {session} from {old_instance} to {new_instance}")
                    redistributed_count += 1
                else:
                    self.logger.warning(f"Redistribution: Failed to move session {session} (new_instance={new_instance})")

            self.logger.info(f"Redistribution: Completed - total sessions redistributed: {redistributed_count}")

    def _cleanup_stale_sessions(self):
        """
        Remove sessions from cache that have exceeded the timeout period.
        """
        current_time = time.time()
        stale_sessions = [
            sid for sid, ts in self.session_timestamps.items()
            if current_time - ts > self.session_timeout_seconds
        ]
        for sid in stale_sessions:
            del self.session_ids_cache[sid]
            del self.session_task_counts[sid]
            del self.session_timestamps[sid]
            self.logger.info(f"Removed stale session {sid} due to timeout")
