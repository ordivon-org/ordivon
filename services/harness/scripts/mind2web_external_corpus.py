#!/usr/bin/env python3
"""Build a digest-bound Mind2Web System-1 external benchmark corpus."""

from __future__ import annotations

import argparse
import collections
import hashlib
import heapq
import importlib.util
import json
import math
import pickle
import statistics
import zipfile
from pathlib import Path
from typing import Any

EXPECTED_TEST_SHA256 = "8f5fbe72afab942fe97cdf7fb397e179885d89b5c16862288e9a14bc6d41ca89"
EXPECTED_SCORES_SHA256 = "884c97cd9ae0544485d21ea39e0d46422aee0291969a7324e56df3a84466dbd7"
MIND2WEB_GIT_REVISION = "33bd95caeee7bba22dd08ecc935845e15c5e5dc7"
MIND2WEB_HF_REVISION = "17ece8eb89862368edc0cc806acee6fca5163474"
CORPUS_ID = "mind2web-top50-hard5-r1"
RECALL_K = (5, 10, 20, 50)
QUOTAS = {"CLICK": 60, "TYPE": 20, "SELECT": 10}
PASSWORD = b"mind2web"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: list[int], p: float) -> float:
    ordered = sorted(values)
    x = (len(ordered) - 1) * p
    lo = int(x)
    hi = min(lo + 1, len(ordered) - 1)
    fraction = x - lo
    return ordered[lo] * (1 - fraction) + ordered[hi] * fraction


