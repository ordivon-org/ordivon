from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".agents/skills/task-space-reentry/scripts/check_obligation_handoff.py"
SPEC = importlib.util.spec_from_file_location("obligation_handoff", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def packet():
    return {
        "source": {"workRef": "work:old", "revision": 2, "state": "completed",
                   "unresolved": ["consumer-readset", "skill-client"]},
        "successors": [
            {"workRef": "work:new", "revision": 4, "state": "open",
             "unresolved": ["consumer-readset-real", "skill-client-e2e"]}
        ],
        "links": [
            {"sourceObligation": "consumer-readset", "sourceRevision": 2,
             "successorRef": "work:new", "successorRevision": 4,
             "successorObligation": "consumer-readset-real"},
            {"sourceObligation": "skill-client", "sourceRevision": 2,
             "successorRef": "work:new", "successorRevision": 4,
             "successorObligation": "skill-client-e2e"},
        ],
    }


def test_exact_navigation_all_items_still_unknown_for_semantic_completion():
    result = helper.assess(packet())
    assert result["navigationCovered"] is True
    assert result["obligationsCarried"] == ["consumer-readset", "skill-client"]
    assert result["semanticEquivalence"] == "UNKNOWN"
    assert result["technicalCompletion"] == "UNKNOWN"
    assert result["ownerCurrentness"] == "UNKNOWN"
    assert result["effectAuthority"] == "NONE"


def test_missing_obligation_negative():
    data = packet()
    data["links"].pop()
    result = helper.assess(data)
    assert result["navigationCovered"] is False
    assert result["missing"] == ["skill-client"]


@pytest.mark.parametrize("mutation", ["receiver_revision", "source_revision", "absent_receiver_obligation"])
def test_stale_or_wrong_link_is_rejected(mutation):
    data = packet()
    link = data["links"][0]
    if mutation == "receiver_revision":
        link["successorRevision"] += 1
    if mutation == "source_revision":
        link["sourceRevision"] -= 1
    if mutation == "absent_receiver_obligation":
        link["successorObligation"] = "made-up"
    result = helper.assess(data)
    assert result["navigationCovered"] is False
    assert result["invalidLinks"] == ["consumer-readset"]


@pytest.mark.parametrize("mutation", ["terminal_receiver", "self", "duplicate_link", "bool_version", "unknown_original"])
def test_bad_boundary_fails_closed(mutation):
    data = packet()
    if mutation == "terminal_receiver":
        data["successors"][0]["state"] = "completed"
    if mutation == "self":
        data["successors"][0]["workRef"] = "work:old"
    if mutation == "duplicate_link":
        data["links"].append(dict(data["links"][0]))
    if mutation == "bool_version":
        data["source"]["revision"] = True
    if mutation == "unknown_original":
        data["links"][0]["sourceObligation"] = "never-existed"
    with pytest.raises(ValueError):
        helper.assess(data)


def test_skill_reference_exposes_optional_transfer_not_automatic_execution():
    from ordivon_skills.catalog import SkillCatalog
    from ordivon_skills.model import SkillContext, SkillSource, TrustState

    catalog = SkillCatalog.scan([
        SkillSource("project-ordivon-next", ROOT / ".agents/skills", "project",
                    900, TrustState.TRUSTED)
    ])
    ctx = SkillContext(workspace_path=ROOT)
    resolved = catalog.resolve("task-space-reentry", context=ctx)
    body = catalog.read_text(
        resolved.resolved.skill_id, relative_path="references/task-packet.md",
        context=ctx, expected_snapshot_revision=resolved.snapshot_revision,
        projection="raw",
    ).content
    for expected in ("scripts/check_obligation_handoff.py", "NAVIGATION_COVERED",
                     "semantic equivalence", "UNKNOWN", "task registry"):
        assert expected.lower() in body.lower()
    row = next(x for x in catalog.inventory if x.skill_id ==
               "project-ordivon-next/task-space-reentry")
    assert row.scan_state == "PASS" and row.implicit_invocation is True


def test_duplicate_host_obligations_have_indexed_navigation_without_false_completion():
    # Host WorkSnapshotInput.unresolved is list[str], not a uniqueness-constrained set.
    data = packet()
    data["source"]["unresolved"] = ["same", "same"]
    data["links"] = [
        {"sourceObligation": "same", "sourceRevision": 2,
         "successorRef": "work:new", "successorRevision": 4,
         "successorObligation": "consumer-readset-real", "sourceIndex": 0},
        {"sourceObligation": "same", "sourceRevision": 2,
         "successorRef": "work:new", "successorRevision": 4,
         "successorObligation": "skill-client-e2e", "sourceIndex": 1},
    ]
    result = helper.assess(data)
    assert result["navigationCovered"] is True
    assert result["coveredIndices"] == [0, 1]
    assert result["technicalCompletion"] == "UNKNOWN"


def test_duplicate_source_without_index_rejected_as_ambiguous():
    data = packet()
    data["source"]["unresolved"] = ["same", "same"]
    data["links"] = [{"sourceObligation": "same", "sourceRevision": 2,
                      "successorRef": "work:new", "successorRevision": 4,
                      "successorObligation": "consumer-readset-real"}]
    with pytest.raises(ValueError, match="sourceIndex"):
        helper.assess(data)


def test_duplicate_receiver_needs_index_and_wrong_index_fails_closed():
    data = packet()
    data["successors"][0]["unresolved"] = ["repeat", "repeat"]
    for i, link in enumerate(data["links"]):
        link["successorObligation"] = "repeat"
    with pytest.raises(ValueError, match="successorIndex"):
        helper.assess(data)
    data["links"][0]["successorIndex"] = 0
    data["links"][1]["successorIndex"] = 1
    assert helper.assess(data)["navigationCovered"] is True
    data["links"][1]["successorIndex"] = 2
    assert helper.assess(data)["navigationCovered"] is False

def _run_cli(raw):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)], input=raw, capture_output=True,
        text=True, check=False, timeout=10,
    )
    return completed, json.loads(completed.stdout)


