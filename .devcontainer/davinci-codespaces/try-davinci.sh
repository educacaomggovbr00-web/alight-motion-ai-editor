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
# Instale Free e Studio em pastas separadas para nao misturar arquivos.
free_private="$base/resolve-21.1.2"
studio_private="$base/resolve-studio-21.1.2"
private="$free_private"
mkdir -p "$base"
chmod 700 "$base"
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
if [[ -x "$free_private/squashfs-root/bin/resolve" ]]; then
  echo 'DaVinci Resolve Free 21.1.2 encontrado.'
else
  echo 'DaVinci Resolve Free 21.1.2 ainda nao esta instalado.'
fi
if [[ -x "$studio_private/squashfs-root/bin/resolve" ]]; then
  echo 'DaVinci Resolve Studio 21.1.2 encontrado (uso exige licenca valida).'
else
  echo 'DaVinci Resolve Studio 21.1.2 ainda nao esta instalado.'
fi
if [[ "$mode" == '--launch' && -x "$studio_private/squashfs-root/bin/resolve" ]]; then
  private="$studio_private"
  resolve="$private/squashfs-root/bin/resolve"
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

if [[ "$mode" == '--download-and-launch' ]]; then
  if [[ -z "${DAVINCI_RESOLVE_LINUX_URL:-}" ]]; then
    echo 'Cole URL oficial assinada Free ou Studio 21.1.2 (entrada oculta; nao vai para historico).'
    read -r -s -p 'URL: ' DAVINCI_RESOLVE_LINUX_URL
    printf '\n'
    export DAVINCI_RESOLVE_LINUX_URL
  fi
  if [[ -z "${DAVINCI_RESOLVE_LINUX_URL:-}" ]]; then
    echo 'URL nao fornecida; nenhum download iniciado.' >&2
    exit 2
  fi

  # Identificar edicao SOMENTE pelo caminho, sem registrar assinatura/query.
  edition="$(python3 - <<'PY'
import os
from urllib.parse import urlsplit
path=urlsplit(os.environ.get('DAVINCI_RESOLVE_LINUX_URL','')).path
if path == '/DaVinciResolve/v21.1.2/DaVinci_Resolve_21.1.2_Linux.zip':
    print('free')
elif path == '/DaVinciResolve/v21.1.2/DaVinci_Resolve_Studio_21.1.2_Linux.zip':
    print('studio')
else:
    print('invalid')
PY
)"
  case "$edition" in
    free) private="$free_private" ;;
    studio)
      private="$studio_private"
      echo 'Edicao escolhida: DaVinci Resolve STUDIO (exige licenca legitima).'
      echo 'Nao sera feita qualquer ativacao ou contorno de licenca.'
      ;;
    *)
      echo 'Caminho do instalador nao e da edicao oficial Free/Studio 21.1.2.' >&2
      exit 2
      ;;
  esac
  resolve="$private/squashfs-root/bin/resolve"
  mkdir -p "$private"
  chmod 700 "$private"

  printf 'Validando host, caminho e validade da URL sem baixar...\n'
  python3 "$source_script" availability --private-dir "$private" --report "$private/preflight.json"

  if [[ ! -x "$resolve" ]]; then
    # O ZIP original ocupa varios gigabytes, e a extracao ainda mais.
    free_kib="$(df -Pk "$private" | awk 'NR==2 {print $4}')"
    if [[ ! "$free_kib" =~ ^[0-9]+$ ]] || (( free_kib < 15*1024*1024 )); then
      echo 'Menos de 15 GiB livres; operacao cancelada para evitar falta de disco.' >&2
      exit 2
    fi
    echo 'Baixando ZIP oficial e extraindo na pasta privada deste Codespace...'
    python3 "$source_script" download --private-dir "$private" --report "$private/download.json"
    python3 "$source_script" extract --private-dir "$private" --report "$private/extract.json"
  else
    echo 'Executavel da edicao selecionada ja existe; download adicional dispensado.'
  fi
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
