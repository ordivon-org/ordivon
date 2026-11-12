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
import json
import os
from pathlib import Path
import subprocess
import tempfile

WG_CONFIG = Path("/etc/network-v2/browserless/nv2blwg.conf")
BASE_ENV = Path("/etc/network-v2/gluetun/serialized-candidate.env")
NATIVE_ENV = Path("/etc/network-v2/gluetun/serialized-native.env")
SECRET = "network-v2-gluetun-surfshark-wgkey"
CONTAINER = "network-v2-gluetun-owned-r1"
SELECTOR_POLICY = Path(__file__).resolve().parent / "config/exit-selector.json"
# This value is also asserted against the natural Podman Quadlet Owner below.
LOADED_WG_SECRETFILE = "/run/secrets/surfshark-wgkey"


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


def parse_selector_policy(raw: str) -> dict[str, list[str]]:
    """One source-owned selector; Gluetun owns the actual server choice.

    Selected countries are transport candidates, never proof that an upstream
    application accepts that public egress or that a catalog IP is healthy.
    """
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate Gluetun selector key: {key}")
            result[key] = value
        return result

    value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    fields = {"regions", "selectedCountries", "excludedCountries"}
    if not isinstance(value, dict) or not fields <= set(value) or (
        set(value) - fields - {"selectionMode"}
    ):
        raise ValueError("Gluetun selector policy fields differ")
    ordered = value.get("selectionMode") == "ordered"
    if "selectionMode" in value and not ordered:
        raise ValueError("Only upstream-native ordered selection mode is supported")
    for field in fields:
        entries = value[field]
        if not isinstance(entries, list):
            raise ValueError(f"Invalid {field} selector list")
        if not all(
            isinstance(x, str)
            and x == x.strip()
            and x
            and all(c.isalnum() or c in " -.'()&" for c in x)
            for x in entries
        ):
            raise ValueError(f"Unsafe {field} selector item")
        if len(entries) != len(set(entries)):
            raise ValueError(f"Duplicate {field} selector")
    if set(value["selectedCountries"]) & set(value["excludedCountries"]):
        raise ValueError("Selected Gluetun country is excluded")
    if ordered:
        # Gluetun's native priority is hostnames > cities > REGIONS >
        # COUNTRIES. A region filter would mask the country order.
        if value["regions"]:
            raise ValueError("Ordered country fallback requires no region filter")
        if len(value["selectedCountries"]) < 2:
            raise ValueError("Ordered country fallback needs at least two countries")
    return value


def read_selector_policy(path: Path = SELECTOR_POLICY) -> dict[str, list[str]]:
    return parse_selector_policy(path.read_text(encoding="utf-8"))


def render_native_selector(
    values: list[str], *, preserve_legacy_region: bool = False,
) -> str:
    # Podman --env-file preserves quote bytes in OCI .Config.Env; it accepts
    # unquoted spaces inside the value. Preserve the already-loaded single
    # Asia Pacific region spelling to avoid an accidental production SourceCut.
    combined = ",".join(values)
    if preserve_legacy_region and combined == "Asia Pacific":
        return '"Asia Pacific"'
    return combined


def generate_env(
    inherited: dict[str, str], interface_address: str,
    selector: dict[str, list[str]] | None = None,
) -> str:
    if selector is None:
        selector = read_selector_policy()
    else:
        selector = parse_selector_policy(json.dumps(selector))
    # v3.41.3 default source stays byte-for-byte unchanged. The optional
    # ordered mode is an upstream Gluetun feature (currently unreleased);
    # it is a source-only preview until a proven supporting OCI is promoted.
    selectors = []
    if selector["regions"]:
        selectors.append(
            f'SERVER_REGIONS={render_native_selector(selector["regions"], preserve_legacy_region=True)}'
        )
    if selector["selectedCountries"]:
        selectors.append(f'SERVER_COUNTRIES={render_native_selector(selector["selectedCountries"])}')
    if selector.get("selectionMode") == "ordered":
        selectors.append("SERVER_SELECTION_MODE=ordered")
    config = [
        "VPN_SERVICE_PROVIDER=surfshark",
        "VPN_TYPE=wireguard",
        f"WIREGUARD_ADDRESSES={interface_address}",
        *selectors,
        "UPDATER_PERIOD=480h",
        # Pinned Gluetun 3.41.3 compares 185 unique Surfshark hostname fetches
        # against 363 transport-expanded stored records. int(0.51*363)=185,
        # rejecting any smaller result count against today's observed census.
        "UPDATER_MIN_RATIO=0.51",
        # Local LAN underlay for the approved mobile Tailnet exit.
        # Gluetun-native CIDR-wide exception; NOT UDP-port-only.
        # Requalify public VPN egress and direct path if local LAN changes.
        "FIREWALL_OUTBOUND_SUBNETS=192.168.0.0/24",
        "HEALTH_RESTART_VPN=on",
        # The VPN startup check must not depend on its own DNS layer.
        # Both IP identities have independently validated TLS certificates.
        "HEALTH_TARGET_ADDRESSES=1.1.1.1:443,8.8.8.8:443",
        # Native Gluetun encrypted DNS, without the legacy DoH SourceCut.
        "DNS_UPSTREAM_RESOLVER_TYPE=dot",
        "DNS_UPSTREAM_RESOLVERS=cloudflare,google",
        # Temporary open-connectivity phase: disable upstream optional malware-domain block.
        # Keep authenticated DoT upstream transport unchanged.
        "BLOCK_MALICIOUS=off",
    ]
    for key in PRESERVED:
        if key in inherited:
            value = inherited[key]
            if any(c in value for c in ("\n", "\r", '"', "'")):
                raise ValueError("Unsafe inherited environment quoting")
            config.append(f"{key}={value}")
    return "\n".join(config) + "\n"


