"""Ownership Manifest Checker — validates EGB-2 path-native ownership."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "governance" / "ownership-manifest.jsonl"

REQUIRED_FIELDS = {
    "path_pattern",
    "reviewers",
    "approvers",
    "owner_role",
    "backup_owner",
    "staleness_days",
    "emeritus_reviewers",
    "notes",
}

REQUIRED_PATTERNS = {
    "docs/governance/**",
    "docs/product/**",
    "docs/architecture/**",
    "docs/runtime/**",
    "docs/ai/**",
    "src/ordivon_verify/**",
    "checkers/**",
    "scripts/**",
    "tests/**",
    "stage-templates/**",
}

DANGEROUS_APPROVAL = [
    re.compile(r"\b(?:authorizes|authorized|authorization)\b", re.IGNORECASE),
    re.compile(r"\bapproved\s+for\s+(?:merge|release|deploy|deployment|publication|trading|external\s+action)\b", re.IGNORECASE),
    re.compile(r"\brelease\s+approval\b", re.IGNORECASE),
]

SAFE_CONTEXT = [
    re.compile(r"\b(?:not|no|does\s+not|must\s+not|without)\b", re.IGNORECASE),
    re.compile(r"\bevidence,\s+not\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class CheckerResult:
    status: str
    exit_code: int
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    entries: list[dict] = []
    errors: list[str] = []
    if not path.exists():
        return entries, [f"missing manifest: {path}"]
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: invalid JSON: {exc}")
            continue
        if not isinstance(entry, dict):
            errors.append(f"line {lineno}: entry must be object")
            continue
        entries.append(entry)
    return entries, errors


def _safe_context(text: str, start: int) -> bool:
    window = text[max(0, start - 50) : start + 100]
    return any(pattern.search(window) for pattern in SAFE_CONTEXT)


def _scan_notes(entry: dict) -> list[str]:
    notes = str(entry.get("notes", ""))
    errors: list[str] = []
    for pattern in DANGEROUS_APPROVAL:
        for match in pattern.finditer(notes):
            if _safe_context(notes, match.start()):
                continue
            errors.append(
                f"{entry.get('path_pattern', '?')}: unsafe ownership authority wording '{match.group(0)}'"
            )
    return errors


def validate_entries(entries: list[dict], required_patterns: set[str] | None = None) -> list[str]:
    required_patterns = required_patterns or REQUIRED_PATTERNS
    errors: list[str] = []
    seen: set[str] = set()

    for index, entry in enumerate(entries, 1):
        pattern = str(entry.get("path_pattern", f"line-{index}"))
        missing = sorted(REQUIRED_FIELDS - set(entry))
        if missing:
            errors.append(f"{pattern}: missing required fields: {missing}")
            continue
        if pattern in seen:
            errors.append(f"{pattern}: duplicate path_pattern")
        seen.add(pattern)

        for field_name in ("reviewers", "approvers", "emeritus_reviewers"):
            value = entry.get(field_name)
            if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
                errors.append(f"{pattern}: {field_name} must be list of strings")
        if not entry.get("reviewers"):
            errors.append(f"{pattern}: reviewers must not be empty")
        if not entry.get("approvers"):
            errors.append(f"{pattern}: approvers must not be empty")

        for field_name in ("owner_role", "backup_owner", "notes"):
            value = entry.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{pattern}: {field_name} must be non-empty string")

        staleness = entry.get("staleness_days")
        if not isinstance(staleness, int) or isinstance(staleness, bool) or staleness <= 0:
            errors.append(f"{pattern}: staleness_days must be positive integer")

        errors.extend(_scan_notes(entry))

    missing_coverage = sorted(required_patterns - {str(e.get("path_pattern", "")) for e in entries})
    for missing in missing_coverage:
        errors.append(f"missing required ownership coverage: {missing}")

    return errors


def run() -> CheckerResult:
    entries, load_errors = load_jsonl(MANIFEST)
    findings = list(load_errors)
    if not load_errors:
        findings.extend(validate_entries(entries))
    return CheckerResult(
        "fail" if findings else "pass",
        1 if findings else 0,
        findings,
        {"entries": len(entries), "findings": len(findings)},
    )


if __name__ == "__main__":
    result = run()
    print(f"Ownership manifest: {'PASS' if result.exit_code == 0 else 'FAIL'}")
    print(f"Entries: {result.stats.get('entries', 0)}")
    for finding in result.findings:
        print(f"  {finding}")
    sys.exit(result.exit_code)
