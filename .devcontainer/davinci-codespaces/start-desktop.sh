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
if ! ss -lnt 2>/dev/null | grep -q ':5900 '; then
  nohup x11vnc -display "$DISPLAY" -auth "$XAUTHORITY" \
    -localhost -nopw -forever -shared -rfbport 5900 \
    > "$workdir/x11vnc.log" 2>&1 < /dev/null &
fi
if ! ss -lnt 2>/dev/null | grep -q ':6080 '; then
  nohup websockify --web=/usr/share/novnc 127.0.0.1:6080 127.0.0.1:5900 \
    > "$workdir/novnc.log" 2>&1 < /dev/null &
fi
sleep 2
if ! curl --silent --fail --output /dev/null http://127.0.0.1:6080/vnc.html; then
  echo 'noVNC nao respondeu; consulte ~/.local/state/davinci-codespaces/novnc.log' >&2
  exit 2
fi
printf '\nDesktop Linux iniciado na porta 6080.\n'
printf 'Abra PORTS -> 6080 -> Open in Browser -> vnc.html -> Connect.\n'
printf 'Port Visibility deve ser PRIVATE. Nao existe GPU fisica no Codespace.\n'
