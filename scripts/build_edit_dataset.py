from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List

from trainer.utils_dataset import load_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge multiple JSONL sources into a single edit dataset.")
    parser.add_argument("--inputs", nargs="+", required=True, help="List of jsonl files to merge.")
    parser.add_argument("--output", required=True, type=Path, help="Path to write merged jsonl.")
    parser.add_argument("--max-rows", type=int, default=None, help="Optional cap on total rows.")
    args = parser.parse_args()

    rows: List[dict] = []
    for path in args.inputs:
        for row in load_jsonl(path):
            rows.append(row)
            if args.max_rows and len(rows) >= args.max_rows:
                break
        if args.max_rows and len(rows) >= args.max_rows:
            break

    write_jsonl(args.output, rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
