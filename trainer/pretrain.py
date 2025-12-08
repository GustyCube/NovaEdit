from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from trainer.utils_dataset import load_jsonl, train_val_split


def run_pretrain(data_path: str | Path, max_steps: int = 100) -> None:
    try:
        import torch
        from torch import nn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Install novaedit[train] to run pretraining.") from exc

    rows = list(load_jsonl(data_path))
    if not rows:
        raise SystemExit("No training rows found.")

    train_rows, val_rows = train_val_split(rows)
    vocab = build_char_vocab(train_rows)
    model = TinyCharModel(vocab_size=len(vocab))
    optim = torch.optim.AdamW(model.parameters(), lr=3e-4)
    loss_fn = nn.CrossEntropyLoss()

    for step in range(max_steps):
        sample = train_rows[step % len(train_rows)]
        tensor = torch.tensor([vocab[c] for c in sample["code"] if c in vocab], dtype=torch.long)
        if tensor.numel() < 2:
            continue
        inputs, targets = tensor[:-1], tensor[1:]
        logits = model(inputs.unsqueeze(0)).squeeze(0)
        loss = loss_fn(logits, targets)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optim.step()
        optim.zero_grad()
        if step % 10 == 0:
            print(f"[pretrain] step={step} loss={loss.item():.4f}")
    print("Finished pretraining stub model.")


class TinyCharModel(nn.Module):
    def __init__(self, vocab_size: int, hidden: int = 64):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, hidden)
        self.gru = nn.GRU(hidden, hidden, batch_first=True)
        self.head = nn.Linear(hidden, vocab_size)

    def forward(self, x):
        emb = self.embed(x)
        out, _ = self.gru(emb.unsqueeze(0))
        return self.head(out).squeeze(0)


def build_char_vocab(rows: List[dict]) -> dict[str, int]:
    chars = sorted({ch for row in rows for ch in row.get("code", "")})
    return {ch: idx for idx, ch in enumerate(chars)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True, help="Path to jsonl of code samples.")
    parser.add_argument("--max-steps", type=int, default=100)
    args = parser.parse_args()
    run_pretrain(args.data, max_steps=args.max_steps)


if __name__ == "__main__":
    main()
