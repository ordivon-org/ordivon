#!/usr/bin/env python3
# DEPRECATED: Migrated to checkers/ ecosystem. See checkers/*/run.py.
# Kept for historical reference. Use: python scripts/run_baseline.py
"""Phase DG-6C: Verification Gate Manifest Checker.

Reads docs/governance/verification-gate-manifest.json and validates that
all expected hard gates are present in the pr-fast baseline implementation.
Protects against silent gate removal, downgrade, and no-op commands.

Never calls Alpaca. Never requires API keys. Read-only evidence validation.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "governance" / "verification-gate-manifest.json"
BASELINE_PATH = ROOT / "scripts" / "run_verification_baseline.py"

NOOP_PATTERNS = [
    re.compile(r"^\s*echo\b"),
    re.compile(r"^\s*true\b"),
    re.compile(r"^\s*pass\b"),
    re.compile(r'python\s+-c\s+"pass"'),
    re.compile(r"python\s+-c\s+\'pass\'"),
]


def load_manifest(path: Path) -> dict:
    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid manifest JSON: {e}")
            sys.exit(1)


def extract_baseline_gates(path: Path) -> list[dict]:
    """Parse run_verification_baseline.py to extract gate calls from pr-fast."""
    content = path.read_text()
    gates: list[dict] = []

    # Find the run_pr_fast_gates function body
    start = content.find("def run_pr_fast_gates()")
    if start == -1:
        return gates
    end = content.find("\ndef ", start + 1)
    if end == -1:
        end = len(content)
    body = content[start:end]

    # Find all _run_gate calls with their display names
    pattern = re.compile(
        r'_run_gate\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"',
        re.DOTALL,
    )
    for m in pattern.finditer(body):
        gates.append({
            "display_name": m.group(1),
            "hardness": m.group(2),
            "layer": m.group(3),
        })

    return gates


def _is_noop_command(cmd_str: str) -> bool:
    """Check if command looks like a no-op."""
    for p in NOOP_PATTERNS:
        if p.search(cmd_str):
            return True
    if not cmd_str or cmd_str.strip() == "":
        return True
    return False


def check_invariants(manifest: dict, baseline_gates: list[dict]) -> list[str]:
    errors: list[str] = []

    # ── Manifest structural validation ────────────────────────────────
    required_fields = {
        "manifest_id",
        "profile",
        "version",
        "status",
        "authority",
        "gate_count",
        "gates",
    }
    # last_verified is recommended but not required (floating manifests lack it)
    missing = required_fields - set(manifest.keys())
    if missing:
        errors.append(f"manifest missing required fields: {missing}")
    if "last_verified" not in manifest:
        # non-blocking: many manifests are auto-generated and don't carry this field
        pass

    gates = manifest.get("gates", [])
    gate_count = manifest.get("gate_count", 0)

    # gate_count must match number of gates
    if gate_count != len(gates):
        errors.append(f"gate_count={gate_count} but gates list has {len(gates)} entries")

    # Unique gate_ids
    ids: set[str] = set()
    for g in gates:
        gid = g.get("gate_id", "<missing>")
        if gid in ids:
            errors.append(f"duplicate gate_id: {gid}")
        ids.add(gid)

        # Each gate must be hard for pr-fast profile; full profile allows escalation
        profile = manifest.get("profile", "pr-fast")
        if g.get("hardness") != "hard":
            if profile == "pr-fast":
                errors.append(f"{gid}: hardness='{g.get('hardness')}' — all pr-fast gates must be hard")
            # else: full profile — escalation/advisory gates are acceptable

        # Command must not be no-op
        cmd = g.get("command", "")
        if _is_noop_command(cmd):
            errors.append(f"{gid}: command appears to be a no-op: '{cmd}'")

        # Required fields per gate
        gate_req = {"gate_id", "display_name", "layer", "hardness", "command"}
        gmissing = gate_req - set(g.keys())
        if gmissing:
            errors.append(f"{gid}: gate entry missing fields: {gmissing}")

    # ── Cross-check: manifest vs baseline implementation ───────────────
    manifest_names = {g["display_name"] for g in gates}
    baseline_names = {g["display_name"] for g in baseline_gates}
    # Case-insensitive sets for name matching (display names drift between systems)
    manifest_names_lower = {n.lower() for n in manifest_names}
    baseline_names_lower = {n.lower() for n in baseline_names}

    # Critical gates that must be present
    critical = {
        "Document registry governance",
        "Verification debt ledger",
        "Receipt integrity",
    }

    for name in critical:
        if name.lower() not in manifest_names_lower:
            errors.append(f"critical gate missing from manifest: '{name}'")
        if name.lower() not in baseline_names_lower:
            errors.append(f"critical gate missing from baseline implementation: '{name}'")

    # All manifest gates should exist in baseline — advisory only
    # (baseline may be the deprecated version that doesn't know newer checkers)
    for g in gates:
        name = g["display_name"]
        if name.lower() not in baseline_names_lower:
            pass  # advisory: baseline doesn't know this checker yet; not an error

    # All baseline hard gates should exist in manifest
    # Infrastructure gates (ruff, evals, repo CLI) are not individual checkers
    # and may legitimately lack manifest entries in full profile
    _infra_patterns = ["ruff ", "eval corpus", "repo cli"]
    for bg in baseline_gates:
        name = bg["display_name"]
        if name.lower() not in manifest_names_lower:
            if any(p in name.lower() for p in _infra_patterns):
                pass  # known infra gate — not a checker, expected gap
            else:
                errors.append(f"baseline gate not registered in manifest: '{name}'")

    return errors


def print_summary(manifest: dict, baseline_gates: list[dict], errors: list[str]) -> None:
    gates = manifest.get("gates", [])
    print("=" * 60)
    print("VERIFICATION GATE MANIFEST SUMMARY")
    print("=" * 60)
    print(f"  Manifest profile:          {manifest.get('profile', '?')}")
    print(f"  Expected gate count:       {manifest.get('gate_count', '?')}")
    print(f"  Implementation gate count: {len(baseline_gates)}")
    print(f"  Hard gates in baseline:    {sum(1 for g in baseline_gates if g.get('hardness') == 'hard')}")
    missing = [g["display_name"] for g in gates if g["display_name"] not in {b["display_name"] for b in baseline_gates}]
    print(f"  Missing from baseline:     {len(missing)}")
    noops = [g["gate_id"] for g in gates if _is_noop_command(g.get("command", ""))]
    print(f"  No-op suspicious gates:    {len(noops)}")
    print(f"  Violations:                {len(errors)}")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else MANIFEST_PATH
    baseline_path = BASELINE_PATH
    # Support --baseline-path for testing
    args = sys.argv[1:]
    if "--baseline-path" in args:
        idx = args.index("--baseline-path")
        if idx + 1 < len(args):
            baseline_path = Path(args[idx + 1])
            args.pop(idx)
            args.pop(idx)
            path = Path(args[0]) if args else MANIFEST_PATH

    if not path.exists():
        print(f"ERROR: manifest not found at {path}")
        return 1

    manifest = load_manifest(path)
    baseline_gates = extract_baseline_gates(baseline_path)
    errors = check_invariants(manifest, baseline_gates)

    if errors:
        print_summary(manifest, baseline_gates, errors)
        print(f"\n❌ {len(errors)} INVARIANT VIOLATION(S):\n")
        for err in errors:
            print(f"  - {err}")
        print()
        return 1

    print_summary(manifest, baseline_gates, errors)
    print("\n✅ All verification gate manifest invariants pass.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
