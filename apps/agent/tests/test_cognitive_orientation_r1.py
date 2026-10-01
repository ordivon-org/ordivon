from __future__ import annotations

import json

import pytest

from ordivon_agent import (
    AgentOrientationViewError,
    project_agent_cognitive_environment,
    project_agent_orientation_view,
)


def work() -> dict:
    return {
        "workRef": "work:test:orientation",
        "revision": 7,
        "snapshotDigest": "sha256:" + "1" * 64,
        "snapshot": {
            "objective": "orient a fresh agent",
            "frontier": "one owner read is stale",
            "established": [
                "historical established fact " + ("x" * 400),
                "another established fact " + ("y" * 400),
            ],
            "unresolved": ["refresh runtime owner"],
            "constraints": ["no effect authority"],
            "nextActions": ["read runtime"],
            "referenceRefs": ["runtime:workspace:ws-o"],
        },
    }


def observation() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.living-owner-observation",
        "subjectRef": "runtime:workspace:ws-o",
        "ownerRef": "ordivon.runtime",
        "observedAt": "2026-10-01T21:00:00+08:00",
        "operation": "workspace.get",
        "standing": "available",
        "evidenceRefs": ["runtime:job:j1"],
        "attributes": {"large": "z" * 1000},
        "sourceRevision": "abc",
        "sourceDigest": "sha256:" + "2" * 64,
        "truthBoundary": "runtime only",
    }


def compact_bytes(value: object) -> int:
    return len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def test_orientation_is_progressive_disclosure_and_smaller() -> None:
    exact = project_agent_cognitive_environment(work(), owner_observations=[observation()])
    orient = project_agent_orientation_view(exact)

    assert orient["kind"] == "ordivon.agent-orientation-view"
    assert orient["work"]["objective"] == "orient a fresh agent"
    assert orient["work"]["establishedCount"] == 2
    assert "established" not in orient["work"]
    assert "attributes" not in orient["ownerCurrentness"][0]
    assert orient["progressiveDisclosure"]["fullWorkEstablishedHistoryIncluded"] is False
    assert orient["progressiveDisclosure"]["fullOwnerAttributesIncluded"] is False
    assert compact_bytes(orient) < compact_bytes(exact)


def test_orientation_retains_exact_expansion_refs_and_currentness() -> None:
    exact = project_agent_cognitive_environment(work(), owner_observations=[observation()])
    orient = project_agent_orientation_view(exact)

    assert orient["ownerCurrentness"] == [
        {
            "ownerRef": "ordivon.runtime",
            "subjectRef": "runtime:workspace:ws-o",
            "standing": "available",
            "observedAt": "2026-10-01T21:00:00+08:00",
            "evidenceRefs": ["runtime:job:j1"],
            "observationDigest": exact["ownerObservations"][0]["observationDigest"],
        }
    ]
    assert orient["expansionRefs"] == [
        "runtime:job:j1",
        "runtime:workspace:ws-o",
        "work:test:orientation",
    ]


def test_orientation_never_adds_authority() -> None:
    exact = project_agent_cognitive_environment(work())
    orient = project_agent_orientation_view(exact)
    assert all(value is False for value in orient["authority"].values())


def test_authoritative_source_projection_is_rejected() -> None:
    exact = project_agent_cognitive_environment(work())
    exact["authority"]["effectAuthority"] = True
    with pytest.raises(AgentOrientationViewError, match="carries authority"):
        project_agent_orientation_view(exact)
