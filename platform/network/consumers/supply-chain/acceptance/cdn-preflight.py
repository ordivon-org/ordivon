#!/usr/bin/env python3
"""Read-only EXACT two-file Supply-Chain CDN policy currentness preflight.

This program NEVER writes installed policy, restarts services or authorizes
production effects. Returns a bounded decision to an independent operator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

HOST = "production.cloudfront.docker.com"
FILES = ("authority.json", "egress.json")
# This preflight is for ONE R4 exact-host source delta, not a general-purpose
# release operator. Any further authorization change must be reviewed and
# intentionally re-pinned, never implicitly inherited through this script.
PINNED_SOURCE_BYTES = {
    "authority.json": "sha256:d43559f2644c0f0ab0113022e96c663bbb2da5a05585b6f4194519d0f1223cc3",
    "egress.json": "sha256:c5fa529080f3eb0ede04c14bfca4f4699a7973e1fe3e013f3a704045a58cb377",
}


def domain_lists(doc: dict, name: str) -> tuple[list[str], list[str]]:
    if name == "authority.json":
        if doc.get("directFallback") is not False:
            raise ValueError("source directFallback must be false")
        return doc["allowedHttpsDomains"], doc["allowedHttpsDomainSuffixes"]
    if doc["route"]["rules"][-1] != {"action": "reject"}:
        raise ValueError("source must end in catch-all reject")
    if doc["outbounds"] != [{
        "type": "http", "tag": "provider-carrier",
        "server": "10.252.246.2", "server_port": 19680,
    }]:
        raise ValueError("source must have exactly one scoped carrier outbound")
    rule = next(r for r in doc["route"]["rules"] if r.get("inbound") == ["supply-chain-oci"])
    if rule.get("port") != 443 or rule.get("network") != ["tcp"] or rule.get("outbound") != "provider-carrier":
        raise ValueError("source unexpected scope/port/outbound")
    return rule["domain"], rule["domain_suffix"]


def source_policy_valid(source: dict[str, dict]) -> bool:
    try:
        a, b = source["authority.json"], source["egress.json"]
        domains_a, suffixes_a = domain_lists(a, "authority.json")
        domains_b, suffixes_b = domain_lists(b, "egress.json")
        if domains_a != domains_b or suffixes_a != suffixes_b:
            return False
        if a.get("networkAuthority", {}).get("name") != "provider-egress":
            return False
        if domains_a.count(HOST) != 1 or any(x.startswith("*") for x in domains_a):
            return False
        # The change is for exactly one Docker blob CDN host, not Docker's full domain.
        if any(x in {"cloudfront.docker.com", "docker.com", "cloudflare.docker.com"} for x in suffixes_a):
            return False
        return True
    except (KeyError, TypeError, IndexError, StopIteration, ValueError):
        return False


def sans_exact_host(source_doc: dict, name: str) -> dict:
    clone = json.loads(json.dumps(source_doc))
    domains, _ = domain_lists(clone, name)
    domains.remove(HOST)
    return clone


def sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--installed-dir", required=True, type=Path)
    args = parser.parse_args()

    record: dict = {
        "schemaVersion": 1,
        "kind": "ordivon.network-v2.supply-chain-cdn-preflight",
        "standing": "HOLD_UNREADABLE_OR_INVALID",
        "sourceHeadAuthority": HOST,
        "effectAttempted": False,
        "installedChanged": False,
        "unitRestartAttempted": False,
    }
    result = 2
    try:
        source_raw = {name: (args.source_dir / name).read_bytes() for name in FILES}
        installed_raw = {name: (args.installed_dir / name).read_bytes() for name in FILES}
        source = {name: json.loads(source_raw[name]) for name in FILES}
        installed = {name: json.loads(installed_raw[name]) for name in FILES}
        record["sourceDigests"] = {name: sha256(source_raw[name]) for name in FILES}
        record["installedDigests"] = {name: sha256(installed_raw[name]) for name in FILES}
        if not source_policy_valid(source) or any(
            sha256(source_raw[name]) != PINNED_SOURCE_BYTES[name] for name in FILES
        ):
            record["standing"] = "HOLD_SOURCE_INVALID"
        else:
            old = {name: sans_exact_host(source[name], name) for name in FILES}
            states = [
                "current" if installed[name] == source[name] else
                "preimage" if installed[name] == old[name] else "drift"
                for name in FILES
            ]
            if states == ["current", "current"]:
                record["standing"] = "ALREADY_DEPLOYED"
                result = 0
            elif states == ["preimage", "preimage"]:
                record["standing"] = "READY_TO_DEPLOY_NARROW_SCOPE"
                result = 0
            elif sorted(states) == ["current", "preimage"]:
                record["standing"] = "HOLD_PARTIAL_DEPLOYMENT"
            else:
                # Identify this specific known legacy alias, but never silently
                # modify it together with the CDN allowlist change.
                legacy = json.loads(json.dumps(old["authority.json"]))
                legacy["networkAuthority"]["name"] = "browserless-prod"
                if installed["authority.json"] == legacy and states[1] == "preimage":
                    record["standing"] = "HOLD_LEGACY_AUTHORITY_ALIAS"
                else:
                    record["standing"] = "HOLD_UNEXPECTED_DRIFT"
            record["perFileState"] = dict(zip(FILES, states))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        record["standing"] = "HOLD_UNREADABLE_OR_INVALID"
    print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return result


if __name__ == "__main__":
    sys.exit(main())
