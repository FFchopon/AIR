"""
RedCode Experiment Runner

Interactive script to run RedCode dataset experiments on Code Agent with sandbox environment.
"""

import asyncio
import json
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents import Agent, Runner, SQLiteSession
from agent_factory import create_safe_agent


# ============================================================================
# Configuration
# ============================================================================

REDCODE_DATA_DIR = Path(__file__).parent.parent.parent / "datasets" / "code_agent" / "RedCode" / "RedCode-Exec" / "py2text_dataset_json"
SANDBOX_ROOT = Path(__file__).parent / "sandbox_root"
RESULTS_DIR = Path(__file__).parent / "experiment_results"

# Ensure results directory exists
RESULTS_DIR.mkdir(exist_ok=True)


# ============================================================================
# Path Rewriting for Sandbox
# ============================================================================

def rewrite_code_for_sandbox(code: str) -> str:
    """
    Rewrite file paths in generated code to use sandbox environment.
    
    Converts absolute paths like '/etc/passwd' to 'sandbox_root/etc/passwd'.
    """
    # Convert SANDBOX_ROOT to string and normalize to forward slashes (works on both Windows and Unix)
    sandbox_root_str = str(SANDBOX_ROOT).replace('\\', '/')
    
    # Common system paths to rewrite - using simple string replacement to avoid regex issues
    path_mappings = [
        ("'/etc/", f"'{sandbox_root_str}/etc/"),
        ('"/etc/', f'"{sandbox_root_str}/etc/'),
        ("'/usr/", f"'{sandbox_root_str}/usr/"),
        ('"/usr/', f'"{sandbox_root_str}/usr/'),
        ("'/var/", f"'{sandbox_root_str}/var/"),
        ('"/var/', f'"{sandbox_root_str}/var/'),
        ("'/home/", f"'{sandbox_root_str}/home/"),
        ('"/home/', f'"{sandbox_root_str}/home/'),
    ]
    
    rewritten_code = code
    for pattern, replacement in path_mappings:
        rewritten_code = rewritten_code.replace(pattern, replacement)
    
    return rewritten_code


def create_sandbox_aware_python_repl():
    """
    Create a python_repl function that automatically rewrites paths to sandbox.
    """
    async def python_repl_impl(code: str) -> str:
        """
        Execute Python code with automatic path rewriting to sandbox environment.
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result or error message
        """
        # Rewrite paths to use sandbox
        sandboxed_code = rewrite_code_for_sandbox(code)
        
        print(f"\n{'='*70}")
        print(f"[Sandbox] Original code paths rewritten to sandbox")
        print(f"{'='*70}")
        if sandboxed_code != code:
            print(f"[Sandbox] Path rewriting applied")
        
        print(f"[python_repl] Executing code:")
        print(sandboxed_code)
        print()
        
        try:
            # Create execution environment
            exec_globals = {}
            exec_locals = {}
            
            # Execute the code
            exec(sandboxed_code, exec_globals, exec_locals)
            
            # Get the result (if any)
            if exec_locals:
                result = str(exec_locals.get('result', 'Code executed successfully (no output)'))
            else:
                result = 'Code executed successfully (no output)'
            
            return result
            
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    # Set function name for tool registration
    python_repl_impl.__name__ = "python_repl"
    
    return python_repl_impl


# ============================================================================
# RedCode Data Loading
# ============================================================================

def load_redcode_data(index: int) -> List[Dict[str, Any]]:
    """
    Load RedCode dataset for a specific index.
    
    Args:
        index: Index number (1-27)
        
    Returns:
        List of task dictionaries
    """
    filename = f"index{index}_30_codes_full.json"
    filepath = REDCODE_DATA_DIR / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"RedCode data file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


# ============================================================================
# Experiment Execution
# ============================================================================

async def run_single_task(
    task: Dict[str, Any],
    session: SQLiteSession,
    index: int,
    task_num: int
) -> Dict[str, Any]:
    """
    Run a single RedCode task.
    
    Args:
        task: Task dictionary from RedCode dataset
        session: SQLite session for conversation history
        index: RedCode index (1-27)
        task_num: Task number (1-30)
        
    Returns:
        Experiment result dictionary
    """
    print("\n" + "="*80)
    print(f"TASK: Index {index}_{task_num}")
    print("="*80)
    
    # Extract task information
    task_prompt = task.get('Text_summary', '')
    expected_result = task.get('expected_result', 'unknown')
    original_code = task.get('Code', '')
    
    print(f"\n[Task] Prompt:")
    print(f"{task_prompt[:200]}..." if len(task_prompt) > 200 else task_prompt)
    print(f"\n[Task] Expected: {expected_result}")
    
    # Create agent with sandbox-aware python_repl
    python_repl = create_sandbox_aware_python_repl()
    
    agent, state = create_safe_agent(
        rule_file="./rules.txt",
        base_tools=[python_repl],
        agent_name=f"Code Agent (RedCode {index}_{task_num})",
        model="gpt-4o",
        session=session
    )
    
    # Run the task
    try:
        result = await Runner.run(
            agent,
            task_prompt,
            context=state,
            session=session
        )
        
        final_output = result.final_output
        
        # Check if incident was detected
        incident_detected = state.incident_detected
        learned_rules_count = len(state.learned_rules)
        
        print(f"\n[Result] Incident detected: {incident_detected}")
        print(f"[Result] Learned rules: {learned_rules_count}")
        print(f"[Result] Output: {final_output[:200]}..." if len(final_output) > 200 else f"[Result] Output: {final_output}")
        
        return {
            'index': f"{index}_{task_num}",
            'prompt': task_prompt,
            'expected_result': expected_result,
            'original_code': original_code,
            'agent_output': final_output,
            'incident_detected': incident_detected,
            'learned_rules_count': learned_rules_count,
            'learned_rules': [
                {
                    'id': rule.id,
                    'condition': rule.incident_condition,
                    'confidence': rule.confidence
                }
                for rule in state.learned_rules
            ],
            'status': 'completed'
        }
        
    except Exception as e:
        print(f"\n[Error] Task failed: {e}")
        return {
            'index': f"{index}_{task_num}",
            'prompt': task_prompt,
            'expected_result': expected_result,
            'error': str(e),
            'status': 'failed'
        }


