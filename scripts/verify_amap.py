#!/usr/bin/env python3
"""Verify AMap geocoding, driving-route, and baseline-weather stages."""
import math
from pathlib import Path

from amap_cli import AMapClient
from travel_common import (
    DEFAULT_CONFIG,
    JsonArgumentParser,
    emit,
    get_api_key,
    positive_finite_float,
)


def _failed(stage, result, completed):
    return {"ok": False, "state": "failed", "failed_stage": stage, "completed_stages": completed, "error": result.get("error", {"code": "verification_failed", "message": "Verification failed"})}


def verify(client):
    completed = []
    geocode = client.geocode("天安门", "北京")
    if not geocode.get("ok"):
        return _failed("geocode", geocode, completed)
    try:
        item = geocode["data"]["geocodes"][0]
        origin = item["location"]
        adcode = item["adcode"]
    except (KeyError, IndexError, TypeError):
        return _failed("geocode", {"error": {"code": "malformed_response", "message": "Geocode response lacks location/adcode"}}, completed)
    try:
        longitude, latitude = (float(value) for value in origin.split(","))
        if not math.isfinite(longitude) or not math.isfinite(latitude) or not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise ValueError("coordinates out of range")
    except (AttributeError, TypeError, ValueError):
        return _failed("geocode", {"error": {"code": "malformed_response", "message": "Geocode response location must be valid lon,lat"}}, completed)
    completed.append("geocode")
    destination = "{:.6f},{:.6f}".format(longitude + 0.01, latitude)
    route = client.route(origin, destination)
    if not route.get("ok"):
        return _failed("route", route, completed)
    try:
        route["data"]["route"]["paths"][0]
    except (KeyError, IndexError, TypeError):
        return _failed("route", {"error": {"code": "malformed_response", "message": "Route response lacks paths"}}, completed)
    completed.append("route")

    weather = client.weather(adcode)
    if not weather.get("ok"):
        return _failed("weather", weather, completed)
    data = weather.get("data", {})
    if not data.get("forecasts") and not data.get("lives"):
        return _failed("weather", {"error": {"code": "malformed_response", "message": "Weather response lacks observations/forecasts"}}, completed)
    completed.append("weather")
    return {"ok": True, "state": "verified_working", "completed_stages": completed}


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--timeout", type=positive_finite_float, default=10.0)
    args = parser.parse_args(argv)
    key, source = get_api_key(args.config)
    if not key:
        return emit({"ok": False, "state": "installed_but_unconfigured", "failed_stage": "configuration", "error": {"code": "missing_key", "message": "Configure an AMap Web Service key first"}}, 2)
    result = verify(AMapClient(key, args.timeout))
    result["key_source"] = source
    return emit(result, 0 if result["ok"] else 1)


if __name__ == "__main__":
    raise SystemExit(main())
