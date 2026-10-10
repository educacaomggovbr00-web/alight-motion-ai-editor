import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('vm_state', Path(__file__).resolve().parents[1] / 'vm_state.py')
if not spec.origin or not Path(spec.origin).exists():
    spec = importlib.util.spec_from_file_location('vm_state', Path(__file__).resolve().parents[1] / 'windows' / 'vm_state.py')
vm = importlib.util.module_from_spec(spec); spec.loader.exec_module(vm)


class PersistenceTests(unittest.TestCase):
    def fixture(self, root):
        root.mkdir(); (root / 'tpm').mkdir()
        (root / 'windows.qcow2').write_bytes(b'fixture-nao-windows')
        (root / 'vars.fd').write_bytes(b'uefi-fixture')
        (root / 'tpm' / 'tpm2-00.permall').write_bytes(b'tpm-fixture')

    def test_backup_restore_and_corruption(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(vm, 'check_disk'):
            base = Path(temp); self.fixture(base / 'original')
            vm.transfer(base / 'original', base / 'backup', offline=True)
            vm.transfer(base / 'backup', base / 'restored', restore=True)
            self.assertEqual(vm.inventory(base / 'original'), vm.inventory(base / 'restored'))
            (base / 'backup' / 'vars.fd').write_bytes(b'corrompido')
            with self.assertRaises(ValueError):
                vm.transfer(base / 'backup', base / 'rejected', restore=True)
            self.assertFalse((base / 'rejected').exists())

    def test_overwrite_symlink_and_offline_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); self.fixture(base / 'original')
            with self.assertRaises(ValueError):
                vm.transfer(base / 'original', base / 'original', offline=True)
            with self.assertRaises(ValueError):
                vm.transfer(base / 'original', base / 'backup')
            (base / 'original' / 'vars.fd').unlink()
            (base / 'original' / 'vars.fd').symlink_to(base / 'original' / 'windows.qcow2')
            with self.assertRaises(ValueError):
                vm.inventory(base / 'original')

    def test_manifest_traversal_rejected(self):
        for name in ['../secret', '/secret', 'tpm/../../secret', 'tpm\\secret', 'extra.exe']:
            with self.assertRaises(ValueError):
                vm.safe_path(name)

    @unittest.skipUnless(shutil.which('qemu-img'), 'qemu-img ausente: integracao executada no CI')
    def test_real_qcow2_backup_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); self.fixture(base / 'original')
            disk = base / 'original' / 'windows.qcow2'; disk.unlink()
            subprocess.run(['qemu-img', 'create', '-f', 'qcow2', str(disk), '8M'], check=True, capture_output=True)
            vm.transfer(base / 'original', base / 'backup', offline=True)
            vm.transfer(base / 'backup', base / 'restored', restore=True)
            vm.check_disk(base / 'restored')
            self.assertEqual(vm.digest(disk), vm.digest(base / 'restored' / 'windows.qcow2'))
            # Disco real, porém vazio: não comprova instalação nem boot de Windows.


if __name__ == '__main__':
    unittest.main()
