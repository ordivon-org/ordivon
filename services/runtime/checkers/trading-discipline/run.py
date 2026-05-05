"""Trading Discipline Fixture Checker — validates intake test fixtures.

Checks that test fixtures for Finance Pack trading discipline are
well-formed JSON and have required fields.
"""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIRS = [
    ROOT / "tests" / "unit" / "finance",
    ROOT / "tests" / "fixtures" / "finance",
]

REQUIRED = {"thesis", "stop_loss", "max_loss_usdt", "position_size_usdt", "risk_unit_usdt", "emotional_state"}

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run() -> CheckerResult:
    findings, stats = [], {"files": 0, "valid": 0, "invalid": 0, "missing_fields": 0}
    for d in FIXTURE_DIRS:
        if not d.exists(): continue
        for fpath in sorted(d.rglob("*.json")):
            stats["files"] += 1
            try:
                payload = json.loads(fpath.read_text())
            except json.JSONDecodeError as e:
                stats["invalid"] += 1
                findings.append(f"{fpath.name}: {e}")
                continue

            # Check for intake-like structure (has thesis/stop_loss fields)
            if any(k in payload for k in ("thesis", "stop_loss", "trade_type")):
                missing = [k for k in REQUIRED if k not in payload or not payload[k]]
                if missing:
                    stats["missing_fields"] += 1
                    findings.append(f"{fpath.name}: missing {missing}")
                else:
                    stats["valid"] += 1
            else:
                stats["valid"] += 1  # Not an intake fixture, just valid JSON

    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, dict(stats))

if __name__ == "__main__":
    r = run()
    s = r.stats
    print(f"Fixtures: {s.get('files',0)} | Valid: {s.get('valid',0)} | Invalid: {s.get('invalid',0)} | Missing: {s.get('missing_fields',0)}")
    for f in r.findings: print(f"  {f}")
    sys.exit(r.exit_code)
