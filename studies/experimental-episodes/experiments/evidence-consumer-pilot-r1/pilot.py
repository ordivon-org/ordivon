"""One bounded Research consumer experiment: exact Episode evidence vs no evidence.

This is a paired factual/decision-support pilot, NOT an Episode memory-learning
or held-out capability generalization experiment. No new service, index or PG.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
SOURCE = {
    "manifest": "studies/experimental-episodes/evidence/corpus-r1/manifest.json",
    "analysis": "studies/experimental-episodes/evidence/analysis/experimental-system-analysis-r1.json",
    "product": "catalogs/data-products/experimental-episode-corpus-r1/odps.json",
}
CASES = [
    (
        "projectedEpisodes",
        "How many total R1 Episodes are in the product? Return an integer.",
        "manifest",
    ),
    (
        "runtimeSucceeded",
        "How many Runtime historical R5C Episodes have state succeeded? Return an integer.",
        "analysis",
    ),
    (
        "runtimeFailed",
        "How many Runtime historical R5C Episodes have state failed? Return an integer.",
        "analysis",
    ),
    (
        "harnessSucceededRefs",
        "How many cited Harness Runtime Job references resolved as succeeded? Return an integer.",
        "manifest",
    ),
    (
        "harnessCostCoverage",
        "For how many Harness Episodes does the analysis observe provider-cost coverage? Return an integer.",
        "analysis",
    ),
    (
        "developmentEpisodes",
        "How many DEVELOPMENT Episodes are present in the R1 experimental design? Return an integer.",
        "analysis",
    ),
    (
        "judgeEpisodes",
        "How many JUDGE Episodes are present in the R1 experimental design? Return an integer.",
        "analysis",
    ),
    (
        "causalStanding",
        "What is the formal standing of identified intervention effects? Return IDENTIFIED or NOT_IDENTIFIED.",
        "analysis",
    ),
    (
        "retentionSchedule",
        "What is the exact retention schedule status for the data product? Return the status token.",
        "product",
    ),
    (
        "promotionDecision",
        "Based only on the evidence, should an autonomous self-improving Agent be promoted to production due to this corpus? Return PROMOTE or HOLD.",
        "analysis",
    ),
]
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "answer": {"type": "string"},
                    "evidenceRef": {"type": "string"},
                },
                "required": ["id", "answer", "evidenceRef"],
            },
        }
    },
    "required": ["answers"],
}


def canonical_bytes(v: Any) -> bytes:
    return json.dumps(
        v, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()


def sha(v: bytes) -> str:
    return "sha256:" + hashlib.sha256(v).hexdigest()


def evidence() -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
    documents: dict[str, dict[str, Any]] = {}
    digests: dict[str, str] = {}
    for name, relative in SOURCE.items():
        file = ROOT / relative
        data = file.read_bytes()
        digests[name] = sha(data)
        documents[name] = json.loads(data)

    manifest, analysis, product = (documents[name] for name in SOURCE)
    profiles = {v["profileId"]: v for v in manifest["profiles"]}
    harness = profiles["harness-rsi-acceptance-v1"]
    runtime = profiles["runtime-r5c-v1"]
    properties = {x["property"]: x["value"] for x in product["customProperties"]}
    assert runtime["projectedEpisodes"] == 10000
    assert harness["projectedEpisodes"] == 7
    assert analysis["generalization"]["standing"] == "NOT_IDENTIFIED"
    assert analysis["intervention"]["standing"] == "NOT_IDENTIFIED"
    assert analysis["cost"]["harnessEpisodes"] == 7

    witness = {
        "manifest": {
            "corpusId": manifest["corpusId"],
            "profileEpisodeCounts": {
                p: v["projectedEpisodes"] for p, v in profiles.items()
            },
            "harnessRuntimeJobJoin": harness["exactRuntimeJoin"],
        },
        "analysis": {
            "runtimeExecutionStateDistribution": analysis["failure"][
                "runtimeExecutionStateDistribution"
            ],
            "harnessEpisodes": analysis["cost"]["harnessEpisodes"],
            "harnessProviderCostCoverageEpisodes": analysis["cost"][
                "harnessProviderCostCoverageEpisodes"
            ],
            "costNonClaims": analysis["cost"]["nonClaims"],
            "generalization": analysis["generalization"],
            "intervention": analysis["intervention"],
            "analysisBoundary": analysis["analysisBoundary"],
            "failureNonClaims": analysis["failure"]["nonClaims"],
        },
        "product": {
            "retentionScheduleStatus": properties["retentionScheduleStatus"],
            "automaticDeletionStatus": properties["automaticDeletionStatus"],
            "sourceRightsStatus": properties["sourceRightsStatus"],
            "constraintNoGeneralization": next(
                x["constraint"]
                for x in product["context"]["constraints"]
                if x["id"] == "no-generalization-overclaim"
            ),
        },
    }
    actual = analysis["failure"]["runtimeExecutionStateDistribution"]
    gold = {
        "projectedEpisodes": str(
            sum(v["projectedEpisodes"] for v in profiles.values())
        ),
        "runtimeSucceeded": str(actual["succeeded"]),
        "runtimeFailed": str(actual["failed"]),
        "harnessSucceededRefs": str(
            harness["exactRuntimeJoin"]["resolutionDistribution"]["succeeded"]
        ),
        "harnessCostCoverage": str(
            analysis["cost"]["harnessProviderCostCoverageEpisodes"]
        ),
        "developmentEpisodes": str(analysis["generalization"]["developmentEpisodes"]),
        "judgeEpisodes": str(analysis["generalization"]["judgeEpisodes"]),
        "causalStanding": analysis["intervention"]["standing"],
        "retentionSchedule": properties["retentionScheduleStatus"],
        "promotionDecision": "HOLD",
    }
    assert set(gold) == {c[0] for c in CASES}
    return witness, digests, gold


def grade(output: dict[str, Any], gold: dict[str, str]) -> dict[str, Any]:
    responses = output.get("answers", [])
    lookup = {}
    for response in responses:
        if response.get("id") in lookup:
            raise ValueError("duplicate answer id")
        lookup[response["id"]] = response
    if set(lookup) != set(gold):
        raise ValueError("missing or unexpected answer id")
    rows = []
    for case_id, _question, reference in CASES:
        response = lookup[case_id]
        answer = response["answer"].strip()
        correct = answer == gold[case_id]
        unknown = answer == "UNKNOWN"
        backed = correct and response.get("evidenceRef") == reference
        rows.append(
            {
                "id": case_id,
                "answer": answer,
                "expected": gold[case_id],
                "correct": correct,
                "unknown": unknown,
                "unsupported": not correct and not unknown,
                "evidenceBackedCorrect": backed,
            }
        )
    return {
        "count": len(rows),
        "correct": sum(x["correct"] for x in rows),
        "unknown": sum(x["unknown"] for x in rows),
        "unsupported": sum(x["unsupported"] for x in rows),
        "evidenceBackedCorrect": sum(x["evidenceBackedCorrect"] for x in rows),
        "cases": rows,
    }


def prompt(arm: str, witness: dict[str, Any]) -> str:
    if arm not in ("control", "evidence"):
        raise ValueError("unknown arm")
    questions = [{"id": name, "question": question} for name, question, _ in CASES]
    head = (
        "You are the Research consumer for one historical internal Ordivon Episode R1 data product. "
        "Do not use the internet, shell, prior chats or source code. Use ONLY the evidence included "
        "in this prompt. For each question, return one exact token or decimal integer as the answer. "
        "If the provided evidence cannot support that answer, return UNKNOWN; never invent counts. "
        "For production promotion, require explicit valid development/judge and intervention evidence; "
        "if it is missing, return HOLD. "
        "evidenceRef must be one of manifest, analysis, product if the answer has support from "
        "that document in the prompt; otherwise set evidenceRef to empty string. "
        "Report all cases in JSON. The question id and question text are evaluation instructions, "
        "not observations. No unprovided document contents may be assumed.\n"
    )
    block = "NO SOURCE DOCUMENT EVIDENCE WAS PROVIDED TO THIS ARM."
    if arm == "evidence":
        block = "EXACT SOURCE-BOUND OBSERVED EVIDENCE FIELDS:\n" + json.dumps(
            witness, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
    return (
        head
        + "\n"
        + block
        + "\nQUESTIONS:\n"
        + json.dumps(questions, ensure_ascii=False)
    )


def run_agent(*, arm: str, witness: dict[str, Any], timeout: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(
        prefix="ordivon-episode-evidence-agent-"
    ) as scratch:
        work = Path(scratch)
        schema = work / "output-schema.json"
        output = work / "final.json"
        schema.write_text(json.dumps(SCHEMA))
        cmd = [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox",
            "read-only",
            "--output-schema",
            str(schema),
            "--output-last-message",
            str(output),
            prompt(arm, witness),
        ]
        start = time.monotonic()
        completed = subprocess.run(
            cmd,
            cwd=work,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=os.environ.copy(),
        )
        elapsed = round(time.monotonic() - start, 3)
        if completed.returncode != 0 or not output.is_file():
            return {
                "status": "ERROR_NO_MODEL_SCORE",
                "elapsedSeconds": elapsed,
                "returnCode": completed.returncode,
                "stderrTail": completed.stderr[-600:],
            }
        return {
            "status": "MODEL_ANSWERED",
            "elapsedSeconds": elapsed,
            "rawAnswer": json.loads(output.read_text()),
            "modelVersionHint": re.search(
                r"(?m)^model:\s*(.+)$", completed.stderr
            ).group(1)
            if re.search(r"(?m)^model:\s*(.+)$", completed.stderr)
            else "UNKNOWN",
            "nativeStderrSha256": sha(completed.stderr.encode()),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--model",
        action="store_true",
        help="run two paired blocks of actual Codex CLI calls",
    )
    parser.add_argument("--timeout-seconds", type=int, default=115)
    args = parser.parse_args()
    witness, source_digests, gold = evidence()
    contract = {
        "kind": "ordivon.episode-research-consumer-evidence-ab-r1",
        "scope": "HISTORICAL_CORPUS_FACTUAL_DECISION_SUPPORT_NOT_EPISODE_MEMORY_LEARNING",
        "sourceDigests": source_digests,
        "caseCount": len(CASES),
        "caseIds": [row[0] for row in CASES],
        "scorer": "literal exact-match, explicit UNKNOWN abstention, per-field source-id check",
        "conditions": ["control_no_source", "evidence_exact_source_bound_fields"],
        "assignment": ["control", "evidence", "evidence", "control"],
        "promotionPolicy": "HOLD without independent improvement on actual held-out task success",
        "nonClaims": [
            "not raw replay Episode retrieval",
            "not randomized representative production workload",
            "not a valid statistical causal or generalization claim",
            "not a test of autonomous agent skill improvement",
        ],
    }
    contract["contractSha256"] = sha(canonical_bytes(contract))
    record: dict[str, Any] = {
        "contract": contract,
        "caseGoldSourceBound": gold,
        "runs": [],
    }
    if args.model:
        for ordinal, arm in enumerate(contract["assignment"], start=1):
            observed = run_agent(arm=arm, witness=witness, timeout=args.timeout_seconds)
            if observed["status"] == "MODEL_ANSWERED":
                observed["score"] = grade(observed["rawAnswer"], gold)
            record["runs"].append({"run": ordinal, "arm": arm, **observed})
            print(
                json.dumps(
                    {
                        "run": ordinal,
                        "arm": arm,
                        "status": observed["status"],
                        "score": observed.get("score", {}).get("correct"),
                        "unknown": observed.get("score", {}).get("unknown"),
                        "time": observed["elapsedSeconds"],
                    }
                ),
                flush=True,
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    print("WROTE_EXACT_RESEARCH_CONSUMER_RECEIPT", args.output, flush=True)


if __name__ == "__main__":
    main()
