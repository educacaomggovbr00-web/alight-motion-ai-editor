#!/usr/bin/env bash
# XFCE completo para Codespaces Ubuntu 24.04 com Xvfb ja iniciado.
# Sem privilegios especiais para apps; usa apt apenas durante instalacao.
set -euo pipefail
: "${DISPLAY:=:99}"
: "${XAUTHORITY:=$HOME/.local/state/davinci-codespaces/Xauthority}"
export DISPLAY XAUTHORITY
state="$HOME/.local/state/davinci-codespaces"
mkdir -p "$state"
chmod 700 "$state"
if ! command -v xdpyinfo >/dev/null 2>&1 || ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
  echo 'X11 nao disponivel; execute start-desktop.sh primeiro.' >&2
  exit 2
fi
packages=(
  xfce4 xfce4-terminal xfce4-whiskermenu-plugin xfce4-taskmanager
  dbus-x11 xfce4-notifyd thunar gvfs
  mousepad galculator ristretto xarchiver xfce4-screenshooter
  falkon adwaita-icon-theme fonts-dejavu-core
)
missing=()
for package in "${packages[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
    missing+=("$package")
  fi
done
if (( ${#missing[@]} > 0 )); then
  if ! command -v sudo >/dev/null 2>&1; then
    echo 'Precisa de sudo para instalar XFCE neste Codespace.' >&2
    exit 2
  fi
  echo "Instalando desktop XFCE e aplicativos (${#missing[@]} pacotes)..."
  sudo env DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "${missing[@]}"
fi

# Criar uma barra inferior de tela inteira com menu, janelas, relogio e desktop.
# Nao substituir configuracoes de usuario ja existentes.
panel_dir="$HOME/.config/xfce4/xfconf/xfce-perchannel-xml"
panel_config="$panel_dir/xfce4-panel.xml"
if [[ ! -s "$panel_config" ]]; then
  mkdir -p "$panel_dir"
  cat > "$panel_config" <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
  <property name="configver" type="int" value="2"/>
  <property name="panels" type="array">
    <value type="int" value="1"/>
    <property name="panel-1" type="empty">
      <property name="position" type="string" value="p=10;x=0;y=0"/>
      <property name="length" type="uint" value="100"/>
      <property name="size" type="uint" value="46"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="autohide-behavior" type="uint" value="0"/>
      <property name="plugin-ids" type="array">
        <value type="int" value="1"/>
        <value type="int" value="2"/>
        <value type="int" value="3"/>
        <value type="int" value="4"/>
        <value type="int" value="5"/>
        <value type="int" value="6"/>
        <value type="int" value="7"/>
      </property>
    </property>
  </property>
  <property name="plugins" type="empty">
    <property name="plugin-1" type="string" value="whiskermenu"/>
    <property name="plugin-2" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
    </property>
    <property name="plugin-3" type="string" value="tasklist"/>
    <property name="plugin-4" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
    </property>
    <property name="plugin-5" type="string" value="systray"/>
    <property name="plugin-6" type="string" value="clock"/>
    <property name="plugin-7" type="string" value="showdesktop"/>
  </property>
</channel>
XML
fi

if ! pgrep -u "$(id -u)" -x xfce4-session >/dev/null 2>&1; then
  # Openbox e o window manager anterior. Feche apenas o do proprio usuario.
  if pgrep -u "$(id -u)" -x openbox >/dev/null 2>&1; then
    pkill -u "$(id -u)" -x openbox || true
  fi
  # Evita composiçao OpenGL pesada em Codespaces sem GPU.
  export LIBGL_ALWAYS_SOFTWARE=1
  export NO_AT_BRIDGE=1
  nohup dbus-run-session -- xfce4-session > "$state/xfce-session.log" 2>&1 < /dev/null &
fi
for attempt in $(seq 1 20); do
  if pgrep -u "$(id -u)" -x xfce4-panel >/dev/null 2>&1 &&
     pgrep -u "$(id -u)" -x xfdesktop >/dev/null 2>&1; then
    echo 'XFCE iniciado: menu, barra inferior, area de trabalho e aplicativos.'
    exit 0
  fi
  sleep 1
done
# Tentativa de recuperacao sem apagar a configuracao XFCE.
echo 'Painel XFCE ainda nao respondeu. Consulte ~/.local/state/davinci-codespaces/xfce-session.log' >&2
exit 2
