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
    return value


def get_api_key(config_path=None):
    env_key = os.environ.get("AMAP_API_KEY")
    if env_key is not None:
        if not env_key.strip():
            return None, None
        return env_key.strip(), "environment"
    amap = load_config(config_path).get("amap", {})
    if not isinstance(amap, dict):
        raise ConfigurationInvalid()
    key = amap.get("api_key") if amap.get("enabled", True) else None
    if key is None:
        return None, None
    if not isinstance(key, str) or not key.strip():
        raise ConfigurationInvalid()
    return key.strip(), "file"


def read_json(path):
    if path == "-":
        raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
    else:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise TravelInputError("input_too_large", f"JSON input exceeds {MAX_JSON_BYTES} bytes")
    return _loads_strict(raw)


def _reject_constant(value):
    raise ValueError(f"non-standard JSON constant: {value}")


def _loads_strict(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw, parse_constant=_reject_constant)


def emit(value, exit_code=0):
    try:
        output = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError):
        output = json.dumps({"ok": False, "error": {"code": "serialization_error", "message": "Result is not strict JSON"}}, sort_keys=True)
        exit_code = exit_code or 1
    print(output)
    return exit_code
