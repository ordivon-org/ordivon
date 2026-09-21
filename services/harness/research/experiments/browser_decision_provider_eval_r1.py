#!/usr/bin/env python3
"""Execute one provider against Browser Decision Corpus R1 without browser effects."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import system1_decision_benchmark as benchmark  # noqa: E402

DEFAULT_CORPUS = ROOT / "config/browser-decision-corpus-r1.json"
CROSS_ENCODER = Path(
    "/root/.local/share/ordivon/experimental/retrieval-models/"
    "ms-marco-MiniLM-L6-v2/233902d25c440f23af6f7d6e94d2946bac0bee0a"
)
LAYA_MODEL = Path(
    "/root/.local/share/ordivon/experimental/laya-models/"
    "1c5edc17a7acd8701df6fc341c0d179f1c62c982"
)


def candidate_text(candidate: dict[str, Any]) -> str:
    rows = [
        f"operation: {candidate.get('operation', '')}",
        f"role: {candidate.get('role', '')}",
        f"name: {candidate.get('name', '')}",
    ]
    for key in ("description", "context", "value", "optionName", "href"):
        value = candidate.get(key)
        if value not in (None, "", {}):
            rows.append(f"{key}: {value}")
    states = candidate.get("states")
    if isinstance(states, dict) and states:
        rows.append(
            "states: "
            + json.dumps(states, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        )
    context_ref = candidate.get("contextRef")
    if context_ref and context_ref != "main":
        rows.append(f"browsing context: {context_ref}")
    return "\n".join(rows)


def _softmax(values: list[float]) -> list[float]:
    if not values:
        raise ValueError("cannot normalize empty score list")
    top = max(values)
    exps = [math.exp(value - top) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def _observation(corpus: dict[str, Any], provider: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.system1-decision-benchmark-observation",
        "corpusDigest": corpus["corpusDigest"],
        "provider": provider,
        "cases": cases,
    }


def crossencoder_observation(corpus: dict[str, Any]) -> dict[str, Any]:
    import torch
    from sentence_transformers import CrossEncoder

    if not CROSS_ENCODER.joinpath("model.safetensors").is_file():
        raise FileNotFoundError(CROSS_ENCODER)
    model = CrossEncoder(str(CROSS_ENCODER), device="cuda" if torch.cuda.is_available() else "cpu")
    model.predict([["warm", "warm"]], show_progress_bar=False)

    rows = []
    for case in corpus["cases"]:
        state = case["state"]
        candidates = state["candidates"]
        query = f"Browser goal: {state['goal']}\nRequired operation: {state['operation']}"
        pairs = [[query, candidate_text(candidate)] for candidate in candidates]
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        started = time.perf_counter()
        raw = model.predict(pairs, batch_size=128, show_progress_bar=False)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - started) * 1000.0
        scores = [float(value) for value in raw]
        probs = _softmax(scores)
        best = max(range(len(probs)), key=probs.__getitem__)
        probability_map = {
            candidate["candidateId"]: probs[index] for index, candidate in enumerate(candidates)
        }
        rows.append(
            {
                "caseId": case["caseId"],
                "caseDigest": case["caseDigest"],
                "standing": "EXECUTED",
                "latencyMs": latency_ms,
                "answers": {
                    "target": {
                        "choice": candidates[best]["candidateId"],
                        "probabilities": probability_map,
                    }
                },
            }
        )
    return _observation(
        corpus,
        {
            "providerId": "crossencoder-msmarco-minilm-l6-v2",
            "implementation": "sentence-transformers",
            "model": "cross-encoder/ms-marco-MiniLM-L6-v2",
            "revision": "233902d25c440f23af6f7d6e94d2946bac0bee0a",
            "modelSha256": "821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae",
            "distribution": "softmax_over_pair_logits",
            "standing": "EXPERIMENTAL_BASELINE",
        },
        rows,
    )


def laya_observation(corpus: dict[str, Any]) -> dict[str, Any]:
    import torch
    import laya

    if not LAYA_MODEL.joinpath("model.safetensors").is_file():
        raise FileNotFoundError(LAYA_MODEL)
    agent = laya.load(str(LAYA_MODEL), device="cuda" if torch.cuda.is_available() else "cpu")
    agent.predict(
        {"goal": "warm"},
        {
            "warm": {
                "type": "noul",
                "instructions": "Does the candidate fulfill the goal?",
                "criteria": {"false": "no", "true": "yes"},
            }
        },
    )

    rows = []
    for case in corpus["cases"]:
        state = case["state"]
        candidates = state["candidates"]
        questions = {}
        for index, candidate in enumerate(candidates):
            questions[f"c{index}"] = {
                "type": "noul",
                "instructions": (
                    "Does this candidate directly fulfill the browser goal using the required "
                    f"operation?\nGoal: {state['goal']}\nRequired operation: "
                    f"{state['operation']}\nCandidate:\n{candidate_text(candidate)}"
                ),
                "criteria": {
                    "false": "candidate does not directly fulfill the goal",
                    "true": "candidate directly fulfills the goal",
                },
            }
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        started = time.perf_counter()
        result = agent.predict(
            {"goal": state["goal"], "operation": state["operation"]},
            questions,
        )
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - started) * 1000.0
        raw_probs = [
            float(result["answers"][f"c{index}"]["noul"])
            for index in range(len(candidates))
        ]
        total = sum(raw_probs)
        probs = (
            [value / total for value in raw_probs]
            if total > 0
            else [1.0 / len(raw_probs)] * len(raw_probs)
        )
        best = max(range(len(probs)), key=probs.__getitem__)
        probability_map = {
            candidate["candidateId"]: probs[index] for index, candidate in enumerate(candidates)
        }
        rows.append(
            {
                "caseId": case["caseId"],
                "caseDigest": case["caseDigest"],
                "standing": "EXECUTED",
                "latencyMs": latency_ms,
                "answers": {
                    "target": {
                        "choice": candidates[best]["candidateId"],
                        "probabilities": probability_map,
                    }
                },
            }
        )
    return _observation(
        corpus,
        {
            "providerId": "laya-base-independent-noul",
            "implementation": "laya",
            "version": "0.3.4",
            "modelRevision": "1c5edc17a7acd8701df6fc341c0d179f1c62c982",
            "modelSha256": "891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c",
            "distribution": "normalized_independent_noul_probabilities",
            "standing": "EXPERIMENTAL_BASE_MODEL",
        },
        rows,
    )


def blocked_jev_observation(corpus: dict[str, Any]) -> dict[str, Any]:
    rows = [
        {
            "caseId": case["caseId"],
            "caseDigest": case["caseDigest"],
            "standing": "BLOCKED",
            "latencyMs": None,
            "answers": None,
        }
        for case in corpus["cases"]
    ]
    return _observation(
        corpus,
        {
            "providerId": "jev-fast-windows-v1",
            "implementation": "jev-ultrafast",
            "version": "0.1.0",
            "sourceRevision": "452c1ad2dd628008f1d5608f28158d76e49e6cc0",
            "routeStanding": "WORKSTATION_PROVIDER_UNHEALTHY",
            "missingEnvironmentNames": ["TYPESAFE_API_KEY"],
            "standing": "BLOCKED_BY_EXISTING_ROUTE_READINESS",
        },
        rows,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--provider", choices=("crossencoder", "laya", "jev-blocked"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    corpus = benchmark.load_corpus(args.corpus)
    if args.provider == "crossencoder":
        observation = crossencoder_observation(corpus)
    elif args.provider == "laya":
        observation = laya_observation(corpus)
    else:
        observation = blocked_jev_observation(corpus)

    benchmark.validate_observation(observation, corpus)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(observation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "providerId": observation["provider"]["providerId"],
                "corpusDigest": corpus["corpusDigest"],
                "caseCount": len(observation["cases"]),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
