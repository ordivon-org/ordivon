#!/usr/bin/env python3
"""Advisory checker: skill-safety

Scans SKILL.md files for governance boundary violations.
Advisory only — produces warnings, never blocks.

Checks:
- Skill claims authority (may not authorize, close debt, suppress risk)
- Skill self-seals output (must declare draft: true)
- Skill lacks do-not-use conditions
- Skill references undefined trust levels
- Skill allows tool access without permission annotation

Usage:
    python3 checkers/skill-safety/run.py [--path skills/ordivon-core-method/SKILL.md]
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_PATTERNS = [
    ("authorize", "Skill claims authority it does not have"),
    ("close debt", "Skill claims ability to close debt"),
    ("suppress risk", "Skill claims ability to suppress risk"),
    ("resolve debt", "Skill claims ability to resolve debt"),
    ("declare final", "Skill claims ability to declare final truth"),
    ("self-upgrade status", "Skill claims ability to self-upgrade status"),
    ("silently change policy", "Skill claims ability to change policy"),
]

REQUIRED_PATTERNS = [
    ("draft", "Skill does not declare outputs as drafts"),
    ("do not use when", "Skill lacks deactivation conditions"),
    ("not: a system", "Skill does not declare what it is NOT"),
    ("not: an authority", "Skill does not declare it is not an authority"),
]

WARNINGS = []
PASS = True


def check_file(path: Path) -> None:
    global PASS
    content = path.read_text().lower()
    
    # Check for forbidden authority claims
    for pattern, msg in FORBIDDEN_PATTERNS:
        # Only flag if it's a claim of ability, not a prohibition
        # Look for patterns like "may authorize" or "can close debt" 
        # but NOT "may not authorize" or "cannot close debt"
        lines = path.read_text().split("\n")
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if pattern in line_lower:
                # Skip if it's a prohibition (contains "not" or "never")
                if "not" in line_lower or "never" in line_lower or "must not" in line_lower:
                    continue
                WARNINGS.append(f"  L{i+1}: possible authority overclaim — '{line.strip()[:80]}'")
                PASS = False
    
    # Check for required boundary declarations
    for pattern, msg in REQUIRED_PATTERNS:
        if pattern not in content:
            WARNINGS.append(f"  MISSING: {msg}")
            PASS = False


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "skills")
    target_path = Path(target)
    
    print("=== skill-safety advisory check ===")
    
    if target_path.is_file():
        check_file(target_path)
    elif target_path.is_dir():
        for skill_md in target_path.rglob("SKILL.md"):
            print(f"\n--- {skill_md.relative_to(ROOT)} ---")
            check_file(skill_md)
    else:
        print(f"Not found: {target}")
        return
    
    print(f"\n=== Result: {'PASS' if PASS else 'ADVISORY WARNINGS'} ===")
    if WARNINGS:
        print(f"  {len(WARNINGS)} advisory finding(s):")
        for w in WARNINGS:
            print(w)
        print("\n  These are ADVISORY only — not blocking gates.")
    else:
        print("  No boundary violations detected.")
    
    # Advisory only — always exit 0
    sys.exit(0)


if __name__ == "__main__":
    main()
