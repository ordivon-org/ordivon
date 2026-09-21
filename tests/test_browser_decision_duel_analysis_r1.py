from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research" / "experiments" / "browser_decision_duel_analysis_r1.py"
SPEC = importlib.util.spec_from_file_location("browser_decision_duel_analysis_r1", SCRIPT)
assert SPEC and SPEC.loader
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def test_duel_analysis_reproduces_frozen_provider_result() -> None:
    result = A.analyze(A.DEFAULT_CORPUS, A.DEFAULT_OBSERVATIONS)
    assert result["caseCount"] == 42
    assert result["providers"]["crossencoder"]["score"]["coverage"]["executedCases"] == 42
    assert result["providers"]["crossencoder"]["score"]["choice"]["accuracy"] == 39 / 42
    assert result["providers"]["laya"]["score"]["choice"]["accuracy"] == 5 / 42
    assert result["providers"]["jev"]["score"]["coverage"]["standings"]["BLOCKED"] == 42
    assert result["decision"]["standing"] == "NO_TRAINING_JUSTIFIED_R1"


def test_diagnostic_reduction_changes_only_two_crossencoder_errors() -> None:
    result = A.analyze(A.DEFAULT_CORPUS, A.DEFAULT_OBSERVATIONS)
    reduction = result["diagnosticSemanticClickReduction"]
    assert reduction["correct"] == 41
    assert reduction["changedCaseIds"] == ["g20-frame-apply", "t03-find-stays"]
    assert reduction["missCaseIds"] == ["g17-nested-button"]
    assert reduction["candidatePairsBefore"] == 638
    assert reduction["candidatePairsAfter"] == 416


def test_name_only_baseline_does_not_explain_context_required_performance() -> None:
    result = A.analyze(A.DEFAULT_CORPUS, A.DEFAULT_OBSERVATIONS)
    lexical = result["lexicalBaselines"]["nameOnly"]
    assert lexical["correct"] == 36
    assert lexical["byCaseClass"]["context_required"]["correct"] == 4
    cross = result["providers"]["crossencoder"]["byCaseClass"]["context_required"]
    assert cross["n"] == 8
    assert cross["accuracy"] == 1.0