@pytest.mark.parametrize("mutation", ["duplicate_root", "duplicate_revision", "duplicate_link", "nonfinite_shadow"])
def test_wire_member_ambiguity_is_rejected_before_typed_coverage(mutation):
    data = packet()
    raw = json.dumps(data)
    if mutation == "duplicate_root":
        raw = '{"source": null, ' + raw[1:]
    elif mutation == "duplicate_revision":
        raw = raw.replace('"revision": 2', '"revision": 1, "revision": 2', 1)
    elif mutation == "duplicate_link":
        raw = raw.replace('"successorRevision": 4', '"successorRevision": 4, "successorRevision": 4', 1)
    else:
        raw = raw.replace('"revision": 2', '"revision": NaN, "revision": 2', 1)
    completed, result = _run_cli(raw)
    assert completed.returncode == 2
    assert result["navigationCovered"] is False
    assert result["kind"] == "ordivon.task-obligation-handoff-error-v1"


@pytest.mark.parametrize("revision", [2**53, 2**63 - 1, 2**63])
@pytest.mark.parametrize("role", ["source", "successor"])
def test_wire_revision_outside_native_host_range_rejected(revision, role):
    data = packet()
    row = data["source"] if role == "source" else data["successors"][0]
    row["revision"] = revision
    field = "sourceRevision" if role == "source" else "successorRevision"
    for link in data["links"]:
        link[field] = revision
    completed, result = _run_cli(json.dumps(data))
    assert completed.returncode == 2
    assert result["navigationCovered"] is False


@pytest.mark.parametrize("role", ["source", "successor"])
def test_wire_exact_native_upper_revision_retains_navigation_only(role):
    data = packet()
    row = data["source"] if role == "source" else data["successors"][0]
    row["revision"] = 2**53 - 1
    field = "sourceRevision" if role == "source" else "successorRevision"
    for link in data["links"]:
        link[field] = row["revision"]
    completed, result = _run_cli(json.dumps(data))
    assert completed.returncode == 0
    assert result["navigationCovered"] is True
    assert result["technicalCompletion"] == "UNKNOWN"
    assert result["effectAuthority"] == "NONE"

