#!/usr/bin/env python3
"""Advisory checker: skill-safety (OPA-powered)

Uses OPA/Rego policy evaluation instead of naive Python string matching.
Advisory only — produces warnings, never blocks.

Usage:
    python3 checkers/skill-safety/run.py [--path skills/ordivon-core-method/SKILL.md]
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

WARNINGS = []
PASS = True


def check_with_opa(target_path: Path) -> None:
    """Use OPA overclaim detection on SKILL.md files."""
    global PASS
    
    try:
        from ordivon_governance_core.opa_engine import check_overclaim_dir, opa_available
        
        if not opa_available():
            WARNINGS.append("OPA not available — falling back.")
            return
        
        if target_path.is_file():
            import tempfile, shutil
            tmpdir = Path(tempfile.mkdtemp())
            shutil.copy(target_path, tmpdir / target_path.name)
            findings = check_overclaim_dir(str(tmpdir))
            shutil.rmtree(tmpdir)
        else:
            findings = check_overclaim_dir(str(target_path))
        
        for f in findings:
            severity = f.get("severity", "WARN")
            desc = f.get("description", str(f))
            WARNINGS.append(f"  [{severity}] {desc}")
            if severity == "BLOCKING":
                PASS = False
                
    except ImportError:
        WARNINGS.append("OPA engine not available — ordivon_governance_core.opa_engine import failed.")
    except Exception as e:
        WARNINGS.append(f"OPA evaluation error: {e}")


def check_boundary_declarations(path: Path) -> None:
    """Lightweight boundary checks that don't need OPA."""
    global PASS
    content = path.read_text().lower()
    
    boundaries = [
        ("draft", "Skill does not declare outputs as drafts"),
        ("do not use when", "Skill lacks deactivation conditions"),
        ("not: a system", "Skill does not declare what it is NOT"),
        ("not: an authority", "Skill does not declare it is not an authority"),
    ]
    for pattern, msg in boundaries:
        if pattern not in content:
            WARNINGS.append(f"  MISSING: {msg}")
            PASS = False


def main():
    target = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--path" else (
        sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "skills"))
    
    if "--path" in sys.argv:
        idx = sys.argv.index("--path")
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else str(ROOT / "skills")
    
    target_path = Path(target)
    
    print("=== skill-safety advisory check (OPA-powered) ===")
    
    if target_path.is_file():
        print(f"\n--- {target_path.relative_to(ROOT)} ---")
        check_with_opa(target_path)
        check_boundary_declarations(target_path)
    elif target_path.is_dir():
        for skill_md in target_path.rglob("SKILL.md"):
            print(f"\n--- {skill_md.relative_to(ROOT)} ---")
            check_with_opa(skill_md)
            check_boundary_declarations(skill_md)
    
    print(f"\n=== Result: {'PASS' if PASS else 'ADVISORY WARNINGS'} ===")
    if WARNINGS:
        print(f"  {len(WARNINGS)} advisory finding(s):")
        for w in WARNINGS:
            print(w)
        print("\n  Advisory only — not blocking gates. Powered by OPA/Rego.")
    else:
        print("  No boundary violations. OPA/Rego evaluation clean.")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
