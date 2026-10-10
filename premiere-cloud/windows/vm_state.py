"""Backup privado de VM QEMU desligada; não cria storage nem instala Adobe."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import subprocess
import tempfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_path(name):
    p = PurePosixPath(name)
    if (not isinstance(name, str) or not name or '\\' in name or
            p.is_absolute() or '..' in p.parts or str(p) != name or
            not (name in ('windows.qcow2', 'vars.fd') or
                 (len(p.parts) > 1 and p.parts[0] == 'tpm'))):
        raise ValueError('Caminho do backup recusado')
    return p


def private_root(root):
    root = Path(root).absolute()
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('Diretorio com symlink recusado')
    # Não permita armazenar/copiar um Windows dentro de um checkout Git.
    if any((p / '.git').exists() for p in (root, *root.parents)):
        raise ValueError('Use armazenamento privado fora do checkout Git')
    return root


def check_disk(root):
    subprocess.run(['qemu-img', 'check', '-f', 'qcow2', str(root / 'windows.qcow2')],
                   check=True, capture_output=True, timeout=600)


def inventory(root):
    files = []
    for base in ('windows.qcow2', 'vars.fd', 'tpm'):
        p = root / base
        if not p.exists() or p.is_symlink():
            raise ValueError('Disco, UEFI ou TPM ausente/invalido')
        candidates = list(p.rglob('*')) if p.is_dir() else [p]
        for item in candidates:
            if item.is_symlink() or (not item.is_dir() and not item.is_file()):
                raise ValueError('Arquivo especial ou symlink recusado')
            if item.is_file():
                name = item.relative_to(root).as_posix()
                safe_path(name)
                files.append({'path': name, 'bytes': item.stat().st_size,
                              'sha256': digest(item)})
    if not any(x['path'].startswith('tpm/') for x in files):
        raise ValueError('Estado TPM vazio')
    return sorted(files, key=lambda x: x['path'])


def verify(root):
    root = private_root(root)
    manifest_path = root / 'manifest.json'
    if manifest_path.is_symlink():
        raise ValueError('Manifest symlink recusado')
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('schema') != 1 or not isinstance(manifest.get('files'), list):
        raise ValueError('Manifest invalido')
    seen = set()
    for item in manifest['files']:
        safe_path(item['path'])
        if item['path'] in seen:
            raise ValueError('Caminho duplicado')
        seen.add(item['path'])
    if manifest['files'] != inventory(root):
        raise ValueError('Integridade SHA256/tamanho/inventario recusada')
    return manifest


def transfer(source, destination, restore=False, offline=False):
    source, destination = private_root(source), private_root(destination)
    if destination.exists() or source == destination or source in destination.parents:
        raise ValueError('Destino deve ser novo e fora da origem; nada sera sobrescrito')
    if not destination.parent.is_dir():
        raise ValueError('Monte o armazenamento privado antes de usar')
    if restore:
        entries = verify(source)['files']
    else:
        if not offline:
            raise ValueError('Desligue Windows, QEMU e swtpm; confirme --offline')
        for name in ('qmp.sock', 'tpm.sock'):
            sock_path = source / name
            if sock_path.exists():
                with socket.socket(socket.AF_UNIX) as s:
                    s.settimeout(1)
                    try:
                        s.connect(str(sock_path))
                    except (ConnectionRefusedError, FileNotFoundError):
                        pass  # socket residual de processo encerrado
                    else:
                        raise ValueError('VM/TPM ainda em execucao')
        check_disk(source)  # leitura com lock do QEMU; nunca usar --force-share
        entries = inventory(source)
    total = sum(x['bytes'] for x in entries)
    if shutil.disk_usage(destination.parent).free < total + 1024**3:
        raise ValueError('Espaco insuficiente para copia e reserva de 1 GiB')
    stage = Path(tempfile.mkdtemp(prefix='.vm-copy-', dir=destination.parent))
    try:
        for item in entries:
            target = stage / item['path']
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with (source / item['path']).open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst, 8 * 1024**2)
                dst.flush(); os.fsync(dst.fileno())
            target.chmod(0o600)
        manifest = {'schema': 1, 'scope': 'offline_disk_uefi_tpm_backup',
                    'files': entries, 'desktopProven': False, 'premiereProven': False}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        (stage / 'manifest.json').chmod(0o600)
        verify(stage)
        check_disk(stage)
        # Détecta alteração da origem durante a cópia; backup deve ser offline.
        if inventory(source) != entries:
            raise ValueError('Origem alterada durante copia')
        # mkdir exclusivo evita substituir um destino criado em paralelo.
        destination.mkdir(mode=0o700)
        try:
            for child in stage.iterdir():
                child.rename(destination / child.name)
        except Exception:
            shutil.rmtree(destination)
            raise
        return manifest
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == '__main__':
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=['backup', 'restore', 'verify'])
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--destination', type=Path)
    p.add_argument('--offline', action='store_true')
    a = p.parse_args()
    if a.operation == 'verify':
        result = verify(a.source)
    else:
        if a.destination is None:
            p.error('--destination obrigatorio')
        result = transfer(a.source, a.destination,
                          restore=a.operation == 'restore', offline=a.offline)
    print(json.dumps({'state': 'testado', 'scope': result['scope'],
                      'files': len(result['files']), 'premiereProven': False}))
