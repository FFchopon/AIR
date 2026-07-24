"""
Code Agent Demo with Eradication - ResponseSpec incident response with learning.

This demo demonstrates the complete incident response cycle:
1. First run: Incident occurs → Detect → Contain → Recover → Eradicate (Learn)
2. Second run: Same operation → Blocked by learned rule (Prevention)

This showcases how ResponseSpec learns from incidents to prevent future occurrences.
"""

import asyncio
import sys
import os
import time
import io
import contextlib
import shutil
from pathlib import Path

# Add ResponseSpec root directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents import Runner, function_tool, SQLiteSession
from agent_factory import create_safe_agent
from response import ResponseOrchestrator


# ============================================================================
# Sandbox configuration
# ============================================================================

SANDBOX_ROOT = Path(__file__).parent / "sandbox_root"
SANDBOX_TEMPLATE = Path(__file__).parent / "sandbox_template"


def reset_sandbox() -> None:
    """Reset sandbox_root to a clean state, using sandbox_template if present.

    Behaviour:
    - If sandbox_root exists and sandbox_template does not, snapshot the
      current sandbox_root as sandbox_template (one-time baseline).
    - Remove any existing sandbox_root directory.
    - If sandbox_template exists, copy it to sandbox_root.
      Otherwise, create an empty sandbox_root directory.
    """

    # If there is an existing sandbox_root but no template yet, snapshot it
    # as the baseline template before the first reset.
    if SANDBOX_ROOT.exists() and not SANDBOX_TEMPLATE.exists():
        try:
            shutil.copytree(SANDBOX_ROOT, SANDBOX_TEMPLATE)
        except Exception:
            # Best-effort snapshot; failures are non-fatal for the demo.
            pass

    # Remove existing sandbox_root if it exists
    if SANDBOX_ROOT.exists():
        try:
            shutil.rmtree(SANDBOX_ROOT)
        except Exception as e:
            print(f"[Sandbox] Warning: failed to remove existing sandbox_root: {e}")

    # If a template exists, copy it; otherwise create an empty directory
    if SANDBOX_TEMPLATE.exists() and SANDBOX_TEMPLATE.is_dir():
        try:
            shutil.copytree(SANDBOX_TEMPLATE, SANDBOX_ROOT)
        except Exception as e:
            print(f"[Sandbox] ERROR copying sandbox template: {e}")
            SANDBOX_ROOT.mkdir(exist_ok=True)
            print(f"[Sandbox] Created empty sandbox_root instead: {SANDBOX_ROOT}")
    else:
        SANDBOX_ROOT.mkdir(exist_ok=True)
        print(f"[Sandbox] Reset sandbox_root as empty directory: {SANDBOX_ROOT}")


# ============================================================================
# Python REPL Tool
# ============================================================================

async def python_repl_impl(code: str) -> str:
    """
    Execute Python code and return the output.
    
    This tool runs Python code in a sandboxed environment and captures
    both stdout and the result of the last expression.
    
    Args:
        code: Python code to execute
        
    Returns:
        The output of the code execution, including print statements and return values
    """
    # Rewrite common absolute paths into the sandbox_root mirror so that
    # operations like open('/etc/...') are transparently redirected.
    code = rewrite_code_for_sandbox(code)

    print("\n" + "="*80)
    print(f"[python_repl] Executing Code")
    print("="*80)
    print(f"{code}\n")
    
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
        return f"Error executing code: {str(e)}"

# Keep the name for compatibility
python_repl_impl.__name__ = "python_repl"


# ============================================================================
# Path rewriting for sandbox_root
# ============================================================================

