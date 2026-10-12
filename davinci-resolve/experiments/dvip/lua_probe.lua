-- Diagnostic only. Runs via the official Lua Console; no editing, network or license changes.
local output = os and os.getenv and os.getenv("CODEX_RENDER_OUTPUT")
local app = resolve
if not app and bmd and bmd.scriptapp then
    app = bmd.scriptapp("Resolve")
end
if output and bmd and bmd.writestring then
    local connected = app ~= nil
    local version, product = "", ""
    if connected then
        local ok, value = pcall(function() return app:GetVersionString() end)
        if ok then version = tostring(value or "") end
        ok, value = pcall(function() return app:GetProductName() end)
        if ok then product = tostring(value or "") end
    end
    -- Only whitelisted text: never write paths, tokens or session state.
    version = string.gsub(version, "[^%d%.]", "")
    product = string.gsub(product, "[^%w%s%-]", "")
    local state = connected and "true" or "false"
    local body = '{"apiConnected":' .. state .. ',"language":"lua","version":"' ..
      version .. '","product":"' .. product .. '"}'
    bmd.writestring(output .. "/lua-console-result.json", body)
end
