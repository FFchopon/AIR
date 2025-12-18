"""Interactive runner for the Computer Use Agent.

This script creates a Computer Use Agent using the OpenAI Agents SDK
hosted Computer tool and lets the user type natural-language instructions
for what they want done on the computer.

Usage (from the ResponseSpec root or this case_study folder):

    python run_computer_use_agent.py

Make sure you have:
  - Set OPENAI_API_KEY in your environment
  - Access to the OpenAI Computer Use tool in your account
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure repo root and this case_study are on sys.path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from agents import Runner  # type: ignore

from computer_use_agent import create_computer_use_agent


async def run_interactive(model: str = "gpt-4.1-mini") -> None:
    """Run an interactive REPL for the Computer Use Agent.

    The user can repeatedly enter instructions; each instruction is run as
    a separate agent invocation so that side effects on the computer are
    explicit per step.
    """

    agent = create_computer_use_agent(model=model)

    print("=" * 80)
    print("Computer Use Agent - Interactive Mode")
    print("Model:", model)
    print("Type natural-language instructions describing what you want the")
    print("agent to do on your computer. Type 'exit' to quit.")
    print("=" * 80)

    while True:
        try:
            instruction = input("\nInstruction (or 'exit'): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not instruction:
            continue
        if instruction.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        print("\n" + "-" * 80)
        print("Running instruction:")
        print("  ", instruction)
        print("-" * 80 + "\n")

        try:
            result = await Runner.run(agent, instruction)
            print("[Agent Output]")
            print(result.final_output)
        except Exception as exc:  # noqa: BLE001
            # Print rich error information so we can diagnose issues like
            # missing model access, tool configuration problems, or
            # Playwright/browser errors.
            import traceback

            print("[Error] Agent run failed (type={}): {}".format(type(exc).__name__, repr(exc)))
            traceback.print_exception(exc)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the Computer Use Agent interactively")
    parser.add_argument("--model", type=str, default="computer-use-preview", help="Model to use")
    args = parser.parse_args()

    asyncio.run(run_interactive(model=args.model))


if __name__ == "__main__":
    main()
