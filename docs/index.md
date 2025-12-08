---
layout: home
title: NovaEdit Docs
hero:
  name: NovaEdit
  text: Code-edit–first model, server, and tooling
  tagline: Send code + diagnostics, get minimal patches back. Ready for IDEs, CLI, and server deploys.
  actions:
    - theme: brand
      text: Quickstart
      link: /guide/quickstart
    - theme: alt
      text: API
      link: /api/server
    - theme: alt
      text: Plan
      link: /plan
features:
  - icon: ⚡️
    title: Precise patches
    details: Minimal diffs from code regions plus diagnostics; structured patch DSL for IDEs.
  - icon: 🛠
    title: IDE-friendly
    details: FastAPI server + VS Code stub + CLI for quick integration.
  - icon: 📦
    title: Publishable
    details: Dockerfile, MIT license, and Hugging Face push helper included.
---

## What’s inside
- Server: FastAPI app returning structured edits.
- CLI: `novaedit` command for local patching or server calls.
- Language: Python adapter with diagnostics and patch applier.
- Training/Eval: data scripts, tiny pretrain/SFT stubs, regression harness.
- Clients: VS Code extension scaffold.

## Next steps
- Start with the [Quickstart](/guide/quickstart) to run server + CLI.
- Review the [Server API](/api/server) for integration.
- Read the [Plan](/plan) for the roadmap and milestones.
