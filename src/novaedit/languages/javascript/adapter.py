from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from novaedit.languages.python.patch_apply import apply_patch_dsl, parse_patch_dsl


class LanguageAdapter(Protocol):
    name: str

    def parse_ast(self, code: str): ...

    def run_diagnostics(self, code: str, path: str | None = None) -> list[str]: ...

    def apply_patch(self, code: str, patch_dsl: str) -> str: ...


@dataclass
class JavaScriptAdapter(LanguageAdapter):
    name: str = "javascript"

    def parse_ast(self, code: str):
        # Placeholder; could integrate tree-sitter or babel in the future.
        return None

    def run_diagnostics(self, code: str, path: str | None = None) -> list[str]:
        # Placeholder diagnostics; integrate eslint/js parser later.
        return []

    def apply_patch(self, code: str, patch_dsl: str) -> str:
        # Reuse line-based patch DSL machinery.
        return apply_patch_dsl(code, patch_dsl)

    def apply_patch_checked(self, code: str, patch_dsl: str) -> str:
        parse_patch_dsl(patch_dsl)
        return self.apply_patch(code, patch_dsl)
