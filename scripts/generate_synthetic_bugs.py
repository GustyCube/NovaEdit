from __future__ import annotations

import argparse
import random
from pathlib import Path

from trainer.utils_dataset import save_jsonl


def inject_missing_import(code: str) -> tuple[str, str]:
    return "import math\n" + code, "NameError: name 'math' is not defined"


def inject_undefined_variable(code: str) -> tuple[str, str]:
    buggy = code.replace("result", "reslt") if "result" in code else code + "\nprint(reslt)\n"
    return buggy, "NameError: name 'reslt' is not defined"


TRANSFORMS = [inject_missing_import, inject_undefined_variable]


def generate_samples(source_dir: Path, limit: int = 20):
    files = list(source_dir.glob("*.py"))
    for path in files[:limit]:
        original = path.read_text()
        transform = random.choice(TRANSFORMS)
        buggy, diag = transform(original)
        yield {
            "language": "python",
            "file_path": str(path),
            "code": buggy,
            "region": {"start_line": 1, "end_line": len(buggy.splitlines())},
            "diagnostics": [diag],
            "instruction": "fix errors only",
            "patch_dsl": "",
            "clean_code": original,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="Directory of .py files.")
    parser.add_argument("--out", type=Path, required=True, help="Where to write JSONL.")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    rows = list(generate_samples(args.source, limit=args.limit))
    save_jsonl(args.out, rows)
    print(f"Wrote {len(rows)} synthetic samples to {args.out}")


if __name__ == "__main__":
    main()
