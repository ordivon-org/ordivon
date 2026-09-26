from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]
SCRIPTS = ROOT / "meta" / "next" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from social_work_fabric_projection_r1 import (  # noqa: E402
    ProjectionError,
    compile_attention,
    compile_authority,
    compile_coordination,
    compile_current,
)


def bundle() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.social-work-fabric-owner-bundle-r1",
        "works": [
            {
                "schemaVersion": 1,
                "kind": "ordivon.host-work",
                "workRef": "work:paper2",
                "workKind": "research",
                "state": "open",
                "revision": 7,
                "snapshotDigest": "sha256:abc",
                "snapshot": {"frontier": "matching", "unresolved": ["agreement"]},
            }
        ],
        "workRelations": [],
        "spaces": [
            {
                "schemaVersion": 1,
                "kind": "ordivon.host-space",
                "spaceRef": "space:paper2-pilot",
                "subjectRefs": ["work:paper2", "resource:crossref"],
                "participants": [
                    {"actorRef": "actor:agent:a1", "standing": "joined"},
                    {"actorRef": "actor:agent:a2", "standing": "joined"},
                ],
                "topics": [
                    {"topicRef": "topic:matching", "state": "open"},
                    {"topicRef": "topic:adjudication", "state": "open"},
                ],
            }
        ],
        "coordinationIntents": [
            {
                "schemaVersion": 1,
                "kind": "ordivon.host-coordination-intent",
                "intentRef": "intent:a1",
                "actorRef": "actor:agent:a1",
                "subjectRef": "resource:crossref",
                "operation": "review",
                "workRef": "work:paper2",
                "spaceRef": "space:paper2-pilot",
                "standing": "active",
                "expiresAtMs": None,
            },
            {
                "schemaVersion": 1,
                "kind": "ordivon.host-coordination-intent",
                "intentRef": "intent:a2",
                "actorRef": "actor:agent:a2",
                "subjectRef": "resource:crossref",
                "operation": "inspect",
                "workRef": "work:paper2",
                "spaceRef": "space:paper2-pilot",
                "standing": "active",
                "expiresAtMs": None,
            },
        ],
        "attention": {
            "schemaVersion": 1,
            "kind": "ordivon.host-attention-delta-r1",
            "actorRef": "actor:agent:a1",
            "afterSequence": 10,
            "snapshotHighSequence": 20,
            "events": [
                {
                    "changeSequence": 17,
                    "eventKind": "message",
                    "sourceRef": "message:17",
                    "contextRef": "topic:matching",
                }
            ],
            "hasMore": False,
            "nextAfterSequence": 17,
            "rankingApplied": False,
        },
        "authorityBindings": [
            {
                "subjectRef": "resource:crossref",
                "relation": "NATURAL_CAPABILITY_OWNER",
                "principalRef": "owner:paper2-provider",
                "sourceRef": "authority:paper2",
            }
        ],
    }


def test_current_preserves_work_and_space_without_domain_promotion() -> None:
    result = compile_current(bundle())
    assert result["works"][0]["frontier"] == "matching"
    assert result["spaces"][0]["participantCount"] == 2
    assert "Runtime" in result["nonClaims"][0]


def test_attention_is_exact_unranked_owner_delta() -> None:
    result = compile_attention(bundle())
    assert result["events"][0]["changeSequence"] == 17
    assert result["rankingApplied"] is False


def test_coordination_exposes_simultaneous_intents_without_conflict_or_winner() -> None:
    result = compile_coordination(bundle())
    row = result["activeIntentsBySubject"][0]
    assert row["subjectRef"] == "resource:crossref"
    assert row["simultaneousIntentCount"] == 2
    for row_value in result["activeIntentsBySubject"]:
        assert "winner" not in row_value
        assert "conflict" not in row_value
        assert "lock" not in row_value
    assert "lock" in result["nonClaims"][0]  # only a non-claim


def test_authority_only_uses_explicit_bindings() -> None:
    result = compile_authority(bundle())
    assert result["bindingCount"] == 1
    assert result["bindings"][0]["principalRef"] == "owner:paper2-provider"
    assert result["inferredFromParticipants"] is False
    assert result["inferredFromIntentActors"] is False


def test_participants_do_not_create_authority_when_bindings_absent() -> None:
    value = bundle()
    value["authorityBindings"] = []
    result = compile_authority(value)
    assert result["bindings"] == []
    assert result["bindingCount"] == 0


def test_projection_rejects_control_fields_anywhere() -> None:
    value = bundle()
    value["works"][0]["priority"] = 99
    with pytest.raises(ProjectionError, match="forbidden control fields"):
        compile_current(value)


def test_projection_rejects_ranked_attention_source() -> None:
    value = bundle()
    value["attention"]["rankingApplied"] = True
    with pytest.raises(ProjectionError, match="unranked"):
        compile_attention(value)
