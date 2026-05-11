#!/usr/bin/env python3
"""Generate gate inventory — discover all PM gates and classify by maturity (N2).

Outputs:
    docs/governance/generated/gate-inventory.json
    docs/governance/generated/_gate-inventory.md
"""

from __future__ import annotations

import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/governance/generated"
VERIFY_MANIFEST = ROOT / "docs/governance/verification-gate-manifest.json"
CI_YML = ROOT / ".github/workflows/ci.yml"

# Gate maturity: DRAFT → ADVISORY → SHADOW → SOFT_BLOCKING → BLOCKING → HARD_BLOCKING
MATURITY_ORDER = {"DRAFT": 0, "ADVISORY": 1, "SHADOW": 2, "SOFT_BLOCKING": 3, "BLOCKING": 4, "HARD_BLOCKING": 5}


def discover_gates() -> list[dict]:
    """Discover all gates from verification-gate-manifest.json + checkers/ directory."""
    gates = []
    seen_ids = set()

    # 1. From gate manifest
    if VERIFY_MANIFEST.exists():
        manifest = json.loads(VERIFY_MANIFEST.read_text())
        for g in manifest.get("gates", []):
            gid = g["gate_id"]
            gates.append({
                "gate_id": gid,
                "display_name": g.get("display_name", gid),
                "source": "verification-gate-manifest.json",
                "command": g.get("command", ""),
                "hardness": g.get("hardness", "advisory"),
                "mode": _hardness_to_mode(g.get("hardness", "advisory")),
                "ci_job": _find_ci_job(gid),
                "owner": "governance-core-maintainer",
                "false_positive_route": f"Check {gid} checker logic and exceptions",
                "rollback_path": "git revert of gate promotion commit",
                "target_mode": _hardness_to_target(g.get("hardness", "advisory")),
                "promotion_criteria": "Negative demo + shadow period (7 days no false positives)",
            })
            seen_ids.add(gid)

    # 2. From checker directory (auto-discovered but not in manifest)
    checkers_dir = ROOT / "checkers"
    if checkers_dir.exists():
        for cd in sorted(checkers_dir.iterdir()):
            if cd.is_dir() and (cd / "CHECKER.md").exists():
                gid = cd.name
                if gid not in seen_ids:
                    gates.append({
                        "gate_id": gid,
                        "display_name": gid.replace("-", " ").title(),
                        "source": "checkers/ auto-discovery",
                        "command": f"uv run python checkers/{gid}/run.py",
                        "hardness": "advisory",
                        "mode": "ADVISORY",
                        "ci_job": _find_ci_job(gid),
                        "owner": "governance-core-maintainer",
                        "false_positive_route": f"Check checkers/{gid}/CHECKER.md",
                        "rollback_path": "git revert",
                        "target_mode": "ADVISORY",
                        "promotion_criteria": "Shadow period before promotion",
                    })
                    seen_ids.add(gid)

    # 3. Script-based gates not in manifest (overclaim, hash, verification)
    script_gates = [
        {"gate_id": "overclaim", "command": "uv run python scripts/detect_overclaim.py docs/", "mode": "ADVISORY"},
        {"gate_id": "hash_ledger", "command": "uv run python scripts/hash_ledger.py --verify docs/governance/dependency-audit-debts.jsonl", "mode": "SHADOW"},
        {"gate_id": "hash_ledger_lesson", "command": "uv run python scripts/hash_ledger.py --verify docs/governance/lesson-ledger.jsonl", "mode": "SHADOW"},
        {"gate_id": "registry_stats", "command": "uv run python scripts/update-registry-stats.py --check", "mode": "BLOCKING"},
        {"gate_id": "literate_ci", "command": "uv run python scripts/check_atomic_governance.py", "mode": "BLOCKING"},
    ]
    for sg in script_gates:
        if sg["gate_id"] not in seen_ids:
            gates.append({
                "gate_id": sg["gate_id"],
                "display_name": sg["gate_id"].replace("_", " ").title(),
                "source": "scripts/",
                "command": sg["command"],
                "hardness": "hard" if sg["mode"] == "BLOCKING" else "advisory",
                "mode": sg["mode"],
                "ci_job": _find_ci_job(sg["gate_id"]),
                "owner": "governance-core-maintainer",
                "false_positive_route": f"Check {sg['gate_id']} script logic",
                "rollback_path": "git revert",
                "target_mode": sg["mode"],
                "promotion_criteria": "N2 gate upgrade receipt",
            })
            seen_ids.add(sg["gate_id"])

    return sorted(gates, key=lambda g: g["gate_id"])


def _hardness_to_mode(hardness: str) -> str:
    return {"hard": "BLOCKING", "escalation": "BLOCKING", "advisory": "ADVISORY"}.get(hardness, "ADVISORY")


def _hardness_to_target(hardness: str) -> str:
    return {"hard": "BLOCKING", "escalation": "SOFT_BLOCKING", "advisory": "SHADOW"}.get(hardness, "SHADOW")


def _find_ci_job(gate_id: str) -> str:
    if not CI_YML.exists():
        return ""
    text = CI_YML.read_text()
    keywords = gate_id.replace("-", " ").replace("_", " ")
    for kw in [gate_id, keywords, gate_id.replace("_", "-")]:
        if kw.lower() in text.lower():
            return f"ci.yml (keyword: {kw})"
    return ""


def generate() -> dict:
    gates = discover_gates()
    mode_counts = {}
    for g in gates:
        mode_counts[g["mode"]] = mode_counts.get(g["mode"], 0) + 1
    blocking = [g for g in gates if g["mode"] in ("BLOCKING", "HARD_BLOCKING")]
    shadow = [g for g in gates if g["mode"] == "SHADOW"]
    advisory = [g for g in gates if g["mode"] == "ADVISORY"]
    blocking_no_ci = [g for g in blocking if not g["ci_job"]]

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "generated_view",
        "stats": {"total": len(gates), "by_mode": mode_counts, "blocking_no_ci_job": len(blocking_no_ci)},
        "gates": gates,
        "findings": [],
        "not_claimed": ["all gates enforced", "full closure", "PolicyActivation"],
    }


def main() -> int:
    data = generate()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "gate-inventory.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    # Markdown
    lines = [
        "# Gate Inventory",
        "",
        "> **GENERATED VIEW — DO NOT EDIT**",
        f"Total gates: {data['stats']['total']}",
        f"Modes: {data['stats']['by_mode']}",
        f"Blocking without CI job: {data['stats']['blocking_no_ci_job']}",
        "",
        "| Gate ID | Mode | CI Job | Owner |",
        "|---|---|---|---|",
    ]
    for g in data["gates"]:
        ci = "✓" if g["ci_job"] else "✗"
        lines.append(f"| {g['gate_id']} | {g['mode']} | {ci} | {g['owner']} |")
    lines.extend(["", "---", "```text", "Full Closure: NOT CLAIMED.", "```"])
    (OUTPUT / "_gate-inventory.md").write_text("\n".join(lines) + "\n")

    print(f"Gate Inventory: {data['stats']['total']} gates")
    for m, c in sorted(data["stats"]["by_mode"].items()):
        print(f"  {m}: {c}")
    if data["stats"]["blocking_no_ci_job"]:
        print(f"  ⚠ {data['stats']['blocking_no_ci_job']} BLOCKING gates without CI job")
    return 0


if __name__ == "__main__":
    sys.exit(main())
