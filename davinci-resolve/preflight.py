"""Diagnostico Linux somente leitura. Nao instala nem executa DaVinci Resolve."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess


def evaluate(arch, gpu_exposed, display, executable):
    blockers=[]
    if arch != 'x86_64':blockers.append('Arquitetura Linux x86_64 nao comprovada')
    if not gpu_exposed:blockers.append('Nenhum dispositivo GPU exposto; CUDA/OpenCL e VRAM nao comprovados')
    if not display:blockers.append('Sessao grafica DISPLAY/WAYLAND_DISPLAY ausente')
    if not executable:blockers.append('Executavel real do DaVinci Resolve nao encontrado')
    return {'state':'bloqueado' if blockers else 'experimental','blockers':blockers,
            'resolveInstalledProven':False,'resolveStartedProven':False,'exportProven':False,
            'manualChecks':['GPU/driver suportados e VRAM real','Requisitos da versao baixada e distribuicao Linux','Licenca da edicao escolhida','Importacao, reproducao e exportacao reais']}


def collect():
    nodes=list(Path('/dev/dri').glob('renderD*')) if Path('/dev/dri').is_dir() else []
    exposed=bool(nodes) or Path('/dev/nvidia0').exists()
    exe=Path('/opt/resolve/bin/resolve')
    report=evaluate(platform.machine(),exposed,bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')),exe.is_file() and os.access(exe,os.X_OK))
    mem={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:'))}
    gpu=[]
    if shutil.which('nvidia-smi'):
        p=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
        if p.returncode==0:
            for line in p.stdout.splitlines():
                parts=line.split(',')
                if len(parts)==3:
                    try:gpu.append({'name':parts[0].strip(),'vramMiB':int(parts[1]),'driver':parts[2].strip()})
                    except ValueError:pass
    report.update(schema=1,scope='host_diagnostic_only',system=platform.system(),architecture=platform.machine(),memoryBytes=mem,gpuDeviceExposed=exposed,nvidiaGpu=gpu,vramProven=bool(gpu),resolveExecutableFound=exe.is_file(),distribution=platform.freedesktop_os_release().get('PRETTY_NAME','unknown'))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=collect();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps({'state':report['state'],'gpuDeviceExposed':report['gpuDeviceExposed'],'resolveStartedProven':False}))
