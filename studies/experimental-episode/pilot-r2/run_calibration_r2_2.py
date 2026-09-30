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
DESIGN_PATH = HERE.with_name("design_r2_2.py")
ANALYSIS_PATH = HERE.with_name("analysis_r2_1.py")
TASK_BLOCK_PATH = HERE.with_name("task_block_runner_r2_1.py")
CLAIM_SPEC_PATH = HERE.parent / "evidence/design/claim-spec-r2_1.json"
CALIBRATION_BUNDLE_PATH = (
    HERE.parent / "evidence/design/r2_2/calibration-task-bank.json"
)
INFERENTIAL_BUNDLE_PATH = (
    HERE.parent / "evidence/design/r2_2/inferential-task-bank.json"
)
REPAIR_SPEC_PATH = HERE.parent / "evidence/design/r2_2/task-bank-repair-spec.json"
PRIOR_ACCEPTANCE_PATH = HERE.parent / "evidence/calibration/20260929-r2/acceptance.json"
R21_PREREG_PATH = HERE.parent / "evidence/calibration/20260929-r2/preregistration.json"
EXPERIMENT_ID = "experiment:experimental-fabric-model-harness-pilot-r2-20260929"
CALIBRATION_ID = "calibration:experimental-fabric-r2:20260930-r3"
DESIGN_REVISION = "r2.2"
MAX_TOTAL_TOKENS = 64_000


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_base_runner():
    return load_module(
        BASE_RUNNER_PATH, "experimental_fabric_r2_base_calibration_runner_r22"
    )


def load_design():
    return load_module(DESIGN_PATH, "experimental_fabric_r22_design")


def load_analysis():
    return load_module(ANALYSIS_PATH, "experimental_fabric_r21_analysis_shared")


def load_task_block():
    return load_module(TASK_BLOCK_PATH, "experimental_fabric_r21_task_block_shared")


def sha256_bytes(v: bytes) -> str:
    return "sha256:" + hashlib.sha256(v).hexdigest()


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _verify_canonical_document(path: Path, digest_field: str, base) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    embedded = value.get(digest_field)
    if embedded != base.canonical_digest(
        {k: v for k, v in value.items() if k != digest_field}
    ):
        raise RuntimeError(f"canonical digest invalid: {path}")
    return value


def verify_bundle(path: Path, cohort: str, base) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        value.get("kind") != "ordivon.experimental-task-bank-bundle"
        or value.get("cohort") != cohort
        or value.get("generatorRevision") != "r2.2"
    ):
        raise RuntimeError(f"R2.2 {cohort} bundle identity differs")
    if value.get("bundleDigest") != base.canonical_digest(
        {k: v for k, v in value.items() if k != "bundleDigest"}
    ):
        raise RuntimeError(f"R2.2 {cohort} bundle digest invalid")
    manifest = value.get("manifest")
    expected_count = 6 if cohort == "calibration" else 24
    if (
        not isinstance(manifest, dict)
        or manifest.get("taskCount") != expected_count
        or len(manifest.get("tasks", [])) != expected_count
    ):
        raise RuntimeError(f"R2.2 {cohort} manifest count differs")
    if manifest.get("manifestDigest") != base.canonical_digest(
        {k: v for k, v in manifest.items() if k != "manifestDigest"}
    ):
        raise RuntimeError(f"R2.2 {cohort} manifest digest invalid")
    by_id = {row["taskId"]: row for row in manifest["tasks"]}
    for payload_row in value.get("tasks", []):
        definition = payload_row.get("definition")
        qa = payload_row.get("qa")
        tid = definition.get("taskId") if isinstance(definition, dict) else None
        row = by_id.get(tid)
        if (
            not isinstance(definition, dict)
            or not isinstance(qa, dict)
            or row is None
            or row.get("qaStanding") != "PASS"
            or qa.get("standing") != "PASS_TASK_QA"
        ):
            raise RuntimeError(f"R2.2 task QA not PASS: {tid}")
        if definition.get("taskDigest") != base.canonical_digest(
            {k: v for k, v in definition.items() if k != "taskDigest"}
        ):
            raise RuntimeError(f"R2.2 task digest invalid: {tid}")
        if qa.get("qaDigest") != base.canonical_digest(
            {k: v for k, v in qa.items() if k != "qaDigest"}
        ):
            raise RuntimeError(f"R2.2 QA digest invalid: {tid}")
        if (
            row.get("taskDigest") != definition["taskDigest"]
            or row.get("qaDigest") != qa["qaDigest"]
        ):
            raise RuntimeError(f"R2.2 manifest/payload binding differs: {tid}")
    return value


