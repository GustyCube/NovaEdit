from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Iterable, Optional

from trainer.utils_dataset import save_jsonl


def mine_diffs(
    repo: Path,
    limit: int = 10,
    file_glob: str = "*.py",
    max_changed_lines: Optional[int] = 400,
    since: Optional[str] = None,
) -> Iterable[dict]:
    """Collect a handful of diffs from a git repo."""
    log_cmd = ["git", "-C", str(repo), "log", "--pretty=format:%H", f"-{limit}"]
    if since:
        log_cmd.extend(["--since", since])
    commits = subprocess.check_output(log_cmd, text=True).splitlines()
    for commit in commits:
        parent = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", f"{commit}^"], text=True
        ).strip()
        diff = subprocess.check_output(
            ["git", "-C", str(repo), "diff", f"{parent}..{commit}", "--", file_glob], text=True
        )
        if not diff.strip():
            continue
        if max_changed_lines is not None:
            changed = sum(1 for line in diff.splitlines() if line.startswith("+") or line.startswith("-"))
            if changed > max_changed_lines:
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
    parser.add_argument("--file-glob", type=str, default="*.py", help="File glob to include (default: *.py)")
    parser.add_argument("--max-changed-lines", type=int, default=400, help="Skip commits with more changes.")
    parser.add_argument("--since", type=str, default=None, help="Optional date constraint, e.g. '30 days ago'.")
    args = parser.parse_args()

    rows = list(
        mine_diffs(
            args.repo,
            limit=args.limit,
            file_glob=args.file_glob,
            max_changed_lines=args.max_changed_lines,
            since=args.since,
        )
    )
    save_jsonl(args.out, rows)
    print(f"Wrote {len(rows)} diffs to {args.out}")


if __name__ == "__main__":
    main()
