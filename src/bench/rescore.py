from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from bench.parse import parse_answer_with_trace
from bench.report import summarize
from bench.types import RunResult


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = Path(args.input)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    source_counts: Counter[str] = Counter()
    changed = 0
    results: list[RunResult] = []
    rescored_rows: list[dict] = []

    for row in rows:
        predicted, source = parse_answer_with_trace(row.get("raw_output") or "", row.get("trace"))
        if predicted != row.get("predicted"):
            changed += 1
        row["predicted"] = predicted
        row["correct"] = predicted == row.get("expected")
        row.setdefault("attempts", 1)
        if source is None:
            row.pop("prediction_source", None)
            source_counts["none"] += 1
        else:
            row["prediction_source"] = source
            source_counts[source] += 1
        rescored_rows.append(row)
        results.append(RunResult(**row))

    if args.output:
        out_path = Path(args.output)
    elif args.in_place:
        out_path = path
    else:
        out_path = path.with_suffix(".rescored.jsonl")

    out_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rescored_rows) + "\n",
        encoding="utf-8",
    )

    if args.summary:
        Path(args.summary).write_text(summarize(results), encoding="utf-8")

    print(f"rows={len(rows)} changed={changed} output={out_path}")
    print("prediction_sources=" + ", ".join(f"{k}:{v}" for k, v in sorted(source_counts.items())))
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Re-score JSONL benchmark results using current parser and trace fallback.")
    parser.add_argument("input", help="Input JSONL result file.")
    parser.add_argument("--output", help="Output JSONL path. Defaults to <input>.rescored.jsonl unless --in-place is set.")
    parser.add_argument("--summary", help="Optional summary markdown output path.")
    parser.add_argument("--in-place", action="store_true", help="Overwrite input JSONL.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
