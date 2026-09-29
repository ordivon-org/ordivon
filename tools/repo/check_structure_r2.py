#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_CANCELLED = {"S3", "S4", "S6", "S7", "S9"}
EXPECTED_RETAINED = {
    "S5-targeted-meta-next-residual-disposition",
    "S8-evidence-driven-contract-fitness",
}


class StructureR2Error(ValueError):
    pass


def validate_plan(value: dict[str, Any], *, repo_root: Path | None = None) -> None:
    _ = repo_root
    if value.get("schemaVersion") != 1:
        raise StructureR2Error("schemaVersion must be 1")
    if value.get("kind") != "ordivon.repository-structure-transition":
        raise StructureR2Error("unexpected plan kind")
    if value.get("truthRole") != "repository-placement-plan-not-runtime-or-domain-authority":
        raise StructureR2Error("unexpected truthRole")
    if value.get("status") != "superseded":
        raise StructureR2Error("Structure R2 must remain superseded")
    if value.get("supersededBy") != "docs/architecture/ARCHITECTURE_REANCHOR_R1.md":
        raise StructureR2Error("Structure R2 must point to Architecture Re-Anchor R1")
    if value.get("openSlices") != []:
        raise StructureR2Error("superseded Structure R2 cannot retain open slices")
    if set(value.get("remainingPathMovesCancelled", [])) != EXPECTED_CANCELLED:
        raise StructureR2Error("cancelled path-only waves drifted")
    if set(value.get("retainedConvergenceWork", [])) != EXPECTED_RETAINED:
        raise StructureR2Error("retained convergence work drifted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", nargs="?", default="docs/architecture/structure-r2-transition-r1.json")
    parser.add_argument("--skip-source-existence", action="store_true")
    args = parser.parse_args()
    path = Path(args.plan)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise StructureR2Error("plan root must be an object")
        validate_plan(value)
    except (OSError, json.JSONDecodeError, StructureR2Error) as exc:
        print(f"structure r2 supersession check failed: {exc}")
        return 2
    print(f"structure r2 supersession check passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
