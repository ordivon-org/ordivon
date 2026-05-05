#!/usr/bin/env python3
"""PGI-1.04 current truth protocol checker.

Detects two high-signal risks:
- current truth described as permanent/final/unsupersedable
- source_of_truth registry entries missing freshness metadata

Findings are review evidence only; this checker does not authorize action.
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


PERMANENT_TRUTH_RE = re.compile(
    r"\bcurrent[_ -]?truth\b.{0,100}\b(?:permanent|forever|final|cannot\s+be\s+superseded|never\s+changes)\b",
    re.IGNORECASE,
)

SAFE_RE = re.compile(
    r"not\s+permanent|not\s+final|can\s+be\s+superseded|current\s+truth\s+is\s+revisable",
    re.IGNORECASE,
)


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
                if p.is_file() and p.suffix in {".md", ".jsonl", ".json"} and "docs/archive/" not in str(p)
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
            match = PERMANENT_TRUTH_RE.search(line)
            if match:
                findings.append(
                    Finding(
                        rule_id="PGI-TRUTH-001",
                        severity="blocking",
                        file=rel,
                        line=lineno,
                        match=match.group(0)[:200],
                        explanation="current_truth is being described as permanent or unsupersedable.",
                        recommended_fix="State that current truth is revisable and can be superseded by fresher source_of_truth.",
                    )
                )

            if path.suffix == ".jsonl":
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("authority") == "source_of_truth" and obj.get("status") == "current":
                    missing = [k for k in ("last_verified", "stale_after_days") if k not in obj]
                    if missing:
                        findings.append(
                            Finding(
                                rule_id="PGI-TRUTH-002",
                                severity="blocking",
                                file=rel,
                                line=lineno,
                                match=obj.get("doc_id", "(unknown)"),
                                explanation=f"source_of_truth registry entry missing freshness fields: {', '.join(missing)}.",
                                recommended_fix="Add last_verified and stale_after_days to current source_of_truth entries.",
                            )
                        )

    stats = {
        "files_scanned": len(files),
        "findings": len(findings),
        "blocking": sum(1 for f in findings if f.severity == "blocking"),
    }
    return findings, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check current truth freshness and supersession risks.")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    findings, stats = scan_paths([Path(p) for p in args.paths])
    payload = {
        "tool": "pgi-current-truth-protocol-checker",
        "stats": stats,
        "findings": [f.to_dict() for f in findings],
        "disclaimer": "Findings are review evidence only; they do not authorize action.",
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("PGI Current Truth Protocol Checker")
        print(f"  files scanned: {stats['files_scanned']}")
        print(f"  findings:      {stats['findings']}")
        print(f"  blocking:      {stats['blocking']}")
        for finding in findings:
            print(f"{finding.file}:{finding.line} [{finding.severity}] {finding.rule_id}")
            print(f"  {finding.match}")
            print(f"  {finding.recommended_fix}")
    return 1 if stats["blocking"] else 0


if __name__ == "__main__":
    sys.exit(main())
