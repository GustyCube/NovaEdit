from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from novaedit.model.modeling_novaedit import NovaEditModel
from trainer.utils_dataset import load_jsonl, train_val_split


def run_sft(data_path: str | Path, max_steps: int = 100) -> None:
    try:
        import torch
        from torch import nn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Install novaedit[train] to run SFT.") from exc

    rows = list(load_jsonl(data_path))
    if not rows:
        raise SystemExit("No SFT rows found.")

    train_rows, _ = train_val_split(rows)
    model = NovaEditModel()
    encoder = lambda text: torch.tensor([ord(c) % 255 for c in text], dtype=torch.long)
    head = nn.Linear(255, 255)
    opt = torch.optim.AdamW(head.parameters(), lr=5e-4)
    loss_fn = nn.CrossEntropyLoss()

    for step in range(max_steps):
        row = train_rows[step % len(train_rows)]
        _, patch_dsl = model.generate_patch(
            code=row["code"],
            start_line=row["region"]["start_line"],
            end_line=row["region"]["end_line"],
            diagnostics=row.get("diagnostics", []),
            instruction=row.get("instruction"),
        )
        target = encoder(patch_dsl)
        if target.numel() < 2:
            continue
        logits = head(torch.nn.functional.one_hot(target[:-1], num_classes=255).float())
        loss = loss_fn(logits, target[1:])
        loss.backward()
        opt.step()
        opt.zero_grad()
        if step % 10 == 0:
            print(f"[sft] step={step} loss={loss.item():.4f}")
    print("Finished SFT stub.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=100)
    args = parser.parse_args()
    run_sft(args.data, max_steps=args.max_steps)


if __name__ == "__main__":
    main()
