"""PGI Failure Predicate Validator — validates PGI fixture payloads."""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "pgi_failure_predicate"

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run():
    stats = {"files":0,"valid":0,"invalid":0}
    findings = []
    if not FIXTURES.exists():
        return CheckerResult("pass",0,[],dict(stats))
    for fpath in sorted(FIXTURES.rglob("*.json")):
        stats["files"]+=1
        try:
            json.loads(fpath.read_text())
            stats["valid"]+=1
        except json.JSONDecodeError as e:
            stats["invalid"]+=1
            findings.append(f"{fpath.name}: {{e}}")
    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, dict(stats))

if __name__=="__main__":
    r=run(); label = "PGI"; print(f"{label}: {r.stats.get('files',0)} files | Invalid: {r.stats.get('invalid',0)}")
    for f in r.findings: print(f"  {f}"); sys.exit(r.exit_code)
