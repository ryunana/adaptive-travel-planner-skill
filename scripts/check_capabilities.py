#!/usr/bin/env python3
"""Report local travel-planner capability states as JSON."""
import shutil
import sys
from pathlib import Path

from travel_common import (
    DEFAULT_CONFIG,
    ConfigurationInvalid,
    JsonArgumentParser,
    emit,
    get_api_key,
)


def detect(config_path=None):
    try:
        key, source = get_api_key(config_path)
    except ConfigurationInvalid:
        return {
            "ok": False,
            "error": {"code": "configuration_invalid", "message": "AMap configuration is invalid"},
            "amap": {"state": "configuration_invalid", "installed": True, "configured": False, "verified": False, "key_source": None},
        }
    amap_state = "configured_but_unverified" if key else "installed_but_unconfigured"
    return {
        "ok": True,
        "web_search": {"state": "unknown", "note": "host capability must be reported by the calling agent"},
        "interactive_browser": {"state": "unknown", "note": "host capability must be reported by the calling agent"},
        "python": {"state": "available", "version": ".".join(map(str, sys.version_info[:3])), "executable_available": bool(shutil.which("python3"))},
        "amap": {"state": amap_state, "installed": True, "configured": bool(key), "verified": False, "key_source": source},
    }


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="configuration file path")
    args = parser.parse_args(argv)
    result = detect(args.config)
    return emit(result, 0 if result["ok"] else 1)


if __name__ == "__main__":
    raise SystemExit(main())
