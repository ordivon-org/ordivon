#!/usr/bin/env python3
"""Analyze Browser Decision Provider Duel R1 from frozen corpus and observations."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import system1_decision_benchmark as benchmark  # noqa: E402

DEFAULT_CORPUS = ROOT / "config/browser-decision-corpus-r1.json"
DEFAULT_OBSERVATIONS = {
    "crossencoder": ROOT
    / "evidence/system1-decision/browser-decision-crossencoder-r1-20260921.json",
    "laya": ROOT / "evidence/system1-decision/browser-decision-laya-r1-20260921.json",
    "jev": ROOT / "evidence/system1-decision/browser-decision-jev-blocked-r1-20260921.json",
}
EDITABLE_CLICK_ROLES = frozenset({"textbox", "searchbox", "spinbutton", "combobox", "generic"})
LEXICAL_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "for",
        "of",
        "in",
        "on",
        "or",
        "and",
        "that",
        "this",
        "with",
        "without",
        "it",
        "its",
        "new",
        "control",
        "field",
        "option",
        "inside",
        "whose",
        "is",
        "per",
        "from",
        "using",
        "open",
    }
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected object: {path}")
    return value


def _rank(case: dict[str, Any], row: dict[str, Any]) -> float:
    probs = row["answers"]["target"]["probabilities"]
    truth = case["expected"]["target"]
    truth_probability = probs[truth]
    better = sum(value > truth_probability for value in probs.values())
    tied_other = sum(
        candidate_id != truth and value == truth_probability
        for candidate_id, value in probs.items()
    )
    return 1.0 + better + 0.5 * tied_other


def _candidate(case: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    rows = [
        candidate
        for candidate in case["state"]["candidates"]
        if candidate["candidateId"] == candidate_id
    ]
    if len(rows) != 1:
        raise ValueError(f"candidate must resolve once: {case['caseId']}:{candidate_id}")
    return rows[0]


def _strata(corpus: dict[str, Any], observation: dict[str, Any], field: str) -> dict[str, Any]:
    case_by_id = {case["caseId"]: case for case in corpus["cases"]}
    groups: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for row in observation["cases"]:
        if row["standing"] != "EXECUTED":
            continue
        case = case_by_id[row["caseId"]]
        truth = case["expected"]["target"]
        pred = row["answers"]["target"]["choice"]
        groups[str(case["state"][field])].append(
            (int(pred == truth), _rank(case, row), float(row["latencyMs"]))
        )
    out: dict[str, Any] = {}
    for key, values in sorted(groups.items()):
        out[key] = {
            "n": len(values),
            "accuracy": sum(value[0] for value in values) / len(values),
            "meanReciprocalRank": sum(1.0 / value[1] for value in values) / len(values),
            "medianLatencyMs": statistics.median(value[2] for value in values),
        }
    return out


def _misses(corpus: dict[str, Any], observation: dict[str, Any]) -> list[dict[str, Any]]:
    case_by_id = {case["caseId"]: case for case in corpus["cases"]}
    rows = []
    for row in observation["cases"]:
        if row["standing"] != "EXECUTED":
            continue
        case = case_by_id[row["caseId"]]
        truth = case["expected"]["target"]
        pred = row["answers"]["target"]["choice"]
        if pred == truth:
            continue
        truth_candidate = _candidate(case, truth)
        pred_candidate = _candidate(case, pred)
        probs = row["answers"]["target"]["probabilities"]
        rows.append(
            {
                "caseId": case["caseId"],
                "operation": case["state"]["operation"],
                "caseClass": case["state"]["caseClass"],
                "goal": case["state"]["goal"],
                "truth": {
                    "candidateId": truth,
                    "role": truth_candidate.get("role"),
                    "name": truth_candidate.get("name"),
                    "optionName": truth_candidate.get("optionName"),
                    "probability": probs[truth],
                },
                "predicted": {
                    "candidateId": pred,
                    "role": pred_candidate.get("role"),
                    "name": pred_candidate.get("name"),
                    "optionName": pred_candidate.get("optionName"),
                    "probability": probs[pred],
                },
                "truthRank": _rank(case, row),
            }
        )
    return rows


def _tokens(text: object) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", str(text).lower())
        if token not in LEXICAL_STOPWORDS
    ]


def _lexical_text(candidate: dict[str, Any], mode: str) -> str:
    fields = ["name", "optionName"]
    if mode == "all":
        fields.extend(["description", "context", "value", "href"])
    return " ".join(str(candidate.get(field) or "") for field in fields)


def _lexical_score(goal: str, candidate: dict[str, Any], mode: str) -> float:
    goal_tokens = set(_tokens(goal))
    evidence_tokens = set(_tokens(_lexical_text(candidate, mode)))
    intersection = len(goal_tokens & evidence_tokens)
    overlap = (
        2 * intersection / (len(goal_tokens) + len(evidence_tokens))
        if goal_tokens or evidence_tokens
        else 0.0
    )
    phrase = 1.0 if any(
        isinstance(value, str)
        and value.strip()
        and value.lower() in goal.lower()
        for value in (candidate.get("name"), candidate.get("optionName"))
    ) else 0.0
    return overlap + phrase


def _lexical_baseline(corpus: dict[str, Any], mode: str) -> dict[str, Any]:
    correct = 0
    class_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    misses: list[str] = []
    for case in corpus["cases"]:
        state = case["state"]
        ranked = sorted(
            (
                (_lexical_score(state["goal"], candidate, mode), candidate["candidateId"])
                for candidate in state["candidates"]
            ),
            reverse=True,
        )
        pred = ranked[0][1]
        truth = case["expected"]["target"]
        ok = pred == truth
        correct += int(ok)
        bucket = class_counts[state["caseClass"]]
        bucket[0] += int(ok)
        bucket[1] += 1
        if not ok:
            misses.append(case["caseId"])
    return {
        "mode": mode,
        "correct": correct,
        "total": len(corpus["cases"]),
        "accuracy": correct / len(corpus["cases"]),
        "byCaseClass": {
            key: {"correct": value[0], "n": value[1], "accuracy": value[0] / value[1]}
            for key, value in sorted(class_counts.items())
        },
        "missCaseIds": misses,
    }


def _semantic_click_reduction(
    corpus: dict[str, Any], crossencoder: dict[str, Any]
) -> dict[str, Any]:
    rows_by_id = {row["caseId"]: row for row in crossencoder["cases"]}
    correct = 0
    changed: list[str] = []
    misses: list[str] = []
    pairs_before = 0
    pairs_after = 0
    deterministic = 0
    for case in corpus["cases"]:
        state = case["state"]
        candidates = list(state["candidates"])
        probs = rows_by_id[case["caseId"]]["answers"]["target"]["probabilities"]
        pairs_before += len(candidates)
        survivors = candidates
        if state["operation"] == "CLICK":
            focus_like = "focus" in set(_tokens(state["goal"]))
            subset = [
                candidate
                for candidate in candidates
                if (candidate.get("role") in EDITABLE_CLICK_ROLES) == focus_like
            ]
            if subset:
                survivors = subset
        pairs_after += len(survivors)
        if len(survivors) == 1:
            deterministic += 1
        pred = max(survivors, key=lambda candidate: probs[candidate["candidateId"]])["candidateId"]
        base = max(candidates, key=lambda candidate: probs[candidate["candidateId"]])["candidateId"]
        if pred != base:
            changed.append(case["caseId"])
        truth = case["expected"]["target"]
        correct += int(pred == truth)
        if pred != truth:
            misses.append(case["caseId"])
    return {
        "standing": "DIAGNOSTIC_ONLY",
        "rule": (
            "For CLICK only: if goal explicitly contains focus, compete editable roles; "
            "otherwise compete non-editable roles when such candidates exist."
        ),
        "correct": correct,
        "total": len(corpus["cases"]),
        "accuracy": correct / len(corpus["cases"]),
        "changedCaseIds": changed,
        "missCaseIds": misses,
        "candidatePairsBefore": pairs_before,
        "candidatePairsAfter": pairs_after,
        "pairReductionFraction": 1.0 - pairs_after / pairs_before,
        "deterministicAfterReduction": deterministic,
        "nonClaims": ["production_intent_parser", "general_open_web_validity"],
    }


def analyze(
    corpus_path: Path,
    observation_paths: dict[str, Path],
) -> dict[str, Any]:
    corpus = benchmark.load_corpus(corpus_path)
    observations = {key: _read(path) for key, path in observation_paths.items()}
    for observation in observations.values():
        benchmark.validate_observation(observation, corpus)

    scores = {
        key: benchmark.score_observation(observation, corpus)
        for key, observation in observations.items()
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-decision-provider-duel-r1",
        "corpusId": corpus["corpusId"],
        "corpusDigest": corpus["corpusDigest"],
        "caseCount": len(corpus["cases"]),
        "providers": {
            key: {
                "score": scores[key],
                "byOperation": _strata(corpus, observation, "operation"),
                "byCaseClass": _strata(corpus, observation, "caseClass"),
                "misses": _misses(corpus, observation),
            }
            for key, observation in observations.items()
        },
        "lexicalBaselines": {
            "nameOnly": _lexical_baseline(corpus, "name"),
            "allEvidence": _lexical_baseline(corpus, "all"),
        },
        "diagnosticSemanticClickReduction": _semantic_click_reduction(
            corpus, observations["crossencoder"]
        ),
        "g17AncestryAudit": {
            "standing": "BENCHMARK_LAYER_CONTAMINATION",
            "caseId": "g17-nested-button",
            "observedWith": "Chromium 153.0.8010.12 AX tree",
            "facts": [
                "The actionable Nested cell button is a button child of a gridcell whose accessible name is Nested cell button.",
                "That parent gridcell is intentionally suppressed from the candidate set by actionable-descendant projection.",
                "The CrossEncoder-selected Scholarship cell is a sibling gridcell in the same row, not the nested button's parent.",
                "The case wording therefore reintroduces an observation-layer parent/child ambiguity that the candidate projector already removed.",
            ],
            "disposition": "retain as R1 negative evidence; do not use this case as training justification",
        },
        "decision": {
            "standing": "NO_TRAINING_JUSTIFIED_R1",
            "reasons": [
                "The controlled corpus has only 42 cases and is not an open-web population.",
                "Base CrossEncoder already executes all cases and reaches 39/42 accuracy, 8/8 on context-required cases.",
                "A browser-semantic diagnostic reduction changes only two CrossEncoder errors and reaches 41/42 without model training.",
                "The remaining error is benchmark-layer contamination, not clean evidence of a model-capacity gap.",
                "Base Laya independent noul composition is substantially worse and slower on this task.",
                "Jev remains blocked by the existing TYPESAFE_API_KEY readiness gate and therefore provides no accuracy evidence in R1.",
            ],
            "nextGate": "larger real-page / real-application candidate census before any Browser-specific training",
        },
        "nonClaims": [
            "provider_superiority_on_open_web",
            "production_calibration",
            "production_route_migration",
            "browser_specific_training_not_ever_needed",
            "cross_browser_equivalence",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--crossencoder", type=Path, default=DEFAULT_OBSERVATIONS["crossencoder"])
    parser.add_argument("--laya", type=Path, default=DEFAULT_OBSERVATIONS["laya"])
    parser.add_argument("--jev", type=Path, default=DEFAULT_OBSERVATIONS["jev"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(
        args.corpus,
        {
            "crossencoder": args.crossencoder,
            "laya": args.laya,
            "jev": args.jev,
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "standing": result["decision"]["standing"],
                "corpusDigest": result["corpusDigest"],
                "crossencoderAccuracy": result["providers"]["crossencoder"]["score"]["choice"]["accuracy"],
                "layaAccuracy": result["providers"]["laya"]["score"]["choice"]["accuracy"],
                "jevCoverage": result["providers"]["jev"]["score"]["coverage"]["fraction"],
                "diagnosticReducedAccuracy": result["diagnosticSemanticClickReduction"]["accuracy"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
