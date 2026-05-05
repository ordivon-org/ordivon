#!/usr/bin/env python3
"""PGI-1.02 philosophical claim checker.

Local static checker for false-comfort claim patterns. It is intentionally
narrow: it detects narrative/feeling/certainty language being used as evidence.

Output is review evidence only. It does not authorize action.
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


SAFE_CONTEXTS = [
    r"not\s+guarantee",
    r"not\s+guaranteed",
    r"does\s+not\s+guarantee",
    r"not\s+prove",
    r"does\s+not\s+prove",
    r"not\s+evidence",
    r"not\s+authorization",
    r"not\s+authority",
    r"cannot\s+prove",
    r"no\s+claim\s+that",
    r"risk\s+remains",
    r"uncertain",
    r"requires\s+evidence",
    r"evidence\s+required",
    r"review\s+required",
]


RULES: list[tuple[str, str, re.Pattern[str], str, str]] = [
    (
        "PGI-CLAIM-001",
        "blocking",
        re.compile(
            r"\b(?:story|narrative|vision|philosophy|roadmap)\b.{0,100}"
            r"\b(?:proves|guarantees|validates|means)\b.{0,100}"
            r"\b(?:complete|true|safe|correct|success|ready)\b",
            re.IGNORECASE,
        ),
        "Narrative or roadmap language is being used as proof.",
        "Name the claim, cite evidence, and state uncertainty or missing evidence.",
    ),
    (
        "PGI-CLAIM-002",
        "blocking",
        re.compile(
            r"\b(?:I|we)\s+(?:feel|believe|sense)\b.{0,100}"
            r"\b(?:therefore|so|proves|means)\b.{0,100}"
            r"\b(?:true|complete|safe|ready|correct)\b",
            re.IGNORECASE,
        ),
        "Feeling or belief is being used as evidence.",
        "Replace feeling-as-proof with evidence, confidence, and review boundary.",
    ),
    (
        "PGI-CLAIM-003",
        "warning",
        re.compile(
            r"\b(?:guaranteed|no\s+risk|always\s+safe|cannot\s+fail|will\s+succeed|certainly\s+safe)\b",
            re.IGNORECASE,
        ),
        "Uncalibrated certainty language detected.",
        "Add uncertainty, failure path, downside, or explicit safe negation.",
    ),
]


def _is_safe_context(line: str) -> bool:
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in SAFE_CONTEXTS)


def _iter_text_files(paths: list[Path]) -> list[Path]:
    extensions = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml"}
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file() and path.suffix in extensions:
            files.append(path)
            continue
        if path.is_dir():
            files.extend(
                p
                for p in sorted(path.rglob("*"))
                if p.is_file() and p.suffix in extensions and ".git/" not in str(p) and "docs/archive/" not in str(p)
            )
    return files


def scan_paths(paths: list[Path]) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    files = _iter_text_files(paths)

    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        rel = str(path.relative_to(ROOT)) if str(path).startswith(str(ROOT)) else str(path)
        for lineno, line in enumerate(lines, 1):
            if _is_safe_context(line):
                continue
            for rule_id, severity, pattern, explanation, recommended_fix in RULES:
                match = pattern.search(line)
                if match:
                    findings.append(
                        Finding(
                            rule_id=rule_id,
                            severity=severity,
                            file=rel,
                            line=lineno,
                            match=match.group(0)[:200],
                            explanation=explanation,
                            recommended_fix=recommended_fix,
                        )
                    )

    stats = {
        "files_scanned": len(files),
        "findings": len(findings),
        "blocking": sum(1 for f in findings if f.severity == "blocking"),
        "warning": sum(1 for f in findings if f.severity == "warning"),
    }
    return findings, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check philosophical claim false-comfort patterns.")
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    findings, stats = scan_paths([Path(p) for p in args.paths])

    if args.json:
        print(
            json.dumps(
                {
                    "tool": "pgi-philosophical-claim-checker",
                    "stats": stats,
                    "findings": [f.to_dict() for f in findings],
                    "disclaimer": "Findings are review evidence only; they do not authorize action.",
                },
                indent=2,
            )
        )
    else:
        print("PGI Philosophical Claim Checker")
        print(f"  files scanned: {stats['files_scanned']}")
        print(f"  findings:      {stats['findings']}")
        print(f"  blocking:      {stats['blocking']}")
        print(f"  warning:       {stats['warning']}")
        if findings:
            print()
            for finding in findings:
                print(f"{finding.file}:{finding.line} [{finding.severity}] {finding.rule_id}")
                print(f"  {finding.match}")
                print(f"  {finding.recommended_fix}")

    return 1 if stats["blocking"] else 0


if __name__ == "__main__":
    sys.exit(main())
