from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from market_capital.semantic import NOT_ADMITTED, ExternalFinancialWriteAdmission


class AuthorityError(RuntimeError):
    """Fail-closed Market Capital execution-authority error."""


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


def verify_internal_authority(repo: Path, config_path: Path) -> dict[str, Any]:
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.market-capital.execution-authority":
        raise AuthorityError("unexpected execution-authority kind")

    semantic = _load_json(_resolve(repo, cfg["semanticContract"]))
    write_admission_doc = _load_json(_resolve(repo, cfg["externalFinancialWriteAdmissionContract"]))
    boundary = _load_json(_resolve(repo, cfg["externalBoundaryContract"]))

    if semantic.get("kind") != "ordivon.market-capital.semantic-core":
        raise AuthorityError("canonical semantic contract missing")
    required = {
        "observation_same_cut",
        "proof_binding_currentness",
        "scientific_truth_not_economic_truth_not_capital_truth",
        "registry_parcel_scarcity_identity",
        "reservation_not_effect_admission",
        "effect_authority_retain_release_consume",
        "revocation_recovery_one_shot_resurrection",
        "external_financial_write_admission_boundary",
    }
    missing = sorted(required - set(semantic.get("ownedSemantics", [])))
    if missing:
        raise AuthorityError(f"canonical semantic contract is incomplete: {missing}")

    if write_admission_doc.get("kind") != "ordivon.market-capital.external-financial-write-admission":
        raise AuthorityError("canonical external-financial-write-admission contract missing")
    if boundary.get("kind") != "ordivon.market-capital.external-boundary":
        raise AuthorityError("canonical external-boundary contract missing")

    write_admission = ExternalFinancialWriteAdmission(state=write_admission_doc["state"])
    return {
        "config": cfg,
        "externalWriteAdmissionState": write_admission.state,
        "externalWriteAdmitted": write_admission.admitted,
        "externalWriteVerifier": write_admission_doc.get("effectVerifier", "NOT_IMPLEMENTED"),
        "providerWriteCapabilityBound": bool(write_admission_doc.get("providerWriteCapabilityBound", False)),
        "externalFinancialWriteAllowedByContract": bool(write_admission_doc.get("externalFinancialWriteAllowed", False)),
        "ownedSemantics": sorted(required),
    }


def evaluate_non_live(repo: Path, config_path: Path) -> dict[str, Any]:
    verified = verify_internal_authority(repo, config_path)
    cfg = verified.pop("config")
    if cfg.get("currentLane") != "NON_LIVE":
        raise AuthorityError("current execution lane must remain NON_LIVE")
    if verified["externalWriteAdmissionState"] != NOT_ADMITTED:
        raise AuthorityError("non-live lane requires external financial write admission NOT_ADMITTED")
    if verified["externalFinancialWriteAllowedByContract"] or verified["providerWriteCapabilityBound"]:
        raise AuthorityError("non-live lane cannot bind or allow an external financial write capability")
    return {
        "standing": "NON_LIVE_EFFECT_BOUNDARY",
        **verified,
        "externalFinancialWritesAllowed": False,
        "effectAuthorityAvailableForExternalWrites": False,
    }


def evaluate_external_write(repo: Path, config_path: Path) -> dict[str, Any]:
    verified = verify_internal_authority(repo, config_path)
    cfg = verified.pop("config")
    if not verified["externalWriteAdmitted"]:
        raise AuthorityError("external financial write admission is not admitted")
    if verified["externalWriteVerifier"] != "IMPLEMENTED_BOUND_CURRENT" or not verified["providerWriteCapabilityBound"]:
        raise AuthorityError("external financial write verifier/capability is not implemented, bound, and current")
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
