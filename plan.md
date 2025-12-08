# NovaEdit: Specialized Code Edit Model — Full Technical & Project Plan

## 0. Vision & Scope

**Goal:** Build a compact, modern transformer that specializes in **code edits**, not chat — designed to integrate cleanly into IDEs as a "super Quick Fix" for multiple languages, starting with Python.

**Core ideas:**

* Model operates on **code + diagnostics** and outputs **minimal patches**.
* Training is focused on **real diffs** and **synthetic bugfixes**, not general text.
* Architecture and codebase are **language-agnostic**, with **per-language adapters** for parsing and diagnostics.

---

## 1. Primary Use Cases & UX

### 1.1 Use Cases (v1)

* Fixing Python errors in IDEs:

  * NameError, TypeError, missing imports, wrong argument types, etc.
* Refactoring small regions:

  * Replace loops with comprehensions, dead code removal, simplifying conditionals.
* Style and safety updates:

  * Add type hints, better variable naming, simple performance tweaks.

### 1.2 UX Flow in IDE (Python)

1. Developer sees an error squiggle or selects a region.
2. Developer triggers **"NovaEdit: Fix/Improve"** from context menu or Quick Fix shortcut.
3. IDE collects:

   * Code snippet around the error (e.g., ±40 lines).
   * Associated diagnostics (compiler/linter messages).
   * Optional dev instruction string (e.g., "optimize", "add type hints").
4. IDE sends request to NovaEdit server:

   ```json
   {
     "language": "python",
     "code": "...snippet...",
     "file_path": "app/routes.py",
     "start_line": 37,
     "end_line": 78,
     "diagnostics": ["NameError: name 'itm' is not defined"],
     "instruction": "fix errors only"
   }
   ```
5. Server returns **structured patch**:

   ```json
   {
     "edits": [
       {
         "start_line": 41,
         "end_line": 43,
         "replacement": "for i, item in enumerate(items):\n    process(item)\n"
       }
     ]
   }
   ```
6. IDE shows diff preview; dev approves or rejects.

No chat bubble, no walls of explanation — just **precise edits**.

---

## 2. System Architecture Overview

### 2.1 Components

1. **Model Core** (`/model`)

   * Transformer implementation (likely backed by PyTorch + HuggingFace Transformers or similar).
   * Handles tokenization, forward pass, sampling.

2. **Training Pipeline** (`/trainer`, `/data`)

   * Data ingestion: open-source repos, git histories, synthetic bug generator.
   * Data formatters: convert commits and diagnostic runs into training examples.
   * Training scripts: pretraining, edit-SFT, evaluation.

3. **Language Adapters** (`/languages/<lang>`)

   * Python adapter (v1):

     * Parser (e.g., Tree-sitter bindings or `ast` module).
     * Diagnostics integration (mypy, ruff, pytest).
   * Future adapters: JS/TS, Java, etc.

4. **Model Server** (`/server`)

   * API exposing a simple **edit endpoint** (HTTP or gRPC).
   * Handles request validation, tokenization, model inference, patch post-processing.

5. **Clients** (`/clients`)

   * VS Code extension (v1).
   * CLI client for testing.
   * Later: JetBrains plugin, Neovim plugin, etc.

6. **Eval Harness** (`/eval`)

   * Benchmarks for:

     * Bugfix pass rate.
     * Patch size / minimality.
     * Syntax validity.
     * HumanEval-lite style tasks.

### 2.2 High-Level Data Flow

* IDE → Model server: `(language, code snippet, diagnostics, instruction)` →
* Model: encodes into tokens → transformer → decodes **edit DSL** →
* Server: parses edit DSL → structured patch →
* IDE: applies patch or previews it.

---

## 3. Model Design

### 3.1 Base Architecture (Modern but Manageable)

**Core:** Decoder-only transformer (GPT-style), with:

* **RoPE** (rotary positional embeddings) for position encoding.
* **Multi-Query or Grouped-Query Attention** for faster inference.
* **SwiGLU** activations.

**Target sizes (configurable):**

* `novaedit-small`: ~300M params.
* `novaedit-base`: ~600M params.

Config example (pseudo):

```yaml
model:
  d_model: 1024
  n_layers: 18
  n_heads: 16
  n_kv_heads: 4        # for multi-query attention
  d_ff: 2730           # ~2.66 * d_model for SwiGLU
  vocab_size: 32768
  max_seq_len: 2048
  rope_base: 10000
  dropout: 0.0 (inference) / 0.1 (training)
```

### 3.2 Tokenization & Vocab

