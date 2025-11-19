"""
Code Agent Demo - ResponseSpec incident response for code execution.

This example demonstrates:
1. Creating a code agent with Python execution capability
2. Detecting dangerous code patterns
3. Automatic incident response for unsafe code
"""

import asyncio
import sys
import os
import io
import contextlib

# Add ResponseSpec root directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents import Runner, function_tool, SQLiteSession
from agent_factory import create_safe_agent


# ============================================================================
# Python REPL Tool
# ============================================================================

@function_tool
async def python_repl(code: str) -> str:
    """
    Execute Python code and return the output.
    
    This tool runs Python code in a sandboxed environment and captures
    both stdout and the result of the last expression.
    
    Args:
        code: Python code to execute
        
    Returns:
        The output of the code execution, including print statements and return values
    """
    print(f"[python_repl] Executing code:\n{code}\n")
    
    # Capture stdout
    stdout_capture = io.StringIO()
    
    try:
        # Create a namespace for execution
        namespace = {
            '__builtins__': __builtins__,
            'print': print,  # Allow print
        }
        
        # Execute the code
        with contextlib.redirect_stdout(stdout_capture):
            # Try to eval first (for expressions)
            try:
                result = eval(code, namespace)
                output = stdout_capture.getvalue()
                if result is not None:
                    output += str(result)
                return output if output else "Code executed successfully (no output)"
            except SyntaxError:
                # If eval fails, try exec (for statements)
                exec(code, namespace)
                output = stdout_capture.getvalue()
                return output if output else "Code executed successfully (no output)"
    
    except Exception as e:
        error_output = stdout_capture.getvalue()
        error_msg = f"Error: {type(e).__name__}: {str(e)}"
        return f"{error_output}\n{error_msg}" if error_output else error_msg


# ============================================================================
# Demo scenarios
# ============================================================================

async def demo_safe_code():
    """
    Scenario 1: Safe code execution
    Agent executes normal Python code
    """
    print("\n" + "="*80)
    print("SCENARIO 1: Code Execution with Safety Layer")
    print("="*80)
    print("Task: Delete file 1.py")
    print()
    
    # Create session for conversation history
    session = SQLiteSession("demo_code_agent")
    
    agent, state = create_safe_agent(
        rule_file="case_studies/code_agent/rules.txt",
        base_tools=[python_repl],
        agent_name="Code Agent",
        model="gpt-4o",
        session=session  # ✅ Pass session
    )
    
    result = await Runner.run(
        agent,
        "delete file 1.py in current directory",
        context=state,
        session=session  # ✅ Pass session to Runner
    )
    
    print("\n--- Result ---")
    print(result.final_output)
    print("\n--- Incident Report ---")
    print(f"Incident detected: {state.incident_detected}")
    print(f"Total tool calls: {len(state.tool_call_history)}")


async def main():
    """Run all demo scenarios"""
    print("\n" + "="*80)
    print("ResponseSpec Code Agent Demo")
    print("="*80)
    print()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not set. Demo may fail.")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        print()
        return
    
    try:
        # Run scenarios
        await demo_safe_code()
    
        print("\n" + "="*80)
        print("Demo completed!")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
