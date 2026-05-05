"""OEP Governance Checker — validates Ordivon Enhancement Proposals."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OEP_DIR = ROOT / "docs" / "governance"

REQUIRED_HEADINGS = [
    "## Summary",
    "## Required Metadata",
    "## Motivation",
    "## Non-Goals",
    "## Design",
    "## Alternatives",
    "## Risks",
    "## Security Review",
    "## Test Plan",
    "## Rollback Plan",
    "## Graduation Criteria",
    "## Authority Boundary",
]

REQUIRED_METADATA = [
    "oep_id:",
    "title:",
    "owner:",
    "status:",
    "affected_layers:",
    "authority_impact:",
    "public_surface_impact:",
]

DANGEROUS_AUTHORIZATION = [
    re.compile(r"\b(?:authorizes|authorized|authorization)\s+(?:merge|release|deploy|deployment|publication|trading|external\s+action|policy\s+activation)\b", re.IGNORECASE),
    re.compile(r"\bapproved\s+for\s+(?:merge|release|deploy|deployment|publication|trading|external\s+action)\b", re.IGNORECASE),
    re.compile(r"\bready\s+for\s+(?:merge|release|deploy|deployment|publication|trading)\b", re.IGNORECASE),
]

SAFE_AUTHORITY_CONTEXTS = [
    re.compile(r"\b(?:does\s+not|not|no|without|non[-\s]?authorization|evidence\s+only)\b", re.IGNORECASE),
    re.compile(r"\bno\s+action\s+authorization\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class CheckerResult:
    status: str
    exit_code: int
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def discover_oeps(root: Path = OEP_DIR) -> list[Path]:
    return sorted(root.glob("oep-000*.md"))


def _safe_context(text: str, start: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    return any(pattern.search(line) for pattern in SAFE_AUTHORITY_CONTEXTS)


def validate_oep_text(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    name = str(path.relative_to(ROOT)) if path.is_absolute() else str(path)

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"{name}: missing heading '{heading}'")

    for key in REQUIRED_METADATA:
        if key not in text:
            errors.append(f"{name}: missing metadata '{key}'")

    lower = text.lower()
    if "no public standard" not in lower and "public standard" not in lower:
        errors.append(f"{name}: non-goals must address public-standard boundary")
    if "rollback" not in lower:
        errors.append(f"{name}: missing rollback language")
    if "graduation" not in lower:
        errors.append(f"{name}: missing graduation language")
    if "security" not in lower:
        errors.append(f"{name}: missing security review language")

    for pattern in DANGEROUS_AUTHORIZATION:
        for match in pattern.finditer(text):
            if _safe_context(text, match.start()):
                continue
            errors.append(f"{name}: unsafe authorization language '{match.group(0)}'")

    return errors


def run() -> CheckerResult:
    findings: list[str] = []
    oeps = discover_oeps()
    if not oeps:
        findings.append("no OEP documents found (expected docs/governance/oep-000*.md)")
    for path in oeps:
        try:
            findings.extend(validate_oep_text(path, path.read_text(encoding="utf-8")))
        except OSError as exc:
            findings.append(f"{path}: read error: {exc}")
    return CheckerResult(
        "fail" if findings else "pass",
        1 if findings else 0,
        findings,
        {"oeps": len(oeps), "findings": len(findings)},
    )


if __name__ == "__main__":
    result = run()
    print(f"OEP governance: {'PASS' if result.exit_code == 0 else 'FAIL'}")
    print(f"OEPs: {result.stats.get('oeps', 0)}")
    for finding in result.findings:
        print(f"  {finding}")
    sys.exit(result.exit_code)
