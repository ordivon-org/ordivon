"""EGB-3 Operating Governance checker.

Shadow-first. Read-only. No network, agent, tool, token, or external action.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EGB3_DOC = ROOT / "docs" / "governance" / "egb-3-operating-governance.md"
REDTEAM_LEDGER = ROOT / "docs" / "governance" / "egb3-operating-governance-redteam.jsonl"
MATURITY_LEDGER = ROOT / "docs" / "governance" / "checker-maturity-ledger.jsonl"
CHECKERS_DIR = ROOT / "checkers"
OEP_DIR = ROOT / "docs" / "governance"

ALLOWED_OEP_STATUSES = {
    "draft",
    "shadow_tested",
    "red_teamed",
    "owner_reviewed",
    "active_or_closed",
}

REQUIRED_DOC_PHRASES = [
    "draft -> shadow_tested -> red_teamed -> owner_reviewed -> active_or_closed",
    "Warnings are evidence",
    "Trust budget counts must be split into",
    "EGB-3 does not promote any EGB-2 checker by default",
]

SAFE_CONTEXT = re.compile(
    r"\b(?:not|no|does\s+not|must\s+not|cannot|separate|shadow-first|evidence\s+only|presented\s+as|described\s+as)\b",
    re.IGNORECASE,
)

VIOLATION_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "reviewer_approver_confusion": [
        re.compile(r"\breviewer[s]?\b.{0,80}\b(?:approve|approves|approved|approval)\b", re.IGNORECASE),
        re.compile(r"\breviewer\s+approval\b", re.IGNORECASE),
    ],
    "ownerless_approval": [
        re.compile(r"\b(?:approval|approved|approver)\b.{0,100}\b(?:without|missing|no)\s+owner\b", re.IGNORECASE),
        re.compile(r"\b(?:owner\s+missing|no\s+owner)\b.{0,100}\b(?:approval|approved|approver)\b", re.IGNORECASE),
    ],
    "shadow_hard_laundering": [
        re.compile(
            r"\bshadow(?:[-\s]?tested| checker| checkers)?\b.{0,100}\b(?:hard\s+gate|pr-fast|blocking|blocks\s+PR|must\s+pass\s+for\s+merge)\b",
            re.IGNORECASE,
        ),
    ],
    "freeze_authorization": [
        re.compile(r"\bfreeze(?: protocol| state)?\b.{0,100}\b(?:authorizes|approves|permits|allows)\b", re.IGNORECASE),
    ],
    "trust_budget_expansion": [
        re.compile(
            r"\btrust\s+budget\b.{0,120}\b(?:spent|exceeded|negative)\b.{0,120}\b(?:continue|expand|new\s+scope|ship|release)\b",
            re.IGNORECASE,
        ),
    ],
}


@dataclass(frozen=True)
class CheckerResult:
    status: str
    exit_code: int
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    entries: list[dict] = []
    errors: list[str] = []
    if not path.exists():
        return entries, [f"missing JSONL ledger: {path.relative_to(ROOT)}"]
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)}:{lineno}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.relative_to(ROOT)}:{lineno}: entry must be object")
            continue
        entries.append(value)
    return entries, errors


def _safe_context(text: str, start: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    if line_end == -1:
        line_end = len(text)
    return bool(SAFE_CONTEXT.search(text[line_start:line_end]))


def detect_operating_violations(text: str) -> list[str]:
    violations: list[str] = []
    for violation_id, patterns in VIOLATION_PATTERNS.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                if _safe_context(text, match.start()):
                    continue
                violations.append(violation_id)
                break
            if violation_id in violations:
                break
    return sorted(set(violations))


def validate_redteam_ledger(path: Path = REDTEAM_LEDGER) -> list[str]:
    entries, load_errors = _load_jsonl(path)
    errors = list(load_errors)
    seen: set[str] = set()

    for entry in entries:
        case_id = str(entry.get("case_id", ""))
        expected = str(entry.get("expected_violation", ""))
        text = str(entry.get("text", ""))
        if not case_id:
            errors.append("redteam entry missing case_id")
        if case_id in seen:
            errors.append(f"{case_id}: duplicate case_id")
        seen.add(case_id)
        if expected not in VIOLATION_PATTERNS:
            errors.append(f"{case_id}: unknown expected_violation '{expected}'")
            continue
        if not text.strip():
            errors.append(f"{case_id}: missing text")
            continue
        actual = detect_operating_violations(text)
        if expected not in actual:
            errors.append(f"{case_id}: expected {expected}, detected {actual}")

    required_cases = {
        "reviewer_approver_confusion",
        "ownerless_approval",
        "shadow_hard_laundering",
        "freeze_authorization",
        "trust_budget_expansion",
    }
    covered = {str(e.get("expected_violation", "")) for e in entries}
    for missing in sorted(required_cases - covered):
        errors.append(f"missing EGB-3 red-team coverage: {missing}")
    return errors


def _extract_oep_status(text: str) -> str | None:
    match = re.search(r"^\s*-\s*status:\s*([A-Za-z0-9_-]+)\s*$", text, re.MULTILINE)
    if match:
        return match.group(1)
    match = re.search(r"^Status:\s*\*\*([^*]+)\*\*", text, re.MULTILINE)
    if match:
        return match.group(1).strip().lower()
    return None


def validate_oep_lifecycle(path: Path, text: str) -> list[str]:
    name = str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    errors: list[str] = []
    status = _extract_oep_status(text)
    if not status:
        return [f"{name}: missing OEP lifecycle status"]
    if status not in ALLOWED_OEP_STATUSES:
        errors.append(f"{name}: invalid EGB-3 OEP status '{status}'")

    lower = text.lower()
    if status in {"shadow_tested", "red_teamed", "owner_reviewed", "active_or_closed"} and "shadow" not in lower:
        errors.append(f"{name}: {status} requires shadow evidence language")
    if (
        status in {"red_teamed", "owner_reviewed", "active_or_closed"}
        and "red-team" not in lower
        and "red team" not in lower
    ):
        errors.append(f"{name}: {status} requires red-team evidence language")
    if status in {"owner_reviewed", "active_or_closed"} and "owner review" not in lower:
        errors.append(f"{name}: {status} requires owner review language")
    return errors


def validate_egb3_document(path: Path = EGB3_DOC) -> list[str]:
    if not path.exists():
        return [f"missing EGB-3 document: {path.relative_to(ROOT)}"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing phrase '{phrase}'")
    unsafe = detect_operating_violations(text)
    if unsafe:
        errors.append(f"{path.relative_to(ROOT)}: unsafe operating-governance wording {unsafe}")
    return errors


def _parse_checker_frontmatter(checker_id: str) -> dict:
    checker_md = CHECKERS_DIR / checker_id.replace("_", "-") / "CHECKER.md"
    if not checker_md.exists():
        return {}
    text = checker_md.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data: dict[str, str] = {}
    for raw in parts[1].splitlines():
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        data[key.strip()] = value.strip().strip("'\"")
    return data


def validate_shadow_first_boundaries(path: Path = MATURITY_LEDGER) -> list[str]:
    entries, load_errors = _load_jsonl(path)
    errors = list(load_errors)
    for entry in entries:
        if str(entry.get("maturity", "")).lower() != "shadow_tested":
            continue
        checker_id = str(entry.get("checker_id", ""))
        frontmatter = _parse_checker_frontmatter(checker_id)
        if not frontmatter:
            errors.append(f"{checker_id}: shadow_tested checker missing CHECKER.md frontmatter")
            continue
        if frontmatter.get("hardness") == "hard":
            errors.append(f"{checker_id}: shadow_tested checker cannot declare hardness=hard")
        profiles = frontmatter.get("profiles", "")
        if "pr-fast" in profiles:
            errors.append(f"{checker_id}: shadow_tested checker cannot be in pr-fast profile")
        notes = str(entry.get("notes", ""))
        if "not pr-fast" not in notes.lower() and "escalation only" not in notes.lower():
            errors.append(f"{checker_id}: maturity notes must state escalation/not-pr-fast boundary")
    return errors


def run() -> CheckerResult:
    findings: list[str] = []
    findings.extend(validate_egb3_document())
    findings.extend(validate_redteam_ledger())
    findings.extend(validate_shadow_first_boundaries())

    oeps = sorted(OEP_DIR.glob("oep-000*.md"))
    for path in oeps:
        findings.extend(validate_oep_lifecycle(path, path.read_text(encoding="utf-8")))

    stats = {
        "oeps": len(oeps),
        "redteam_cases": len(_load_jsonl(REDTEAM_LEDGER)[0]) if REDTEAM_LEDGER.exists() else 0,
        "findings": len(findings),
    }
    return CheckerResult(
        "fail" if findings else "pass",
        1 if findings else 0,
        findings,
        stats,
    )


if __name__ == "__main__":
    result = run()
    print(f"EGB-3 operating governance: {'PASS' if result.exit_code == 0 else 'FAIL'}")
    print(f"OEPs: {result.stats.get('oeps', 0)}")
    print(f"Red-team cases: {result.stats.get('redteam_cases', 0)}")
    for finding in result.findings:
        print(f"  {finding}")
    sys.exit(result.exit_code)
