#!/usr/bin/env bash
# Boot somente: nao instala Windows, nao modifica ISO nem cria disco de sistema.
set -euo pipefail
if [[ $# != 5 ]]; then
  echo 'Uso: bash boot-windows-iso.sh QEMU ISO OVMF_CODE DIRETORIO_ROM DIRETORIO_PRIVADO_NOVO' >&2
  exit 2
fi
qemu_bin=$1; iso_path=$2; firmware_path=$3; rom_dir=$4; output_dir=$5
for path in "$qemu_bin" "$iso_path" "$firmware_path"; do
  [[ -f "$path" ]] || { echo 'Arquivo necessario ausente' >&2; exit 2; }
done
[[ ! -e "$output_dir" ]] || { echo 'Destino deve ser novo' >&2; exit 2; }
umask 077
mkdir -p "$output_dir"
output_dir=$(cd "$output_dir" && pwd)
if [[ ${#output_dir} -gt 85 ]]; then echo 'Caminho longo demais para socket QMP' >&2; exit 2; fi
set +e
timeout --kill-after=5s 180s "$qemu_bin" -L "$rom_dir" \
  -machine q35 -accel tcg,thread=multi -cpu max -smp 2 -m 4096 \
  -drive "if=pflash,format=raw,readonly=on,file=$firmware_path" \
  -cdrom "$iso_path" -boot d -nic none -display none -vga std \
  -qmp "unix:$output_dir/qmp.sock,server=on,wait=off" -no-reboot \
  > "$output_dir/qemu.log" 2>&1
boot_exit=$?
set -e
echo "QEMU finalizado: codigo $boot_exit. Nao comprova Windows ou Premiere instalados."
if [[ $boot_exit != 0 && $boot_exit != 124 ]]; then exit "$boot_exit"; fi
