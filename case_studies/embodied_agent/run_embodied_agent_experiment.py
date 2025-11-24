"""
Embodied Agent Experiment Runner

Run SafeAgentBench experiments with LLM-based Embodied Agent.
Similar structure to run_redcode_experiment.py but for embodied tasks.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "sandbox_root"))

from agents import Runner, SQLiteSession
from sandbox_manager import SandboxManager
from agent_factory import create_safe_embodied_agent
from embodied_agent import (
    create_embodied_agent,
    set_sandbox,
    ALL_TOOLS,
    EMBODIED_BASE_INSTRUCTIONS,
    _turn_on,
)


# ============================================================================
# Configuration
# ============================================================================

DATASET_DIR = Path(__file__).parent.parent.parent / "datasets" / "embody_agent" / "SafeAgentBench" / "dataset_scene_base"
RESULTS_DIR = Path(__file__).parent / "experiment_results"

# Ensure results directory exists
RESULTS_DIR.mkdir(exist_ok=True)


# ============================================================================
# Dataset Loading
# ============================================================================

def load_tasks(risk_category: str) -> List[Dict[str, Any]]:
    """
    Load tasks from dataset file.
    
    Args:
        risk_category: Risk category name (e.g., "Fire Hazard")
        
    Returns:
        List of task dictionaries
    """
    # Map risk category to filename
    category_files = {
        "Fire Hazard": "fire_hazard.json",
        "Explosion Hazard": "explosion.json",
        "Electrical Shock Hazard": "electrical_shock.json",
        "Poisoning/Ingestion Hazard": "poisoning_ingestion.json",
        "Slip Hazard": "slip_hazard.json",
        "Suffocation Hazard": "suffocation.json",
        "Burn Hazard": "burn.json",
        "Scalding Hazard": "scalding.json",
        "Cuts and Lacerations": "cuts.json",
        "Physical Injury": "physical_injury.json",
    }
    
    filename = category_files.get(risk_category)
    if not filename:
        raise ValueError(f"Unknown risk category: {risk_category}")
    
    filepath = DATASET_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    return tasks


# ============================================================================
# Task Execution
# ============================================================================

async def run_single_task(
    task: Dict[str, Any],
    task_num: int,
    risk_category: str,
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Run a single embodied task with the agent.
    
    Args:
        task: Task specification from dataset
        task_num: Task number
        risk_category: Risk category
        model: OpenAI model to use
        
    Returns:
        Result dictionary
    """
    instruction = task.get('instruction', '')
    final_state = task.get('final_state')
    
    print(f"\n{'='*80}")
    print(f"TASK #{task_num}")
    print(f"{'='*80}")
    print(f"Instruction: {instruction}")
    print(f"Risk Category: {risk_category}")
    print(f"{'='*80}\n")
    
    # Initialize sandbox environment for this task
    sandbox = SandboxManager(risk_category)
    sandbox.reset_for_task(task)
    set_sandbox(sandbox)
    
    env = sandbox.get_environment()
    print(f"\n[Sandbox] Environment initialized: {env.scene_name}")
    print(f"[Sandbox] Total objects: {len(env.objects)}")
    
    # Show key objects mentioned in instruction
    mentioned_objects = []
    for obj_name in env.objects.keys():
        if obj_name.lower() in instruction.lower():
            mentioned_objects.append(obj_name)
    
    if mentioned_objects:
        print(f"[Sandbox] Key objects for this task:")
        for obj_name in mentioned_objects:
            obj = env.get_object(obj_name)
            print(f"  • {obj_name} ({obj.object_type}): {obj.get_location_description()}")
    
    # Create session for conversation history and tool call tracking
    session = SQLiteSession(":memory:")

    # Create a ResponseSpec-enabled Embodied Agent using agent_factory.
    # Use the embodied_agent-specific rules file in this case_study folder.
    rule_file = str(Path(__file__).parent / "rules.txt")

    agent, incident_state = create_safe_embodied_agent(
        rule_file=rule_file,
        tools=ALL_TOOLS,
        base_instructions=EMBODIED_BASE_INSTRUCTIONS,
        agent_name=f"Embodied Agent (Task {task_num})",
        model=model,
        session=session,
        turn_on_impl=_turn_on,
    )

    # Snapshot how many learned rules were present before this task
    initial_learned_rules_count = len(incident_state.learned_rules)
    
    print(f"\n{'='*80}")
    print("AGENT EXECUTION")
    print(f"{'='*80}\n")
    
    # Run the task with the safe Embodied Agent. All tool calls go through
    # the OpenAI Agent SDK Runner, with IncidentState as context, so that
    # ResponseSpec hooks can observe and react to tool usage.
    try:
        result = await Runner.run(
            agent,
            instruction,
            context=incident_state,
            session=session,
            max_turns=15,
        )
        
        final_output = result.final_output

        # Collect safety-related information from IncidentState
        incident_detected = getattr(incident_state, "incident_detected", False)
        incident_occurred = getattr(
            incident_state,
            "incident_occurred",
            incident_detected,
        )
        total_learned_rules_count = len(getattr(incident_state, "learned_rules", []))
        new_learned_rules_count = max(
            0,
            total_learned_rules_count - initial_learned_rules_count,
        )
        stop_after_eradication = getattr(
            incident_state,
            "stop_after_eradication",
            False,
        )

        # Verify final state
        state_matches = sandbox.verify_final_state()
        
        print(f"\n{'='*80}")
        print("TASK RESULT")
        print(f"{'='*80}")
        print(f"\n[Agent] {final_output}")
        print(f"\n[Verification] Final State Matches: {'✓ YES' if state_matches else '✗ NO'}")
        print(f"[Verification] Total Actions: {len(sandbox.action_history)}")
        
        # Get state diff
        state_diff = sandbox.get_state_diff()
        
        # Display state changes
        if state_diff.get('changed_objects'):
            print(f"\n[State Changes]")
            for change in state_diff['changed_objects']:
                print(f"  • {change['object']}:")
                for prop, values in change['changes'].items():
                    print(f"    - {prop}: {values['from']} → {values['to']}")
        else:
            print(f"\n[State Changes] No changes detected")
        
        return {
            'task_num': task_num,
            'instruction': instruction,
            'risk_category': risk_category,
            'agent_output': final_output,
            'final_state_matches': state_matches,
            'expected_final_state': final_state,
            'action_count': len(sandbox.action_history),
            'actions': [
                {
                    'action': record.action_name,
                    'args': record.arguments,
                    'result': record.result,
                    'success': record.success
                }
                for record in sandbox.action_history
            ],
            'state_diff': state_diff,
            # ResponseSpec / safety-related fields
            'incident_detected': incident_detected,
            'incident_occurred': incident_occurred,
            'learned_rules_count': total_learned_rules_count,
            'new_learned_rules_count': new_learned_rules_count,
            'learned_rules': [
                {
                    'id': rule.id,
                    'condition': rule.incident_condition,
                    'confidence': getattr(rule, 'confidence', None),
                }
                for rule in getattr(incident_state, 'learned_rules', [])
            ],
            'stop_after_eradication': stop_after_eradication,
            'status': 'completed'
        }
        
    except Exception as e:
        print(f"\n[Error] Task failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'task_num': task_num,
            'instruction': instruction,
            'risk_category': risk_category,
            'error': str(e),
            'status': 'failed'
        }


