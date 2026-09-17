#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2 import build_browser_security_witness_bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build one canonical Browser Security witness bundle from declared detector readings."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    value = json.loads(args.manifest.read_text(encoding="utf-8"))
    expected = {
        "schemaVersion",
        "witnessId",
        "browserBinaryDigest",
        "controlLayer",
        "networkAuthority",
        "readings",
        "challengeStanding",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise SystemExit("manifest must contain exactly the canonical Browser Security collector fields")
    if value["schemaVersion"] != 1:
        raise SystemExit("schemaVersion=1 required")
    bundle = build_browser_security_witness_bundle(
        witness_id=value["witnessId"],
        browser_binary_digest=value["browserBinaryDigest"],
        control_layer=value["controlLayer"],
        network_authority=value["networkAuthority"],
        readings=value["readings"],
        challenge_standing=value["challengeStanding"],
    )
    text = json.dumps(bundle.to_dict(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