def stage(
    config_path: Path, base_path: Path, selector_path: Path = SELECTOR_POLICY,
) -> tuple[str, str]:
    private_key, address = parse_wireguard(config_path.read_text())
    env = generate_env(parse_env(base_path.read_text()), address, read_selector_policy(selector_path))
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



def verify_loaded_env(expected: str, loaded: list[str]) -> None:
    """Check the loaded OCI environment, not just the file used on next restart.

    Compare only keys emitted by this source and reject hidden narrower server
    filters. Never expose inspected environment values, including credentials.
    """
    expected_values = dict(line.split("=", 1) for line in expected.splitlines())
    extra_server_filters = {
        "SERVER_COUNTRIES", "SERVER_CITIES", "SERVER_HOSTNAMES", "SERVER_NAMES",
        "SERVER_CATEGORIES", "SERVER_REGIONS", "SERVER_SELECTION_MODE",
    }
    # An extra explicit endpoint or plaintext key in the running container can
    # silently bypass native Surfshark server selection even when the selected
    # country and region match. These keys are never emitted by the source
    # profile; Gluetun receives the WireGuard key via the Quadlet-mounted Secret.
    forbidden_identity_overrides = {
        "WIREGUARD_ENDPOINT_IP", "WIREGUARD_ENDPOINT_PORT",
        "WIREGUARD_PUBLIC_KEY", "WIREGUARD_PRIVATE_KEY",
        "WIREGUARD_PRESHARED_KEY",
    }
    loaded_only_expected = {
        "WIREGUARD_PRIVATE_KEY_SECRETFILE": LOADED_WG_SECRETFILE,
    }
    relevant = (
        expected_values.keys() | extra_server_filters |
        forbidden_identity_overrides | loaded_only_expected.keys()
    )
    observed: dict[str, str] = {}
    for item in loaded:
        key, sep, value = item.partition("=")
        if not sep or key not in relevant:
            continue
        if key in observed:
            raise ValueError(f"Duplicate loaded Gluetun key: {key}")
        observed[key] = value
    mismatches = sorted(
        key for key, value in (expected_values | loaded_only_expected).items()
        if observed.get(key) != value
    )
    unexpected = sorted(
        key for key in extra_server_filters | forbidden_identity_overrides
        if key not in expected_values and observed.get(key)
    )
    if mismatches or unexpected:
        keys = ", ".join(mismatches + unexpected)
        raise ValueError(f"Gluetun selected running configuration differs: {keys}")


def verify_running_container(expected: str) -> None:
    # One Podman inspection reads the active state and selected loaded config
    # from the same container object. No private Env values go to stdout/logs.
    inspected = subprocess.run(
        [
            "/usr/bin/podman", "inspect", "-f",
            "{{.State.Running}} {{json .Config.Env}}", CONTAINER,
        ],
        check=True, capture_output=True, text=True, timeout=20,
    )
    running, separator, payload = inspected.stdout.strip().partition(" ")
    if running != "true" or not separator:
        raise SystemExit("Selected Gluetun container is not running")
    try:
        loaded = json.loads(payload)
    except json.JSONDecodeError:
        raise SystemExit("Cannot decode selected Gluetun loaded environment") from None
    if not isinstance(loaded, list) or not all(isinstance(x, str) for x in loaded):
        raise SystemExit("Invalid selected Gluetun loaded environment shape")
    try:
        verify_loaded_env(expected, loaded)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None

def main() -> None:
    arg = argparse.ArgumentParser()
    choices = arg.add_mutually_exclusive_group(required=True)
    choices.add_argument("--check", action="store_true")
    choices.add_argument("--apply", action="store_true")
    choices.add_argument("--verify", action="store_true")
    arg.add_argument("--wireguard", type=Path, default=WG_CONFIG)
    arg.add_argument("--base-env", type=Path, default=BASE_ENV)
    arg.add_argument("--native-env", type=Path, default=NATIVE_ENV)
    arg.add_argument("--selector-policy", type=Path, default=SELECTOR_POLICY)
    arg.add_argument(
        "--allow-ordered-apply", action="store_true",
        help="Explicitly allow applying a tested upstream ordered-capable image profile",
    )
    args = arg.parse_args()
    private_key, env = stage(args.wireguard, args.base_env, args.selector_policy)
    if args.apply:
        if "SERVER_SELECTION_MODE=ordered" in env and not args.allow_ordered_apply:
            raise SystemExit(
                "Ordered preview requires an explicitly qualified upstream OCI image "
                "and --allow-ordered-apply; unchanged stable v3.41.3 ignores this mode"
            )
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
        verify_running_container(env)
    # Report the exact bytes staged for admission, never a second read of the
    # selector file which could change between generation and observation.
    emitted = dict(line.split("=", 1) for line in env.splitlines())
    regions = emitted.get("SERVER_REGIONS", "").strip('"')
    countries = emitted.get("SERVER_COUNTRIES", "*").strip('"')
    print(
        "native_profile=" + ("APPLIED" if args.apply else "VERIFIED" if args.verify else "VALID")
        + " provider=surfshark wireguard=eligible"
        + f" regions={regions} countries={countries} key=REDACTED"
    )


if __name__ == "__main__":
    main()
