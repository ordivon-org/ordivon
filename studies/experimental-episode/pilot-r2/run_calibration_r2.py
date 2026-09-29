from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from anc_canonical import canonical_digest
from ordivon_harness.ordivon.deepseek import DeepSeekSettings

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
HARNESS_ROOT = ROOT / "services" / "harness"
ANALYSIS_PATH = HERE.with_name("analysis_r2.py")
DESIGN_PATH = HERE.with_name("design_r2.py")
LIVE_RUNNER_PATH = HARNESS_ROOT / "scripts" / "run_adaptive_edit_r2_live_ab.py"
TASK_BUNDLE_PATH = HERE.parent / "evidence" / "design" / "calibration-task-bank.json"
PREFLIGHT_PATH = HERE.parent / "evidence" / "preflight" / "20260929-r1" / "provider-identity-preflight.json"
EXPERIMENT_ID = "experiment:experimental-fabric-model-harness-pilot-r2-20260929"
CALIBRATION_ID = "calibration:experimental-fabric-r2:20260929-r1"
MAX_TOTAL_TOKENS = 64_000


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def journal_append(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_analysis():
    return load_module(ANALYSIS_PATH, "experimental_fabric_r2_analysis")


def load_design():
    return load_module(DESIGN_PATH, "experimental_fabric_r2_design")


def verify_generated(source: str, task_spec) -> dict[str, bool]:
    with tempfile.TemporaryDirectory(prefix="ordivon-r2-verify-") as directory:
        workspace = Path(directory) / "workspace"
        shutil.copytree(task_spec.fixture, workspace)
        (workspace / task_spec.target_path).write_text(source, encoding="utf-8")
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "ORDIVON_EVAL_WORKSPACE": str(workspace)}
        visible = subprocess.run(
            ["/usr/bin/python3", "-m", "pytest", "-q", task_spec.visible_test],
            cwd=workspace, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30, check=False,
        )
        hidden = subprocess.run(
            ["/usr/bin/python3", str(task_spec.hidden_verifier)],
            cwd=workspace, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30, check=False,
        )
        return {"visiblePassed": visible.returncode == 0, "hiddenPassed": hidden.returncode == 0}


def load_live_runner():
    module = load_module(LIVE_RUNNER_PATH, "experimental_fabric_r2_live_runner")
    module.ROOT = HARNESS_ROOT
    module.verify = verify_generated
    return module


def verify_bundle() -> dict[str, Any]:
    value = json.loads(TASK_BUNDLE_PATH.read_text(encoding="utf-8"))
    if value.get("kind") != "ordivon.experimental-task-bank-bundle" or value.get("cohort") != "calibration":
        raise RuntimeError("calibration task bundle kind/cohort differs")
    expected_bundle = canonical_digest({key: item for key, item in value.items() if key != "bundleDigest"})
    if value.get("bundleDigest") != expected_bundle:
        raise RuntimeError("calibration task bundle digest invalid")
    manifest = value.get("manifest")
    if not isinstance(manifest, dict):
        raise RuntimeError("calibration task bundle lacks manifest")
    expected_manifest = canonical_digest({key: item for key, item in manifest.items() if key != "manifestDigest"})
    if manifest.get("manifestDigest") != expected_manifest:
        raise RuntimeError("calibration task manifest digest invalid")
    if manifest.get("taskCount") != 6 or len(value.get("tasks", [])) != 6:
        raise RuntimeError("calibration task bundle must contain six tasks")
    manifest_rows = {row["taskId"]: row for row in manifest.get("tasks", [])}
    if len(manifest_rows) != 6:
        raise RuntimeError("calibration manifest task IDs are not unique")
    for payload in value["tasks"]:
        definition = payload.get("definition")
        qa = payload.get("qa")
        if not isinstance(definition, dict) or not isinstance(qa, dict):
            raise RuntimeError("calibration task payload lacks definition/QA")
        task_id = definition.get("taskId")
        if task_id not in manifest_rows:
            raise RuntimeError(f"calibration payload absent from manifest: {task_id}")
        if qa.get("standing") != "PASS" or manifest_rows[task_id].get("qaStanding") != "PASS":
            raise RuntimeError(f"calibration task QA not PASS: {task_id}")
        expected_task = canonical_digest({key: item for key, item in definition.items() if key != "taskDigest"})
        if definition.get("taskDigest") != expected_task or manifest_rows[task_id].get("taskDigest") != expected_task:
            raise RuntimeError(f"calibration task digest invalid: {task_id}")
        expected_qa = canonical_digest({key: item for key, item in qa.items() if key != "qaDigest"})
        if qa.get("qaDigest") != expected_qa or manifest_rows[task_id].get("qaDigest") != expected_qa:
            raise RuntimeError(f"calibration QA digest invalid: {task_id}")
    return value


