from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import List, Tuple


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a JSONL dataset into train/val/test sets.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--train-out", type=Path, required=True)
    parser.add_argument("--val-out", type=Path, required=True)
    parser.add_argument("--test-out", type=Path, required=True)
    parser.add_argument("--val-ratio", type=float, default=0.05)
    parser.add_argument("--test-ratio", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rows = load_jsonl(args.input)
    train, val, test = split_rows(rows, args.val_ratio, args.test_ratio, args.seed)
    write_jsonl(args.train_out, train)
    write_jsonl(args.val_out, val)
    write_jsonl(args.test_out, test)
    print(
        f"Split {len(rows)} rows -> train {len(train)}, val {len(val)}, test {len(test)}"
    )


def split_rows(
    rows: List[dict], val_ratio: float, test_ratio: float, seed: int
) -> Tuple[List[dict], List[dict], List[dict]]:
    random.seed(seed)
    shuffled = rows[:]
    random.shuffle(shuffled)
    n = len(shuffled)
    n_val = int(n * val_ratio)
    n_test = int(n * test_ratio)
    val = shuffled[:n_val]
    test = shuffled[n_val : n_val + n_test]
    train = shuffled[n_val + n_test :]
    return train, val, test


def load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open() as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
