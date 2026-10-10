"""VM Windows 11 nova: instalação oficial, TPM, evidência serial e limites."""
import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import time
from pathlib import Path

ISO_SHA256 = '29bd7592e832d32073d1637ce83689de5f375700a963b2d753e437cc64d76c09'
GIB = 1024**3


class GuestProbeError(RuntimeError):
    def __init__(self, first):
        super().__init__('Probe Windows falhou; WARP nao confirmado')
        self.first = first


def qmp(root, command, arguments=None):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(5)
        s.connect(str(root / 'qmp.sock'))
        with s.makefile('rwb') as stream:
            json.loads(stream.readline())
            for packet in ({'execute': 'qmp_capabilities'},
                           {'execute': command, 'arguments': arguments or {}}):
                stream.write((json.dumps(packet) + '\n').encode()); stream.flush()
                while True:
                    line = stream.readline()
                    if not line:
                        raise RuntimeError('QMP desconectado')
                    reply = json.loads(line)
                    if 'error' in reply:
                        raise RuntimeError('Comando QMP recusado')
                    if 'return' in reply:
                        break
            return reply['return']


def parse_evidence(serial):
    first = warp = None
    guest_error = False
    for line in serial.splitlines():
        prefix, _, payload = line.partition(' ')
        if prefix not in ('CODEX_WINDOWS11_FIRST_BOOT', 'CODEX_WINDOWS11_WARP_OK', 'CODEX_GUEST_ERROR'):
            continue
        try:
            data = json.loads(payload)
        except (ValueError, TypeError):
            continue
        if not isinstance(data, dict):
            continue
        if prefix == 'CODEX_GUEST_ERROR':
            guest_error = True
        if prefix == 'CODEX_WINDOWS11_FIRST_BOOT' and data.get('windows11') is True and data.get('phase') == 'specialize':
            first = data
        if (prefix == 'CODEX_WINDOWS11_WARP_OK' and data.get('windows11') is True
                and data.get('state') == 'testado' and data.get('renderer') == 'WARP_CPU'
                and data.get('featureLevel') == '0xb000'
                and data.get('scope') == 'criacao_dispositivo_Direct3D11_WARP_apenas'):
            warp = data
    if guest_error:
        raise GuestProbeError(first)
    return first, warp


