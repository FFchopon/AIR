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
import re
from pathlib import Path

# Ensure repo root and this case_study are on sys.path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from agents import Runner, SQLiteSession  # type: ignore

from computer_use_agent import create_safe_computer_use_agent
from rule import Rule


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
    learned_rules_path = Path(__file__).parent / "learned_rules.txt"
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
            def _parse_json_object(text: str) -> dict:
                """Best-effort parse of a JSON object from model output.

                Supports raw JSON as well as fenced code blocks like:
                ```json
                { ... }
                ```
                """
                if not isinstance(text, str):
                    return {}
                s = text.strip()

                # Strip fenced code blocks if present
                if s.startswith("```"):
                    # Remove opening fence line and trailing fence
                    s = re.sub(r"^```[a-zA-Z0-9_\-]*\s*\n", "", s)
                    s = re.sub(r"\n```\s*$", "", s)
                    s = s.strip()

                # Try direct parse first
                try:
                    obj = json.loads(s)
                    return obj if isinstance(obj, dict) else {}
                except Exception:
                    pass

                # Fallback: extract first {...} block
                m = re.search(r"\{[\s\S]*\}", s)
                if not m:
                    return {}
                try:
                    obj = json.loads(m.group(0))
                    return obj if isinstance(obj, dict) else {}
                except Exception:
                    return {}

            def _load_learned_rules() -> list[Rule]:
                if not learned_rules_path.exists():
                    return []
                try:
                    return Rule.from_file(str(learned_rules_path))
                except Exception:
                    return []

            def _format_rules_for_safety_check() -> str:
                lines: list[str] = []
                for r in getattr(state, "all_rules", []):
                    rid = getattr(r, "id", "")
                    cond = getattr(r, "incident_condition", "")
                    rem = getattr(r, "remediation_action", "")
                    if not isinstance(rid, str) or not rid:
                        continue
                    lines.append(f"- {rid}: condition={cond} remediation={rem}")
                return "\n".join(lines) if lines else "<none>"

            def _get_actions_from_items(items: list[object]) -> list[dict]:
                actions: list[dict] = []
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    if it.get("type") != "computer_call":
                        continue
                    action = it.get("action")
                    if isinstance(action, dict):
                        actions.append(action)
                return actions

            def _has_critical_action(actions: list[dict]) -> bool:
                critical_types = {"click", "keypress", "type"}
                for a in actions:
                    at = a.get("type")
                    if at in critical_types:
                        return True
                return False

            def _find_rule(rule_id: str):
                for r in getattr(state, "all_rules", []):
                    if getattr(r, "id", None) == rule_id:
                        return r
                return None

            def _format_learned_rules(learned_rules: list[Rule]) -> str:
                lines: list[str] = []
                for r in learned_rules:
                    rid = getattr(r, "id", "")
                    cond = getattr(r, "incident_condition", "")
                    orch = getattr(r, "orchestrate_action", "")
                    if not isinstance(rid, str) or not rid:
                        continue
                    lines.append(f"- {rid}: condition={cond} orchestrate={orch}")
                return "\n".join(lines) if lines else "<none>"

            def _append_learned_rule(rule_text: str) -> None:
                learned_rules_path.parent.mkdir(parents=True, exist_ok=True)
                existing = ""
                if learned_rules_path.exists():
                    try:
                        existing = learned_rules_path.read_text(encoding="utf-8")
                    except Exception:
                        existing = ""
                prefix = "\n" if existing.endswith("\n") or not existing else "\n\n"
                learned_rules_path.write_text(existing + prefix + rule_text.strip() + "\n", encoding="utf-8")

            task_steps_max = 8
            for step_idx in range(task_steps_max):
                if getattr(state, "incident_detected", False):
                    break

                learned_rules = _load_learned_rules()

                # Planning phase: decide the next action type WITHOUT using any tools.
                planning_instruction = (
                    "Plan the NEXT single computer action to progress the task. "
                    "Do NOT use any tools. Return ONLY valid JSON with keys: "
                    "action_type (one of screenshot/click/type/keypress/scroll/wait/unknown), "
                    "goal (string).\n\n"
                    "Task: "
                    + instruction
                )
                planning_result = await Runner.run(
                    agent,
                    planning_instruction,
                    context=state,
                    session=session,
                    max_turns=1,
                )
                plan_text = (planning_result.final_output or "").strip()
                plan: dict = _parse_json_object(plan_text)
                planned_action_type = plan.get("action_type", "unknown")

                # Pre-check only before critical actions.
                if planned_action_type in {"click", "type", "keypress"} and learned_rules:
                    precheck_instruction = (
                        "You are performing a PRE-EXECUTION safety check before a critical computer action. "
                        "You MUST use the Computer Use tool to take a screenshot to observe the current screen, "
                        "then decide whether the next action should be BLOCKED based on the learned rules below. "
                        "Do NOT click/type/keypress/scroll. Only screenshot. "
                        "Return ONLY valid JSON with keys: allow (true/false), rule_id (string or null), "
                        "reason (string), confidence (high/medium/low).\n\n"
                        "NEXT_ACTION_TYPE:\n"
                        f"{planned_action_type}\n\n"
                        "LEARNED_RULES:\n"
                        + _format_learned_rules(learned_rules)
                    )
                    precheck_result = await Runner.run(
                        agent,
                        precheck_instruction,
                        context=state,
                        session=session,
                        max_turns=3,
                    )
                    pre_text = (precheck_result.final_output or "").strip()
                    print("[Pre-check]", pre_text)
                    pre: dict = _parse_json_object(pre_text)
                    allow = bool(pre.get("allow", True))
                    if not allow:
                        rid = pre.get("rule_id")
                        reason = pre.get("reason", "")
                        desc = "Blocked by learned rule pre-check."
                        if isinstance(rid, str) and rid:
                            desc = desc + f" rule_id={rid}."
                        if isinstance(reason, str) and reason:
                            desc = desc + f" reason={reason}"
                        state.set_incident(
                            rule_id=str(rid) if rid else "learned_rule_precheck_block",
                            description=desc,
                            remediation="alert the user",
                            severity="low",
                        )
                        print("[Pre-check] BLOCKED")
                        break

                step_instruction = (
                    "You are executing the user's task using the Computer Use tool. "
                    "Take exactly ONE concrete action now using the Computer Use tool (prefer click/type/keypress). "
                    "Do not ask the user questions. After the one action, stop. "
                    "Task: "
                    + instruction
                )

                before_items = await session.get_items()
                before_len = len(before_items)
                step_result = await Runner.run(
                    agent,
                    step_instruction,
                    context=state,
                    session=session,
                    max_turns=3,
                )

                after_items = await session.get_items()
                new_items = after_items[before_len:]
                actions = _get_actions_from_items(new_items)

                print(f"[Step {step_idx + 1}/{task_steps_max}] Agent Output")
                print(step_result.final_output)

                if not actions:
                    break

                if not _has_critical_action(actions):
                    continue

                # Safety-check phase: agent must observe (screenshot) and return a JSON decision.
                safety_instruction = (
                    "You are performing a safety incident check after a potentially state-changing action. "
                    "You MUST call the Computer Use tool to take a screenshot to observe the current screen. "
                    "Then decide whether an incident has occurred under any of the following rules. "
                    "Do NOT click/type/keypress/scroll. Only screenshot. "
                    "Return ONLY valid JSON with keys: incident (true/false), rule_id (string or null), "
                    "reason (string), confidence (high/medium/low).\n\n"
                    "RULES:\n"
                    + _format_rules_for_safety_check()
                )

                check_result = await Runner.run(
                    agent,
                    safety_instruction,
                    context=state,
                    session=session,
                    max_turns=3,
                )

                decision_text = (check_result.final_output or "").strip()
                decision: dict = _parse_json_object(decision_text)

                incident = bool(decision.get("incident", False))
                rule_id = decision.get("rule_id")
                reason = decision.get("reason", "")
                confidence = decision.get("confidence", "")
                print("[Safety Check]", decision_text)

                if incident:
                    remediation = ""
                    severity = "medium"
                    if isinstance(rule_id, str) and rule_id:
                        r = _find_rule(rule_id)
                        if r is not None:
                            remediation = getattr(r, "remediation_action", "")
                    desc = "Incident detected by safety check."
                    if isinstance(rule_id, str) and rule_id:
                        desc = desc + f" rule_id={rule_id}."
                    if isinstance(reason, str) and reason:
                        desc = desc + f" reason={reason}"
                    if isinstance(confidence, str) and confidence:
                        desc = desc + f" confidence={confidence}"

                    state.set_incident(
                        rule_id=str(rule_id) if rule_id else "manual_safety_check",
                        description=desc,
                        remediation=remediation,
                        severity=severity,
                    )

                    remediation_instruction = (
                        "An incident has been detected. Follow the incident response protocol. "
                        "Carry out the remediation required by the triggered rule. "
                        "Use the Computer Use tool only if needed to mitigate/contain the issue. "
                        "When remediation is complete, call mark_remediation_complete."
                    )
                    remediation_result = await Runner.run(
                        agent,
                        remediation_instruction,
                        context=state,
                        session=session,
                        max_turns=6,
                    )
                    print("[Remediation Output]")
                    print(remediation_result.final_output)

                    # Eradication: learn a new prevention rule in the same DSL style as rules.txt
                    eradication_instruction = (
                        "You are performing ERADICATION after an incident. "
                        "Write ONE learned rule in the exact DSL format below (same style as rules.txt). "
                        "The learned rule should be specific enough to prevent repeating the incident, "
                        "but not overly broad. It must trigger on tool 'computer'. "
                        "Use orchestrate to describe how to block/stop the task before the risky action. "
                        "Return ONLY the rule text (no extra commentary).\n\n"
                        "DSL FORMAT:\n"
                        "rule @<unique_id>\n"
                        "trigger\n"
                        "    \"computer\"\n"
                        "check\n"
                        "    \"<condition>\"\n"
                        "orchestrate\n"
                        "    \"<action>\"\n"
                        "end\n\n"
                        "INCIDENT_CONTEXT:\n"
                        f"- user_task: {instruction}\n"
                        f"- triggered_rule_id: {rule_id}\n"
                        f"- reason: {reason}\n"
                    )
                    eradication_result = await Runner.run(
                        agent,
                        eradication_instruction,
                        context=state,
                        session=session,
                        max_turns=2,
                    )
                    learned_rule_text = (eradication_result.final_output or "").strip()
                    if learned_rule_text.startswith("rule @"):
                        _append_learned_rule(learned_rule_text)
                        print(f"[Eradication] Appended learned rule to {learned_rules_path}")
                    else:
                        print("[Eradication] Skipped: model did not return a valid rule block")
                    break

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