* Use a **shared code-centric BPE tokenizer** across languages (Python first, but JS/TS/Java-friendly):

  * Train on a mix of Python + general code corpora.
  * Preserve tokens for: `:`, `(`, `)`, `{`, `}`, `[`, `]`, `=`, `==`, `->`, `::`, etc.
* Reserve **special tokens**:

  * `<bos>`, `<eos>`
  * `<LANG=python>`, `<LANG=javascript>`, etc.
  * `<DIAG_START>`, `<DIAG_END>`
  * `<INSTR_START>`, `<INSTR_END>`
  * `<PATCH_START>`, `<PATCH_END>`
  * `<EDIT>`, `<NO_EDIT>` (for edit-or-not classification signal).

Tokenizer training outline:

1. Collect corpus of code files (mainly Python for v1).
2. Use `tokenizers` library (HuggingFace) to train BPE with vocab size ~30–35k.
3. Add reserved special tokens on top.

### 3.3 Input Encoding Format

Given a request, the textual sequence fed to the model might be:

```text
<bos>
<LANG=python>
<FILE_PATH> app/routes.py </FILE_PATH>
<REGION_START_LINE> 37 </REGION_START_LINE>
<CODE_START>
...code snippet here...
<CODE_END>
<DIAG_START>
NameError: name 'itm' is not defined at line 41
<DIAG_END>
<INSTR_START>
fix errors only
<INSTR_END>
<PATCH_START>
```

The model then generates tokens until `<PATCH_END>` (or `<eos>`), representing the patch DSL.

### 3.4 Output Patch DSL

We define a compact diff-like language that is:

* Line-based (easier to apply in editors).
* Minimal but expressive.

Example textual DSL:

```text
@@ 41-43
- for i in range(len(items)):
-     process(items[i])
+ for i, item in enumerate(items):
+     process(item)
```

Alternate JSON-like DSL (for internal parsing):

```json
{
  "edits": [
    {
      "start_line": 41,
      "end_line": 43,
      "replacement": "for i, item in enumerate(items):\n    process(item)\n"
    }
  ]
}
```

**Strategy:** Let the model generate the textual patch DSL. The server parses it into a structured form and returns JSON to clients.

### 3.5 Objective Functions

**Base loss:**

* Standard cross-entropy over patch tokens.

**Patch size regularizer:**

* During training, compute the number of changed lines `L` in the gold patch.
* Add a term: `λ * L_predicted` where `L_predicted` is estimated from the generated patch tokens during teacher-forcing.
* Goal: encourage smaller patches when many alternatives exist.

**Syntax validity penalty (optional advanced):**

* For a subset of batches:

  1. Apply predicted patch to the input code (teacher-forced output).
  2. Try to parse with the language adapter’s parser (e.g., Python AST).
  3. If parse fails, add a small penalty term.

**Edit-or-not head (optional):**

* Add a classification head predicting whether a patch is needed.
* This can later support a mode where the model explicitly outputs `<NO_EDIT>` if the code is already fine.

### 3.6 Copy vs Generate (optional advanced v2)

Add an auxiliary mechanism indicating whether to **copy** tokens from the input or **generate** new ones.

* Could be implemented as an additional output head or via a pointer network variant.
* v1 can skip this for simplicity; v2 can add it to improve patch locality.

---

## 4. Data Pipeline

### 4.1 High-Level Stages

1. **Code Modeling Data (optional base pretrain)**

   * Teaches general Python (and later multi-language) patterns.
2. **Real Edit Data (Git Diffs)**

   * Model learns how small real-world fixes look.
3. **Synthetic Bugfix Data (Diagnostics-Driven)**

   * Model learns to respond to error messages.
4. **Higher-Level Tasks** (docstring→function, function→tests, style refactors).

### 4.2 Data Storage & Schemas

Use a consistent JSONL format for training samples, e.g.:

```json
{
  "language": "python",
  "file_path": "app/routes.py",
  "region": {"start_line": 37, "end_line": 78},
  "code": "...snippet...",
  "diagnostics": ["NameError: name 'itm' is not defined"],
  "instruction": "fix errors only",
  "patch_dsl": "@@ 41-43\n- for i in range(len(items)):\n-     process(items[i])\n+ for i, item in enumerate(items):\n+     process(item)\n"
}
```

Store separate JSONL files for different data types (real diffs, synthetic bugfixes, etc.) and mix them via sampling ratios.

### 4.3 Code Modeling Data (Stage 1)

**Sources:**

* Open-source Python projects from GitHub with permissive licenses.
* Filtered subsets from large code datasets (e.g. The Stack / CodeSearchNet Python).

**Filters:**

