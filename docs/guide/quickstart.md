---
title: Quickstart
outline: [2, 3]
---

# Quickstart

Run NovaEdit locally: server, CLI, and IDE client.

## Prerequisites
- Python 3.10+
- Optional: Node 18+ (for docs) and VS Code (for the extension)

## Install
```bash
pip install -e .            # base runtime (CLI + server)
pip install -e .[dev]       # add linters/tests
```

## Run the server
```bash
uvicorn novaedit.server.main:app --reload --port 8000
```
Health check: `curl http://localhost:8000/health`

## Try the CLI
```bash
novaedit edit --code-file examples/buggy.py --language python
```

## Call the HTTP API
```bash
curl -X POST http://localhost:8000/v1/edit \
  -H "Content-Type: application/json" \
  -d '{"language":"python","code":"def add(a,b):\n    return a+b\nresult=add(1)","file_path":"app.py","start_line":1,"end_line":4,"diagnostics":["TypeError: add() missing 1 required positional argument: b"],"instruction":"fix errors only"}'
```

## VS Code extension (stub)
```bash
cd clients/vscode
npm install
npm run compile
# Press F5 in VS Code to launch the Extension Development Host
```

## Docker
```bash
docker build -t novaedit:dev -f docker/Dockerfile .
docker run -p 8000:8000 novaedit:dev
```

## Tests
```bash
pip install -e .[dev]
pytest
```

## Docs
```bash
cd docs
npm install
npm run dev      # or npm run build
```
