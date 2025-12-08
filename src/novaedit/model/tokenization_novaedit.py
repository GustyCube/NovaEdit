from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

try:
    from tokenizers import Tokenizer
    from tokenizers.models import BPE
    from tokenizers.pre_tokenizers import Whitespace
    from tokenizers.trainers import BpeTrainer
except ImportError:  # pragma: no cover - optional dependency
    Tokenizer = None  # type: ignore
    BPE = None  # type: ignore
    Whitespace = None  # type: ignore
    BpeTrainer = None  # type: ignore


SPECIAL_TOKENS = [
    "<bos>",
    "<eos>",
    "<LANG=python>",
    "<CODE_START>",
    "<CODE_END>",
    "<DIAG_START>",
    "<DIAG_END>",
    "<INSTR_START>",
    "<INSTR_END>",
    "<PATCH_START>",
    "<PATCH_END>",
    "<EDIT>",
    "<NO_EDIT>",
]


class NovaEditTokenizer:
    """Tiny wrapper around Hugging Face `tokenizers` with sensible defaults."""

    def __init__(self, tokenizer: Optional["Tokenizer"] = None):
        if tokenizer is None and Tokenizer is None:
            raise ImportError("tokenizers is not installed; install novaedit[train].")
        self._tokenizer = tokenizer or Tokenizer(BPE())

    @classmethod
    def from_file(cls, path: str | Path) -> "NovaEditTokenizer":
        if Tokenizer is None:
            raise ImportError("tokenizers is not installed; install novaedit[train].")
        tokenizer = Tokenizer.from_file(str(path))
        return cls(tokenizer)

    def train_from_files(
        self, files: Iterable[str | Path], vocab_size: int = 32000, min_frequency: int = 2
    ) -> None:
        if Tokenizer is None or BpeTrainer is None or Whitespace is None:
            raise ImportError("tokenizers is not installed; install novaedit[train].")
        trainer = BpeTrainer(
            vocab_size=vocab_size,
            min_frequency=min_frequency,
            special_tokens=SPECIAL_TOKENS,
        )
        self._tokenizer.pre_tokenizer = Whitespace()
        self._tokenizer.train([str(f) for f in files], trainer=trainer)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._tokenizer.save(str(path))

    def encode(self, text: str) -> List[int]:
        return self._tokenizer.encode(text).ids

    def decode(self, ids: List[int]) -> str:
        return self._tokenizer.decode(ids)

    @property
    def vocab_size(self) -> int:
        return self._tokenizer.get_vocab_size()
