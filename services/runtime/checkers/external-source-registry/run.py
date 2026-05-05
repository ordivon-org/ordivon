"""External Source Registry Checker — validates EGB-2 benchmark sources."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "governance" / "external-benchmark-source-registry.jsonl"

REQUIRED_FIELDS = {
    "source_id",
    "source_name",
    "source_url",
    "source_kind",
    "owner_area",
    "last_checked",
    "source_version_or_date",
    "use_allowed",
    "use_forbidden",
    "ordivon_mapping",
    "freshness_days",
    "notes",
}

REQUIRED_FORBIDDEN = {
    "compliance_claim",
    "certification_claim",
    "endorsement_claim",
    "partnership_claim",
    "equivalence_claim",
    "public_standard_claim",
    "authorization_claim",
}

OVERCLAIM_PATTERNS = [
    re.compile(r"\b(?:certified|certification|compliant|compliance)\b", re.IGNORECASE),
    re.compile(r"\b(?:endorsed|endorsement|partnership|partnered)\b", re.IGNORECASE),
    re.compile(r"\b(?:equivalent|equivalence)\b", re.IGNORECASE),
    re.compile(r"\bpublic\s+standard\b", re.IGNORECASE),
    re.compile(r"\bproduction[-\s]?ready\b", re.IGNORECASE),
    re.compile(r"\b(?:authorizes|authorized)\b", re.IGNORECASE),
    re.compile(r"\bauthorization\s+claim\b", re.IGNORECASE),
    re.compile(r"\bSLSA\s+level\s+\d+\b", re.IGNORECASE),
]

SAFE_CONTEXTS = [
    re.compile(r"\b(?:not|no|without|forbidden|does\s+not|must\s+not)\b", re.IGNORECASE),
    re.compile(r"\buse_forbidden\b", re.IGNORECASE),
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
        return entries, [f"missing registry: {path}"]
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"line {lineno}: entry must be object")
            continue
        entries.append(value)
    return entries, errors


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"https", "http"} and bool(parsed.netloc)


def _is_safe_context(text: str, match_start: int) -> bool:
    window = text[max(0, match_start - 40) : match_start + 80]
    return any(pattern.search(window) for pattern in SAFE_CONTEXTS)


def _scan_overclaim(entry: dict) -> list[str]:
    errors: list[str] = []
    fields_to_scan = [
        "source_name",
        "source_kind",
        "owner_area",
        "source_version_or_date",
        "notes",
    ]
    fields_to_scan.extend(str(v) for v in entry.get("use_allowed", []))
    fields_to_scan.extend(str(v) for v in entry.get("ordivon_mapping", []))
    text = " | ".join(str(entry.get(f, "")) for f in fields_to_scan[:5])
    text = text + " | " + " | ".join(fields_to_scan[5:])
    for pattern in OVERCLAIM_PATTERNS:
        for match in pattern.finditer(text):
            if _is_safe_context(text, match.start()):
                continue
            errors.append(
                f"{entry.get('source_id', '?')}: unsafe external benchmark claim '{match.group(0)}'"
            )
    return errors


def validate_entries(entries: list[dict], reference_date: date | None = None) -> list[str]:
    reference_date = reference_date or date.today()
    errors: list[str] = []
    seen: set[str] = set()

    for index, entry in enumerate(entries, 1):
        sid = str(entry.get("source_id", f"line-{index}"))
        missing = sorted(REQUIRED_FIELDS - set(entry))
        if missing:
            errors.append(f"{sid}: missing required fields: {missing}")
            continue

        if sid in seen:
            errors.append(f"{sid}: duplicate source_id")
        seen.add(sid)

        if not _valid_url(str(entry.get("source_url", ""))):
            errors.append(f"{sid}: source_url must be http(s) URL")

        for list_field in ("use_allowed", "use_forbidden", "ordivon_mapping"):
            value = entry.get(list_field)
            if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
                errors.append(f"{sid}: {list_field} must be a non-empty list of strings")

        forbidden = set(entry.get("use_forbidden", []))
        missing_forbidden = sorted(REQUIRED_FORBIDDEN - forbidden)
        if missing_forbidden:
            errors.append(f"{sid}: use_forbidden missing {missing_forbidden}")

        try:
            last_checked = date.fromisoformat(str(entry.get("last_checked", "")))
        except ValueError:
            errors.append(f"{sid}: last_checked must be YYYY-MM-DD")
            last_checked = reference_date

        freshness_days = entry.get("freshness_days")
        if not isinstance(freshness_days, int) or isinstance(freshness_days, bool) or freshness_days <= 0:
            errors.append(f"{sid}: freshness_days must be positive integer")
        elif (reference_date - last_checked).days > freshness_days:
            errors.append(
                f"{sid}: source is stale ({(reference_date - last_checked).days}d > {freshness_days}d)"
            )

        errors.extend(_scan_overclaim(entry))

    return errors


def run() -> CheckerResult:
    entries, load_errors = load_jsonl(REGISTRY)
    errors = list(load_errors)
    if not load_errors:
        errors.extend(validate_entries(entries))
    return CheckerResult(
        "fail" if errors else "pass",
        1 if errors else 0,
        errors,
        {"entries": len(entries), "errors": len(errors), "registry": str(REGISTRY)},
    )


if __name__ == "__main__":
    result = run()
    print(f"External source registry: {'PASS' if result.exit_code == 0 else 'FAIL'}")
    print(f"Entries: {result.stats.get('entries', 0)}")
    for finding in result.findings:
        print(f"  {finding}")
    sys.exit(result.exit_code)
