from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.social_fabric_coordination_r2 import (
    CANDIDATE,
    DAMAGE,
    INHIBITION,
    SUPPORT,
    compile_coordination_projection,
)
from scripts.social_fabric_r1 import SocialFabricError

ROOT = Path(__file__).resolve().parents[1]
DOGFOOD = (
    ROOT / "evidence/acceptance/social-fabric-coordination-r2-vhd-cut-20260923.json"
)


def _event(
    event_id: str,
    event_type: str,
    *,
    subject: str = "resource:test",
    source: str = "urn:test:agent",
    scope: str = "direct",
    time: str = "2026-09-23T07:00:00+08:00",
    expires: str | None = "2026-09-23T07:10:00+08:00",
    data: dict | None = None,
) -> dict:
    result = {
        "specversion": "1.0",
        "id": event_id,
        "source": source,
        "type": event_type,
        "subject": subject,
        "time": time,
        "datacontenttype": "application/json",
        "ordivonscope": scope,
        "data": data or {"evidenceRefs": []},
    }
    if expires is not None:
        result["ordivonexpiresat"] = expires
    return result


def _candidate(event_id: str, mode: str = "exclusive") -> dict:
    return _event(
        event_id,
        CANDIDATE,
        data={
            "holderRef": f"job:{event_id}",
            "effectOwner": "runtime.windows",
            "operation": "maintain",
            "mode": mode,
            "evidenceRefs": [f"evidence:{event_id}"],
        },
    )


def _cut() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.social-fabric-coordination-cut",
        "observedAt": "2026-09-23T07:05:00+08:00",
        "events": [_candidate("candidate:a")],
        "receptors": [
            {
                "receptorId": "receptor:test",
                "acceptedTypes": [CANDIDATE, DAMAGE],
                "scopes": ["direct"],
                "subjectPrefixes": ["resource:"],
                "sources": [],
                "maxAgeSeconds": 600,
                "requireEvidence": True,
            }
        ],
    }


def test_projection_is_deterministic_and_shadow_only() -> None:
    first = compile_coordination_projection(_cut())
    second = compile_coordination_projection(copy.deepcopy(_cut()))
    assert first == second
    assert first["truthRole"] == "rebuildable-shadow-coordination-projection"
    assert first["candidateStanding"][0]["state"] == "eligible_shadow"
    assert first["commitmentProjection"]["state"] == "NOT_EVALUATED"
    assert first["nonClaims"]


def test_expiry_removes_candidate_from_active_standing() -> None:
    cut = _cut()
    cut["observedAt"] = "2026-09-23T07:11:00+08:00"
    result = compile_coordination_projection(cut)
    assert result["candidateStanding"] == []
    assert result["lifecycle"][0]["status"] == "expired"


def test_refresh_replaces_old_event_without_immortal_warning() -> None:
    cut = _cut()
    old = cut["events"][0]
    old["ordivonexpiresat"] = "2026-09-23T07:06:00+08:00"
    refreshed = copy.deepcopy(old)
    refreshed["id"] = "candidate:a:r2"
    refreshed["time"] = "2026-09-23T07:04:00+08:00"
    refreshed["ordivonexpiresat"] = "2026-09-23T07:14:00+08:00"
    refreshed["ordivonrefreshes"] = "candidate:a"
    cut["events"].append(refreshed)
    result = compile_coordination_projection(cut)
    statuses = {row["eventId"]: row["status"] for row in result["lifecycle"]}
    assert statuses["candidate:a"] == "refreshed"
    assert statuses["candidate:a:r2"] == "active"
    assert [row["candidateEventId"] for row in result["candidateStanding"]] == [
        "candidate:a:r2"
    ]


def test_refresh_cannot_change_subject_or_source() -> None:
    cut = _cut()
    refreshed = copy.deepcopy(cut["events"][0])
    refreshed["id"] = "candidate:a:r2"
    refreshed["time"] = "2026-09-23T07:04:00+08:00"
    refreshed["subject"] = "resource:other"
    refreshed["ordivonrefreshes"] = "candidate:a"
    cut["events"].append(refreshed)
    with pytest.raises(SocialFabricError, match="must preserve type/source/subject"):
        compile_coordination_projection(cut)


