from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Callable, Iterable, Tuple

import ast

from trainer.utils_dataset import save_jsonl

Transform = Callable[[str], Tuple[str, str]]


def inject_missing_import(code: str) -> tuple[str, str]:
    return "import math\n" + code, "NameError: name 'math' is not defined"


def inject_undefined_variable(code: str) -> tuple[str, str]:
    buggy = code.replace("result", "reslt") if "result" in code else code + "\nprint(reslt)\n"
    return buggy, "NameError: name 'reslt' is not defined"


def inject_off_by_one(code: str) -> tuple[str, str]:
    buggy = code.replace("range(len(", "range(len(")  # noop base
    if "range(" in buggy:
        buggy = buggy.replace("range(", "range(1 + ", 1)
    return buggy, "Potential off-by-one loop range"


def inject_wrong_comparator(code: str) -> tuple[str, str]:
    if "<=" in code:
        buggy = code.replace("<=", "==", 1)
    elif ">=" in code:
        buggy = code.replace(">=", "==", 1)
    else:
        buggy = code.replace("==", "!=", 1) if "==" in code else code + "\nif x == y:\n    pass\n"
        buggy = buggy.replace("==", "!=", 1)
    return buggy, "Logical comparator may be wrong"


def inject_missing_return(code: str) -> tuple[str, str]:
    if "return" in code:
        buggy = code.replace("return", "# return", 1)
    else:
        buggy = code + "\n\ndef compute(x):\n    y = x * 2\n    # missing return\n"
    return buggy, "Function missing return statement"


TRANSFORMS: list[Transform] = [
    inject_missing_import,
    inject_undefined_variable,
    inject_off_by_one,
    inject_wrong_comparator,
    inject_missing_return,
]


def generate_samples(
    source_dir: Path, limit: int = 20, pattern: str = "*.py", validate: bool = False
) -> Iterable[dict]:
    files = sorted(source_dir.rglob(pattern))
    for path in files[:limit]:
        original = path.read_text()
        transform = random.choice(TRANSFORMS)
        buggy, diag = transform(original)
        if validate:
            if not is_valid_python(original) or not is_valid_python(buggy):
                continue
        yield {
            "language": "python",
            "file_path": str(path),
            "code": buggy,
            "region": {"start_line": 1, "end_line": len(buggy.splitlines())},
            "diagnostics": [diag],
            "instruction": "fix errors only",
            "patch_dsl": "",
            "clean_code": original,
            "transform": transform.__name__,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="Directory of .py files.")
    parser.add_argument("--out", type=Path, required=True, help="Where to write JSONL.")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--pattern", type=str, default="*.py", help="Glob for files, default *.py (recursive).")
    parser.add_argument("--validate", action="store_true", help="Skip samples that fail AST parse.")
    args = parser.parse_args()

    rows = list(generate_samples(args.source, limit=args.limit, pattern=args.pattern, validate=args.validate))
    save_jsonl(args.out, rows)
    print(f"Wrote {len(rows)} synthetic samples to {args.out}")


if __name__ == "__main__":
    main()


def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False
