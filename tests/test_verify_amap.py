import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
FIXTURES = ROOT / "tests" / "fixtures"


class FakeClient:
    def __init__(self, fail=None, geocode_data=None):
        self.fail = fail
        self.geocode_data = geocode_data
        self.calls = []
    def _result(self, stage, data):
        self.calls.append(stage)
        if self.fail == stage:
            return {"ok": False, "error": {"code": "fixture_failure", "message": "failed"}}
        return {"ok": True, "data": data}
    def geocode(self, address, city=None):
        data = self.geocode_data or {"geocodes": [{"location": "116.397,39.908", "adcode": "110101"}]}
        return self._result("geocode", data)
    def route(self, origin, destination):
        return self._result("route", {"route": {"paths": [{"distance": "1"}]}})
    def weather(self, city):
        return self._result("weather", {"forecasts": [{"city": "北京"}]})


class VerifyTests(unittest.TestCase):
    def test_all_three_verification_stages_pass(self):
        import verify_amap
        client = FakeClient()
        result = verify_amap.verify(client)
        self.assertTrue(result["ok"])
        self.assertEqual(client.calls, ["geocode", "route", "weather"])
        self.assertEqual(result["state"], "verified_working")

    def test_exact_failed_stage_stops_verification(self):
        import verify_amap
        client = FakeClient(fail="route")
        result = verify_amap.verify(client)
        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_stage"], "route")
        self.assertEqual(client.calls, ["geocode", "route"])

    def test_malformed_geocode_location_is_structured_and_stops(self):
        import verify_amap
        fixture = json.loads((FIXTURES / "amap_geocode_malformed_location.json").read_text())
        client = FakeClient(geocode_data={"geocodes": fixture["geocodes"]})
        result = verify_amap.verify(client)
        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_stage"], "geocode")
        self.assertEqual(result["error"]["code"], "malformed_response")
        self.assertEqual(result["completed_stages"], [])
        self.assertEqual(client.calls, ["geocode"])

    def test_verifier_requires_usable_route_and_weather_records(self):
        import verify_amap
        class ShapeClient(FakeClient):
            def __init__(self, route_data, weather_data):
                super().__init__()
                self.route_data = route_data
                self.weather_data = weather_data
            def route(self, origin, destination):
                return self._result("route", self.route_data)
            def weather(self, city):
                return self._result("weather", self.weather_data)
        cases = (
            ({"route": {"paths": [None]}}, {"forecasts": [{"city": "x"}]}),
            ({"route": {"paths": [{}]}}, {"forecasts": "bad"}),
            ({"route": {"paths": [{}]}}, {"forecasts": []}),
        )
        for route_data, weather_data in cases:
            with self.subTest(route_data=route_data, weather_data=weather_data):
                result = verify_amap.verify(ShapeClient(route_data, weather_data))
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "malformed_response")


if __name__ == "__main__": unittest.main()
