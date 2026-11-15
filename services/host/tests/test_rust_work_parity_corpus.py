"""Frozen Python Host Work wire/digest oracle for Rust migration (no database I/O).

The JSON corpus is shared with the Rust implementation.  These tests prevent an
apparently successful port from silently changing defaults, aliases, strict
integer domains or RFC 8785 bytes.  This does NOT establish PostgreSQL CAS,
receipt replay, installed MCP, or production equivalence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from ordivon_host_v2.canonical_json import canonical_bytes, canonical_digest
from ordivon_host_v2.mcp_tool_registration import _request_id
from ordivon_host_v2.mcp_work_tools import AdvancableWorkRevision, PositiveWorkRevision
from ordivon_host_v2.work_inputs import WorkSnapshotInput

_CORPUS = json.loads(Path(__file__).with_name("rust_work_parity_r1.json").read_text("utf-8"))
_REVISION_ADAPTERS = {
    "work.get": TypeAdapter(PositiveWorkRevision),
    "work.snapshot.commit": TypeAdapter(AdvancableWorkRevision),
}


def test_fixture_identity_and_coverage() -> None:
    assert _CORPUS["schemaVersion"] == 1
    assert _CORPUS["kind"] == "ordivon.host-rust-work-parity"
    assert _CORPUS["oracle"]["scope"] == "pure-python-host-wire-and-digest"
    assert len(_CORPUS["validSnapshots"]) >= 5
    assert len(_CORPUS["invalidSnapshots"]) >= 5
    assert len(_CORPUS["revisions"]) >= 10
    assert _CORPUS["postgresqlEffectsProven"] is False


@pytest.mark.parametrize("case", _CORPUS["validSnapshots"], ids=lambda case: case["id"])
def test_canonical_snapshot_and_store_request_match_frozen_python_oracle(
    case: dict[str, object],
) -> None:
    snapshot = WorkSnapshotInput.model_validate(case["input"])
    payload = snapshot.canonical_payload()
    assert payload == case["canonicalPayload"]
    assert canonical_bytes(payload).hex() == case["canonicalUtf8Hex"]
    assert canonical_digest(payload) == case["snapshotDigest"]

    request = {
        "operation": "work.snapshot.commit",
        "workRef": case["workRef"],
        "expectedRevision": case["expectedRevision"],
        "snapshot": payload,
        "actorRef": case["actorRef"],
        "state": case["state"],
    }
    assert canonical_digest(request) == case["storeRequestDigest"]

    mcp_request = {
        "workRef": case["workRef"],
        "expectedRevision": case["expectedRevision"],
        "snapshot": payload,
        "actorRef": case["actorRef"],
        "continuityDisposition": {
            "open": "continue",
            "completed": "complete",
            "abandoned": "abandon",
        }[case["state"]],
    }
    assert canonical_digest(mcp_request) == case["mcpRequestDigest"]
    assert _request_id("work-snapshot-commit", mcp_request) == case["mcpClientRequestId"]

    create = {
        "operation": "work.create",
        "workRef": case["workRef"],
        "kind": case["workKind"],
        "actorRef": case["actorRef"],
        "initialSnapshot": payload,
    }
    assert canonical_digest(create) == case["storeCreateDigest"]


@pytest.mark.parametrize("case", _CORPUS["invalidSnapshots"], ids=lambda case: case["id"])
def test_invalid_work_snapshot_remains_invalid(case: dict[str, object]) -> None:
    with pytest.raises(ValidationError) as exc_info:
        WorkSnapshotInput.model_validate(case["input"])
    assert case["errorType"] in {error["type"] for error in exc_info.value.errors()}


@pytest.mark.parametrize("case", _CORPUS["revisions"], ids=lambda case: case["id"])
def test_work_revision_mcp_ingress_uses_strict_postgresql_domains(
    case: dict[str, object],
) -> None:
    adapter = _REVISION_ADAPTERS[case["operation"]]
    if case["accepted"]:
        value = adapter.validate_python(case["value"])
        assert type(value) is int
        assert value == case["value"]
    else:
        with pytest.raises(ValidationError):
            adapter.validate_python(case["value"])


def test_no_unintended_unicode_normalization() -> None:
    cases = {case["id"]: case for case in _CORPUS["validSnapshots"]}
    assert (
        cases["unicode_combining"]["snapshotDigest"]
        != cases["unicode_precomposed"]["snapshotDigest"]
    )


def test_historical_lifecycle_standing_is_not_reconstructed_from_snapshot() -> None:
    # Contract marker: the historic Work payload alone does not encode its state.
    # Real PG readback and its old-revision edge cases are tested independently.
    assert _CORPUS["historicalRevisionState"] == "historical_state_unknown"


def test_python_only_edge_whitespace_and_internal_control_are_distinguished() -> None:
    ids = {case["id"] for case in _CORPUS["invalidSnapshots"]}
    assert {f"python_only_strip_U+{n:04X}" for n in range(0x1C, 0x20)} <= ids
    valid = {case["id"]: case for case in _CORPUS["validSnapshots"]}
    assert valid["embedded_python_only_whitespace"]["input"]["established"] == ["a\x1cb"]
