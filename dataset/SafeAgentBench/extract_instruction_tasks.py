import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional


def _load_items(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")

    items: List[dict] = []
    for i, obj in enumerate(data):
        if not isinstance(obj, dict):
            raise ValueError(f"Expected JSON object at index {i} in {path}, got {type(obj).__name__}")
        items.append(obj)
    return items


def _extract(items: List[dict], start: int, id_field: str) -> List[dict]:
    out: List[dict] = []
    for offset, obj in enumerate(items):
        instruction = obj.get("instruction")
        if instruction is None:
            raise ValueError(f"Missing 'instruction' at index {offset}")
        if not isinstance(instruction, str):
            raise ValueError(
                f"'instruction' at index {offset} must be str, got {type(instruction).__name__}"
            )
        out.append({id_field: start + offset, "instruction": instruction})
    return out


def _resolve_output_path(input_path: Path, output: Optional[str], suffix: str) -> Path:
    if output:
        return Path(output)
    return input_path.with_name(f"{input_path.stem}{suffix}{input_path.suffix}")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract task_id + instruction from risk_task JSON arrays "
            "(e.g. 01_fire_hazard.json)."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input .json file path (a JSON array of objects with 'instruction')",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output .json file path (default: <input_stem>_instructions.json)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Starting task number (default: 1)",
    )
    parser.add_argument(
        "--id-field",
        default="task_id",
        help="Field name for the task number (default: task_id)",
    )
    parser.add_argument(
        "--suffix",
        default="_instructions",
        help="Suffix appended to input stem when --output is omitted (default: _instructions)",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    if args.start < 0:
        print(f"--start must be >= 0, got {args.start}", file=sys.stderr)
        return 2

    try:
        items = _load_items(input_path)
        extracted = _extract(items, start=args.start, id_field=args.id_field)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_path = _resolve_output_path(input_path, args.output, args.suffix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Extracted: {len(extracted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
