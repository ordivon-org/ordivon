#!/usr/bin/env python3
"""Run base Laya on a provider-neutral Mind2Web dynamic-choice corpus."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path
from typing import Any

import laya
import torch
from laya import Agent


def load_benchmark_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("system1_decision_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark contract: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def model_revision(model_path: Path) -> str:
    name = model_path.name
    if len(name) == 40 and all(c in "0123456789abcdef" for c in name.lower()):
        return name
    return "unknown-local-revision"


def sync(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def case_payload(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    state = case["state"]
    candidates = state["candidates"]
    provider_state = {
        "goal": state["goal"],
        "operation": state["operation"],
        "previousActions": state["previousActions"],
        "context": state["context"],
    }
    question = {
        "type": "choice",
        "instructions": (
            "Choose the page element to interact with next for the known operation "
            "to make progress on the task."
        ),
        "criteria": {
            row["candidateId"]: row["text"]
            for row in candidates
        },
    }
    return provider_state, {"target": question}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--benchmark-contract", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    contract = load_benchmark_module(args.benchmark_contract)
    corpus = contract.load_corpus(args.corpus)
    if corpus["standing"] != "EXTERNAL_BENCHMARK":
        raise ValueError("Mind2Web Laya run requires EXTERNAL_BENCHMARK corpus")

    load_started = time.perf_counter()
    agent = Agent(str(args.model), device="cuda")
    sync(agent.device)
    load_ms = (time.perf_counter() - load_started) * 1000.0
    if agent.device.type != "cuda":
        raise RuntimeError(f"expected CUDA Laya execution, observed {agent.device}")

    first_state, first_question = case_payload(corpus["cases"][0])
    agent.system_one(first_state, first_question)
    sync(agent.device)

    rows = []
    for index, case in enumerate(corpus["cases"], 1):
        state, questions = case_payload(case)
        sync(agent.device)
        started = time.perf_counter()
        result = agent.system_one(state, questions)
        sync(agent.device)
        latency_ms = (time.perf_counter() - started) * 1000.0
        answer = result["answers"]["target"]
        probabilities = {
            key: float(value)
            for key, value in answer["probabilities"].items()
        }
        total = sum(probabilities.values())
        if total <= 0:
            raise ValueError("Laya emitted non-positive probability mass")
        probabilities = {
            key: value / total for key, value in probabilities.items()
        }
        rows.append({
            "caseId": case["caseId"],
            "caseDigest": case["caseDigest"],
            "standing": "EXECUTED",
            "latencyMs": latency_ms,
            "answers": {
                "target": {
                    "choice": answer["choice"],
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
            "providerId": "laya-base-listwise-hard5",
            "implementation": "laya",
            "version": laya.__version__,
            "modelRevision": model_revision(args.model),
            "device": str(agent.device),
            "dtype": str(agent.dtype),
            "maxLen": agent.cfg.get("max_len"),
            "headMaxLen": agent.cfg.get("head_max_len"),
            "warmupCalls": 1,
            "modelLoadMs": load_ms,
            "representation": (
                "state=goal+known-operation+recent-actions+official-pruned-context; "
                "choice-criteria=5 official Mind2Web candidate projections"
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
