#!/usr/bin/env python3
"""Opt-in research patch; does not advertise missing driver capabilities."""
import hashlib
import json
import sys
from pathlib import Path
p = Path(sys.argv[1]) / 'src/gallium/frontends/rusticl/core/device.rs'
original = p.read_bytes()
expected = 'a19c449b95586524b6b73e252fd42713c0250b7e4e43bc297fbbb8ef2b324530'
if hashlib.sha256(original).hexdigest() != expected:
    raise SystemExit('Blocked: expected unmodified Mesa 26.2.4 device.rs SHA-256.')
old = '&& !self.is_device_software()'
new = '''&& (!self.is_device_software()
                || std::env::var_os("CODEX_EXPERIMENTAL_SOFTWARE_GL_SHARING")
                    .as_deref() == Some(std::ffi::OsStr::new("1")))'''
s = original.decode()
if s.count(old) != 1:
    raise SystemExit('Blocked: unique software guard not found.')
loader = Path(sys.argv[1]) / 'src/gallium/frontends/rusticl/mesa/pipe/device.rs'
loader_raw = loader.read_bytes()
loader_expected = '8949ba583ef997b52019e32d4a4166536a02b909402a3e0e2abfbbe7866f0994'
if hashlib.sha256(loader_raw).hexdigest() != loader_expected:
    raise SystemExit('Blocked: expected unmodified Mesa 26.2.4 pipe device source.')
# Leave the loader untouched: forcing software_vulkan removed all devices.
function_old = """    pub fn is_gl_sharing_supported(&self) -> bool {
        self.screen.caps().cl_gl_sharing
            && self.screen.caps().dmabuf != 0
            && !self.is_device_software()
            && self.screen.is_res_handle_supported()
            && self.screen.device_uuid().is_some()
            && self.caps.has_create_fence_fd
    }"""
function_new = """    pub fn is_gl_sharing_supported(&self) -> bool {
        let experimental = std::env::var_os("CODEX_EXPERIMENTAL_SOFTWARE_GL_SHARING")
            .as_deref() == Some(std::ffi::OsStr::new("1"));
        let allowed = self.screen.caps().cl_gl_sharing
            && self.screen.caps().dmabuf != 0
            && (!self.is_device_software() || experimental)
            && self.screen.is_res_handle_supported()
            && self.screen.device_uuid().is_some()
            && self.caps.has_create_fence_fd;
        if experimental {
            eprintln!("CODEX_GL_CAPS gl_sharing={} dmabuf={} software={} handles={} uuid={} fence_fd={} allowed={}",
                self.screen.caps().cl_gl_sharing, self.screen.caps().dmabuf,
                self.is_device_software(), self.screen.is_res_handle_supported(),
                self.screen.device_uuid().is_some(), self.caps.has_create_fence_fd, allowed);
        }
        allowed
    }"""
if s.count(function_old) != 1:
    raise SystemExit('Blocked: expected unique GL sharing predicate.')
p.write_text(s.replace(function_old, function_new))
assert loader.read_bytes() == loader_raw
print(json.dumps({'state': 'experimental', 'sourceSha256': expected,
                  'patchedSha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                  'loaderSourceSha256': loader_expected,
                  'loaderPatchedSha256': hashlib.sha256(loader.read_bytes()).hexdigest(),
                  'softwareVulkanScreenOptIn': False, 'loaderUnmodified': True, 'softwareGuardOptIn': True, 'capabilitiesForged': False,
                  'resolveModified': False}))
