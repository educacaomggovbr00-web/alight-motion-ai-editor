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
loader_old = 'let s = unsafe { pipe_loader_create_screen(self.ldev.as_ptr(), false) };'
loader_new = '''let software_vulkan = self.device_type()
            == pipe_loader_device_type::PIPE_LOADER_DEVICE_SOFTWARE
            && env::var_os("CODEX_EXPERIMENTAL_SOFTWARE_GL_SHARING")
                .as_deref() == Some(std::ffi::OsStr::new("1"));
        let s = unsafe { pipe_loader_create_screen(self.ldev.as_ptr(), software_vulkan) };'''
loader_text = loader_raw.decode()
if loader_text.count(loader_old) != 1:
    raise SystemExit('Blocked: unique software screen loader not found.')
p.write_text(s.replace(old, new))
loader.write_text(loader_text.replace(loader_old, loader_new))
print(json.dumps({'state': 'experimental', 'sourceSha256': expected,
                  'patchedSha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                  'loaderSourceSha256': loader_expected,
                  'loaderPatchedSha256': hashlib.sha256(loader.read_bytes()).hexdigest(),
                  'softwareVulkanScreenOptIn': True, 'softwareGuardOptIn': True, 'capabilitiesForged': False,
                  'resolveModified': False}))
