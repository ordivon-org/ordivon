from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from .admission import ReplayBinding, canonical_digest

_EFFECT_PROPOSAL_KIND = "ordivon.security.dwc-effect-proposal-r1"
_REVERSIBILITY = {"REVERSIBLE", "COMPENSATABLE", "IRREVERSIBLE"}


class EffectExecutionError(ValueError):
    pass


class TransportLost(RuntimeError):
    """Provider transport failed; provider may or may not have committed."""


class EffectProvider(Protocol):
    provider_ref: str
    reconciliation_authoritative: bool

    def reconcile(self, *, request_id: str, request_digest: str) -> dict[str, Any] | None: ...

    def apply(
        self, *, request: dict[str, Any], request_digest: str, proposal: Mapping[str, Any]
    ) -> dict[str, Any]: ...


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EffectExecutionError(f"{label} is required")
    return value


def _sha(value: object, label: str) -> str:
    text = _text(value, label)
    if not text.startswith("sha256:") or len(text) != 71:
        raise EffectExecutionError(f"{label} must be sha256:<64 hex>")
    return text


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EffectExecutionError(f"{label} must be an object")
    return value


def validate_effect_proposal(proposal: Mapping[str, Any]) -> None:
    if proposal.get("schemaVersion") != 1 or proposal.get("kind") != _EFFECT_PROPOSAL_KIND:
        raise EffectExecutionError("unsupported DWC effect proposal")
    _text(proposal.get("proposalRef"), "proposalRef")
    _text(proposal.get("requestId"), "requestId")
    _text(proposal.get("caseRef"), "caseRef")
    subject = _mapping(proposal.get("subject"), "subject")
    _text(subject.get("subjectRef"), "subject.subjectRef")
    _sha(subject.get("snapshotDigest"), "subject.snapshotDigest")
    _text(proposal.get("effectType"), "effectType")
    action = _mapping(proposal.get("action"), "action")
    _text(action.get("name"), "action.name")
    _text(action.get("targetRef"), "action.targetRef")
    _text(action.get("actuatorRef"), "action.actuatorRef")
    arguments = action.get("arguments", {})
    if not isinstance(arguments, Mapping):
        raise EffectExecutionError("action.arguments must be an object")

    metadata = _mapping(proposal.get("effectMetadata"), "effectMetadata")
    _text(metadata.get("commitPoint"), "effectMetadata.commitPoint")
    _text(metadata.get("replayIdentityRef"), "effectMetadata.replayIdentityRef")
    reversibility = _text(metadata.get("reversibility"), "effectMetadata.reversibility")
    if reversibility not in _REVERSIBILITY:
        raise EffectExecutionError("unsupported effectMetadata.reversibility")
    compensation_ref = metadata.get("compensationRef")
    if reversibility in {"REVERSIBLE", "COMPENSATABLE"}:
        _text(compensation_ref, "effectMetadata.compensationRef")
    elif compensation_ref is not None:
        raise EffectExecutionError("IRREVERSIBLE effect must not claim a compensationRef")
    _text(metadata.get("reconciliationOracleRef"), "effectMetadata.reconciliationOracleRef")
    _text(metadata.get("blastRadius"), "effectMetadata.blastRadius")

    obligation = _mapping(proposal.get("authorityObligation"), "authorityObligation")
    _text(obligation.get("id"), "authorityObligation.id")
    _sha(obligation.get("obligationDigest"), "authorityObligation.obligationDigest")


def project_openc2(proposal: Mapping[str, Any]) -> dict[str, Any]:
    """Optional OpenC2-shaped interoperability projection. No transport or authorization."""
    validate_effect_proposal(proposal)
    action = _mapping(proposal["action"], "action")
    result = {
        "action": action["name"],
        "target": {"target_ref": action["targetRef"]},
        "actuator": {"actuator_ref": action["actuatorRef"]},
        "args": dict(action.get("arguments", {})),
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.openc2-interoperability-projection-r1",
        "command": result,
        "transportPerformed": False,
        "authorizationDecisionIncluded": False,
        "truthBoundary": (
            "This is an optional Action-Target-Actuator-Arguments interoperability shape only. "
            "It is not transmitted and does not grant or imply effect authority."
        ),
    }


