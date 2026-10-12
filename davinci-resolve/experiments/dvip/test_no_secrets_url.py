import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[3]
WF = ROOT / ".github" / "workflows" / "experimentar-davinci-dvip.yml"
EXPERIMENTAL = ROOT / ".github" / "workflows" / "testar-mesa-software-sharing.yml"

class OneTimeOfficialUrlTests(unittest.TestCase):
    def test_url_is_workflow_input_not_embedded_in_git(self):
        src = WF.read_text()
        self.assertIn("installer_url_once:", src)
        self.assertIn("inputs.installer_url_once || secrets.DAVINCI_RESOLVE_LINUX_URL", src)
        self.assertEqual(src.count("inputs.installer_url_once || secrets.DAVINCI_RESOLVE_LINUX_URL"), 2)
        self.assertNotIn("Key-Pair-Id=", src)
        self.assertNotIn("Signature=", src)
        self.assertNotIn("Expires=", src)

    def test_synthetic_mode_requires_public_url_consent(self):
        src=EXPERIMENTAL.read_text()
        self.assertIn("inputs.installer_url_once == '' || inputs.accept_public_url", src)
        self.assertIn("installer_url_once: ${{ inputs.accept_public_url && inputs.installer_url_once || '' }}", src)

    def test_called_workflow_checkout_is_experimental(self):
        src=WF.read_text()
        self.assertEqual(src.count("ref: experiment/davinci-21-1-1-software-dvip"), 2)

    def test_workflow_files_valid_yaml_structure(self):
        for path in [WF, EXPERIMENTAL]:
            parsed=yaml.safe_load(path.read_text())
            self.assertIsInstance(parsed, dict)
            self.assertIn("jobs", parsed)

if __name__ == "__main__":
    unittest.main()