def test_retraction_removes_target_from_current_standing() -> None:
    cut = _cut()
    cut["events"].append(
        _event(
            "retract:a",
            "io.ordivon.social.retract.v1",
            time="2026-09-23T07:04:00+08:00",
            data={"targetEventId": "candidate:a", "evidenceRefs": ["receipt:cancel"]},
        )
    )
    result = compile_coordination_projection(cut)
    statuses = {row["eventId"]: row["status"] for row in result["lifecycle"]}
    assert statuses["candidate:a"] == "retracted"
    assert result["candidateStanding"] == []


def test_receptor_honors_scope_freshness_and_evidence() -> None:
    cut = _cut()
    cut["events"].append(
        _event(
            "damage:old",
            DAMAGE,
            time="2026-09-23T06:40:00+08:00",
            expires=None,
            data={"reasonCode": "OLD", "evidenceRefs": ["log:1"]},
        )
    )
    cut["events"].append(
        _event(
            "damage:no-evidence",
            DAMAGE,
            time="2026-09-23T07:04:00+08:00",
            data={"reasonCode": "NO_EVIDENCE", "evidenceRefs": []},
        )
    )
    delivery = compile_coordination_projection(cut)["receptorDeliveries"][0]
    assert delivery["signalIds"] == ["candidate:a"]


def test_exclusive_candidate_conflict_is_symmetric_and_has_no_winner() -> None:
    cut = _cut()
    cut["events"].append(_candidate("candidate:b", "shared"))
    result = compile_coordination_projection(cut)
    standing = {row["candidateEventId"]: row for row in result["candidateStanding"]}
    assert standing["candidate:a"]["state"] == "inhibited_shadow"
    assert standing["candidate:b"]["state"] == "inhibited_shadow"
    assert standing["candidate:a"]["conflictsWith"] == ["candidate:b"]
    assert standing["candidate:b"]["conflictsWith"] == ["candidate:a"]
    assert result["commonOperatingPicture"]["conflictFindingCount"] == 1
    assert "winner" not in result["commitmentProjection"]
    assert "selectedCandidateId" not in result["commitmentProjection"]
    assert all("winner" not in row for row in result["candidateStanding"])


def test_shared_candidates_do_not_conflict() -> None:
    cut = _cut()
    cut["events"][0]["data"]["mode"] = "shared"
    cut["events"].append(_candidate("candidate:b", "shared"))
    result = compile_coordination_projection(cut)
    assert result["commonOperatingPicture"]["conflictFindingCount"] == 0
    assert {row["state"] for row in result["candidateStanding"]} == {"eligible_shadow"}


def test_explicit_inhibition_blocks_shadow_standing_without_authority_claim() -> None:
    cut = _cut()
    cut["events"].append(
        _event(
            "inhibit:a",
            INHIBITION,
            data={
                "candidateEventId": "candidate:a",
                "inhibitorRef": "policy:maintenance-window",
                "reasonCode": "MAINTENANCE_WINDOW_HELD",
                "evidenceRefs": ["lease:external"],
            },
        )
    )
    result = compile_coordination_projection(cut)
    row = result["candidateStanding"][0]
    assert row["state"] == "inhibited_shadow"
    assert row["inhibitionEventIds"] == ["inhibit:a"]
    assert "cannot" in row["truthBoundary"]


def test_support_is_recorded_but_not_scored_or_counted_as_quorum() -> None:
    cut = _cut()
    cut["events"].append(
        _event(
            "support:a",
            SUPPORT,
            data={
                "candidateEventId": "candidate:a",
                "supporterRef": "reviewer:ops",
                "evidenceRefs": ["evidence:review"],
            },
        )
    )
    result = compile_coordination_projection(cut)
    row = result["candidateStanding"][0]
    assert row["supportEventIds"] == ["support:a"]
    assert row["state"] == "eligible_shadow"
    assert result["commitmentProjection"]["state"] == "NOT_EVALUATED"


def test_real_vhd_dogfood_detects_competing_maintenance_and_pressure() -> None:
    cut = json.loads(DOGFOOD.read_text(encoding="utf-8"))
    result = compile_coordination_projection(cut)
    codes = [row["code"] for row in result["findings"]]
    assert codes.count("SUBJECT_MODE_CONFLICT") == 3
    assert result["commonOperatingPicture"]["activeCandidateCount"] == 3
    assert result["commonOperatingPicture"]["inhibitedCandidateCount"] == 3
    assert result["commonOperatingPicture"]["activeDamageSignalCount"] == 1
    assert result["commonOperatingPicture"]["activeModulatorySignalCount"] == 1
    assert result["commitmentProjection"]["state"] == "NOT_EVALUATED"
