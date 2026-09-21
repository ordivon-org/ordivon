from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "system1_decision_benchmark.py"
SPEC = importlib.util.spec_from_file_location("system1_decision_benchmark", SCRIPT)
assert SPEC and SPEC.loader
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)

CORPUS = ROOT / "config" / "browser-decision-corpus-r1.json"


def test_browser_decision_corpus_is_digest_bound_controlled_fixture() -> None:
    corpus = B.load_corpus(CORPUS)
    assert corpus["corpusId"] == "browser-decision-r1-controlled"
    assert corpus["standing"] == "CONTROLLED_FIXTURE_ONLY"
    assert len(corpus["cases"]) == 42
    assert corpus["questions"]["target"]["type"] == "dynamic_choice"
    assert corpus["corpusDigest"].startswith("sha256:")


def test_browser_decision_corpus_has_operation_partition_and_context_cases() -> None:
    corpus = B.load_corpus(CORPUS)
    operations = {case["state"]["operation"] for case in corpus["cases"]}
    assert operations == {"CLICK", "FILL", "SELECT"}
    assert sum(case["state"]["caseClass"] == "context_required" for case in corpus["cases"]) >= 6
    for case in corpus["cases"]:
        operation = case["state"]["operation"]
        candidates = case["state"]["candidates"]
        assert len(candidates) >= 2
        assert all(candidate["operation"] == operation for candidate in candidates)
        ids = {candidate["candidateId"] for candidate in candidates}
        assert len(ids) == len(candidates)
        assert case["expected"]["target"] in ids
        assert all("backendDOMNodeId" not in candidate for candidate in candidates)
        assert all("axNodeId" not in candidate for candidate in candidates)


def test_browser_decision_corpus_excludes_sensitive_candidate_names() -> None:
    corpus = B.load_corpus(CORPUS)
    names = {
        candidate.get("name")
        for case in corpus["cases"]
        for candidate in case["state"]["candidates"]
    }
    assert "Password secret" not in names
    assert "Upload CV" not in names
    assert "Inert action" not in names
    assert "Disabled submit" not in names
