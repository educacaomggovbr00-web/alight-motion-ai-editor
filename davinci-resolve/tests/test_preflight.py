import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'preflight.py';s=importlib.util.spec_from_file_location('preflight',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class PreflightTests(unittest.TestCase):
 def test_missing_gpu_blocks(self):
  self.assertEqual(m.evaluate('x86_64',False,True,True)['state'],'bloqueado')
 def test_no_claim_of_functioning_from_devices(self):
  r=m.evaluate('x86_64',True,True,True)
  self.assertEqual(r['state'],'experimental');self.assertFalse(r['resolveStartedProven']);self.assertFalse(r['exportProven'])
 def test_missing_desktop_and_application(self):
  self.assertEqual(len(m.evaluate('x86_64',True,False,False)['blockers']),2)
 def test_arm_not_claimed_supported(self):
  self.assertEqual(m.evaluate('aarch64',True,True,True)['state'],'bloqueado')
