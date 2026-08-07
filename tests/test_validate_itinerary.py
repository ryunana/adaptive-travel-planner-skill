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


if __name__ == "__main__": unittest.main()