@pytest.mark.parametrize("mutation", [
    "utf16", "utf8_bom", "surrogate", "nul", "short_ref", "long_ref",
    "padded_ref", "control_ref", "padded_obligation", "too_many_obligations",
])
def test_handoff_requires_host_representable_utf8_snapshot(mutation):
    data = packet()
    source = data["source"]
    if mutation == "surrogate":
        source["workRef"] = "work:\ud800"
    elif mutation == "nul":
        source["workRef"] = "work:a\x00b"
    elif mutation == "short_ref":
        source["workRef"] = "x"
    elif mutation == "long_ref":
        source["workRef"] = "w" * 1025
    elif mutation == "padded_ref":
        source["workRef"] = " work:old"
    elif mutation == "control_ref":
        source["workRef"] = "work:a\nb"
    elif mutation == "padded_obligation":
        source["unresolved"][0] = " consumer-readset "
        data["links"][0]["sourceObligation"] = source["unresolved"][0]
    elif mutation == "too_many_obligations":
        source["unresolved"] = [f"obligation-{i}" for i in range(129)]
        data["links"] = [
            dict(data["links"][0], sourceObligation=value)
            for value in source["unresolved"]
        ]
    raw = json.dumps(data).encode("utf-8")
    if mutation == "utf16":
        raw = raw.decode("utf-8").encode("utf-16")
    elif mutation == "utf8_bom":
        raw = b"\xef\xbb\xbf" + raw
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)], input=raw, capture_output=True,
        check=False, timeout=10,
    )
    assert completed.returncode == 2, completed.stderr
    assert json.loads(completed.stdout)["navigationCovered"] is False


def test_handoff_unicode_scalar_roundtrip_keeps_exact_obligation_text():
    data = packet()
    data["source"]["unresolved"][0] = "验证 👋 e\u0301"
    data["links"][0]["sourceObligation"] = data["source"]["unresolved"][0]
    completed, result = _run_cli(json.dumps(data, ensure_ascii=True))
    assert completed.returncode == 0
    assert result["obligationsCarried"][0] == "验证 👋 e\u0301"
    assert result["effectAuthority"] == "NONE"

@pytest.mark.parametrize("field", ["workRef", "unresolved"])
def test_successor_snapshot_has_same_native_text_boundary(field):
    data = packet()
    receiver = data["successors"][0]
    if field == "workRef":
        receiver["workRef"] = "work:\ud800"
        for link in data["links"]:
            link["successorRef"] = receiver["workRef"]
    else:
        receiver["unresolved"][0] = "x\x00y"
        data["links"][0]["successorObligation"] = receiver["unresolved"][0]
    completed, result = _run_cli(json.dumps(data))
    assert completed.returncode == 2
    assert result["navigationCovered"] is False


def test_handoff_ascii_stdout_does_not_change_unicode_scalar_text():
    data = packet()
    value = "验证 👋 e\u0301"
    data["source"]["unresolved"][0] = value
    data["links"][0]["sourceObligation"] = value
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)], input=json.dumps(data).encode("utf-8"),
        capture_output=True, check=False, timeout=10,
        env={**os.environ, "PYTHONIOENCODING": "ascii:strict"},
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["obligationsCarried"][0] == value


def test_native_snapshot_limits_are_inclusive():
    data = packet()
    data["source"]["workRef"] = "w" * 1024
    data["source"]["unresolved"] = [f"obligation-{i}" for i in range(128)]
    data["links"] = [
        dict(data["links"][0], sourceObligation=value)
        for value in data["source"]["unresolved"]
    ]
    completed, result = _run_cli(json.dumps(data))
    assert completed.returncode == 0
    assert result["coveredIndices"] == list(range(128))
    assert result["technicalCompletion"] == "UNKNOWN"


def test_handoff_revision_limit_matches_native_host_wire_contract():
    import runpy

    bounds = runpy.run_path(str(
        ROOT / "services/host/src/ordivon_host_v2/postgres_bounds.py"
    ))
    assert helper._MAX_HOST_REVISION == bounds["HOST_WIRE_INT_MAX"]
