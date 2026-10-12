"""Fast offline tests; no download, proprietary data or Actions secret."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import installer_cache as cache


class EncryptedInstallerCache(unittest.TestCase):
    PASSWORD = "only-fixture-32-chars-not-a-real-secret-0123456789"
    WRONG = "DIFFERENT-fixture-password-not-a-real-secret-0123456789"

    def test_optional_key_without_secret(self):
        with patch.dict(os.environ, {"DAVINCI_INSTALLER_CACHE_PASSWORD": ""}):
            self.assertFalse(cache.emit_key()["cacheEnabled"])

    def test_short_password_does_not_create_weak_cache(self):
        with patch.dict(os.environ, {"DAVINCI_INSTALLER_CACHE_PASSWORD": "short"}):
            with self.assertRaises(cache.CacheBlocked):
                cache.emit_key()

    def test_key_suffix_deterministic_rotates_but_contains_no_secret(self):
        p = self.PASSWORD.encode()
        a = cache.key_suffix(p)
        self.assertEqual(a, cache.key_suffix(p))
        self.assertNotEqual(a, cache.key_suffix(self.WRONG.encode()))
        self.assertNotIn("fixture", a)

    def test_roundtrip_and_authentication(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            installer = directory / "download"
            installer.mkdir()
            plain = installer / cache.NAME
            plain.write_bytes((b"official-installer-TEST-FIXTURE\0" * 16000))
            expected = cache.digest(plain)
            cached = directory / "cache"
            dest = directory / "restored"
            with patch.dict(os.environ, {"DAVINCI_INSTALLER_CACHE_PASSWORD": self.PASSWORD}), \
                 patch.object(cache, "RUN_SHA256", expected):
                report = cache.encrypt(installer, cached)
                self.assertTrue(report["encrypted"])
                self.assertFalse(report["plaintextCached"])
                encrypted = (cached / cache.ENCRYPTED_NAME).read_bytes()
                self.assertNotIn(b"official-installer-TEST-FIXTURE", encrypted)
                self.assertFalse((cached / cache.NAME).exists())
                restored = cache.decrypt(cached, dest)
                self.assertTrue(restored["downloadSkipped"])
                self.assertEqual((dest / cache.NAME).read_bytes(), plain.read_bytes())

    def test_wrong_password_and_tampering_fail_without_plaintext(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            installer = directory / "input"
            installer.mkdir()
            (installer / cache.NAME).write_bytes(b"test-official-fixture-" * 1000)
            expected = cache.digest(installer / cache.NAME)
            encrypted_dir = directory / "encrypted"
            with patch.object(cache, "RUN_SHA256", expected):
                with patch.dict(os.environ, {"DAVINCI_INSTALLER_CACHE_PASSWORD": self.PASSWORD}):
                    cache.encrypt(installer, encrypted_dir)
                with patch.dict(os.environ, {"DAVINCI_INSTALLER_CACHE_PASSWORD": self.WRONG}):
                    with self.assertRaises(cache.CacheBlocked):
                        cache.decrypt(encrypted_dir, directory / "badpass")
                self.assertFalse((directory / "badpass" / cache.NAME).exists())
                path = encrypted_dir / cache.ENCRYPTED_NAME
                changed = bytearray(path.read_bytes())
                changed[-24] ^= 1
                path.write_bytes(changed)
                with patch.dict(os.environ, {"DAVINCI_INSTALLER_CACHE_PASSWORD": self.PASSWORD}):
                    with self.assertRaises(cache.CacheBlocked):
                        cache.decrypt(encrypted_dir, directory / "tampered")
                self.assertFalse((directory / "tampered" / cache.NAME).exists())

    def test_invalid_digest_blocks_cache_creation(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            original = root / "original"
            original.mkdir()
            (original / cache.NAME).write_bytes(b"not-the-official-installer")
            with patch.dict(os.environ, {"DAVINCI_INSTALLER_CACHE_PASSWORD": self.PASSWORD}):
                with self.assertRaises(cache.CacheBlocked):
                    cache.encrypt(original, root / "cache")
            self.assertFalse((root / "cache" / cache.ENCRYPTED_NAME).exists())

    def test_wrong_expected_digest_blocks_restoration(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            original = root / "original"
            original.mkdir()
            (original / cache.NAME).write_bytes(b"sha256-fixture" * 100)
            expected = cache.digest(original / cache.NAME)
            with patch.dict(os.environ, {"DAVINCI_INSTALLER_CACHE_PASSWORD": self.PASSWORD}):
                with patch.object(cache, "RUN_SHA256", expected):
                    cache.encrypt(original, root / "cache")
                with self.assertRaises(cache.CacheBlocked):
                    cache.decrypt(root / "cache", root / "restored")
            self.assertFalse((root / "restored" / cache.NAME).exists())


if __name__ == "__main__":
    unittest.main()