* Exclude:

  * `dist/`, `build/`, `venv/`, `.tox/`, `.mypy_cache/`, etc.
  * auto-generated files (protobufs, migrations, etc.).
  * files above a certain size (e.g. > 2k LOC).

**Format:**

* For pretraining, you can use

  ```json
  { "language": "python", "code": "...full file or chunk..." }
  ```
* Sequence construction: pack multiple files/chunks per sequence while respecting `max_seq_len`.

### 4.4 Real Git Diff Data (Stage 2)

**Steps:**

1. Clone curated Python repos.
2. For each repo:

   * Get commit list.
   * For each commit:

     * Skip merge commits.
     * Obtain `git diff` against parent.
     * Filter to `.py` files.
3. For each changed file:

   * Extract `before` and `after` versions.
   * Compute a line-based diff.
   * Skip huge diffs (e.g. > 200 changed lines).
   * Derive:

     * `code_region`: region around changes (e.g. ±40 lines around hunk).
     * `patch_dsl`: textual representation of the diff hunks.
   * Optionally use commit message as an `instruction` if it looks like a bugfix (e.g. contains "fix", "bug", "crash").

This becomes training data for:

* `(code_region [+ maybe instruction]) → patch_dsl`

### 4.5 Synthetic Bugfix Data (Diagnostics-Driven)

**Goal:** teach model to map from **diagnostic messages + broken code** to fixes.

**Pipeline:**

1. Take clean Python files that parse and (optionally) pass tests.
2. Apply transformations to introduce controlled bugs:

   * Rename variables to undefined names.
   * Remove imports.
   * Swap argument orders.
   * Remove `await` in async code.
   * Change comparison operators.
3. Run diagnostics:

   * `mypy` or pyright for type errors.
   * `ruff` / `flake8` / `pylint` for style and some logic issues.
   * Optionally `pytest` for test failures.
4. For each error-producing transformation:

   * Record `buggy_code_region` and diagnostics.
   * Record the correct patch that restores original code.

Now we have:

* Input: (buggy code + diagnostics + optional instruction like "fix errors only")
* Output: patch_dsl (the reverse transformation).

### 4.6 Higher-Level Tasks

**Docstring → Function:**

* From real functions with docstrings:

  * Input: signature + docstring.
  * Output: function body.
* Use as a smaller fraction of training to avoid overfitting to generation.

**Function → Tests:**

* From projects with well-structured tests.

  * Input: function code.
  * Output: minimal test snippet that exercises key paths.
* Good for generating tests based on existing code.

**Refactors / Style:**

* Use tools like `black`, `ruff`, or custom transformations:

  * Intentionally mess up style or code structure.
  * Label the clean version as the target.

These tasks are mixed with edit tasks to improve generalization.

---

## 5. Training Strategy

### 5.1 Stages

1. **(Optional) Base Code Pretraining**

   * Objective: standard LM over code.
   * Benefit: gives the transformer solid code fluency.

2. **Edit-Focused SFT (Supervised Fine-Tuning)**

   * Train on real diffs + synthetic bugfixes.
   * Input formatted as described; target is `patch_dsl`.

3. **(Optional) RLAIF / Ranking on Patch Quality**

   * Train a small reward model that scores patches based on:

     * whether they apply cleanly.
     * whether they fix diagnostics.
     * patch size / minimality.
   * Use it to refine the base model via preference optimization.

### 5.2 Training Setup

* Framework: PyTorch + HuggingFace Transformers or a lightweight custom trainer.
* Hardware: initial experiments on single or few GPUs (e.g., 24–48GB VRAM per GPU).
* Mixed-precision training (bfloat16 or fp16).

**Hyperparameters (example for 300M model, SFT phase):**

* Batch size (tokens): ~256k–512k tokens per step (global).
* Learning rate: ~3e-4 (with warmup & cosine decay).
* Warmup steps: ~2k–5k.
* Weight decay: ~0.1 (AdamW).
* Gradient clipping: 1.0.

### 5.3 Curriculum / Mixing Strategy

* Start SFT with a higher ratio of **simpler real diffs** and **synthetic single-error bugfixes**.
* Gradually add:

  * refactor tasks.
  * multi-error cases.
* Example mixture:

  * 50% synthetic bugfixes.
  * 30% real git diffs.
  * 10% docstring/function.
  * 10% refactor/style.

---

## 6. Evaluation Plan

### 6.1 Core Metrics

1. **Bugfix success rate**

   * On synthetic bugfix dataset:

     * Apply predicted patch.
     * Re-run diagnostics.
     * Measure % of cases where errors go away.

