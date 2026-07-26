"""Code Agent batch runner for RedCode index datasets.

Loads one ``indexN_30_codes_full.json`` file (N = 1..27), feeds each task's
``Text_summary`` to the ResponseSpec-enabled code agent, and supports
``--start`` / ``--count`` to select a contiguous slice of tasks.

Safety rules are read from ``rules.txt`` in this directory by default
(override with ``--rule-file``).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CASE_DIR = Path(__file__).resolve().parent
DEFAULT_TASK_DIR = ROOT_DIR / "dataset" / "RedCode"
DEFAULT_RULE_FILE = CASE_DIR / "rules.txt"

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(CASE_DIR))

from agents import Runner, SQLiteSession
from agent_factory import create_safe_agent
from response import ResponseOrchestrator

from code_agent_demo import (
    SANDBOX_ROOT,
    python_repl_impl,
    reset_sandbox,
)


# RedCode categories: index1 .. index27
NUM_INDEXES = 27


def resolve_task_file(task_file: str, task_dir: Path) -> Path:
    """Resolve ``--task-file`` to an absolute JSON path.

    Accepts:
    - index ``1``..``27`` or ``01``..``27``
    - basename such as ``index5_30_codes_full.json``
    - absolute / relative path to a JSON file
    """
    key = task_file.strip()

    # Numeric index: 1, 01, 16, ...
    if key.isdigit():
        idx = int(key)
        if 1 <= idx <= NUM_INDEXES:
            path = task_dir / f"index{idx}_30_codes_full.json"
        else:
            raise FileNotFoundError(
                f"Index {idx} out of range [1, {NUM_INDEXES}]. "
                f"Use 1-{NUM_INDEXES} or a filename under {task_dir}."
            )
    else:
        candidate = Path(key)
        if candidate.is_file():
            path = candidate.resolve()
        else:
            path = (task_dir / key).resolve()

    if not path.is_file():
        raise FileNotFoundError(
            f"Task file not found: {task_file!r} (resolved to {path}). "
            f"Use 1-{NUM_INDEXES} or a filename under {task_dir}."
        )
    return path


def load_tasks(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return data


def select_tasks(
    tasks: List[Dict[str, Any]],
    start: int,
    count: Optional[int],
) -> Tuple[List[Dict[str, Any]], int, int]:
    """Slice tasks by start index and count. Returns (slice, start, end_exclusive)."""
    n = len(tasks)
    if start < 0 or start >= n:
        raise ValueError(f"--start {start} out of range [0, {n})")
    end = n if count is None else min(n, start + count)
    if count is not None and count <= 0:
        raise ValueError(f"--count must be positive, got {count}")
    return tasks[start:end], start, end


def task_instruction(task: Dict[str, Any]) -> str:
    """Prefer Text_summary; fall back to Text_details / Prompt."""
    for key in ("Text_summary", "Text_details", "Prompt"):
        value = (task.get(key) or "").strip()
        if value:
            return value
    return ""


def reset_incident_state_for_task(state) -> None:
    """Clear per-task incident / history fields; keep learned rules."""
    state.clear_incident()
    state.incident_occurred = False
    state.tool_call_history = []
    state.last_tool_called = None
    state.current_tool_arguments = {}
    state.pending_eradication = None
    state.stop_after_eradication = False
    state.reset_turn_state()
    state.reset_timing_state()


def create_agent(rule_file: Path, model: str, session: SQLiteSession, generate_learned_rules: bool = True):
    return create_safe_agent(
        rule_file=str(rule_file),
        base_tools=[python_repl_impl],
        agent_name="Code Agent (Batch)",
        model=model,
        session=session,
        use_learned_rules=False,
        generate_learned_rules=generate_learned_rules,
    )


async def maybe_force_remediation(agent, state, max_turns: int = 8) -> Optional[str]:
    """If an incident is open, force a remediation round (same as interactive demo)."""
    if not (state.incident_detected and not state.remediation_completed):
        return None

    print("\n[Batch] Incident unresolved — forcing remediation round")
    print(f"[Batch] Rule: {state.triggered_rule_id}")
    print(f"[Batch] Required action: {state.remediation_action}")

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
        session=state.session,
        max_turns=max_turns,
    )
    return rem_result.final_output


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Batch-run RedCode index tasks on the code agent. "
            "Rules are loaded from case_studies/code_agent/rules.txt by default."
        )
    )
    parser.add_argument(
        "--task-file",
        "-t",
        required=True,
        help="RedCode index: 1-27 (or 01-27), basename, or path to a JSON file",
    )
    parser.add_argument(
        "--start",
        "-s",
        type=int,
        default=0,
        help="0-based start index into the task array (default: 0)",
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=None,
        help="Number of tasks to run from --start (default: all remaining)",
    )
    parser.add_argument(
        "--task-dir",
        type=Path,
        default=DEFAULT_TASK_DIR,
        help=f"Directory containing RedCode JSON files (default: {DEFAULT_TASK_DIR})",
    )
    parser.add_argument(
        "--rule-file",
        type=Path,
        default=DEFAULT_RULE_FILE,
        help=f"ResponseSpec rules file (default: {DEFAULT_RULE_FILE})",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.6-luna",
        help="Model name for the code agent (default: gpt-5.6-luna)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=20,
        help="Max agent turns per task (default: 20)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Optional path to write JSON results",
    )
    parser.add_argument(
        "--generate-learned-rules",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "After remediation, generate a learned rule (default: on). "
            "Pass --no-generate-learned-rules to only run orchestrate."
        ),
    )
    return parser.parse_args(argv)


async def run_batch(args: argparse.Namespace) -> List[Dict[str, Any]]:
    task_path = resolve_task_file(args.task_file, Path(args.task_dir))
    rule_file = Path(args.rule_file)
    if not rule_file.is_file():
        raise FileNotFoundError(f"Rule file not found: {rule_file}")

    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set. Batch will not work without it.")

    all_tasks = load_tasks(task_path)
    selected, start, end = select_tasks(all_tasks, args.start, args.count)

    print("\n" + "=" * 80)
    print("ResponseSpec Code Agent - Batch Runner")
    print("=" * 80)
    print(f"Task file : {task_path}")
    print(f"Rules     : {rule_file}")
    print(f"Model     : {args.model}")
    print(
        f"Learn     : generate_learned_rules="
        f"{'ON' if args.generate_learned_rules else 'OFF'}"
    )
    print(f"Slice     : indices [{start}, {end})  ({len(selected)} task(s) / {len(all_tasks)} total)")
    print("=" * 80 + "\n")

    learned_rules_file = str(CASE_DIR / "learned_rules.txt")
    session = SQLiteSession(f"batch_code_{task_path.stem}_{start}_{end}")
    agent, state = create_agent(
        rule_file,
        args.model,
        session,
        generate_learned_rules=args.generate_learned_rules,
    )
    state.learned_rules_db_path = learned_rules_file
    state.load_learned_rules()

    print(f"[Batch] Loaded {len(state.all_rules)} initial rule(s)")
    print(f"[Batch] Loaded {len(state.learned_rules)} learned rule(s) from {learned_rules_file}\n")

    results: List[Dict[str, Any]] = []

    for offset, task in enumerate(selected):
        idx = start + offset
        task_id = task.get("Index", str(idx))
        instruction = task_instruction(task)
        expected = task.get("expected_result", "")

        print("\n" + "-" * 80)
        print(f"[{offset + 1}/{len(selected)}] Task index={idx} id={task_id}")
        print(f"  expected_result : {expected}")
        print(f"  instruction     : {instruction[:200]}{'...' if len(instruction) > 200 else ''}")
        print("-" * 80)

        if not instruction:
            record = {
                "index": idx,
                "task_id": task_id,
                "instruction": instruction,
                "expected_result": expected,
                "status": "skipped",
                "error": "empty instruction",
                "final_output": None,
                "remediation_output": None,
                "elapsed_s": 0.0,
                "incident_occurred": False,
                "incident_detected": False,
                "remediation_completed": False,
                "triggered_rule_id": "",
            }
            results.append(record)
            print("[Skip] Empty instruction")
            continue

        # Leave sandbox cwd before deleting/recreating it (important on Windows).
        os.chdir(CASE_DIR)
        reset_sandbox()
        os.chdir(SANDBOX_ROOT)

        reset_incident_state_for_task(state)
        state.session = SQLiteSession(f"batch_code_{task_path.stem}_{idx}")

        t0 = time.time()
        status = "ok"
        error_msg = None
        final_output = None
        remediation_output = None

        try:
            result = await Runner.run(
                agent,
                instruction,
                context=state,
                session=state.session,
                max_turns=args.max_turns,
            )
            final_output = result.final_output
            remediation_output = await maybe_force_remediation(agent, state)
        except Exception as exc:
            status = "error"
            error_msg = f"{type(exc).__name__}: {exc}"
            print(f"[Error] {error_msg}")

        elapsed = time.time() - t0
        record = {
            "index": idx,
            "task_id": task_id,
            "instruction": instruction,
            "expected_result": expected,
            "status": status,
            "error": error_msg,
            "final_output": final_output,
            "remediation_output": remediation_output,
            "elapsed_s": round(elapsed, 3),
            "incident_occurred": bool(getattr(state, "incident_occurred", False)),
            "incident_detected": bool(getattr(state, "incident_detected", False)),
            "remediation_completed": bool(getattr(state, "remediation_completed", False)),
            "triggered_rule_id": getattr(state, "triggered_rule_id", "") or "",
            "learned_rules_count": len(getattr(state, "learned_rules", []) or []),
        }
        results.append(record)

        print(
            f"[Done] status={status} elapsed={elapsed:.1f}s "
            f"incident={record['incident_occurred']} "
            f"rule={record['triggered_rule_id'] or '-'}"
        )
        if final_output:
            print("Agent Output:")
            print(final_output)

    # Summary
    ok = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] == "error")
    skip = sum(1 for r in results if r["status"] == "skipped")
    incidents = sum(1 for r in results if r.get("incident_occurred"))

    print("\n" + "=" * 80)
    print("Batch Summary")
    print("=" * 80)
    print(f"  total     : {len(results)}")
    print(f"  ok        : {ok}")
    print(f"  error     : {err}")
    print(f"  skipped   : {skip}")
    print(f"  incidents : {incidents}")
    print("=" * 80)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "task_file": str(task_path),
            "rule_file": str(rule_file),
            "model": args.model,
            "start": start,
            "end": end,
            "results": results,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"\n[Output] Wrote results to {out_path}")

    return results


async def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    try:
        await run_batch(args)
    except KeyboardInterrupt:
        print("\nBatch interrupted by user")


if __name__ == "__main__":
    asyncio.run(main())
