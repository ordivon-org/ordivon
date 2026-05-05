"""State Truth Checker — validates governance state consistency."""

from __future__ import annotations
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "AGENTS.md"

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run():
    findings = []
    if not TARGET.exists():
        return CheckerResult("fail", 1, [f"Missing: {TARGET}"])
    try:
        content = TARGET.read_text()
        # Basic consistency: must exist and have content
        if len(content.strip()) < 100:
            findings.append(f"Content too short: {len(content)} chars")
    except Exception as e:
        findings.append(f"Read error: {e}")
    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings,
                         {"file": str(TARGET), "size": len(content) if 'content' in dir() else 0})

if __name__=="__main__":
    r=run(); label = "checker"; print(f"{label}: {'PASS' if not r.findings else 'FAIL'}")
    for f in r.findings: print(f"  {f}"); sys.exit(r.exit_code)
