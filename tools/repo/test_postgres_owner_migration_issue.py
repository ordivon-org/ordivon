"""Formal-first PostgreSQL cutover census; no alternative registry or false deployment claims."""

import copy
import json
from pathlib import Path

import pytest

from tools.repo.test_architecture_docs import module

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261025_R1.json"
ISSUES = {
    "DB-PG-RUNTIME-20261026": ("services/runtime", "rust"),
    "DB-PG-HARNESS-20261026": ("services/harness", "run"),
    "DB-PG-CAPITAL-20261026": ("domains/capital", "accounting"),
    "DB-PG-MEDIA-20261026": ("capabilities/media", "hash"),
}


def _read():
    return json.loads(CENSUS.read_text(encoding="utf-8"))


def _plans():
    paths = ("tools/repo/planning/lego-plan-r1.json", "services/runtime/planning/lego-plan-r1.json")
    return {path: json.loads((ROOT / path).read_text(encoding="utf-8")) for path in paths}


def test_pg_cutover_requires_owner_specific_consumers_and_actual_recovery_proof() -> None:
    d = _read()
    selected = {x["id"]: x for x in d["issues"] if x["id"] in ISSUES}
    assert set(selected) == set(ISSUES)
    assert len({x["id"] for x in d["issues"]}) == len(d["issues"])
    for issue_id, (owner, semantic) in ISSUES.items():
        issue = selected[issue_id]
        assert issue["naturalOwner"] == owner
        assert issue["problemClass"] == "DATABASE_AUTHORITY_CONVERGENCE"
        assert issue["registration"]["state"] == "UNREGISTERED"
        assert semantic in (issue["consumers"] + issue["formalObligation"]).lower()
        obligation = issue["formalObligation"]
        assert all(x in obligation for x in (
            "SnapshotByteComplete", "LogicalMappingBijection", "ReplayReconciliationPass",
            "OwnerNativeRecoveryPass", "RollbackSourceRetained",
        ))
        assert issue["requalification"]["sourceCut"]
    module.validate_formal_issue_census(d, _plans())


def test_pg_migration_cannot_claim_verified_owner_registration_from_census_only() -> None:
    d = _read()
    issue = next(x for x in d["issues"] if x["id"] == "DB-PG-RUNTIME-20261026")
    assert issue["registration"]["state"] == "UNREGISTERED"
    unsupported = copy.deepcopy(d)
    row = next(x for x in unsupported["issues"] if x["id"] == issue["id"])
    row["registration"] = {
        "state": "LINKED",
        "ownerPlan": "services/runtime/planning/lego-plan-r1.json",
        "slice": "RW-NONEXISTENT-DB-MIGRATION",
    }
    with pytest.raises(module.ArchitectureDocsError):
        module.validate_formal_issue_census(unsupported, _plans())
