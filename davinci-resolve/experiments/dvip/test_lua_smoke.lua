-- Deterministic offline contract tests. No Resolve installation, private media or GPU.
-- Uses Lua 5.1 mocks to exercise the REAL canary and native edit scripts.
local root = "davinci-resolve/experiments/dvip/"
local real_getenv = os.getenv
local settings = {
    CODEX_RENDER_OUTPUT = "/safe-test-output",
    CODEX_SYNTHETIC_VIDEO = "/synthetic-fixture.mov",
    CODEX_WIDTH = "640", CODEX_HEIGHT = "360", CODEX_DURATION = "3"
}
os.getenv = function(key) return settings[key] end
local reports = {}
local state = {}
local function contains(text,pattern)
    return type(text) == "string" and string.find(text,pattern,1,true) ~= nil
end
local function report(name)
    return reports[settings.CODEX_RENDER_OUTPUT .. "/" .. name]
end
local function mock_resolve(mode)
    state = {renderStarted=false, importCalled=false, timelineCreated=false, codecLookups={}}
    local item = {
        SetProperty = function(self,key,value) self[key]=value return true end,
        GetProperty = function(self) return {ZoomX=self.ZoomX,ZoomY=self.ZoomY} end
    }
    local timeline = {
        GetItemListInTrack = function(self,kind,n)
            assert(kind=="video" and n==1)
            return {item}
        end
    }
    local pool = {
        ImportMedia=function(self,inputs)
            assert(inputs[1] == settings.CODEX_SYNTHETIC_VIDEO)
            state.importCalled=true
            return {{id=1}}
        end,
        CreateTimelineFromClips=function(self,name,clips)
            assert(state.importCalled and clips[1].id==1)
            state.timelineCreated=true
            return timeline
        end
    }
    local project = {
        SetSetting=function(self,k,v) return true end,
        GetMediaPool=function() return pool end,
        SetCurrentTimeline=function() return true end,
        GetRenderFormats=function()
            return {QuickTime="mov",MP4="mp4"}
        end,
        GetRenderCodecs=function(self,fmt)
            table.insert(state.codecLookups,fmt)
            -- API expects "mov", not the UI label "QuickTime".
            assert(fmt=="mov" or fmt=="mp4")
            if mode=="no-codec" then return {} end
            if fmt=="mov" then return {["DNxHR LB"]="DNxHR_LB"} end
            return {}
        end,
        SetCurrentRenderFormatAndCodec=function(self,fmt,codec)
            assert(fmt=="mov" and codec=="DNxHR_LB")
            return true
        end,
        SetCurrentRenderMode=function(self,mode) return mode==1 end,
        SetRenderSettings=function(self,r)
            assert(r.TargetDir==settings.CODEX_RENDER_OUTPUT)
            assert(r.CustomName=="resolve-synthetic")
            return true
        end,
        AddRenderJob=function() return "mock-job" end,
        StartRendering=function(self,jobs)
            assert(jobs[1]=="mock-job")
            state.renderStarted=true
            return true
        end,
        IsRenderingInProgress=function() return false end,
        GetRenderJobStatus=function() return {JobStatus="Complete"} end
    }
    local manager = {
        CreateProject=function(self,name)
            assert(contains(name,"Codex_Lua_Smoke_"))
            return project
        end,
        SaveProject=function() return true end
    }
    resolve = {
        GetVersion=function() return {21,1,1} end,
        GetProjectManager=function() return manager end,
        GetVersionString=function() return "21.1.1" end,
        GetProductName=function() return "DaVinci Resolve" end
    }
end
local function mock_bmd(writes_available,write_success)
    bmd = {
        fileexists=function(path)
            return path==settings.CODEX_SYNTHETIC_VIDEO or
                   (state.renderStarted and path==settings.CODEX_RENDER_OUTPUT.."/resolve-synthetic.mov")
        end,
        wait=function() end,
        scriptapp=function(name) if name=="Resolve" then return resolve end end
    }
    if writes_available then
        bmd.writefile=function(path,body)
            assert(type(path)=="string" and type(body)=="string")
            if write_success==false then return false end
            reports[path]=body
            return true
        end
    end
    -- Writestring intentionally exists as a trap. It must NEVER be called.
    bmd.writestring=function(...)
        error("writestring does not write files")
    end
end
local function reset(mode,writes_available,write_success)
    reports = {}
    mock_resolve(mode)
    mock_bmd(writes_available,write_success)
end

-- In-memory serializer does not accidentally produce false-positive results.
reset("normal",true,true)
dofile(root.."lua_probe.lua")
assert(contains(report("lua-console-result.json"),'"apiConnected":true'))
assert(contains(report("lua-console-result.json"),'"version":"21.1.1"'))

-- With a mocked 21.1.1 Resolve, verify each native API call is sequenced.
reset("normal",true,true)
dofile(root.."lua_edit_smoke.lua")
assert(state.importCalled and state.timelineCreated and state.renderStarted)
assert(contains(report("sdk-result.json"),'"renderProducedFile":true'))
assert(contains(report("sdk-result.json"),'"invocationContext":"internal-lua-console"'))
assert(not contains(report("sdk-result.json"),"nativeRenderProven"))
assert(state.codecLookups[1]=="mov")

-- Missing codecs must block rendering; a nonexistent file must not be invented.
reset("no-codec",true,true)
dofile(root.."lua_edit_smoke.lua")
assert(not state.renderStarted)
assert(contains(report("sdk-result.json"),'"reason":"no-advertised-supported-render-codec"'))
assert(not contains(report("sdk-result.json"),'"renderProducedFile":true'))

-- No file API: report must remain absent rather than falsely claiming success.
reset("normal",false,true)
dofile(root.."lua_probe.lua")
assert(report("lua-console-result.json")==nil)
dofile(root.."lua_edit_smoke.lua")
assert(not state.importCalled and report("sdk-result.json")==nil)

-- Disk API returns failure: pcall succeeding does NOT mean a report was written.
reset("normal",true,false)
dofile(root.."lua_probe.lua")
dofile(root.."lua_edit_smoke.lua")
assert(report("lua-console-result.json")==nil)
assert(report("sdk-result.json")==nil)

os.getenv = real_getenv
print("OK: Lua 5.1 offline probe, native timeline/render flow, codec fallback, missing writer and failed writer")
