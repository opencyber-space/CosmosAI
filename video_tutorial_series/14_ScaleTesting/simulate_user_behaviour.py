#!/usr/bin/env python3
"""
User Behavior Simulation Generator

This script generates a CSV file containing user-specific usage patterns for load testing.
The CSV contains an MxN matrix where:
- M = users_per_hour (number of users)
- N = 24 (hours 0-23)
- Each cell contains a multiplier for request activity during that hour

Usage:
    python simulate_user_behaviour.py [config_file]
    
Output:
    user_behavior_patterns.csv - Matrix of user-specific hourly patterns
"""

import yaml
import csv
import random
import numpy as np
import argparse
import os
from typing import Dict, List

class UserBehaviorGenerator:
    """Generates diverse user behavior patterns for load testing"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        self.users_per_hour = self.config.get('crowd_config', {}).get('users_per_hour', 100)
        self.base_patterns = self.config.get('user_config', {}).get('usage_patterns', {})
        
        # Convert base patterns to list for easier manipulation
        self.base_hourly_pattern = [self.base_patterns.get(hour, 1.0) for hour in range(24)]
        
    def generate_behavior_types(self) -> List[Dict[str, any]]:
        """Define different types of user behaviors"""
        behavior_types = [
            {
                'name': 'Early Bird',
                'description': 'High activity in morning hours (6-10)',
                'peak_hours': [6, 7, 8, 9, 10],
                'low_hours': [22, 23, 0, 1, 2, 3, 4, 5],
                'weight': 0.15
            },
            {
                'name': 'Night Owl',
                'description': 'High activity in evening/night hours (20-2)',
                'peak_hours': [20, 21, 22, 23, 0, 1, 2],
                'low_hours': [6, 7, 8, 9, 10, 11],
                'weight': 0.10
            },
            {
                'name': 'Business Hours',
                'description': 'Traditional 9-5 pattern',
                'peak_hours': [9, 10, 11, 14, 15, 16, 17],
                'low_hours': [0, 1, 2, 3, 4, 5, 6, 22, 23],
                'weight': 0.25
            },
            {
                'name': 'Lunch Skipper', 
                'description': 'Active during lunch hours',
                'peak_hours': [12, 13, 14],
                'low_hours': [2, 3, 4, 5],
                'weight': 0.08
            },
            {
                'name': 'Sporadic',
                'description': 'Random usage throughout the day',
                'peak_hours': [],  # Will be randomized
                'low_hours': [],   # Will be randomized
                'weight': 0.12
            },
            {
                'name': 'Weekend Warrior',
                'description': 'Higher activity on weekends (simulated as late hours)',
                'peak_hours': [11, 12, 13, 18, 19, 20],
                'low_hours': [3, 4, 5, 6, 7, 8],
                'weight': 0.10
            },
            {
                'name': 'Standard',
                'description': 'Follows the default pattern from config',
                'peak_hours': [],  # Will use base pattern
                'low_hours': [],
                'weight': 0.20
            }
        ]
        
        # Validate weights immediately
        self._validate_behavior_weights(behavior_types)
        return behavior_types
    
    def _validate_behavior_weights(self, behavior_types: List[Dict]) -> None:
        """Validate that behavior type weights sum to 1.0"""
        total_weight = sum(behavior['weight'] for behavior in behavior_types)
        
        print(f"Behavior type weight validation:")
        for behavior in behavior_types:
            print(f"  {behavior['name']}: {behavior['weight']:.3f} ({behavior['weight']:.1%})")
        print(f"  Total: {total_weight:.3f}")
        
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Behavior type weights must sum to 1.0, got {total_weight:.3f}")
        
        print("  ✅ Weight validation passed")
    
    def create_user_pattern(self, behavior_type: Dict) -> List[float]:
        """Create a 24-hour usage pattern for a specific behavior type"""
        if behavior_type['name'] == 'Standard':
            # Use base pattern with small random variation
            pattern = []
            for hour_value in self.base_hourly_pattern:
                # Add ±10% random variation
                variation = random.uniform(0.9, 1.1)
                pattern.append(round(hour_value * variation, 3))
            return pattern
            
        elif behavior_type['name'] == 'Sporadic':
            # Create completely random pattern
            pattern = []
            for _ in range(24):
                pattern.append(round(random.uniform(0.05, 1.0), 3))
            return pattern
            
        else:
            # Create pattern based on peak and low hours
            pattern = [0.3] * 24  # Base medium activity
            
            # Set peak hours (high activity)
            for hour in behavior_type['peak_hours']:
                pattern[hour] = round(random.uniform(0.8, 1.0), 3)
            
            # Set low hours (low activity)
            for hour in behavior_type['low_hours']:
                pattern[hour] = round(random.uniform(0.05, 0.2), 3)
            
            # Fill remaining hours with medium activity
            peak_set = set(behavior_type['peak_hours'])
            low_set = set(behavior_type['low_hours'])
            
            for hour in range(24):
                if hour not in peak_set and hour not in low_set:
                    pattern[hour] = round(random.uniform(0.3, 0.7), 3)
            
            return pattern
    
    def generate_user_behaviors(self) -> List[List[float]]:
        """Generate behavior patterns for all users"""
        behavior_types = self.generate_behavior_types()
        
        # Validate that weights sum to 1.0
        total_weight = sum(behavior['weight'] for behavior in behavior_types)
        if abs(total_weight - 1.0) > 0.001:  # Allow small floating point tolerance
            print(f"⚠️  Warning: Behavior type weights sum to {total_weight:.3f}, not 1.0")
            print("   Normalizing weights to ensure proper distribution...")
            
            # Normalize weights to sum to 1.0
            for behavior in behavior_types:
                behavior['weight'] = behavior['weight'] / total_weight
            
            print("   ✅ Weights normalized successfully")
        
        user_patterns = []
        
        print(f"Generating behavior patterns for {self.users_per_hour} users...")
        
        # Calculate number of users for each behavior type
        users_per_behavior = []
        remaining_users = self.users_per_hour
        
        for i, behavior in enumerate(behavior_types):
            if i == len(behavior_types) - 1:  # Last behavior gets remaining users
                users_per_behavior.append(remaining_users)
            else:
                count = int(self.users_per_hour * behavior['weight'])
                users_per_behavior.append(count)
                remaining_users -= count
        
        # Validate total user count
        total_assigned = sum(users_per_behavior)
        if total_assigned != self.users_per_hour:
            print(f"⚠️  User assignment mismatch: {total_assigned} assigned vs {self.users_per_hour} expected")
            # Adjust the last behavior type to match exactly
            users_per_behavior[-1] += (self.users_per_hour - total_assigned)
            print(f"   ✅ Adjusted last behavior type to {users_per_behavior[-1]} users")
        
        # Generate patterns for each behavior type
        for behavior, user_count in zip(behavior_types, users_per_behavior):
            print(f"  {behavior['name']}: {user_count} users ({behavior['weight']:.1%}) - {behavior['description']}")
            
            for _ in range(user_count):
                pattern = self.create_user_pattern(behavior)
                user_patterns.append(pattern)
        
        # Shuffle to avoid clustering by behavior type
        random.shuffle(user_patterns)
        
        return user_patterns
    
    def save_to_csv(self, user_patterns: List[List[float]], filename: str = "user_behavior_patterns.csv"):
        """Save user behavior patterns to CSV file"""
        print(f"\nSaving {len(user_patterns)} user patterns to {filename}...")
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row (hour labels)
            header = ['user_index'] + [f'hour_{i}' for i in range(24)]
            writer.writerow(header)
            
            # Write user patterns
            for user_index, pattern in enumerate(user_patterns):
                row = [user_index] + pattern
                writer.writerow(row)
        
        print(f"✅ Successfully generated behavior patterns:")
        print(f"   - File: {filename}")
        print(f"   - Users: {len(user_patterns)}")
        print(f"   - Hours: 24 (0-23)")
        print(f"   - Total cells: {len(user_patterns) * 24}")
    
    def print_sample_patterns(self, user_patterns: List[List[float]], num_samples: int = 5):
        """Print sample patterns for verification"""
        print(f"\nSample patterns (first {num_samples} users):")
        print("User | 00   01   02   03   04   05   06   07   08   09   10   11   12   13   14   15   16   17   18   19   20   21   22   23")
        print("-" * 120)
        
        for i in range(min(num_samples, len(user_patterns))):
            pattern_str = " ".join(f"{val:.2f}" for val in user_patterns[i])
            print(f"{i:4d} | {pattern_str}")

def main():
    parser = argparse.ArgumentParser(description='Generate user behavior patterns for load testing')
    parser.add_argument('config', nargs='?', default='config.yaml', 
                       help='Path to config.yaml file (default: config.yaml)')
    parser.add_argument('--output', '-o', default='user_behavior_patterns.csv',
                       help='Output CSV filename (default: user_behavior_patterns.csv)')
    parser.add_argument('--seed', type=int, help='Random seed for reproducible results')
    parser.add_argument('--preview', action='store_true', 
                       help='Show sample patterns without generating file')
    parser.add_argument('--validate-weights', action='store_true',
                       help='Validate behavior type weights and exit')
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility if provided
    if args.seed:
        random.seed(args.seed)
        np.random.seed(args.seed)
        print(f"Using random seed: {args.seed}")
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Config file '{args.config}' not found!")
        print("Please ensure the config file exists or specify the correct path.")
        return 1
    
    try:
        # Generate behavior patterns
        generator = UserBehaviorGenerator(args.config)
        
        # If just validating weights, do that and exit
        if args.validate_weights:
            print("✅ Weight validation completed successfully!")
            return 0
        
        user_patterns = generator.generate_user_behaviors()
        
        # Show sample patterns
        generator.print_sample_patterns(user_patterns)
        
        if not args.preview:
            # Save to CSV
            generator.save_to_csv(user_patterns, args.output)
            
            print(f"\n📝 Next steps:")
            print(f"   1. Review and edit {args.output} to customize user behaviors")
            print(f"   2. Run: python crowd.py {args.config}")
            print(f"   3. The load test will use individual user patterns from the CSV")
        else:
            print(f"\n👀 Preview mode - no file generated. Use without --preview to create CSV.")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
