#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import time
from typing import Any, Callable

from anc_canonical import canonical_digest
from ordivon_harness.ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter
from ordivon_harness.ordivon.model import AgentToolDefinition, AgentTurnRequest

ROOT = Path(__file__).resolve().parents[4]
CORPUS = ROOT / "docs/architecture/evidence/agent-native-cognitive-environment-f7-live-ab-corpus-r1.json"
EXPECTED_CORPUS_SHA256 = "dae05b5c8552ae1cd39740accce5da32719b5dab9350784e615e96395303002e"
CARRIER = ROOT / "docs/architecture/evidence/agent-native-f7-carrier-r1"
EXPECTED_CARRIER = {
    "cognitive_projection_r1.py": "370fc216fe87ccbc88d0403a44092960502f5976806dde9d3a014dce512b341e",
    "cognitive_orientation_r1.py": "0f3924bab6f15f9106d293dc64d850d358091b73e609ac71a16310d971394996",
    "cognitive_delta_r1.py": "c83295405f5aaa4630d9d4ef77c01c250e1a474a3f689c08f27f317bca6895e3",
}
CRITICAL = {"living-authority", "browser-next-action", "browser-unknown"}
CURRENTNESS = {"living-current-candidate", "browser-currentness"}
NEXT_ACTION = {"living-next-action", "browser-next-action"}

SYSTEM = (
    "Fresh Agent orientation benchmark. Use only the supplied structured current context. "
    "Natural-owner observations may show that semantic continuity prose is stale, but each "
    "observation is authoritative only inside its stated truth boundary. A projection never "
    "grants execution, effect, semantic-acceptance, or domain authority. UNKNOWN remains UNKNOWN. "
    "Call submit_answer exactly once with A, B, C, or D. Do not perform any external effect."
)

