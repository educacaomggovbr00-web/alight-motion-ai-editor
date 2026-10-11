import tempfile,unittest
from pathlib import Path
import private_crypto as crypto
from cryptography.exceptions import InvalidTag
PASSWORD='TEST_ONLY_not_a_real_secret_12345'
class PrivateEnvelopeTests(unittest.TestCase):
    def test_round_trip_and_no_plain_cache(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'source';source.write_bytes(b'PRIVATE_UNIT_FIXTURE_NOT_REAL_MEDIA'*50)
            envelope=root/'prepared.dvi';target=root/'target'
            crypto.encrypt(source,envelope,PASSWORD,'input');crypto.decrypt(envelope,target,PASSWORD,'input')
            self.assertEqual(source.read_bytes(),target.read_bytes())
            self.assertNotIn(b'PRIVATE_UNIT_FIXTURE',envelope.read_bytes())
            self.assertNotIn(PASSWORD.encode(),envelope.read_bytes())
    def test_wrong_password_and_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'source';source.write_bytes(b'UNIT_FIXTURE_NOT_VIDEO'*10);envelope=root/'private';target=root/'target'
            crypto.encrypt(source,envelope,PASSWORD,'delivery')
            with self.assertRaises(InvalidTag):crypto.decrypt(envelope,target,PASSWORD+'wrong','delivery')
            damaged=bytearray(envelope.read_bytes());damaged[-1]^=1;envelope.write_bytes(damaged)
            with self.assertRaises(InvalidTag):crypto.decrypt(envelope,target,PASSWORD,'delivery')
            self.assertFalse(target.exists())
    def test_input_cache_invalidation(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'source';p.write_bytes(b'UNIT_FIXTURE')
            a=crypto.input_cache_key(p,PASSWORD,'v1')
            self.assertNotEqual(a,crypto.input_cache_key(p,PASSWORD+'new','v1'))
            self.assertNotEqual(a,crypto.input_cache_key(p,PASSWORD,'v2'))
            p.write_bytes(b'DIFFERENT_FIXTURE');self.assertNotEqual(a,crypto.input_cache_key(p,PASSWORD,'v1'))
    def test_no_unbounded_kdf_or_weak_password(self):
        with self.assertRaises(ValueError):crypto.password_bytes('short')
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'fake';p.write_bytes(b'DVR1'+b'\0'*100)
            with self.assertRaises(ValueError):crypto.decrypt(p,Path(t)/'target',PASSWORD,'delivery')
if __name__=='__main__':unittest.main()
