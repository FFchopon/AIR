"""Embodied Agent batch runner for SafeAgentBench risk_task datasets.

Loads one risk_task JSON file (01-10), feeds each task's ``instruction``
to the ResponseSpec-enabled embodied agent, and supports ``--start`` /
``--count`` to select a contiguous slice of tasks.

Safety rules are always read from ``rules.txt`` in this directory.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CASE_DIR = Path(__file__).resolve().parent
SANDBOX_ROOT = CASE_DIR / "sandbox_root"
DEFAULT_TASK_DIR = ROOT_DIR / "dataset" / "SafeAgentBench" / "risk_task"
DEFAULT_RULE_FILE = CASE_DIR / "rules.txt"

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


# Filename stems under dataset/SafeAgentBench/risk_task (excluding adversarial/)
TASK_FILE_MAP: Dict[str, str] = {
    "01": "01_fire_hazard.json",
    "02": "02_electrical_shock_hazard.json",
    "03": "03_explosion_hazard.json",
    "04": "04_poisoning_ingestion_hazard.json",
    "05": "05_slip_hazard.json",
    "06": "06_liquid_hazard.json",
    "07": "07_breakage_hazard.json",
    "08": "08_appliance_misuse_hazard.json",
    "09": "09_furniture_damage_hazard.json",
    "10": "10_smallitem_damage_hazard.json",
}


def resolve_task_file(task_file: str, task_dir: Path) -> Path:
    """Resolve ``--task-file`` to an absolute JSON path.

    Accepts:
    - index ``01``..``10``
    - basename such as ``03_explosion_hazard.json``
    - absolute / relative path to a JSON file
    """
    key = task_file.strip()
    if key in TASK_FILE_MAP:
        path = task_dir / TASK_FILE_MAP[key]
    else:
        candidate = Path(key)
        if candidate.is_file():
            path = candidate.resolve()
        else:
            path = (task_dir / key).resolve()

    if not path.is_file():
        known = ", ".join(f"{k}→{v}" for k, v in TASK_FILE_MAP.items())
        raise FileNotFoundError(
            f"Task file not found: {task_file!r} (resolved to {path}). "
            f"Use 01-10 or a filename under {task_dir}. Known: {known}"
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


def reset_incident_state_for_task(state) -> None:
    """Clear per-task incident / history fields; keep learned rules."""
    state.clear_incident()
    state.incident_occurred = False
    state.severity = ""
    state.tool_call_history = []
    state.last_tool_called = None
    state.current_tool_arguments = {}
    state.pending_eradication = None
    state.stop_after_eradication = False
    state.reset_turn_state()
    state.reset_timing_state()


def create_agent(rule_file: Path, model: str, session: SQLiteSession, generate_learned_rules: bool = True):
    return create_safe_embodied_agent(
        rule_file=str(rule_file),
        tools=ALL_TOOLS,
        base_instructions=EMBODIED_BASE_INSTRUCTIONS,
        agent_name="Embodied Agent (Batch)",
        model=model,
        session=session,
        generate_learned_rules=generate_learned_rules,
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


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Batch-run SafeAgentBench risk_task instructions on the embodied agent. "
            "Rules are loaded from case_studies/embodied_agent/rules.txt."
        )
    )
    parser.add_argument(
        "--task-file",
        "-t",
        required=True,
        help="Risk task file: 01-10, basename (e.g. 03_explosion_hazard.json), or path",
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
        help=f"Directory containing risk_task JSON files (default: {DEFAULT_TASK_DIR})",
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
        help="Model name for the embodied agent (default: gpt-5.6-luna)",
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

    all_tasks = load_tasks(task_path)
    selected, start, end = select_tasks(all_tasks, args.start, args.count)

    print("\n" + "=" * 80)
    print("ResponseSpec Embodied Agent - Batch Runner")
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

    # Unified scene; risk_category kept for SandboxManager compatibility
    primary_risk = selected[0].get("risk_category", "Fire Hazard")
    if isinstance(primary_risk, str) and "," in primary_risk:
        primary_risk = primary_risk.split(",")[0].strip()

    sandbox = SandboxManager(risk_category=primary_risk)
    set_sandbox(sandbox)

    session = SQLiteSession(f"batch_embodied_{task_path.stem}_{start}_{end}")
    agent, state = create_agent(
        rule_file,
        args.model,
        session,
        generate_learned_rules=args.generate_learned_rules,
    )

    results: List[Dict[str, Any]] = []

    for offset, task in enumerate(selected):
        idx = start + offset
        instruction = (task.get("instruction") or "").strip()
        risk_category = task.get("risk_category", "")
        scene_name = task.get("scene_name", "")

        print("\n" + "-" * 80)
        print(f"[{offset + 1}/{len(selected)}] Task index={idx}")
        print(f"  risk_category : {risk_category}")
        print(f"  scene_name    : {scene_name}")
        print(f"  instruction   : {instruction}")
        print("-" * 80)

        if not instruction:
            record = {
                "index": idx,
                "instruction": instruction,
                "risk_category": risk_category,
                "scene_name": scene_name,
                "status": "skipped",
                "error": "empty instruction",
                "final_output": None,
                "elapsed_s": 0.0,
                "incident_occurred": False,
            }
            results.append(record)
            print("[Skip] Empty instruction")
            continue

        sandbox.reset_for_task(task)
        set_sandbox(sandbox)
        reset_incident_state_for_task(state)
        # Fresh conversation per task; learned rules stay on ``state``
        state.session = SQLiteSession(f"batch_embodied_{task_path.stem}_{idx}")

        t0 = time.time()
        status = "ok"
        error_msg = None
        final_output = None

        try:
            result = await Runner.run(
                agent,
                instruction,
                context=state,
                session=state.session,
                max_turns=args.max_turns,
            )
            final_output = result.final_output
        except Exception as exc:
            status = "error"
            error_msg = f"{type(exc).__name__}: {exc}"
            print(f"[Error] {error_msg}")

        elapsed = time.time() - t0
        record = {
            "index": idx,
            "instruction": instruction,
            "risk_category": risk_category,
            "scene_name": scene_name,
            "status": status,
            "error": error_msg,
            "final_output": final_output,
            "elapsed_s": round(elapsed, 3),
            "incident_occurred": bool(getattr(state, "incident_occurred", False)),
            "triggered_rule_id": getattr(state, "triggered_rule_id", "") or "",
            "action_count": len(sandbox.get_action_history()),
        }
        results.append(record)

        print(f"[Done] status={status} elapsed={elapsed:.1f}s "
              f"incident={record['incident_occurred']} actions={record['action_count']}")
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
