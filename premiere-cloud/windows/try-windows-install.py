"""Tentativa local limitada; disco esparso não garante capacidade física."""
import argparse
import json
import shutil
import signal
import subprocess
import time
from pathlib import Path


def main():
    def stop(_signal, _frame):
        raise KeyboardInterrupt('Encerramento solicitado')
    signal.signal(signal.SIGTERM, stop)
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('qemu', 'swtpm', 'iso', 'firmware', 'vars-template', 'roms', 'destination'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--resume', action='store_true', help='Retomar somente o disco desta tentativa, sem recriar')
    a = p.parse_args()
    for item in (a.qemu, a.swtpm, a.iso, a.firmware, a.vars_template):
        if not item.is_file():
            p.error('Arquivo necessário ausente')
    root = a.destination.resolve()
    if len(str(root)) > 75 or (root.exists() and not a.resume):
        p.error('Destino deve ser novo e ter caminho curto; para retomar use --resume')
    if a.resume:
        if not (root / 'attempt.json').is_file() or not (root / 'vars.fd').is_file() or not (root / 'tpm').is_dir():
            p.error('Estado da tentativa anterior ausente; nada foi alterado')
        if not (root / 'windows.raw').is_file() or (root / 'windows.raw').stat().st_size != 100 * 1024**3:
            p.error('Disco anterior invalido; nada foi alterado')
    else:
        root.mkdir(mode=0o700, parents=True)
    reserve = 4 * 1024**3
    if shutil.disk_usage(root).free < reserve + 1024**3:
        p.error('Espaço físico insuficiente até para tentativa')
    disk = root / 'windows.raw'
    if not a.resume:
        with disk.open('xb') as f:
            f.truncate(100 * 1024**3)
        shutil.copyfile(a.vars_template, root / 'vars.fd')
        (root / 'tpm').mkdir(mode=0o700)
    tpm = vm = None
    reason = 'nao_iniciado'
    started = time.monotonic()
    try:
        with (root / 'tpm.log').open('wb') as tpm_log, (root / 'qemu.log').open('wb') as vm_log:
            tpm = subprocess.Popen([str(a.swtpm), 'socket', '--tpm2', '--tpmstate',
                f'dir={root / "tpm"}', '--ctrl', f'type=unixio,path={root / "tpm.sock"}',
                '--flags', 'not-need-init,startup-clear'], stdout=tpm_log, stderr=tpm_log)
            for _ in range(50):
                if (root / 'tpm.sock').exists():
                    break
                if tpm.poll() is not None:
                    raise RuntimeError('TPM não iniciou; consultar log privado')
                time.sleep(.1)
            else:
                raise RuntimeError('Timeout aguardando TPM')
            vm = subprocess.Popen([str(a.qemu), '-L', str(a.roms),
                '-machine', 'q35,smm=on', '-accel', 'tcg,thread=multi',
                '-cpu', 'max', '-smp', '2', '-m', '6144',
                '-global', 'driver=cfi.pflash01,property=secure,value=on',
                '-drive', f'if=pflash,format=raw,readonly=on,file={a.firmware}',
                '-drive', f'if=pflash,format=raw,file={root / "vars.fd"}',
                '-drive', f'file={disk},format=raw,if=ide',
                '-chardev', f'socket,id=chrtpm,path={root / "tpm.sock"}',
                '-tpmdev', 'emulator,id=tpm0,chardev=chrtpm',
                '-device', 'tpm-tis,tpmdev=tpm0',
                '-cdrom', str(a.iso), '-boot', 'c' if a.resume else 'd', '-nic', 'none',
                '-display', 'none', '-vga', 'std', '-qmp',
                f'unix:{root / "qmp.sock"},server=on,wait=off', '-no-reboot'],
                stdout=vm_log, stderr=vm_log)
            reason = 'processo_encerrado'
            while vm.poll() is None:
                if shutil.disk_usage(root).free < reserve:
                    reason = 'reserva_fisica_4GiB'; break
                if time.monotonic() - started >= 600:
                    reason = 'limite_600s'; break
                time.sleep(1)
    except KeyboardInterrupt:
        reason = 'interrompido'
    finally:
        for process in (vm, tpm):
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
        report = dict(state='experimental', reason=reason,
            durationSeconds=round(time.monotonic() - started),
            freePhysicalBytes=shutil.disk_usage(root).free,
            diskVirtualBytes=disk.stat().st_size,
            diskAllocatedBytes=disk.stat().st_blocks * 512,
            qemuExit=vm.returncode if vm else None,
            windowsInstalledProven=False, warpInWindows11Proven=False,
            premiereInstalledProven=False)
        (root / 'attempt.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
