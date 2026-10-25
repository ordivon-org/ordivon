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


def test_runtime_pg_historical_detail_is_not_automatically_migration_valuable() -> None:
    """Native issue evidence cannot promote obsolete detail from counts alone."""
    row = next(x for x in _read()["issues"] if x["id"] == "DB-PG-RUNTIME-20261026")
    audit = row["latestRetentionAudit"]
    assert audit["disposition"] == "NOT_ADMITTED_NO_PHYSICAL_CUTOVER_OR_ROW_RETIREMENT"
    assert audit["observedCounts"]["jobs"] == audit["observedCounts"]["idempotencyKeys"]
    assert audit["observedCounts"]["stdoutMetadata"] > 0
    assert audit["observedCounts"]["stderrMetadata"] > 0
    assert audit["observedCounts"]["terminalJobsObserved"] < audit["observedCounts"]["jobs"]
    assert "NOT an atomic" in audit["observationScope"]
    assert "Terminal(Job) does NOT imply RetireHistory(Job)" in audit["formalObligation"]
    assert "ReplayIdentityStillUnique" in audit["formalObligation"]
    assert "ExternalEffectStillNonrepeatable" in audit["formalObligation"]
    assert "OwnerNativePostgresReadbackEquivalent" in audit["formalObligation"]
    assert len(audit["requiredNativeCounterexamples"]) >= 4
    for evidence in audit["consumerSourceFiles"]:
        assert (ROOT / evidence).is_file(), evidence
    module.validate_formal_issue_census(_read(), _plans())
