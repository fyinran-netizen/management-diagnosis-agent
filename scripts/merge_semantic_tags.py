"""CLI orchestration for the historical semantic-tag review workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.tools.ingestion.metadata.semantic import merge_records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pending-only", action="store_true")
    args = parser.parse_args()
    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    merged, _results = merge_records(records, pending_only=args.pending_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in merged) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
