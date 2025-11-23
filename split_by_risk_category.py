#!/usr/bin/env python3
"""
Script to split SafeAgentBench dataset by risk categories.
Each task can appear in multiple category files if it has multiple risk categories.
"""

import json
import os
from collections import defaultdict

# Define the 10 risk categories
RISK_CATEGORIES = [
    "Fire Hazard",
    "Electrical Shock",
    "Explosion",
    "Poisoning/Ingestion",
    "Slip Hazard",
    "Liquid and Spill Damage",
    "Breakage and Dropping",
    "Misuse of Electrical Appliances",
    "Furniture and Decor Damage",
    "Damage to Small Items"
]

# Input and output paths
INPUT_FILE = r"d:\10.4\AgentSpec-master\ResponseSpec\datasets\embody_agent\SafeAgentBench\dataset\unsafe_detailed_1009.jsonl"
OUTPUT_DIR = r"d:\10.4\AgentSpec-master\ResponseSpec\datasets\embody_agent\SafeAgentBench\dataset_scene_base"

def normalize_category(category):
    """Normalize category names to match the standard list."""
    category = category.strip()
    
    # Handle variations in naming
    mappings = {
        "Electrical Shock Hazard": "Electrical Shock",
        "Explosion Hazard": "Explosion",
        "Poisoning/Ingestion Hazard": "Poisoning/Ingestion",
        "Harmful Shards Hazard": "Slip Hazard",  # Assuming broken glass/shards are slip hazards
    }
    
    return mappings.get(category, category)

def main():
    # Dictionary to store tasks by category
    category_tasks = defaultdict(list)
    
    # Read the JSONL file
    print(f"Reading from: {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                task = json.loads(line)
                risk_category = task.get('risk_category', '')
                
                # Split by comma if multiple categories exist
                categories = [cat.strip() for cat in risk_category.split(',')]
                
                # Normalize and add task to each category
                for category in categories:
                    normalized = normalize_category(category)
                    if normalized in RISK_CATEGORIES:
                        category_tasks[normalized].append(task)
                    else:
                        print(f"Warning: Unknown category '{category}' (normalized: '{normalized}') at line {line_num}")
                        
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
                continue
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Write tasks to separate JSON files for each category
    print(f"\nWriting to: {OUTPUT_DIR}")
    for category in RISK_CATEGORIES:
        tasks = category_tasks[category]
        
        # Create safe filename from category name
        filename = category.replace('/', '_').replace(' ', '_').lower() + '.json'
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        # Write tasks to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
        
        print(f"  {category}: {len(tasks)} tasks -> {filename}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total categories: {len(RISK_CATEGORIES)}")
    print(f"  Total unique tasks processed: {sum(1 for _ in open(INPUT_FILE, 'r', encoding='utf-8'))}")
    print(f"  Total task instances across all categories: {sum(len(tasks) for tasks in category_tasks.values())}")

if __name__ == "__main__":
    main()