def verify_claim_spec(base):
    return _verify_canonical_document(CLAIM_SPEC_PATH, "claimSpecDigest", base)


def verify_prior_rejection(base):
    value = _verify_canonical_document(PRIOR_ACCEPTANCE_PATH, "acceptanceDigest", base)
    if (
        value.get("standing") != "REJECT_TASK_BANK_DIFFICULTY"
        or value.get("inferentialCampaignAdmitted") is not False
    ):
        raise RuntimeError("R2.1 predecessor is not a frozen non-admitting rejection")
    return value


def verify_repair_spec(base):
    value = _verify_canonical_document(REPAIR_SPEC_PATH, "repairSpecDigest", base)
    prior = verify_prior_rejection(base)
    if value.get("trigger", {}).get("acceptanceDigest") != prior["acceptanceDigest"]:
        raise RuntimeError("repair spec does not bind predecessor rejection")
    return value


def build_preregistration(*, source_revision: str | None = None) -> dict[str, Any]:
    base = load_base_runner()
    design = load_design()
    claim = verify_claim_spec(base)
    prior = verify_prior_rejection(base)
    repair = verify_repair_spec(base)
    cal = verify_bundle(CALIBRATION_BUNDLE_PATH, "calibration", base)
    inf = verify_bundle(INFERENTIAL_BUNDLE_PATH, "inferential", base)
    preflight = base.verify_preflight()
    r21 = _verify_canonical_document(R21_PREREG_PATH, "preregistrationDigest", base)
    schedule = design.compile_balanced_calibration_schedule(cal["manifest"])
    inferential_schedule = design.compile_balanced_inferential_schedule(
        inf["manifest"], preflight
    )
    current = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    git_revision = current if source_revision is None else source_revision
    if source_revision is not None:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_revision, current],
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
        "designRevision": DESIGN_REVISION,
        "gitRevision": git_revision,
        "supersedesAfterRejectedCalibration": {
            "path": str(PRIOR_ACCEPTANCE_PATH.relative_to(ROOT)),
            "acceptanceDigest": prior["acceptanceDigest"],
            "standing": prior["standing"],
            "reason": "R2.1 live calibration exceeded the frozen ceiling; R2.2 repairs only the task-bank difficulty surface while preserving gate and treatment contracts.",
        },
        "claimSpecBinding": {
            "path": str(CLAIM_SPEC_PATH.relative_to(ROOT)),
            "fileDigest": file_digest(CLAIM_SPEC_PATH),
            "claimSpecDigest": claim["claimSpecDigest"],
        },
        "taskBankRepairSpecBinding": {
            "path": str(REPAIR_SPEC_PATH.relative_to(ROOT)),
            "fileDigest": file_digest(REPAIR_SPEC_PATH),
            "repairSpecDigest": repair["repairSpecDigest"],
        },
        "runnerBinding": {
            "path": str(HERE.relative_to(ROOT)),
            "digest": file_digest(HERE),
        },
        "baseRunnerHelperBinding": {
            "path": str(BASE_RUNNER_PATH.relative_to(ROOT)),
            "digest": file_digest(BASE_RUNNER_PATH),
        },
        "successorDesignBinding": {
            "path": str(DESIGN_PATH.relative_to(ROOT)),
            "digest": file_digest(DESIGN_PATH),
        },
        "sharedAnalysisBinding": {
            "path": str(ANALYSIS_PATH.relative_to(ROOT)),
            "digest": file_digest(ANALYSIS_PATH),
        },
        "sharedTaskBlockRunnerBinding": {
            "path": str(TASK_BLOCK_PATH.relative_to(ROOT)),
            "digest": file_digest(TASK_BLOCK_PATH),
        },
        "liveHarnessBinding": r21["liveHarnessBinding"],
        "providerIdentityPreflightBinding": r21["providerIdentityPreflightBinding"],
        "taskBundleBinding": {
            "path": str(CALIBRATION_BUNDLE_PATH.relative_to(ROOT)),
            "fileDigest": file_digest(CALIBRATION_BUNDLE_PATH),
            "bundleDigest": cal["bundleDigest"],
            "manifestDigest": cal["manifest"]["manifestDigest"],
        },
        "inferentialTaskBundleBinding": {
            "path": str(INFERENTIAL_BUNDLE_PATH.relative_to(ROOT)),
            "fileDigest": file_digest(INFERENTIAL_BUNDLE_PATH),
            "bundleDigest": inf["bundleDigest"],
            "manifestDigest": inf["manifest"]["manifestDigest"],
        },
        "schedule": schedule,
        "plannedInferentialSchedule": inferential_schedule,
        "resourceEnvelope": r21["resourceEnvelope"],
        "fullGate": r21["fullGate"],
        "decisionFrontier": {
            "atomicObservationUnit": "complete-four-cell-task-block",
            "algorithm": "enumerate-all-legal-remaining-block-success-counts-v1",
            "semantics": "stop only when every legal completion yields the same frozen full 24-cell gate standing",
            "analysisDigest": file_digest(ANALYSIS_PATH),
        },
        "stopRules": [
            "A task block is atomic for difficulty-gate decisions; never stop within its four Model×Harness cells.",
            "After each durable complete task block, evaluate the decision frontier; a decisive standing stops before any later block.",
            "An unmatched trial_started requires exact reconciliation before any further Provider dispatch.",
            "Provider effective-identity drift or a Harness exception is durably recorded and stops before the next Provider dispatch.",
            "Calibration outcomes never enter the inferential treatment-effect sample.",
        ],
        "nonClaims": [
            "R2.2 changes task difficulty, not the gate, treatment levels, or estimand.",
            "A calibration PASS would admit only the frozen R2.2 inferential schedule; it would not establish treatment efficacy or a general model/Harness ranking.",
        ],
    }
    value["preregistrationDigest"] = base.canonical_digest(value)
    return value


