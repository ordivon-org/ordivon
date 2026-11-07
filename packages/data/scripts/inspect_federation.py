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
    args = parser.parse_args()
    try:
        result = inspect_catalog(
            args.catalog,
            verify_local=args.verify_local,
            allowed_roots=(REPO_ROOT, *args.allow_root),
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"catalog inspection failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    if any(
        dist["verification"] == "FALSIFIED"
        for product in result["products"]
        for dist in product["distributions"]
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
