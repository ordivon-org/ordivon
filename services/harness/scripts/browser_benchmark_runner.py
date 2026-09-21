#!/usr/bin/env python3
"""BCR-S3 orchestration and Runtime execution-proposal builder.

This layer does not call Runtime and does not own physical execution truth. It runs S2 preflight,
materializes one digest-bound route-run request, then returns the exact local_linux or windows_native
execution proposal required for a caller with Runtime authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Callable, Mapping

import browser_benchmark_contract as benchmark
import browser_benchmark_route_adapter as route_adapter
import browser_capability_router as router

ROOT = Path(__file__).resolve().parents[1]
ROUTE_ADAPTER = ROOT / "scripts/browser_benchmark_route_adapter.py"
JEV_ACTIVE_USER_LAUNCHER = ROOT / "scripts/jev_active_user_launcher.ps1"
DEFAULT_STATE_ROOT = Path(
    os.environ.get(
        "ORDIVON_BROWSER_BENCHMARK_STATE_ROOT",
        "/tmp/ordivon-browser-benchmark-s3",
    )
)
JEV_PROVIDER_STATUS = Path("/root/tools/bin/workstation-windows-jev-provider")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        current = _read_json(path)
        if current != value:
            raise RuntimeError(f"benchmark state conflict: {path}")
        return
    fd, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(raw, path)
    finally:
        try:
            os.unlink(raw)
        except FileNotFoundError:
            pass


def _case_by_id(suite: Mapping[str, Any], case_id: str) -> dict[str, Any]:
    rows = [row for row in benchmark.compile_cases(suite) if row["caseId"] == case_id]
    if len(rows) != 1:
        raise ValueError(f"caseId must resolve exactly once: {case_id}")
    return rows[0]


def _default_jev_status() -> dict[str, Any]:
    proc = subprocess.run(
        [str(JEV_PROVIDER_STATUS), "status"],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("Windows Jev provider status returned invalid JSON") from error
    if not isinstance(value, dict) or value.get("healthy") is not True:
        raise RuntimeError("Windows Jev provider is not healthy")
    return value


def _default_windows_path(path: Path) -> str:
    proc = subprocess.run(
        ["/usr/bin/wslpath", "-w", str(path)],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError("cannot project benchmark path into Windows namespace")
    return proc.stdout.strip()


def _required_secret_environment(
    policy: Mapping[str, Any], case: Mapping[str, Any]
) -> list[str]:
    route = next(row for row in policy["routes"] if row["routeId"] == case["routeId"])
    readiness = route["readiness"]
    names = {
        item
        for item in readiness.get("requiredEnvironment", [])
        if isinstance(item, str) and item
    }
    feature_env = readiness.get("featureEnvironment")
    if isinstance(feature_env, dict):
        for feature in case["routeRequest"]["requiredFeatures"]:
            values = feature_env.get(feature)
            if isinstance(values, list):
                names.update(item for item in values if isinstance(item, str) and item)
    return sorted(names)


def _execution_proposal(
    case: Mapping[str, Any],
    request_path: Path,
    *,
    policy: Mapping[str, Any],
    jev_status_fn: Callable[[], Mapping[str, Any]] = _default_jev_status,
    windows_path_fn: Callable[[Path], str] = _default_windows_path,
) -> dict[str, Any]:
    route_id = case["routeId"]
    route_request = _read_json(request_path)
    run_id = route_request.get("runId")
    route_request_digest = route_request.get("requestDigest")
    if not isinstance(run_id, str) or not route_adapter.RUN_ID.fullmatch(run_id):
        raise ValueError("route-run request has invalid runId")
    if not isinstance(route_request_digest, str) or not route_request_digest.startswith("sha256:"):
        raise ValueError("route-run request has invalid requestDigest")
    common = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-runtime-execution-proposal",
        "runId": run_id,
        "caseId": case["caseId"],
        "caseDigest": case["caseDigest"],
        "routeId": route_id,
        "routeRunRequestDigest": route_request_digest,
        "adapterScriptDigest": _sha256_file(ROUTE_ADAPTER),
        "requestFileDigest": _sha256_file(request_path),
        "requiredSecretEnvironment": _required_secret_environment(policy, case),
        "cwdRelative": ".",
        "timeoutMs": 120000,
        "stdoutLimitBytes": 131072,
        "stderrLimitBytes": 32768,
        "nonClaims": [
            "runtime_admission",
            "task_authorization",
            "provider_credentials_transferred",
            "semantic_success",
        ],
    }
    if route_id == "browser-use-browserless-v1":
        proposal = {
            **common,
            "executionTarget": "local_linux",
            "executionProfile": "trusted_local",
            "windowsAuthority": None,
            "executable": "/usr/bin/python3",
            "args": [
                str(ROUTE_ADAPTER),
                "run",
                "--request-file",
                str(request_path),
            ],
            "env": {},
        }
    elif route_id == "jev-fast-windows-v1":
        status = dict(jev_status_fn())
        python = status.get("python")
        chrome = status.get("chrome")
        if not isinstance(python, dict) or not isinstance(chrome, dict):
            raise RuntimeError("Windows Jev status omitted python/chrome contract")
        python_path = Path(str(python.get("providerVenvPath") or ""))
        if not str(python_path).startswith("/mnt/") or python_path.suffix.lower() != ".exe":
            raise RuntimeError("Windows Jev provider venv Python path is not Runtime-addressable")
        proposal = {
            **common,
            "executionTarget": "windows_native",
            "executionProfile": "trusted_local",
            "windowsAuthority": "active_user",
            "executable": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "launcherScriptDigest": _sha256_file(JEV_ACTIVE_USER_LAUNCHER),
            "args": [
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                windows_path_fn(JEV_ACTIVE_USER_LAUNCHER),
                "-PythonExe",
                windows_path_fn(python_path),
                "-AdapterPath",
                windows_path_fn(ROUTE_ADAPTER),
                "-RequestFile",
                windows_path_fn(request_path),
                "-ChromePath",
                str(chrome.get("path") or ""),
                "-ChromeProfile",
                str(chrome.get("profileWindows") or ""),
                "-CdpPort",
                str(chrome.get("cdpPort") or ""),
                "-TypesafeDpapiFile",
                str((status.get("consumerCredentials") or {}).get("typesafeBlobWindows") or ""),
                "-TextModelDpapiFile",
                str((status.get("consumerCredentials") or {}).get("textModelBlobWindows") or ""),
            ],
            "env": {},
        }
    else:
        raise ValueError(f"S3 has no execution proposal for route {route_id}")
    proposal["proposalDigest"] = router.canonical_digest(proposal)
    return proposal


def prepare_case(
    case_id: str,
    run_id: str,
    *,
    state_root: Path = DEFAULT_STATE_ROOT,
    policy: Mapping[str, Any] | None = None,
    suite: Mapping[str, Any] | None = None,
    readiness_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    jev_status_fn: Callable[[], Mapping[str, Any]] = _default_jev_status,
    windows_path_fn: Callable[[Path], str] = _default_windows_path,
) -> dict[str, Any]:
    if not route_adapter.RUN_ID.fullmatch(run_id):
        raise ValueError("runId must be a bounded stable identifier")
    policy = policy or router.load_policy()
    suite = suite or benchmark.load_suite(policy=policy)
    case = _case_by_id(suite, case_id)
    preflight = benchmark.preflight_case(
        case,
        policy=policy,
        readiness_overrides=readiness_overrides,
    )
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-run-preparation",
        "benchmarkId": suite["benchmarkId"],
        "suiteDigest": suite["suiteDigest"],
        "runId": run_id,
        "caseId": case["caseId"],
        "caseDigest": case["caseDigest"],
        "routeId": case["routeId"],
        "preflightReceipt": preflight,
        "standing": "READY_FOR_RUNTIME" if preflight["standing"] == "READY" else "PREEXEC_BLOCKED",
        "executionProposal": None,
        "effectsExecuted": False,
    }
    if preflight["standing"] != "READY":
        result["preparationDigest"] = router.canonical_digest(result)
        return result

    request = route_adapter.build_run_request(case, preflight, run_id)
    key = hashlib.sha256(f"{run_id}:{case['caseDigest']}".encode()).hexdigest()[:32]
    request_path = state_root / key / "route-run-request.json"
    _atomic_json(request_path, request)
    result["executionProposal"] = _execution_proposal(
        case,
        request_path,
        policy=policy,
        jev_status_fn=jev_status_fn,
        windows_path_fn=windows_path_fn,
    )
    result["preparationDigest"] = router.canonical_digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=benchmark.DEFAULT_SUITE)
    parser.add_argument("--policy", type=Path, default=router.DEFAULT_ROUTE_CONFIG)
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--case-id", required=True)
    prepare.add_argument("--run-id", required=True)
    args = parser.parse_args()
    policy = router.load_policy(args.policy)
    suite = benchmark.load_suite(args.suite, policy=policy)
    value = prepare_case(
        args.case_id,
        args.run_id,
        state_root=args.state_root,
        policy=policy,
        suite=suite,
    )
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
