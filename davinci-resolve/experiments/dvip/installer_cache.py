#!/usr/bin/env python3
"""Authenticated, streaming cache for the unmodified official Resolve 21.1.1 installer.

GitHub Actions caches are readable by some PR workflows. ONLY the AES-256-GCM
ciphertext belongs in the cache. Never cache the .run/.zip, URL or password.
"""
import argparse
import hashlib
import hmac
import json
import os
import struct
import tempfile
from pathlib import Path

from source import NAME, RUN_SHA256, digest

MAGIC = b"DVICACH1"
ITERATIONS = 600_000
CHUNK_BYTES = 4 * 1024 * 1024
MAX_BYTES = 5 * 1024 ** 3
HEADER_BYTES = len(MAGIC) + 16 + 12 + 4
TAG_BYTES = 16
ENCRYPTED_NAME = "resolve-21.1.1.run.aesgcm"


class CacheBlocked(ValueError):
    pass


def password_bytes(required=False):
    value = os.environ.get("DAVINCI_INSTALLER_CACHE_PASSWORD", "")
    if not value:
        if required:
            raise CacheBlocked("Configure DAVINCI_INSTALLER_CACHE_PASSWORD como segredo aleatório de 32+ caracteres.")
        return None
    if len(value) < 32:
        raise CacheBlocked("DAVINCI_INSTALLER_CACHE_PASSWORD deve ter 32+ caracteres aleatórios.")
    return value.encode("utf-8")


def key_suffix(password):
    """A stable, domain-separated identifier; safe only with a random secret."""
    return hmac.new(password, b"resolve-21.1.1-installer-aesgcm-cache-v1",
                    hashlib.sha256).hexdigest()[:24]


def emit_key():
    key = password_bytes()
    enabled = key is not None
    suffix = key_suffix(key) if enabled else ""
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as file:
            file.write("enabled=" + str(enabled).lower() + "\n")
            file.write("suffix=" + suffix + "\n")
    return {"cacheEnabled": enabled, "plaintextCached": False}


def validate_installer(path):
    if path.is_symlink() or not path.is_file() or not (0 < path.stat().st_size <= MAX_BYTES):
        raise CacheBlocked("Instalador original não existe ou seu tamanho é inválido.")
    if digest(path) != RUN_SHA256:
        raise CacheBlocked("SHA-256 do instalador não coincide com a amostra oficial anteriormente verificada.")


def derive(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password, salt, ITERATIONS, dklen=32)


def encrypt(private_dir, cache_dir):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    password = password_bytes(required=True)
    installer = private_dir / NAME
    validate_installer(installer)
    cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(cache_dir, 0o700)
    target = cache_dir / ENCRYPTED_NAME
    if target.exists() or target.is_symlink():
        raise CacheBlocked("Cache de destino já existe; não sobrescrever silenciosamente.")
    salt, nonce = os.urandom(16), os.urandom(12)
    header = MAGIC + salt + nonce + struct.pack(">I", ITERATIONS)
    cipher = Cipher(algorithms.AES(derive(password, salt)), modes.GCM(nonce)).encryptor()
    cipher.authenticate_additional_data(header)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=cache_dir, prefix=".install-", delete=False) as out:
            temporary = Path(out.name)
            os.chmod(temporary, 0o600)
            out.write(header)
            with installer.open("rb") as source:
                while chunk := source.read(CHUNK_BYTES):
                    out.write(cipher.update(chunk))
            out.write(cipher.finalize())
            out.write(cipher.tag)
        temporary.replace(target)
        os.chmod(target, 0o600)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"encrypted": True, "plaintextCached": False,
            "ciphertextSizeBytes": target.stat().st_size, "installerVerified": True}


def decrypt(cache_dir, private_dir):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.exceptions import InvalidTag

    password = password_bytes(required=True)
    source = cache_dir / ENCRYPTED_NAME
    if (source.is_symlink() or not source.is_file() or
            not (HEADER_BYTES + TAG_BYTES < source.stat().st_size <= MAX_BYTES + HEADER_BYTES + TAG_BYTES)):
        raise CacheBlocked("Cache cifrado ausente ou com tamanho inválido.")

    with source.open("rb") as data:
        header = data.read(HEADER_BYTES)
        if (len(header) != HEADER_BYTES or header[:len(MAGIC)] != MAGIC or
                struct.unpack(">I", header[-4:])[0] != ITERATIONS):
            raise CacheBlocked("Cabeçalho do cache cifrado inválido.")
        salt = header[len(MAGIC):len(MAGIC) + 16]
        nonce = header[len(MAGIC) + 16:len(MAGIC) + 28]
        data.seek(-TAG_BYTES, 2)
        tag = data.read(TAG_BYTES)
        data.seek(HEADER_BYTES)
        remaining = source.stat().st_size - HEADER_BYTES - TAG_BYTES
        cipher = Cipher(algorithms.AES(derive(password, salt)), modes.GCM(nonce, tag)).decryptor()
        cipher.authenticate_additional_data(header)
        private_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(private_dir, 0o700)
        target = private_dir / NAME
        if target.exists() or target.is_symlink():
            raise CacheBlocked("Instalador de destino já existe; operação recusada.")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=private_dir, prefix=".resolve-", delete=False) as out:
                temporary = Path(out.name)
                os.chmod(temporary, 0o600)
                while remaining:
                    encrypted = data.read(min(CHUNK_BYTES, remaining))
                    if not encrypted:
                        raise CacheBlocked("Cache truncado.")
                    remaining -= len(encrypted)
                    out.write(cipher.update(encrypted))
                try:
                    out.write(cipher.finalize())
                except InvalidTag:
                    raise CacheBlocked("Cache não autenticado: senha errada ou arquivo adulterado.") from None
            validate_installer(temporary)
            temporary.replace(target)
            os.chmod(target, 0o700)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return {"authenticated": True, "installerVerified": True,
            "downloadSkipped": True, "plaintextCached": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("key", "encrypt", "decrypt"))
    p.add_argument("--private-dir", type=Path)
    p.add_argument("--cache-dir", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    try:
        if args.action == "key":
            result = emit_key()
        else:
            if args.private_dir is None or args.cache_dir is None:
                raise CacheBlocked("Diretórios privados e de cache são necessários.")
            result = (encrypt if args.action == "encrypt" else decrypt)(
                args.private_dir, args.cache_dir)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        return 0
    except (CacheBlocked, OSError, ValueError) as exc:
        # Never show full paths, signed URLs, passwords or cryptographic keys.
        print(json.dumps({"state": "bloqueado", "reason": str(exc) if
                          isinstance(exc, CacheBlocked) else type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