def stop_process(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait()


def run(iso, root, reports):
    report = dict(state='nao_iniciado', windowsImageBootedProven=False,
                  windowsSetupCompletedProven=False, desktopConfirmed=False,
                  warpInWindows11Proven=False, premiereInstalledProven=False)
    vm = tpm = None
    started = time.monotonic()
    try:
        if root.exists() or len(str(root)) > 75:
            raise RuntimeError('Destino deve ser novo e curto; nenhum disco existente sera usado')
        if shutil.disk_usage(root.parent).free < 38*GIB:
            raise RuntimeError('Menos de38GiB fisicos livres depois do download')
        mem_kib = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))
        if mem_kib < 10*1024**2:
            raise RuntimeError('RAM disponivel menor que10GiB; nao iniciar VM8GiB')
        h = hashlib.sha256()
        with iso.open('rb') as f:
            while chunk := f.read(8*1024**2):
                h.update(chunk)
        if h.hexdigest() != ISO_SHA256:
            raise RuntimeError('SHA256 Microsoft nao confere; ISO recusada')
        report['isoSha256'] = h.hexdigest()
        root.mkdir(mode=0o700)
        media = root / 'answer-files'; media.mkdir()
        source = Path(__file__).resolve().parent
        for name in ('Autounattend.xml', 'codex-probe.ps1', 'test-warp.ps1'):
            shutil.copyfile(source / name, media / name)
        subprocess.run(['xorriso', '-as', 'mkisofs', '-quiet', '-J', '-R', '-V', 'CODEX_SETUP',
                        '-o', str(root / 'answers.iso'), str(media)], check=True, capture_output=True)
        subprocess.run(['qemu-img', 'create', '-f', 'qcow2', str(root / 'windows.qcow2'), '80G'], check=True)
        firmware = Path('/usr/share/OVMF/OVMF_CODE_4M.ms.fd')
        variables = Path('/usr/share/OVMF/OVMF_VARS_4M.ms.fd')
        if not firmware.is_file() or not variables.is_file():
            raise RuntimeError('Firmware UEFI Microsoft ausente; nao substituir por bypass')
        shutil.copyfile(variables, root / 'vars.fd')
        (root / 'tpm').mkdir()
        tpm_log = (root / 'tpm.log').open('wb')
        tpm = subprocess.Popen(['swtpm', 'socket', '--tpm2', '--tpmstate', f'dir={root / "tpm"}',
                                '--ctrl', f'type=unixio,path={root / "tpm.sock"}',
                                '--flags', 'not-need-init,startup-clear'], stdout=tpm_log, stderr=tpm_log)
        for _ in range(100):
            if (root / 'tpm.sock').exists():
                break
            if tpm.poll() is not None:
                raise RuntimeError('TPM falhou ao iniciar')
            time.sleep(.1)
        else:
            raise RuntimeError('TPM nao respondeu')
        kvm = os.access('/dev/kvm', os.R_OK | os.W_OK)
        report.update(state='experimental', acceleration='kvm' if kvm else 'tcg', vmRamGiB=8, vmDiskVirtualGiB=80)
        vm_log = (reports / 'qemu.log').open('wb')
        vm = subprocess.Popen(['qemu-system-x86_64', '-machine', 'q35,smm=on',
            '-accel', 'kvm' if kvm else 'tcg,thread=multi', '-cpu', 'host' if kvm else 'max',
            '-smp', '2', '-m', '8192', '-global', 'driver=cfi.pflash01,property=secure,value=on',
            '-drive', f'if=pflash,format=raw,readonly=on,file={firmware}',
            '-drive', f'if=pflash,format=raw,file={root / "vars.fd"}',
            '-drive', f'file={root / "windows.qcow2"},format=qcow2,if=ide,index=0',
            '-drive', f'file={iso},media=cdrom,readonly=on,if=ide,index=2',
            '-drive', f'file={root / "answers.iso"},media=cdrom,readonly=on,if=ide,index=3',
            '-chardev', f'socket,id=chrtpm,path={root / "tpm.sock"}',
            '-tpmdev', 'emulator,id=tpm0,chardev=chrtpm', '-device', 'tpm-tis,tpmdev=tpm0',
            '-boot', 'order=c,once=d', '-nic', 'none', '-display', 'none', '-vga', 'std',
            '-serial', f'file:{root / "serial.txt"}', '-qmp',
            f'unix:{root / "qmp.sock"},server=on,wait=off'], stdout=vm_log, stderr=vm_log)
        boot_key_sent = False
        next_snapshot = 0
        report['reason'] = 'processo_encerrado_sem_evidencia'
        while vm.poll() is None:
            elapsed = time.monotonic() - started
            if shutil.disk_usage(root).free < 8*GIB:
                report['reason'] = 'reserva_fisica_8GiB'; break
            if elapsed >= 2700:
                report['reason'] = 'limite_45min'; break
            serial_path = root / 'serial.txt'
            first, warp = parse_evidence(serial_path.read_text(errors='replace') if serial_path.exists() else '')
            if first:
                report['windowsImageBootedProven'] = True
                (reports / 'first-boot.json').write_text(json.dumps(first, indent=2))
            if first and warp:
                report.update(state='testado', warpInWindows11Proven=True,
                              reason='primeiro_boot_e_dispositivo_WARP_confirmados')
                (reports / 'warp.json').write_text(json.dumps(warp, indent=2))
                break
            # Envia Enter uma unica vez, somente quando OCR encontra prompt DVD.
            if (not boot_key_sent and elapsed < 120) or elapsed >= next_snapshot:
                try:
                    ppm = root / 'screen.ppm'
                    qmp(root, 'screendump', {'filename': str(ppm)})
                    from PIL import Image
                    with Image.open(ppm) as img:
                        img.save(reports / 'last-screen.png')
                    next_snapshot = elapsed + 60
                    if not boot_key_sent and elapsed < 120:
                        text = subprocess.run(['tesseract', str(ppm), 'stdout', '--psm', '6'],
                                              capture_output=True, text=True, timeout=10).stdout.lower()
                        if 'press any key' in text and 'boot from' in text:
                            qmp(root, 'human-monitor-command', {'command-line': 'sendkey ret'})
                            boot_key_sent = True
                except (OSError, RuntimeError, subprocess.TimeoutExpired):
                    pass
            time.sleep(1)
    except GuestProbeError as error:
        if error.first:
            report['windowsImageBootedProven'] = True
            (reports / 'first-boot.json').write_text(json.dumps(error.first, indent=2))
        report.update(state='bloqueado', reason=str(error), errorType=type(error).__name__)
    except KeyboardInterrupt:
        report.update(state='bloqueado', reason='interrompido')
    except Exception as error:
        report.update(state='bloqueado', reason=str(error), errorType=type(error).__name__)
    finally:
        stop_process(vm); stop_process(tpm)
        report['durationSeconds'] = round(time.monotonic() - started)
        report['freePhysicalBytes'] = shutil.disk_usage(root.parent).free
        if (root / 'windows.qcow2').exists():
            report['diskAllocatedBytes'] = (root / 'windows.qcow2').stat().st_blocks * 512
        (reports / 'installation.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report), flush=True)
    return 0 if report['warpInWindows11Proven'] else 2


if __name__ == '__main__':
    def interrupted(_signum, _frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupted)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', required=True, type=Path)
    p.add_argument('--destination', required=True, type=Path)
    p.add_argument('--reports', required=True, type=Path)
    a = p.parse_args()
    os.umask(0o077)
    a.reports.mkdir(parents=True, exist_ok=True)
    raise SystemExit(run(a.iso.resolve(), a.destination.resolve(), a.reports.resolve()))
