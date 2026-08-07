import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class SetupTests(unittest.TestCase):
    def test_atomic_user_only_configuration_and_no_secret_output(self):
        import setup_amap
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "nested" / "config.json"
            with mock.patch("setup_amap.getpass.getpass", return_value="fixture-super-secret"):
                result = setup_amap.configure(target, offer_setup=False)
            self.assertTrue(result["ok"])
            self.assertNotIn("fixture-super-secret", json.dumps(result))
            config = json.loads(target.read_text())
            self.assertEqual(config["amap"]["api_key"], "fixture-super-secret")
            self.assertFalse(config["onboarding"]["offer_amap_setup"])
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)
            self.assertEqual(list(target.parent.glob("*.tmp")), [])

    def test_empty_key_is_structured_failure(self):
        import setup_amap
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "config.json"
            with mock.patch("setup_amap.getpass.getpass", return_value=""):
                result = setup_amap.configure(target)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "missing_key")
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
