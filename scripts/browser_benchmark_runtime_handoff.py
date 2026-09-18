#!/usr/bin/env python3
"""BCR-S4 Runtime admission-template and result reconciliation boundary.

This module never calls Runtime. It mechanically projects one S3 READY preparation into a
workspace.exec-compatible execution template without serializing secret values, then reconciles
an exact Runtime observation with an exact S3 route-run result. Runtime process success, route
execution, and semantic benchmark success remain separate truth axes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

import browser_benchmark_route_adapter as route_adapter
import browser_capability_router as router

WORKSPACE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
DELIVERY_DISPOSITIONS = frozenset(
    {"in_progress", "committed", "reconciliation_required", "unknown"}
)
SEMANTIC_STANDINGS = frozenset({"NOT_EXECUTED", "UNVERIFIED", "PASS", "FAIL"})


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _digest_without(value: Mapping[str, Any], field: str) -> str:
    copy = dict(value)
    copy.pop(field, None)
    return router.canonical_digest(copy)


def validate_preparation(raw: Mapping[str, Any]) -> dict[str, Any]:
    if (
        raw.get("schemaVersion") != 1
        or raw.get("kind") != "ordivon.browser-benchmark-run-preparation"
    ):
        raise ValueError("benchmark preparation identity mismatch")
    standing = raw.get("standing")
    if standing not in {"PREEXEC_BLOCKED", "READY_FOR_RUNTIME"}:
        raise ValueError("benchmark preparation standing is invalid")
    for key in (
        "benchmarkId",
        "suiteDigest",
        "runId",
        "caseId",
        "caseDigest",
        "routeId",
        "preparationDigest",
    ):
        value = raw.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"benchmark preparation has invalid {key}")
    if raw.get("effectsExecuted") is not False:
        raise ValueError("benchmark preparation must not claim effects")
    if raw["preparationDigest"] != _digest_without(raw, "preparationDigest"):
        raise ValueError("benchmark preparation digest mismatch")

    proposal = raw.get("executionProposal")
    if standing == "PREEXEC_BLOCKED":
        if proposal is not None:
            raise ValueError("PREEXEC_BLOCKED preparation must not carry execution proposal")
        receipt = raw.get("preflightReceipt")
        if not isinstance(receipt, dict) or receipt.get("standing") != "PREEXEC_BLOCKED":
            raise ValueError("PREEXEC_BLOCKED preparation requires blocked preflight receipt")
        return dict(raw)

    if not isinstance(proposal, dict):
        raise ValueError("READY_FOR_RUNTIME preparation requires execution proposal")
    if (
        proposal.get("schemaVersion") != 1
        or proposal.get("kind")
        != "ordivon.browser-benchmark-runtime-execution-proposal"
    ):
        raise ValueError("Runtime execution proposal identity mismatch")
    if proposal.get("proposalDigest") != _digest_without(proposal, "proposalDigest"):
        raise ValueError("Runtime execution proposal digest mismatch")
    for key in ("runId", "caseId", "caseDigest", "routeId"):
        if proposal.get(key) != raw.get(key):
            raise ValueError(f"Runtime execution proposal differs from preparation: {key}")
    request_digest = proposal.get("routeRunRequestDigest")
    if (
        not isinstance(request_digest, str)
        or len(request_digest) != 71
        or not request_digest.startswith("sha256:")
    ):
        raise ValueError("Runtime execution proposal has invalid routeRunRequestDigest")
    required = proposal.get("requiredSecretEnvironment")
    if (
        not isinstance(required, list)
        or any(not isinstance(item, str) or not item for item in required)
        or len(required) != len(set(required))
    ):
        raise ValueError("Runtime execution proposal secret-name contract is invalid")
    env = proposal.get("env")
    if not isinstance(env, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in env.items()
    ):
        raise ValueError("Runtime execution proposal env is invalid")
    leaked = sorted(set(required) & set(env))
    if leaked:
        raise ValueError(f"Runtime execution proposal serialized secret values: {leaked}")
    return dict(raw)


def build_admission_template(
    preparation: Mapping[str, Any],
    *,
    workspace_id: str,
) -> dict[str, Any]:
    prep = validate_preparation(preparation)
    if not WORKSPACE_ID.fullmatch(workspace_id):
        raise ValueError("workspaceId is invalid")
    if prep["standing"] == "PREEXEC_BLOCKED":
        value = {
            "schemaVersion": 1,
            "kind": "ordivon.browser-benchmark-runtime-admission-template",
            "standing": "PREEXEC_BLOCKED",
            "preparationDigest": prep["preparationDigest"],
            "runId": prep["runId"],
            "caseDigest": prep["caseDigest"],
            "routeId": prep["routeId"],
            "workspaceId": workspace_id,
            "clientRequestId": None,
            "runtimeOperation": None,
            "execution": None,
            "requiredSecretEnvironment": [],
            "secretValuesIncluded": False,
            "nonClaims": ["runtime_admission", "semantic_success"],
        }
        value["templateDigest"] = router.canonical_digest(value)
        return value

    proposal = prep["executionProposal"]
    client_basis = (
        prep["preparationDigest"]
        + ":"
        + proposal["proposalDigest"]
        + ":"
        + workspace_id
    )
    client_request_id = "bcr-s4-" + hashlib.sha256(client_basis.encode()).hexdigest()[:48]
    execution = {
        "workspaceId": workspace_id,
        "executable": proposal["executable"],
        "args": list(proposal["args"]),
        "cwdRelative": proposal["cwdRelative"],
        "env": dict(proposal["env"]),
        "executionTarget": proposal["executionTarget"],
        "executionProfile": proposal["executionProfile"],
        "timeoutMs": proposal["timeoutMs"],
        "stdoutLimitBytes": proposal["stdoutLimitBytes"],
        "stderrLimitBytes": proposal["stderrLimitBytes"],
    }
    if proposal.get("windowsAuthority") is not None:
        execution["windowsAuthority"] = proposal["windowsAuthority"]

    if proposal["executionTarget"] == "local_linux":
        dependencies = [
            {
                "path": str(proposal["args"][0]),
                "expectedDigest": proposal["adapterScriptDigest"],
            },
            {
                "path": str(proposal["args"][-1]),
                "expectedDigest": proposal["requestFileDigest"],
            },
        ]
        execution["hostDependencies"] = sorted(dependencies, key=lambda row: row["path"])
        source_continuity = "RUNTIME_HOST_DEPENDENCY_WITNESS"
    else:
        source_continuity = "PROPOSAL_DIGEST_ONLY_NO_WINDOWS_HOST_DEPENDENCY_WITNESS"

    value = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-runtime-admission-template",
        "standing": "ADMISSION_TEMPLATE_READY",
        "preparationDigest": prep["preparationDigest"],
        "proposalDigest": proposal["proposalDigest"],
        "routeRunRequestDigest": proposal["routeRunRequestDigest"],
        "runId": prep["runId"],
        "caseDigest": prep["caseDigest"],
        "routeId": prep["routeId"],
        "workspaceId": workspace_id,
        "clientRequestId": client_request_id,
        "runtimeOperation": "workspace.exec",
        "execution": execution,
        "requiredSecretEnvironment": list(proposal["requiredSecretEnvironment"]),
        "secretValuesIncluded": False,
        "sourceContinuity": source_continuity,
        "nonClaims": [
            "runtime_admission",
            "required_secrets_present",
            "physical_execution",
            "semantic_success",
        ],
    }
    value["templateDigest"] = router.canonical_digest(value)
    return value


def _runtime_projection(raw: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("executionTerminal", "recoveryRequired", "resultAvailable"):
        if type(raw.get(key)) is not bool:
            raise ValueError(f"Runtime observation omitted boolean {key}")
    if raw.get("semanticCompletionEvaluated") is not False:
        raise ValueError("Runtime must not claim benchmark semantic completion")
    delivery = raw.get("deliveryDisposition")
    if delivery not in DELIVERY_DISPOSITIONS:
        raise ValueError("Runtime deliveryDisposition is invalid")
    disposition = raw.get("executionDisposition")
    if disposition is not None and not isinstance(disposition, str):
        raise ValueError("Runtime executionDisposition is invalid")
    job_id = raw.get("jobId")
    attempt_id = raw.get("attemptId")
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("Runtime observation omitted jobId")
    if attempt_id is not None and (not isinstance(attempt_id, str) or not attempt_id):
        raise ValueError("Runtime attemptId is invalid")
    return {
        "jobId": job_id,
        "attemptId": attempt_id,
        "executionTerminal": raw["executionTerminal"],
        "executionDisposition": disposition,
        "deliveryDisposition": delivery,
        "recoveryRequired": raw["recoveryRequired"],
        "resultAvailable": raw["resultAvailable"],
        "exitCode": raw.get("exitCode"),
        "semanticCompletionEvaluated": False,
    }


def _base_reconciliation(
    prep: Mapping[str, Any],
    runtime: Mapping[str, Any] | None,
    *,
    standing: str,
    semantic: str,
) -> dict[str, Any]:
    if semantic not in SEMANTIC_STANDINGS:
        raise ValueError("semantic standing is invalid")
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-runtime-reconciliation",
        "runId": prep["runId"],
        "caseDigest": prep["caseDigest"],
        "routeId": prep["routeId"],
        "preparationDigest": prep["preparationDigest"],
        "proposalDigest": (
            prep["executionProposal"]["proposalDigest"]
            if isinstance(prep.get("executionProposal"), dict)
            else None
        ),
        "standing": standing,
        "semanticStanding": semantic,
        "runtime": dict(runtime) if runtime is not None else None,
        "routeResultDigest": None,
        "benchmarkReceiptDigest": None,
        "providerEffectMayHaveOccurred": None,
        "nonClaims": [
            "runtime_process_success_is_not_route_execution",
            "route_execution_is_not_semantic_success",
        ],
    }
    return value


def reconcile(
    preparation: Mapping[str, Any],
    runtime_observation: Mapping[str, Any] | None,
    route_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    prep = validate_preparation(preparation)
    if prep["standing"] == "PREEXEC_BLOCKED":
        if runtime_observation is not None or route_result is not None:
            raise ValueError("blocked preparation cannot have Runtime or route result")
        result = _base_reconciliation(
            prep,
            None,
            standing="PREEXEC_BLOCKED",
            semantic="NOT_EXECUTED",
        )
        result["providerEffectMayHaveOccurred"] = False
        result["reconciliationDigest"] = router.canonical_digest(result)
        return result

    if runtime_observation is None:
        result = _base_reconciliation(
            prep,
            None,
            standing="RUNTIME_RESULT_UNRESOLVED",
            semantic="UNVERIFIED",
        )
        result["reconciliationDigest"] = router.canonical_digest(result)
        return result

    runtime = _runtime_projection(runtime_observation)
    delivery = runtime["deliveryDisposition"]
    if (
        runtime["recoveryRequired"]
        or delivery in {"in_progress", "reconciliation_required"}
    ):
        result = _base_reconciliation(
            prep,
            runtime,
            standing="RUNTIME_RECONCILIATION_REQUIRED",
            semantic="UNVERIFIED",
        )
        result["reconciliationDigest"] = router.canonical_digest(result)
        return result
    if delivery == "unknown":
        result = _base_reconciliation(
            prep,
            runtime,
            standing="RUNTIME_RESULT_UNRESOLVED",
            semantic="UNVERIFIED",
        )
        result["reconciliationDigest"] = router.canonical_digest(result)
        return result
    if not runtime["executionTerminal"]:
        raise ValueError("Runtime committed observation is not terminal")
    if runtime["executionDisposition"] != "succeeded":
        result = _base_reconciliation(
            prep,
            runtime,
            standing="RUNTIME_FAILED",
            semantic="UNVERIFIED",
        )
        result["reconciliationDigest"] = router.canonical_digest(result)
        return result
    if runtime.get("exitCode") != 0:
        raise ValueError("Runtime succeeded disposition requires exitCode=0")
    if not runtime["resultAvailable"]:
        result = _base_reconciliation(
            prep,
            runtime,
            standing="RUNTIME_RESULT_UNRESOLVED",
            semantic="UNVERIFIED",
        )
        result["reconciliationDigest"] = router.canonical_digest(result)
        return result
    if route_result is None:
        result = _base_reconciliation(
            prep,
            runtime,
            standing="RUNTIME_RESULT_UNRESOLVED",
            semantic="UNVERIFIED",
        )
        result["reconciliationDigest"] = router.canonical_digest(result)
        return result

    proposal = prep["executionProposal"]
    route = route_adapter.validate_run_result(
        route_result,
        expected_run_id=prep["runId"],
        expected_request_digest=proposal["routeRunRequestDigest"],
        expected_case_digest=prep["caseDigest"],
        expected_route_id=prep["routeId"],
    )
    if route["standing"] == "PRE_EFFECT_ABORTED":
        result = _base_reconciliation(
            prep,
            runtime,
            standing="PRE_EFFECT_ABORTED",
            semantic="NOT_EXECUTED",
        )
        result["routeResultDigest"] = route["resultDigest"]
        result["providerEffectMayHaveOccurred"] = False
        result["reconciliationDigest"] = router.canonical_digest(result)
        return result

    receipt = route["benchmarkReceipt"]
    witness = receipt["outcomeWitness"]["standing"]
    if witness not in {"UNVERIFIED", "PASS", "FAIL"}:
        raise ValueError("executed benchmark receipt has invalid semantic witness")
    result = _base_reconciliation(
        prep,
        runtime,
        standing="BENCHMARK_EXECUTED",
        semantic=witness,
    )
    result["routeResultDigest"] = route["resultDigest"]
    result["benchmarkReceiptDigest"] = receipt["receiptDigest"]
    result["providerEffectMayHaveOccurred"] = route["providerEffectMayHaveOccurred"]
    result["reconciliationDigest"] = router.canonical_digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    admission = sub.add_parser("admission-template")
    admission.add_argument("--preparation-file", type=Path, required=True)
    admission.add_argument("--workspace-id", required=True)
    rec = sub.add_parser("reconcile")
    rec.add_argument("--preparation-file", type=Path, required=True)
    rec.add_argument("--runtime-observation-file", type=Path)
    rec.add_argument("--route-result-file", type=Path)
    args = parser.parse_args()
    preparation = _read_json(args.preparation_file)
    if args.command == "admission-template":
        value = build_admission_template(preparation, workspace_id=args.workspace_id)
    else:
        runtime = (
            _read_json(args.runtime_observation_file)
            if args.runtime_observation_file is not None
            else None
        )
        route = (
            _read_json(args.route_result_file)
            if args.route_result_file is not None
            else None
        )
        value = reconcile(preparation, runtime, route)
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
