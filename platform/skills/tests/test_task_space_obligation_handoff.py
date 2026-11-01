from __future__ import annotations

import importlib.util
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
