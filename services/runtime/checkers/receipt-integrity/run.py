#!/usr/bin/env python3
"""Advisory checker: receipt-integrity

Scans receipt JSON files for honesty violations.
Advisory only — produces warnings, never blocks.

Checks:
- Receipt has evidence (not just claims in evidence field)
- Receipt declares remaining_debt
- Receipt has draft flag (not self-sealed)
- Receipt status matches evidence
- Receipt has verification_result

Usage:
    python3 checkers/receipt-integrity/run.py [--path receipts/]
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

WARNINGS = []
PASS = True


def check_receipt(path: Path) -> None:
    global PASS
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        WARNINGS.append(f"  {path.name}: not valid JSON — {e}")
        PASS = False
        return
    
    name = path.name
    
    # Check evidence field
    evidence = data.get("evidence", "")
    if isinstance(evidence, str):
        if len(evidence) < 50:
            WARNINGS.append(f"  {name}: evidence field is very short ({len(evidence)} chars) — may be a claim, not evidence")
            PASS = False
        claim_words = ["completed successfully", "all good", "no issues", "done", "finished"]
        for cw in claim_words:
            if cw in evidence.lower():
                WARNINGS.append(f"  {name}: evidence contains claim-like language: '{cw}'")
                PASS = False
    
    # Check remaining_debt
    debt = data.get("remaining_debt", data.get("remaining debt", None))
    if debt is None:
        WARNINGS.append(f"  {name}: missing remaining_debt field")
        PASS = False
    elif isinstance(debt, list) and len(debt) == 0:
        WARNINGS.append(f"  {name}: remaining_debt is empty — suspicious for closure")
        PASS = False
    elif isinstance(debt, str) and debt.lower() in ("none", "n/a", "na", ""):
        WARNINGS.append(f"  {name}: remaining_debt is '{debt}' — verify this is not overclaim")
        PASS = False
    
    # Check draft flag
    draft = data.get("draft", None)
    if draft is False:
        WARNINGS.append(f"  {name}: draft is false — receipt appears self-sealed")
        PASS = False
    elif draft is None and data.get("status") == "PASS":
        WARNINGS.append(f"  {name}: no draft flag + status PASS — may be self-sealed")
        PASS = False
    
    # Check status consistency
    status = data.get("status", "")
    degraded_reasons = data.get("degraded_reasons", [])
    if status == "PASS" and degraded_reasons:
        WARNINGS.append(f"  {name}: status is PASS but degraded_reasons present — inconsistent")
        PASS = False
    
    # Check verification
    verification = data.get("verification_result", data.get("verification", ""))
    if isinstance(verification, str) and len(verification) < 20:
        WARNINGS.append(f"  {name}: verification_result is very short — may lack specific checks")
        PASS = False


def main():
    target = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--path" else (
        sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "receipts"))
    
    if "--path" in sys.argv:
        idx = sys.argv.index("--path")
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else str(ROOT / "receipts")
    
    target_path = Path(target)
    
    print("=== receipt-integrity advisory check ===")
    
    if not target_path.exists():
        print(f"Not found: {target}")
        return
    
    for receipt_file in sorted(target_path.rglob("*.json")):
        print(f"\n--- {receipt_file.relative_to(ROOT)} ---")
        check_receipt(receipt_file)
    
    print(f"\n=== Result: {'PASS' if PASS else 'ADVISORY WARNINGS'} ===")
    if WARNINGS:
        print(f"  {len(WARNINGS)} advisory finding(s):")
        for w in WARNINGS:
            print(w)
        print("\n  These are ADVISORY only — not blocking gates.")
        print("  Receipt theater risk: check if warnings indicate false completion.")
    else:
        print("  All receipts pass integrity check.")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
