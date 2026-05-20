#!/usr/bin/env python3
"""Receipt Claim Extractor — extract executable claims from governance receipts.

Usage:
    python3 scripts/governance/extract_receipt_claims.py <receipt.md>
    python3 scripts/governance/extract_receipt_claims.py --phase AOS-1

Extracts:
    - Fenced code blocks with command-like content
    - Declared validation results (e.g. "Valid fixtures: 1/1 passed")
    - Expected exit codes
    - Expected output patterns

Output:
    JSON with claim_id, command, expected exit_code, expected_patterns.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Patterns for extracting claims from receipt markdown
COMMAND_PATTERN = re.compile(r"^[\$>]\s*(.+)$|^```(?:bash|shell|sh|text)?\s*\n(.*?)\n```", re.MULTILINE | re.DOTALL)
VALIDATION_RESULT_PATTERN = re.compile(
    r"(Valid fixtures?:?\s*[\d]+/[\d]+\s*passed[\s\S]*?"
    r"(?:Invalid fixtures?:?\s*[\d]+/[\d]+\s*(?:correctly )?rejected[\s\S]*?)?)",
    re.IGNORECASE,
)
PASS_FAIL_PATTERN = re.compile(r"(all|[\d]+)\s*(passed|failed)", re.IGNORECASE)
EXIT_CODE_HINT = re.compile(r"exit(?:\s*code)?\s*[:=]?\s*(\d+)", re.IGNORECASE)


def extract_claims(receipt_path: Path) -> list[dict]:
    """Extract claims from a receipt markdown file."""
    content = receipt_path.read_text()
    claims = []

    # Find code blocks with shell commands
    code_blocks = re.findall(r"```(?:bash|shell|sh|text)?\s*\n(.*?)\n```", content, re.DOTALL)

    claim_id = 0
    for block in code_blocks:
        lines = block.strip().split("\n")
        commands = []
        outputs = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("$ ") or stripped.startswith("> "):
                commands.append(stripped[2:])
            elif stripped and not stripped.startswith("#"):
                outputs.append(stripped)

        if commands:
            claim_id += 1
            claim = {
                "claim_id": f"{receipt_path.stem}-CLAIM-{claim_id:03d}",
                "source_file": str(receipt_path.relative_to(ROOT)),
                "commands": commands,
                "declared_outputs": outputs,
                "expected_exit_code": None,
                "expected_patterns": [],
            }

            # Extract exit code hints
            for line in lines:
                em = EXIT_CODE_HINT.search(line)
                if em:
                    claim["expected_exit_code"] = int(em.group(1))

            # Extract expected patterns from outputs
            for out in outputs:
                vm = VALIDATION_RESULT_PATTERN.search(out)
                if vm:
                    claim["expected_patterns"].append(vm.group(0).strip())
                else:
                    pm = PASS_FAIL_PATTERN.search(out)
                    if pm:
                        claim["expected_patterns"].append(pm.group(0))
                    elif out:
                        claim["expected_patterns"].append(out.strip())

            claims.append(claim)

    return claims


def extract_phase_claims(phase: str) -> list[dict]:
    """Extract claims from all receipts for a phase."""
    receipts_dir = ROOT / "receipts/governance"
    all_claims = []

    phase_lower = phase.lower()
    for receipt_path in sorted(receipts_dir.glob(f"{phase_lower}*.md")):
        claims = extract_claims(receipt_path)
        all_claims.extend(claims)

    return all_claims


def main():
    if not sys.argv[1:]:
        print("Usage: extract_receipt_claims.py <receipt.md>")
        print("       extract_receipt_claims.py --phase AOS-1")
        return 1

    if sys.argv[1] == "--phase":
        if len(sys.argv) < 3:
            print("Usage: extract_receipt_claims.py --phase AOS-1")
            return 1
        claims = extract_phase_claims(sys.argv[2])
    else:
        path = Path(sys.argv[1]).resolve()
        if not path.exists():
            print(f"Receipt not found: {path}")
            return 1
        claims = extract_claims(path)

    print(json.dumps(claims, indent=2))
    print(f"\nExtracted {len(claims)} claims", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
