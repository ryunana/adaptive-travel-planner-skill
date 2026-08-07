#!/usr/bin/env python3
"""Shared configuration, CLI, and JSON helpers for travel-planner scripts."""
import argparse
import json
import math
import os
import sys
from pathlib import Path

DEFAULT_CONFIG = Path.home() / ".config" / "adaptive-travel-planner" / "config.json"
MAX_JSON_BYTES = 1024 * 1024
MAX_JSON_DEPTH = 100


class TravelInputError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class ConfigurationInvalid(TravelInputError):
    def __init__(self):
        super().__init__("configuration_invalid", "AMap configuration is invalid")


class JsonArgumentParser(argparse.ArgumentParser):
    """Keep command-line usage errors on the scripts' JSON output contract."""

    def error(self, message):
        emit({"ok": False, "error": {"code": "invalid_arguments", "message": "Invalid command-line arguments"}})
        raise SystemExit(2)


def positive_finite_float(value):
    """Parse a strictly positive finite command-line number."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be positive and finite")
    return number


def load_config(path=None):
    path = Path(path) if path else DEFAULT_CONFIG
    if not path.exists():
        return {}
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError("configuration exceeds size limit")
        value = _loads_strict(raw)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ConfigurationInvalid() from exc
    if not isinstance(value, dict):
        raise ConfigurationInvalid()
    if "amap" in value and not isinstance(value["amap"], dict):
        raise ConfigurationInvalid()
    if "onboarding" in value and not isinstance(value["onboarding"], dict):
        raise ConfigurationInvalid()
    amap = value.get("amap", {})
    onboarding = value.get("onboarding", {})
    if "enabled" in amap and not isinstance(amap["enabled"], bool):
        raise ConfigurationInvalid()
    if "api_key" in amap and (not isinstance(amap["api_key"], str) or not amap["api_key"].strip()):
        raise ConfigurationInvalid()
    if "offer_amap_setup" in onboarding and not isinstance(onboarding["offer_amap_setup"], bool):
        raise ConfigurationInvalid()
    return value


def get_api_key(config_path=None):
    env_key = os.environ.get("AMAP_API_KEY")
    if env_key is not None:
        if not env_key.strip():
            return None, None
        return env_key.strip(), "environment"
    path = Path(config_path) if config_path else DEFAULT_CONFIG
    config = load_config(path)
    amap = config.get("amap", {})
    if not isinstance(amap, dict):
        raise ConfigurationInvalid()
    key = amap.get("api_key") if amap.get("enabled", True) else None
    if key is None:
        return None, None
    if not isinstance(key, str) or not key.strip():
        raise ConfigurationInvalid()
    if os.name == "posix":
        try:
            if path.stat().st_mode & 0o077:
                raise ConfigurationInvalid()
        except OSError as exc:
            raise ConfigurationInvalid() from exc
    return key.strip(), "file"


def read_json(path):
    if path == "-":
        raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
    else:
        try:
            with open(path, "rb") as handle:
                raw = handle.read(MAX_JSON_BYTES + 1)
        except OSError as exc:
            raise TravelInputError("input_unreadable", "JSON input file could not be read") from exc
    if len(raw) > MAX_JSON_BYTES:
        raise TravelInputError("input_too_large", f"JSON input exceeds {MAX_JSON_BYTES} bytes")
    return _loads_strict(raw)


def _reject_constant(value):
    raise ValueError(f"non-standard JSON constant: {value}")


def _loads_strict(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        value = json.loads(raw, parse_constant=_reject_constant)
    except RecursionError as exc:
        raise ValueError("JSON nesting exceeds limit") from exc
    validate_json_value(value)
    return value


def validate_json_value(value, max_depth=MAX_JSON_DEPTH):
    """Reject non-finite floats and excessive container nesting iteratively."""
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        if isinstance(current, float) and not math.isfinite(current):
            raise ValueError("JSON contains a non-finite number")
        if isinstance(current, dict):
            if depth >= max_depth:
                raise ValueError("JSON nesting exceeds limit")
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            if depth >= max_depth:
                raise ValueError("JSON nesting exceeds limit")
            stack.extend((item, depth + 1) for item in current)


def emit(value, exit_code=0):
    try:
        output = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        output = json.dumps({"ok": False, "error": {"code": "serialization_error", "message": "Result is not strict JSON"}}, sort_keys=True)
        exit_code = exit_code or 1
    print(output)
    return exit_code