async def run_experiment(
    risk_category: str,
    task_numbers: List[int],
    model: str = "gpt-4o-mini"
):
    """
    Run experiment for specified tasks.
    
    Args:
        risk_category: Risk category (e.g., "Fire Hazard")
        task_numbers: List of task numbers to run
        model: OpenAI model to use
    """
    print(f"\n{'='*80}")
    print(f"EMBODIED AGENT EXPERIMENT")
    print(f"Risk Category: {risk_category}")
    print(f"Tasks: {task_numbers}")
    print(f"Model: {model}")
    print(f"{'='*80}\n")
    
    # Load tasks
    try:
        all_tasks = load_tasks(risk_category)
        print(f"[Dataset] Loaded {len(all_tasks)} tasks from {risk_category}")
    except Exception as e:
        print(f"[Error] Failed to load dataset: {e}")
        return
    
    # Run selected tasks
    results = []
    for task_num in task_numbers:
        if task_num < 1 or task_num > len(all_tasks):
            print(f"\n[Warning] Task {task_num} out of range (1-{len(all_tasks)}), skipping")
            continue
        
        task = all_tasks[task_num - 1]
        result = await run_single_task(task, task_num, risk_category, model)
        results.append(result)
        
        # Save individual result
        safe_category = risk_category.replace(' ', '_').replace('/', '_')
        result_file = RESULTS_DIR / f"{safe_category}_task_{task_num}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[Saved] {result_file}")
    
    # Save batch results
    safe_category = risk_category.replace(' ', '_').replace('/', '_')
    batch_file = RESULTS_DIR / f"{safe_category}_batch_results.json"
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump({
            'risk_category': risk_category,
            'model': model,
            'task_count': len(results),
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"EXPERIMENT COMPLETED")
    print(f"{'='*80}")
    print(f"Total tasks: {len(results)}")
    print(f"Completed: {sum(1 for r in results if r['status'] == 'completed')}")
    print(f"Failed: {sum(1 for r in results if r['status'] == 'failed')}")
    print(f"Final state matches: {sum(1 for r in results if r.get('final_state_matches', False))}")
    print(f"\nResults saved to: {batch_file}")


# ============================================================================
# Interactive Menu
# ============================================================================

RISK_CATEGORIES = {
    "1": {"name": "Fire Hazard", "file": "fire_hazard.json", "implemented": True},
    "2": {"name": "Electrical Shock Hazard", "file": "electrical_shock.json", "implemented": True},
    "3": {"name": "Explosion Hazard", "file": "explosion.json", "implemented": True},
    "4": {"name": "Poisoning/Ingestion Hazard", "file": "poisoning_ingestion.json", "implemented": True},
    "5": {"name": "Slip Hazard", "file": "slip_hazard.json", "implemented": True},
    "6": {"name": "Suffocation Hazard", "file": "suffocation.json", "implemented": False},
    "7": {"name": "Burn Hazard", "file": "burn.json", "implemented": False},
    "8": {"name": "Scalding Hazard", "file": "scalding.json", "implemented": False},
    "9": {"name": "Cuts and Lacerations", "file": "cuts.json", "implemented": False},
    "10": {"name": "Physical Injury", "file": "physical_injury.json", "implemented": False},
}


def show_risk_category_menu():
    """Display risk category selection menu."""
    print("\n" + "=" * 80)
    print("EMBODIED AGENT EXPERIMENT - INTERACTIVE MODE")
    print("=" * 80)
    print("\nSelect Risk Category:")
    print()
    
    for key, info in sorted(RISK_CATEGORIES.items()):
        status = "✓ Ready" if info["implemented"] else "⚠️  Not Implemented"
        print(f"  {key}. {info['name']:<30} [{status}]")
    
    print()
    print("  0. Exit")
    print()


def select_tasks_interactive(total_tasks: int):
    """Interactive task selection."""
    print(f"\n📋 Available Tasks: 1-{total_tasks}")
    print("\nOptions:")
    print("  - Enter single task number (e.g., '5')")
    print("  - Enter multiple tasks (e.g., '1,3,5')")
    print("  - Enter range (e.g., '1-5')")
    print("  - Enter 'all' to run all tasks")
    print("  - Enter '0' to go back")
    print()
    
    while True:
        choice = input("Select tasks: ").strip()
        
        if choice == '0':
            return None
        
        if choice.lower() == 'all':
            return list(range(1, total_tasks + 1))
        
        try:
            task_numbers = []
            for part in choice.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    task_numbers.extend(range(start, end + 1))
                else:
                    task_numbers.append(int(part))
            
            # Validate
            if all(1 <= t <= total_tasks for t in task_numbers):
                return task_numbers
            else:
                print(f"❌ Invalid task number. Please enter 1-{total_tasks}")
        except ValueError:
            print("❌ Invalid input. Please try again.")


def interactive_mode():
    """Run in interactive mode."""
    while True:
        show_risk_category_menu()
        choice = input("Enter your choice: ").strip()
        
        if choice == '0':
            print("\n👋 Goodbye!")
            break
        
        if choice not in RISK_CATEGORIES:
            print("❌ Invalid choice. Please try again.")
            continue
        
        category_info = RISK_CATEGORIES[choice]
        
        if not category_info["implemented"]:
            print(f"\n⚠️  {category_info['name']} is not yet implemented.")
            print("   Currently available: Fire Hazard, Electrical Shock, Explosion, Poisoning/Ingestion, Slip Hazard")
            input("\nPress Enter to continue...")
            continue
        
        risk_category = category_info["name"]
        
        # Load tasks to get count
        try:
            all_tasks = load_tasks(risk_category)
            print(f"\n✓ Loaded {len(all_tasks)} tasks from {risk_category}")
        except Exception as e:
            print(f"❌ Failed to load dataset: {e}")
            input("\nPress Enter to continue...")
            continue
        
        # Select tasks
        task_numbers = select_tasks_interactive(len(all_tasks))
        
        if task_numbers is None:
            continue
        
        # Confirm
        print(f"\n📝 Will run {len(task_numbers)} task(s): {task_numbers}")
        confirm = input("Continue? (y/n): ").strip().lower()
        
        if confirm != 'y':
            continue
        
        # Run experiment
        print("\n" + "=" * 80)
        asyncio.run(run_experiment(risk_category, task_numbers, "gpt-4o-mini"))
        
        input("\n\nPress Enter to continue...")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Embodied Agent Experiments")
    parser.add_argument("--risk-category", type=str, default=None,
                       help="Risk category to test (if not provided, use interactive mode)")
    parser.add_argument("--tasks", type=str, default=None,
                       help="Task numbers to run (e.g., '1' or '1,2,3' or '1-5')")
    parser.add_argument("--model", type=str, default="gpt-4o-mini",
                       help="OpenAI model to use")
    parser.add_argument("--interactive", action="store_true",
                       help="Run in interactive mode")
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive or (args.risk_category is None and args.tasks is None):
        interactive_mode()
        return
    
    # Command-line mode
    if args.risk_category is None or args.tasks is None:
        print("❌ Please provide both --risk-category and --tasks, or use --interactive mode")
        return
    
    # Parse task numbers
    task_numbers = []
    for part in args.tasks.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            task_numbers.extend(range(start, end + 1))
        else:
            task_numbers.append(int(part))
    
    # Run experiment
    asyncio.run(run_experiment(args.risk_category, task_numbers, args.model))


if __name__ == "__main__":
    main()
