"""Smoke tests for the phone-friendly repo ZIP import route."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "import-repo-zip.py"

class RepoZipImportTests(unittest.TestCase):
    def test_import_valid_repository_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "importar").mkdir()
            (root / "public").mkdir()
            with zipfile.ZipFile(root / "importar" / "entrada.zip", "w") as bundle:
                bundle.writestr("artist.mp4", b"mock-video-not-a-real-mp4")
                bundle.writestr("beats.json", b'{"beats":[0.5]}')
            run = subprocess.run([sys.executable, str(SCRIPT)], cwd=root,
                                 text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertEqual((root / "public/input/artist.mp4").read_bytes(),
                             b"mock-video-not-a-real-mp4")
            self.assertEqual((root / "public/input/beats.json").read_bytes(),
                             b'{"beats":[0.5]}')

    def test_missing_zip_does_not_create_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "public").mkdir()
            run = subprocess.run([sys.executable, str(SCRIPT)], cwd=root,
                                 text=True, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse((root / "public/input").exists())

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "importar").mkdir()
            (root / "public").mkdir()
            with zipfile.ZipFile(root / "importar" / "entrada.zip", "w") as bundle:
                bundle.writestr("artist.mp4", b"mock")
                bundle.writestr("../outside.mp4", b"no")
            run = subprocess.run([sys.executable, str(SCRIPT)], cwd=root,
                                 text=True, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse((root / "public/input").exists())

if __name__ == "__main__":
    unittest.main()