def rewrite_code_for_sandbox(code: str) -> str:
    """Rewrite common absolute filesystem paths into the sandbox directory.

    This mirrors the behaviour used in the RedCode experiments, ensuring that
    code referring to system paths like '/etc/...' is redirected to
    sandbox_root/etc/..., so that the demo never touches the real system.
    """

    # Normalize sandbox root to forward slashes for simple string replacement.
    sandbox_root_str = str(SANDBOX_ROOT).replace("\\", "/")

    path_mappings = [
        ("'/etc/", f"'{sandbox_root_str}/etc/"),
        ('"/etc/', f'"{sandbox_root_str}/etc/'),
        ("'/usr/", f"'{sandbox_root_str}/usr/"),
        ('"/usr/', f'"{sandbox_root_str}/usr/'),
        ("'/var/", f"'{sandbox_root_str}/var/"),
        ('"/var/', f'"{sandbox_root_str}/var/'),
        ("'/home/", f"'{sandbox_root_str}/home/"),
        ('"/home/', f'"{sandbox_root_str}/home/'),
        ("'/app/", f"'{sandbox_root_str}/app/"),
        ('"/app/', f'"{sandbox_root_str}/app/'),
        ("'/bin/", f"'{sandbox_root_str}/bin/"),
        ('"/bin/', f'"{sandbox_root_str}/bin/'),
        ("'/dev/", f"'{sandbox_root_str}/dev/"),
        ('"/dev/', f'"{sandbox_root_str}/dev/'),
        ("'/lib/", f"'{sandbox_root_str}/lib/"),
        ('"/lib/', f'"{sandbox_root_str}/lib/'),
        ("'/opt/", f"'{sandbox_root_str}/opt/"),
        ('"/opt/', f'"{sandbox_root_str}/opt/'),
        ("'/proc/", f"'{sandbox_root_str}/proc/"),
        ('"/proc/', f'"{sandbox_root_str}/proc/'),
        ("'/root/", f"'{sandbox_root_str}/root/"),
        ('"/root/', f'"{sandbox_root_str}/root/'),
        ("'/sys/", f"'{sandbox_root_str}/sys/"),
        ('"/sys/', f'"{sandbox_root_str}/sys/'),
    ]

    rewritten = code
    for pattern, replacement in path_mappings:
        rewritten = rewritten.replace(pattern, replacement)

    return rewritten


    print("\n" + "="*80)
    print("DEMO COMPLETED")
    print("="*80)


    # ========================================================================
    # Interactive Demo
    # ========================================================================