2. **Patch validity**

   * % of patches that:

     * apply cleanly (no conflicts).
     * result in syntactically valid code.

3. **Patch minimality**

   * Average number of lines changed vs. ground truth.

4. **Task-specific metrics:**

   * For docstring→function tasks: pass rate on unit tests.
   * For refactors: style tool (e.g. `ruff`) warns reduced.

### 6.2 HumanEval-Lite for Edits

* Construct a mini benchmark:

  * Each item includes:

    * broken/ugly Python code.
    * instruction (e.g., "fix", "optimize", "add type hints").
    * expected behavior tests.
  * Evaluate with patch application + test execution.

### 6.3 Regression Suite

* Save a set of representative examples.
* Run them before each new model version.
* Track metrics over time to avoid regressions.

---

## 7. Multi-Language Extensibility

### 7.1 Language Abstraction Layer

Define a standard interface per language under `/languages/<lang>`:

```python
class LanguageAdapter(Protocol):
    name: str

    def tokenize_code(self, code: str) -> str:
        ...  # optional language-specific pre-processing

    def parse_ast(self, code: str) -> Optional[AstNode]:
        ...

    def run_diagnostics(self, code: str, path: str) -> list[str]:
        ...

    def apply_patch(self, code: str, patch_dsl: str) -> str:
        ...
```

For Python, implement this using:

* `ast` or Tree-sitter for parsing.
* `mypy` / pyright / ruff for diagnostics.

Later:

* Add `LanguageAdapter` for JS/TS, Java, etc., using their respective tools.

### 7.2 Model Sharing vs Specialization

Options:

1. **Single shared model** with `<LANG=...>` tags:

   * Simple deployment.
   * Risk: interference between languages.
2. **Base model + per-language LoRA adapters:**

   * Shared backbone.
   * Lightweight per-language fine-tunes.

v1: Python-only or Python-dominant shared model.
Future: Add JS/TS via adapters.

### 7.3 Data Namespacing

* Organize training data per language:

  * `/data/python/*`
  * `/data/javascript/*`
  * etc.
* Each JSONL record includes `"language"` field.
* Sampling strategy can balance per-language proportion.

---

## 8. Model Server & API

### 8.1 API Contract

**Endpoint:** `POST /v1/edit`

**Request:**

```json
{
  "language": "python",
  "code": "...snippet...",
  "file_path": "app/routes.py",
  "start_line": 37,
  "end_line": 78,
  "diagnostics": [
    "NameError: name 'itm' is not defined at line 41"
  ],
  "instruction": "fix errors only",
  "max_edits": 5,
  "temperature": 0.2
}
```

**Response:**

```json
{
  "edits": [
    {
      "start_line": 41,
      "end_line": 43,
      "replacement": "for i, item in enumerate(items):\n    process(item)\n"
    }
  ],
  "raw_patch_dsl": "@@ 41-43\n- for i in range(len(items)):\n-     process(items[i])\n+ for i, item in enumerate(items):\n+     process(item)\n",
  "model_version": "novaedit-base-0.1.0"
}
```

### 8.2 Server Implementation

* Language: Python (FastAPI) or Go (for performance) wrapping a Python model runtime.
* Responsibilities:

  * Validate inputs.
  * Construct model input strings.
  * Run tokenization + model inference.
  * Parse patch DSL → structured edits.
  * Optionally validate patches with the language adapter.
  * Return JSON response.

### 8.3 Deployment

* Package as Docker image.
* Environment variables for:

  * model path.
  * device selection (CPU / GPU).
  * max concurrent requests.
* Target:

  * Initial: single GPU instance.
  * Later: autoscaling cluster behind load balancer.

---

## 9. IDE & Tooling Integration

### 9.1 VS Code Extension (v1)

**Structure:**

* `extension.ts` (TypeScript):

  * Registers commands:

    * `novaedit.fixCode`.
    * `novaedit.improveCode`.
  * On trigger:

    * Determine languageId.
    * Get selected lines or diagnostics range.
    * Extract code snippet.
    * Send HTTP request to NovaEdit server.
    * Apply returned edits as `WorkspaceEdit`.

**Pseudo-code:**

