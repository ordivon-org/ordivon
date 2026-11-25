"""Readiness inquiry: retain evidence facets and falsifiable next checks.

Gateway never decides that an Owner actually executed a Job, that an Access
principal has a Security grant, or that a real Host mutation is complete.
The pure inquiry describes what was observed and which further *read-only*
or separately authorized checks would distinguish competing explanations.
No additional Owner RPC or automatic effect retry occurs in this module.
"""

from __future__ import annotations

from collections.abc import Mapping

from ..contracts import (
    CapabilityDescriptor,
    CapabilityRoute,
    ReadinessCheck,
    ReadinessFact,
    ReadinessInquiry,
    ReadinessOwnerStatusWitness,
)
from .readiness_evidence import OwnerConfiguration, OwnerObservation, _check, _fact, status_witness
from .readiness_runtime import append_runtime_facts
from .runtime_status import runtime_ready_target_observed, valid_runtime_status_envelope


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
        append_runtime_facts(
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
            configured = (
                response.get("structuredReleaseConfigured")
                if valid_runtime_status_envelope(response) and isinstance(response, dict)
                else None
            )
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
            append_runtime_facts(
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
            if (
                owner_configurations.get(owner_id, (False, None))[0]
                and error is None
                and runtime_ready_target_observed(response)
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
