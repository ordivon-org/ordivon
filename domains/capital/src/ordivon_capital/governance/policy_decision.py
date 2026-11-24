"""Effect-side Governance: execution lane admission, never financial risk math."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .decision_inputs import (
    DECISION_IMPLEMENTATION,
    PolicyDecisionError,
    _load_json,
    _require_local_implementation,
    _resolve,
)


def _execution_decision(*, current_lane: Any, write_policy: dict[str, Any]) -> dict[str, bool]:
    allow_non_live = (
        current_lane == "NON_LIVE"
        and write_policy.get("state") == "NOT_ADMITTED"
        and write_policy.get("externalFinancialWriteAllowed") is False
        and write_policy.get("providerWriteCapabilityBound") is False
        and write_policy.get("effectVerifier") != "IMPLEMENTED_BOUND_CURRENT"
    )
    allow_external_write = (
        current_lane == "EXTERNAL_WRITE"
        and write_policy.get("state") == "ADMITTED"
        and write_policy.get("externalFinancialWriteAllowed") is True
        and write_policy.get("providerWriteCapabilityBound") is True
        and write_policy.get("effectVerifier") == "IMPLEMENTED_BOUND_CURRENT"
    )
    if allow_non_live and allow_external_write:
        raise PolicyDecisionError("mutually incompatible lane decisions")
    return {
        "allowNonLive": allow_non_live,
        "allowExternalWrite": allow_external_write,
    }


def evaluate_execution_policy(repo: Path, config_path: Path) -> dict[str, Any]:
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.capital.governance.execution-policy":
        raise PolicyDecisionError("unexpected execution-policy kind")
    _require_local_implementation(cfg)

    write_doc = _load_json(_resolve(repo, cfg["externalWritePolicyInputContract"]))
    if write_doc.get("kind") != "ordivon.capital.governance.external-write-policy-input":
        raise PolicyDecisionError("external-write policy input missing")

    decision = _execution_decision(
        current_lane=cfg.get("currentLane"),
        write_policy=write_doc,
    )
    return {
        "decisionImplementation": DECISION_IMPLEMENTATION,
        "currentLane": cfg.get("currentLane"),
        **decision,
        "externalWritePolicyStanding": write_doc.get("state"),
        "externalWriteVerifier": write_doc.get("effectVerifier", "NOT_IMPLEMENTED"),
        "providerWriteCapabilityBound": bool(write_doc.get("providerWriteCapabilityBound", False)),
        "externalFinancialWriteAllowedByContract": bool(
            write_doc.get("externalFinancialWriteAllowed", False)
        ),
    }


def enforce_non_live(repo: Path, config_path: Path) -> dict[str, Any]:
    decision = evaluate_execution_policy(repo, config_path)
    if not decision["allowNonLive"]:
        raise PolicyDecisionError("policy denied non-live execution lane")
    return {
        "standing": "NON_LIVE_POLICY_ALLOWED",
        **decision,
        "externalFinancialWritesAllowed": False,
    }


def enforce_external_write(repo: Path, config_path: Path) -> dict[str, Any]:
    decision = evaluate_execution_policy(repo, config_path)
    if not decision["allowExternalWrite"]:
        raise PolicyDecisionError("policy denied external financial write")
    raise PolicyDecisionError("external-write execution path is not implemented")


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
