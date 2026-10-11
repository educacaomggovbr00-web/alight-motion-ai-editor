import importlib.util
from pathlib import Path
import tempfile
import unittest

p = Path(__file__).resolve().parents[1] / 'windows/inspect_resume.py'
if not p.exists():
    p = Path(__file__).resolve().parents[1] / 'inspect_resume.py'
spec = importlib.util.spec_from_file_location('inspect_resume', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ResumeTests(unittest.TestCase):
    def fixture(self, root):
        (root/'windows.raw').write_bytes(b'partial-disk')
        (root/'vars.fd').write_bytes(b'uefi-fixture')
        (root/'tpm').mkdir()
        (root/'tpm/state').write_bytes(b'tpm-fixture')

    def test_inspection_does_not_claim_boot_or_change_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root)
            before={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()}
            r=m.inspect_state(root)
            self.assertFalse(r['bootableProven']);self.assertFalse(r['premiereProven'])
            self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir() if p.is_file()})

    def test_missing_state_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.inspect_state(d)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root)
            (root/'vars.fd').unlink();(root/'vars.fd').symlink_to(root/'windows.raw')
            with self.assertRaises(ValueError):m.inspect_state(root)

    def test_two_disks_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root);(root/'windows.qcow2').write_bytes(b'other')
            with self.assertRaises(ValueError):m.inspect_state(root)
