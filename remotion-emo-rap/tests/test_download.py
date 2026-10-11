import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('download',Path(__file__).resolve().parents[1]/'scripts/download-input.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class DownloadTests(unittest.TestCase):
    def test_safe_zip_and_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);z=p/'safe.zip'
            with zipfile.ZipFile(z,'w') as f:f.writestr('artist.mp4',b'fixture')
            m.extract(z,p/'input');self.assertEqual((p/'input/artist.mp4').read_bytes(),b'fixture')
            with zipfile.ZipFile(z,'w') as f:f.writestr('artist.mp4',b'fixture');f.writestr('../secret',b'x')
            with self.assertRaises(ValueError):m.extract(z,p/'rejected')
            self.assertFalse((p/'rejected').exists())
    def test_private_host_and_redirects(self):
        with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
            with self.assertRaises(ValueError):m.validate_url('https://media.example/video','media.example')
        for url in ['http://media.example/x','https://evil.example/x','https://user:password@media.example/x']:
            with self.assertRaises(ValueError):m.validate_url(url,'media.example')
