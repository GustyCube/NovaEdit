---
title: Data & Training
outline: [2, 3]
---

# Data & Training

NovaEdit is trained to emit patch DSL from code regions + diagnostics. This repo includes scaffolding you can extend with real data and checkpoints.

## Data layout
- `data/python/raw` — raw corpora
- `data/python/diffs` — mined git diffs
- `data/python/synthetic_bugfixes` — generated bugfix samples
- `data/javascript/*` — future languages

## Prep scripts
```bash
bash scripts/prepare_python_data.sh
# mines small diffs and synthetic samples into data/python/...
```
- `scripts/mine_git_diffs.py` — collect recent Python diffs from a repo.
- `scripts/generate_synthetic_bugs.py` — inject simple bugs and save JSONL.

## Training stubs
- `trainer/pretrain.py` — tiny character LM to smoke-test pipelines.
- `trainer/sft_edit.py` — SFT scaffold using the heuristic model as pseudo-labels.
- Config examples live in `model/config/*.yaml` (small/base).

## Evaluation
- `eval/run_eval_bugfix.py --data <jsonl>` — measures diagnostic count reduction.
- `eval/run_eval_regression.py` — prints patches for a small regression suite.

## Hugging Face
- Push weights/config with `scripts/push_to_hub.py --repo <org/model> --path weights/novaedit-small`.
- For Spaces, run the FastAPI app (`novaedit.server.main:app`) via the provided Dockerfile.
