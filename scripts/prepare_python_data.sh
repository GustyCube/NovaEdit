#!/usr/bin/env bash
set -euo pipefail

# Simple data prep scaffold for NovaEdit.
# 1) Mine git diffs into data/python/diffs
# 2) Generate synthetic bugfix samples
# 3) Merge into a single JSONL file

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python "$ROOT_DIR/scripts/mine_git_diffs.py" --repo "$ROOT_DIR" --out "$ROOT_DIR/data/python/diffs/sample_diffs.jsonl"
python "$ROOT_DIR/scripts/generate_synthetic_bugs.py" --source "$ROOT_DIR/examples" --out "$ROOT_DIR/data/python/synthetic_bugfixes/samples.jsonl"

echo "Data prep complete."
