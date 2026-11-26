"""Runtime-specific readiness evidence; no transport or permission checks."""

from __future__ import annotations

from ..contracts import ReadinessCheck, ReadinessFact
from .readiness_evidence import OwnerConfiguration, OwnerObservation, _check, _fact
from .runtime_status import (
    valid_runtime_execution_context_inventory,
    valid_runtime_status_envelope,
    valid_runtime_target_inventory,
)


def append_runtime_facts(
    owner_id: str,
    target_name: str | None,
    configured: OwnerConfiguration,
    observed: OwnerObservation,
    facts: list[ReadinessFact],
    unresolved: list[str],
    checks: list[ReadinessCheck],
    candidates: list[str],
) -> None:
    """Inspect each raw observation as separate predicates, never Python truthiness."""
    gateway_configured, _config_error = configured
    facts.append(
        _fact(
            owner_id,
            "gateway.owner_endpoint_qualified",
            "supported" if gateway_configured else "refuted",
            "gateway.configuration",
        )
    )
    response, error = observed
    if not gateway_configured:
        facts.append(_fact(owner_id, "owner.status_observed", "unobserved", "runtime.describe"))
        unresolved.append(f"{owner_id}: natural Owner readiness not observed")
        candidates.append(f"{owner_id}: route or Owner credential is not configured at Gateway")
        checks.append(
            _check(
                "forward",
                owner_id,
                "inspect_owner_configuration",
                "Gateway endpoint and machine identity exist",
            )
        )
        return

    if response is None:
        facts.append(_fact(owner_id, "owner.status_observed", "unobserved", "runtime.describe"))
        unresolved.append(f"{owner_id}: Runtime status unavailable; physical readiness unverified")
        if error and error.startswith("TimeoutError:"):
            candidates.extend(
                (
                    f"{owner_id}: status exceeded observation deadline",
                    f"{owner_id}: MCP connection or negotiation stalled",
                )
            )
        elif error:
            candidates.append(f"{owner_id}: owner transport or protocol may have failed")
        else:
            candidates.append(f"{owner_id}: no Runtime status result was obtained")
        checks.append(
            _check(
                "reverse",
                owner_id,
                "runtime.describe",
                "Independent owner status response with target inventory",
                request={"schemaVersion": 1},
            )
        )
        return

    facts.append(_fact(owner_id, "owner.status_observed", "supported", "runtime.describe"))
    if not valid_runtime_status_envelope(response):
        facts.append(_fact(owner_id, "owner.status_envelope_valid", "invalid", "runtime.describe"))
        unresolved.append(f"{owner_id}: Runtime status envelope is missing/invalid version 1")
        checks.append(
            _check(
                "reverse",
                owner_id,
                "runtime.describe",
                "Native Runtime schemaVersion=1 status contract",
                request={"schemaVersion": 1},
            )
        )
        return
    facts.append(_fact(owner_id, "owner.status_envelope_valid", "supported", "runtime.describe"))
    targets = response.get("targets")
    if not isinstance(targets, list):
        facts.append(_fact(owner_id, "owner.target_inventory_valid", "invalid", "runtime.describe"))
        unresolved.append(f"{owner_id}: target inventory is malformed; readiness unverified")
        checks.append(
            _check(
                "reverse",
                owner_id,
                "runtime.describe",
                "Versioned owner target inventory is well formed",
                request={"schemaVersion": 1},
            )
        )
        return

    facts.append(_fact(owner_id, "owner.target_inventory_is_list", "supported", "runtime.describe"))
    if not valid_runtime_target_inventory(targets):
        facts.append(
            _fact(owner_id, "owner.target_inventory_consistent", "invalid", "runtime.describe")
        )
        unresolved.append(f"{owner_id}: strict target inventory is invalid")

    all_rows = [item for item in targets if isinstance(item, dict)]
    # Inventory identity uniqueness is a *global* Owner contract, even if
    # this capability uses only one selected target. A duplicate sibling
    # target must not be hidden by an otherwise healthy selected target.
    valid_names = [
        row["target"]
        for row in all_rows
        if isinstance(row.get("target"), str) and row["target"].strip()
    ]
    duplicates = len(set(valid_names)) < len(valid_names)
    if target_name is None:
        # Artifact is dynamic; preserve all rows while never selecting an
        # arbitrary duplicated target as the preferred evidence witness.
        matches = all_rows
    else:
        matches = [row for row in all_rows if row.get("target") == target_name]
        facts.append(
            _fact(
                owner_id,
                f"owner.target_advertised:{target_name}",
                "supported" if matches else "refuted",
                "runtime.describe",
            )
        )
    if duplicates:
        facts.append(
            _fact(owner_id, "owner.target_identity_unique", "contradictory", "runtime.describe")
        )
        unresolved.append(f"{owner_id}: duplicate target identities; select no preferred duplicate")
        candidates.append(f"{owner_id}: Owner target inventory may violate uniqueness")
    elif target_name is not None and not matches:
        unresolved.append(f"{owner_id}: intended target absent from advertised inventory")
        candidates.append(f"{owner_id}: route target and Owner inventory may disagree")

    for index, target in enumerate(matches[:16]):
        label = target_name or str(target.get("target", f"index-{index}"))[:64]
        if target_name is None and not isinstance(target.get("target"), str):
            facts.append(
                _fact(owner_id, f"owner.target_identity:{label}", "invalid", "runtime.describe")
            )
        for field in ("configured", "available"):
            value = target.get(field)
            facts.append(
                _fact(
                    owner_id,
                    f"owner.target_{field}:{label}",
                    ("supported" if value else "refuted") if type(value) is bool else "invalid",
                    "runtime.describe",
                )
            )
        if target.get("available") is True and target.get("configured") is False:
            facts.append(
                _fact(
                    owner_id,
                    f"owner.target_consistent:{label}",
                    "contradictory",
                    "runtime.describe",
                )
            )
            unresolved.append(f"{owner_id}: reported available=True with configured=False")
        if not valid_runtime_execution_context_inventory(target, label):
            facts.append(
                _fact(owner_id, f"owner.context_inventory:{label}", "invalid", "runtime.describe")
            )
            unresolved.append(f"{owner_id}: invalid context inventory {label}")

    if len(matches) > 16:
        unresolved.append(f"{owner_id}: additional target rows omitted from bounded inquiry")
    if (
        (target_name is not None and not matches)
        or duplicates
        or any(f.state in {"invalid", "contradictory"} and f.owner_id == owner_id for f in facts)
    ):
        checks.append(
            _check(
                "reverse",
                owner_id,
                "runtime.describe",
                "Confirm target identity and strict boolean/status contract",
                request={"schemaVersion": 1},
            )
        )
