"""HAP Payload Validator — validates HAP protocol fixture files."""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "hap"
EXAMPLES_DIR = ROOT / "examples" / "hap"

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run():
    stats = {"files":0,"valid":0,"invalid":0}
    findings = []
    for d in (FIXTURES_DIR, EXAMPLES_DIR):
        if not d.exists(): continue
        for fpath in sorted(d.rglob("*.json")):
            stats["files"]+=1
            try:
                payload = json.loads(fpath.read_text())
            except json.JSONDecodeError as e:
                stats["invalid"]+=1; findings.append(f"{fpath.name}: {e}"); continue
            stats["valid"]+=1

    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, dict(stats))

if __name__=="__main__":
    r=run(); print(f"HAP fixtures: {r.stats.get('files',0)} | Invalid: {r.stats.get('invalid',0)}")
    for f in r.findings: print(f"  {f}"); sys.exit(r.exit_code)
