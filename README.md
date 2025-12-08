# NovaEdit

NovaEdit is a compact, code-edit–first model stack and toolkit. It accepts code regions plus diagnostics and returns minimal patches that IDEs can preview and apply. The repository includes a small heuristic baseline, server, CLI, training/eval scaffolding, and a VS Code extension stub so the project is immediately runnable and ready for GitHub/Hugging Face publication.

## Quickstart
- Install (Python 3.10+): `pip install -e .` (adds the `novaedit` CLI). For training features, use `pip install -e .[train]`.
- Run the server: `uvicorn novaedit.server.main:app --reload --port 8000`
- Try a local edit without the server: `novaedit edit --code-file examples/buggy.py --language python`
- Call the API: `curl -X POST http://localhost:8000/v1/edit -H "Content-Type: application/json" -d '{"language":"python","code":"def add(a,b):\n    return a+b\nresult=add(1)","file_path":"app.py","start_line":1,"end_line":4,"diagnostics":["TypeError: add() missing 1 required positional argument: b"],"instruction":"fix errors only"}'`

## What’s Included
- `src/novaedit/model/*`: lightweight tokenizer wrapper, config objects, and a heuristic `NovaEditModel` that emits small patches; pluggable with future Transformer checkpoints.
- `src/novaedit/server/*`: FastAPI app exposing `/v1/edit` with Pydantic schemas, env-configurable backend/device/concurrency.
- `src/novaedit/languages/python/*`: language adapter, simple diagnostics, and patch application helpers.
- `src/novaedit/languages/javascript/*`: stub adapter to unblock multi-language wiring.
- `src/novaedit/clients/cli/*`: Typer CLI for local edits or talking to the server.
- `trainer/*` and `scripts/*`: data prep and training stubs matching the plan.
- `eval/*`: simple bugfix/regression harness skeletons.
- `clients/vscode/*`: starter VS Code extension targeting the HTTP endpoint.
- `docker/Dockerfile`: container to serve the API with a bundled model.
- `docs/`: VitePress docs site (2.0 alpha; run with `npm run dev` from `docs`).
- `data/python/processed/sample_edits.jsonl`: tiny sample dataset to smoke-test training pipelines.
- `model/tokenizer-sample.json`: toy tokenizer built from `examples/` for pipeline sanity checks.

## Using a Hugging Face checkpoint (optional)
The baseline is heuristic. To try a HF model (e.g., a small causal LM), instantiate the model with `NovaEditModel(hf_model_id="org/model-name")`. Requires `transformers` and `torch` installed and will generate patch text via the HF model before parsing to structured edits.

## CLI highlights
- `novaedit edit --code-file examples/buggy.py --language python --hf-model-id org/model` to use a local HF model.
- `novaedit regression` to run built-in regression cases.
- Pass diagnostics via `--diag` flags or `--diagnostics-file` (one per line). Use `--max-edits` to cap patch size.

## Server config
- Environment variables:
  - `NOVAEDIT_MODEL_ID` to load a HF model for inference (falls back to heuristics if unset).
  - `NOVAEDIT_DEVICE` to pick device (e.g., `cuda:0`).
  - `NOVAEDIT_LANGUAGE` (default `python`) and `NOVAEDIT_MAX_CODE_LINES` (default `2000`).
- Health endpoint reports backend type and language.

## Hugging Face Model Card & Upload
- Edit `model/config/novaedit-small.yaml` (or add your own) and place trained weights under `weights/` or point to a Hub repo.
- Use `scripts/push_to_hub.py` (or `huggingface_hub` CLI) to create a repository:  
  `python scripts/push_to_hub.py --repo novaedit-small --path weights/novaedit-small`
- For Spaces, deploy the FastAPI server via `docker/Dockerfile` or a small `app.py` that imports `novaedit.server.main:app`.

## Repo Layout
- `plan.md` — original technical plan (kept for context).
- `pyproject.toml` — package metadata and dependencies; installs `novaedit` CLI.
- `model/config/*.yaml` — sample model configs aligned to the plan (small/base).
- `examples/` — tiny code snippets for smoke tests.
- `tests/` — placeholder for future automated checks (not populated yet).

## Status
This is a working scaffold: server and CLI run today with a rule-based baseline model. Training/eval code is provided as structured stubs to be filled with real data and weights. Refer to `plan.md` for the roadmap toward a full transformer-based NovaEdit release.
