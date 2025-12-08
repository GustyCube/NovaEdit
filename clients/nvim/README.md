## NovaEdit Neovim (stub)

Lightweight Neovim command that sends the current selection to the NovaEdit server and applies returned edits. Requires Neovim 0.8+ with `plenary.nvim` for HTTP.

### Install (lazy.nvim example)
```lua
{
  "yourname/novaedit-nvim",
  dependencies = { "nvim-lua/plenary.nvim" },
  config = function()
    require("novaedit").setup({
      endpoint = "http://localhost:8000/v1/edit",
      instruction = "fix errors only",
      timeout = 15000,
    })
  end,
}
```

### Usage
- Select lines in visual mode (or leave empty to use the current line), then run:
```
:NovaEditFix
```
The plugin sends the selected lines with diagnostics (if available from LSP) to the server and applies returned edits.

### Config
- `endpoint`: NovaEdit server URL.
- `instruction`: text to pass to the model.
- `timeout`: request timeout in ms.
