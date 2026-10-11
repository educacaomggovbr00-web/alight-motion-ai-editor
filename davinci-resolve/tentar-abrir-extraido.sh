#!/usr/bin/env bash
# Tentativa experimental; não instala nem verifica capacidade de exportação.
set -euo pipefail
if [[ $# != 2 ]]; then
  echo "Uso: $0 PASTA_EXTRAIDA PASTA_PRIVADA_DE_RELATORIOS" >&2
  exit 2
fi
resolve_root=$(realpath "$1")
report_root=$(realpath -m "$2")
[[ -x "$resolve_root/bin/resolve" ]] || { echo "Executável real não encontrado." >&2; exit 2; }
script_root=$(dirname "$(realpath "$0")")
checkout_root=$(git -C "$script_root" rev-parse --show-toplevel 2>/dev/null || printf '%s\n' "$script_root")
case "$report_root/" in "$checkout_root/"*) echo "Salve os relatórios fora do repositório público." >&2; exit 2;; esac
for command_name in Xvfb timeout; do
  command -v "$command_name" >/dev/null || { echo "Dependência ausente: $command_name" >&2; exit 2; }
done
umask 077
mkdir -p "$report_root"
display_number_file="$report_root/display-number.txt"
: > "$display_number_file"
Xvfb -displayfd 3 -screen 0 1280x720x24 -nolisten tcp -ac 3>"$display_number_file" >"$report_root/xvfb.log" 2>&1 &
display_pid=$!
trap 'kill "$display_pid" 2>/dev/null || true' EXIT
for attempt in {1..50}; do
  [[ -s "$display_number_file" ]] && break
  kill -0 "$display_pid" 2>/dev/null || { echo "A tela virtual falhou." >&2; exit 3; }
  sleep 0.1
done
[[ -s "$display_number_file" ]] || { echo "Tempo esgotado ao preparar a tela." >&2; exit 3; }
export DISPLAY=":$(cat "$display_number_file")"
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=2 POCL_MAX_PTHREAD_COUNT=2
export LD_LIBRARY_PATH="$resolve_root/libs${DAVINCI_EXTRA_LIBS:+:$DAVINCI_EXTRA_LIBS}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
set +e
timeout --kill-after=5 65 "$resolve_root/bin/resolve" >"$report_root/resolve.log" 2>&1
launch_status=$?
set -e
printf '%s\n' "$launch_status" >"$report_root/process-exit.txt"
echo "Tentativa encerrada, código $launch_status. Revise a interface e os logs; isso não comprova edição."
exit "$launch_status"
