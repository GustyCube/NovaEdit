from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from trainer.utils_dataset import save_jsonl


def mine_diffs(repo: Path, limit: int = 10):
    """Collect a handful of Python diffs from a git repo."""
    cmd = ["git", "-C", str(repo), "log", "--pretty=format:%H", f"-{limit}"]
    commits = subprocess.check_output(cmd, text=True).splitlines()
    for commit in commits:
        parent = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", f"{commit}^"], text=True
        ).strip()
        diff = subprocess.check_output(
            ["git", "-C", str(repo), "diff", f"{parent}..{commit}", "--", "*.py"], text=True
        )
        if not diff.strip():
            continue
        yield {
            "language": "python",
            "commit": commit,
            "patch": diff,
            "instruction": "apply commit diff",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True, help="Path to git repo.")
    parser.add_argument("--out", type=Path, required=True, help="Where to save JSONL.")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    rows = list(mine_diffs(args.repo, limit=args.limit))
    save_jsonl(args.out, rows)
    print(f"Wrote {len(rows)} diffs to {args.out}")


if __name__ == "__main__":
    main()
