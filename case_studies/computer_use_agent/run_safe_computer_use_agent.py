"""Interactive runner for the *safe* Computer Use Agent (with ResponseSpec).

This script creates a Computer Use Agent that is integrated with the
ResponseSpec incident response layer, using the rules defined in this
case_study's ``rules.txt`` file.

Usage (from the ResponseSpec root or this case_study folder):

    python run_safe_computer_use_agent.py

Make sure you have:
  - Set OPENAI_API_KEY in your environment
  - Access to the OpenAI Computer Use tool in your account
  - Written ResponseSpec rules in ``rules.txt`` under this folder
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure repo root and this case_study are on sys.path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from agents import Runner, SQLiteSession  # type: ignore

from computer_use_agent import create_safe_computer_use_agent
from tool_wrapper import check_initial_rule
from eradication import eradicate_incident


async def run_interactive(model: str = "computer-use-preview") -> None:
    """Run an interactive REPL for the safe Computer Use Agent.

    Each instruction is executed as a separate agent run, with all tool calls
    monitored by ResponseSpec via the IncidentState context.
    """

    case_dir = Path(__file__).parent
    rule_file = str(case_dir / "rules.txt")

    # Session for conversation history and tool call tracking
    session = SQLiteSession(":memory:")

    agent, incident_state = create_safe_computer_use_agent(
        rule_file=rule_file,
        agent_name="Computer Use Agent (Safe)",
        model=model,
        session=session,
    )

    print("=" * 80)
    print("Safe Computer Use Agent - Interactive Mode (ResponseSpec enabled)")
    print("Model:", model)
    print("Rules:", rule_file)
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
            result = await Runner.run(
                agent,
                instruction,
                context=incident_state,
                session=session,
                max_turns=15,
            )
            print("[Agent Output]")
            print(result.final_output)

            # After the run completes, manually perform initial rule evaluation
            # for the last tool call. For Computer Use, this ensures that
            # ComputerTool invocations participate in the same ResponseSpec
            # pipeline as wrapped function tools, without modifying the
            # framework core.
            if incident_state.tool_call_history:
                last_call = incident_state.tool_call_history[-1]
                tool_name = last_call.tool_name
                tool_args = last_call.arguments
                tool_result = last_call.result

                # Trim large tool results (e.g., screenshot base64) before passing them into eradicate_incident
                if isinstance(tool_result, str) and len(tool_result) > 500:
                    tool_result = tool_result[:500] + "...[TRUNCATED]"

                # Temporary debug to help align rule trigger tool names.
                print("\n[Debug] Last tool call:")
                print("  tool_name:", tool_name)
                print("  tool_args:", tool_args)

                triggered_rules = incident_state.get_triggered_rules_for_tool(tool_name)

                for rule in triggered_rules:
                    evaluation = await check_initial_rule(
                        rule,
                        tool_name,
                        tool_args,
                        tool_result,
                        incident_state,
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

                    # Mark incident in IncidentState so that dynamic instructions
                    # and any follow-up logic can see the detection result.
                    incident_state.set_incident(
                        rule_id=rule.id,
                        description=description,
                        remediation=rule.remediation_action,
                        severity="medium",
                    )

                    # Immediately enter eradication phase for this incident in
                    # this case study, so that a learned rule is generated from
                    # the current tool_call_history (similar to code_agent /
                    # embodied_agent experiments, but localized here).
                    #
                    # IMPORTANT: For Computer Use, tool_result may be a very
                    # large base64-encoded screenshot. To avoid exceeding the
                    # model context window inside eradicate_incident, we pass
                    # only a trimmed preview of these result strings.

                    # Prepare trimmed tool_result preview
                    trimmed_tool_result = tool_result
                    if isinstance(trimmed_tool_result, str) and len(trimmed_tool_result) > 500:
                        trimmed_tool_result = trimmed_tool_result[:500] + "...[TRUNCATED]"

                    # Prepare trimmed recent history (limit last 5 calls and
                    # truncate each result field if it is too large).
                    recent_history = incident_state.get_recent_history(n=5)
                    trimmed_history = []
                    for h in recent_history:
                        if not isinstance(h, dict):
                            trimmed_history.append(h)
                            continue
                        h_copy = dict(h)
                        h_res = h_copy.get("result", "")
                        if isinstance(h_res, str) and len(h_res) > 500:
                            h_copy["result"] = h_res[:500] + "...[TRUNCATED]"
                        trimmed_history.append(h_copy)

                    # Build tool_call payload using trimmed result
                    if trimmed_history:
                        last_history_call = trimmed_history[-1]
                        tool_call = {
                            "tool": last_history_call.get("tool", tool_name),
                            "arguments": last_history_call.get("arguments", tool_args),
                            "result": last_history_call.get("result", trimmed_tool_result),
                        }
                    else:
                        tool_call = {
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": trimmed_tool_result,
                        }

                    incident_details = {
                        "rule_id": rule.id,
                        "original_condition": rule.incident_condition,
                        "tool_call": tool_call,
                        "description": description,
                        "recent_history": trimmed_history,
                    }

                    # This will call the Rule Generator Agent and append a
                    # learned rule into incident_state.learned_rules and the
                    # learned_rules.txt DSL file for this case_study.
                    await eradicate_incident(incident_details, incident_state)

                    # For this interactive case, mark that eradication has
                    # completed so callers can see that we stopped after
                    # learning a rule from this incident.
                    incident_state.stop_after_eradication = True

                    # Mirror tool_wrapper behaviour: stop at first non-NO_RISK.
                    break

            # Show a brief snapshot of ResponseSpec state
            incident_detected = getattr(incident_state, "incident_detected", False)
            incident_occurred = getattr(
                incident_state,
                "incident_occurred",
                incident_detected,
            )
            learned_rules = getattr(incident_state, "learned_rules", [])

            print("\n[ResponseSpec]")
            print("  incident_detected:", incident_detected)
            print("  incident_occurred:", incident_occurred)
            print("  learned_rules_count:", len(learned_rules))
        except Exception as exc:  # noqa: BLE001
            import traceback

            print("[Error] Agent run failed (type={}): {}".format(type(exc).__name__, repr(exc)))
            traceback.print_exception(exc)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the ResponseSpec-integrated Computer Use Agent interactively",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="computer-use-preview",
        help="Model to use (must support the Computer Use tool)",
    )
    args = parser.parse_args()

    asyncio.run(run_interactive(model=args.model))


if __name__ == "__main__":
    main()
