#!/usr/bin/env bash
# Diagnóstico experimental de Wine no Linux.
# NÃO instala, baixa, ativa ou executa o Adobe Premiere Pro.
set -uo pipefail

OUT_DIR="relatorios/premiere-linux"
if [ "$#" -ge 1 ]; then OUT_DIR="$1"; fi
mkdir -p "$OUT_DIR"
REPORT="$OUT_DIR/resultado.md"
LOG="$OUT_DIR/wine.log"
: > "$LOG"

line() { printf '%s\n' "$*" | tee -a "$REPORT"; }
status() {
  local label="$1" code="$2"
  if [ "$code" -eq 0 ]; then
    line "- ✅ $label: OK"
  else
    line "- ❌ $label: falhou (código $code)"
  fi
}

cat > "$REPORT" <<'EOF'
# Diagnóstico Wine / Linux — Premiere Pro

**Escopo:** verifica apenas se o Wine inicia e executa um comando Windows
em uma tela virtual no runner do GitHub. **NÃO testa o Adobe Premiere Pro.**
Não baixa instaladores, não ativa licenças, não acessa conta Adobe.

## Informações do ambiente
EOF

line "- Data UTC: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
line "- Sistema: $(uname -srm)"
line "- Memória RAM disponível (aprox.): $(free -h | awk '/^Mem:/ {print $7}')"
line "- Espaço livre em disco: $(df -h . | awk 'NR==2 {print $4}')"

if grep -qw avx2 /proc/cpuinfo; then
  line "- CPU com AVX2: sim"
else
  line "- CPU com AVX2: não detectado"
fi

if command -v glxinfo >/dev/null 2>&1; then
  renderer=$(timeout 12s xvfb-run -a glxinfo -B 2>>"$LOG" | grep 'OpenGL renderer string:' | head -n 1 || true)
  if [ -z "$renderer" ]; then renderer="não detectado"; fi
  line "- Renderizador OpenGL na tela virtual: $renderer"
fi

line ""
line "## Testes do Wine"

if ! command -v wine >/dev/null 2>&1; then
  line "- ❌ Wine: comando não encontrado"
  line ""
  line "**Conclusão:** ambiente Wine indisponível; Premiere não testado."
  exit 2
fi
line "- Versão Wine: $(wine --version 2>>"$LOG" || echo 'não identificada')"

if ! command -v xvfb-run >/dev/null 2>&1; then
  line "- ❌ Xvfb: comando xvfb-run não encontrado"
  line ""
  line "**Conclusão:** tela virtual indisponível; Premiere não testado."
  exit 2
fi

# Prefixo temporário isolado, removido ao final.
prefix=$(mktemp -d "/tmp/wine-premiere.XXXXXXXX")
export WINEPREFIX="$prefix"
export WINEARCH=win64
export WINEDEBUG=-all
# Evita pop-ups de componentes opcionais que o diagnóstico não necessita.
export WINEDLLOVERRIDES="mscoree,mshtml="
cleanup() {
  wineserver -k >>"$LOG" 2>&1 || true
  rm -rf -- "$prefix"
}
trap cleanup EXIT

timeout 120s xvfb-run -a wineboot -u >>"$LOG" 2>&1
boot_rc=$?
status "Criar prefixo Windows 64-bit com tela virtual" "$boot_rc"

if [ "$boot_rc" -ne 0 ]; then
  line ""
  line "**Conclusão:** Wine não iniciou corretamente neste runner. Premiere não testado."
  exit 1
fi

timeout 60s xvfb-run -a wine cmd /c ver >>"$LOG" 2>&1
cmd_rc=$?
status "Executar comando Windows no Wine" "$cmd_rc"

line ""
if [ "$cmd_rc" -eq 0 ]; then
  line "**Conclusão:** o ambiente básico do Wine funcionou. **Isto NÃO comprova compatibilidade com Premiere Pro**, nem instalação, GPU, login Adobe ou exportação de vídeo."
  exit 0
else
  line "**Conclusão:** o Wine não executou o comando de teste; Premiere não testado."
  exit 1
fi
