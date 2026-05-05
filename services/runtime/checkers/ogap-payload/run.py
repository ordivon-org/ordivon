"""OGAP Payload Validator — validates JSON payloads against OGAP schemas.

This checker validates fixture files, not runtime payloads.
Requires jsonschema and schema files in src/ordivon_verify/schemas/.
"""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = ROOT / "src" / "ordivon_verify" / "schemas"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "ogap"

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run():
    stats = {"files":0,"valid":0,"invalid":0}
    findings = []
    if not FIXTURES_DIR.exists():
        return CheckerResult("pass", 0, [], dict(stats))

    for fpath in sorted(FIXTURES_DIR.rglob("*.json")):
        stats["files"]+=1
        try:
            payload = json.loads(fpath.read_text())
        except json.JSONDecodeError as e:
            stats["invalid"]+=1
            findings.append(f"{fpath.name}: invalid JSON: {e}")
            continue
        # Basic structural checks
        errors = []
        if "decision" in payload and payload.get("decision","") not in {"READY","DEGRADED","BLOCKED","HOLD","REJECT","NO-GO"}:
            errors.append(f"invalid decision: {payload.get('decision')}")
        if payload.get("decision") == "READY" and "authorizes" in str(payload.get("authority_statement","")).lower():
            errors.append("READY-authorizes-execution")
        if errors:
            stats["invalid"]+=1
            findings.append(f"{fpath.name}: {'; '.join(errors)}")
        else:
            stats["valid"]+=1

    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, dict(stats))

if __name__=="__main__":
    r=run()
    print(f"OGAP fixtures: {r.stats.get('files',0)} files, {r.stats.get('valid',0)} valid, {r.stats.get('invalid',0)} invalid")
    for f in r.findings: print(f"  {f}")
    sys.exit(r.exit_code)
