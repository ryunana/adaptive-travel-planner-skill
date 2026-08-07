import json
import stat
import sys
import tempfile
import unittest
import warnings
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

    def test_getpass_warning_fails_without_writing_key(self):
        import getpass

        import setup_amap
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "config.json"
            def warned(_prompt):
                warnings.warn("echo fallback", getpass.GetPassWarning)
                return "fixture-super-secret"
            with mock.patch("setup_amap.getpass.getpass", side_effect=warned):
                result = setup_amap.configure(target)
            self.assertEqual(result["error"]["code"], "input_unavailable")
            self.assertFalse(target.exists())
            self.assertNotIn("fixture-super-secret", json.dumps(result))

    def test_corrupt_existing_config_is_preserved(self):
        import setup_amap
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "config.json"
            for original in (b'{"amap": invalid\xff', b'{"onboarding":[]}'):
                with self.subTest(original=original):
                    target.write_bytes(original)
                    with mock.patch("setup_amap.getpass.getpass", return_value="fixture-super-secret"):
                        result = setup_amap.configure(target)
                    self.assertEqual(result["error"]["code"], "configuration_invalid")
                    self.assertEqual(target.read_bytes(), original)

    def test_existing_custom_parent_permissions_are_preserved(self):
        import setup_amap
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "shared"
            parent.mkdir(mode=0o755)
            target = parent / "config.json"
            with mock.patch("setup_amap.getpass.getpass", return_value="fixture-super-secret"):
                result = setup_amap.configure(target)
            self.assertTrue(result["ok"])
            self.assertEqual(stat.S_IMODE(parent.stat().st_mode), 0o755)

    def test_do_not_ask_again_only_persists_preference(self):
        import setup_amap
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "config.json"
            existing = {"amap": {"enabled": True, "api_key": "fixture-secret"}, "extension": {"kept": True}}
            target.write_text(json.dumps(existing))
            with mock.patch("setup_amap.getpass.getpass") as prompt:
                result = setup_amap.configure(target, disable_offer_only=True)
            self.assertTrue(result["ok"])
            prompt.assert_not_called()
            saved = json.loads(target.read_text())
            self.assertEqual(saved["amap"], existing["amap"])
            self.assertEqual(saved["extension"], existing["extension"])
            self.assertFalse(saved["onboarding"]["offer_amap_setup"])
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)

    def test_default_parent_symlink_target_mode_is_preserved(self):
        import setup_amap
        with tempfile.TemporaryDirectory() as directory:
            shared = Path(directory) / "shared"
            shared.mkdir(mode=0o755)
            link = Path(directory) / "config-parent"
            link.symlink_to(shared, target_is_directory=True)
            target = link / "config.json"
            with mock.patch.object(setup_amap, "DEFAULT_CONFIG", target), mock.patch("setup_amap.getpass.getpass", return_value="fixture-secret"):
                result = setup_amap.configure(target)
            self.assertTrue(result["ok"])
            self.assertEqual(stat.S_IMODE(shared.stat().st_mode), 0o755)


if __name__ == "__main__":
    unittest.main()
