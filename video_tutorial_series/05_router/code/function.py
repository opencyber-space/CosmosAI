import json
import requests
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
import sys

class AIOSv1PolicyRule:
    """
    A policy for selecting the best block based on dynamic weighted scoring.

    This policy filters candidate blocks by application type and then scores them
    based on a weighted combination of real-time performance metrics and static
    hardware characteristics.
    """

    def __init__(self, rule_id: str, settings: Dict, parameters: Dict):
        """
        Initializes the policy rule.

        Args:
            rule_id (str): The unique identifier for this rule.
            settings (Dict): Configuration settings, e.g., API endpoints.
                             Expected to contain 'METRICS_BASE_URL'.
            parameters (Dict): Default parameters for the policy.
        """
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters
        self.metrics_base_url =self.parameters.get("METRICS_BASE_URL", os.environ.get("METRICS_BASE_URL"))

        # Set up structured logging
        self.logger = logging.getLogger(f"AIOSv1PolicyRule.{self.rule_id}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Define the mapping from optimization goals to metric accessors
        self.optimization_metric_map = {
            "Cost_Saver": {
                "parameterCountB": {"path": "componentMetadata.architecture.parameterCountB", "normalize": "min"},
                "gpu_totalMem": {"path": "hardware.gpus[0].totalMem", "normalize": "min"},
            },
            "High_Quality_Lane": {
                "end_to_end_latency": {"path": "end_to_end_latency", "normalize": "min"},
                "end_to_end_fps": {"path": "end_to_end_fps", "normalize": "max"},
                "MMLU": {"path": "componentMetadata.evaluation.benchmarks.MMLU.value", "normalize": "max"},
            },
            "Balanced_Performer": {
                "end_to_end_latency": {"path": "end_to_end_latency", "normalize": "min"},
                "parameterCountB": {"path": "componentMetadata.architecture.parameterCountB", "normalize": "min"},
                "end_to_end_fps": {"path": "end_to_end_fps", "normalize": "max"},
            },
            "Fast_Generator": {
                "llm_tokens_per_second": {"path": "llm_tokens_per_second", "normalize": "max"}
            },
            "Active_Block": {
                "llm_active_sessions": {"path": "llm_active_sessions", "normalize": "max"},
                "tasks_processed": {"path": "tasks_processed.average_1m", "normalize": "max"},
                "end_to_end_count_total": {"path": "end_to_end_count_total", "normalize": "max"}
            },
            "Free_Block": {
                "llm_active_sessions": {"path": "llm_active_sessions", "normalize": "min"},
                "queue_length": {"path": "queue_length.average_1m", "normalize": "min"}
            },

        }

        self.app_map = self.settings.get("APP_MAP", {
            "RAG": "chat-completion",
            "Code": "code-generation",
            "Vision": "multi-modal",
            "Chat": "chat-completion"
        })

    def eval(self, parameters: Dict, input_data: List[Dict], context: Dict) -> Dict:
        """
        Evaluates the policy to select the best block.

        Args:
            parameters (Dict): Runtime parameters, including the 'selection_query'.
            input_data (List[Dict]): A list of candidate block dictionaries.
            context (Dict): The execution context (not used in this policy).

        Returns:
            Dict: A dictionary containing the selected block or an error reason.
        """
        try:
            self.logger.info(f"Starting policy evaluation for rule '{self.rule_id}'.")
            self.logger.info(f"Parameters: {json.dumps(parameters, indent=2)}")
            self.logger.info(f"Number of candidate blocks received: {len(input_data)}")

            selection_query = parameters.get("selection_query")
            if selection_query is None:
                self.logger.warning("Invalid or missing 'selection_query' in parameters. Aborting.")
                return {"result": [], "reason": "Invalid or missing 'selection_query' in parameters."}

            # 1. Filter by Application Type (optional)
            if "application_type" in selection_query:
                application_type = selection_query["application_type"]
                self.logger.info(f"Step 1: Filtering for application_type: '{application_type}'")
                filtered_candidates = self._filter_by_application_type(input_data, application_type)
                self.logger.info(f"Found {len(filtered_candidates)} candidates after filtering.")
            else:
                self.logger.info("Step 1: Skipping application_type filtering as it was not provided.")
                filtered_candidates = input_data

            if not filtered_candidates:
                self.logger.warning(f"No candidates found matching the criteria.")
                return {"result": [], "reason": f"No candidates found matching the criteria."}

            # 2. Fetch Metrics and Score
            optimization_goals = selection_query.get("optimization_goals", [])
            if not optimization_goals:
                # If no goals, return the first compatible candidate
                selected_candidate = filtered_candidates[0]
                self.logger.info(f"No optimization goals provided. Selected first compatible candidate: {selected_candidate.get('id')}")
                # return {"result": [selected_candidate], "reason": "No optimization goals provided; returning first compatible candidate."}
                return selected_candidate
            
            self.logger.info(f"Step 2: Scoring {len(filtered_candidates)} candidates based on {len(optimization_goals)} optimization goal(s).")
            # Fetch metrics for all candidates first
            for candidate in filtered_candidates:
                block_id = candidate.get("id")
                self.logger.info(f"Processing candidate block ID: {block_id}")
                if not block_id:
                    self.logger.info("Found a candidate with no 'id'. It will be ignored.")
                    continue # Cannot score without an id
                self.logger.info("Gettign metrics for block ID: %s", block_id)
                metrics = self._fetch_metrics(block_id)
                if metrics:
                    candidate.update(metrics) # Attach for scoring

            # Score candidates
            scored_candidates = self._score_candidates(filtered_candidates, optimization_goals)
            self.logger.info(f"Scoring complete. Got scores for {len(scored_candidates)} candidates.")

            # 3. Select the Best Candidate
            if not scored_candidates:
                self.logger.warning("Scoring did not yield any valid candidates.")
                return {"result": [], "reason": "Scoring did not yield any valid candidates."}

            best_candidate = max(scored_candidates, key=lambda x: x["final_score"])
            self.logger.info(f"Best candidate selected: {best_candidate['candidate'].get('id')} with score {best_candidate['final_score']:.4f}")

            # return {"result": [best_candidate["candidate"]], "metadata": {"scores": scored_candidates}}
            return best_candidate["candidate"]
        except Exception as e:
            # Get the line number from the exception traceback
            _, _, exc_tb = sys.exc_info()
            line_number = exc_tb.tb_lineno
            self.logger.error(f"An unexpected error occurred in eval at line {line_number}: {e}", exc_info=True)
            return {"result": [], "reason": f"An unexpected error occurred on line {line_number}: {e}"}

    def _filter_by_application_type(self, candidates: List[Dict], application_type: str) -> List[Dict]:
        """Filters candidates based on their declared use cases."""
        filtered = []
        target_usecase = self.app_map.get(application_type, application_type.lower())

        for candidate in candidates:
            usecases = candidate.get("componentMetadata", {}).get("usecase", [])
            if isinstance(usecases, str):
                # Handle comma-separated string for backward compatibility
                usecases = [uc.strip() for uc in usecases.split(',')]
            
            if target_usecase in usecases:
                filtered.append(candidate)
        return filtered

    def _fetch_metrics(self, block_id: str) -> Optional[Dict]:
        """Fetches live metrics for a given block ID from the metrics API."""
        if not self.metrics_base_url:
            self.logger.info("METRICS_BASE_URL not set. Skipping live metric fetch.")
            return {}
        try:
            url = f"{self.metrics_base_url.rstrip('/')}/{block_id}"
            self.logger.info(f"Fetching metrics from URL: {url}")
            response = requests.get(url, timeout=50)
            response.raise_for_status()
            api_response = response.json()

            if not api_response.get("success") or not api_response.get("data"):
                self.logger.info(f"Metrics API response for {block_id} indicates failure or no data.")
                return {}

            # The 'data' list can contain multiple entries for a block, we need to find the right one.
            for block_data in api_response["data"]:
                if block_data.get("blockId") == block_id:
                    # We need to find the instance with the detailed metrics, not the summary 'executor' instance.
                    for instance in block_data.get("instances", []):
                        if instance.get("instanceId") != "executor":
                            self.logger.info(f"Found detailed metrics for instance {instance.get('instanceId')} of block {block_id}.")
                            return instance # This instance has the detailed metrics we need.
            
            self.logger.info(f"No instance with detailed metrics found for block {block_id}.")
            return {}
            
        except (requests.RequestException, json.JSONDecodeError) as e:
            self.logger.info(f"Could not fetch or parse metrics for block {block_id}: {e}")
            return {}

    def _get_nested_value(self, data: Dict, path: str) -> Optional[Any]:
        """Safely retrieves a value from a nested dict using a dot-separated path."""
        self.logger.debug(f"Attempting to get value for path '{path}'")
        keys = path.split('.')
        current = data
        for i, key in enumerate(keys):
            path_so_far = '.'.join(keys[:i+1])
            if isinstance(current, dict):
                current = current.get(key)
                self.logger.debug(f"  - Traversing path: '{path_so_far}'. Value: {current}")
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    if idx < len(current):
                        current = current[idx]
                        self.logger.debug(f"  - Traversing list at index {idx}: '{path_so_far}'. Value: {current}")
                    else:
                        self.logger.debug(f"  - Index {idx} out of bounds for list at path '{'.'.join(keys[:i])}'.")
                        return None
                except (ValueError, IndexError):
                    self.logger.debug(f"Failed to get value at index '{key}' in path '{path}'.")
                    return None
            else:
                self.logger.debug(f"  - Path traversal stopped. Cannot get key '{key}' from non-dict/list value at path '{'.'.join(keys[:i])}'.")
                return None
            if current is None:
                self.logger.debug(f"  - Value became None at path '{path_so_far}'.")
                break
        return current

    def _normalize_metrics(self, values: List[float], method: str) -> List[float]:
        """Normalizes a list of values."""
        self.logger.info(f"Normalizing (method: {method}): {values}")
        if not values or max(values) == min(values):
            self.logger.info("All values are the same or list is empty. Returning neutral scores (0.5).")
            return [0.5] * len(values) # Neutral score if all values are the same

        max_val, min_val = max(values), min(values)
        self.logger.info(f"Normalization range: min={min_val}, max={max_val}")
        
        normalized = []
        for v in values:
            # The denominator can't be zero here because we checked if max == min
            denominator = max_val - min_val
            if method == "max": # Higher is better
                normalized.append((v - min_val) / denominator)
            elif method == "min": # Lower is better
                normalized.append(1 - ((v - min_val) / denominator))
        
        self.logger.info(f"Normalized result: {normalized}")
        return normalized

    def _score_candidates(self, candidates: List[Dict], goals: List[Dict]) -> List[Dict]:
        """Calculates a weighted score for each candidate based on optimization goals."""
        scores = {c["id"]: {"total_score": 0, "weighted_scores": {}} for c in candidates}
        
        # First, extract all necessary metric values for normalization
        metric_values_for_norm = {}
        for goal in goals:
            goal_name = goal["name"]
            if goal_name in self.optimization_metric_map:
                metric_values_for_norm[goal_name] = {}
                for metric, props in self.optimization_metric_map[goal_name].items():
                    metric_values_for_norm[goal_name][metric] = [
                        self._get_nested_value(c, props["path"]) or 0 for c in candidates
                    ]

        # Normalize them
        normalized_values = {}
        for goal_name, metrics in metric_values_for_norm.items():
            normalized_values[goal_name] = {}
            for metric, values in metrics.items():
                norm_method = self.optimization_metric_map[goal_name][metric]["normalize"]
                normalized_values[goal_name][metric] = self._normalize_metrics(values, norm_method)

        # Now, calculate the final scores
        for i, candidate in enumerate(candidates):
            block_id = candidate["id"]
            final_score = 0
            
            # Log the parsed metric values for this candidate
            metric_log = {}
            for goal in goals:
                goal_name = goal["name"]
                if goal_name in self.optimization_metric_map:
                    for metric, props in self.optimization_metric_map[goal_name].items():
                        value = self._get_nested_value(candidate, props["path"])
                        metric_log[metric] = value
            self.logger.info(f"Candidate '{block_id}' - Parsed Metrics: {json.dumps(metric_log)}")

            for goal in goals:
                goal_name = goal["name"]
                goal_weight = goal.get("weight", 1.0)
                
                if goal_name in self.optimization_metric_map:
                    goal_score = 0
                    num_metrics = len(self.optimization_metric_map[goal_name])
                    for metric in self.optimization_metric_map[goal_name]:
                        # Get the pre-normalized value for this candidate
                        norm_score = normalized_values[goal_name][metric][i]
                        goal_score += norm_score
                    
                    # Average the scores for the metrics within the goal
                    if num_metrics > 0:
                        avg_goal_score = goal_score / num_metrics
                        weighted_score = avg_goal_score * goal_weight
                        scores[block_id]["weighted_scores"][goal_name] = weighted_score
                        final_score += weighted_score

            scores[block_id]["total_score"] = final_score
            self.logger.info(f"Candidate '{block_id}' - Final Score: {final_score:.4f}")

        # Format the output
        result = []
        for i, c in enumerate(candidates):
            block_id = c["id"]
            result.append({
                "candidate": c,
                "final_score": scores[block_id]["total_score"],
                "breakdown": scores[block_id]["weighted_scores"]
            })
        
        self.logger.debug(f"Final scores: {json.dumps(result, indent=2)}")
        return result
