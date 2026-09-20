#!/usr/bin/env python3
"""Provider-neutral scoring contract for typed System-1 decision observations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path
from statistics import mean, median
from typing import Any

SOURCE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = SOURCE_ROOT / "config/system1-decision-corpus-r1.json"


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def load_corpus(path: Path = DEFAULT_CORPUS) -> dict[str, Any]:
    value = _read_json(path)
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.system1-decision-corpus":
        raise ValueError("decision corpus identity mismatch")
    if value.get("standing") != "SYNTHETIC_SMOKE_ONLY":
        raise ValueError("R1 only admits explicitly synthetic smoke corpus")
    questions = value.get("questions")
    cases = value.get("cases")
    if not isinstance(questions, dict) or not questions:
        raise ValueError("corpus requires questions")
    if not isinstance(cases, list) or not cases:
        raise ValueError("corpus requires cases")
    for qid, q in questions.items():
        if not isinstance(qid, str) or not qid or not isinstance(q, dict):
            raise ValueError("invalid question")
        qtype = q.get("type")
        if qtype not in {"choice", "noul"}:
            raise ValueError(f"unsupported R1 question type: {qtype}")
        if qtype == "choice":
            criteria = q.get("criteria")
            if not isinstance(criteria, dict) or len(criteria) < 2:
                raise ValueError("choice question requires at least two criteria")
    seen: set[str] = set()
    normalized = []
    for row in cases:
        if not isinstance(row, dict):
            raise TypeError("case must be an object")
        cid = row.get("caseId")
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ValueError("caseId must be unique non-empty text")
        seen.add(cid)
        state = row.get("state")
        expected = row.get("expected")
        if not isinstance(state, (dict, str, list)) or not isinstance(expected, dict):
            raise TypeError(f"invalid case: {cid}")
        if set(expected) != set(questions):
            raise ValueError(f"expected answer set mismatch: {cid}")
        for qid, q in questions.items():
            exp = expected[qid]
            if q["type"] == "choice" and exp not in q["criteria"]:
                raise ValueError(f"unknown expected choice: {cid}:{qid}")
            if q["type"] == "noul" and type(exp) is not bool:
                raise ValueError(f"noul expected answer must be boolean: {cid}:{qid}")
        case = {"caseId": cid, "state": state, "expected": expected}
        case["caseDigest"] = canonical_digest(case)
        normalized.append(case)
    result = {
        "schemaVersion": 1,
        "kind": value["kind"],
        "corpusId": value.get("corpusId"),
        "standing": value["standing"],
        "nonClaims": list(value.get("nonClaims", [])),
        "questions": questions,
        "cases": normalized,
    }
    result["corpusDigest"] = canonical_digest(result)
    return result


def _probabilities(answer: Mapping[str, Any], keys: list[str], label: str) -> list[float]:
    probs = answer.get("probabilities")
    if not isinstance(probs, dict) or set(probs) != set(keys):
        raise ValueError(f"{label} probability key set mismatch")
    values = []
    for key in keys:
        value = probs[key]
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"{label} invalid probability")
        values.append(float(value))
    if abs(sum(values) - 1.0) > 0.02:
        raise ValueError(f"{label} probabilities do not sum to one")
    return values


def validate_observation(observation: Mapping[str, Any], corpus: Mapping[str, Any]) -> None:
    if (
        observation.get("schemaVersion") != 1
        or observation.get("kind") != "ordivon.system1-decision-benchmark-observation"
    ):
        raise ValueError("decision observation identity mismatch")
    if observation.get("corpusDigest") != corpus["corpusDigest"]:
        raise ValueError("observation corpusDigest mismatch")
    provider = observation.get("provider")
    if not isinstance(provider, dict) or not isinstance(provider.get("providerId"), str):
        raise TypeError("observation requires provider identity")
    rows = observation.get("cases")
    if not isinstance(rows, list) or len(rows) != len(corpus["cases"]):
        raise ValueError("observation case count mismatch")
    expected_by_id = {row["caseId"]: row for row in corpus["cases"]}
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("observation case must be object")
        cid = row.get("caseId")
        if cid in seen or cid not in expected_by_id:
            raise ValueError("observation case identity mismatch")
        seen.add(cid)
        if row.get("caseDigest") != expected_by_id[cid]["caseDigest"]:
            raise ValueError(f"caseDigest mismatch: {cid}")
        standing = row.get("standing")
        if standing not in {"EXECUTED", "ERROR", "BLOCKED"}:
            raise ValueError(f"invalid standing: {cid}")
        latency = row.get("latencyMs")
        if standing == "EXECUTED":
            if type(latency) not in (int, float) or not math.isfinite(latency) or latency < 0:
                raise ValueError(f"EXECUTED case requires latency: {cid}")
            answers = row.get("answers")
            if not isinstance(answers, dict) or set(answers) != set(corpus["questions"]):
                raise ValueError(f"answer set mismatch: {cid}")
            for qid, q in corpus["questions"].items():
                answer = answers[qid]
                if not isinstance(answer, dict):
                    raise TypeError(f"invalid answer: {cid}:{qid}")
                if q["type"] == "choice":
                    keys = list(q["criteria"])
                    _probabilities(answer, keys, f"{cid}:{qid}")
                    if answer.get("choice") not in q["criteria"]:
                        raise ValueError(f"invalid choice: {cid}:{qid}")
                else:
                    p = answer.get("noul")
                    if type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1:
                        raise ValueError(f"invalid noul probability: {cid}:{qid}")
        else:
            if latency is not None or row.get("answers") is not None:
                raise ValueError(f"{standing} case cannot carry latency/answers: {cid}")


def _ece(conf: list[float], correct: list[int], bins: int = 10) -> float | None:
    if not conf:
        return None
    total = 0.0
    for index in range(bins):
        lo, hi = index / bins, (index + 1) / bins
        ids = [
            i for i, value in enumerate(conf)
            if (value > lo and value <= hi) or (index == 0 and value == 0)
        ]
        if ids:
            total += len(ids) / len(conf) * abs(
                mean(conf[i] for i in ids) - mean(correct[i] for i in ids)
            )
    return total


def _percentile95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def score_observation(observation: Mapping[str, Any], corpus: Mapping[str, Any]) -> dict[str, Any]:
    validate_observation(observation, corpus)
    by_case = {row["caseId"]: row for row in corpus["cases"]}
    executed = [row for row in observation["cases"] if row["standing"] == "EXECUTED"]
    latencies = [float(row["latencyMs"]) for row in executed]

    choice_correct: list[int] = []
    choice_conf: list[float] = []
    choice_brier: list[float] = []
    choice_nll: list[float] = []
    noul_correct: list[int] = []
    noul_conf: list[float] = []
    noul_brier: list[float] = []
    noul_nll: list[float] = []

    for row in executed:
        expected = by_case[row["caseId"]]["expected"]
        for qid, q in corpus["questions"].items():
            answer = row["answers"][qid]
            if q["type"] == "choice":
                keys = list(q["criteria"])
                probs = _probabilities(answer, keys, f"{row['caseId']}:{qid}")
                truth = expected[qid]
                idx = keys.index(truth)
                choice_correct.append(int(answer["choice"] == truth))
                choice_conf.append(max(probs))
                choice_brier.append(sum((p - int(i == idx)) ** 2 for i, p in enumerate(probs)))
                choice_nll.append(-math.log(max(probs[idx], 1e-12)))
            else:
                p = float(answer["noul"])
                y = int(expected[qid])
                pred = p >= 0.5
                noul_correct.append(int(pred == bool(y)))
                noul_conf.append(max(p, 1 - p))
                noul_brier.append((p - y) ** 2)
                noul_nll.append(
                    -(y * math.log(max(p, 1e-12)) + (1 - y) * math.log(max(1 - p, 1e-12)))
                )

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.system1-decision-benchmark-score",
        "provider": observation["provider"],
        "corpusId": corpus["corpusId"],
        "corpusDigest": corpus["corpusDigest"],
        "coverage": {
            "totalCases": len(corpus["cases"]),
            "executedCases": len(executed),
            "fraction": len(executed) / len(corpus["cases"]),
            "standings": {
                name: sum(row["standing"] == name for row in observation["cases"])
                for name in ("EXECUTED", "ERROR", "BLOCKED")
            },
        },
        "choice": {
            "n": len(choice_correct),
            "accuracy": mean(choice_correct) if choice_correct else None,
            "meanBrier": mean(choice_brier) if choice_brier else None,
            "meanNll": mean(choice_nll) if choice_nll else None,
            "ece10MaxProbability": _ece(choice_conf, choice_correct),
        },
        "noul": {
            "n": len(noul_correct),
            "accuracyAt0_5": mean(noul_correct) if noul_correct else None,
            "meanBrier": mean(noul_brier) if noul_brier else None,
            "meanNll": mean(noul_nll) if noul_nll else None,
            "ece10": _ece(noul_conf, noul_correct),
        },
        "latencyMs": {
            "median": median(latencies) if latencies else None,
            "mean": mean(latencies) if latencies else None,
            "p95": _percentile95(latencies),
        },
        "nonClaims": [
            "production_calibration",
            "provider_superiority",
            "representative_external_population",
        ],
    }
    result["scoreDigest"] = canonical_digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-corpus")
    score = sub.add_parser("score")
    score.add_argument("--observation-file", type=Path, required=True)
    args = parser.parse_args()
    corpus = load_corpus(args.corpus)
    if args.command == "validate-corpus":
        print(json.dumps({
            "standing": "VALID",
            "corpusId": corpus["corpusId"],
            "corpusDigest": corpus["corpusDigest"],
            "caseCount": len(corpus["cases"]),
        }, sort_keys=True))
        return 0
    observation = _read_json(args.observation_file)
    print(json.dumps(score_observation(observation, corpus), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
