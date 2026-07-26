import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, List


def _normalize_risk_categories(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
        return [p for p in parts if p]

    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            out.extend(_normalize_risk_categories(item))
        return out

    return [str(value).strip()] if str(value).strip() else []


def _iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_no} in {path}: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"Expected JSON object at line {line_no} in {path}, got {type(obj).__name__}")
            yield obj


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Extract items whose risk_category contains 'Fire Hazard' from a jsonl file, and save as a JSON array."
    )
    parser.add_argument(
        "--input",
        default=str(Path(__file__).parent / "unsafe_detailed_1009.jsonl"),
        help="Input .jsonl file path",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "fire_hazard_extracted.json"),
        help="Output .json file path (a JSON array)",
    )
    parser.add_argument(
        "--category",
        default="Damage to Small Items",
        help="Risk category name to match",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Match category with case sensitivity (default: case-insensitive)",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    category = args.category

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    if not args.case_sensitive:
        category_cmp = category.lower()
    else:
        category_cmp = category

    total = 0
    matched: List[dict] = []

    for obj in _iter_jsonl(input_path):
        total += 1
        cats = _normalize_risk_categories(obj.get("risk_category"))
        if args.case_sensitive:
            hit = any(c == category_cmp for c in cats)
        else:
            hit = any(c.lower() == category_cmp for c in cats)

        if hit:
            matched.append(obj)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(matched, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Matched: {len(matched)} / {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