ANSWER_TOOL = AgentToolDefinition(
    name="submit_answer",
    description="Submit the single benchmark answer. This is scoring-only and has no external effect.",
    input_schema={
        "type": "object",
        "properties": {"answer": {"type": "string", "enum": ["A", "B", "C", "D"]}},
        "required": ["answer"],
        "additionalProperties": False,
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_inputs() -> tuple[dict[str, Any], Callable[..., dict[str, object]], Callable[..., dict[str, object]]]:
    actual = sha256(CORPUS)
    if actual != EXPECTED_CORPUS_SHA256:
        raise RuntimeError(f"corpus digest differs: {actual}")
    for name, expected in EXPECTED_CARRIER.items():
        actual = sha256(CARRIER / name)
        if actual != expected:
            raise RuntimeError(f"carrier digest differs for {name}: {actual}")
    corpus = json.loads(CORPUS.read_text())
    projection = load_module("f7_projection", CARRIER / "cognitive_projection_r1.py")
    orientation = load_module("f7_orientation", CARRIER / "cognitive_orientation_r1.py")
    return corpus, projection.project_agent_cognitive_environment, orientation.project_agent_orientation_view


def build_contexts(corpus: dict[str, Any], project, orient) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    metrics: dict[str, Any] = {}
    for consumer in corpus["cases"]:
        cid = consumer["consumerId"]
        raw = {
            "schemaVersion": 1,
            "kind": "ordivon.agent-native-f7-raw-current-material",
            "work": consumer["work"],
            "ownerObservations": consumer["ownerObservations"],
            "proofBoundary": (
                "Raw benchmark material. Host Work is semantic continuity; supplied owner observations "
                "retain their own truth boundaries. No authority is granted by packaging."
            ),
        }
        exact = project(
            consumer["work"],
            owner_observations=consumer["ownerObservations"],
        )
        compact = orient(exact)
        for value in (exact, compact):
            authority = value["authority"]
            if any(authority.values()):
                raise AssertionError(f"{cid} treatment carries authority: {authority}")
        contexts[cid] = {"A": raw, "B": exact, "C": compact}
        metrics[cid] = {
            t: len(json.dumps(v, sort_keys=True, separators=(",", ":")).encode())
            for t, v in contexts[cid].items()
        }
    return contexts, metrics


def questions(corpus: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for consumer in corpus["cases"]:
        for q in consumer["questions"]:
            row = dict(q)
            row["consumerId"] = consumer["consumerId"]
            if row["id"] in out:
                raise AssertionError(f"duplicate question {row['id']}")
            out[row["id"]] = row
    return out


def compile_request(context: dict[str, Any], question: dict[str, Any], treatment: str) -> AgentTurnRequest:
    options = "\n".join(f"{key}. {value}" for key, value in question["options"].items())
    user = (
        "STRUCTURED CURRENT CONTEXT:\n"
        + json.dumps(context, sort_keys=True, separators=(",", ":"))
        + "\n\nQUESTION:\n"
        + question["prompt"]
        + "\n"
        + options
    )
    messages = (
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    )
    return AgentTurnRequest(
        harness_run_id=f"harness-run:agent-native-f7:{question['id']}:{treatment}",
        turn_id=f"turn:agent-native-f7:{question['id']}:{treatment}:1",
        sequence=1,
        assignment_id=f"assignment:agent-native-f7:{question['id']}:{treatment}",
        context_digest=canonical_digest(list(messages)),
        tool_catalog_digest=canonical_digest([ANSWER_TOOL.to_dict()]),
        messages=messages,
        tools=(ANSWER_TOOL,),
        remaining_budget={
            "modelCalls": 1,
            "modelRetries": 0,
            "toolCalls": 1,
            "wallTimeMs": 90_000,
            "observationOnlyTurns": 1,
            "noProgressTurns": 1,
        },
    )


def validate_only() -> dict[str, Any]:
    corpus, project, orient = load_inputs()
    contexts, context_bytes = build_contexts(corpus, project, orient)
    qs = questions(corpus)
    expected_ids = {item["questionId"] for item in corpus["trialOrder"]}
    if expected_ids != set(qs):
        raise AssertionError("trial/question coverage differs")
    if len(corpus["trialOrder"]) != 18:
        raise AssertionError("expected 18 frozen trials")
    for qid in qs:
        ts = [row["treatment"] for row in corpus["trialOrder"] if row["questionId"] == qid]
        if sorted(ts) != ["A", "B", "C"]:
            raise AssertionError(f"treatment coverage differs for {qid}")
    if len(contexts) != 2:
        raise AssertionError("expected exactly two real consumers")
    return {
        "verdict": "PASS",
        "corpusSha256": EXPECTED_CORPUS_SHA256,
        "carrierSha256": EXPECTED_CARRIER,
        "consumerCount": len(contexts),
        "questionCount": len(qs),
        "trialCount": len(corpus["trialOrder"]),
        "contextBytes": context_bytes,
        "criticalQuestions": sorted(CRITICAL),
        "nonClaims": [
            "preflight proves frozen mechanics only, not model behavior",
            "owner observations are supplied rather than autonomously discovered",
        ],
    }


def run_live(output: Path) -> dict[str, Any]:
    corpus, project, orient = load_inputs()
    contexts, context_bytes = build_contexts(corpus, project, orient)
    qs = questions(corpus)
    settings = DeepSeekSettings.from_secret_file(timeout_seconds=60.0, max_output_tokens=128)
    trials: list[dict[str, Any]] = []
    for ordinal, item in enumerate(corpus["trialOrder"], 1):
        q = qs[item["questionId"]]
        treatment = item["treatment"]
        context = contexts[q["consumerId"]][treatment]
        request = compile_request(context, q, treatment)
        adapter = DeepSeekTurnAdapter(settings)
        _, _, _, body = adapter._prepare_request(request)
        row: dict[str, Any] = {
            "ordinal": ordinal,
            "questionId": q["id"],
            "consumerId": q["consumerId"],
            "treatment": treatment,
            "correctAnswer": q["correct"],
            "contextBytes": context_bytes[q["consumerId"]][treatment],
            "providerRequestBytes": len(body),
            "requestTokenUpperBound": adapter.request_token_upper_bound(request),
            "providerRequestDigest": adapter.provider_request_digest(request),
        }
        started = time.monotonic()
        try:
            result = adapter.invoke(request)
            row["latencyMs"] = round((time.monotonic() - started) * 1000, 3)
            row["status"] = "completed"
            row["modelId"] = result.model_id
            row["rawResponseDigest"] = result.raw_response_digest
            row["usage"] = result.usage
            row["toolCallCount"] = len(result.tool_calls)
            answer = None
            if len(result.tool_calls) == 1 and result.tool_calls[0].name == "submit_answer":
                raw_answer = result.tool_calls[0].arguments.get("answer")
                if raw_answer in {"A", "B", "C", "D"}:
                    answer = raw_answer
            row["answer"] = answer
            row["correct"] = answer == q["correct"]
            row["critical"] = q["id"] in CRITICAL
            row["currentnessQuestion"] = q["id"] in CURRENTNESS
            row["nextActionQuestion"] = q["id"] in NEXT_ACTION
        except Exception as error:
            row["latencyMs"] = round((time.monotonic() - started) * 1000, 3)
            row["status"] = "provider_error"
            row["errorType"] = type(error).__name__
            row["error"] = str(error)[:1000]
        trials.append(row)
        output.write_text(json.dumps({
            "schemaVersion": 1,
            "kind": "ordivon.agent-native-cognitive-environment-f7-live-ab-result-r1",
            "corpusSha256": EXPECTED_CORPUS_SHA256,
            "providerModel": settings.model,
            "status": "in_progress",
            "trials": trials,
        }, indent=2, sort_keys=True) + "\n")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.agent-native-cognitive-environment-f7-live-ab-result-r1",
        "corpusSha256": EXPECTED_CORPUS_SHA256,
        "providerModel": settings.model,
        "status": "completed",
        "contextBytes": context_bytes,
        "trials": trials,
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def summarize(result: dict[str, Any]) -> dict[str, Any]:
    rows = result["trials"]
    treatments: dict[str, Any] = {}
    for treatment in ("A", "B", "C"):
        selected = [r for r in rows if r["treatment"] == treatment]
        completed = [r for r in selected if r["status"] == "completed"]
        def accuracy(subset):
            if not subset:
                return None
            return round(sum(bool(r.get("correct")) for r in subset) / len(subset), 6)
        def mean_usage(key):
            if not completed:
                return None
            return round(statistics.mean(r["usage"].get(key, 0) for r in completed), 3)
        critical_completed = [r for r in completed if r.get("critical")]
        currentness_completed = [r for r in completed if r.get("currentnessQuestion")]
        action_completed = [r for r in completed if r.get("nextActionQuestion")]
        treatments[treatment] = {
            "trials": len(selected),
            "completed": len(completed),
            "providerErrors": len(selected)-len(completed),
            "accuracy": accuracy(completed),
            "criticalCompleted": len(critical_completed),
            "criticalAccuracy": accuracy(critical_completed),
            "currentnessAccuracy": accuracy(currentness_completed),
            "nextActionAccuracy": accuracy(action_completed),
            "meanPromptTokens": mean_usage("prompt_tokens"),
            "meanCompletionTokens": mean_usage("completion_tokens"),
            "meanTotalTokens": mean_usage("total_tokens"),
            "meanProviderRequestBytes": None if not completed else round(statistics.mean(r["providerRequestBytes"] for r in completed),3),
            "meanContextBytes": None if not completed else round(statistics.mean(r["contextBytes"] for r in completed),3),
            "medianLatencyMs": None if not completed else round(statistics.median(r["latencyMs"] for r in completed),3),
            "invalidAnswerCount": sum(r.get("answer") is None for r in completed),
        }
    completed_total=sum(v["completed"] for v in treatments.values())
    a=treatments["A"]; b=treatments["B"]; c=treatments["C"]
    semantics=(
        completed_total >= 15
        and c["completed"] >= 5
        and c["accuracy"] is not None and c["accuracy"] >= 5/6
        and a["accuracy"] is not None and c["accuracy"] >= a["accuracy"] - 1/6
        and c["criticalCompleted"] >= 2
        and c["criticalAccuracy"] == 1.0
        and c["invalidAnswerCount"] == 0
    )
    efficiency=(
        semantics
        and c["meanPromptTokens"] is not None
        and a["meanPromptTokens"] is not None
        and b["meanPromptTokens"] is not None
        and c["meanPromptTokens"] < a["meanPromptTokens"]
        and c["meanPromptTokens"] < b["meanPromptTokens"]
    )
    if completed_total < 15:
        classification="incomplete"
    elif efficiency:
        classification="positive_compact_nonregression"
    elif semantics:
        classification="semantic_nonregression_without_efficiency_gain"
    else:
        classification="negative_or_insufficient"
    return {
        "classification": classification,
        "completedCalls": completed_total,
        "thresholds": {
            "totalCompletedMin": 15,
            "cCompletedMin": 5,
            "cAccuracyMin": round(5/6,6),
            "cMayTrailAByAtMostCases": 1,
            "cCriticalCompletedMin": 2,
            "cCriticalAccuracyRequired": 1.0,
            "cMeanPromptTokensMustBeLessThanAAndBForPositiveCompactClaim": True,
        },
        "treatments": treatments,
        "nonClaims": [
            "two Works do not establish cross-domain or cross-model generality",
            "owner endpoint discovery was supplied, not tested",
            "no effect was dispatched",
        ],
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--validate-only",action="store_true")
    parser.add_argument("--output",type=Path,default=ROOT/"docs/architecture/evidence/agent-native-cognitive-environment-f7-live-ab-result-r1.json")
    args=parser.parse_args()
    if args.validate_only:
        print(json.dumps(validate_only(),indent=2,sort_keys=True))
        return 0
    result=run_live(args.output)
    summary=summarize(result)
    summary_path=args.output.with_name("agent-native-cognitive-environment-f7-live-ab-summary-r1.json")
    summary_path.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
