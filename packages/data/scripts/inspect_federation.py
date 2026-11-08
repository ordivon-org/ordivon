#!/usr/bin/env python3
"""Inspect the existing domain-owned DCAT projection without copying a registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DATA_ROOT.parents[1]
sys.path.insert(0, str(DATA_ROOT / "src"))

from ordivon_data.catalog import inspect_catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=REPO_ROOT
        / "studies/data-lifecycle/evidence/data-products-r2/federated-catalog.dcat.jsonld",
        help="Existing compact DCAT 3 JSON-LD catalog projection",
    )
    parser.add_argument(
        "--verify-local",
        action="store_true",
        help="Check exact digest only for local files within explicitly allowed roots",
    )
    parser.add_argument(
        "--allow-root",
        type=Path,
        action="append",
        default=[],
        help="Additional trusted local root for read-only byte verification",
    )
    parser.add_argument(
        "--require-verified",
        action="store_true",
        help="Require every distribution to have a verified scoped digest; UNKNOWN is not success",
    )
    parser.add_argument(
        "--require-port",
        action="append",
        nargs=3,
        default=[],
        metavar=("PRODUCT_ID", "PRODUCT_VERSION", "DISTRIBUTION_URN"),
        help=(
            "Require exact product ID/version/distribution URN to be VERIFIED. "
            "This consumer-scoped gate does NOT certify unselected product ports."
        ),
    )
    args = parser.parse_args()
    if (args.require_verified or args.require_port) and not args.verify_local:
        parser.error("integrity admission requires --verify-local")
    if args.require_verified and args.require_port:
        parser.error("--require-verified and --require-port are exclusive")
    if len({tuple(ref) for ref in args.require_port}) != len(args.require_port):
        parser.error("duplicate --require-port selection")
    try:
        result = inspect_catalog(
            args.catalog,
            verify_local=args.verify_local,
            allowed_roots=(REPO_ROOT, *args.allow_root),
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"catalog inspection failed: {error}", file=sys.stderr)
        return 2
    observed = [
        distribution["verification"]
        for product in result["products"]
        for distribution in product["distributions"]
    ]
    result["inspection"] = {
        "distributionCount": len(observed),
        "verifiedCount": observed.count("VERIFIED"),
        "unknownCount": observed.count("UNKNOWN"),
        "falsifiedCount": observed.count("FALSIFIED"),
        "notCheckedCount": observed.count("NOT_CHECKED"),
        "integrityGate": (
            "PASS"
            if observed and all(state == "VERIFIED" for state in observed)
            else "NOT_ESTABLISHED"
        ),
    }
    if args.require_port:
        selections = []
        for product_id, version, distribution_urn in args.require_port:
            products = [
                p
                for p in result["products"]
                if p["id"] == product_id and p["version"] == version
            ]
            matched = [
                d
                for p in products
                for d in p["distributions"]
                if d["id"] == distribution_urn
            ]
            if len(matched) > 1:
                print("ambiguous --require-port distribution identity", file=sys.stderr)
                return 2
            status = matched[0]["verification"] if matched else "UNKNOWN"
            selections.append(
                {
                    "productId": product_id,
                    "productVersion": version,
                    "distributionId": distribution_urn,
                    "verification": status,
                }
            )
        result["inspection"]["selectedPorts"] = selections
        result["inspection"]["selectedPortIntegrityGate"] = (
            "PASS"
            if selections and all(s["verification"] == "VERIFIED" for s in selections)
            else "NOT_ESTABLISHED"
        )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    if "FALSIFIED" in observed:
        return 2
    if args.require_verified and result["inspection"]["integrityGate"] != "PASS":
        return 3
    if (
        args.require_port
        and result["inspection"]["selectedPortIntegrityGate"] != "PASS"
    ):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