def load_dom_utils(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("mind2web_dom_utils", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Mind2Web dom_utils: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def priority(sample_id: str) -> int:
    raw = hashlib.sha256(f"{CORPUS_ID}\0{sample_id}".encode()).digest()
    return int.from_bytes(raw, "big")


def retain_case(
    reservoirs: dict[tuple[str, str], list[tuple[int, str, dict[str, Any]]]],
    split: str,
    operation: str,
    record: dict[str, Any],
) -> None:
    quota = QUOTAS[operation]
    sample_id = record["sampleId"]
    pr = priority(sample_id)
    heap = reservoirs.setdefault((split, operation), [])
    item = (-pr, sample_id, record)
    if len(heap) < quota:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def candidate_generator_summary(stats: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for split, value in sorted(stats.items()):
        actions = value["actions"]
        cards = value["candidateCards"]
        report[split] = {
            "actions": actions,
            "operations": dict(sorted(value["operations"].items())),
            "missingRankMap": value["missingRankMap"],
            "positiveEmpty": {
                "count": value["positiveEmpty"],
                "rate": value["positiveEmpty"] / actions,
            },
            "positiveSingle": {
                "count": value["positiveSingle"],
                "rate": value["positiveSingle"] / actions,
            },
            "positiveMulti": {
                "count": value["positiveMulti"],
                "rate": value["positiveMulti"] / actions,
            },
            "recall": {
                f"r@{k}": {
                    "count": value["recall"][k],
                    "rate": value["recall"][k] / actions,
                }
                for k in RECALL_K
            },
            "hard5Eligible": {
                "count": value["eligible"],
                "rate": value["eligible"] / actions,
            },
            "candidateCardinality": {
                "median": statistics.median(cards),
                "p95": percentile(cards, 0.95),
                "max": max(cards),
            },
        }
    return report


def official_projection(record: dict[str, Any], dom_utils: Any, etree: Any) -> dict[str, Any]:
    candidate_ids = record["candidateIds"]
    dom_tree = etree.fromstring(record["cleanedHtml"])
    pruned = dom_utils.prune_tree(dom_tree, candidate_ids)
    context, id_mapping = dom_utils.get_tree_repr(
        pruned, id_mapping={}, keep_html_brackets=False
    )
    candidates = []
    for node in pruned.xpath("//*[@backend_node_id]"):
        candidate_id = node.attrib["backend_node_id"]
        text = " ".join(
            dom_utils.get_tree_repr(
                node,
                id_mapping=id_mapping,
                keep_html_brackets=False,
            )[0].split()[:10]
        )
        candidates.append({"candidateId": candidate_id, "text": text})
    expected = set(candidate_ids)
    observed = {row["candidateId"] for row in candidates}
    if observed != expected:
        raise ValueError(
            f"official candidate projection drift for {record['sampleId']}: "
            f"expected={sorted(expected)} observed={sorted(observed)}"
        )
    candidates.sort(
        key=lambda row: hashlib.sha256(
            f"{CORPUS_ID}\0{record['sampleId']}\0{row['candidateId']}".encode()
        ).digest()
    )
    return {
        "caseId": (
            f"mind2web:{record['split']}:{record['operation']}:{record['sampleId']}"
        ),
        "state": {
            "goal": record["goal"],
            "operation": record["operation"],
            "previousActions": record["previousActions"][-5:],
            "context": context,
            "candidates": candidates,
        },
        "expected": {"target": record["positiveId"]},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-zip", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--dom-utils", type=Path, required=True)
    parser.add_argument("--corpus-out", type=Path, required=True)
    parser.add_argument("--candidate-report-out", type=Path, required=True)
    args = parser.parse_args()

    test_digest = sha256_file(args.test_zip)
    score_digest = sha256_file(args.scores)
    if test_digest != EXPECTED_TEST_SHA256:
        raise ValueError(f"Mind2Web test.zip digest mismatch: {test_digest}")
    if score_digest != EXPECTED_SCORES_SHA256:
        raise ValueError(f"Mind2Web scores digest mismatch: {score_digest}")

    with args.scores.open("rb") as handle:
        candidate_results = pickle.load(handle)
    if set(candidate_results) != {"scores", "ranks"}:
        raise ValueError("Mind2Web score-file top-level identity mismatch")
    ranks: dict[str, dict[str, int]] = candidate_results["ranks"]

    reservoirs: dict[
        tuple[str, str], list[tuple[int, str, dict[str, Any]]]
    ] = {}
    stats: dict[str, Any] = {}

    with zipfile.ZipFile(args.test_zip) as archive:
        shards = sorted(name for name in archive.namelist() if name.endswith(".json"))
        for index, shard in enumerate(shards, 1):
            split = shard.split("/", 1)[0]
            split_stats = stats.setdefault(
                split,
                {
                    "actions": 0,
                    "operations": collections.Counter(),
                    "missingRankMap": 0,
                    "positiveEmpty": 0,
                    "positiveSingle": 0,
                    "positiveMulti": 0,
                    "recall": collections.Counter(),
                    "eligible": 0,
                    "candidateCards": [],
                },
            )
            with archive.open(shard, pwd=PASSWORD) as handle:
                tasks = json.load(handle)
            for task in tasks:
                actions = task.get("actions", [])
                action_reprs = task.get("action_reprs", [])
                for action_index, action in enumerate(actions):
                    split_stats["actions"] += 1
                    operation = (action.get("operation") or {}).get("op")
                    split_stats["operations"][operation] += 1
                    pos = action.get("pos_candidates") or []
                    neg = action.get("neg_candidates") or []
                    split_stats["candidateCards"].append(len(pos) + len(neg))
                    split_stats["positiveEmpty"] += int(len(pos) == 0)
                    split_stats["positiveSingle"] += int(len(pos) == 1)
                    split_stats["positiveMulti"] += int(len(pos) > 1)

                    sample_id = f"{task['annotation_id']}_{action['action_uid']}"
                    rank_map = ranks.get(sample_id)
                    if rank_map is None:
                        split_stats["missingRankMap"] += 1
                        continue

                    pos_ids = [row["backend_node_id"] for row in pos]
                    for k in RECALL_K:
                        if any(rank_map.get(candidate_id, math.inf) < k for candidate_id in pos_ids):
                            split_stats["recall"][k] += 1

                    if operation not in QUOTAS or len(pos) != 1:
                        continue
                    positive_id = pos_ids[0]
                    if rank_map.get(positive_id, math.inf) >= 50:
                        continue
                    hard_negatives = sorted(
                        (
                            (rank_map.get(row["backend_node_id"], math.inf), row["backend_node_id"])
                            for row in neg
                            if rank_map.get(row["backend_node_id"], math.inf) < 50
                        ),
                        key=lambda item: (item[0], item[1]),
                    )
                    if len(hard_negatives) < 4:
                        continue

                    split_stats["eligible"] += 1
                    retain_case(
                        reservoirs,
                        split,
                        operation,
                        {
                            "split": split,
                            "sampleId": sample_id,
                            "operation": operation,
                            "goal": task["confirmed_task"],
                            "previousActions": action_reprs[:action_index],
                            "cleanedHtml": action["cleaned_html"],
                            "positiveId": positive_id,
                            "candidateIds": [
                                positive_id,
                                *[candidate_id for _, candidate_id in hard_negatives[:4]],
                            ],
                        },
                    )
            print(
                json.dumps(
                    {
                        "finishedShard": shard,
                        "index": index,
                        "total": len(shards),
                        "actions": split_stats["actions"],
                    }
                ),
                flush=True,
            )

    missing_quota = {}
    selected: list[dict[str, Any]] = []
    for split in sorted(stats):
        for operation, quota in QUOTAS.items():
            rows = reservoirs.get((split, operation), [])
            if len(rows) != quota:
                missing_quota[f"{split}:{operation}"] = {
                    "required": quota,
                    "observed": len(rows),
                }
            selected.extend(
                row[2] for row in sorted(rows, key=lambda item: (-item[0], item[1]))
            )
    if missing_quota:
        raise ValueError(f"Mind2Web sample quota unsatisfied: {missing_quota}")

    dom_utils = load_dom_utils(args.dom_utils)
    from lxml import etree

    cases = [official_projection(row, dom_utils, etree) for row in selected]
    cases.sort(key=lambda row: row["caseId"])

    candidate_report = {
        "schemaVersion": 1,
        "kind": "mind2web-candidate-generator-ceiling",
        "source": {
            "gitRevision": MIND2WEB_GIT_REVISION,
            "hfRevision": MIND2WEB_HF_REVISION,
            "testZipSha256": EXPECTED_TEST_SHA256,
            "scoresSha256": EXPECTED_SCORES_SHA256,
        },
        "splits": candidate_generator_summary(stats),
    }
    args.candidate_report_out.parent.mkdir(parents=True, exist_ok=True)
    args.candidate_report_out.write_text(
        json.dumps(candidate_report, indent=2, sort_keys=True) + "\n"
    )

    corpus = {
        "schemaVersion": 1,
        "kind": "ordivon.system1-decision-corpus",
        "corpusId": CORPUS_ID,
        "standing": "EXTERNAL_BENCHMARK",
        "source": {
            "dataset": "osunlp/Mind2Web",
            "gitRevision": MIND2WEB_GIT_REVISION,
            "hfRevision": MIND2WEB_HF_REVISION,
            "testZipSha256": EXPECTED_TEST_SHA256,
            "scoresSha256": EXPECTED_SCORES_SHA256,
            "adaptation": {
                "candidateGenerator": "official published scores_all_data.pkl",
                "candidateRankGate": "positive rank < 50",
                "candidateSet": "one unique positive plus four highest-ranked negatives",
                "elementProjection": "official prune_tree + get_tree_repr",
                "selection": "sha256-priority stratified by split and operation",
                "candidateOrder": "sha256(case identity + candidate identity) deterministic permutation",
                "quotaPerSplit": QUOTAS,
                "excluded": [
                    "positive candidate missing from top-50",
                    "zero positive candidates",
                    "multiple positive candidates",
                    "fewer than four top-50 negative candidates",
                ],
            },
        },
        "nonClaims": [
            "full Mind2Web action-prediction reproduction",
            "candidate-generator-free performance",
            "multi-positive action coverage",
            "production browser calibration",
            "provider superiority",
        ],
        "questions": {
            "target": {
                "type": "dynamic_choice",
                "candidateSetField": "candidates",
                "instructions": (
                    "Choose the page element to interact with next to make progress "
                    "on the task, given the recent actions and pruned page context."
                ),
            }
        },
        "cases": cases,
    }
    args.corpus_out.parent.mkdir(parents=True, exist_ok=True)
    args.corpus_out.write_text(json.dumps(corpus, indent=2, sort_keys=True) + "\n")

    print(
        json.dumps(
            {
                "corpus": str(args.corpus_out),
                "cases": len(cases),
                "candidateReport": str(args.candidate_report_out),
                "quotas": QUOTAS,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
