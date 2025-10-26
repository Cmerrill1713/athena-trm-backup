-- Athena Neovim Adapter
-- Ultra-thin adapter for Neovim

local M = {}

local ATHENA_URL = "http://localhost:8765"

-- Helper to get current context
local function get_context()
    local buf = vim.api.nvim_get_current_buf()
    local filepath = vim.api.nvim_buf_get_name(buf)
    local cursor = vim.api.nvim_win_get_cursor(0)
    
    -- Get selection
    local selection = nil
    local mode = vim.fn.mode()
    if mode == 'v' or mode == 'V' then
        local start_line = vim.fn.line("'<")
        local end_line = vim.fn.line("'>")
        selection = {start = start_line, ["end"] = end_line}
    end
    
    -- Get visible buffers
    local visible_files = {}
    for _, win in ipairs(vim.api.nvim_list_wins()) do
        local winbuf = vim.api.nvim_win_get_buf(win)
        local winfile = vim.api.nvim_buf_get_name(winbuf)
        if winfile ~= "" then
            table.insert(visible_files, winfile)
        end
    end
    
    -- Get diagnostics
    local diagnostics = {}
    for _, diag in ipairs(vim.diagnostic.get(buf)) do
        table.insert(diagnostics, {
            file = filepath,
            line = diag.lnum + 1,
            msg = diag.message,
            severity = diag.severity
        })
    end
    
    return {
        repoRoot = vim.fn.getcwd(),
        file = filepath,
        cursor = {line = cursor[1], col = cursor[2]},
        selection = selection,
        visibleFiles = visible_files,
        diagnostics = diagnostics,
        intent = "explain-and-fix"
    }
end

-- Main function: Call Athena
function M.athena_assist()
    local context = get_context()
    
    -- Show loading message
    vim.notify("Athena is thinking...", vim.log.levels.INFO)
    
    -- Call Athena via curl (async)
    local json = vim.fn.json_encode(context)
    local cmd = string.format(
        "curl -s -X POST %s/assist -H 'Content-Type: application/json' -d '%s'",
        ATHENA_URL,
        json:gsub("'", "'\\''")
    )
    
    vim.fn.jobstart(cmd, {
        stdout_buffered = true,
        on_stdout = function(_, data)
            if data then
                local response_text = table.concat(data, "\n")
                local ok, response = pcall(vim.fn.json_decode, response_text)
                
                if ok and response.summary then
                    -- Open new split with answer
                    vim.cmd('vsplit')
                    local newbuf = vim.api.nvim_create_buf(false, true)
                    vim.api.nvim_win_set_buf(0, newbuf)
                    
                    -- Set content
                    local lines = vim.split(response.summary, "\n")
                    
                    -- Add citations
                    table.insert(lines, "")
                    table.insert(lines, "Citations:")
                    for _, cite in ipairs(response.citations or {}) do
                        table.insert(lines, "  " .. cite)
                    end
                    
                    vim.api.nvim_buf_set_lines(newbuf, 0, -1, false, lines)
                    vim.api.nvim_buf_set_option(newbuf, 'buftype', 'nofile')
                    vim.api.nvim_buf_set_option(newbuf, 'filetype', 'markdown')
                    
                    vim.notify("Athena answered!", vim.log.levels.INFO)
                else
                    vim.notify("Athena error: " .. response_text, vim.log.levels.ERROR)
                end
            end
        end,
        on_stderr = function(_, data)
            if data and #data > 0 then
                vim.notify("Athena error: " .. table.concat(data, "\n"), vim.log.levels.ERROR)
            end
        end
    })
end

-- Keymapping: <leader>aa for "Athena Assist"
vim.keymap.set('n', '<leader>aa', M.athena_assist, {desc = "Athena: Explain & Fix"})
vim.keymap.set('v', '<leader>aa', M.athena_assist, {desc = "Athena: Explain & Fix"})

return M

