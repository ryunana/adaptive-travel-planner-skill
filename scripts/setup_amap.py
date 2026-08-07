#!/usr/bin/env python3
"""Interactively store an AMap Web Service key without exposing it."""
import getpass
import json
import os
import tempfile
from pathlib import Path

from travel_common import DEFAULT_CONFIG, JsonArgumentParser, emit, load_config


def configure(path=DEFAULT_CONFIG, offer_setup=True):
    path = Path(path)
    try:
        key = getpass.getpass("AMap Web Service API key (hidden): ").strip()
    except EOFError:
        return {"ok": False, "error": {"code": "input_unavailable", "message": "No interactive input is available; run this command in a terminal"}}
    if not key:
        return {"ok": False, "error": {"code": "missing_key", "message": "No key was provided"}}
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path.parent, 0o700)
        config = load_config(path)
        config["amap"] = {"enabled": True, "api_key": key}
        config.setdefault("onboarding", {})["offer_amap_setup"] = bool(offer_setup)
        fd, temporary = tempfile.mkstemp(prefix=".config-", suffix=".tmp", dir=str(path.parent))
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(config, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            os.chmod(path, 0o600)
        except BaseException:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise
        return {"ok": True, "configured": True, "path": str(path), "key_source": "file", "permissions": "0600"}
    except OSError as exc:
        return {"ok": False, "error": {"code": "config_write_failed", "message": str(exc)}}


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="configuration file path")
    parser.add_argument("--do-not-ask-again", action="store_true", help="disable future setup offers")
    args = parser.parse_args(argv)
    result = configure(args.config, offer_setup=not args.do_not_ask_again)
    return emit(result, 0 if result["ok"] else 1)


if __name__ == "__main__":
    raise SystemExit(main())
