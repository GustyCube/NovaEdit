from __future__ import annotations

import ast
from typing import List


def run_basic_diagnostics(code: str, path: str | None = None) -> List[str]:
    """Very small diagnostic runner using stdlib only."""
    errors: List[str] = []
    try:
        ast.parse(code, filename=path or "<snippet>")
    except SyntaxError as exc:  # pragma: no cover - hard to trigger in tests
        errors.append(f"SyntaxError: {exc.msg} at line {exc.lineno}")
    return errors
