import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
FIXTURES = ROOT / "tests" / "fixtures"


def load(name): return json.loads((FIXTURES / name).read_text())


class ItineraryTests(unittest.TestCase):
    def codes(self, name):
        import validate_itinerary
        return {issue["code"] for issue in validate_itinerary.validate(load(name))["issues"]}

    def test_valid_itinerary(self):
        import validate_itinerary
        result = validate_itinerary.validate(load("itinerary_valid.json"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["issues"], [])

    def test_date_and_hotel_night_mismatch(self):
        codes = self.codes("itinerary_date_mismatch.json")
        self.assertIn("hotel_nights_mismatch", codes)
        self.assertIn("day_count_mismatch", codes)

    def test_core_activity_overload(self):
        self.assertIn("core_activity_overload", self.codes("itinerary_overload.json"))

    def test_route_backtracking(self):
        self.assertIn("route_backtracking", self.codes("itinerary_backtracking.json"))

    def test_unsupported_dynamic_claim(self):
        self.assertIn("unsupported_dynamic_claim", self.codes("itinerary_unsupported_claim.json"))

    def test_core_activities_must_be_an_array(self):
        import validate_itinerary
        for value in (None, "activity", {}):
            with self.subTest(value=value):
                payload = load("itinerary_valid.json")
                payload["days"][0]["core_activities"] = value
                codes = {item["code"] for item in validate_itinerary.validate(payload)["issues"]}
                self.assertIn("invalid_core_activities", codes)

    def test_dynamic_claim_fields_require_valid_strings(self):
        import validate_itinerary
        cases = (
            ("status", [], "evidence_status_invalid"),
            ("source", [], "evidence_source_invalid"),
            ("source", "   ", "evidence_source_invalid"),
            ("queried_at", {}, "evidence_query_time_invalid"),
            ("queried_at", "", "evidence_query_time_invalid"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field, value=value):
                payload = load("itinerary_valid.json")
                payload["dynamic_claims"] = [{
                    "status": "verified", "value": "open", "source": "official", "queried_at": "2026-08-07T12:00:00Z"
                }]
                payload["dynamic_claims"][0][field] = value
                codes = {item["code"] for item in validate_itinerary.validate(payload)["issues"]}
                self.assertIn(expected, codes)

    def test_boolean_activity_limit_is_invalid(self):
        import validate_itinerary
        payload = load("itinerary_valid.json")
        payload["max_core_activities_per_day"] = True
        codes = {item["code"] for item in validate_itinerary.validate(payload)["issues"]}
        self.assertIn("load_limit_invalid", codes)


if __name__ == "__main__": unittest.main()
