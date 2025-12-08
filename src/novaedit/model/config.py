from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class ModelConfig:
    d_model: int = 1024
    n_layers: int = 18
    n_heads: int = 16
    n_kv_heads: int = 4
    d_ff: int = 2730
    vocab_size: int = 32768
    max_seq_len: int = 2048
    rope_base: int = 10000
    dropout: float = 0.0
    pad_token_id: int = 0
    bos_token_id: int = 1
    eos_token_id: int = 2

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ModelConfig":
        data: Dict[str, Any] = yaml.safe_load(Path(path).read_text())
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


SMALL_CONFIG_PATH = Path("model/config/novaedit-small.yaml")
BASE_CONFIG_PATH = Path("model/config/novaedit-base.yaml")


def load_default_config(prefer_small: bool = True) -> ModelConfig:
    """Load the shipped YAML configs."""
    path = SMALL_CONFIG_PATH if prefer_small else BASE_CONFIG_PATH
    if not path.exists():
        return ModelConfig()
    return ModelConfig.from_yaml(path)
