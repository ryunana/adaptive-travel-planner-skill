import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
NAMES = ["check_capabilities", "setup_amap", "amap_cli", "verify_amap", "score_destinations", "validate_itinerary"]


class CliContractTests(unittest.TestCase):
    def run_script(self, name, *args, env=None, input_text=None):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / (name + ".py")), *args],
            cwd=ROOT,
            env=env,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10,
        )

    def test_all_six_scripts_have_help(self):
        for name in NAMES:
            with self.subTest(name=name):
                result = self.run_script(name, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)

    def test_capability_command_emits_json_without_key(self):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()
            env.pop("AMAP_API_KEY", None)
            result = self.run_script("check_capabilities", "--config", str(Path(directory) / "missing.json"), env=env)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_network_commands_fail_as_json_without_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            config = str(Path(directory) / "missing.json")
            env = os.environ.copy()
            env.pop("AMAP_API_KEY", None)
            for name, args in (("amap_cli", ("--config", config, "geocode", "x")), ("verify_amap", ("--config", config))):
                with self.subTest(name=name):
                    result = self.run_script(name, *args, env=env)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(json.loads(result.stdout)["error"]["code"], "missing_key")

    def test_argument_errors_are_structured_json(self):
        for name in NAMES:
            with self.subTest(name=name):
                result = self.run_script(name, "--definitely-invalid-option", input_text="")
                self.assertEqual(result.returncode, 2)
                payload = json.loads(result.stdout)
                self.assertFalse(payload["ok"])
                self.assertEqual(payload["error"]["code"], "invalid_arguments")

    def test_no_argument_results_are_structured_json(self):
        for name in NAMES:
            with self.subTest(name=name):
                result = self.run_script(name, input_text="")
                payload = json.loads(result.stdout)
                self.assertIn("ok", payload)

    def test_json_consumers_reject_malformed_shapes_as_json(self):
        cases = (
            ("score_destinations", "[]"),
            ("score_destinations", '{"candidates":[null]}'),
            ("validate_itinerary", "[]"),
            ("validate_itinerary", '{"days":[null],"start_date":"x","end_date":"x"}'),
        )
        for name, value in cases:
            with self.subTest(name=name, value=value):
                result = self.run_script(name, "-", input_text=value)
                self.assertNotEqual(result.returncode, 0)
                payload = json.loads(result.stdout)
                self.assertFalse(payload["ok"])


if __name__ == "__main__": unittest.main()
