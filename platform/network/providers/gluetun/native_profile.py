#!/usr/bin/env python3
"""Migrate the single already-owned Surfshark WG identity to Gluetun native inputs.

This is configuration materialization, not a controller. No VPN connection is
started here; systemd/Podman own lifecycle and Gluetun owns server selection.
"""
from __future__ import annotations

import argparse
import base64
import configparser
import ipaddress
import os
from pathlib import Path
import subprocess
import tempfile

WG_CONFIG = Path("/etc/network-v2/browserless/nv2blwg.conf")
BASE_ENV = Path("/etc/network-v2/gluetun/serialized-candidate.env")
NATIVE_ENV = Path("/etc/network-v2/gluetun/serialized-native.env")
SECRET = "network-v2-gluetun-surfshark-wgkey"
REGION = "Asia Pacific"
COUNTRIES = "Singapore,Japan"

PRESERVED = (
    "HTTPPROXY",
    "HTTPPROXY_LISTENING_ADDRESS",
    "DNS_SERVER",
    "PUBLICIP_ENABLED",
    "HTTP_CONTROL_SERVER_ADDRESS",
    "FIREWALL_INPUT_PORTS",
)


def parse_wireguard(source: str) -> tuple[str, str]:
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.read_string(source)
    if not parser.has_section("Interface"):
        raise ValueError("WireGuard [Interface] is absent")
    secret = parser["Interface"]["PrivateKey"].strip()
    if len(base64.b64decode(secret, validate=True)) != 32:
        raise ValueError("WireGuard identity is not 32 bytes")
    addresses = parser["Interface"]["Address"].split(",")
    ipv4 = next(
        (str(ipaddress.ip_interface(raw.strip())) for raw in addresses
         if ipaddress.ip_interface(raw.strip()).version == 4),
        None,
    )
    if ipv4 is None:
        raise ValueError("WireGuard IPv4 interface address is absent")
    return secret, ipv4


def parse_env(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("Malformed inherited environment")
        key, value = line.split("=", 1)
        if key in values:
            raise ValueError("Duplicate inherited environment key")
        values[key] = value
    if values.get("VPN_SERVICE_PROVIDER") != "custom":
        raise ValueError("Expected the exact previous Custom provider source")
    if values.get("VPN_TYPE") != "wireguard":
        raise ValueError("Expected a WireGuard provider")
    return values


def generate_env(inherited: dict[str, str], interface_address: str) -> str:
    config = [
        "VPN_SERVICE_PROVIDER=surfshark",
        "VPN_TYPE=wireguard",
        f"WIREGUARD_ADDRESSES={interface_address}",
        'SERVER_REGIONS="Asia Pacific"',
        f"SERVER_COUNTRIES={COUNTRIES}",
        "UPDATER_PERIOD=480h",
        "HEALTH_RESTART_VPN=on",
        # The VPN startup check must not depend on its own DNS layer.
        # Both IP identities have independently validated TLS certificates.
        "HEALTH_TARGET_ADDRESSES=1.1.1.1:443,8.8.8.8:443",
        # Native Gluetun encrypted DNS, without the legacy DoH SourceCut.
        "DNS_UPSTREAM_RESOLVER_TYPE=dot",
        "DNS_UPSTREAM_RESOLVERS=cloudflare,google",
    ]
    for key in PRESERVED:
        if key in inherited:
            value = inherited[key]
            if any(c in value for c in ("\n", "\r", '"', "'")):
                raise ValueError("Unsafe inherited environment quoting")
            config.append(f"{key}={value}")
    return "\n".join(config) + "\n"


def stage(config_path: Path, base_path: Path) -> tuple[str, str]:
    private_key, address = parse_wireguard(config_path.read_text())
    env = generate_env(parse_env(base_path.read_text()), address)
    return private_key, env


def materialize(private_key: str, generated: str, output: Path) -> None:
    # Podman secret stays in its native protected store, never a Git or env value.
    subprocess.run(
        ["/usr/bin/podman", "secret", "create", "--replace", SECRET, "-"],
        input=(private_key + "\n").encode(),
        stdout=subprocess.DEVNULL,
        check=True,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, path = tempfile.mkstemp(dir=output.parent, prefix=".native-env.")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as fp:
            os.fchmod(fp.fileno(), 0o600)
            fp.write(generated)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(path, output)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def main() -> None:
    arg = argparse.ArgumentParser()
    choices = arg.add_mutually_exclusive_group(required=True)
    choices.add_argument("--check", action="store_true")
    choices.add_argument("--apply", action="store_true")
    choices.add_argument("--verify", action="store_true")
    arg.add_argument("--wireguard", type=Path, default=WG_CONFIG)
    arg.add_argument("--base-env", type=Path, default=BASE_ENV)
    arg.add_argument("--native-env", type=Path, default=NATIVE_ENV)
    args = arg.parse_args()
    private_key, env = stage(args.wireguard, args.base_env)
    if args.apply:
        materialize(private_key, env, args.native_env)
    if args.verify:
        if args.native_env.read_text() != env:
            raise SystemExit("Native Gluetun environment SourceCut mismatch")
        if args.native_env.stat().st_mode & 0o077:
            raise SystemExit("Native Gluetun environment has unsafe permissions")
        subprocess.run(
            ["/usr/bin/podman", "secret", "inspect", SECRET],
            check=True, capture_output=True,
        )
    print(
        "native_profile=" + ("APPLIED" if args.apply else "VERIFIED" if args.verify else "VALID")
        + " provider=surfshark wireguard=eligible region=Asia_Pacific countries=Singapore,Japan key=REDACTED"
    )


if __name__ == "__main__":
    main()
