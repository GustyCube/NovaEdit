from __future__ import annotations

import argparse
from pathlib import Path

from novaedit.languages.python.adapter import PythonAdapter
from novaedit.model import NovaEditModel
from trainer.utils_dataset import load_jsonl


def evaluate(dataset_path: Path) -> None:
    adapter = PythonAdapter()
    model = NovaEditModel()
    total = 0
    successes = 0
    applied_ok = 0
    syntax_ok = 0
    total_patch_lines = 0
    for row in load_jsonl(dataset_path):
        total += 1
        code = row["code"]
        diags = row.get("diagnostics", [])
        edits, patch_dsl = model.generate_patch(
            code=code,
            start_line=row.get("region", {}).get("start_line", 1),
            end_line=row.get("region", {}).get("end_line", len(code.splitlines())),
            diagnostics=diags,
            instruction=row.get("instruction", ""),
        )
        try:
            fixed = adapter.apply_patch(code, patch_dsl)
            applied_ok += 1
        except Exception:
            continue
        total_patch_lines += count_patch_lines(patch_dsl)
        before = len(adapter.run_diagnostics(code))
        after = len(adapter.run_diagnostics(fixed))
        if adapter.parse_ast(fixed):
            syntax_ok += 1
        if after < before:
            successes += 1
    rate = successes / total if total else 0
    avg_patch = (total_patch_lines / applied_ok) if applied_ok else 0
    print(f"Bugfix success rate: {rate:.2%} ({successes}/{total})")
    print(f"Patches applied: {applied_ok}/{total}")
    print(f"Syntax OK after patch: {syntax_ok}/{applied_ok}")
    print(f"Avg patch line delta (add/remove): {avg_patch:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    args = parser.parse_args()
    evaluate(args.data)


if __name__ == "__main__":
    main()


def count_patch_lines(patch_dsl: str) -> int:
    return sum(1 for line in patch_dsl.splitlines() if line.startswith("+") or line.startswith("-"))
