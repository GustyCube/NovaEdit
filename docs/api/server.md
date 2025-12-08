---
title: Server API
outline: [2, 3]
---

# Server API

NovaEdit exposes a single edit endpoint over HTTP.

## POST `/v1/edit`
**Request**
```json
{
  "language": "python",
  "code": "...snippet...",
  "file_path": "app/routes.py",
  "start_line": 37,
  "end_line": 78,
  "diagnostics": ["NameError: name 'itm' is not defined at line 41"],
  "instruction": "fix errors only",
  "max_edits": 5,
  "temperature": 0.2
}
```

**Response**
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
  "model_version": "novaedit-baseline-0.1.0"
}
```

## Running locally
```bash
uvicorn novaedit.server.main:app --reload --port 8000
```

Health check: `GET /health` → `{ "status": "ok", "version": "..." }`

## Error handling
- `400` if `start_line > end_line` or payload is invalid.
- `200` with zero edits if the model emits no changes.

## Notes
- Current model is heuristic; replace `NovaEditModel` with a trained checkpoint to upgrade quality.
- Patch DSL is line-based; the server converts it to structured edits in JSON for clients.