def write_or_validate_preregistration(output_dir: Path, prereg: dict[str, Any]) -> None:
    tb = load_task_block()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "preregistration.json"
    if path.exists():
        if json.loads(path.read_text()) != prereg:
            raise RuntimeError("stored R2.2 preregistration differs from bound method")
        return
    if any(output_dir.iterdir()):
        raise RuntimeError("non-empty R2.2 evidence directory lacks preregistration")
    tb.json_write(path, prereg)
    tb.json_write(output_dir / "schedule.json", prereg["schedule"])
    tb.json_write(
        output_dir / "planned-inferential-schedule.json",
        prereg["plannedInferentialSchedule"],
    )


def resolve_preregistration(output_dir: Path) -> dict[str, Any]:
    base = load_base_runner()
    path = output_dir / "preregistration.json"
    if not path.exists():
        v = build_preregistration()
        write_or_validate_preregistration(output_dir, v)
        return v
    current = json.loads(path.read_text())
    expected = base.canonical_digest(
        {k: v for k, v in current.items() if k != "preregistrationDigest"}
    )
    if current.get("preregistrationDigest") != expected:
        raise RuntimeError("stored R2.2 preregistration digest invalid")
    rev = current.get("gitRevision")
    if not isinstance(rev, str) or not rev:
        raise RuntimeError("stored R2.2 preregistration lacks Git revision")
    rebuilt = build_preregistration(source_revision=rev)
    if rebuilt != current:
        raise RuntimeError(
            "stored R2.2 preregistration no longer matches bound code/evidence"
        )
    return current


def execute_campaign(output_dir: Path, prereg: dict[str, Any]):
    base = load_base_runner()
    analysis = load_analysis()
    tb = load_task_block()
    journal = output_dir / "journal.jsonl"
    tb.assert_no_uncertain_started(journal)
    bundle = verify_bundle(CALIBRATION_BUNDLE_PATH, "calibration", base)
    preflight = base.verify_preflight()
    payloads = base.task_payloads(bundle)
    live = base.load_live_runner()
    settings_base = base.DeepSeekSettings.from_secret_file(
        timeout_seconds=60.0, max_response_bytes=2_097_152, max_output_tokens=2048
    )
    all_records = []

    def continuation(record):
        if record["result"].get("status") != "completed":
            raise RuntimeError(
                f"calibration trial ended with Harness exception; stop campaign: {record['trialId']}"
            )
        if record["providerIdentity"]["standing"] != "PASS_EFFECTIVE_IDENTITY":
            raise RuntimeError(
                f"Provider identity drift detected; stop campaign: {record['trialId']}"
            )

    for block in prereg["schedule"]["blocks"]:
        trials = [
            r for r in prereg["schedule"]["trials"] if r["blockId"] == block["blockId"]
        ]

        def execute_one(trial):
            payload = payloads[trial["taskId"]]
            settings = replace(settings_base, model=trial["model"])
            with tempfile.TemporaryDirectory(
                prefix="ordivon-r2-2-calibration-"
            ) as directory:
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
                "designRevision": DESIGN_REVISION,
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
                        "totalTokens": (result.get("usage") or {}).get("totalTokens")
                        if isinstance(result.get("usage"), dict)
                        else None,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            return record

        rows = tb.execute_task_block(
            output_dir=output_dir,
            trials=trials,
            execute_one=execute_one,
            continuation_check=continuation,
        )
        all_records.extend(rows)
        cert = analysis.decision_frontier_certificate(all_records, prereg["schedule"])
        tb.json_write(
            output_dir / "frontier" / f"after-block-{block['blockOrdinal']:02d}.json",
            cert,
        )
        print("CALIBRATION_FRONTIER=" + json.dumps(cert, sort_keys=True), flush=True)
        if cert["standing"] != "UNDECIDED":
            return all_records, cert
    cert = analysis.decision_frontier_certificate(all_records, prereg["schedule"])
    if cert["standing"] == "UNDECIDED":
        raise RuntimeError("complete R2.2 calibration unexpectedly remains undecided")
    return all_records, cert


