#!/usr/bin/env python3
"""Shared configuration, CLI, and JSON helpers for travel-planner scripts."""
import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_CONFIG = Path.home() / ".config" / "adaptive-travel-planner" / "config.json"


class JsonArgumentParser(argparse.ArgumentParser):
    """Keep command-line usage errors on the scripts' JSON output contract."""

    def error(self, message):
        emit({"ok": False, "error": {"code": "invalid_arguments", "message": message}})
        raise SystemExit(2)


def load_config(path=None):
    path = Path(path) if path else DEFAULT_CONFIG
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def get_api_key(config_path=None):
    env_key = os.environ.get("AMAP_API_KEY")
    if env_key:
        return env_key, "environment"
    amap = load_config(config_path).get("amap", {})
    key = amap.get("api_key") if isinstance(amap, dict) and amap.get("enabled", True) else None
    return (key, "file") if key else (None, None)


def read_json(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def emit(value, exit_code=0):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return exit_code
