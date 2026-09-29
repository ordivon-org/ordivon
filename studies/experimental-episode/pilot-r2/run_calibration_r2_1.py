from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
BASE_RUNNER_PATH = HERE.with_name("run_calibration_r2.py")
DESIGN_PATH = HERE.with_name("design_r2_1.py")
ANALYSIS_PATH = HERE.with_name("analysis_r2_1.py")
TASK_BLOCK_PATH = HERE.with_name("task_block_runner_r2_1.py")
CLAIM_SPEC_PATH = HERE.parent / "evidence" / "design" / "claim-spec-r2_1.json"
OLD_PREREG_PATH = HERE.parent / "evidence" / "calibration" / "20260929-r1" / "preregistration.json"
EXPERIMENT_ID = "experiment:experimental-fabric-model-harness-pilot-r2-20260929"
CALIBRATION_ID = "calibration:experimental-fabric-r2:20260929-r2"
MAX_TOTAL_TOKENS = 64_000


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_base_runner():
    return load_module(BASE_RUNNER_PATH, "experimental_fabric_r2_base_calibration_runner")


def load_design():
    return load_module(DESIGN_PATH, "experimental_fabric_r2_successor_design")


def load_analysis():
    return load_module(ANALYSIS_PATH, "experimental_fabric_r2_successor_analysis")


def load_task_block():
    return load_module(TASK_BLOCK_PATH, "experimental_fabric_r2_task_block_runner")


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def verify_claim_spec(base) -> dict[str, Any]:
    value = json.loads(CLAIM_SPEC_PATH.read_text(encoding="utf-8"))
    if value.get("kind") != "ordivon.experimental-claim-specification" or value.get("designRevision") != "r2.1":
        raise RuntimeError("R2.1 claim specification identity differs")
    embedded = value.get("claimSpecDigest")
    base_value = {key: item for key, item in value.items() if key != "claimSpecDigest"}
    if embedded != base.canonical_digest(base_value):
        raise RuntimeError("R2.1 claim specification digest invalid")
    return value


def verify_old_prereg(base) -> dict[str, Any]:
    value = json.loads(OLD_PREREG_PATH.read_text(encoding="utf-8"))
    embedded = value.get("preregistrationDigest")
    if embedded != base.canonical_digest({key: item for key, item in value.items() if key != "preregistrationDigest"}):
        raise RuntimeError("superseded calibration-r1 preregistration digest invalid")
    return value


def build_preregistration(*, source_revision: str | None = None) -> dict[str, Any]:
    base = load_base_runner()
    design = load_design()
    bundle = base.verify_bundle()
    base.verify_preflight()
    claim_spec = verify_claim_spec(base)
    old_prereg = verify_old_prereg(base)
    schedule = design.compile_balanced_calibration_schedule(bundle["manifest"])
    current_revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    git_revision = current_revision if source_revision is None else source_revision
    if source_revision is not None:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_revision, current_revision],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-preregistration",
        "calibrationId": CALIBRATION_ID,
        "experimentId": EXPERIMENT_ID,
        "designRevision": "r2.1",
        "gitRevision": git_revision,
        "supersedesPreEffect": {
            "path": str(OLD_PREREG_PATH.relative_to(ROOT)),
            "preregistrationDigest": old_prereg["preregistrationDigest"],
            "reason": "No calibration-r1 live effect existed before the successor was frozen; r1 remains immutable historical evidence.",
        },
        "claimSpecBinding": {
            "path": str(CLAIM_SPEC_PATH.relative_to(ROOT)),
            "fileDigest": file_digest(CLAIM_SPEC_PATH),
            "claimSpecDigest": claim_spec["claimSpecDigest"],
        },
        "runnerBinding": {"path": str(HERE.relative_to(ROOT)), "digest": file_digest(HERE)},
        "successorDesignBinding": {"path": str(DESIGN_PATH.relative_to(ROOT)), "digest": file_digest(DESIGN_PATH)},
        "successorAnalysisBinding": {"path": str(ANALYSIS_PATH.relative_to(ROOT)), "digest": file_digest(ANALYSIS_PATH)},
        "taskBlockRunnerBinding": {"path": str(TASK_BLOCK_PATH.relative_to(ROOT)), "digest": file_digest(TASK_BLOCK_PATH)},
        "liveHarnessBinding": old_prereg["liveHarnessBinding"],
        "taskBundleBinding": old_prereg["taskBundleBinding"],
        "providerIdentityPreflightBinding": old_prereg["providerIdentityPreflightBinding"],
        "schedule": schedule,
        "resourceEnvelope": old_prereg["resourceEnvelope"],
        "fullGate": old_prereg["gate"],
        "decisionFrontier": {
            "atomicObservationUnit": "complete-four-cell-task-block",
            "algorithm": "enumerate-all-legal-remaining-block-success-counts-v1",
            "semantics": "stop only when every legal completion yields the same original full 24-cell gate standing",
            "analysisDigest": file_digest(ANALYSIS_PATH),
        },
        "stopRules": [
            "A task block is atomic for calibration decision checks; never stop within its four Model×Harness cells for difficulty-gate reasons.",
            "After each durable complete task block, evaluate the decision frontier; DECISIVE_PASS or DECISIVE_REJECT stops before any later block.",
            "An unmatched trial_started requires exact reconciliation before any further Provider dispatch.",
            "Provider effective-identity drift or a Harness exception is durably recorded and stops before the next Provider dispatch.",
            "Calibration outcomes never enter the inferential treatment-effect sample.",
        ],
        "nonClaims": [
            "The decision frontier is a semantic short-circuit of the frozen full difficulty gate, not a treatment-effect interim analysis.",
            "A calibration PASS does not establish power, treatment efficacy, model superiority, or Harness superiority.",
        ],
    }
    value["preregistrationDigest"] = base.canonical_digest(value)
    return value