def verify_preflight() -> dict[str, Any]:
    value = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    design = load_design()
    design.validate_provider_identity_preflight(value)
    expected = canonical_digest({key: item for key, item in value.items() if key != "preflightDigest"})
    if value.get("preflightDigest") != expected:
        raise RuntimeError("Provider identity preflight digest invalid")
    return value


def build_preregistration(*, source_revision: str | None = None) -> dict[str, Any]:
    bundle = verify_bundle()
    preflight = verify_preflight()
    analysis = load_analysis()
    schedule = analysis.compile_calibration_schedule(bundle["manifest"])
    current_revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    git_revision = current_revision if source_revision is None else source_revision
    if source_revision is not None:
        subprocess.run(["git", "merge-base", "--is-ancestor", source_revision, current_revision], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-preregistration",
        "calibrationId": CALIBRATION_ID,
        "experimentId": EXPERIMENT_ID,
        "gitRevision": git_revision,
        "runnerBinding": {"path": str(HERE.relative_to(ROOT)), "digest": file_digest(HERE)},
        "liveHarnessBinding": {"path": str(LIVE_RUNNER_PATH.relative_to(ROOT)), "digest": file_digest(LIVE_RUNNER_PATH)},
        "analysisBinding": {"path": str(ANALYSIS_PATH.relative_to(ROOT)), "digest": file_digest(ANALYSIS_PATH)},
        "taskBundleBinding": {"path": str(TASK_BUNDLE_PATH.relative_to(ROOT)), "fileDigest": file_digest(TASK_BUNDLE_PATH), "bundleDigest": bundle["bundleDigest"], "manifestDigest": bundle["manifest"]["manifestDigest"]},
        "providerIdentityPreflightBinding": {"path": str(PREFLIGHT_PATH.relative_to(ROOT)), "fileDigest": file_digest(PREFLIGHT_PATH), "preflightDigest": preflight["preflightDigest"], "effectiveIdentityMap": preflight["effectiveIdentityMap"]},
        "schedule": schedule,
        "resourceEnvelope": {"maxModelCalls": 6, "maxToolCalls": 8, "maxWallTimeMs": 90_000, "maxTotalTokens": MAX_TOTAL_TOKENS, "maxOutputTokensPerProviderCall": 2048, "maxModelRetries": 1},
        "gate": {"minimumSuccessesInclusive": analysis.CALIBRATION_MIN_SUCCESSES, "maximumSuccessesInclusive": analysis.CALIBRATION_MAX_SUCCESSES, "minimumMixedTasks": analysis.CALIBRATION_MIN_MIXED_TASKS, "minimumMixedFamilies": analysis.CALIBRATION_MIN_MIXED_FAMILIES, "gateImplementationDigest": file_digest(ANALYSIS_PATH)},
        "stopRules": [
            "Each of the 24 calibration cells is admitted at most once in this calibration revision.",
            "An unmatched trial_started requires reconciliation before any further Provider dispatch.",
            "Any Provider effective-identity drift or Harness exception completes the observed trial record and stops the calibration campaign before the next cell.",
            "Calibration outcomes never enter the inferential treatment-effect sample.",
            "REJECT_TASK_BANK_DIFFICULTY forbids R2 inferential preregistration/campaign under this frozen task bank.",
        ],
        "nonClaims": [
            "Calibration is a preregistered task-difficulty admission gate, not a treatment-effect hypothesis test.",
            "The four-call Provider identity preflight is not rerun by this calibration runner.",
            "A PASS calibration does not establish power, treatment efficacy, model superiority, or Harness superiority.",
        ],
    }
    value["preregistrationDigest"] = canonical_digest(value)
    return value


def write_or_validate_preregistration(output_dir: Path, prereg: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "preregistration.json"
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
        if current != prereg:
            raise RuntimeError("stored calibration preregistration differs from bound method")
        return
    if any(output_dir.iterdir()):
        raise RuntimeError("non-empty calibration evidence directory lacks preregistration")
    json_write(path, prereg)
    json_write(output_dir / "schedule.json", prereg["schedule"])


def resolve_preregistration(output_dir: Path) -> dict[str, Any]:
    path = output_dir / "preregistration.json"
    if not path.exists():
        value = build_preregistration()
        write_or_validate_preregistration(output_dir, value)
        return value
    current = json.loads(path.read_text(encoding="utf-8"))
    expected_digest = canonical_digest({key: item for key, item in current.items() if key != "preregistrationDigest"})
    if current.get("preregistrationDigest") != expected_digest:
        raise RuntimeError("stored calibration preregistration digest invalid")
    source_revision = current.get("gitRevision")
    if not isinstance(source_revision, str) or not source_revision:
        raise RuntimeError("stored calibration preregistration lacks Git revision")
    expected = build_preregistration(source_revision=source_revision)
    if current != expected:
        raise RuntimeError("stored calibration preregistration no longer matches bound code/evidence")
    return current


def read_journal(path: Path) -> tuple[set[str], set[str]]:
    started: set[str] = set()
    completed: set[str] = set()
    if not path.exists():
        return started, completed
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("event") == "trial_started":
            started.add(row["trialId"])
        elif row.get("event") == "trial_completed":
            completed.add(row["trialId"])
    return started, completed


def trial_record_path(output_dir: Path, trial_id: str) -> Path:
    return output_dir / "trials" / f"{trial_id.replace(':', '-')}.json"


def task_payloads(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["definition"]["taskId"]): row for row in bundle["tasks"]}


