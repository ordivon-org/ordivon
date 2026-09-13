from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from market_capital.semantic import BLOCK_NOT_GRANTED, ProductionAuthorization


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
    production_doc = _load_json(_resolve(repo, cfg["productionAuthorizationContract"]))
    boundary = _load_json(_resolve(repo, cfg["externalBoundaryContract"]))

    if semantic.get("kind") != "ordivon.market-capital.semantic-core":
        raise AuthorityError("canonical semantic contract missing")
    required = {
        "observation_same_cut",
        "proof_binding_currentness",
        "scientific_truth_not_economic_truth_not_capital_truth",
        "registry_parcel_scarcity_identity",
        "reservation_not_grant",
        "effect_authority_retain_release_consume",
        "revocation_recovery_one_shot_resurrection",
        "production_authorization_boundary",
    }
    missing = sorted(required - set(semantic.get("ownedSemantics", [])))
    if missing:
        raise AuthorityError(f"canonical semantic contract is incomplete: {missing}")

    if production_doc.get("kind") != "ordivon.market-capital.production-authorization":
        raise AuthorityError("canonical production-authorization contract missing")
    if boundary.get("kind") != "ordivon.market-capital.external-boundary":
        raise AuthorityError("canonical external-boundary contract missing")

    production = ProductionAuthorization(state=production_doc["state"])
    return {
        "config": cfg,
        "productionState": production.state,
        "productionGranted": production.granted,
        "productionExternalFinancialWriteAllowed": bool(
            production_doc.get("externalFinancialWriteAllowed", False)
        ),
        "ownedSemantics": sorted(required),
    }


def evaluate_non_live(repo: Path, config_path: Path) -> dict[str, Any]:
    verified = verify_internal_authority(repo, config_path)
    cfg = verified.pop("config")
    if cfg.get("currentLane") != "NON_LIVE":
        raise AuthorityError("current execution lane must remain NON_LIVE")
    if verified["productionState"] != BLOCK_NOT_GRANTED:
        raise AuthorityError("non-live lane requires ProductionAuthorization=BLOCK_NOT_GRANTED")
    if verified["productionExternalFinancialWriteAllowed"]:
        raise AuthorityError("non-live lane requires externalFinancialWriteAllowed=false")
    return {
        "standing": "INTERNAL_AUTHORITY_GATE_NON_LIVE",
        **verified,
        "externalFinancialWritesAllowed": False,
        "effectAuthorityAvailableForExternalWrites": False,
    }


def evaluate_external_write(repo: Path, config_path: Path) -> dict[str, Any]:
    verified = verify_internal_authority(repo, config_path)
    cfg = verified.pop("config")
    if cfg.get("externalFinancialWriteAdmission") != "ADMITTED":
        raise AuthorityError("external financial write admission is not admitted")
    if cfg.get("liveGrantMechanism") != "ADMITTED":
        raise AuthorityError("independent live grant mechanism is not admitted")
    raise AuthorityError(
        "external-write verifier is intentionally not implemented; code-level live admission is required"
    )


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
