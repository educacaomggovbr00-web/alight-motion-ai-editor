#!/usr/bin/env bash
# Uso: bash .devcontainer/davinci-codespaces/start-desktop.sh
# MANTENHA A PORTA 6080 PRIVATE no Codespaces.
set -euo pipefail

# Codespaces criados ANTES da configuracao costumam usar a imagem padrao.
# Instalar dependencias somente quando o usuario executar este script.
packages=(xvfb openbox xterm x11vnc novnc websockify xauth openssl x11-utils iproute2 curl)
commands=(Xvfb openbox xterm x11vnc websockify xauth openssl xdpyinfo ss curl)
need_install=false
for item in "${commands[@]}"; do
  if ! command -v "$item" >/dev/null 2>&1; then
    need_install=true
    break
  fi
done
if [[ ! -f /usr/share/novnc/vnc.html ]]; then need_install=true; fi
if [[ "$need_install" == true ]]; then
  echo 'Instalando desktop Linux (Xvfb/noVNC) na imagem padrao deste Codespace...'
  if ! command -v sudo >/dev/null 2>&1; then
    echo 'sudo ausente; recrie o Codespace com a configuracao DaVinci Linux.' >&2
    exit 2
  fi
  sudo env DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "${packages[@]}"
fi
export DISPLAY=:99
workdir="${HOME}/.local/state/davinci-codespaces"
mkdir -p "$workdir"
chmod 700 "$workdir"
export XAUTHORITY="$workdir/Xauthority"
if [[ ! -f "$XAUTHORITY" ]]; then
  touch "$XAUTHORITY"
  chmod 600 "$XAUTHORITY"
  xauth -f "$XAUTHORITY" add "$DISPLAY" . "$(openssl rand -hex 16)"
fi
if ! pgrep -u "$(id -u)" -f '^Xvfb :99 ' >/dev/null 2>&1; then
  nohup Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp -auth "$XAUTHORITY" \
    > "$workdir/xvfb.log" 2>&1 < /dev/null &
fi
for attempt in $(seq 1 30); do
  if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then break; fi
  sleep 1
done
if ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
  echo 'Xvfb nao iniciou; consulte ~/.local/state/davinci-codespaces/xvfb.log' >&2
  exit 2
fi
if ! pgrep -u "$(id -u)" -x openbox >/dev/null 2>&1; then
  nohup openbox > "$workdir/openbox.log" 2>&1 < /dev/null &
fi
if ! pgrep -u "$(id -u)" -x xterm >/dev/null 2>&1; then
  nohup xterm -display "$DISPLAY" -geometry 110x32+40+40 \
    -title 'Codespaces: Linux experimental sem GPU' \
    > "$workdir/xterm.log" 2>&1 < /dev/null &
fi
# VNC exige autenticacao extra, alem do login GitHub da porta PRIVADA.
# Protocolo VNC classico aceita apenas os primeiros oito caracteres de senha.
passfile="$workdir/vnc-password.txt"
authfile="$workdir/vnc-rfbauth"
if [[ ! -s "$passfile" || ! -s "$authfile" ]]; then
  umask 077
  python3 - "$passfile" <<'PY'
import secrets, sys
from pathlib import Path
alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
Path(sys.argv[1]).write_text(''.join(secrets.choice(alphabet) for _ in range(8)) + '\n')
PY
  chmod 600 "$passfile"
  vnc_password="$(cat "$passfile")"
  # A opcao documentada aceita senha e arquivo; stdout fica oculto.
  # A senha nao e adicionada ao historico nem a arquivos do repositorio.
  x11vnc -storepasswd "$vnc_password" "$authfile" >/dev/null 2>&1
  chmod 600 "$authfile"
  unset vnc_password
fi
# A versao anterior executava VNC sem senha. Reinicie o VNC do usuario.
if pgrep -u "$(id -u)" -x x11vnc >/dev/null 2>&1; then
  pkill -u "$(id -u)" -x x11vnc || true
  sleep 1
fi
nohup x11vnc -display "$DISPLAY" -auth "$XAUTHORITY" \
  -localhost -rfbauth "$authfile" -forever -shared -rfbport 5900 \
  > "$workdir/x11vnc.log" 2>&1 < /dev/null &

if ! ss -lnt 2>/dev/null | grep -q ':6080 '; then
  nohup websockify --web=/usr/share/novnc 127.0.0.1:6080 127.0.0.1:5900 \
    > "$workdir/novnc.log" 2>&1 < /dev/null &
fi
sleep 2
if ! curl --silent --fail --output /dev/null http://127.0.0.1:6080/vnc.html; then
  echo 'noVNC nao respondeu; consulte ~/.local/state/davinci-codespaces/novnc.log' >&2
  exit 2
fi
if ! ss -lnt | grep -q ':5900 '; then
  echo 'VNC nao iniciou; veja o log privado no seu Codespace.' >&2
  exit 2
fi
printf '\n==============================================\n'
printf 'DESKTOP LINUX DO CODESPACE - NO VNC\n'
if [[ -n "${CODESPACE_NAME:-}" && -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
  printf 'LINK: https://%s-6080.%s/vnc.html\n' "$CODESPACE_NAME" "$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"
else
  printf 'LINK: abra a porta 6080 em PORTS e adicione /vnc.html\n'
fi
printf 'SENHA VNC: %s\n' "$(cat "$passfile")"
printf 'IMPORTANTE: mantenha a porta PRIVATE e nao compartilhe a senha.\n'
printf 'Para tentar o DaVinci 21.1.2 original, execute:\n'
printf 'bash .devcontainer/davinci-codespaces/try-davinci.sh\n'
printf '==============================================\n'
