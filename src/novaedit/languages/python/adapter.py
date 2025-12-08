from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Protocol, Sequence

from novaedit.languages.python import diagnostics, patch_apply


class LanguageAdapter(Protocol):
    name: str

    def parse_ast(self, code: str) -> ast.AST | None: ...

    def run_diagnostics(self, code: str, path: str | None = None) -> list[str]: ...

    def apply_patch(self, code: str, patch_dsl: str) -> str: ...


@dataclass
class PythonAdapter(LanguageAdapter):
    name: str = "python"

    def parse_ast(self, code: str) -> ast.AST | None:
        try:
            return ast.parse(code)
        except SyntaxError:
            return None

    def run_diagnostics(self, code: str, path: str | None = None) -> list[str]:
        return diagnostics.run_basic_diagnostics(code, path)

    def apply_patch(self, code: str, patch_dsl: str) -> str:
        return patch_apply.apply_patch_dsl(code, patch_dsl)

    def apply_edits(self, code: str, edits: Sequence[patch_apply.Edit]) -> str:
        return patch_apply.apply_edits(code, edits)
