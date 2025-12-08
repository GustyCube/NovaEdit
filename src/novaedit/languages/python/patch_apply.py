from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass
class Edit:
    start_line: int
    end_line: int
    replacement: str


def parse_patch_dsl(patch_dsl: str) -> List[Edit]:
    edits: List[Edit] = []
    if not patch_dsl.strip():
        return edits

    lines = patch_dsl.splitlines()
    idx = 0
    while idx < len(lines):
        header = lines[idx].strip()
        if not header.startswith("@@"):
            idx += 1
            continue
        try:
            span = header.split(" ", maxsplit=1)[1]
            start_str, end_str = span.split("-")
            start_line, end_line = int(start_str), int(end_str)
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid patch header: {header}") from exc
        idx += 1
        replacement_lines: List[str] = []
        while idx < len(lines) and not lines[idx].startswith("@@"):
            line = lines[idx]
            if line.startswith("+"):
                replacement_lines.append(line[2:] if line.startswith("+ ") else line[1:])
            idx += 1
        replacement = "\n".join(replacement_lines) + ("\n" if replacement_lines else "")
        edits.append(Edit(start_line=start_line, end_line=end_line, replacement=replacement))
    return edits


def apply_edits(code: str, edits: Sequence[Edit]) -> str:
    lines = code.splitlines()
    # apply bottom-up to maintain offsets
    for edit in sorted(edits, key=lambda e: e.start_line, reverse=True):
        start = max(1, edit.start_line) - 1
        end = max(start + 1, edit.end_line) - 1
        lines[start : end + 1] = edit.replacement.rstrip("\n").splitlines()
    return "\n".join(lines) + ("\n" if code.endswith("\n") else "")


def apply_patch_dsl(code: str, patch_dsl: str) -> str:
    edits = parse_patch_dsl(patch_dsl)
    return apply_edits(code, edits)