def write_or_validate_preregistration(output_dir: Path, prereg: dict[str, Any]) -> None:
    task_block = load_task_block()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "preregistration.json"
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
        if current != prereg:
            raise RuntimeError("stored R2.1 calibration preregistration differs from bound method")
        return
    if any(output_dir.iterdir()):
        raise RuntimeError("non-empty R2.1 calibration evidence directory lacks preregistration")
    task_block.json_write(path, prereg)
    task_block.json_write(output_dir / "schedule.json", prereg["schedule"])


def resolve_preregistration(output_dir: Path) -> dict[str, Any]:
    base = load_base_runner()
    path = output_dir / "preregistration.json"
    if not path.exists():
        value = build_preregistration()
        write_or_validate_preregistration(output_dir, value)
        return value
    current = json.loads(path.read_text(encoding="utf-8"))
    expected_digest = base.canonical_digest({key: item for key, item in current.items() if key != "preregistrationDigest"})
    if current.get("preregistrationDigest") != expected_digest:
        raise RuntimeError("stored R2.1 calibration preregistration digest invalid")
    source_revision = current.get("gitRevision")
    if not isinstance(source_revision, str) or not source_revision:
        raise RuntimeError("stored R2.1 calibration preregistration lacks Git revision")
    expected = build_preregistration(source_revision=source_revision)
    if current != expected:
        raise RuntimeError("stored R2.1 calibration preregistration no longer matches bound code/evidence")
    return current


