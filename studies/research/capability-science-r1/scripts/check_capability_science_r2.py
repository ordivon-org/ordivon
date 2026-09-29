#!/usr/bin/env python3
"""R2 acceptance for the first heterogeneous synthetic digital-world loop."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from synthetic_world_r2 import evaluate_selected_roundtrip


STUDY = Path(__file__).resolve().parents[1]
REPO = STUDY.parents[2]


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()

    result = evaluate_selected_roundtrip()
    require(result["standing"] == "BOUNDED_HETEROGENEOUS_DISCOVERY_LOOP_EXECUTED", "synthetic loop standing mismatch")
    require(result["enumeratedRoundtripCount"] >= 2, "search must enumerate more than one persistent typed roundtrip")
    circuit = result["selectedCircuit"]
    require(circuit["sourceType"] == "Payload" and circuit["boundaryType"] == "Handle", "selected semantic boundary mismatch")
    require(circuit["storePath"] == ["encode", "publish"], "unexpected outward path")
    require(circuit["recoverPath"] == ["resolve", "render"], "unexpected inward path")
    require(result["observations"]["recover_after_local_forget"]["payloadRecovered"] is True, "same-world recovery failed")
    require(result["observations"]["recover_in_fresh_session"]["payloadRecovered"] is True, "fresh-session recovery failed")
    novelty = result["novelty"]
    require(novelty["verdict"] == "CERTIFIED_NOVEL_WITHIN_BOUNDED_POLICY", "R5 did not admit the discovered composition")
    require(len(novelty["witnesses"]) == 2, "candidate requires one distinguishing witness per baseline")
    require(result["authorityGranted"] is False and result["executionAuthorityGranted"] is False, "discovery must not grant authority")

    checks = [
        "synthetic-world:heterogeneous-components-executed",
        "synthetic-world:typed-path-search-enumerated-multiple-roundtrips",
        "synthetic-world:persistent-payload-roundtrip-discovered",
        "synthetic-world:fresh-session-recovery-reproduced",
        "synthetic-world:r5-bounded-novelty-admission-pass",
        "synthetic-world:no-authority-grant",
    ]
    tracked = [
        STUDY / "scripts" / "synthetic_world_r2.py",
        STUDY / "scripts" / "run_synthetic_world_r2.py",
        STUDY / "scripts" / "check_capability_science_r2.py",
        STUDY / "tests" / "test_synthetic_world_r2.py",
    ]
    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.capability-science-r2-acceptance",
        "standing": "R2_SYNTHETIC_HETEROGENEOUS_LOOP_ACCEPTED_BOUNDED",
        "sourceRevision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "checks": checks,
        "discovery": result,
        "artifactDigests": {str(path.relative_to(REPO)): digest(path) for path in tracked},
        "authorityGranted": False,
        "executionAuthorityGranted": False,
        "domainAcceptanceEstablished": False,
        "nonClaims": result["nonClaims"],
    }
    if args.write_evidence:
        output = STUDY / "evidence" / "capability-science-r2-synthetic-loop.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
