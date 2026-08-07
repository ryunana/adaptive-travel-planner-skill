import contextlib
import io
import json
import math
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
            check=False,
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

    def test_argument_errors_never_echo_raw_values(self):
        canary = "CANARY_NOT_A_REAL_KEY_1234567890"
        cases = (
            ("setup_amap", ("--config", canary, "--bad")),
            ("amap_cli", ("--api-key", canary)),
            ("verify_amap", ("--timeout", canary)),
        )
        for name, args in cases:
            with self.subTest(name=name):
                result = self.run_script(name, *args, input_text="")
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(canary, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["error"]["code"], "invalid_arguments")

        for name in NAMES:
            with self.subTest(name=name, generic=True):
                result = self.run_script(name, "--" + canary, input_text="")
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(canary, result.stdout + result.stderr)

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

    def test_reported_nested_shape_regressions_remain_structured_json(self):
        cases = (
            ("score_destinations", '{"candidates":[{"name":"A","hard_gates":[{"state":[],"evidence_status":"verified"}],"dimensions":{}}]}'),
            ("score_destinations", '{"candidates":[{"name":"A","hard_gates":[{"state":"pass","evidence_status":[]}],"dimensions":{}}]}'),
            ("score_destinations", '{"candidates":[{"name":"A","hard_gates":[],"dimensions":{"preference_fit":{"score":4,"evidence_status":[]}}}]}'),
            ("score_destinations", '{"weights":{"preference_fit":NaN,"seasonal_weather_fit":20,"core_experience_density":15,"access_route_friction":10,"crowd_ticket_friction":10,"bad_weather_resilience":10,"composite_load_fit":5,"current_value_for_money":5},"candidates":[]}'),
            ("validate_itinerary", '{"start_date":"2026-08-07","end_date":"2026-08-07","hotel_nights":0,"days":[{"date":"2026-08-07","core_activities":null}],"route":[]}'),
            ("validate_itinerary", '{"start_date":"2026-08-07","end_date":"2026-08-07","hotel_nights":0,"days":[{"date":"2026-08-07","core_activities":[]}],"route":[],"dynamic_claims":[{"status":[]}]}'),
        )
        for name, value in cases:
            with self.subTest(name=name):
                result = self.run_script(name, "-", input_text=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")
                payload = json.loads(result.stdout, parse_constant=lambda value: self.fail(value))
                self.assertFalse(payload["ok"])

    def test_json_consumers_reject_nonstandard_constants(self):
        for name, value in (
            ("score_destinations", '{"minimum_viable_days":NaN,"candidates":[]}'),
            ("validate_itinerary", '{"start_date":"2026-08-07","end_date":"2026-08-07","hotel_nights":NaN,"days":[],"route":[]}'),
        ):
            with self.subTest(name=name):
                result = self.run_script(name, "-", input_text=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")
                payload = json.loads(result.stdout, parse_constant=lambda constant: self.fail(constant))
                self.assertFalse(payload["ok"])

    def test_json_file_input_size_boundary(self):
        sys.path.insert(0, str(SCRIPTS))
        import travel_common
        with tempfile.TemporaryDirectory() as directory:
            below = Path(directory) / "below.json"
            above = Path(directory) / "above.json"
            prefix = b'{"padding":"'
            suffix = b'"}'
            below.write_bytes(prefix + (b"a" * (travel_common.MAX_JSON_BYTES - len(prefix) - len(suffix))) + suffix)
            above.write_bytes(below.read_bytes() + b" ")
            accepted = self.run_script("validate_itinerary", str(below))
            rejected = self.run_script("validate_itinerary", str(above))
        self.assertNotEqual(accepted.returncode, 0)
        self.assertNotEqual(json.loads(accepted.stdout)["issues"][0]["code"], "input_too_large")
        self.assertEqual(json.loads(rejected.stdout)["issues"][0]["code"], "input_too_large")

    def test_strict_emitter_converts_nonfinite_output_to_json_error(self):
        sys.path.insert(0, str(SCRIPTS))
        import travel_common
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = travel_common.emit({"ok": True, "value": math.nan})
        self.assertNotEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue())["error"]["code"], "serialization_error")

    def test_network_timeouts_must_be_positive_and_finite(self):
        env = os.environ.copy()
        env.pop("AMAP_API_KEY", None)
        with tempfile.TemporaryDirectory() as directory:
            config = str(Path(directory) / "missing.json")
            for name, suffix in (("amap_cli", ("geocode", "x")), ("verify_amap", ())):
                for value in ("0", "-1", "NaN", "Infinity", "-Infinity"):
                    with self.subTest(name=name, value=value):
                        result = self.run_script(name, "--config", config, "--timeout", value, *suffix, env=env)
                        self.assertEqual(result.returncode, 2)
                        self.assertEqual(result.stderr, "")
                        payload = json.loads(result.stdout)
                        self.assertEqual(payload["error"]["code"], "invalid_arguments")

    def test_positive_finite_network_timeout_remains_accepted(self):
        env = os.environ.copy()
        env.pop("AMAP_API_KEY", None)
        with tempfile.TemporaryDirectory() as directory:
            config = str(Path(directory) / "missing.json")
            for name, suffix in (("amap_cli", ("geocode", "x")), ("verify_amap", ())):
                with self.subTest(name=name):
                    result = self.run_script(name, "--config", config, "--timeout", "0.25", *suffix, env=env)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(json.loads(result.stdout)["error"]["code"], "missing_key")


if __name__ == "__main__": unittest.main()
