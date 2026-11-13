#!/usr/bin/env python3
"""Prepare upstream Gluetun's private native control role; no provider restart.

The host volume is already mounted as /gluetun, and the official Gluetun
process loads the role config at startup. No credential is ever printed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import tomllib

TARGET = Path("/var/lib/network-v2/gluetun/auth/config.toml")
READ_ROUTES = (
    "GET /v1/version", "GET /v1/vpn/status",
    "GET /v1/publicip/ip", "GET /v1/updater/status",
    "GET /v1/dns/status",
)
CHANGE_ROUTES = ("GET /v1/vpn/settings", "PUT /v1/vpn/settings")


def rendered(token: str) -> str:
    if len(token) < 28 or not token.isascii() or '"' in token or "\\" in token:
        raise ValueError("Unsupported native Gluetun API key encoding")
    config = (
        '[[roles]]\n'
        'name = "ordivon-public-status"\n'
        'auth = "none"\n'
        'routes = ' + json.dumps(list(READ_ROUTES)) + '\n\n'
        '[[roles]]\n'
        'name = "ordivon-native-country-switch"\n'
        'auth = "apikey"\n'
        'apikey = ' + json.dumps(token) + '\n'
        'routes = ' + json.dumps(list(CHANGE_ROUTES)) + '\n'
    )
    assert_role_contract(config)
    return config


def assert_role_contract(contents: str) -> dict:
    roles = tomllib.loads(contents).get("roles")
    if not isinstance(roles, list) or len(roles) != 2:
        raise ValueError("Unexpected upstream Gluetun role count")
    public, admin = roles
    if (public.get("name") != "ordivon-public-status" or
        public.get("auth") != "none" or
        set(public.get("routes", [])) != set(READ_ROUTES)):
        raise ValueError("Unexpected Gluetun public-status routes")
    if (admin.get("name") != "ordivon-native-country-switch" or
        admin.get("auth") != "apikey" or
        set(admin.get("routes", [])) != set(CHANGE_ROUTES)):
        raise ValueError("Unexpected Gluetun native control routes")
    if set(public.get("routes", [])) & set(admin.get("routes", [])):
        raise ValueError("Public role overlaps privileged routes")
    if any(x not in ("name", "auth", "routes") for x in public) or any(
        x not in ("name", "auth", "apikey", "routes") for x in admin
    ):
        raise ValueError("Unexpected Gluetun control authority field")
    if len(str(admin.get("apikey", ""))) < 28:
        raise ValueError("Missing Gluetun key")
    return {"routeCount": len(READ_ROUTES) + len(CHANGE_ROUTES),
            "authenticatedWriteRouteCount": 1}


def verify(target: Path = TARGET, *, require_root: bool = True) -> dict:
    st = target.lstat()
    if not target.is_file() or (require_root and st.st_uid != 0) or st.st_mode & 0o077:
        raise ValueError("Native Gluetun auth config is not root-only")
    return assert_role_contract(target.read_text(encoding="utf-8"))


def install(target: Path = TARGET, *, require_root: bool = True) -> dict:
    if require_root and os.geteuid() != 0:
        raise ValueError("Native auth installation needs current root authority")
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if (require_root and target.parent.stat().st_uid != 0) or target.parent.stat().st_mode & 0o077:
        raise ValueError("Native auth directory must be root-only")
    if target.exists() or target.is_symlink():
        return {"standing": "PRESENT_UNCHANGED", **verify(target, require_root=require_root), "effectAttempted": False}
    text = rendered(secrets.token_urlsafe(32))
    fd, name = tempfile.mkstemp(prefix=".auth-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, target)  # no overwrite; never replace an existing secret
    finally:
        os.unlink(name)
    return {"standing": "NATIVE_AUTH_PREPARED_NOT_LOADED",
            **verify(target, require_root=require_root), "effectAttempted": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-source", action="store_true")
    group.add_argument("--install", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        if args.check_source:
            result = {"standing": "NATIVE_AUTH_TEMPLATE_VALID", **assert_role_contract(
                rendered("synthetic_dummy_secret_NEVER_IN_PRODUCTION_00000"))}
        elif args.install:
            result = install()
        else:
            result = {"standing": "NATIVE_AUTH_INSTALLED_CONFIG_VALID", **verify()}
    except (OSError, ValueError, tomllib.TOMLDecodeError) as e:
        result = {"standing": "NATIVE_AUTH_UNKNOWN", "reasonClass": type(e).__name__}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["standing"] != "NATIVE_AUTH_UNKNOWN" else 1


if __name__ == "__main__":
    sys.exit(main())
