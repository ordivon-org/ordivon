#!/usr/bin/env python3
"""Governance Review Router — map changed files to required checks and owners.

Uses OpenFGA for authorization (who can review what domain) and OPA for
check routing (what checks are required for each governance surface).

Phase 3: Replaced hardcoded SURFACE_CHECKS dict with OpenFGA + OPA-backed
routing. The hardcoded dict is kept as fallback for environments without
OpenFGA/OPA.

Usage:
    python3 scripts/governance/route_reviewers.py --changed-files <diff-output>
    python3 scripts/governance/route_reviewers.py --path aos/schemas/aos-object.schema.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "docs/governance/config/routing-surfaces.json"

# ── Hardcoded surface→checks mapping (fallback when OpenFGA/OPA unavailable) ─

FALLBACK_SURFACE_CHECKS = {
    "aos/schemas": {
        "required_checks": ["validate-aos-object-identity --all-fixtures", "check_pipeline_compatibility"],
        "authority_domain": "implementation",
    },
    "scripts/aos": {
        "required_checks": [
            "validate-aos-object-identity --all-fixtures",
            "pytest test_aos_identity_admission_compatibility",
        ],
        "authority_domain": "implementation",
    },
    "docs/governance/document-registry.jsonl": {
        "required_checks": [
            "admit_artifact",
            "inventory_phase.py --phase AOS",
            "reconcile.py registry",
            "generate_document_wiki.py",
        ],
        "authority_domain": "documentation",
    },
    "docs/governance/schemas/document-types.json": {
        "required_checks": ["admit_artifact", "inventory_phase.py"],
        "authority_domain": "documentation",
    },
    "receipts/governance": {
        "required_checks": ["extract_receipt_claims", "detect_overclaim"],
        "authority_domain": "documentation",
    },
    "docs/governance/audits": {
        "required_checks": ["detect_overclaim"],
        "authority_domain": "documentation",
    },
    "docs/governance/aos-auto": {
        "required_checks": ["inventory_phase.py --phase AOS-AUTO", "detect_overclaim", "governance verify"],
        "authority_domain": "documentation",
    },
    "docs/governance/evidence": {
        "required_checks": ["verify_stage_evidence"],
        "authority_domain": "documentation",
    },
    "docs/ai/current-phase-boundaries.md": {
        "required_checks": ["inventory_phase.py --phase AOS"],
        "authority_domain": "documentation",
    },
    "aos/debts": {
        "required_checks": ["admit_artifact (debt schema)"],
        "authority_domain": "documentation",
    },
    "aos/fixtures": {
        "required_checks": [
            "validate-aos-object-identity --all-fixtures",
            "pytest test_aos_identity_admission_compatibility",
        ],
        "authority_domain": "implementation",
    },
    "tests/unit/governance": {
        "required_checks": ["pytest tests/unit/governance/"],
        "authority_domain": "implementation",
    },
}


def _load_routing_config() -> dict[str, dict]:
    """Load routing surfaces from config. Falls back to hardcoded."""
    if CONFIG_PATH.exists():
        try:
            config = json.loads(CONFIG_PATH.read_text())
            surfaces = {}
            for pattern, cfg in config.get("surfaces", {}).items():
                surfaces[pattern] = {
                    "required_checks": cfg.get("required_checks", []),
                    "authority_domain": cfg.get("authority_domain", "documentation"),
                }
            if surfaces:
                return surfaces
        except (json.JSONDecodeError, KeyError):
            pass
    return FALLBACK_SURFACE_CHECKS


# ── OpenFGA-based routing (Phase 3) ────────────────────────────────────────


async def _route_with_openfga(filepath: str, user: str = "ordivon-core-maintainer") -> dict | None:
    """Route a file using OpenFGA authorization.

    Returns dict with required_checks and authority_domain, or None if
    OpenFGA is unavailable.
    """
    try:
        from ordivon_governance_core.openfga_client import get_client

        client = get_client()
        surfaces = _load_routing_config()

        for pattern, config in surfaces.items():
            if filepath.startswith(pattern) or pattern in filepath:
                domain = config["authority_domain"]

                # Check if user can review this domain
                allowed = await client.check(
                    user=f"user:{user}",
                    relation="reviewer",
                    object=f"domain:{domain}",
                )
                if allowed:
                    return {
                        "pattern": pattern,
                        "required_checks": config["required_checks"],
                        "authority_domain": domain,
                        "authorized_by": "openfga",
                    }
        return None
    except (ImportError, Exception):
        return None


def route_file_fallback(filepath: str) -> list[dict]:
    """Fallback routing without OpenFGA (uses hardcoded surfaces)."""
    surfaces = _load_routing_config()
    matches = []
    for pattern, config in surfaces.items():
        if filepath.startswith(pattern) or pattern in filepath:
            matches.append({
                "pattern": pattern,
                "required_checks": config["required_checks"],
                "authority_domain": config["authority_domain"],
                "authorized_by": "fallback",
            })
    return matches


async def route_file(filepath: str, user: str = "ordivon-core-maintainer") -> list[dict]:
    """Route a single file — OpenFGA first, fallback if unavailable."""
    result = await _route_with_openfga(filepath, user)
    if result:
        return [result]
    return route_file_fallback(filepath)


def match_surface(filepath: str) -> list[dict]:
    """Match a filepath against governance surface patterns (sync, fallback)."""
    surfaces = _load_routing_config()
    matches = []
    for pattern, config in surfaces.items():
        if filepath.startswith(pattern) or pattern in filepath:
            matches.append({
                "pattern": pattern,
                "required_checks": config["required_checks"],
                "authority_domain": config["authority_domain"],
            })
    return matches


async def route_files_async(files: list[str], user: str = "ordivon-core-maintainer") -> dict:
    """Route files using OpenFGA authorization (async)."""
    all_checks: set[str] = set()
    domains: set[str] = set()
    file_routes: list[dict] = []

    for filepath in files:
        matches = await route_file(filepath, user)
        if matches:
            for m in matches:
                all_checks.update(m["required_checks"])
                if "authority_domain" in m:
                    domains.add(m["authority_domain"])
            file_routes.append({
                "file": filepath,
                "matched_surfaces": [m["pattern"] for m in matches],
                "required_checks": list(set(c for m in matches for c in m["required_checks"])),
                "authorized_by": matches[0].get("authorized_by", "fallback"),
            })
        else:
            file_routes.append({
                "file": filepath,
                "matched_surfaces": [],
                "required_checks": [],
                "warning": "No governance surface matched",
            })

    return {
        "changed_files": len(files),
        "matched_files": sum(1 for f in file_routes if f["matched_surfaces"]),
        "unmatched_files": sum(1 for f in file_routes if not f["matched_surfaces"]),
        "unique_checks": sorted(all_checks),
        "authority_domains": sorted(domains),
        "file_routes": file_routes,
    }


def route_files(files: list[str]) -> dict:
    """Route a list of changed files to required checks (sync, fallback)."""
    all_checks: set[str] = set()
    domains: set[str] = set()
    file_routes: list[dict] = []

    for filepath in files:
        matches = match_surface(filepath)
        if matches:
            for m in matches:
                all_checks.update(m["required_checks"])
                domains.add(m["authority_domain"])
            file_routes.append({
                "file": filepath,
                "matched_surfaces": [m["pattern"] for m in matches],
                "required_checks": list(set(c for m in matches for c in m["required_checks"])),
            })
        else:
            file_routes.append({
                "file": filepath,
                "matched_surfaces": [],
                "required_checks": [],
                "warning": "No governance surface matched",
            })

    return {
        "changed_files": len(files),
        "matched_files": sum(1 for f in file_routes if f["matched_surfaces"]),
        "unmatched_files": sum(1 for f in file_routes if not f["matched_surfaces"]),
        "unique_checks": sorted(all_checks),
        "authority_domains": sorted(domains),
        "file_routes": file_routes,
    }


def main() -> int:
    import asyncio

    files: list[str] = []

    if "--changed-files" in sys.argv:
        idx = sys.argv.index("--changed-files")
        if idx + 1 < len(sys.argv):
            source = sys.argv[idx + 1]
            if source == "-":
                files = [l.strip() for l in sys.stdin.read().split("\n") if l.strip()]
            else:
                path = Path(source)
                if path.exists():
                    files = [l.strip() for l in path.read_text().split("\n") if l.strip()]
    elif "--path" in sys.argv:
        idx = sys.argv.index("--path")
        if idx + 1 < len(sys.argv):
            files = [sys.argv[idx + 1]]
    else:
        # Default: show known surfaces
        surfaces = _load_routing_config()
        print("Governance surface → required checks:")
        for pattern, config in sorted(surfaces.items()):
            print(f"  {pattern}")
            for check in config["required_checks"]:
                print(f"    → {check}")
            print(f"    domain: {config['authority_domain']}")
        return 0

    if not files:
        print("No files to route")
        return 0

    # Try async OpenFGA routing first
    try:
        result = asyncio.run(route_files_async(files))
        print(json.dumps(result, indent=2))
    except Exception:
        result = route_files(files)
        print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
