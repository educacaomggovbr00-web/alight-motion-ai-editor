"""Inspecao somente leitura; nao inicia VM, nao baixa ISO e nao prova Premiere."""
import argparse
import json
import os
from pathlib import Path
import shutil


def inspect_state(root):
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Diretorio de estado ausente ou symlink')
    disks = [root / n for n in ('windows.raw', 'windows.qcow2') if (root / n).exists()]
    if len(disks) != 1:
        raise ValueError('Exige exatamente um disco RAW ou QCOW2')
    for item in [disks[0], root / 'vars.fd', root / 'tpm']:
        if item.is_symlink() or not item.exists():
            raise ValueError('Estado disco/UEFI/TPM incompleto')
    if not disks[0].is_file() or not (root / 'vars.fd').is_file() or not (root / 'tpm').is_dir():
        raise ValueError('Tipo de arquivo invalido')
    tpm = list((root / 'tpm').rglob('*'))
    if any(p.is_symlink() or (not p.is_dir() and not p.is_file()) for p in tpm):
        raise ValueError('Estado TPM invalido')
    if not any(p.is_file() and p.stat().st_size > 0 for p in tpm):
        raise ValueError('Estado TPM vazio')
    previous = {}
    evidence = root / 'attempt.json'
    if evidence.is_symlink():
        raise ValueError('Relatorio symlink recusado')
    if evidence.is_file():
        if evidence.stat().st_size > 65536:
            raise ValueError('Relatorio excede limite')
        previous = json.loads(evidence.read_text())
        if not isinstance(previous, dict):
            raise ValueError('Relatorio invalido')
    stat = disks[0].stat()
    return {'diskFormat': disks[0].suffix[1:], 'diskLogicalBytes': stat.st_size,
            'diskAllocatedBytes': stat.st_blocks * 512, 'uefiAndTpmPresent': True,
            'previousEvidence': {k: previous.get(k) for k in
                ('state', 'reason', 'windowsInstalledProven', 'premiereInstalledProven')},
            'bootableProven': False, 'desktopProven': False, 'premiereProven': False,
            'note': 'Presenca dos arquivos nao prova integridade, boot ou instalacao concluida.'}


def inspect_host(root):
    ram_kib = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                       if line.startswith('MemAvailable:')))
    reasons = []
    kvm = os.access('/dev/kvm', os.R_OK | os.W_OK)
    dri = Path('/dev/dri')
    gpu_device = dri.is_dir() and any(dri.glob('renderD*'))
    if not kvm:
        reasons.append('KVM indisponivel: retomada seria emulada por CPU, muito lenta.')
    if not gpu_device:
        reasons.append('Nenhum dispositivo GPU renderD exposto; VRAM/pass-through nao comprovados.')
    if ram_kib < 10 * 1024**2:
        reasons.append('Menos de 10 GiB RAM livre exigidos pelo launcher de retomada.')
    tools = {name: bool(shutil.which(name)) for name in ('qemu-system-x86_64', 'qemu-img', 'swtpm')}
    if not all(tools.values()):
        reasons.append('Ferramentas QEMU/TPM ausentes do PATH; binarios privados exigem configuracao explicita.')
    free = shutil.disk_usage(root).free
    if free < 8 * 1024**3:
        reasons.append('Menos de 8 GiB de disco livre para retomada.')
    return {'state': 'bloqueado' if reasons else 'experimental', 'kvmAvailable': kvm,
            'gpuDeviceExposed': gpu_device, 'vramProven': False, 'availableRamBytes': ram_kib * 1024,
            'freeDiskBytes': free, 'toolsOnPath': tools, 'blockers': reasons,
            'premiereProven': False,
            'nextAction': 'Host privado persistente autorizado com Windows/GPU/licencas; executar preflight.ps1 na sessao grafica.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state-dir', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    report = {'schema': 1, 'scope': 'read_only_resume_audit',
              'host': inspect_host(a.state_dir or Path.cwd()),
              'vm': inspect_state(a.state_dir) if a.state_dir else None}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print('Inspecao somente leitura salva. Nenhuma VM ou instalacao iniciada.')
