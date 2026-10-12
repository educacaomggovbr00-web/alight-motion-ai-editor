-- Optional native Resolve 21.1.1 Lua smoke test. Executes INSIDE the official
-- Workspace > Console, never as an external Python/Studio API call.
-- A successful Lua report is not evidence of a native render: the supervisor
-- independently inspects the resulting MOV/MP4 with FFprobe before approving.
-- Only run on media explicitly supplied to the experimental workflow.

local function env(key)
    return os and os.getenv and os.getenv(key) or nil
end

local output = env("CODEX_RENDER_OUTPUT")
local media = env("CODEX_SYNTHETIC_VIDEO")
local width = tonumber(env("CODEX_WIDTH") or "")
local height = tonumber(env("CODEX_HEIGHT") or "")
local duration = tonumber(env("CODEX_DURATION") or "")
local result = {
    state = "blocked", invocationContext = "internal-lua-console",
    apiConnected = false, projectCreated = false, mediaImported = false,
    timelineCreated = false, effectApplied = false, exportProven = false,
    renderProducedFile = false, projectSaved = false,
    nativeFormat = "", nativeCodec = "", nativeFileName = "",
    reason = "not-started"
}

local function safe_string(value)
    local raw = tostring(value or "")
    return string.gsub(raw, '[^%w%s%._%-]', '_'):sub(1,120)
end

local function write_checkpoint(is_final)
    if not output or not bmd or type(bmd.writefile) ~= 'function' then return false end
    local function flag(name)
        return '"' .. name .. '":' .. (result[name] and "true" or "false")
    end
    local encoded = '{' ..
        flag("apiConnected") .. ',' ..
        flag("projectCreated") .. ',' ..
        flag("mediaImported") .. ',' ..
        flag("timelineCreated") .. ',' ..
        flag("effectApplied") .. ',' ..
        flag("exportProven") .. ',' ..
        flag("projectSaved") .. ',' ..
        flag("renderProducedFile") .. ',' ..
        '"state":"' .. safe_string(result.state) .. '",' ..
        '"invocationContext":"internal-lua-console",' ..
        '"nativeFormat":"' .. safe_string(result.nativeFormat) .. '",' ..
        '"nativeCodec":"' .. safe_string(result.nativeCodec) .. '",' ..
        '"nativeFileName":"' .. safe_string(result.nativeFileName) .. '",' ..
        '"reason":"' .. safe_string(result.reason) .. '",' ..
        '"renderStatus":{"JobStatus":"' .. safe_string(result.renderStatus or "") .. '"}' ..
        '}'
    local name = is_final and "sdk-result.json" or "sdk-progress.json"
    -- The Fusion writestring() API produces a serialized string, not a file.
    -- Write the bounded report to disk through the file API, checking its result.
    local ok, written = pcall(function()
        return bmd.writefile(output .. '/' .. name, encoded)
    end)
    return ok and written == true
end

local function fail(reason)
    result.reason = reason
    result.state = "blocked"
    write_checkpoint(true)
end

local function find_available_codec(project)
    local formats = project:GetRenderFormats() or {}
    local function format_present(ext)
        for k,v in pairs(formats) do
            if k == ext or v == ext then return true end
        end
        return false
    end
    -- Prefer the DNxHR path already validated by the existing pipeline,
    -- then the ProRes 422 path confirmed by independent Linux Free tests.
    -- Only accept codecs that the running application advertises.
    local wanted = {
        {"mov", "dnxhr", "lb"},
        {"mov", "prores", "422"},
        {"mp4", "h264", ""}
    }
    for _, spec in ipairs(wanted) do
        local ext, needle, detail = spec[1], spec[2], spec[3]
        if format_present(ext) then
            local codecs = project:GetRenderCodecs(ext) or {}
            for description, identifier in pairs(codecs) do
                local name = string.lower(tostring(description) .. " " .. tostring(identifier))
                local compact = string.gsub(name, "[^%w]", "")
                if string.find(compact, needle, 1, true) and
                   (detail == "" or string.find(compact, detail, 1, true)) then
                    if project:SetCurrentRenderFormatAndCodec(ext, identifier) then
                        return ext, identifier
                    end
                end
            end
        end
    end
    return nil, nil
end

