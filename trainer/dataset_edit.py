from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


try:
    import torch
except Exception:  # pragma: no cover - optional dependency
    torch = None  # type: ignore


@dataclass
class EditSample:
    prompt: str
    target: str


def load_edit_samples(paths: Sequence[str | Path]) -> List[EditSample]:
    import json

    samples: List[EditSample] = []
    for path in paths:
        with Path(path).open() as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                prompt = build_prompt(
                    language=row.get("language", "python"),
                    code=row["code"],
                    start_line=row["region"]["start_line"],
                    end_line=row["region"]["end_line"],
                    diagnostics=row.get("diagnostics", []),
                    instruction=row.get("instruction", ""),
                )
                target = row.get("patch_dsl", "")
                samples.append(EditSample(prompt=prompt, target=target))
    return samples


def build_prompt(
    language: str,
    code: str,
    start_line: int,
    end_line: int,
    diagnostics: Iterable[str],
    instruction: str,
) -> str:
    diag_text = "\n".join(diagnostics)
    lines = code.splitlines()
    snippet = "\n".join(lines[start_line - 1 : end_line])
    return (
        f"<LANG={language}>\n"
        f"<REGION_START_LINE> {start_line} </REGION_START_LINE>\n"
        f"<REGION_END_LINE> {end_line} </REGION_END_LINE>\n"
        f"<CODE_START>\n{snippet}\n<CODE_END>\n"
        f"<DIAG_START>\n{diag_text}\n<DIAG_END>\n"
        f"<INSTR_START>\n{instruction}\n<INSTR_END>\n"
        f"<PATCH_START>\n"
    )


class EditDataset(torch.utils.data.Dataset):  # type: ignore[misc]
    """PyTorch dataset for edit examples."""

    def __init__(self, tokenizer, samples: List[EditSample], max_length: int = 2048):
        if torch is None:
            raise ImportError("Install torch to use EditDataset.")
        self.tokenizer = tokenizer
        self.samples = samples
        self.max_length = max_length

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.samples)

    def __getitem__(self, idx: int):
        sample = self.samples[idx]
        encoded = self.tokenizer(
            sample.prompt,
            text_target=sample.target,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in encoded.items()}
        return item


def collate_fn(batch):
    if not batch:  # pragma: no cover - defensive
        return {}
    keys = batch[0].keys()
    return {k: torch.stack([item[k] for item in batch], dim=0) for k in keys}
