from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any


class AuthorityError(RuntimeError):
    """Fail-closed execution-policy error."""


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise AuthorityError(f"expected JSON object: {path}")
    return value


def _resolve(repo: Path, relative: str) -> Path:
    path = (repo / relative).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise AuthorityError(f"authority contract escapes repository: {relative}") from exc
    if not path.is_file():
        raise AuthorityError(f"authority contract unavailable: {relative}")
    return path


def _evaluate_opa(*, binary: Path, policy: Path, query: str, input_doc: dict[str, Any]) -> bool:
    if not binary.is_file():
        raise AuthorityError(f"OPA binary unavailable: {binary}")
    proc = subprocess.run(
        [str(binary), "eval", "--format=raw", "--data", str(policy), "--stdin-input", query],
        input=json.dumps(input_doc),
        text=True,
        capture_output=True,
        timeout=10,
    )
    if proc.returncode != 0:
        raise AuthorityError(f"OPA policy evaluation failed: {proc.stderr.strip()}")
    value = proc.stdout.strip()
    if value not in {"true", "false"}:
        raise AuthorityError(f"unexpected OPA policy result: {value!r}")
    return value == "true"


def verify_internal_authority(repo: Path, config_path: Path) -> dict[str, Any]:
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.market-capital.execution-authority":
        raise AuthorityError("unexpected execution-authority kind")

    write_doc = _load_json(_resolve(repo, cfg["externalWritePolicyInputContract"]))
    boundary = _load_json(_resolve(repo, cfg["externalBoundaryContract"]))
    if write_doc.get("kind") != "ordivon.market-capital.external-write-policy-input":
        raise AuthorityError("external-write policy input missing")
    if boundary.get("kind") != "ordivon.market-capital.external-boundary":
        raise AuthorityError("external-boundary contract missing")

    engine = cfg.get("policyEngine")
    if not isinstance(engine, dict) or engine.get("name") != "OPA":
        raise AuthorityError("OPA policy engine is required")
    policy = _resolve(repo, str(engine.get("policy") or ""))
    allowed = _evaluate_opa(
        binary=Path(str(engine.get("binary") or "")),
        policy=policy,
        query=str(engine.get("query") or ""),
        input_doc=write_doc,
    )

    return {
        "config": cfg,
        "policyEngine": "OPA",
        "externalWritePolicyAllowed": allowed,
        "externalWritePolicyStanding": write_doc.get("state"),
        "externalWriteVerifier": write_doc.get("effectVerifier", "NOT_IMPLEMENTED"),
        "providerWriteCapabilityBound": bool(write_doc.get("providerWriteCapabilityBound", False)),
        "externalFinancialWriteAllowedByContract": bool(write_doc.get("externalFinancialWriteAllowed", False)),
    }


def evaluate_non_live(repo: Path, config_path: Path) -> dict[str, Any]:
    verified = verify_internal_authority(repo, config_path)
    cfg = verified.pop("config")
    if cfg.get("currentLane") != "NON_LIVE":
        raise AuthorityError("current execution lane must remain NON_LIVE")
    if verified["externalWritePolicyAllowed"]:
        raise AuthorityError("non-live lane cannot allow external financial writes")
    if verified["externalFinancialWriteAllowedByContract"] or verified["providerWriteCapabilityBound"]:
        raise AuthorityError("non-live lane cannot bind or allow an external financial write capability")
    return {
        "standing": "NON_LIVE_EFFECT_BOUNDARY",
        **verified,
        "externalFinancialWritesAllowed": False,
    }


def evaluate_external_write(repo: Path, config_path: Path) -> dict[str, Any]:
    verified = verify_internal_authority(repo, config_path)
    if not verified["externalWritePolicyAllowed"]:
        raise AuthorityError("external financial write policy denied")
    raise AuthorityError("external-write execution path is not implemented")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--mode", choices=("non-live", "external-write"), default="non-live")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = (
        evaluate_non_live(args.repo, args.config)
        if args.mode == "non-live"
        else evaluate_external_write(args.repo, args.config)
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
