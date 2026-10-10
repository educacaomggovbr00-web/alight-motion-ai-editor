import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('inspect_download', Path(__file__).parents[1] / 'inspect_download.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class DownloadInspectionTests(unittest.TestCase):
    def test_unsafe_zip_rejected_before_signature_or_execution(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'package.zip'
            for bad in ('../outside', '/absolute', 'C:\\outside'):
                with zipfile.ZipFile(archive, 'w') as package:
                    package.writestr(bad, b'unsafe')
                    package.writestr('Set-up.exe', b'not an executable')
                with self.subTest(path=bad), self.assertRaisesRegex(ValueError, 'Caminho inseguro'):
                    module.inspect(archive, 'verifier-must-not-run', 'unused')

    def test_missing_or_duplicate_setup_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'package.zip'
            for names in (['readme.txt'], ['Set-up.exe', 'other/Set-up.exe']):
                with zipfile.ZipFile(archive, 'w') as package:
                    for name in names:
                        package.writestr(name, b'test')
                with self.assertRaisesRegex(ValueError, 'único'):
                    module.inspect(archive, 'verifier-must-not-run', 'unused')
