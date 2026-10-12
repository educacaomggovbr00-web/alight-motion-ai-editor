-- Diagnostic only. Runs via the official Lua Console; no editing, network or license changes.
local output = os and os.getenv and os.getenv("CODEX_RENDER_OUTPUT")
local app = resolve
if not app and bmd and bmd.scriptapp then
    app = bmd.scriptapp("Resolve")
end
if output and bmd and type(bmd.writefile) == 'function' then
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
    -- writestring(table) serializes in memory; writefile(path, contents) writes to disk.
    -- A failed or unavailable file transport must NOT be reported as API success.
    local ok, written = pcall(function()
        return bmd.writefile(output .. "/lua-console-result.json", body)
    end)
    if not ok or written ~= true then
        print("CODEX LUA: unable to persist read-only API probe")
    end
end
