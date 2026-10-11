"""Baixa ZIP de URL secreta HTTPS, sem imprimir a URL ou erros de transporte."""
import ipaddress
import os
from pathlib import Path
import shutil
import socket
import stat
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile

MAX_BYTES = 450 * 1024**2
ALLOWED = {'artist.mp4', 'music.wav', 'music.mp3', 'music.m4a', 'lyrics.json', 'beats.json'}


def validate_url(url, host):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != host or parsed.port not in (None, 443) or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('URL/host recusado')
    if not host or host.endswith('.local') or host in ('localhost', 'metadata.google.internal'):
        raise ValueError('Host recusado')
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses):
        raise ValueError('Endereco privado recusado')


class Redirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, host):
        self.host = host
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl, self.host)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def extract(source, target):
    if target.exists():
        raise ValueError('Entrada ja existe; use pasta nova')
    with zipfile.ZipFile(source) as z:
        entries = z.infolist()
        names = [e.filename for e in entries]
        if len(entries) > 6 or len(set(names)) != len(names) or 'artist.mp4' not in names:
            raise ValueError('ZIP requer artist.mp4 e no maximo seis arquivos sem duplicacao')
        if any(e.filename not in ALLOWED or e.is_dir() or stat.S_ISLNK(e.external_attr >> 16) for e in entries):
            raise ValueError('ZIP possui caminhos/arquivos nao permitidos')
        if sum(e.file_size for e in entries) > MAX_BYTES:
            raise ValueError('ZIP expandido excede limite')
        with tempfile.TemporaryDirectory(dir=target.parent) as temp:
            stage = Path(temp)
            for e in entries:
                limit = (300 if e.filename == 'artist.mp4' else 1 if e.filename.endswith('.json') else 100) * 1024**2
                if e.file_size == 0 or e.file_size > limit:
                    raise ValueError('Arquivo excede limite')
                with z.open(e) as src, (stage / e.filename).open('xb') as dst:
                    total = 0
                    while chunk := src.read(1024**2):
                        total += len(chunk)
                        if total > limit:
                            raise ValueError('Arquivo expandido excede limite')
                        dst.write(chunk)
            # Só publica entrada quando o ZIP inteiro foi validado.
            shutil.copytree(stage, target)


def main():
    url = os.environ.get('REMOTION_INPUT_BUNDLE_URL', '')
    host = os.environ.get('REMOTION_MEDIA_HOST', '').strip().lower()
    validate_url(url, host)
    target = Path('public/input');target.parent.mkdir(exist_ok=True)
    opener = urllib.request.build_opener(Redirect(host))
    started = time.monotonic()
    with tempfile.TemporaryDirectory() as temp:
        bundle = Path(temp) / 'input.zip'
        with opener.open(url, timeout=30) as response, bundle.open('xb') as output:
            total = 0
            while chunk := response.read(1024**2):
                total += len(chunk)
                if total > MAX_BYTES or time.monotonic() - started > 1200:
                    raise ValueError('Limite de download excedido')
                output.write(chunk)
        extract(bundle, target)
    print('Entrada privada baixada; nenhum link publicado')


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except Exception:
        raise SystemExit('Entrada indisponivel/invalida. Confira secret, host autorizado, validade do link e formato ZIP; detalhes sensiveis omitidos.')
