import argparse
import json
import sys
from pathlib import Path
from typing import List


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


def _renumber(items: List[dict], start: int, id_field: str) -> List[dict]:
    out: List[dict] = []
    for offset, obj in enumerate(items):
        new_obj = dict(obj)
        new_obj[id_field] = start + offset
        out.append(new_obj)
    return out


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Renumber task_id fields in a risk_task JSON array to a continuous "
            "sequence (1, 2, 3, ...), preserving item order and other fields."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input .json file path (a JSON array)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output .json file path (default: overwrite --input in place)",
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
        renumbered = _renumber(items, start=args.start, id_field=args.id_field)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else input_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(renumbered, f, ensure_ascii=False, indent=2)
        f.write("\n")

    old_ids = [obj.get(args.id_field) for obj in items]
    new_ids = [obj[args.id_field] for obj in renumbered]
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Count: {len(renumbered)}")
    print(f"Old {args.id_field}: {old_ids}")
    print(f"New {args.id_field}: {new_ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
