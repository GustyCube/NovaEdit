## NovaEdit VS Code Extension (stub)

This is a lightweight starter extension that calls the NovaEdit HTTP API.

### Build & Run
1. Install dependencies: `npm install`
2. Compile: `npm run compile`
3. Press `F5` in VS Code to launch an Extension Development Host.

The extension sends selected code (plus in-range diagnostics) to `NOVAEDIT_URL` or `http://localhost:8000/v1/edit` by default and applies returned edits.
