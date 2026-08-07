import json
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
FIXTURES = ROOT / "tests" / "fixtures"
SECRET = "fixture-key-never-print"


class Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.payload


def payload(name):
    return (FIXTURES / name).read_bytes()


class AMapClientTests(unittest.TestCase):
    def client(self, name):
        import amap_cli
        self.seen = []
        def opener(request, timeout):
            self.seen.append((request.full_url, timeout))
            return Response(payload(name))
        return amap_cli.AMapClient(SECRET, timeout=3.5, opener=opener)

    def test_successful_geocode_uses_official_endpoint_and_redacts_key(self):
        result = self.client("amap_geocode_success.json").geocode("天安门", "北京")
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["geocodes"][0]["adcode"], "110101")
        url, timeout = self.seen[0]
        self.assertEqual(urlparse(url).path, "/v3/geocode/geo")
        self.assertEqual(parse_qs(urlparse(url).query)["key"], [SECRET])
        self.assertEqual(timeout, 3.5)
        self.assertNotIn(SECRET, json.dumps(result))

    def test_invalid_key_is_structured_and_redacted(self):
        result = self.client("amap_invalid_key.json").geocode("x")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_key")
        self.assertNotIn(SECRET, json.dumps(result))

    def test_quota_is_structured(self):
        result = self.client("amap_quota.json").weather("110000")
        self.assertEqual(result["error"]["code"], "quota_exceeded")

    def test_malformed_response_is_structured(self):
        result = self.client("amap_malformed.txt").geocode("x")
        self.assertEqual(result["error"]["code"], "malformed_response")

    def test_timeout_is_structured(self):
        import amap_cli
        def opener(request, timeout): raise TimeoutError("fixture timeout")
        result = amap_cli.AMapClient(SECRET, opener=opener).geocode("x")
        self.assertEqual(result["error"]["code"], "timeout")
        self.assertNotIn(SECRET, json.dumps(result))

    def test_route_and_weather_success(self):
        route = self.client("amap_route_success.json").route("116.1,39.1", "116.2,39.2")
        self.assertTrue(route["ok"])
        self.assertEqual(route["data"]["route"]["paths"][0]["tolls"], "5")
        weather = self.client("amap_weather_success.json").weather("110000")
        self.assertTrue(weather["ok"])
        self.assertEqual(weather["data"]["forecasts"][0]["city"], "北京市")


if __name__ == "__main__": unittest.main()
