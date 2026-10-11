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
p.write_text(s.replace(old, new))
print(json.dumps({'state': 'experimental', 'sourceSha256': expected,
                  'patchedSha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                  'softwareGuardOptIn': True, 'capabilitiesForged': False,
                  'resolveModified': False}))
