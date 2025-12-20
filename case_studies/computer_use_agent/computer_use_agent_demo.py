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
import os
import sys
import json
from pathlib import Path

# Ensure repo root and this case_study are on sys.path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from agents import Runner, SQLiteSession  # type: ignore

from computer_use_agent import create_safe_computer_use_agent
from tool_wrapper import check_initial_rule
from state import IncidentState


async def run_interactive(model: str = "computer-use-preview") -> None:
    """Run an interactive REPL for the Computer Use Agent.

    The user can repeatedly enter instructions; each instruction is run as
    a separate agent invocation so that side effects on the computer are
    explicit per step.
    """

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not set. Demo will not work without it.")
        print("   Set it in your environment before running this demo.\n")
        return

    session = SQLiteSession("demo_computer_use_agent_interactive")
    rule_file = str(Path(__file__).parent / "rules.txt")
    agent, state = create_safe_computer_use_agent(
        rule_file=rule_file,
        agent_name="Computer Use Agent (Interactive)",
        model=model,
        session=session,
    )

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
            result = None
            for attempt in range(3):
                run_instruction = instruction
                if attempt > 0:
                    run_instruction = (
                        "Continue the task using the Computer Use tool. "
                        "Do not ask the user questions. "
                        "You already have a browser. "
                        "You MUST take concrete actions (click/type/keypress) now to complete: "
                        + instruction
                    )

                before_items = await session.get_items()
                before_len = len(before_items)

                result = await Runner.run(
                    agent,
                    run_instruction,
                    context=state,
                    session=session,
                    max_turns=10,
                )

                after_items = await session.get_items()
                new_items = after_items[before_len:]

                computer_actions: list[str] = []
                for item in new_items:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "computer_call":
                        action = item.get("action")
                        if isinstance(action, dict):
                            at = action.get("type")
                            if isinstance(at, str):
                                computer_actions.append(at)

                non_screenshot_actions = [a for a in computer_actions if a != "screenshot"]
                if non_screenshot_actions or attempt == 2:
                    break

            print("[Agent Output]")
            print(result.final_output if result is not None else "")

            # -----------------------------------------------------------------
            # ResponseSpec (Option 1): post-run evaluation for Computer Use
            #
            # The Agents SDK records Computer Use activity as `computer_call` /
            # `computer_call_output` session items rather than `function_call`.
            # ResponseSpec's core session-extractor is function_call-based, so
            # we mirror the older ResponseSpec case study and run the initial
            # rule check manually from the session trace.
            # -----------------------------------------------------------------
            # Build call_id -> (action, output) pairs
            calls_by_id: dict[str, dict] = {}
            outputs_by_id: dict[str, dict] = {}
            for item in new_items:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "computer_call":
                    cid = item.get("call_id")
                    if isinstance(cid, str):
                        calls_by_id[cid] = item
                if item.get("type") == "computer_call_output":
                    cid = item.get("call_id")
                    if isinstance(cid, str):
                        outputs_by_id[cid] = item

            paired_ids = [cid for cid in calls_by_id.keys() if cid in outputs_by_id]
            if paired_ids:
                print(f"[ResponseSpec] Detected {len(paired_ids)} computer_call pair(s) in this run")
            else:
                print("[ResponseSpec] No computer_call pairs found in this run")

            # Evaluate each computer call in order
            any_triggered = False
            incident_set_this_run = False
            initial_triggered_ids: set[str] = set()
            learned_triggered_ids: set[str] = set()
            incident_rule_id: str | None = None
            incident_outcome: str | None = None
            for cid in paired_ids:
                if incident_set_this_run:
                    break
                call_item = calls_by_id[cid]
                out_item = outputs_by_id[cid]

                action = call_item.get("action")
                output = out_item.get("output")

                tool_name = "computer"
                tool_args = {"action": action} if action is not None else {}

                # Output can be huge (base64 screenshots). Store a trimmed preview.
                if isinstance(output, dict):
                    output_preview = dict(output)
                    image_url = output_preview.get("image_url")
                    if isinstance(image_url, str) and len(image_url) > 200:
                        output_preview["image_url"] = image_url[:200] + "...[TRUNCATED]"
                    tool_result = json.dumps(output_preview, ensure_ascii=False)
                else:
                    tool_result = repr(output)

                if isinstance(tool_result, str) and len(tool_result) > 1000:
                    tool_result = tool_result[:1000] + "...[TRUNCATED]"

                state.add_tool_call(tool_name, tool_args, tool_result)

                # Use a minimal, truncated view of history for LLM-based rule evaluation.
                eval_state = IncidentState(all_rules=state.all_rules, session=state.session)
                eval_state.learned_rules = list(getattr(state, "learned_rules", []))
                for h in state.get_recent_history(n=5):
                    if not isinstance(h, dict):
                        continue
                    h_tool = h.get("tool", "")
                    h_args = h.get("arguments", {})
                    h_res = h.get("result", "")
                    if isinstance(h_res, str) and len(h_res) > 1000:
                        h_res = h_res[:1000] + "...[TRUNCATED]"
                    eval_state.add_tool_call(str(h_tool), h_args if isinstance(h_args, dict) else {}, str(h_res))

                # 1) Initial rules (rules.txt)
                initial_triggered_rules = state.get_triggered_rules_for_tool(tool_name)
                if initial_triggered_rules:
                    any_triggered = True
                    for r in initial_triggered_rules:
                        if isinstance(getattr(r, "id", None), str):
                            initial_triggered_ids.add(r.id)
                for rule in initial_triggered_rules:
                    evaluation = await check_initial_rule(
                        rule,
                        tool_name,
                        tool_args,
                        tool_result,
                        eval_state,
                    )
                    outcome = evaluation.get("outcome", "NO_RISK")
                    if outcome == "NO_RISK":
                        continue

                    reasoning = evaluation.get("reasoning", "")
                    description = (
                        f"The executed operation matched the condition of rule "
                        f"'{rule.id}': {rule.incident_condition}"
                    )
                    if reasoning:
                        description = description + f" Reasoning: {reasoning}"

                    state.set_incident(
                        rule_id=rule.id,
                        description=description,
                        remediation=rule.remediation_action,
                        severity="medium",
                    )
                    incident_set_this_run = True
                    incident_rule_id = rule.id
                    incident_outcome = str(outcome)
                    break

                # 2) Learned rules (learned_rules.txt)
                # NOTE: In option-1 post-run mode, learned rules cannot *block* execution
                # because ComputerTool calls already happened. We only surface matches.
                learned_rules = list(getattr(state, "learned_rules", []))
                learned_triggered = [r for r in learned_rules if getattr(r, "trigger_tool", None) == tool_name]
                if learned_triggered and not incident_set_this_run:
                    any_triggered = True
                    for r in learned_triggered:
                        if isinstance(getattr(r, "id", None), str):
                            learned_triggered_ids.add(r.id)

            if initial_triggered_ids:
                print(f"[ResponseSpec] Initial rules triggered by '{tool_name}': {sorted(initial_triggered_ids)}")
            if learned_triggered_ids:
                print(
                    f"[ResponseSpec] Learned rules matched tool '{tool_name}' (post-run only; no pre-block): "
                    f"{sorted(learned_triggered_ids)}"
                )
            if incident_rule_id is not None:
                print(f"[ResponseSpec] INCIDENT set by rule={incident_rule_id} outcome={incident_outcome}")

            if not any_triggered:
                learned_tools = {getattr(r, "trigger_tool", "") for r in getattr(state, "learned_rules", [])}
                print(
                    "[ResponseSpec] No rules triggered. "
                    f"Recorded tool_name='{tool_name}'. "
                    f"learned_rules trigger_tool(s)={sorted([t for t in learned_tools if t])}"
                )

            after_items = await session.get_items()
            new_items = after_items[before_len:]
            type_counts: dict[str, int] = {}
            observed_names: list[str] = []

            for item in new_items:
                if not isinstance(item, dict):
                    continue

                item_type = item.get("type")
                if isinstance(item_type, str):
                    type_counts[item_type] = type_counts.get(item_type, 0) + 1

                for key in ("name", "tool_name", "tool", "action"):
                    val = item.get(key)
                    if isinstance(val, str):
                        observed_names.append(f"{item_type}.{key}={val}")

            print("[Debug] New session item types:", type_counts if type_counts else "<none>")
            if observed_names:
                print("[Debug] Observed tool/name fields:")
                for s in observed_names[:30]:
                    print("  -", s)
            else:
                print("[Debug] No tool/name fields observed in new session items.")

            for item in new_items[:5]:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                print(f"[Debug] New item type={item_type} keys={sorted(list(item.keys()))}")
                if item_type == "message":
                    content = item.get("content")
                    if isinstance(content, str):
                        print("[Debug] message.content:", content[:300])
                if item_type in {"computer_call", "computer_call_output"}:
                    for k in ("action", "input", "output", "call_id", "id"):
                        v = item.get(k)
                        if v is not None:
                            s = v if isinstance(v, str) else repr(v)
                            print(f"[Debug] {item_type}.{k}:", s[:300])
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
