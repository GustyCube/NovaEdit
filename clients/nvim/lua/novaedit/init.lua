local M = {}

local default_opts = {
  endpoint = "http://localhost:8000/v1/edit",
  instruction = "fix errors only",
  timeout = 15000,
}

local config = vim.deepcopy(default_opts)

function M.setup(opts)
  config = vim.tbl_deep_extend("force", default_opts, opts or {})
  vim.api.nvim_create_user_command("NovaEditFix", function()
    M.run()
  end, { range = true })
end

local function get_selection()
  local bufnr = vim.api.nvim_get_current_buf()
  local start_line, _ = unpack(vim.api.nvim_buf_get_mark(bufnr, "<"))
  local end_line, _ = unpack(vim.api.nvim_buf_get_mark(bufnr, ">"))
  if start_line == 0 or end_line == 0 then
    start_line = vim.api.nvim_win_get_cursor(0)[1]
    end_line = start_line
  end
  if start_line > end_line then
    start_line, end_line = end_line, start_line
  end
  local lines = vim.api.nvim_buf_get_lines(bufnr, start_line - 1, end_line, false)
  return start_line, end_line, table.concat(lines, "\n")
end

function M.run()
  local start_line, end_line, code = get_selection()
  local diagnostics = {} -- TODO: optional LSP diagnostics integration
  local payload = {
    language = vim.bo.filetype or "python",
    code = code,
    file_path = vim.api.nvim_buf_get_name(0),
    start_line = start_line,
    end_line = end_line,
    diagnostics = diagnostics,
    instruction = config.instruction,
  }

  local json = vim.fn.json_encode(payload)
  local job = require("plenary.job")
  job
    :new({
      command = "curl",
      args = {
        "-s",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        "--max-time",
        tostring(config.timeout / 1000),
        "-d",
        json,
        config.endpoint,
      },
      on_exit = function(j, return_val)
        if return_val ~= 0 then
          vim.schedule(function()
            vim.notify("NovaEdit failed: curl error", vim.log.levels.ERROR)
          end)
          return
        end
        local res = table.concat(j:result(), "\n")
        local ok, body = pcall(vim.fn.json_decode, res)
        if not ok or not body.edits then
          vim.schedule(function()
            vim.notify("NovaEdit: invalid response", vim.log.levels.ERROR)
          end)
          return
        end
        apply_edits(body.edits, start_line, end_line)
      end,
    })
    :start()
end

function apply_edits(edits, start_line, end_line)
  local bufnr = vim.api.nvim_get_current_buf()
  vim.schedule(function()
    for _, edit in ipairs(edits) do
      local s = math.max(1, edit.start_line) - 1
      local e = math.max(s, edit.end_line) - 1
      local replacement = {}
      for line in string.gmatch(edit.replacement .. "\n", "([^\n]*)\n") do
        table.insert(replacement, line)
      end
      vim.api.nvim_buf_set_lines(bufnr, s, e + 1, false, replacement)
    end
    vim.notify("NovaEdit applied", vim.log.levels.INFO)
  end)
end

return M