def materialize_task(payload: dict[str, Any], live, root: Path):
    definition = payload["definition"]
    fixture = root / "fixture"
    fixture.mkdir(parents=True)
    for row in payload["visibleFiles"]:
        path = fixture / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(row["content"], encoding="utf-8")
    task_path = root / "task.json"
    task_path.write_text(json.dumps({"taskId": definition["taskId"], "taskVersion": 1, "objective": definition["objective"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    oracle = root / "oracle.py"
    oracle.write_text(payload["oracleSource"], encoding="utf-8")
    verifier = root / "hidden_verifier.py"
    verifier.write_text(payload["hiddenVerifierSource"], encoding="utf-8")
    read_paths = tuple(row["path"] for row in payload["visibleFiles"])
    return live.LiveTaskSpec(task_path=task_path, fixture=fixture, oracle=oracle, hidden_verifier=verifier, read_paths=read_paths, target_path=definition["targetPath"], visible_test=definition["visibleTestPath"])


def assess_provider_identity(result: dict[str, Any], requested: str, preflight: dict[str, Any]) -> dict[str, Any]:
    expected = preflight["effectiveIdentityMap"][requested]
    usage = result.get("usage")
    if not isinstance(usage, dict):
        return {"standing": "FAIL_MISSING_USAGE", "requestedModelId": requested, "expectedEffectiveModelId": expected}
    effective = usage.get("effectiveModelIds")
    rows = usage.get("providerUsage") if isinstance(usage.get("providerUsage"), list) else []
    pass_rows = bool(rows) and all(isinstance(row, dict) and row.get("requestedModelId") == requested and row.get("effectiveModelId") == expected and row.get("providerModel") == expected for row in rows)
    passed = usage.get("requestedModelId") == requested and effective == [expected] and pass_rows
    return {"standing": "PASS_EFFECTIVE_IDENTITY" if passed else "FAIL_EFFECTIVE_IDENTITY_DRIFT", "requestedModelId": requested, "expectedEffectiveModelId": expected, "observedEffectiveModelIds": effective if isinstance(effective, list) else [], "providerCallCount": len(rows), "systemFingerprints": sorted({str(row["systemFingerprint"]) for row in rows if isinstance(row, dict) and row.get("systemFingerprint")})}


def execute_trials(output_dir: Path, prereg: dict[str, Any]) -> list[dict[str, Any]]:
    journal = output_dir / "journal.jsonl"
    started, completed = read_journal(journal)
    uncertain = sorted(started - completed)
    if uncertain:
        raise RuntimeError(f"uncertain calibration trials require reconciliation before dispatch: {uncertain}")
    bundle = verify_bundle()
    preflight = verify_preflight()
    payload_by_id = task_payloads(bundle)
    live = load_live_runner()
    base = DeepSeekSettings.from_secret_file(timeout_seconds=60.0, max_response_bytes=2_097_152, max_output_tokens=2048)
    records: list[dict[str, Any]] = []
    for trial in prereg["schedule"]["trials"]:
        trial_id = trial["trialId"]
        path = trial_record_path(output_dir, trial_id)
        if trial_id in completed:
            if not path.is_file():
                raise RuntimeError(f"completed calibration journal entry lacks trial artifact: {trial_id}")
            records.append(json.loads(path.read_text(encoding="utf-8")))
            continue
        journal_append(journal, {"event": "trial_started", "trialId": trial_id, "ordinal": trial["ordinal"], "taskId": trial["taskId"], "taskFamily": trial["taskFamily"], "model": trial["model"], "codec": trial["codec"], "observedAtUnixMs": int(time.time() * 1000)})
        payload = payload_by_id[trial["taskId"]]
        settings = replace(base, model=trial["model"])
        with tempfile.TemporaryDirectory(prefix="ordivon-r2-calibration-") as directory:
            task_spec = materialize_task(payload, live, Path(directory))
            result = live.run_one(trial["codec"], trial["ordinal"], settings, task_spec=task_spec, max_total_tokens=MAX_TOTAL_TOKENS)
        identity = assess_provider_identity(result, trial["model"], preflight)
        record = {"schemaVersion": 1, "kind": "ordivon.experimental-calibration-live-trial", "calibrationId": CALIBRATION_ID, "experimentId": EXPERIMENT_ID, **trial, "taskDigest": payload["definition"]["taskDigest"], "qaDigest": payload["qa"]["qaDigest"], "provider": "deepseek", "providerRandomness": "provider-owned", "providerIdentity": identity, "result": result}
        record["recordDigest"] = canonical_digest(record)
        json_write(path, record)
        journal_append(journal, {"event": "trial_completed", "trialId": trial_id, "recordDigest": record["recordDigest"], "status": result.get("status"), "providerIdentityStanding": identity["standing"], "observedAtUnixMs": int(time.time() * 1000)})
        records.append(record)
        print(json.dumps({"trial": trial_id, "task": trial["taskId"], "family": trial["taskFamily"], "model": trial["model"], "codec": trial["codec"], "status": result.get("status"), "hiddenPassed": result.get("hiddenPassed"), "candidateCompleted": result.get("candidateCompleted"), "identity": identity["standing"], "totalTokens": (result.get("usage") or {}).get("totalTokens") if isinstance(result.get("usage"), dict) else None}, sort_keys=True), flush=True)
        if result.get("status") != "completed":
            raise RuntimeError(f"calibration trial ended with Harness exception; stop campaign: {trial_id}")
        if identity["standing"] != "PASS_EFFECTIVE_IDENTITY":
            raise RuntimeError(f"Provider identity drift detected; stop campaign: {trial_id}")
    return records


def finalize(output_dir: Path, prereg: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) != 24:
        raise RuntimeError(f"calibration finalization requires 24 trial records, got {len(records)}")
    if len({row["trialId"] for row in records}) != 24:
        raise RuntimeError("calibration trial records are not unique")
    if any(row["result"].get("status") != "completed" for row in records):
        raise RuntimeError("calibration cannot finalize with Harness exception records")
    if any(row["providerIdentity"]["standing"] != "PASS_EFFECTIVE_IDENTITY" for row in records):
        raise RuntimeError("calibration cannot finalize with Provider identity drift")
    result_set = {"schemaVersion": 1, "kind": "ordivon.experimental-calibration-result-set", "calibrationId": CALIBRATION_ID, "experimentId": EXPERIMENT_ID, "preregistrationDigest": prereg["preregistrationDigest"], "records": sorted(records, key=lambda row: row["ordinal"])}
    result_set["resultSetDigest"] = canonical_digest(result_set)
    json_write(output_dir / "results.json", result_set)
    gate_records = [{"trialId": row["trialId"], "taskId": row["taskId"], "taskFamily": row["taskFamily"], "model": row["model"], "codec": row["codec"], "hiddenPassed": bool(row["result"]["hiddenPassed"])} for row in records]
    gate = load_analysis().calibration_gate(gate_records)
    gate["preregistrationDigest"] = prereg["preregistrationDigest"]
    gate["resultSetDigest"] = result_set["resultSetDigest"]
    gate["providerIdentityPreflightDigest"] = prereg["providerIdentityPreflightBinding"]["preflightDigest"]
    gate["calibrationReceiptDigest"] = canonical_digest(gate)
    json_write(output_dir / "gate.json", gate)
    acceptance = {"schemaVersion": 1, "kind": "ordivon.experimental-calibration-acceptance", "calibrationId": CALIBRATION_ID, "experimentId": EXPERIMENT_ID, "preregistrationDigest": prereg["preregistrationDigest"], "resultSetDigest": result_set["resultSetDigest"], "gateDigest": gate["calibrationReceiptDigest"], "trialCount": len(records), "providerIdentityStanding": "PASS_DISTINCT_EFFECTIVE_IDENTITIES_AND_NO_DRIFT", "standing": gate["standing"], "inferentialCampaignAdmitted": gate["standing"] == "PASS_CALIBRATION_DIFFICULTY", "nonClaims": ["Calibration acceptance is a task-bank difficulty gate only.", "Calibration observations are excluded from R2 inferential treatment-effect estimates."]}
    acceptance["acceptanceDigest"] = canonical_digest(acceptance)
    json_write(output_dir / "acceptance.json", acceptance)
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
    records = execute_trials(args.output_dir, prereg)
    acceptance = finalize(args.output_dir, prereg, records)
    print("CALIBRATION_ACCEPTANCE=" + json.dumps(acceptance, sort_keys=True), flush=True)
    return 0 if acceptance["standing"] == "PASS_CALIBRATION_DIFFICULTY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
