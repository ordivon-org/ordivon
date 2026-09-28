from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
RUNNER = HERE.with_name("run_factorial_pilot_r1.py")
EXPERIMENT_ID = "experiment:experimental-fabric-model-harness-pilot-r1-20260928"
RECOVERY_REASON = "POST_LIVE_CANONICAL_FLOAT_SERIALIZATION_FAILURE"


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_runner():
    spec = importlib.util.spec_from_file_location("oef_pilot_r1_frozen", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen pilot runner: {RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ratio(value: Fraction | int) -> dict[str, int]:
    exact = value if isinstance(value, Fraction) else Fraction(value)
    return {"numerator": exact.numerator, "denominator": exact.denominator}


def mean(values: list[int]) -> Fraction | None:
    return None if not values else Fraction(sum(values), len(values))


def serialize_fraction(value: Fraction | None) -> dict[str, int] | None:
    return None if value is None else ratio(value)


def assert_no_float(value: Any, *, path: str = "$") -> None:
    if isinstance(value, float):
        raise RuntimeError(f"floating-point value forbidden in recovered artifact at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert_no_float(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_float(item, path=f"{path}[{index}]")


def verify_frozen_evidence(output_dir: Path, pilot):
    prereg = json.loads((output_dir / "preregistration.json").read_text(encoding="utf-8"))
    runner_digest = file_digest(RUNNER)
    if prereg["pilotRunnerBinding"]["digest"] != runner_digest:
        raise RuntimeError(
            "frozen runner bytes no longer match preregistration; recovery refuses method drift"
        )
    expected_prereg = pilot.canonical_digest(
        {key: value for key, value in prereg.items() if key != "preregistrationDigest"}
    )
    if prereg["preregistrationDigest"] != expected_prereg:
        raise RuntimeError("preregistration digest invalid")

    journal = read_jsonl(output_dir / "journal.jsonl")
    started = {row["trialId"] for row in journal if row.get("event") == "trial_started"}
    completed = {row["trialId"] for row in journal if row.get("event") == "trial_completed"}
    if len(started) != 12 or len(completed) != 12 or started != completed:
        raise RuntimeError(
            "recovery requires 12 completed trials and zero uncertain starts: "
            f"started={len(started)} completed={len(completed)} "
            f"uncertain={sorted(started - completed)}"
        )

    raw = json.loads((output_dir / "results.json").read_text(encoding="utf-8"))
    expected_result_set = pilot.canonical_digest(
        {key: value for key, value in raw.items() if key != "resultSetDigest"}
    )
    if raw["resultSetDigest"] != expected_result_set:
        raise RuntimeError("result set digest invalid")
    if raw["preregistrationDigest"] != prereg["preregistrationDigest"]:
        raise RuntimeError("result set is not bound to the frozen preregistration")
    records = sorted(raw["records"], key=lambda row: row["ordinal"])
    if len(records) != 12 or {row["trialId"] for row in records} != started:
        raise RuntimeError("result records do not match completed journal trials")
    for record in records:
        expected = pilot.canonical_digest(
            {key: value for key, value in record.items() if key != "recordDigest"}
        )
        if record["recordDigest"] != expected:
            raise RuntimeError(f"trial record digest invalid: {record['trialId']}")

    episodes = read_jsonl(output_dir / "episodes.jsonl")
    if len(episodes) != 12:
        raise RuntimeError(f"expected 12 episode projections, found {len(episodes)}")
    for episode in episodes:
        pilot.validate("experimental-episode-binding-r1.schema.json", episode)
        expected = pilot.canonical_digest(
            {key: value for key, value in episode.items() if key != "projectionDigest"}
        )
        if episode["projectionDigest"] != expected:
            raise RuntimeError(f"episode projection digest invalid: {episode['episodeId']}")
    episodes_by_trial = {
        episode["episodeId"].removeprefix("episode:"): episode for episode in episodes
    }

    evaluations = read_jsonl(output_dir / "evaluations.jsonl")
    if len(evaluations) != 72:
        raise RuntimeError(f"expected 72 evaluation records, found {len(evaluations)}")
    for evaluation in evaluations:
        pilot.validate("experimental-evaluation-record-r1.schema.json", evaluation)
        expected = pilot.canonical_digest(
            {key: value for key, value in evaluation.items() if key != "recordDigest"}
        )
        if evaluation["recordDigest"] != expected:
            raise RuntimeError(f"evaluation digest invalid: {evaluation['evaluationId']}")

    return prereg, raw, records, episodes_by_trial, evaluations


def effect_analysis_exact(records: list[dict[str, Any]], pilot) -> dict[str, Any]:
    def result_rows(model: str | None = None, codec: str | None = None) -> list[dict[str, Any]]:
        rows = records
        if model is not None:
            rows = [row for row in rows if row["model"] == model]
        if codec is not None:
            rows = [row for row in rows if row["codec"] == codec]
        return rows

    exact_cells: dict[str, dict[str, Fraction | None]] = {}
    cells: dict[str, Any] = {}
    for model in pilot.MODELS:
        for codec in pilot.CODECS:
            subset = result_rows(model, codec)
            hidden = [1 if row["result"].get("hiddenPassed") else 0 for row in subset]
            completed = [1 if row["result"].get("candidateCompleted") else 0 for row in subset]
            tokens = [
                int(row["result"]["usage"]["totalTokens"])
                for row in subset
                if isinstance(row["result"].get("usage"), dict)
                and isinstance(row["result"]["usage"].get("totalTokens"), int)
            ]
            tool_calls = [
                int(row["result"]["toolCalls"])
                for row in subset
                if isinstance(row["result"].get("toolCalls"), int)
            ]
            elapsed = [
                int(row["result"]["elapsedMs"])
                for row in subset
                if isinstance(row["result"].get("elapsedMs"), int)
            ]
            exact = {
                "hiddenPassRate": mean(hidden),
                "candidateCompletionRate": mean(completed),
                "meanTotalTokens": mean(tokens),
                "meanToolCalls": mean(tool_calls),
                "meanElapsedMs": mean(elapsed),
            }
            key = f"{model}|{codec}"
            exact_cells[key] = exact
            cells[key] = {
                "runs": len(subset),
                **{name: serialize_fraction(value) for name, value in exact.items()},
                "exceptions": sum(row["result"].get("status") == "exception" for row in subset),
            }

    def avg_rate(rows: list[dict[str, Any]], key: str) -> Fraction | None:
        return mean([1 if row["result"].get(key) else 0 for row in rows])

    flash_rate = avg_rate(result_rows(pilot.MODELS[0]), "hiddenPassed")
    v4_rate = avg_rate(result_rows(pilot.MODELS[1]), "hiddenPassed")
    exact_rate = avg_rate(result_rows(codec=pilot.CODECS[0]), "hiddenPassed")
    anchored_rate = avg_rate(result_rows(codec=pilot.CODECS[1]), "hiddenPassed")

    def hidden_cell(model: str, codec: str) -> Fraction | None:
        return exact_cells[f"{model}|{codec}"]["hiddenPassRate"]

    interaction: Fraction | None = None
    hidden_cells = [hidden_cell(model, codec) for model in pilot.MODELS for codec in pilot.CODECS]
    if all(value is not None for value in hidden_cells):
        v4_exact = hidden_cell(pilot.MODELS[1], pilot.CODECS[0])
        v4_anchored = hidden_cell(pilot.MODELS[1], pilot.CODECS[1])
        flash_exact = hidden_cell(pilot.MODELS[0], pilot.CODECS[0])
        flash_anchored = hidden_cell(pilot.MODELS[0], pilot.CODECS[1])
        assert None not in (v4_exact, v4_anchored, flash_exact, flash_anchored)
        interaction = (v4_exact - v4_anchored) - (flash_exact - flash_anchored)

    by_task = []
    for task in pilot.TASK_IDS:
        rows = [row for row in records if row["taskId"] == task]
        by_task.append(
            {
                "taskId": task,
                "rows": [
                    {
                        "model": row["model"],
                        "codec": row["codec"],
                        "hiddenPassed": bool(row["result"].get("hiddenPassed")),
                        "candidateCompleted": bool(row["result"].get("candidateCompleted")),
                        "status": row["result"].get("status"),
                    }
                    for row in sorted(rows, key=lambda item: (item["model"], item["codec"]))
                ],
            }
        )

    model_effect = None if flash_rate is None or v4_rate is None else v4_rate - flash_rate
    codec_effect = None if exact_rate is None or anchored_rate is None else exact_rate - anchored_rate
    analysis = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-factorial-pilot-analysis",
        "experimentId": EXPERIMENT_ID,
        "analysisClass": "pilot-descriptive-blocked-factorial-exact-rational-recovery",
        "numericRepresentation": "exact-rational-numerator-denominator",
        "cells": cells,
        "primaryEffects": {
            "modelHiddenPassDifference": serialize_fraction(model_effect),
            "codecHiddenPassDifferenceExactMinusAnchored": serialize_fraction(codec_effect),
            "modelByCodecHiddenPassInteraction": serialize_fraction(interaction),
        },
        "taskBlocks": by_task,
        "recovery": {
            "reasonCode": RECOVERY_REASON,
            "providerDispatchPermitted": False,
            "sourceEvidencePolicy": "frozen-completed-trials-only",
        },
        "nonClaims": [
            "No p-value, ranking, or broad capability claim is admitted from this 12-run pilot.",
            "Provider-owned stochasticity and temporal drift remain nuisance variation despite randomized order.",
            "Recovery changes only analysis representation after all live trials completed; it does not alter preregistration, trial records, Episodes, or EvaluationRecords.",
        ],
    }
    assert_no_float(analysis)
    analysis["analysisDigest"] = pilot.canonical_digest(analysis)
    return analysis


def recover(output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    pilot = load_runner()
    prereg, raw, records, episodes, evaluations = verify_frozen_evidence(output_dir, pilot)

    analysis = effect_analysis_exact(records, pilot)
    pilot.json_write(output_dir / "analysis.json", analysis)

    forks = pilot.make_forks(records, episodes, prereg)
    assert_no_float(forks)
    pilot.json_write(output_dir / "forks.json", forks)

    acceptance = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-factorial-pilot-acceptance",
        "experimentId": EXPERIMENT_ID,
        "gitRevision": prereg["gitRevision"],
        "preregistrationDigest": prereg["preregistrationDigest"],
        "resultSetDigest": raw["resultSetDigest"],
        "analysisDigest": analysis["analysisDigest"],
        "plannedTrials": len(prereg["schedule"]["trials"]),
        "observedTrials": len(records),
        "exceptionTrials": sum(row["result"].get("status") == "exception" for row in records),
        "episodeCount": len(episodes),
        "evaluationCount": len(evaluations),
        "declaredForkStanding": forks["declared"]["assessment"]["standing"],
        "contaminatedForkStanding": forks["contaminated"]["assessment"]["standing"],
        "standing": "PASS_PILOT_MECHANICS" if len(records) == 12 else "FAIL_INCOMPLETE_CAMPAIGN",
        "recoveryReasonCode": RECOVERY_REASON,
        "providerDispatchesDuringRecovery": 0,
        "nonClaims": [
            "PASS_PILOT_MECHANICS is protocol/execution acceptance, not a model or Harness winner declaration.",
            "Any observed treatment differences remain pilot-scale descriptive evidence.",
            "Recovery consumed only frozen completed trial evidence and performed no Provider dispatch.",
        ],
    }
    assert_no_float(acceptance)
    acceptance["acceptanceDigest"] = pilot.canonical_digest(acceptance)
    pilot.json_write(output_dir / "acceptance.json", acceptance)

    repo_root = HERE.parents[3]
    relative_tool = str(HERE.relative_to(repo_root))
    tool_revision = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", relative_tool],
        cwd=repo_root,
        text=True,
    ).strip()
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-factorial-finalization-recovery",
        "experimentId": EXPERIMENT_ID,
        "reasonCode": RECOVERY_REASON,
        "recoveryToolRevision": tool_revision,
        "frozenRunnerBinding": prereg["pilotRunnerBinding"],
        "recoveryToolBinding": {
            "objectId": relative_tool,
            "digest": file_digest(HERE),
        },
        "inputs": {
            "preregistrationDigest": prereg["preregistrationDigest"],
            "resultSetDigest": raw["resultSetDigest"],
            "journalFileDigest": file_digest(output_dir / "journal.jsonl"),
            "episodesFileDigest": file_digest(output_dir / "episodes.jsonl"),
            "evaluationsFileDigest": file_digest(output_dir / "evaluations.jsonl"),
        },
        "outputs": {
            "analysisDigest": analysis["analysisDigest"],
            "forkSetDigest": pilot.canonical_digest(forks),
            "acceptanceDigest": acceptance["acceptanceDigest"],
        },
        "providerDispatches": 0,
        "standing": "PASS_RECOVERED_FINALIZATION",
        "nonClaims": [
            "Recovery receipt does not replace the frozen preregistration or natural-owner live evidence.",
            "Recovery makes no general model or Harness superiority claim.",
        ],
    }
    assert_no_float(receipt)
    receipt["receiptDigest"] = pilot.canonical_digest(receipt)
    pilot.json_write(output_dir / "recovery.json", receipt)
    return {"analysis": analysis, "forks": forks, "acceptance": acceptance, "recovery": receipt}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = recover(args.output_dir)
    print("RECOVERY_RECEIPT=" + json.dumps(result["recovery"], sort_keys=True), flush=True)
    print("FINAL_ACCEPTANCE=" + json.dumps(result["acceptance"], sort_keys=True), flush=True)
    return 0 if result["acceptance"]["standing"] == "PASS_PILOT_MECHANICS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
