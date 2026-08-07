import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        self.old = os.environ.pop("AMAP_API_KEY", None)
        self.tmp = tempfile.TemporaryDirectory()
        self.config = Path(self.tmp.name) / "config.json"

    def tearDown(self):
        if self.old is not None:
            os.environ["AMAP_API_KEY"] = self.old
        else:
            os.environ.pop("AMAP_API_KEY", None)
        self.tmp.cleanup()

    def test_no_configuration_is_installed_unconfigured(self):
        import check_capabilities
        result = check_capabilities.detect(config_path=self.config)
        self.assertEqual(result["amap"]["state"], "installed_but_unconfigured")
        self.assertFalse(result["amap"]["configured"])

    def test_file_configuration_is_configured_unverified(self):
        import check_capabilities
        self.config.write_text(json.dumps({"amap": {"enabled": True, "api_key": "fixture-secret"}}))
        result = check_capabilities.detect(config_path=self.config)
        self.assertEqual(result["amap"]["state"], "configured_but_unverified")
        self.assertEqual(result["amap"]["key_source"], "file")
        self.assertNotIn("fixture-secret", json.dumps(result))

    def test_environment_overrides_file(self):
        import check_capabilities
        self.config.write_text(json.dumps({"amap": {"enabled": True, "api_key": "file-secret"}}))
        os.environ["AMAP_API_KEY"] = "environment-secret"
        result = check_capabilities.detect(config_path=self.config)
        self.assertEqual(result["amap"]["key_source"], "environment")
        self.assertNotIn("secret", json.dumps(result))

    def test_corrupt_configuration_has_distinct_fail_closed_state(self):
        import check_capabilities
        self.config.write_bytes(b'{"amap": invalid\xff')
        result = check_capabilities.detect(config_path=self.config)
        self.assertFalse(result["ok"])
        self.assertEqual(result["amap"]["state"], "configuration_invalid")
        self.assertEqual(result["error"]["code"], "configuration_invalid")

    def test_numeric_and_blank_keys_are_not_configured(self):
        import check_capabilities
        for key in (123, "   "):
            with self.subTest(key=key):
                self.config.write_text(json.dumps({"amap": {"enabled": True, "api_key": key}}))
                result = check_capabilities.detect(config_path=self.config)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "configuration_invalid")


if __name__ == "__main__":
    unittest.main()
