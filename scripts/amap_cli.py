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
import http.client
import math
import re
from pathlib import Path
from urllib import error, parse, request

from travel_common import (
    DEFAULT_CONFIG,
    ConfigurationInvalid,
    JsonArgumentParser,
    _loads_strict,
    emit,
    get_api_key,
    positive_finite_float,
)

BASE_URL = "https://restapi.amap.com"
INVALID_KEY_CODES = {"10001", "10002", "10007"}
QUOTA_CODES = {"10003", "10004", "10010", "10019", "10020", "10021"}
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
ADCODE = re.compile(r"\d{6}")


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
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except TimeoutError:
            return self._error("timeout", "AMap request timed out")
        except error.URLError as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError):
                return self._error("timeout", "AMap request timed out")
            return self._error("network_error", "AMap request failed")
        except http.client.HTTPException:
            return self._error("network_error", "AMap response was interrupted")
        except OSError:
            return self._error("network_error", "AMap request failed")
        try:
            if len(raw) > MAX_RESPONSE_BYTES:
                return self._error("malformed_response", "AMap response exceeds the size limit")
            payload = _loads_strict(raw)
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
            return self._error(code, "AMap rejected the request")
        if path == "/v3/geocode/geo":
            geocodes = payload.get("geocodes")
            if not isinstance(geocodes, list) or any(not isinstance(item, dict) for item in geocodes):
                return self._error("malformed_response", "AMap geocode response has an invalid shape")
        if path == "/v3/direction/driving":
            route = payload.get("route")
            paths = route.get("paths") if isinstance(route, dict) else None
            if not isinstance(paths, list) or any(not isinstance(item, dict) for item in paths):
                return self._error("malformed_response", "AMap route response has an invalid shape")
        if path == "/v3/weather/weatherInfo":
            field = "forecasts" if params.get("extensions") == "all" else "lives"
            records = payload.get(field)
            if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
                return self._error("malformed_response", "AMap weather response has an invalid shape")
        return {"ok": True, "provider": "amap", "data": self._redact(payload)}

    def _redact(self, value):
        """Remove reflected configured-key substrings from bounded provider JSON."""
        if isinstance(value, str):
            return value.replace(self.api_key, "[REDACTED]")
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        if isinstance(value, dict):
            return {self._redact(key) if isinstance(key, str) else key: self._redact(item) for key, item in value.items()}
        return value

    @staticmethod
    def _error(code, message, **details):
        error_value = {"code": code, "message": message}
        error_value.update(details)
        return {"ok": False, "provider": "amap", "error": error_value}

    def geocode(self, address, city=None):
        if not isinstance(address, str) or not address.strip() or (city is not None and (not isinstance(city, str) or not city.strip())):
            return self._error("invalid_arguments", "Address and city must be non-empty text")
        params = {"address": address}
        if city:
            params["city"] = city
        return self._call("/v3/geocode/geo", params)

    def route(self, origin, destination):
        if not self._valid_coordinates(origin) or not self._valid_coordinates(destination):
            return self._error("invalid_arguments", "Route coordinates must be finite in-range lon,lat pairs")
        return self._call("/v3/direction/driving", {"origin": origin, "destination": destination, "extensions": "all"})

    def weather(self, city, extensions="all"):
        if not isinstance(city, str) or not ADCODE.fullmatch(city):
            return self._error("invalid_arguments", "Weather city must be a six-digit AMap adcode")
        return self._call("/v3/weather/weatherInfo", {"city": city, "extensions": extensions})

    @staticmethod
    def _valid_coordinates(value):
        if not isinstance(value, str):
            return False
        try:
            parts = value.split(",")
            if len(parts) != 2:
                return False
            longitude, latitude = (float(part) for part in parts)
        except ValueError:
            return False
        return math.isfinite(longitude) and math.isfinite(latitude) and -180 <= longitude <= 180 and -90 <= latitude <= 90


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="configuration file path")
    parser.add_argument("--timeout", type=positive_finite_float, default=10.0, help="network timeout in seconds")
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
    try:
        key, source = get_api_key(args.config)
    except ConfigurationInvalid:
        return emit({"ok": False, "error": {"code": "configuration_invalid", "message": "AMap configuration is invalid"}}, 2)
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
