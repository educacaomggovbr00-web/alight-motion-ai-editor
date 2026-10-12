-- Diagnostic only. Runs via the official Lua Console; no editing, network or license changes.
local output = os and os.getenv and os.getenv("CODEX_RENDER_OUTPUT")
-- Write machine-readable JSON only to the explicitly configured output directory.
-- Fusion's bmd.writefile serializes Lua tables, so prefer Lua's normal text I/O.
local function persist_json(path, body)
    if io and type(io.open) == "function" then
        local ok, success = pcall(function()
            local file = io.open(path, "wb")
            if not file then return false end
            local written = file:write(body) ~= nil
            local closed = file:close()
            return written and closed ~= nil
        end)
        if ok and success then return true end
    end
    if bmd and type(bmd.writefile) == "function" then
        local ok, success = pcall(function() return bmd.writefile(path, body) end)
        return ok and success == true
    end
    return false
end

local app = resolve
if not app and bmd and bmd.scriptapp then
    app = bmd.scriptapp("Resolve")
end
if output then
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
    if not persist_json(output .. "/lua-console-result.json", body) then
        print("CODEX LUA: unable to persist read-only API probe")
    end
end