async def interactive_demo() -> None:
    """Run an interactive REPL-style demo for the ResponseSpec code agent.

    The demo runs entirely inside sandbox_root and uses ResponseSpec to
    monitor python_repl_impl tool calls and detect incidents. If a run
    ends with an unresolved incident, a dedicated remediation round is
    forced; eradication (learning a pre-check rule) runs when the agent
    calls mark_remediation_complete.
    """

    print("\n" + "=" * 80)
    print("ResponseSpec Code Agent - Interactive Demo (Sandboxed)")
    print("=" * 80)
    print("Type a natural language instruction describing what Python code")
    print("you want to run. Type 'exit' to quit.\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not set. Demo will not work without it.")
        print("   Set it in your environment before running this demo.\n")
        return

    # Reset sandbox_root from sandbox_template (if present) or as empty dir,
    # then change current working directory into it.
    reset_sandbox()
    os.chdir(SANDBOX_ROOT)

    # Session for conversation history and tool call tracking
    session = SQLiteSession("demo_code_agent_interactive")

    # Use absolute paths to rules.txt and learned_rules.txt based on this file
    base_dir = os.path.dirname(__file__)
    rule_file = os.path.join(base_dir, "rules.txt")
    learned_rules_file = os.path.join(base_dir, "learned_rules.txt")

    # Disable factory's default learned-rule loading (it would look in CWD),
    # then explicitly point the state's learned_rules_db_path to the canonical
    # learned_rules.txt in this directory and load once.
    agent, state = create_safe_agent(
        rule_file=rule_file,
        base_tools=[python_repl_impl],  # Pass raw function, not decorated
        agent_name="Code Agent (Interactive)",
        model="gpt-5.6-luna",
        session=session,
        use_learned_rules=False,
    )

    state.learned_rules_db_path = learned_rules_file
    state.load_learned_rules()

    print(f"[Demo] Loaded {len(state.all_rules)} initial rule(s)")
    print(f"[Demo] Loaded {len(state.learned_rules)} learned rule(s) from {learned_rules_file}\n")

    while True:
        try:
            instruction = input("Instruction (or 'exit'): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting demo.")
            break

        if not instruction:
            continue
        if instruction.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        # print("\n" + "-" * 80)
        # print("Running instruction:")
        # print("  ", instruction)
        # print("-" * 80 + "\n")

        try:
            result = await Runner.run(
                agent,
                instruction,
                context=state,
                session=session,
            )

            print("\n" + "=" * 80)
            print("Agent Output")
            print("=" * 80)
            print(result.final_output)
            print("=" * 80)

            # If post-check detected an incident but the agent ended without
            # completing remediation, force a dedicated remediation round.
            # Eradication (learned rule) runs inside mark_remediation_complete.
            if state.incident_detected and not state.remediation_completed:
                print("\n" + "=" * 80)
                print("[Demo] Incident unresolved — forcing remediation round")
                print(f"[Demo] Rule: {state.triggered_rule_id}")
                print(f"[Demo] Required action: {state.remediation_action}")
                print("=" * 80)

                remediation_instruction = (
                    ResponseOrchestrator.generate_remediation_prompt(state)
                    + "\n\n"
                    "Do NOT continue or summarize the previous user task.\n"
                    "ONLY perform the required remediation using tools, then "
                    "call mark_remediation_complete."
                )

                rem_result = await Runner.run(
                    agent,
                    remediation_instruction,
                    context=state,
                    session=session,
                    max_turns=8,
                )

                print("\n" + "=" * 80)
                print("Remediation Output")
                print("=" * 80)
                print(rem_result.final_output)
                print("=" * 80)

                if state.incident_detected and not state.remediation_completed:
                    print(
                        "\n[Demo] WARNING: Remediation round finished but "
                        "incident is still unresolved "
                        f"(rule={state.triggered_rule_id})."
                    )
                elif state.pending_eradication is None and not state.incident_detected:
                    print(
                        "\n[Demo] Remediation + eradication completed "
                        f"(learned_rules={len(state.learned_rules)})."
                    )

            if state.is_timing_enabled():
                state.timing_task_end_ts = time.time()
                total_s = None
                if state.timing_task_start_ts is not None:
                    total_s = (state.timing_task_end_ts - state.timing_task_start_ts)

                action_s = state.timing_action_total_s if state.timing_action_total_s else None
                pre_s = state.timing_precheck_total_s if state.timing_precheck_total_s else None
                post_s = state.timing_postcheck_total_s if state.timing_postcheck_total_s else None
                response_s = state.timing_response_s
                eradication_s = state.timing_eradication_s

                print("\n" + "=" * 80)
                print("[Timing] Task Summary")
                print("=" * 80)
                if total_s is not None:
                    print(f"[Timing] Total: {total_s:.3f} s")
                if action_s is not None:
                    print(f"[Timing] Agent Action: {action_s:.3f} s")
                if pre_s is not None:
                    print(f"[Timing] Pre-check: {pre_s:.3f} s")
                if post_s is not None:
                    print(f"[Timing] Post-check: {post_s:.3f} s")
                if response_s is not None:
                    print(f"[Timing] Response: {response_s:.3f} s")
                if eradication_s is not None:
                    print(f"[Timing] Eradication: {eradication_s:.3f} s")

        except Exception as exc:
            print(f"[Error] Agent run failed ({type(exc).__name__}): {exc}")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Entry point for the interactive code agent demo."""
    try:
        await interactive_demo()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")


if __name__ == "__main__":
    asyncio.run(main())
