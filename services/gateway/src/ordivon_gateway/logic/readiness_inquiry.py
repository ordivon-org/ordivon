"""Readiness inquiry: retain evidence facets and falsifiable next checks.

Gateway never decides that an Owner actually executed a Job, that an Access
principal has a Security grant, or that a real Host mutation is complete.
The pure inquiry describes what was observed and which further *read-only*
or separately authorized checks would distinguish competing explanations.
No additional Owner RPC or automatic effect retry occurs in this module.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from ..contracts import (
    CapabilityDescriptor,
    CapabilityRoute,
    ReadinessCheck,
    ReadinessFact,
    ReadinessInquiry,
    ReadinessOwnerStatusWitness,
)
from .runtime_status import (
    valid_runtime_execution_context_inventory,
    valid_runtime_status_envelope,
    valid_runtime_target_inventory,
)

OwnerObservation = tuple[dict[str, Any] | None, str | None]
OwnerConfiguration = tuple[bool, str | None]


def status_witness(
    owner_id: str,
    tool_name: str,
    *,
    configured: bool,
    observation: OwnerObservation,
) -> ReadinessOwnerStatusWitness:
    """Bind native result bytes without returning unchecked/sensitive Owner JSON."""
    response, _error = observation
    if not configured:
        return ReadinessOwnerStatusWitness(
            owner_id=owner_id,
            tool_name=tool_name,  # type: ignore[arg-type]
            disposition="skipped_unconfigured",
        )
    if response is None:
        return ReadinessOwnerStatusWitness(
            owner_id=owner_id,
            tool_name=tool_name,  # type: ignore[arg-type]
            disposition="no_result",
        )
    try:
        payload = json.dumps(
            response,
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except TypeError, ValueError, OverflowError:
        return ReadinessOwnerStatusWitness(
            owner_id=owner_id,
            tool_name=tool_name,  # type: ignore[arg-type]
            disposition="no_result",
        )
    return ReadinessOwnerStatusWitness(
        owner_id=owner_id,
        tool_name=tool_name,  # type: ignore[arg-type]
        disposition="response_received",
        payload_digest="sha256:" + hashlib.sha256(payload).hexdigest(),
        payload_bytes=len(payload),
    )


def _fact(owner_id: str, predicate: str, state: str, source: str) -> ReadinessFact:
    return ReadinessFact(
        owner_id=owner_id,
        predicate=predicate,
        state=state,  # type: ignore[arg-type]
        source=source,
    )


def _check(
    direction: str,
    owner_id: str,
    action: str,
    predicate: str,
    *,
    request: dict[str, Any] | None = None,
    effect: str = "read_only",
) -> ReadinessCheck:
    return ReadinessCheck(
        direction=direction,  # type: ignore[arg-type]
        owner_id=owner_id,
        action=action,
        expected_evidence=predicate,
        request=request,
        effect=effect,  # type: ignore[arg-type]
    )


def _runtime_facts(
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
    unique_names = {row.get("target") for row in all_rows if isinstance(row.get("target"), str)}
    duplicates = len(unique_names) < len(all_rows)
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


def project_readiness_inquiry(
    descriptor: CapabilityDescriptor,
    route: CapabilityRoute,
    *,
    owner_configurations: Mapping[str, OwnerConfiguration],
    owner_observations: Mapping[str, OwnerObservation],
) -> ReadinessInquiry:
    """Produce a bounded evidence trail, not a second readiness classifier."""
    observations: list[ReadinessOwnerStatusWitness] = []
    facts: list[ReadinessFact] = []
    unresolved: list[str] = []
    candidates: list[str] = []
    checks: list[ReadinessCheck] = []
    scope = "owner_status"

    if route.category in {"execution", "release"}:
        owner_id = route.owner_id
        _runtime_facts(
            owner_id,
            route.execution_target,
            owner_configurations.get(owner_id, (False, "owner unconfigured")),
            owner_observations.get(owner_id, (None, None)),
            facts,
            unresolved,
            checks,
            candidates,
        )
        observations.append(
            status_witness(
                owner_id,
                "runtime.describe",
                configured=owner_configurations.get(owner_id, (False, None))[0],
                observation=owner_observations.get(owner_id, (None, None)),
            )
        )
        if route.category == "release":
            response, _error = owner_observations.get(owner_id, (None, None))
            configured = response.get("structuredReleaseConfigured") if response else None
            facts.append(
                _fact(
                    owner_id,
                    "owner.structured_release_configured",
                    ("supported" if configured else "refuted")
                    if type(configured) is bool
                    else "unobserved",
                    "runtime.describe",
                )
            )
            for predicate, action in (
                ("installed_gateway_release_tool", "inspect_installed_tools_list"),
                ("verified_principal_effect_permission", "inspect_current_security_decision"),
                ("runtime_release_admission_and_receipt", "runtime.release.get"),
            ):
                facts.append(_fact(owner_id, predicate, "unobserved", "not_inspected"))
                unresolved.append(f"{owner_id}: {predicate} not established by runtime.describe")
                checks.append(
                    _check(
                        "reverse",
                        owner_id,
                        action,
                        predicate,
                        effect="requires_authorized_context"
                        if action != "inspect_installed_tools_list"
                        else "read_only",
                    )
                )
        elif descriptor.readiness_state == "ready":
            facts.append(
                _fact(
                    owner_id,
                    "owner.physical_job_spawned",
                    "unobserved",
                    "status_read_is_not_execution",
                )
            )
            checks.append(
                _check(
                    "forward",
                    owner_id,
                    "workspace.exec",
                    "A particular authorized Job is accepted and physically observed",
                    effect="requires_authorized_context",
                )
            )
            checks.append(
                _check(
                    "reverse",
                    owner_id,
                    "execution.get",
                    "Existing OperationRef resolves to native Job/Attempt and process evidence",
                    effect="requires_authorized_context",
                )
            )

    elif route.category == "artifact":
        scope = "multi_owner_status"
        ready_owners = 0
        for owner_id in ("runtime.linux", "runtime.windows"):
            observations.append(
                status_witness(
                    owner_id,
                    "runtime.describe",
                    configured=owner_configurations.get(owner_id, (False, None))[0],
                    observation=owner_observations.get(owner_id, (None, None)),
                )
            )
            _runtime_facts(
                owner_id,
                None,
                owner_configurations.get(owner_id, (False, "owner unconfigured")),
                owner_observations.get(owner_id, (None, None)),
                facts,
                unresolved,
                checks,
                candidates,
            )
            response, error = owner_observations.get(owner_id, (None, None))
            if response is not None and error is None:
                targets = response.get("targets")
                if (
                    valid_runtime_target_inventory(targets)
                    and targets
                    and any(t["available"] and t["configured"] for t in targets)
                ):
                    ready_owners += 1
        facts.append(
            _fact(
                "runtime.dynamic",
                "owner.any_runtime_target_ready",
                "supported" if ready_owners else "unobserved",
                "runtime.describe",
            )
        )
        facts.append(
            _fact(
                "runtime.dynamic",
                "artifact.bytes_retrievable",
                "unobserved",
                "status_read_is_not_artifact_receipt",
            )
        )
        unresolved.append("Artifact bytes require an existing OperationRef and actual owner read")
        checks.append(
            _check(
                "reverse",
                "runtime.dynamic",
                "artifact.read",
                "Bytes returned by the producing Runtime for an existing operation",
                effect="requires_authorized_context",
            )
        )

    elif route.category == "continuity":
        observations.append(
            status_witness(
                "host",
                "host.status",
                configured=owner_configurations.get("host", (False, None))[0],
                observation=owner_observations.get("host", (None, None)),
            )
        )
        configured, _ = owner_configurations.get("host", (False, "owner unconfigured"))
        write_configured, _ = owner_configurations.get(
            "host.write", (False, "write endpoint unconfigured")
        )
        facts.append(
            _fact(
                "host",
                "gateway.host_write_endpoint_qualified",
                "supported" if write_configured else "refuted",
                "gateway.configuration",
            )
        )
        if not write_configured:
            unresolved.append(
                "Host write route is not qualified; a successful status read proves no write capability"
            )
            checks.append(
                _check(
                    "forward",
                    "host",
                    "inspect_owner_write_configuration",
                    "A separately authenticated Host write endpoint is available",
                )
            )
        facts.append(
            _fact(
                "host",
                "gateway.owner_endpoint_qualified",
                "supported" if configured else "refuted",
                "gateway.configuration",
            )
        )
        response, error = owner_observations.get("host", (None, None))
        valid = (
            isinstance(response, dict)
            and type(response.get("schemaVersion")) is int
            and response["schemaVersion"] == 3
            and response.get("kind") == "ordivon.host-status"
        )
        facts.append(
            _fact(
                "host",
                "host.status_envelope_valid",
                "supported" if valid else ("invalid" if response is not None else "unobserved"),
                "host.status",
            )
        )
        if not valid:
            unresolved.append("Host status and Work/Message continuity require direct confirmation")
            if error:
                candidates.append("Host status read may have timed out or failed at transport")
            checks.append(
                _check(
                    "reverse",
                    "host",
                    "host.status",
                    "Valid versioned Host response",
                    request={"detail": "summary"},
                )
            )
        facts.append(
            _fact(
                "host",
                "host.specific_work_read_authorized",
                "unobserved",
                "status_does_not_prove_access",
            )
        )
        checks.append(
            _check(
                "forward",
                "host",
                "work.get",
                "A caller-authorized exact Work read",
                effect="requires_authorized_context",
            )
        )

    elif route.category == "research":
        scope = "route_metadata"
        facts.append(
            _fact(
                "research.composition",
                "gateway.recipe_metadata_defined",
                "supported",
                "research.routes",
            )
        )
        facts.append(
            _fact(
                "research.composition",
                "research.provider_effect_ready",
                "unobserved",
                "route_metadata",
            )
        )
        unresolved.append("Research provider/tool and scientific completion are not observed")
        checks.append(
            _check(
                "forward",
                "skills",
                "capability.resolve",
                "Advisory exact Skill/recipe binding, not research completion",
                effect="requires_authorized_context",
            )
        )
        checks.append(
            _check(
                "reverse",
                "research.composition",
                "verify_domain_evidence",
                "Research Owner verifies method, data and output",
                effect="requires_authorized_context",
            )
        )
    else:
        scope = "route_metadata"
        facts.append(
            _fact(route.owner_id, "owner.readiness", "unobserved", "route_without_adapter")
        )
        unresolved.append("No Owner-specific readiness observer is implemented")

    # A status-only "ready" must not silently drop an unsatisfied proof
    # obligation. Do not create a second classifier: enumerate each existing
    # missing predicate in the same Owner/source evidence representation.
    for fact in facts:
        if fact.state in {"unobserved", "invalid", "contradictory"} and not any(
            fact.predicate in item for item in unresolved
        ):
            unresolved.append(
                f"{fact.owner_id}: {fact.predicate} remains {fact.state}"
                f" (source: {fact.source}); investigate with natural Owner evidence"
            )

    return ReadinessInquiry(
        scope=scope,
        observations=observations,
        facts=facts,
        unresolved_questions=unresolved,
        possible_explanations=candidates,
        next_checks=checks,
    )
