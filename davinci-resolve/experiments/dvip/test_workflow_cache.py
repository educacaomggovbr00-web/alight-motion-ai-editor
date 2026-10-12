"""Static YAML safety checks: prevent an invalid cache workflow from reaching Actions."""
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[3] / ".github" / "workflows"
FILES = (
    "cache-installer-davinci.yml",
    "experimentar-davinci-dvip.yml",
    "testar-mesa-software-sharing.yml",
)

def walk(node, path="root"):
    if isinstance(node, yaml.MappingNode):
        seen = set()
        for key, value in node.value:
            name = key.value
            if name in seen:
                raise ValueError("Duplicate YAML key at " + path + "." + name)
            seen.add(name)
            walk(value, path + "." + name)
    elif isinstance(node, yaml.SequenceNode):
        for idx, child in enumerate(node.value):
            walk(child, path + "[" + str(idx) + "]")

class WorkflowSafety(unittest.TestCase):
    def test_workflow_yaml_has_no_duplicate_keys(self):
        for name in FILES:
            with self.subTest(name=name):
                source = (ROOT / name).read_text()
                document = yaml.compose(source)
                self.assertIsNotNone(document)
                walk(document)

    def test_encrypted_installation_is_the_only_cached_file(self):
        source = (ROOT / "cache-installer-davinci.yml").read_text()
        self.assertIn("installer_cache.py encrypt", source)
        self.assertIn("installer_cache.py decrypt", source)
        self.assertNotIn("cache/save@v4\n        with:\n          path: ${{ runner.temp }}/davinci-private", source)
        self.assertIn("DAVINCI_INSTALLER_CACHE_PASSWORD", source)

    def test_preflight_supports_expired_url_with_existing_cache(self):
        source = (ROOT / "experimentar-davinci-dvip.yml").read_text()
        self.assertIn("lookup-only: true", source)
        self.assertIn("INSTALLER_CACHE_HIT", source)
        self.assertIn("installer_cache.py decrypt", source)

if __name__ == "__main__":
    unittest.main()