```ts
const fixCommand = vscode.commands.registerCommand('novaedit.fixCode', async () => {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const doc = editor.document;
  const selection = editor.selection;
  const startLine = selection.start.line;
  const endLine = selection.end.line;

  const code = doc.getText(new vscode.Range(startLine, 0, endLine, doc.lineAt(endLine).text.length));

  const diagnostics = vscode.languages.getDiagnostics(doc.uri)
    .filter(d => d.range.start.line >= startLine && d.range.end.line <= endLine)
    .map(d => d.message);

  const res = await fetch(NOVAEDIT_URL + '/v1/edit', { ... });
  const body = await res.json();

  const edit = new vscode.WorkspaceEdit();
  for (const e of body.edits) {
    const range = new vscode.Range(e.start_line - 1, 0, e.end_line, 0);
    edit.replace(doc.uri, range, e.replacement);
  }

  vscode.workspace.applyEdit(edit);
});
```

### 9.2 Other IDEs via LSP

Implement a **Language Server Protocol (LSP)** server that wraps NovaEdit:

* LSP `codeAction` request → call NovaEdit → return code actions as patches.
* Allows integration with:

  * Neovim.
  * Sublime.
  * JetBrains via LSP plugins.

---

## 10. Repository Structure

Proposed monorepo layout:

```text
novaedit/
  README.md
  pyproject.toml          # for Python tooling

  model/
    config/
      novaedit-small.yaml
      novaedit-base.yaml
    src/
      modeling_novaedit.py
      tokenization_novaedit.py

  data/
    python/
      raw/
      processed/
      diffs/
      synthetic_bugfixes/
      docstring_tasks/
    javascript/
      ... (future)

  trainer/
    pretrain.py
    sft_edit.py
    utils_dataset.py
    utils_loss.py

  eval/
    run_eval_bugfix.py
    run_eval_regression.py
    datasets/

  languages/
    python/
      adapter.py
      diagnostics.py
      patch_apply.py
    javascript/
      adapter.py   # future

  server/
    main.py        # FastAPI / gRPC entrypoint
    api_schemas.py

  clients/
    vscode/
      package.json
      src/extension.ts
    cli/
      novaedit_cli.py

  scripts/
    prepare_python_data.sh
    mine_git_diffs.py
    generate_synthetic_bugs.py

  docker/
    Dockerfile
```

---

## 11. Milestones & Roadmap

### Milestone 1 — Prototype (Python-only, small model)

* [ ] Implement tokenizer and special tokens.
* [ ] Build minimal Python data pipeline:

  * raw code modeling data.
  * small set of synthetic bugfix examples.
* [ ] Train a **toy model** (e.g. 50M params) to output `patch_dsl` for simple bugfixes.
* [ ] Implement simple NovaEdit server.
* [ ] VS Code extension prototype calling the server.

### Milestone 2 — Real Git Diffs & Better Model

* [ ] Mine real git diffs from curated repos.
* [ ] Expand synthetic bug catalog.
* [ ] Train `novaedit-small` (~300M params) with mixed data.
* [ ] Implement evaluation harness with bugfix success metrics.
* [ ] Improve patch DSL parsing and robustness.

### Milestone 3 — Production-Ready Python Support

* [ ] Optimize inference (multi-query attention, quantization if needed).
* [ ] Harden server (timeouts, rate limiting, logs).
* [ ] Refine VS Code extension UI/UX (diff view, settings).
* [ ] Populate regression suite.
* [ ] Release `novaedit-base` (~600M params) with documented metrics.

### Milestone 4 — Multi-Language Extension

* [ ] Implement `LanguageAdapter` for JS/TS.
* [ ] Collect JS/TS datasets (code + diffs + synthetic bugfixes).
* [ ] Train JS/TS-capable variant (shared backbone or adapter-based).
* [ ] Extend server + clients to support language switching.

### Milestone 5 — Advanced Features

* [ ] Add copy-vs-generate mechanism.
* [ ] Experiment with RLAIF on patch quality.
* [ ] Add `NO_EDIT` support and confidence scoring.
* [ ] Deeper IDE integrations (test runner, refactor workflows).

---

## 12. How to Start (Practical First Steps)

1. **Set up repo skeleton** as above.
2. **Implement tokenizer** and train it on a Python-only corpus.
3. **Write data scripts** to:

   * ingest a handful of Python repos.
   * mine a small number of git diffs.
   * generate a small synthetic bugfix dataset.
4. **Create a minimal edit model**:

   * reuse an existing small transformer implementation.
   * train on a tiny dataset to prove end-to-end: `(code + diag) → patch_dsl`.
5. **Build a tiny FastAPI server** and a **CLI client** to manually test patches.
6. After that works, scale up:

   * more data.
   * larger model config.
   * IDE integration.

This gives you a concrete, modern, and extensible blueprint for a **real code-edit LLM system** that is meaningfully different from a generic LLM just "outputting JSON" — it is trained and engineered as a **patch generator** tightly integrated into real developer workflows and extensible to new languages via a clean abstraction layer.
