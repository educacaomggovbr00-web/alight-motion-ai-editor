import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('windows_install', ROOT / 'windows/install-unattended.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class WindowsUnattendedTests(unittest.TestCase):
    def test_success_requires_guest_first_boot_and_real_warp_fields(self):
        first = dict(windows11=True, phase='specialize', build='26300')
        warp = dict(windows11=True, state='testado', renderer='WARP_CPU', featureLevel='0xb000',
                    scope='criacao_dispositivo_Direct3D11_WARP_apenas')
        prefix = 'CODEX_WINDOWS11_WARP_OK '
        self.assertEqual(mod.parse_evidence('script completed successfully'), (None, None))
        self.assertIsNone(mod.parse_evidence(prefix + json.dumps(warp))[0])
        for field, value in [('windows11', False), ('renderer', 'hardware'), ('featureLevel', '0x9300')]:
            bad = {**warp, field: value}
            self.assertIsNone(mod.parse_evidence(prefix + json.dumps(bad))[1])
        serial = 'CODEX_WINDOWS11_FIRST_BOOT ' + json.dumps(first) + '\n' + prefix + json.dumps(warp)
        self.assertEqual(mod.parse_evidence(serial), (first, warp))

    def test_guest_errors_and_malformed_json_never_pass(self):
        self.assertEqual(mod.parse_evidence('CODEX_WINDOWS11_WARP_OK not-json'), (None, None))
        with self.assertRaises(RuntimeError):
            mod.parse_evidence('CODEX_GUEST_ERROR {"state":"bloqueado"}')
        first = {'windows11': True, 'phase': 'specialize'}
        with self.assertRaises(mod.GuestProbeError) as caught:
            mod.parse_evidence('CODEX_WINDOWS11_FIRST_BOOT ' + json.dumps(first) + '\nCODEX_GUEST_ERROR {}')
        self.assertEqual(caught.exception.first, first)

    def test_existing_machine_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); machine = base / 'machine'; machine.mkdir()
            disk = machine / 'windows.qcow2'; disk.write_bytes(b'preserve existing disk')
            reports = base / 'reports'; reports.mkdir()
            self.assertEqual(mod.run(base / 'missing.iso', machine, reports), 2)
            self.assertEqual(disk.read_bytes(), b'preserve existing disk')
            data = json.loads((reports / 'installation.json').read_text())
            self.assertFalse(data['windowsImageBootedProven'])
            self.assertFalse(data['premiereInstalledProven'])

    def test_answer_file_targets_only_new_vm_disk_without_account_bypass(self):
        tree = ET.parse(ROOT / 'windows/Autounattend.xml')
        ns = {'u': 'urn:schemas-microsoft-com:unattend'}
        self.assertEqual(tree.find('.//u:Disk/u:DiskID', ns).text, '0')
        self.assertEqual(tree.find('.//u:InstallTo/u:PartitionID', ns).text, '3')
        forbidden = {'ProductKey', 'AutoLogon', 'LocalAccounts', 'SkipMachineOOBE', 'SkipUserOOBE'}
        self.assertFalse(forbidden & {node.tag.split('}')[-1] for node in tree.iter()})


if __name__ == '__main__':
    unittest.main()
