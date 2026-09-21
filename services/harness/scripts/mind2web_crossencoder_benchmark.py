#!/usr/bin/env python3
"""Run a mature generic CrossEncoder on the Mind2Web hard-5 corpus."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import sentence_transformers
import torch
from sentence_transformers import CrossEncoder


def load_contract(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("system1_decision_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark contract: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sync(device: str) -> None:
    if device.startswith("cuda"):
        torch.cuda.synchronize()


def query_text(state: dict[str, Any]) -> str:
    parts = [
        f"Task: {state['goal']}",
        f"Operation: {state['operation']}",
    ]
    if state["previousActions"]:
        parts.append("Previous actions: " + "; ".join(state["previousActions"][-5:]))
    parts.append("Page context: " + state["context"])
    return "\n".join(parts)


def softmax(values: np.ndarray) -> np.ndarray:
    x = values.astype(np.float64)
    x = x - np.max(x)
    e = np.exp(x)
    return e / e.sum()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--benchmark-contract", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    contract = load_contract(args.benchmark_contract)
    corpus = contract.load_corpus(args.corpus)
    if corpus["standing"] != "EXTERNAL_BENCHMARK":
        raise ValueError("CrossEncoder benchmark requires EXTERNAL_BENCHMARK corpus")

    load_started = time.perf_counter()
    model = CrossEncoder(str(args.model), device="cuda")
    sync("cuda")
    load_ms = (time.perf_counter() - load_started) * 1000.0

    first = corpus["cases"][0]
    q = query_text(first["state"])
    pairs = [[q, row["text"]] for row in first["state"]["candidates"]]
    model.predict(pairs, convert_to_numpy=True, show_progress_bar=False)
    sync("cuda")

    rows = []
    for index, case in enumerate(corpus["cases"], 1):
        state = case["state"]
        q = query_text(state)
        candidates = state["candidates"]
        pairs = [[q, row["text"]] for row in candidates]
        sync("cuda")
        started = time.perf_counter()
        logits = np.asarray(
            model.predict(
                pairs,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        ).reshape(-1)
        sync("cuda")
        latency_ms = (time.perf_counter() - started) * 1000.0
        if logits.shape[0] != len(candidates):
            raise ValueError(f"unexpected CrossEncoder shape: {logits.shape}")
        probs = softmax(logits)
        winner = int(np.argmax(probs))
        probabilities = {
            row["candidateId"]: float(prob)
            for row, prob in zip(candidates, probs, strict=True)
        }
        if not math.isclose(sum(probabilities.values()), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("CrossEncoder probability mass drift")
        rows.append({
            "caseId": case["caseId"],
            "caseDigest": case["caseDigest"],
            "standing": "EXECUTED",
            "latencyMs": latency_ms,
            "answers": {
                "target": {
                    "choice": candidates[winner]["candidateId"],
                    "probabilities": probabilities,
                }
            },
        })
        if index % 30 == 0 or index == len(corpus["cases"]):
            print(json.dumps({
                "progress": index,
                "total": len(corpus["cases"]),
                "executed": len(rows),
            }), flush=True)

    observation = {
        "schemaVersion": 1,
        "kind": "ordivon.system1-decision-benchmark-observation",
        "corpusDigest": corpus["corpusDigest"],
        "provider": {
            "providerId": "crossencoder-msmarco-minilm-l6-v2-hard5",
            "implementation": "sentence-transformers",
            "sentenceTransformersVersion": sentence_transformers.__version__,
            "model": "cross-encoder/ms-marco-MiniLM-L6-v2",
            "modelRevision": "233902d25c440f23af6f7d6e94d2946bac0bee0a",
            "device": "cuda",
            "distribution": "softmax_over_pair_logits",
            "warmupCases": 1,
            "modelLoadMs": load_ms,
            "representation": (
                "query=goal+known-operation+recent-actions+official-pruned-context; "
                "document=official Mind2Web candidate projection"
            ),
        },
        "cases": rows,
    }
    contract.validate_observation(observation, corpus)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(observation, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(args.output),
        "executed": len(rows),
        "modelLoadMs": load_ms,
        "corpusDigest": corpus["corpusDigest"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
