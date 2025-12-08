from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence


def load_jsonl(path: str | Path) -> Iterator[dict]:
    with Path(path).open() as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def save_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def train_val_split(rows: Sequence[dict], val_ratio: float = 0.05) -> tuple[List[dict], List[dict]]:
    cutoff = int(len(rows) * (1 - val_ratio))
    return list(rows[:cutoff]), list(rows[cutoff:])
