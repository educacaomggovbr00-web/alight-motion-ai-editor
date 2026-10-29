#!/usr/bin/env bash
# Diagnostico; nao comprova DaVinci funcional.
set -euo pipefail
printf '=== Sistema ===\n'; uname -a
printf '\n=== GPU fisica ===\n'
if [[ -d /dev/dri ]]; then ls -la /dev/dri; else echo 'Nenhum /dev/dri'; fi
printf '\n=== OpenCL ===\n'; clinfo -l || true
printf '\n=== OpenGL (DISPLAY=:99) ===\n'; DISPLAY=:99 glxinfo -B 2>&1 || true
printf '\n=== DaVinci Resolve original ===\n'
if [[ -x /opt/resolve/bin/resolve ]]; then
  echo 'Resolve encontrado; GPU, interface e exportacao ainda nao verificados.'
else
  echo 'Resolve ausente: instalador nao e baixado automaticamente.'
fi
echo 'GPU Codespaces foram descontinuadas em 2025. Mesa/llvmpipe nao substitui GPU.'