def finalize(
    output_dir: Path,
    prereg: dict[str, Any],
    records: list[dict[str, Any]],
    certificate: dict[str, Any],
) -> dict[str, Any]:
    base = load_base_runner()
    tb = load_task_block()
    observed = {r["trialId"] for r in records}
    all_ids = [r["trialId"] for r in prereg["schedule"]["trials"]]
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-result-set",
        "calibrationId": CALIBRATION_ID,
        "experimentId": EXPERIMENT_ID,
        "designRevision": DESIGN_REVISION,
        "preregistrationDigest": prereg["preregistrationDigest"],
        "observedTrialCount": len(records),
        "unobservedTrialIds": [x for x in all_ids if x not in observed],
        "records": sorted(records, key=lambda r: r["ordinal"]),
    }
    result["resultSetDigest"] = base.canonical_digest(result)
    tb.json_write(output_dir / "results.json", result)
    standing = (
        "PASS_CALIBRATION_DIFFICULTY"
        if certificate["standing"] == "DECISIVE_PASS_CALIBRATION_DIFFICULTY"
        else "REJECT_TASK_BANK_DIFFICULTY"
    )
    gate = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-decision-frontier-gate",
        "calibrationId": CALIBRATION_ID,
        "experimentId": EXPERIMENT_ID,
        "designRevision": DESIGN_REVISION,
        "standing": standing,
        "decisionFrontierCertificate": certificate,
        "preregistrationDigest": prereg["preregistrationDigest"],
        "resultSetDigest": result["resultSetDigest"],
        "providerIdentityPreflightDigest": prereg["providerIdentityPreflightBinding"][
            "preflightDigest"
        ],
        "semanticBridge": "Standing is licensed only because the decision-frontier certificate preserves the frozen full-gate decision across every legal completion.",
    }
    gate["calibrationReceiptDigest"] = base.canonical_digest(gate)
    tb.json_write(output_dir / "gate.json", gate)
    acc = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-acceptance",
        "calibrationId": CALIBRATION_ID,
        "experimentId": EXPERIMENT_ID,
        "designRevision": DESIGN_REVISION,
        "preregistrationDigest": prereg["preregistrationDigest"],
        "resultSetDigest": result["resultSetDigest"],
        "gateDigest": gate["calibrationReceiptDigest"],
        "observedTrialCount": len(records),
        "plannedTrialCount": prereg["schedule"]["trialCount"],
        "providerIdentityStanding": "PASS_DISTINCT_EFFECTIVE_IDENTITIES_AND_NO_DRIFT",
        "standing": standing,
        "inferentialCampaignAdmitted": standing == "PASS_CALIBRATION_DIFFICULTY",
        "admittedInferentialScheduleDigest": prereg["plannedInferentialSchedule"][
            "scheduleDigest"
        ]
        if standing == "PASS_CALIBRATION_DIFFICULTY"
        else None,
        "nonClaims": [
            "Calibration is a task-bank difficulty gate only.",
            "Calibration observations are excluded from R2 inferential treatment-effect estimates.",
        ],
    }
    acc["acceptanceDigest"] = base.canonical_digest(acc)
    tb.json_write(output_dir / "acceptance.json", acc)
    return acc


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preregister-only", action="store_true")
    mode.add_argument("--run-live", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    prereg = resolve_preregistration(args.output_dir)
    if args.preregister_only:
        print(
            "CALIBRATION_PREREGISTRATION=" + json.dumps(prereg, sort_keys=True),
            flush=True,
        )
        return 0
    records, cert = execute_campaign(args.output_dir, prereg)
    acc = finalize(args.output_dir, prereg, records, cert)
    print("CALIBRATION_ACCEPTANCE=" + json.dumps(acc, sort_keys=True), flush=True)
    return 0 if acc["standing"] == "PASS_CALIBRATION_DIFFICULTY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