def execute_campaign(output_dir: Path, prereg: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base = load_base_runner()
    analysis = load_analysis()
    task_block = load_task_block()
    journal = output_dir / "journal.jsonl"
    # Critical fence: no Provider secret is loaded while an effect is uncertain.
    task_block.assert_no_uncertain_started(journal)
    bundle = base.verify_bundle()
    preflight = base.verify_preflight()
    payload_by_id = base.task_payloads(bundle)
    live = base.load_live_runner()
    settings_base = base.DeepSeekSettings.from_secret_file(
        timeout_seconds=60.0,
        max_response_bytes=2_097_152,
        max_output_tokens=2048,
    )
    all_records: list[dict[str, Any]] = []

    def continuation_check(record: dict[str, Any]) -> None:
        if record["result"].get("status") != "completed":
            raise RuntimeError(f"calibration trial ended with Harness exception; stop campaign: {record['trialId']}")
        if record["providerIdentity"]["standing"] != "PASS_EFFECTIVE_IDENTITY":
            raise RuntimeError(f"Provider identity drift detected; stop campaign: {record['trialId']}")

    for block in prereg["schedule"]["blocks"]:
        block_trials = [row for row in prereg["schedule"]["trials"] if row["blockId"] == block["blockId"]]

        def execute_one(trial: dict[str, Any]) -> dict[str, Any]:
            payload = payload_by_id[trial["taskId"]]
            settings = replace(settings_base, model=trial["model"])
            with tempfile.TemporaryDirectory(prefix="ordivon-r2-1-calibration-") as directory:
                task_spec = base.materialize_task(payload, live, Path(directory))
                result = live.run_one(
                    trial["codec"],
                    trial["ordinal"],
                    settings,
                    task_spec=task_spec,
                    max_total_tokens=MAX_TOTAL_TOKENS,
                )
            identity = base.assess_provider_identity(result, trial["model"], preflight)
            record = {
                "schemaVersion": 1,
                "kind": "ordivon.experimental-calibration-live-trial",
                "calibrationId": CALIBRATION_ID,
                "experimentId": EXPERIMENT_ID,
                "designRevision": "r2.1",
                **trial,
                "taskDigest": payload["definition"]["taskDigest"],
                "qaDigest": payload["qa"]["qaDigest"],
                "provider": "deepseek",
                "providerRandomness": "provider-owned",
                "providerIdentity": identity,
                "hiddenPassed": bool(result.get("hiddenPassed")),
                "result": result,
            }
            record["recordDigest"] = base.canonical_digest(record)
            print(
                json.dumps(
                    {
                        "trial": trial["trialId"],
                        "block": trial["blockId"],
                        "task": trial["taskId"],
                        "family": trial["taskFamily"],
                        "model": trial["model"],
                        "codec": trial["codec"],
                        "status": result.get("status"),
                        "hiddenPassed": result.get("hiddenPassed"),
                        "identity": identity["standing"],
                        "totalTokens": (result.get("usage") or {}).get("totalTokens") if isinstance(result.get("usage"), dict) else None,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            return record

        block_records = task_block.execute_task_block(
            output_dir=output_dir,
            trials=block_trials,
            execute_one=execute_one,
            continuation_check=continuation_check,
        )
        all_records.extend(block_records)
        certificate = analysis.decision_frontier_certificate(all_records, prereg["schedule"])
        task_block.json_write(
            output_dir / "frontier" / f"after-block-{block['blockOrdinal']:02d}.json",
            certificate,
        )
        print("CALIBRATION_FRONTIER=" + json.dumps(certificate, sort_keys=True), flush=True)
        if certificate["standing"] != "UNDECIDED":
            return all_records, certificate
    certificate = analysis.decision_frontier_certificate(all_records, prereg["schedule"])
    if certificate["standing"] == "UNDECIDED":
        raise RuntimeError("complete calibration schedule unexpectedly remains undecided")
    return all_records, certificate


def finalize(
    output_dir: Path,
    prereg: dict[str, Any],
    records: list[dict[str, Any]],
    certificate: dict[str, Any],
) -> dict[str, Any]:
    base = load_base_runner()
    task_block = load_task_block()
    if certificate["standing"] == "UNDECIDED":
        raise RuntimeError("cannot finalize an undecided calibration frontier")
    observed_ids = {row["trialId"] for row in records}
    all_trial_ids = [row["trialId"] for row in prereg["schedule"]["trials"]]
    result_set = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-result-set",
        "calibrationId": CALIBRATION_ID,
        "experimentId": EXPERIMENT_ID,
        "designRevision": "r2.1",
        "preregistrationDigest": prereg["preregistrationDigest"],
        "observedTrialCount": len(records),
        "unobservedTrialIds": [trial_id for trial_id in all_trial_ids if trial_id not in observed_ids],
        "records": sorted(records, key=lambda row: row["ordinal"]),
    }
    result_set["resultSetDigest"] = base.canonical_digest(result_set)
    task_block.json_write(output_dir / "results.json", result_set)
    full_standing = (
        "PASS_CALIBRATION_DIFFICULTY"
        if certificate["standing"] == "DECISIVE_PASS_CALIBRATION_DIFFICULTY"
        else "REJECT_TASK_BANK_DIFFICULTY"
    )
    gate = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-decision-frontier-gate",
        "calibrationId": CALIBRATION_ID,
        "experimentId": EXPERIMENT_ID,
        "designRevision": "r2.1",
        "standing": full_standing,
        "decisionFrontierCertificate": certificate,
        "preregistrationDigest": prereg["preregistrationDigest"],
        "resultSetDigest": result_set["resultSetDigest"],
        "providerIdentityPreflightDigest": prereg["providerIdentityPreflightBinding"]["preflightDigest"],
        "semanticBridge": "The emitted full-gate standing is licensed only because the certificate proves all legal completions of unobserved complete task blocks have the same original calibration-r1 full-gate standing.",
    }
    gate["calibrationReceiptDigest"] = base.canonical_digest(gate)
    task_block.json_write(output_dir / "gate.json", gate)
    acceptance = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-acceptance",
        "calibrationId": CALIBRATION_ID,
        "experimentId": EXPERIMENT_ID,
        "designRevision": "r2.1",
        "preregistrationDigest": prereg["preregistrationDigest"],
        "resultSetDigest": result_set["resultSetDigest"],
        "gateDigest": gate["calibrationReceiptDigest"],
        "observedTrialCount": len(records),
        "plannedTrialCount": prereg["schedule"]["trialCount"],
        "providerIdentityStanding": "PASS_DISTINCT_EFFECTIVE_IDENTITIES_AND_NO_DRIFT",
        "standing": full_standing,
        "inferentialCampaignAdmitted": full_standing == "PASS_CALIBRATION_DIFFICULTY",
        "nonClaims": [
            "Calibration acceptance is a task-bank difficulty gate only.",
            "Unobserved calibration cells are not imputed; they are unnecessary only because the decision frontier is invariant to every legal completion.",
            "Calibration observations are excluded from R2 inferential treatment-effect estimates.",
        ],
    }
    acceptance["acceptanceDigest"] = base.canonical_digest(acceptance)
    task_block.json_write(output_dir / "acceptance.json", acceptance)
    return acceptance


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preregister-only", action="store_true")
    mode.add_argument("--run-live", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prereg = resolve_preregistration(args.output_dir)
    if args.preregister_only:
        print("CALIBRATION_PREREGISTRATION=" + json.dumps(prereg, sort_keys=True), flush=True)
        return 0
    records, certificate = execute_campaign(args.output_dir, prereg)
    acceptance = finalize(args.output_dir, prereg, records, certificate)
    print("CALIBRATION_ACCEPTANCE=" + json.dumps(acceptance, sort_keys=True), flush=True)
    return 0 if acceptance["standing"] == "PASS_CALIBRATION_DIFFICULTY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
