"""Native source-only consumer/obligation regression, not live network authority."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "platform/network/planning/lego-plan-r1.json"
TARGETS = {"N06", "N07", "N08"}
ACTUAL_WITNESSES = {
    "N06": (
        "platform/network/Taskfile.yml",
        "consumers/x-reality/config/egress.json",
    ),
    "N07": (
        "tools/repo/workspace-ready",
        "platform/network/consumers/developer-egress/profile.sh",
    ),
    "N08": (
        "platform/network/tests/test_readiness_shared_budget.py",
        "consumers/supply-chain/ready.sh",
    ),
}


def _nodes():
    return {n["id"]: n for n in json.loads(PLAN.read_text())["nodes"]}


def test_existing_network_legos_have_bounded_consumers_and_unproved_obligations():
    nodes = _nodes()
    assert TARGETS <= set(nodes)
    for identity in sorted(TARGETS):
        n = nodes[identity]
        assert n["inputs"] and n["outputs"] and n["behavioralContract"]
        assert len(n["formalObligations"]) == 3
        assert len(n["consumerEvidence"]) >= 2
        assert n["formalVerificationStanding"] == "DECLARED_NOT_MATHEMATICALLY_PROVED"
        assert n["consumerQualificationStanding"] == (
            "EXISTING_NATIVE_CONSUMER_REFERENCES_INSTALLED_UNKNOWN"
        )
        assert n["proofReuseAdmissible"] is False
        assert n["deletionAuthorized"] is False
        for field in ("consumerEvidence", "behavioralContract",
                      "formalObligations", "evidence"):
            assert n.get(field), (identity, field)
        for ref in n["consumerEvidence"]:
            source = (ROOT / ref if ref.startswith("tools/")
                      else ROOT / "platform/network" / ref)
            assert source.is_file(), ref
        file, literal = ACTUAL_WITNESSES[identity]
        assert literal in (ROOT / file).read_text(encoding="utf-8")


def test_network_consumer_and_formal_obligations_are_independent_problem_fields():
    for identity in sorted(TARGETS):
        n = _nodes()[identity]
        for removed in ("consumerEvidence", "formalObligations"):
            changed = dict(n)
            del changed[removed]
            assert not changed.get(removed), (identity, removed)
            for other in {"consumerEvidence", "behavioralContract",
                          "formalObligations", "evidence"} - {removed}:
                assert changed.get(other), (identity, other)
            assert changed["deletionAuthorized"] is False
