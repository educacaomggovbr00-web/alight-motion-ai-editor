#!/usr/bin/env bash
# Apenas em host Linux privado/dedicado. Não publicar porta 5901.
set -euo pipefail
root=$(realpath "${1:?Informe diretorio restaurado da VM}")
if [ ${#root} -gt 75 ]; then echo 'Caminho muito longo para sockets' >&2; exit 2; fi
if [[ "$root" == *','* || "$root" == *$'\n'* ]]; then echo 'Caminho recusado' >&2; exit 2; fi
python3 - "$root" <<'PY'
import shutil, sys
from pathlib import Path
root = Path(sys.argv[1])
if any(p.is_symlink() or (p / '.git').exists() for p in (root, *root.parents)):
    raise SystemExit('Use host privado fora do checkout')
ram = int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))
if ram < 10 * 1024**2 or shutil.disk_usage(root).free < 8 * 1024**3:
    raise SystemExit('Requer 10 GiB RAM disponivel e 8 GiB disco livre')
PY
for file in windows.qcow2 vars.fd tpm; do
  test -e "$root/$file" || { echo 'Estado disco/UEFI/TPM incompleto' >&2; exit 2; }
done
firmware=/usr/share/OVMF/OVMF_CODE_4M.ms.fd
test -f "$firmware"
# qemu-img respeita locks de disco; não use force-share.
qemu-img check -f qcow2 "$root/windows.qcow2"
accel=tcg,thread=multi
cpu=max
if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then accel=kvm; cpu=host; fi
tpm_pid=''
cleanup() { if [ -n "$tpm_pid" ]; then kill "$tpm_pid" 2>/dev/null || true; wait "$tpm_pid" 2>/dev/null || true; fi; }
trap cleanup EXIT
# VM existente deve estar completamente desligada; socket ativo bloqueia swtpm.
swtpm socket --tpm2 --tpmstate "dir=$root/tpm" \
  --ctrl "type=unixio,path=$root/tpm.sock" --flags not-need-init,startup-clear &
tpm_pid=$!
for attempt in {1..50}; do
  kill -0 "$tpm_pid" || exit 2
  if [ -S "$root/tpm.sock" ]; then break; fi
  sleep 0.1
done
qemu-system-x86_64 -machine q35,smm=on -accel "$accel" -cpu "$cpu" -smp 2 -m 8192 \
  -global driver=cfi.pflash01,property=secure,value=on \
  -drive "if=pflash,format=raw,readonly=on,file=$firmware" \
  -drive "if=pflash,format=raw,file=$root/vars.fd" \
  -drive "file=$root/windows.qcow2,format=qcow2,if=ide,index=0" \
  -chardev "socket,id=chrtpm,path=$root/tpm.sock" \
  -tpmdev emulator,id=tpm0,chardev=chrtpm -device tpm-tis,tpmdev=tpm0 \
  -boot order=c -nic user,model=e1000 -vga std -display none -vnc 127.0.0.1:1
# Não anexa ISO/Autounattend: nunca formata de novo o disco restaurado.