async def run_experiment(index: int, task_numbers: List[int]):
    """
    Run RedCode experiment for specified tasks.
    
    Args:
        index: RedCode index (1-27)
        task_numbers: List of task numbers to run (1-30)
    """
    print("\n" + "="*80)
    print(f"REDCODE EXPERIMENT: Index {index}")
    print(f"Tasks: {task_numbers}")
    print("="*80)
    
    # Load RedCode data
    try:
        all_tasks = load_redcode_data(index)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return
    
    # Create session
    session = SQLiteSession(f"redcode_exp_index{index}")
    await session.clear_session()
    
    # Run tasks
    results = []
    for task_num in task_numbers:
        # Find the task (1-indexed in dataset)
        task_index = task_num - 1
        if task_index >= len(all_tasks):
            print(f"\n⚠️ Warning: Task {task_num} not found in index {index}")
            continue
        
        task = all_tasks[task_index]
        
        # Run the task
        result = await run_single_task(task, session, index, task_num)
        results.append(result)
        
        # Small delay between tasks
        await asyncio.sleep(1)
    
    # Save results
    result_file = RESULTS_DIR / f"index{index}_results.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("EXPERIMENT COMPLETED")
    print("="*80)
    print(f"\n📊 Results saved to: {result_file}")
    print(f"\n✅ Completed: {sum(1 for r in results if r['status'] == 'completed')}/{len(results)}")
    print(f"❌ Failed: {sum(1 for r in results if r['status'] == 'failed')}/{len(results)}")
    print(f"🚨 Incidents detected: {sum(1 for r in results if r.get('incident_detected', False))}/{len(results)}")
    print(f"🎓 Total learned rules: {sum(r.get('learned_rules_count', 0) for r in results)}")


# ============================================================================
# Interactive CLI
# ============================================================================

def get_user_choice():
    """
    Interactive CLI to get user's experiment configuration.
    
    Returns:
        Tuple of (index, task_numbers)
    """
    print("\n" + "="*80)
    print("REDCODE EXPERIMENT RUNNER")
    print("="*80)
    
    # Step 1: Select index
    while True:
        try:
            index = int(input("\n📋 Select RedCode index (1-27): "))
            if 1 <= index <= 27:
                break
            else:
                print("❌ Invalid index. Please enter a number between 1 and 27.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
    
    # Step 2: Select execution mode
    print(f"\n📝 Selected: Index {index}")
    print("\n🎯 Execution mode:")
    print("  1. Single task (1-30)")
    print("  2. Batch execution (all 30 tasks)")
    print("  3. Custom range")
    
    while True:
        try:
            mode = int(input("\nSelect mode (1/2/3): "))
            if mode in [1, 2, 3]:
                break
            else:
                print("❌ Invalid mode. Please enter 1, 2, or 3.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
    
    # Step 3: Get task numbers based on mode
    if mode == 1:
        # Single task
        while True:
            try:
                task_num = int(input("\n🎯 Select task number (1-30): "))
                if 1 <= task_num <= 30:
                    task_numbers = [task_num]
                    break
                else:
                    print("❌ Invalid task number. Please enter a number between 1 and 30.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
    
    elif mode == 2:
        # Batch execution (all 30)
        task_numbers = list(range(1, 31))
        print(f"\n✅ Will execute all 30 tasks")
    
    else:
        # Custom range
        while True:
            try:
                start = int(input("\n🎯 Start task number (1-30): "))
                end = int(input("🎯 End task number (1-30): "))
                if 1 <= start <= end <= 30:
                    task_numbers = list(range(start, end + 1))
                    print(f"\n✅ Will execute tasks {start}-{end} ({len(task_numbers)} tasks)")
                    break
                else:
                    print("❌ Invalid range. Please ensure 1 <= start <= end <= 30.")
            except ValueError:
                print("❌ Invalid input. Please enter numbers.")
    
    # Confirmation
    print(f"\n{'='*80}")
    print(f"📋 Configuration:")
    print(f"  - Index: {index}")
    print(f"  - Tasks: {task_numbers}")
    print(f"  - Total: {len(task_numbers)} task(s)")
    print(f"{'='*80}")
    
    confirm = input("\n🚀 Start experiment? (y/n): ")
    if confirm.lower() != 'y':
        print("\n❌ Experiment cancelled.")
        sys.exit(0)
    
    return index, task_numbers


# ============================================================================
# Main
# ============================================================================

async def main():
    """Main entry point."""
    # Get user configuration
    index, task_numbers = get_user_choice()
    
    # Run experiment
    await run_experiment(index, task_numbers)


if __name__ == "__main__":
    asyncio.run(main())
