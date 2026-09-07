#!/usr/bin/env python3
from __future__ import annotations
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINDINGS = [
    {
        "id": "F13_BEHAVIOR_POLICY_RUNTIME_COPY_R1",
        "source": ROOT / "f13-behavior/creature_behavior_policy.gd",
        "target": ROOT / "godot/vendor/f13/creature_behavior_policy.gd",
        "expected_sha256": "8ad2a4f449969444dd27b1b5c28956e80de368070a0de0b03f3a901370e4a847",
    },
]

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    for binding in BINDINGS:
        source = binding["source"]
        target = binding["target"]
        expected = binding["expected_sha256"]
        if not source.is_file():
            raise SystemExit(f"missing authoritative producer source: {source}")
        actual = sha256(source)
        if actual != expected:
            raise SystemExit(f"producer source digest changed for {binding['id']}: expected={expected} actual={actual}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        copied = sha256(target)
        if copied != expected:
            raise SystemExit(f"runtime copy digest mismatch for {binding['id']}: {copied}")
        print(f"VEILWILD_A17_RUNTIME_INPUT_SYNC_PASS id={binding['id']} sha256={copied}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
