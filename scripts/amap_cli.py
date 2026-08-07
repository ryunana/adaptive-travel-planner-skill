#!/usr/bin/env python3
"""Call selected official AMap Web Service endpoints and emit JSON.

Official contracts rechecked 2026-08-07:
https://lbs.amap.com/api/webservice/guide/api/georegeo
https://lbs.amap.com/api/webservice/guide/api/direction
https://lbs.amap.com/api/webservice/guide/api/weatherinfo
https://lbs.amap.com/api/webservice/guide/create-project/get-key
https://lbs.amap.com/api/webservice/guide/tools/flowlevel
https://lbs.amap.com/pages/terms/

The API requires a Web Service key. Quotas/QPS are account/product specific and
must be read from the pricing page and authenticated console, not hard-coded.
"""
import json
import socket
from pathlib import Path
from urllib import error, parse, request

from travel_common import DEFAULT_CONFIG, JsonArgumentParser, emit, get_api_key

BASE_URL = "https://restapi.amap.com"
INVALID_KEY_CODES = {"10001", "10002", "10007"}
QUOTA_CODES = {"10003", "10004", "10010", "10019", "10020", "10021"}


class AMapClient:
    def __init__(self, api_key, timeout=10.0, opener=request.urlopen):
        self.api_key = api_key
        self.timeout = timeout
        self.opener = opener

    def _call(self, path, params):
        query = dict(params)
        query.update({"key": self.api_key, "output": "JSON"})
        url = BASE_URL + path + "?" + parse.urlencode(query)
        req = request.Request(url, headers={"User-Agent": "adaptive-travel-planner/2"})
        try:
            with self.opener(req, timeout=self.timeout) as response:
                raw = response.read()
        except (TimeoutError, socket.timeout):
            return self._error("timeout", "AMap request timed out")
        except error.URLError as exc:
            if isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
                return self._error("timeout", "AMap request timed out")
            return self._error("network_error", "AMap request failed")
        except OSError:
            return self._error("network_error", "AMap request failed")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError, AttributeError):
            return self._error("malformed_response", "AMap returned non-JSON data")
        if not isinstance(payload, dict) or "status" not in payload:
            return self._error("malformed_response", "AMap response lacks required status")
        if str(payload.get("status")) != "1":
            infocode = str(payload.get("infocode", ""))
            if infocode in INVALID_KEY_CODES:
                code = "invalid_key"
            elif infocode in QUOTA_CODES:
                code = "quota_exceeded"
            else:
                code = "provider_error"
            return self._error(code, "AMap rejected the request", infocode=infocode)
        return {"ok": True, "provider": "amap", "data": payload}

    @staticmethod
    def _error(code, message, **details):
        error_value = {"code": code, "message": message}
        error_value.update(details)
        return {"ok": False, "provider": "amap", "error": error_value}

    def geocode(self, address, city=None):
        params = {"address": address}
        if city:
            params["city"] = city
        return self._call("/v3/geocode/geo", params)

    def route(self, origin, destination):
        return self._call("/v3/direction/driving", {"origin": origin, "destination": destination, "extensions": "all"})

    def weather(self, city, extensions="all"):
        return self._call("/v3/weather/weatherInfo", {"city": city, "extensions": extensions})


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="configuration file path")
    parser.add_argument("--timeout", type=float, default=10.0, help="network timeout in seconds")
    sub = parser.add_subparsers(dest="command", required=True)
    geo = sub.add_parser("geocode", help="geocode an address")
    geo.add_argument("address")
    geo.add_argument("--city")
    route = sub.add_parser("route", help="calculate a driving route")
    route.add_argument("origin", help="longitude,latitude")
    route.add_argument("destination", help="longitude,latitude")
    weather = sub.add_parser("weather", help="query city baseline weather")
    weather.add_argument("city", help="AMap adcode")
    weather.add_argument("--extensions", choices=("base", "all"), default="all")
    args = parser.parse_args(argv)
    key, source = get_api_key(args.config)
    if not key:
        return emit({"ok": False, "error": {"code": "missing_key", "message": "Configure an AMap Web Service key first"}}, 2)
    client = AMapClient(key, args.timeout)
    if args.command == "geocode":
        result = client.geocode(args.address, args.city)
    elif args.command == "route":
        result = client.route(args.origin, args.destination)
    else:
        result = client.weather(args.city, args.extensions)
    result["key_source"] = source
    return emit(result, 0 if result["ok"] else 1)


if __name__ == "__main__":
    raise SystemExit(main())