def compile_effect_request(
    proposal: Mapping[str, Any], authority_context: Mapping[str, Any]
) -> dict[str, Any]:
    validate_effect_proposal(proposal)
    actor_id = _text(authority_context.get("actorId"), "authority.actorId")
    authority_id = _text(authority_context.get("authorityId"), "authority.authorityId")
    zone_ref = _text(authority_context.get("zoneRef"), "authority.zoneRef")
    capability = _text(authority_context.get("capability"), "authority.capability")

    action = _mapping(proposal["action"], "action")
    payload = {
        "proposalRef": proposal["proposalRef"],
        "proposalDigest": canonical_digest(proposal),
        "caseRef": proposal["caseRef"],
        "subject": dict(proposal["subject"]),
        "action": {
            "name": action["name"],
            "targetRef": action["targetRef"],
            "actuatorRef": action["actuatorRef"],
            "arguments": dict(action.get("arguments", {})),
        },
        "effectMetadata": dict(proposal["effectMetadata"]),
        "authorityObligation": dict(proposal["authorityObligation"]),
    }
    request = {
        "schemaVersion": 1,
        "kind": "ordivon.security.range-effect-request",
        "requestId": proposal["requestId"],
        "actorId": actor_id,
        "authorityId": authority_id,
        "zoneRef": zone_ref,
        "capability": capability,
        "effectType": proposal["effectType"],
        "payload": payload,
    }
    request_digest = canonical_digest(request)
    policy_request = {
        "requestId": request["requestId"],
        "requestDigest": request_digest,
        "actorId": actor_id,
        "authorityId": authority_id,
        "zoneRef": zone_ref,
        "capability": capability,
        "effectType": proposal["effectType"],
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-effect-request-binding-r1",
        "proposalDigest": canonical_digest(proposal),
        "request": request,
        "requestDigest": request_digest,
        "policyRequest": policy_request,
        "openC2Projection": project_openc2(proposal),
        "truthBoundary": (
            "This carrier binds one exact DWC proposal to the existing Security effect-admission "
            "request shape. It does not contain an admission decision or execute an effect."
        ),
    }


def _validate_admission(prepared: Mapping[str, Any], admission: Mapping[str, Any]) -> None:
    if admission.get("kind") != "ordivon.security.range-effect-admission":
        raise EffectExecutionError("unsupported effect-admission kind")
    request = _mapping(prepared.get("request"), "prepared.request")
    expected = {
        "requestId": request["requestId"],
        "requestDigest": prepared["requestDigest"],
        "actorId": request["actorId"],
        "authorityId": request["authorityId"],
        "zoneRef": request["zoneRef"],
        "capability": request["capability"],
        "effectType": request["effectType"],
    }
    for key, value in expected.items():
        if admission.get(key) != value:
            raise EffectExecutionError(f"admission {key} does not bind the exact request")
    if not isinstance(admission.get("admitted"), bool):
        raise EffectExecutionError("admission.admitted must be boolean")
    _text(admission.get("reason"), "admission.reason")


def _validate_receipt(
    prepared: Mapping[str, Any], proposal: Mapping[str, Any], receipt: Mapping[str, Any]
) -> dict[str, Any]:
    request = _mapping(prepared["request"], "prepared.request")
    metadata = _mapping(proposal["effectMetadata"], "proposal.effectMetadata")
    if receipt.get("requestId") != request["requestId"]:
        raise EffectExecutionError("provider receipt requestId mismatch")
    if receipt.get("requestDigest") != prepared["requestDigest"]:
        raise EffectExecutionError("provider receipt requestDigest mismatch")
    if receipt.get("effectExecuted") is not True:
        raise EffectExecutionError("provider receipt must report effectExecuted=true")
    if receipt.get("worldEffectVerified") is not False:
        raise EffectExecutionError(
            "provider receipt must not self-claim worldEffectVerified"
        )
    _sha(receipt.get("stateDigestAfterWrite"), "receipt.stateDigestAfterWrite")
    _text(receipt.get("providerCommitRef"), "receipt.providerCommitRef")
    if receipt.get("commitPoint") != metadata["commitPoint"]:
        raise EffectExecutionError("provider receipt commitPoint mismatch")
    if receipt.get("replayIdentityRef") != metadata["replayIdentityRef"]:
        raise EffectExecutionError("provider receipt replayIdentityRef mismatch")
    if receipt.get("compensationRef") != metadata.get("compensationRef"):
        raise EffectExecutionError("provider receipt compensationRef mismatch")
    return dict(receipt)


