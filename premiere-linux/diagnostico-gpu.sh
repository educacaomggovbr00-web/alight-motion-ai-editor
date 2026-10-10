#!/usr/bin/env bash
# Testa recursos gráficos do Linux e APIs Windows básicas com Wine.
# NÃO instala nem executa o Premiere e não garante compatibilidade com ele.
set -uo pipefail

OUT="relatorios/premiere-gpu"
mkdir -p "$OUT"
REPORT="$OUT/resultado.md"
VULKAN_LOG="$OUT/vulkan.txt"
D3D_LOG="$OUT/directx11.txt"
WINE_LOG="$OUT/wine-erros.txt"
: > "$WINE_LOG"
{
  printf '# Diagnóstico gráfico Wine para Premiere\n\n'
  printf 'O script testa OpenGL, Vulkan, Direct3D 11 e adaptadores DXGI, não o Premiere Pro.\n\n'
  printf -- '- Data UTC: %s\n' "$(date -u '+%Y-%m-%d %H:%M UTC')"
  printf -- '- Sistema: %s\n' "$(uname -srm)"
  printf -- '- Wine: %s\n' "$(wine --version 2>&1)"
  printf -- '- Arquitetura: %s\n' "$(uname -m)"
  if grep -qw avx2 /proc/cpuinfo; then
    printf -- '- AVX2: detectado\n'
  else
    printf -- '- AVX2: não detectado\n'
  fi
  printf '\n## OpenGL\n\n'
  OPENGL=$(timeout 15s xvfb-run -a -s '-screen 0 1920x1080x24' glxinfo -B 2>&1)
  printf '%s\n' "$OPENGL" | grep -E 'OpenGL vendor string:|OpenGL renderer string:|OpenGL core profile version string:' || true
  if printf '%s' "$OPENGL" | grep -Eiq 'llvmpipe|softpipe|swrast'; then
    printf '\n**Observação:** renderização OpenGL por SOFTWARE; não é uma GPU dedicada com VRAM.\n'
  fi
  printf '\n## Vulkan\n\n'
  if timeout 25s vulkaninfo --summary > "$VULKAN_LOG" 2>&1; then
    grep -E 'deviceName[[:space:]]*=|deviceType[[:space:]]*=|apiVersion[[:space:]]*=' "$VULKAN_LOG" | head -n 24 || true
  else
    printf 'vulkaninfo falhou; consulte vulkan.txt.\n'
  fi
  if grep -Eiq 'llvmpipe|lavapipe|CPU' "$VULKAN_LOG"; then
    printf '\n**Observação:** Vulkan encontrado pode ser implementado por SOFTWARE (CPU).\n'
  fi
  printf '\n## Direct3D 11 / DXGI via Wine\n\n'
} > "$REPORT"

export WINEDEBUG="-all"
export WINEARCH="win64"
export WINEDLLOVERRIDES="mscoree,mshtml="
export WINEPREFIX
WINEPREFIX=$(mktemp -d "/tmp/premiere-gpu-wine.XXXXXXXX")
cleanup() {
  wineserver -k >> "$WINE_LOG" 2>&1 || true
  rm -rf -- "$WINEPREFIX"
}
trap cleanup EXIT

if ! timeout 120s xvfb-run -a -s '-screen 0 1920x1080x24' wineboot -u >> "$WINE_LOG" 2>&1; then
  printf 'Não foi possível iniciar o Wine; veja wine-erros.txt.\n' | tee -a "$REPORT"
  exit 1
fi

# Exe compilado de código aberto no workflow, não é código ou instalador da Adobe.
set +e
timeout 90s xvfb-run -a -s '-screen 0 1920x1080x24' wine premiere-linux/windows/d3d11_probe.exe > "$D3D_LOG" 2>> "$WINE_LOG"
RESULT=$?
set -e
{
  printf -- '- Código de saída do teste D3D11: %s\n' "$RESULT"
  grep -E 'DXGI\.|D3D11\.' "$D3D_LOG" | head -n 50 || true
  printf '\n## Comparação com requisitos do Premiere Pro\n\n'
  printf -- '- Requisitos oficiais em 2026: Windows 11 v24H2 e GPU compatível com pelo menos 4 GB de memória gráfica.\n'
  printf -- '- Wine não equivale a um Windows 11 real e a renderização por CPU não equivale a GPU dedicada.\n'
  printf -- '- DXGI pode relatar valores emulados: NÃO os interprete como VRAM física garantida.\n'
  printf -- '- Um resultado positivo em D3D11 não prova recursos DirectX 12, Creative Cloud, login, codecs ou exportação.\n'
  printf -- '- Nenhum instalador da Adobe foi executado.\n'
} >> "$REPORT"

# Se a API falhar, isso é um RESULTADO válido do diagnóstico, não um erro do próprio script.
exit 0
