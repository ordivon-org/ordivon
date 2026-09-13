from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


class AuthorityWaistError(RuntimeError):
    """Fail-closed authority-waist binding error."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise AuthorityWaistError(f"expected JSON object: {path}")
    return value


def _provider_head(repo: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AuthorityWaistError(f"cannot resolve provider revision: {repo}") from exc


def _load_provider_semantics(path: Path):
    spec = importlib.util.spec_from_file_location("market_capital_external_semantic_waist", path)
    if spec is None or spec.loader is None:
        raise AuthorityWaistError(f"cannot load provider semantic implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def verify_authority_binding(config_path: Path) -> dict[str, Any]:
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.market-capital.authority-waist-binding":
        raise AuthorityWaistError("unexpected authority-waist binding kind")

    provider = cfg.get("provider")
    if not isinstance(provider, dict):
        raise AuthorityWaistError("authority provider missing")
    repo = Path(provider["repo"])
    if not repo.is_dir():
        raise AuthorityWaistError(f"authority provider repo unavailable: {repo}")

    expected_revision = provider["revision"]
    observed_revision = _provider_head(repo)
    if observed_revision != expected_revision:
        raise AuthorityWaistError(
            f"authority provider revision drift: expected {expected_revision}, got {observed_revision}"
        )

    implementation = provider["implementation"]
    implementation_path = repo / implementation["path"]
    observed_implementation_digest = _sha256(implementation_path)
    if observed_implementation_digest != implementation["sha256"]:
        raise AuthorityWaistError("authority semantic implementation digest drift")

    contract_docs: dict[str, dict[str, Any]] = {}
    contract_digests: dict[str, str] = {}
    for name, binding in provider["contracts"].items():
        path = repo / binding["path"]
        observed = _sha256(path)
        if observed != binding["sha256"]:
            raise AuthorityWaistError(f"authority contract digest drift: {name}")
        contract_docs[name] = _load_json(path)
        contract_digests[name] = observed

    semantic = contract_docs["semanticFreeze"]
    owned = set(semantic.get("ownedSemantics", []))
    missing = sorted(set(cfg.get("requiredOwnedSemantics", [])) - owned)
    if missing:
        raise AuthorityWaistError(f"provider no longer owns required semantics: {missing}")

    module = _load_provider_semantics(implementation_path)
    production_doc = contract_docs["productionAuthorization"]
    production = module.ProductionAuthorization(state=production_doc["state"])

    return {
        "config": cfg,
        "providerRepo": str(repo),
        "providerRevision": observed_revision,
        "providerImplementationSha256": observed_implementation_digest,
        "contractDigests": contract_digests,
        "productionState": production.state,
        "productionGranted": bool(production.granted),
        "productionExternalFinancialWriteAllowed": bool(
            production_doc.get("externalFinancialWriteAllowed", False)
        ),
        "semanticModule": module,
    }


def evaluate_non_live(config_path: Path) -> dict[str, Any]:
    bound = verify_authority_binding(config_path)
    module = bound.pop("semanticModule")
    cfg = bound.pop("config")
    if bound["productionState"] != module.BLOCK_NOT_GRANTED:
        raise AuthorityWaistError("non-live lane requires provider ProductionAuthorization=BLOCK_NOT_GRANTED")
    if bound["productionExternalFinancialWriteAllowed"]:
        raise AuthorityWaistError("non-live lane requires externalFinancialWriteAllowed=false")
    if cfg.get("currentLane") != "NON_LIVE":
        raise AuthorityWaistError("authority binding currentLane must remain NON_LIVE")
    return {
        "standing": "AUTHORITY_WAIST_BOUND_NON_LIVE",
        **bound,
        "externalFinancialWritesAllowed": False,
        "effectAuthorityAvailableForExternalWrites": False,
    }


def evaluate_external_write(config_path: Path, envelope_path: Path | None) -> dict[str, Any]:
    bound = verify_authority_binding(config_path)
    module = bound.pop("semanticModule")
    cfg = bound.pop("config")

    # A semantic GRANTED string alone is intentionally insufficient to turn on money-moving effects.
    if cfg.get("externalFinancialWriteAdmission") != "ADMITTED":
        raise AuthorityWaistError("external financial write admission is not admitted")
    if cfg.get("liveGrantMechanism") != "ADMITTED":
        raise AuthorityWaistError("independent live grant mechanism is not admitted")
    # No live verifier exists yet. Even changing both admission strings in configuration
    # must not create a money-moving path without a new code-level admission.
    raise AuthorityWaistError(
        "external-write verifier is intentionally not implemented; code-level live admission is required"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--mode", choices=("non-live", "external-write"), default="non-live")
    parser.add_argument("--envelope", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.mode == "non-live":
        result = evaluate_non_live(args.config)
    else:
        result = evaluate_external_write(args.config, args.envelope)

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
