from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Any, Iterable, List, Sequence, Tuple

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    import torch  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    AutoModelForCausalLM = None  # type: ignore
    AutoTokenizer = None  # type: ignore
    torch = None  # type: ignore

from novaedit.languages.python.adapter import PythonAdapter
from novaedit.languages.javascript.adapter import JavaScriptAdapter
from novaedit.languages.python.patch_apply import apply_patch_dsl
from novaedit.model.config import ModelConfig, load_default_config


@dataclass
class PatchEdit:
    start_line: int
    end_line: int
    replacement: str


class NovaEditModel:
    """Heuristic baseline with optional Hugging Face generation hook.

    - By default runs lightweight heuristics so the repo is runnable without weights.
    - If `hf_model_id` is provided and transformers is installed, uses the HF model
      to produce a textual patch DSL, then parses it.
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        language: str = "python",
        hf_model_id: str | None = None,
        device: str | None = None,
    ):
        self.config = config or load_default_config()
        self.language = language
        if language == "python":
            self.adapter = PythonAdapter()
        elif language == "javascript":
            self.adapter = JavaScriptAdapter()
        else:
            self.adapter = None
        self.hf_model_id = hf_model_id
        self.device = device or ("cuda" if torch and torch.cuda.is_available() else "cpu")
        self._hf_model = None
        self._hf_tokenizer = None
        if hf_model_id:
            self._load_hf_model(hf_model_id)

    def generate_patch(
        self,
        code: str,
        start_line: int,
        end_line: int,
        diagnostics: Sequence[str] | None = None,
        instruction: str | None = None,
    ) -> Tuple[List[PatchEdit], str]:
        """Return structured edits and textual patch DSL."""
        diagnostics = diagnostics or []
        instruction = instruction or ""
        if self._hf_model:
            return self._generate_with_hf(code, start_line, end_line, diagnostics, instruction)

        lines = code.splitlines()
        slice_start = max(1, start_line)
        slice_end = min(len(lines), end_line)
        snippet = "\n".join(lines[slice_start - 1 : slice_end])

        edits: List[PatchEdit] = []
        edits.extend(self._fix_name_errors(snippet, slice_start, diagnostics))
        edits.extend(self._add_missing_imports(snippet, slice_start, diagnostics))

        if not edits and instruction:
            edits.extend(self._style_pass(snippet, slice_start, instruction))

        if not edits:
            # Fallback: no-op message to keep the pipeline flowing.
            snippet_lines = snippet.splitlines()
            num_lines = max(1, len(snippet_lines))
            edits.append(
                PatchEdit(
                    start_line=slice_start,
                    end_line=slice_start + num_lines - 1,
                    replacement=snippet + "\n# TODO: review diagnostics above\n",
                )
            )

        patch_dsl = build_patch_dsl(lines, edits)
        return edits, patch_dsl

    def _fix_name_errors(
        self, snippet: str, snippet_start_line: int, diagnostics: Sequence[str]
    ) -> List[PatchEdit]:
        edits: List[PatchEdit] = []
        undefined_pattern = re.compile(r"name '([^']+)' is not defined")
        all_names = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", snippet)
        defined_names = {name for name in all_names if not name.isupper()}

        for diag in diagnostics:
            match = undefined_pattern.search(diag)
            if not match:
                continue
            missing = match.group(1)
            candidate = self._find_best_name_match(missing, defined_names)
            lines = snippet.splitlines()
            for idx, line in enumerate(lines):
                if missing in line:
                    absolute_line = snippet_start_line + idx
                    replacement_line = line.replace(missing, candidate or f"{missing}_value")
                    edits.append(
                        PatchEdit(
                            start_line=absolute_line,
                            end_line=absolute_line,
                            replacement=replacement_line + "\n",
                        )
                    )
                    break
            if not candidate:
                # Add a simple initialization at the top of the snippet.
                snippet_lines = snippet.splitlines()
                num_lines = max(1, len(snippet_lines))
                replacement = f"{missing} = None  # inferred placeholder\n" + snippet + "\n"
                edits.append(
                    PatchEdit(
                        start_line=snippet_start_line,
                        end_line=snippet_start_line + num_lines - 1,
                        replacement=replacement,
                    )
                )
        return edits

    def _add_missing_imports(
        self, snippet: str, snippet_start_line: int, diagnostics: Sequence[str]
    ) -> List[PatchEdit]:
        edits: List[PatchEdit] = []
        import_pattern = re.compile(r"No module named '([^']+)'|undefined name '([^']+)'")
        for diag in diagnostics:
            match = import_pattern.search(diag)
            if not match:
                continue
            module = match.group(1) or match.group(2)
            snippet_lines = snippet.splitlines()
            num_lines = max(1, len(snippet_lines))
            import_line = f"import {module}\n"
            edits.append(
                PatchEdit(
                    start_line=snippet_start_line,
                    end_line=snippet_start_line + num_lines - 1,
                    replacement=import_line + snippet + "\n",
                )
            )
        return edits

    def _style_pass(
        self, snippet: str, snippet_start_line: int, instruction: str
    ) -> List[PatchEdit]:
        edits: List[PatchEdit] = []
        if "type" in instruction.lower():
            lines = snippet.splitlines()
            patched_lines = [self._maybe_add_type_hint(line) for line in lines]
            replacement = "\n".join(patched_lines) + "\n"
            edits.append(
                PatchEdit(
                    start_line=snippet_start_line,
                    end_line=snippet_start_line + len(lines) - 1,
                    replacement=replacement,
                )
            )
        return edits

    def _maybe_add_type_hint(self, line: str) -> str:
        match = re.match(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\):", line.strip())
        if not match or "->" in line:
            return line
        fn_name, params = match.groups()
        typed_params = []
        for param in params.split(","):
            stripped = param.strip()
            if not stripped or ":" in stripped:
                typed_params.append(stripped)
                continue
            typed_params.append(f"{stripped}: Any")
        typed = ", ".join(p.strip() for p in typed_params if p is not None)
        return f"def {fn_name}({typed}) -> Any:"

    def _find_best_name_match(self, missing: str, names: Iterable[str]) -> str | None:
        candidates = difflib.get_close_matches(missing, list(names), n=1, cutoff=0.6)
        return candidates[0] if candidates else None

    def apply_patch(self, code: str, patch_dsl: str) -> str:
        if self.adapter:
            return apply_patch_dsl(code, patch_dsl)
        return code

    def _load_hf_model(self, model_id: str) -> None:
        if AutoModelForCausalLM is None or AutoTokenizer is None or torch is None:
            raise ImportError("Install transformers and torch to load Hugging Face models.")
        self._hf_tokenizer = AutoTokenizer.from_pretrained(model_id)
        self._hf_model = AutoModelForCausalLM.from_pretrained(model_id).to(self.device)
        self._hf_model.eval()

    def _generate_with_hf(
        self,
        code: str,
        start_line: int,
        end_line: int,
        diagnostics: Sequence[str],
        instruction: str,
    ) -> Tuple[List[PatchEdit], str]:
        assert self._hf_model and self._hf_tokenizer
        prompt = self._format_prompt(code, start_line, end_line, diagnostics, instruction)
        inputs = self._hf_tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            output = self._hf_model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                pad_token_id=self._hf_tokenizer.eos_token_id,
                eos_token_id=self._hf_tokenizer.eos_token_id,
            )
        generated = self._hf_tokenizer.decode(output[0][inputs["input_ids"].shape[1] :])
        # crude cut on PATCH_END or eos
        patch_text = generated.split("<PATCH_END>")[0].strip()
        edits = self._parse_patch_text(patch_text)
        patch_dsl = build_patch_dsl(code.splitlines(), edits)
        return edits, patch_dsl

    def _format_prompt(
        self, code: str, start_line: int, end_line: int, diagnostics: Sequence[str], instruction: str
    ) -> str:
        lines = code.splitlines()
        snippet = "\n".join(lines[start_line - 1 : end_line])
        diag_text = "\n".join(diagnostics)
        return (
            f"<LANG={self.language}>\n"
            f"<REGION_START_LINE> {start_line} </REGION_START_LINE>\n"
            f"<REGION_END_LINE> {end_line} </REGION_END_LINE>\n"
            f"<CODE_START>\n{snippet}\n<CODE_END>\n"
            f"<DIAG_START>\n{diag_text}\n<DIAG_END>\n"
            f"<INSTR_START>\n{instruction}\n<INSTR_END>\n"
            f"<PATCH_START>\n"
        )

    def _parse_patch_text(self, text: str) -> List[PatchEdit]:
        # Expect lines like "@@ 3-4", "- old", "+ new"
        edits: List[PatchEdit] = []
        lines = [ln for ln in text.splitlines() if ln.strip()]
        idx = 0
        original_stub: List[str] = []
        while idx < len(lines):
            header = lines[idx].strip()
            if not header.startswith("@@"):
                idx += 1
                continue
            try:
                span = header.split(" ", maxsplit=1)[1]
                start_str, end_str = span.split("-")
                start, end = int(start_str), int(end_str)
            except Exception:
                break
            idx += 1
            replacement_lines: List[str] = []
            while idx < len(lines) and not lines[idx].startswith("@@"):
                line = lines[idx]
                if line.startswith("+"):
                    replacement_lines.append(line[2:] if line.startswith("+ ") else line[1:])
                elif line.startswith("-"):
                    original_stub.append(line[2:] if line.startswith("- ") else line[1:])
                idx += 1
            replacement = "\n".join(replacement_lines).rstrip("\n") + ("\n" if replacement_lines else "")
            edits.append(PatchEdit(start_line=start, end_line=end, replacement=replacement))
        return edits


def build_patch_dsl(original_lines: List[str], edits: Sequence[PatchEdit]) -> str:
    chunks: List[str] = []
    for edit in edits:
        start = max(1, edit.start_line)
        end = max(start, edit.end_line)
        chunks.append(f"@@ {start}-{end}")
        for line in original_lines[start - 1 : end]:
            chunks.append(f"- {line.rstrip()}")
        for line in edit.replacement.rstrip("\n").splitlines():
            chunks.append(f"+ {line}")
    return "\n".join(chunks)
