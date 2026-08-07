import http.client
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
    def read(self, size=-1): return self.payload if size < 0 else self.payload[:size]


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

    def test_provider_cannot_reflect_key_in_success_or_error(self):
        import amap_cli
        success = json.dumps({"status": "1", "geocodes": [{"location": SECRET, SECRET: "x"}]}).encode()
        result = amap_cli.AMapClient(SECRET, opener=lambda request, timeout: Response(success)).geocode("x")
        self.assertTrue(result["ok"])
        self.assertNotIn(SECRET, json.dumps(result))
        failure = json.dumps({"status": "0", "infocode": SECRET, "info": SECRET}).encode()
        result = amap_cli.AMapClient(SECRET, opener=lambda request, timeout: Response(failure)).geocode("x")
        self.assertFalse(result["ok"])
        self.assertNotIn(SECRET, json.dumps(result))

    def test_provider_rejects_nonfinite_exponent_and_excessive_depth(self):
        import amap_cli
        for raw in (b'{"status":"1","geocodes":[{"x":1e9999}]}', b"[" * 2000 + b"]" * 2000):
            result = amap_cli.AMapClient(SECRET, opener=lambda request, timeout, raw=raw: Response(raw)).geocode("x")
            self.assertEqual(result["error"]["code"], "malformed_response")

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

    def test_incomplete_response_is_structured_and_redacted(self):
        import amap_cli
        class IncompleteResponse(Response):
            def read(self, size=-1):
                raise http.client.IncompleteRead(b"partial", 100)
        def opener(request, timeout):
            return IncompleteResponse(b"")
        result = amap_cli.AMapClient(SECRET, opener=opener).geocode("x")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "network_error")
        self.assertNotIn(SECRET, json.dumps(result))

    def test_route_and_weather_success(self):
        route = self.client("amap_route_success.json").route("116.1,39.1", "116.2,39.2")
        self.assertTrue(route["ok"])
        self.assertEqual(route["data"]["route"]["paths"][0]["tolls"], "5")
        weather = self.client("amap_weather_success.json").weather("110000")
        self.assertTrue(weather["ok"])
        self.assertEqual(weather["data"]["forecasts"][0]["city"], "北京市")

    def test_endpoint_payload_shapes_are_validated(self):
        import amap_cli
        cases = (
            ("geocode", {"status": "1"}),
            ("geocode", {"status": "1", "geocodes": "bad"}),
            ("route", {"status": "1", "route": {}}),
            ("route", {"status": "1", "route": {"paths": "bad"}}),
            ("weather", {"status": "1", "forecasts": {}}),
        )
        for method, value in cases:
            with self.subTest(method=method, value=value):
                raw = json.dumps(value).encode()
                client = amap_cli.AMapClient(SECRET, opener=lambda request, timeout, raw=raw: Response(raw))
                if method == "geocode":
                    result = client.geocode("x")
                elif method == "route":
                    result = client.route("1,1", "2,2")
                else:
                    result = client.weather("110000")
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "malformed_response")

        client = amap_cli.AMapClient(SECRET, opener=lambda request, timeout: Response(b'{"status":"1","geocodes":NaN}'))
        self.assertEqual(client.geocode("x")["error"]["code"], "malformed_response")

    def test_provider_response_size_boundary(self):
        import amap_cli
        valid = json.dumps({"status": "1", "geocodes": []}).encode()
        padding = b" " * (amap_cli.MAX_RESPONSE_BYTES - len(valid))
        below = amap_cli.AMapClient(SECRET, opener=lambda request, timeout: Response(valid + padding)).geocode("x")
        above = amap_cli.AMapClient(SECRET, opener=lambda request, timeout: Response(valid + padding + b" ")).geocode("x")
        self.assertTrue(below["ok"])
        self.assertEqual(above["error"]["code"], "malformed_response")

    def test_local_argument_validation_prevents_network_calls(self):
        import amap_cli
        calls = []
        client = amap_cli.AMapClient(SECRET, opener=lambda request, timeout: calls.append(request))
        cases = (
            lambda: client.geocode(" "),
            lambda: client.route("NaN,1", "2,2"),
            lambda: client.route("181,1", "2,2"),
            lambda: client.weather("abc"),
        )
        for invoke in cases:
            with self.subTest(invoke=invoke):
                result = invoke()
                self.assertEqual(result["error"]["code"], "invalid_arguments")
        self.assertEqual(calls, [])


if __name__ == "__main__": unittest.main()
