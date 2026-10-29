#!/usr/bin/env bash
# Diagnostico e tentativa explicita do DaVinci Resolve original 21.1.2 Linux.
# Executar no terminal de seu Codespace; nao colocar URL assinada nos commits.
set -euo pipefail
mode="${1:---check}"
case "$mode" in
  --check|--launch|--download-and-launch) ;;
  *) echo 'Uso: bash .devcontainer/davinci-codespaces/try-davinci.sh [--check|--launch|--download-and-launch]' >&2; exit 2;;
esac
base="${HOME}/.local/state/davinci-codespaces"
private="$base/resolve-21.1.2"
mkdir -p "$private"
chmod 700 "$base" "$private"
export DISPLAY="${DISPLAY:-:99}"
export XAUTHORITY="${XAUTHORITY:-$base/Xauthority}"
resolve="$private/squashfs-root/bin/resolve"
source_script="davinci-resolve/experiments/dvip/source.py"
log="$base/davinci-launch.log"

printf '=== DaVinci Resolve 21.1.2 ORIGINAL / Codespaces ===\n'
printf 'Ambiente: %s | Desktop: %s\n' "$(uname -s)" "$DISPLAY"
if [[ -d /dev/dri ]]; then
  ls /dev/dri/renderD* 2>/dev/null || true
else
  echo 'Sem /dev/dri (GPU de render fisica nao detectada).'
fi
if command -v nvidia-smi >/dev/null 2>&1; then nvidia-smi -L || true; fi
if command -v glxinfo >/dev/null 2>&1; then
  DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" glxinfo -B 2>/dev/null | grep -E 'OpenGL renderer|OpenGL vendor|OpenGL version' || true
fi
if [[ ! -x "$resolve" ]]; then
  echo 'DaVinci original 21.1.2 nao foi extraido neste Codespace.'
else
  echo 'Executavel 21.1.2 encontrado na pasta privada do Codespace.'
fi

if [[ "$mode" == '--check' ]]; then
  printf '\nProximo passo, opcional (baixar ZIP oficial de varios GiB e tentar iniciar):\n'
  echo 'bash .devcontainer/davinci-codespaces/try-davinci.sh --download-and-launch'
  echo 'Nao e garantido funcionar: Codespaces atual nao oferece GPU suportada.'
  exit 0
fi

if ! command -v xdpyinfo >/dev/null 2>&1 || ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
  echo 'Desktop X11 indisponivel: primeiro execute start-desktop.sh.' >&2
  exit 2
fi

if [[ "$mode" == '--download-and-launch' && ! -x "$resolve" ]]; then
  # O arquivo zip oficial ocupa varios gigabytes, e a extracao ainda mais.
  free_kib="$(df -Pk "$private" | awk 'NR==2 {print $4}')"
  if [[ ! "$free_kib" =~ ^[0-9]+$ ]] || (( free_kib < 15*1024*1024 )); then
    echo 'Espaco livre inferior a 15 GiB; download/extracao cancelados para evitar falta de disco.' >&2
    exit 2
  fi
  if [[ -z "${DAVINCI_RESOLVE_LINUX_URL:-}" ]]; then
    echo 'Cole sua URL oficial assinada 21.1.2 (entrada oculta; nao vai para o historico).'
    read -r -s -p 'URL: ' DAVINCI_RESOLVE_LINUX_URL
    printf '\n'
    export DAVINCI_RESOLVE_LINUX_URL
  fi
  if [[ -z "${DAVINCI_RESOLVE_LINUX_URL:-}" ]]; then
    echo 'URL nao fornecida; nada baixado.' >&2; exit 2
  fi
  printf 'Validando URL oficial sem iniciar download...\n'
  python3 "$source_script" availability --private-dir "$private" --report "$private/preflight.json"
  printf 'Baixando ZIP oficial somente para a pasta privada do Codespace...\n'
  python3 "$source_script" download --private-dir "$private" --report "$private/download.json"
  printf 'Extraindo executavel oficial 21.1.2 sem alterar os binarios...\n'
  python3 "$source_script" extract --private-dir "$private" --report "$private/extract.json"
  unset DAVINCI_RESOLVE_LINUX_URL
fi

if [[ ! -x "$resolve" ]]; then
  echo 'Resolve original nao encontrado para iniciar. Use --download-and-launch.' >&2
  exit 2
fi

printf '\nTentando iniciar DaVinci original na tela do Codespace...\n'
echo 'O Codespace nao tem GPU suportada garantida; abrir processo nao prova interface ou render.'
if pgrep -u "$(id -u)" -f 'squashfs-root/bin/resolve' >/dev/null 2>&1; then
  echo 'Um processo DaVinci ja parece estar ativo neste Codespace.'
  exit 0
fi
(
  cd "$private/squashfs-root"
  export LD_LIBRARY_PATH="$private/squashfs-root/libs:${LD_LIBRARY_PATH:-}"
  export QT_QPA_PLATFORM=xcb
  nohup "$resolve" > "$log" 2>&1 < /dev/null &
  echo $! > "$base/resolve-launch.pid"
)
sleep 12
pid="$(cat "$base/resolve-launch.pid")"
if kill -0 "$pid" 2>/dev/null; then
  echo 'Processo DaVinci iniciado; veja se aparece no desktop noVNC.'
  echo 'Isso NAO comprova GPU, edicao nem exportacao.'
else
  echo 'O processo DaVinci encerrou ou nao iniciou (possivel incompatibilidade com GPU/bibliotecas).'
  echo "Log de diagnostico LOCAL: $log"
  echo 'Nao envie URLs assinadas nem log com dados privados ao GitHub publico.'
  exit 2
fi
