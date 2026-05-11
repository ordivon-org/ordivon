#!/usr/bin/env python3
"""Verify generated path map matches repo reality (GOS-PM-1).

Regenerates path map to a temp location and compares with committed version.
Detects drift: manual edits to generated files, unclassified protected paths.

Usage:
    python scripts/verify-path-map.py          # CI mode (exit 1 on drift)
    python scripts/verify-path-map.py --json   # Machine-readable
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/governance/generated"


def verify() -> tuple[bool, dict]:
    """Save committed version, regenerate, compare. Returns (pass, stats)."""
    json_path = OUTPUT_DIR / "path-map.json"
    if not json_path.exists():
        return False, {"error": "path-map.json not found — run update-path-map.py first"}

    # STEP 1: Save committed version BEFORE regeneration
    committed = json.loads(json_path.read_text())

    # STEP 2: Regenerate (this overwrites the file on disk)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/update-path-map.py")],
        capture_output=True, text=True, cwd=str(ROOT), timeout=30
    )

    # STEP 3: Read the freshly regenerated version
    regenerated = json.loads(json_path.read_text())

    # STEP 4: Compare committed (saved) vs regenerated (fresh)
    c_stats = {k: v for k, v in committed.get("stats", {}).items() if k != "generated_at"}
    r_stats = {k: v for k, v in regenerated.get("stats", {}).items() if k != "generated_at"}

    drift = c_stats != r_stats
    blocked = regenerated["stats"].get("blocked", 0) > 0

    # STEP 5: Restore committed version
    json_path.write_text(json.dumps(committed, indent=2, ensure_ascii=False) + "\n")

    return (not drift and not blocked), {
        "committed": c_stats,
        "regenerated": r_stats,
        "drift": drift,
        "blocked": blocked,
    }


def main() -> int:
    as_json = "--json" in sys.argv
    passed, info = verify()

    if as_json:
        output = {
            "status": "READY" if passed else "BLOCKED",
            "drift": info.get("drift", False),
            "blocked": info.get("blocked", False),
            "error": info.get("error"),
        }
        print(json.dumps(output, indent=2))
        return 0 if passed else 1

    if info.get("error"):
        print(f"✗ {info['error']}")
        return 1

    if info.get("drift"):
        print("✗ PATH MAP DRIFT")
        print(f"  Committed:   {info['committed']}")
        print(f"  Regenerated: {info['regenerated']}")
        print("  Run: python scripts/update-path-map.py")
        return 1

    if info.get("blocked"):
        print("✗ BLOCKED FILES DETECTED")
        print(f"  Blocked count: {info['regenerated'].get('blocked', '?')}")
        return 1

    print("✓ Path map consistent with repo reality")
    print(f"  {info['committed'].get('tracked_files','?')} files → "
          f"{info['committed'].get('governed','?')} governed, "
          f"{info['committed'].get('blocked','?')} blocked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
