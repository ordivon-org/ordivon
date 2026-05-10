#!/usr/bin/env python3
"""Generate coverage review routing — map every coverage object to owner/reviewer/approver (PM-8).

Derives owners from registry, exclusions, debt ledger, and classifier metadata.
Owner ≠ Reviewer. Reviewer ≠ Approver. Routing ≠ Authorization.

Usage:
    python scripts/generate-coverage-review-routing.py
"""

from __future__ import annotations

import json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/governance/generated"
SCHEMA_DIR = ROOT / "docs/governance/schemas"
COVERAGE = OUTPUT_DIR / "coverage-boundary.json"
ROUTING = SCHEMA_DIR / "coverage-review-routing.json"


def derive_owner(path: str, status: str, source: str, reg_owner: str, excl_meta: dict, debt_meta: dict, meta: dict) -> str:
    """Derive owner from the coverage object's source."""
    if reg_owner and status == "governed":
        return reg_owner
    if status == "excluded":
        return str(excl_meta.get("reason", "unknown exclusion owner"))[:60]
    if status == "debt_parked":
        return str(debt_meta.get("owner", "unknown debt owner"))[:60]
    if status == "generated":
        return "generator script (see source_refs)"
    if status == "fixture":
        return str(meta.get("owning_test", "unknown fixture owner"))
    if status == "legacy":
        return "governance-core maintainer (legacy review)"
    if status == "blocked":
        return "REQUIRES IMMEDIATE RESOLUTION"
    return "governance-core maintainer"


def generate() -> dict:
    coverage = json.loads(COVERAGE.read_text())
    routing = json.loads(ROUTING.read_text())

    # Build registry owner index
    reg_path = ROOT / "docs/governance/document-registry.jsonl"
    reg_owners = {}
    if reg_path.exists():
        with open(reg_path) as f:
            for line in f:
                if line.strip():
                    e = json.loads(line)
                    reg_owners[e["path"]] = e.get("owner", "")

    # Build debt owner index
    debt_path = ROOT / "docs/governance/dependency-audit-debts.jsonl"
    debt_owners = {}
    if debt_path.exists():
        with open(debt_path) as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    if d.get("path"):
                        debt_owners[d["path"]] = d

    objects = []
    ownerless = []
    counts = Counter()

    for f in coverage.get("files", []):
        path = f["path"]
        status = f["coverage_status"]
        source = f.get("source", "")
        meta = f.get("metadata", {})

        owner = derive_owner(path, status, source, reg_owners.get(path, ""), {}, debt_owners.get(path, {}), meta)

        route = routing.get("routing", {}).get(status, {})
        reviewer = route.get("reviewer_route", "governance-core maintainer")
        approver = route.get("approver_route", "governance-core maintainer")
        requires_review = route.get("mutation_requires_review", False)
        requires_approver = route.get("authority_mutation_requires_approver", False) or route.get("closing_requires_approver", False)

        obj = {
            "path": path,
            "coverage_status": status,
            "owner": owner,
            "reviewer_route": reviewer,
            "approver_route": approver,
            "mutation_requires_review": requires_review,
            "mutation_requires_approver": requires_approver,
        }

        if not owner or owner in ("", "unknown", "REQUIRES IMMEDIATE RESOLUTION"):
            ownerless.append(obj)

        objects.append(obj)
        counts[status] += 1

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "generated_view",
        "stats": {"total": len(objects), "ownerless": len(ownerless), "by_status": dict(counts)},
        "ownerless": [o["path"] for o in ownerless],
        "objects": objects[:50],  # sample — full set in generated file
        "not_claimed": ["human identity system", "external governance", "PolicyActivation", "full closure"],
    }


def main() -> int:
    data = generate()
    (OUTPUT_DIR / "coverage-review-routing.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    # Generate markdown
    lines = [
        "# Coverage Review Routing",
        "",
        "> **GENERATED VIEW — DO NOT EDIT**",
        "> Owner ≠ Reviewer. Reviewer ≠ Approver. Routing ≠ Authorization.",
        "",
        f"Total coverage objects: {data['stats']['total']}",
        f"Ownerless: {data['stats']['ownerless']}",
        "",
        "## Status → Owner → Reviewer → Approver",
        "",
        "| Status | Owner Source | Reviewer | Approver | Review Required |",
        "|---|---|---|---|---|",
    ]
    routing = json.loads(ROUTING.read_text())
    for st, r in routing.get("routing", {}).items():
        owner_src = r.get("owner_source", "")[:40]
        reviewer = r.get("reviewer_route", "")[:30]
        approver = r.get("approver_route", "")[:30]
        review_req = "yes" if r.get("mutation_requires_review") else "no"
        lines.append(f"| {st} | {owner_src} | {reviewer} | {approver} | {review_req} |")

    if data["ownerless"]:
        lines.append("")
        lines.append("## Ownerless Objects")
        for p in data["ownerless"][:10]:
            lines.append(f"- `{p}`")

    lines.extend(["", "---", "```text", "Full Closure: NOT CLAIMED.", "```"])
    (OUTPUT_DIR / "_coverage-review-routing.md").write_text("\n".join(lines) + "\n")

    print(f"Coverage Review Routing: {data['stats']['total']} objects")
    print(f"Ownerless: {data['stats']['ownerless']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
