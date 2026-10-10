"""Inspeção Linux de pacote Adobe já baixado; não instala nem executa Adobe."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import zipfile

def inspect(archive, verifier, ca_file):
    archive = Path(archive)
    if archive.stat().st_size > 650_000_000:
        raise ValueError('Pacote excede limite de download')
    with zipfile.ZipFile(archive) as package:
        entries = package.infolist()
        if len(entries) > 10000 or sum(e.file_size for e in entries) > 2_000_000_000:
            raise ValueError('ZIP excede limite de extração')
        for entry in entries:
            name = entry.filename.replace('\\', '/')
            parts = PurePosixPath(name)
            if parts.is_absolute() or '..' in parts.parts or ':' in name:
                raise ValueError('Caminho inseguro no pacote')
        setups = [e for e in entries if PurePosixPath(e.filename).name.lower() == 'set-up.exe']
        if len(setups) != 1:
            raise ValueError('Instalador único não encontrado')
        if package.testzip() is not None:
            raise ValueError('CRC inválido')
        with tempfile.TemporaryDirectory(prefix='adobe-signature-') as root:
            setup = Path(root) / 'Set-up.exe'
            setup.write_bytes(package.read(setups[0]))
            result = subprocess.run([str(verifier), 'verify', '-CAfile', str(ca_file), '-in', str(setup)],
                                    capture_output=True, text=True, timeout=90)
            # Retorno inclui integridade do PE, cadeia de confiança e timestamp.
            # Validação Windows Authenticode deverá ser repetida antes da instalação.
            adobe = re.search(r'Subject:\s*CN=Adobe Inc\.,[^\n]*\bO=Adobe Inc\.(?:,|$)', result.stdout)
            if result.returncode != 0 or not adobe or 'Signature verification: ok' not in result.stdout:
                raise ValueError('Assinatura Adobe/cadeia de confiança não comprovada')
            with setup.open('rb') as stream:
                setup_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    with archive.open('rb') as stream:
        archive_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    return dict(state='testado', scope='download_e_assinatura_apenas', bytes=archive.stat().st_size,
                zip_entries=len(entries), zip_crc='valid', archive_sha256=archive_hash,
                installer_sha256=setup_hash, publisher='Adobe Inc.', signature='verified_osslsigncode',
                installed=False, premiere_executed=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', required=True)
    parser.add_argument('--verifier', required=True)
    parser.add_argument('--ca-file', default='/etc/ssl/certs/ca-certificates.crt')
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    try:
        report = inspect(args.archive, args.verifier, args.ca_file)
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False))
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.TimeoutExpired) as error:
        print('Inspeção bloqueada: ' + type(error).__name__)
        raise SystemExit(2)