@dataclass(slots=True)
class EffectExecutionCoordinator:
    replay_binding: ReplayBinding

    def execute(
        self,
        *,
        proposal: Mapping[str, Any],
        prepared: Mapping[str, Any],
        admission: Mapping[str, Any],
        provider: EffectProvider,
    ) -> dict[str, Any]:
        validate_effect_proposal(proposal)
        if prepared.get("proposalDigest") != canonical_digest(proposal):
            raise EffectExecutionError("prepared request targets a stale/different proposal")
        _validate_admission(prepared, admission)
        request = dict(_mapping(prepared["request"], "prepared.request"))
        bound_admission, admission_replayed = self.replay_binding.bind(
            request=request, admission=dict(admission)
        )
        if not bound_admission["admitted"]:
            return self._result(
                standing="NOT_ADMITTED",
                prepared=prepared,
                proposal=proposal,
                provider_ref=provider.provider_ref,
                admission=bound_admission,
                admission_replayed=admission_replayed,
                receipt=None,
                reconciliation_performed=False,
                retry_safe=False,
            )

        existing = provider.reconcile(
            request_id=request["requestId"], request_digest=prepared["requestDigest"]
        )
        if existing is not None:
            receipt = _validate_receipt(prepared, proposal, existing)
            return self._result(
                standing="RECONCILED_COMMITTED_UNVERIFIED",
                prepared=prepared,
                proposal=proposal,
                provider_ref=provider.provider_ref,
                admission=bound_admission,
                admission_replayed=admission_replayed,
                receipt=receipt,
                reconciliation_performed=True,
                retry_safe=False,
            )
        if admission_replayed and not provider.reconciliation_authoritative:
            return self._result(
                standing="AMBIGUOUS_RECONCILIATION_REQUIRED",
                prepared=prepared,
                proposal=proposal,
                provider_ref=provider.provider_ref,
                admission=bound_admission,
                admission_replayed=True,
                receipt=None,
                reconciliation_performed=True,
                retry_safe=False,
            )

        try:
            raw_receipt = provider.apply(
                request=request,
                request_digest=prepared["requestDigest"],
                proposal=proposal,
            )
        except TransportLost:
            recovered = provider.reconcile(
                request_id=request["requestId"], request_digest=prepared["requestDigest"]
            )
            if recovered is not None:
                receipt = _validate_receipt(prepared, proposal, recovered)
                return self._result(
                    standing="TRANSPORT_LOSS_RECONCILED_UNVERIFIED",
                    prepared=prepared,
                    proposal=proposal,
                    provider_ref=provider.provider_ref,
                    admission=bound_admission,
                    admission_replayed=admission_replayed,
                    receipt=receipt,
                    reconciliation_performed=True,
                    retry_safe=False,
                )
            return self._result(
                standing=(
                    "RETRY_SAFE_AFTER_AUTHORITATIVE_NO_COMMIT"
                    if provider.reconciliation_authoritative
                    else "AMBIGUOUS_RECONCILIATION_REQUIRED"
                ),
                prepared=prepared,
                proposal=proposal,
                provider_ref=provider.provider_ref,
                admission=bound_admission,
                admission_replayed=admission_replayed,
                receipt=None,
                reconciliation_performed=True,
                retry_safe=bool(provider.reconciliation_authoritative),
            )

        receipt = _validate_receipt(prepared, proposal, raw_receipt)
        return self._result(
            standing="COMMITTED_UNVERIFIED",
            prepared=prepared,
            proposal=proposal,
            provider_ref=provider.provider_ref,
            admission=bound_admission,
            admission_replayed=admission_replayed,
            receipt=receipt,
            reconciliation_performed=False,
            retry_safe=False,
        )

    @staticmethod
    def _result(
        *,
        standing: str,
        prepared: Mapping[str, Any],
        proposal: Mapping[str, Any],
        provider_ref: str,
        admission: Mapping[str, Any],
        admission_replayed: bool,
        receipt: Mapping[str, Any] | None,
        reconciliation_performed: bool,
        retry_safe: bool,
    ) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schemaVersion": 1,
            "kind": "ordivon.security.dwc-effect-execution-result-r1",
            "standing": standing,
            "proposalDigest": prepared["proposalDigest"],
            "requestId": prepared["request"]["requestId"],
            "requestDigest": prepared["requestDigest"],
            "providerRef": provider_ref,
            "admission": dict(admission),
            "admissionReplayed": admission_replayed,
            "reconciliationPerformed": reconciliation_performed,
            "retrySafeAfterReconciliation": retry_safe,
            "receipt": None if receipt is None else dict(receipt),
            "effectExecuted": bool(receipt is not None),
            "worldEffectVerified": False,
            "verifiedProtectionEstablished": False,
            "compensationAvailable": (
                proposal["effectMetadata"]["reversibility"]
                in {"REVERSIBLE", "COMPENSATABLE"}
            ),
            "compensationRef": proposal["effectMetadata"].get("compensationRef"),
            "truthBoundary": (
                "DW07 establishes at most exact admission/replay/provider-commit evidence. "
                "A provider receipt is not authoritative world truth. Consequence verification "
                "belongs to DW08 and remains false here."
            ),
        }
        value["resultDigest"] = canonical_digest(value)
        return value
