from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any


class ExecutionPolicyError(RuntimeError):
    """Fail-closed execution-policy evaluation error."""


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ExecutionPolicyError(f"expected JSON object: {path}")
    return value


def _resolve(repo: Path, relative: str) -> Path:
    path = (repo / relative).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise ExecutionPolicyError(f"policy path escapes repository: {relative}") from exc
    if not path.is_file():
        raise ExecutionPolicyError(f"policy input unavailable: {relative}")
    return path


def _evaluate_opa(*, binary: Path, policy: Path, query: str, input_doc: dict[str, Any]) -> bool:
    if not binary.is_file():
        raise ExecutionPolicyError(f"OPA binary unavailable: {binary}")
    proc = subprocess.run(
        [str(binary), "eval", "--format=raw", "--data", str(policy), "--stdin-input", query],
        input=json.dumps(input_doc),
        text=True,
        capture_output=True,
        timeout=10,
    )
    if proc.returncode != 0:
        raise ExecutionPolicyError(f"OPA policy evaluation failed: {proc.stderr.strip()}")
    value = proc.stdout.strip()
    if value not in {"true", "false"}:
        raise ExecutionPolicyError(f"unexpected OPA policy result: {value!r}")
    return value == "true"


def evaluate_execution_policy(repo: Path, config_path: Path) -> dict[str, Any]:
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.market-capital.execution-policy":
        raise ExecutionPolicyError("unexpected execution-policy kind")

    write_doc = _load_json(_resolve(repo, cfg["externalWritePolicyInputContract"]))
    if write_doc.get("kind") != "ordivon.market-capital.external-write-policy-input":
        raise ExecutionPolicyError("external-write policy input missing")

    engine = cfg.get("policyEngine")
    if not isinstance(engine, dict) or engine.get("name") != "OPA":
        raise ExecutionPolicyError("OPA policy engine is required")
    policy = _resolve(repo, str(engine.get("policy") or ""))
    binary = Path(str(engine.get("binary") or ""))

    policy_input = {
        "currentLane": cfg.get("currentLane"),
        "writePolicy": write_doc,
    }
    allow_non_live = _evaluate_opa(
        binary=binary,
        policy=policy,
        query=str(engine.get("queryNonLive") or ""),
        input_doc=policy_input,
    )
    allow_external_write = _evaluate_opa(
        binary=binary,
        policy=policy,
        query=str(engine.get("queryExternalWrite") or ""),
        input_doc=policy_input,
    )
    if allow_non_live and allow_external_write:
        raise ExecutionPolicyError("OPA returned mutually incompatible lane decisions")

    return {
        "policyEngine": "OPA",
        "currentLane": cfg.get("currentLane"),
        "allowNonLive": allow_non_live,
        "allowExternalWrite": allow_external_write,
        "externalWritePolicyStanding": write_doc.get("state"),
        "externalWriteVerifier": write_doc.get("effectVerifier", "NOT_IMPLEMENTED"),
        "providerWriteCapabilityBound": bool(write_doc.get("providerWriteCapabilityBound", False)),
        "externalFinancialWriteAllowedByContract": bool(write_doc.get("externalFinancialWriteAllowed", False)),
    }


def enforce_non_live(repo: Path, config_path: Path) -> dict[str, Any]:
    decision = evaluate_execution_policy(repo, config_path)
    if not decision["allowNonLive"]:
        raise ExecutionPolicyError("OPA denied non-live execution lane")
    return {
        "standing": "NON_LIVE_POLICY_ALLOWED",
        **decision,
        "externalFinancialWritesAllowed": False,
    }


def enforce_external_write(repo: Path, config_path: Path) -> dict[str, Any]:
    decision = evaluate_execution_policy(repo, config_path)
    if not decision["allowExternalWrite"]:
        raise ExecutionPolicyError("OPA denied external financial write")
    raise ExecutionPolicyError("external-write execution path is not implemented")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--mode", choices=("non-live", "external-write"), default="non-live")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = (
        enforce_non_live(args.repo, args.config)
        if args.mode == "non-live"
        else enforce_external_write(args.repo, args.config)
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
