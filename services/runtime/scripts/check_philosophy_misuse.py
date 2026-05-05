#!/usr/bin/env python3
"""PGI-1.09 philosophical misuse checker.

Detects high-signal cases where philosophical language rationalizes overwork,
gambling, evidence bypass, emotional suppression, or responsibility avoidance.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Finding:
    rule_id: str
    severity: str
    file: str
    line: int
    match: str
    explanation: str
    recommended_fix: str

    def to_dict(self) -> dict:
        return self.__dict__


RULES = [
    (
        "PGI-MISUSE-001",
        re.compile(r"\blong[- ]term(?:ism)?\b.{0,120}\b(?:ignore sleep|sacrifice (?:the )?body|no rest|burn out)\b", re.I),
        "Long-termism used to rationalize overwork or body neglect.",
        "Run Anti-Overforce review and Body/Energy boundary check.",
    ),
    (
        "PGI-MISUSE-002",
        re.compile(r"\bfreedom\b.{0,120}\b(?:all[- ]in|high leverage|gamble|double down)\b", re.I),
        "Freedom language used to rationalize gambling or fragility.",
        "Run Finance Pack risk gate with max-loss and FOMO/self-proof screen.",
    ),
    (
        "PGI-MISUSE-003",
        re.compile(r"\bdiscipline\b.{0,120}\b(?:ignore fatigue|suppress emotion|ignore emotion|push through pain)\b", re.I),
        "Discipline language used to suppress valid body/emotion signals.",
        "Classify the signal before increasing effort.",
    ),
    (
        "PGI-MISUSE-004",
        re.compile(r"\b(?:existential|meaning|destiny)\b.{0,120}\b(?:ignore evidence|skip evidence|bypass evidence)\b", re.I),
        "Meaning language used to bypass evidence.",
        "Restore EvidenceRecord requirement and uncertainty review.",
    ),
    (
        "PGI-MISUSE-005",
        re.compile(r"\b(?:non[- ]attachment|wu wei|daoism|let it flow)\b.{0,120}\b(?:avoid responsibility|no review|do nothing)\b", re.I),
        "Non-attachment/non-force language used to avoid responsibility.",
        "Separate non-force from avoidance; create review or refusal receipt.",
    ),
    (
        "PGI-MISUSE-006",
        re.compile(r"\bpragmatism\b.{0,120}\b(?:ignore principle|skip evidence|bypass boundary|shortcut)\b", re.I),
        "Pragmatism used to justify unprincipled shortcuts.",
        "Check Constitution boundary and evidence before action.",
    ),
]

SAFE_RE = re.compile(r"red-team|unsafe fixture|do\s+not\b|must\s+not\b|not a justification|misuse", re.I)


def _iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                p
                for p in sorted(path.rglob("*"))
                if p.is_file() and p.suffix in {".md", ".txt", ".json", ".jsonl"}
            )
    return files


def scan_paths(paths: list[Path]) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    files = _iter_files(paths)
    for path in files:
        rel = str(path.relative_to(ROOT)) if str(path).startswith(str(ROOT)) else str(path)
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            if SAFE_RE.search(line):
                continue
            for rule_id, pattern, explanation, fix in RULES:
                match = pattern.search(line)
                if match:
                    findings.append(
                        Finding(
                            rule_id=rule_id,
                            severity="blocking",
                            file=rel,
                            line=lineno,
                            match=match.group(0)[:200],
                            explanation=explanation,
                            recommended_fix=fix,
                        )
                    )
    stats = {
        "files_scanned": len(files),
        "findings": len(findings),
        "blocking": len(findings),
    }
    return findings, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check philosophical misuse patterns.")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    findings, stats = scan_paths([Path(p) for p in args.paths])
    payload = {
        "tool": "pgi-philosophy-misuse-checker",
        "stats": stats,
        "findings": [f.to_dict() for f in findings],
        "disclaimer": "Findings are review evidence only; they do not authorize action.",
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("PGI Philosophy Misuse Checker")
        print(f"  files scanned: {stats['files_scanned']}")
        print(f"  findings:      {stats['findings']}")
        for finding in findings:
            print(f"{finding.file}:{finding.line} [{finding.rule_id}] {finding.match}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
