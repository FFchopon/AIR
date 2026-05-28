"""Embodied Agent Interactive Demo with ResponseSpec.

This script provides a minimal interactive demo for the embodied agent
integrated with ResponseSpec. It focuses on a single sandboxed scene
and lets you type natural-language instructions describing what the
agent should do in the environment.

The demo:
- Initializes an embodied sandbox environment (single risk category).
- Creates a ResponseSpec-enabled embodied agent using create_safe_embodied_agent.
- Runs a REPL where each instruction is handled with full incident
  detection, remediation, and eradication (learning pre-check rules).
"""

import asyncio
import sys
from pathlib import Path

# Add project root and sandbox_root to path
ROOT_DIR = Path(__file__).parent.parent.parent
SANDBOX_ROOT = Path(__file__).parent / "sandbox_root"

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SANDBOX_ROOT))

from agents import Runner, SQLiteSession
from agent_factory import create_safe_embodied_agent
from sandbox_manager import SandboxManager
from embodied_agent import (
    set_sandbox,
    ALL_TOOLS,
    EMBODIED_BASE_INSTRUCTIONS,
    _turn_on,
    _find,
    _pick,
    _open_receptacle,
    _close_receptacle,
    _turn_off,
    _break_object,
    _slice_object,
    _cook,
    _dirty,
    _clean,
    _put,
    _drop,
    _throw,
    _fillLiquid,
    _pour,
    _emptyLiquid,
)


async def interactive_demo() -> None:
    """Run an interactive REPL-style demo for the embodied agent.

    The demo uses a single sandbox environment (e.g., Fire Hazard scene)
    and a ResponseSpec-enabled embodied agent. Each natural-language
    instruction is executed with safety monitoring and possible
    eradication (learning new rules for pre-check).
    """

    print("\n" + "=" * 80)
    print("ResponseSpec Embodied Agent - Interactive Demo")
    print("=" * 80)
    print("Type a natural language instruction for the embodied agent.")
    # print("For example: 'Safely light the candle on the table' or")
    # print("'Put the hot pan somewhere safe'. Type 'reset' to reset the scene,")
    print("or 'exit' to quit.\n")

    # Initialize sandbox for a single risk category
    risk_category = "Fire Hazard"
    sandbox = SandboxManager(risk_category=risk_category)

    # Use a simple dummy task to initialize the environment template
    dummy_task = {"risk_category": risk_category}
    sandbox.reset_for_task(dummy_task)
    set_sandbox(sandbox)

    env = sandbox.get_environment()
    print(f"[Sandbox] Environment initialized: {env.scene_name}")
    # print(f"[Sandbox] Total objects: {len(env.objects)}\n")

    # Session for conversation history and safety tracking
    session = SQLiteSession("demo_embodied_agent_interactive")

    rule_file = str(Path(__file__).parent / "rules.txt")

    agent, state = create_safe_embodied_agent(
        rule_file=rule_file,
        tools=ALL_TOOLS,
        base_instructions=EMBODIED_BASE_INSTRUCTIONS,
        agent_name="Embodied Agent (Interactive)",
        model="gpt-5",
        session=session,
        turn_on_impl=_turn_on,
        find_impl=_find,
        pick_impl=_pick,
        open_receptacle_impl=_open_receptacle,
        close_receptacle_impl=_close_receptacle,
        turn_off_impl=_turn_off,
        break_object_impl=_break_object,
        slice_object_impl=_slice_object,
        cook_impl=_cook,
        dirty_impl=_dirty,
        clean_impl=_clean,
        put_impl=_put,
        drop_impl=_drop,
        throw_impl=_throw,
        fillLiquid_impl=_fillLiquid,
        pour_impl=_pour,
        emptyLiquid_impl=_emptyLiquid,
    )

    while True:
        try:
            instruction = input("Instruction (or 'reset' / 'exit'): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting demo.")
            break

        if not instruction:
            continue

        if instruction.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        if instruction.lower() == "reset":
            # Reset sandbox to pristine state for the same dummy task
            sandbox.reset_for_task(dummy_task)
            set_sandbox(sandbox)
            env = sandbox.get_environment()
            print("\n[Sandbox] Scene reset.")
            print(f"[Sandbox] Environment: {env.scene_name}")
            print(f"[Sandbox] Total objects: {len(env.objects)}\n")
            continue

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
                max_turns=10,
            )

            print("=" * 80)
            print("Agent Output")
            print("=" * 80)
            print(result.final_output)
            print("=" * 80)

            # Show a brief summary of current environment state
            # print("\n[Sandbox] Current Environment State Summary:")
            # print(sandbox.get_environment().get_state_summary())

        except Exception as exc:
            print(f"[Error] Agent run failed ({type(exc).__name__}): {exc}")


async def main() -> None:
    try:
        await interactive_demo()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")


if __name__ == "__main__":
    asyncio.run(main())
