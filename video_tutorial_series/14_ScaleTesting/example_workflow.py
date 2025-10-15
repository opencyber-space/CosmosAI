#!/usr/bin/env python3
"""
Example workflow for generating and using custom user behavior patterns

This script demonstrates the complete workflow:
1. Generate user behavior patterns CSV
2. Run load test with custom patterns
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and show output"""
    print(f"\n🔄 {description}")
    print(f"   Command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ Success")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
    else:
        print(f"   ❌ Failed")
        if result.stderr:
            print(f"   Error: {result.stderr.strip()}")
        return False
    return True

def main():
    print("🎯 User Behavior Pattern Generation Workflow")
    print("=" * 50)
    
    # Step 1: Generate behavior patterns
    if not run_command("python simulate_user_behaviour.py config.yaml", 
                      "Generating user behavior patterns"):
        return 1
    
    # Step 2: Show CSV info
    if os.path.exists("user_behavior_patterns.csv"):
        with open("user_behavior_patterns.csv", 'r') as f:
            lines = f.readlines()
            print(f"\n📊 Generated CSV file:")
            print(f"   - File: user_behavior_patterns.csv")
            print(f"   - Total rows: {len(lines) - 1} (excluding header)")
            print(f"   - Columns: 25 (user_index + 24 hours)")
            
            # Show first few lines
            print(f"\n   Preview (first 3 users):")
            for i in range(min(4, len(lines))):  # Header + 3 users
                line = lines[i].strip()
                if len(line) > 80:
                    line = line[:77] + "..."
                print(f"   {line}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Edit user_behavior_patterns.csv to customize individual user patterns")
    print(f"   2. Run: python crowd.py config.yaml")
    print(f"   3. Each user will follow their individual hourly pattern from the CSV")
    print(f"\n💡 Tips:")
    print(f"   - Values in CSV represent activity multipliers (0.0 = no activity, 1.0 = full activity)")
    print(f"   - You can create user clusters by giving similar users similar patterns")
    print(f"   - Use different patterns to simulate business hours, night owls, early birds, etc.")
    
    return 0

if __name__ == "__main__":
    exit(main())