local function exercise()
    if not output or not media or
       not ((width == 640 and height == 360) or
            (width == 540 and height == 960)) or
       not duration or duration < 1 or duration > 30 then
        fail("invalid-bounded-test-configuration")
        return
    end
    if not bmd or not bmd.writestring then
        result.reason = "bmd-writefile-unavailable"
        print("CODEX LUA: result transport unavailable")
        return
    end
    if not bmd.fileexists or not bmd.fileexists(media) then
        fail("input-not-found")
        return
    end

    local app = resolve
    if not app and bmd.scriptapp then app = bmd.scriptapp("Resolve") end
    if not app then fail("resolve-api-unavailable"); return end
    result.apiConnected = true
    result.reason = "api-connected"
    write_checkpoint(false)

    local version = app:GetVersion() or {}
    if version[1] ~= 21 or version[2] ~= 1 or version[3] ~= 1 then
        fail("unexpected-resolve-version")
        return
    end
    local manager = app:GetProjectManager()
    if not manager then fail("project-manager-unavailable"); return end
    local name = "Codex_Lua_Smoke_" .. tostring(os and os.time and os.time() or 0)
    local project = manager:CreateProject(name)
    if not project then fail("create-project-failed"); return end
    result.projectCreated = true
    result.reason = "project-created"
    write_checkpoint(false)

    local frame_rate = "30"
    if not project:SetSetting("timelineFrameRate", frame_rate) or
       not project:SetSetting("timelineResolutionWidth", tostring(width)) or
       not project:SetSetting("timelineResolutionHeight", tostring(height)) then
        fail("timeline-settings-rejected")
        return
    end
    local pool = project:GetMediaPool()
    if not pool then fail("media-pool-unavailable"); return end
    local clips = pool:ImportMedia({media})
    if not clips or not clips[1] then fail("import-media-failed"); return end
    result.mediaImported = true
    result.reason = "media-imported"
    write_checkpoint(false)

    local timeline = pool:CreateTimelineFromClips("Codex_Lua_Timeline", clips)
    if not timeline or not project:SetCurrentTimeline(timeline) then
        fail("timeline-creation-failed")
        return
    end
    result.timelineCreated = true
    result.reason = "timeline-created"
    write_checkpoint(false)

    -- A zoom is optional: it must be reported as applied only if verified.
    local items = timeline:GetItemListInTrack("video", 1) or {}
    if items[1] then
        local ok, changed = pcall(function()
            return items[1]:SetProperty("ZoomX", 1.06) and
                   items[1]:SetProperty("ZoomY", 1.06)
        end)
        if ok and changed then
            local properties = items[1]:GetProperty() or {}
            result.effectApplied =
                math.abs(tonumber(properties.ZoomX or 0) - 1.06) < 0.001 and
                math.abs(tonumber(properties.ZoomY or 0) - 1.06) < 0.001
        end
    end
    result.projectSaved = manager:SaveProject() == true
    write_checkpoint(false)

    local fmt, codec = find_available_codec(project)
    if not fmt then fail("no-advertised-supported-render-codec"); return end
    result.nativeFormat = fmt
    result.nativeCodec = tostring(codec)
    if not project:SetCurrentRenderMode(1) then
        fail("render-mode-rejected")
        return
    end
    local settings = {
        TargetDir = output, CustomName = "resolve-synthetic",
        SelectAllFrames = true, ExportVideo = true, ExportAudio = true,
        FormatWidth = width, FormatHeight = height, FrameRate = 30
    }
    if not project:SetRenderSettings(settings) then
        fail("render-settings-rejected")
        return
    end
    local job = project:AddRenderJob()
    if not job then fail("render-job-rejected"); return end
    if not bmd.wait or not os or not os.time then
        fail("bounded-wait-unavailable")
        return
    end
    write_checkpoint(false)
    if not project:StartRendering({job}) then
        fail("render-start-rejected")
        return
    end
    local deadline = os.time() + 150
    while project:IsRenderingInProgress() do
        if os.time() > deadline then
            project:StopRendering()
            fail("render-timeout")
            return
        end
        bmd.wait(1)
    end
    local status = project:GetRenderJobStatus(job) or {}
    result.renderStatus = status.JobStatus or "Unknown"
    if result.renderStatus ~= "Complete" then
        fail("render-not-complete")
        return
    end
    result.nativeFileName = "resolve-synthetic." .. fmt
    result.renderProducedFile = bmd.fileexists(output .. "/" .. result.nativeFileName) == true
    result.state = result.renderProducedFile and "reported" or "blocked"
    result.reason = result.renderProducedFile and "native-file-needs-ffprobe" or "render-file-missing"
    -- 'reported' is NOT 'proven': FFprobe and origin validation happen in supervise.py.
    write_checkpoint(true)
end

local ok = pcall(exercise)
if not ok then
    fail("lua-execution-error")
end
