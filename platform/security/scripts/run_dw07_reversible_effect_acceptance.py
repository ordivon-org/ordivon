#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ordivon_security_v2.admission import ReplayBinding, canonical_digest
from ordivon_security_v2.effect_execution import (
    EffectExecutionCoordinator,
    TransportLost,
    compile_effect_request,
)

OPA_IMAGE = (
    "docker.io/openpolicyagent/opa@"
    "sha256:9c5770a0023d56a11224b0514fec2e4e0247357db4392b955c1270fd49cb1f0f"
)


def proposal(request_id: str, *, value: str = "on") -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-effect-proposal-r1",
        "proposalRef": f"proposal:dw07:{request_id}",
        "requestId": request_id,
        "caseRef": "case:dw07:reversible-acceptance",
        "subject": {
            "subjectRef": "fixture:in-memory-flag",
            "snapshotDigest": "sha256:" + "1" * 64,
        },
        "effectType": "fixture.set-flag",
        "action": {
            "name": "set",
            "targetRef": "fixture:flag",
            "actuatorRef": "fixture:memory-provider",
            "arguments": {"value": value},
        },
        "effectMetadata": {
            "commitPoint": "provider-write",
            "replayIdentityRef": request_id,
            "reversibility": "REVERSIBLE",
            "compensationRef": "fixture:restore-previous-value",
            "reconciliationOracleRef": "fixture:provider-ledger",
            "blastRadius": "single-in-memory-key",
        },
        "authorityObligation": {
            "id": "authority:dw07-effect-execution",
            "obligationDigest": "sha256:" + "2" * 64,
        },
    }


def authority_context(*, capability: str = "fixture-write") -> dict[str, str]:
    return {
        "actorId": "actor:dw07-acceptance",
        "authorityId": "range-authority:dw07-acceptance",
        "zoneRef": "zone:fixture",
        "capability": capability,
    }


def authority() -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.security.range-authority",
        "authorityId": "range-authority:dw07-acceptance",
        "revision": "1",
        "actorId": "actor:dw07-acceptance",
        "zoneRefs": ["zone:fixture"],
        "capabilities": ["fixture-write"],
        "externalBoundary": "denied",
        "metadata": {"scope": "in-memory-acceptance-only"},
    }
    value["authorityDigest"] = canonical_digest(value)
    return value


def opa_decision(policy_dir: Path, prepared: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "actorIds": ["actor:dw07-acceptance"],
        "authorities": [authority()],
        "request": prepared["policyRequest"],
    }
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        input_path = root / "input.json"
        input_path.write_text(json.dumps(payload), encoding="utf-8")
        proc = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--user",
                "0",
                "-v",
                f"{policy_dir.resolve()}:/policies:ro",
                "-v",
                f"{root.resolve()}:/input:ro",
                OPA_IMAGE,
                "eval",
                "--format=json",
                "--data",
                "/policies/effect_admission.rego",
                "--input",
                "/input/input.json",
                "data.ordivon.security.v2.effect_admission.decision",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    value = json.loads(proc.stdout)
    return value["result"][0]["expressions"][0]["value"]


@dataclass
class MemoryProvider:
    provider_ref: str = "provider:dw07-memory-acceptance"
    reconciliation_authoritative: bool = True
    value: str = "off"
    apply_count: int = 0
    records: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    prior_values: dict[str, str] = field(default_factory=dict)
    transport_mode: str | None = None

    def reconcile(self, *, request_id: str, request_digest: str) -> dict[str, Any] | None:
        row = self.records.get((request_id, request_digest))
        return None if row is None else dict(row)

    def apply(
        self, *, request: dict[str, Any], request_digest: str, proposal: dict[str, Any]
    ) -> dict[str, Any]:
        if self.transport_mode == "before":
            raise TransportLost("transport lost before commit")
        self.apply_count += 1
        self.prior_values[request["requestId"]] = self.value
        self.value = proposal["action"]["arguments"]["value"]
        receipt = {
            "schemaVersion": 1,
            "kind": "fixture.provider-receipt",
            "requestId": request["requestId"],
            "requestDigest": request_digest,
            "effectExecuted": True,
            "worldEffectVerified": False,
            "stateDigestAfterWrite": canonical_digest({"value": self.value}),
            "providerCommitRef": f"commit:{request['requestId']}:{self.apply_count}",
            "commitPoint": proposal["effectMetadata"]["commitPoint"],
            "replayIdentityRef": proposal["effectMetadata"]["replayIdentityRef"],
            "compensationRef": proposal["effectMetadata"]["compensationRef"],
        }
        self.records[(request["requestId"], request_digest)] = dict(receipt)
        if self.transport_mode == "after":
            raise TransportLost("transport lost after commit")
        return receipt

    def compensate(self, request_id: str) -> dict[str, Any]:
        previous = self.prior_values[request_id]
        self.value = previous
        return {
            "compensationRef": "fixture:restore-previous-value",
            "standing": "COMPENSATED",
            "stateDigestAfterCompensation": canonical_digest({"value": self.value}),
        }


def run_case(
    *,
    policy_dir: Path,
    request_id: str,
    provider: MemoryProvider,
    coordinator: EffectExecutionCoordinator,
    value: str = "on",
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    p = proposal(request_id, value=value)
    prepared = compile_effect_request(p, authority_context())
    decision = opa_decision(policy_dir, prepared)
    result = coordinator.execute(
        proposal=p,
        prepared=prepared,
        admission=decision,
        provider=provider,
    )
    return p, prepared, result


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    policy_dir = repo / "platform/security/policies"
    out = repo / "platform/security/evidence/acceptance"
    out.mkdir(parents=True, exist_ok=True)

    normal_provider = MemoryProvider()
    coordinator = EffectExecutionCoordinator(ReplayBinding())
    _, normal_prepared, normal = run_case(
        policy_dir=policy_dir,
        request_id="effect-request:dw07-normal",
        provider=normal_provider,
        coordinator=coordinator,
    )
    replay = coordinator.execute(
        proposal=proposal("effect-request:dw07-normal"),
        prepared=normal_prepared,
        admission=opa_decision(policy_dir, normal_prepared),
        provider=normal_provider,
    )
    compensation = normal_provider.compensate("effect-request:dw07-normal")

    transport_provider = MemoryProvider(transport_mode="after")
    _, _, transport = run_case(
        policy_dir=policy_dir,
        request_id="effect-request:dw07-transport-after",
        provider=transport_provider,
        coordinator=EffectExecutionCoordinator(ReplayBinding()),
    )

    changed_error = None
    try:
        changed = proposal("effect-request:dw07-normal", value="different")
        changed_prepared = compile_effect_request(changed, authority_context())
        coordinator.execute(
            proposal=changed,
            prepared=changed_prepared,
            admission=opa_decision(policy_dir, changed_prepared),
            provider=normal_provider,
        )
    except ValueError as exc:
        changed_error = str(exc)

    denied_prepared = compile_effect_request(
        proposal("effect-request:dw07-denied"),
        authority_context(capability="not-granted"),
    )
    denied_decision = opa_decision(policy_dir, denied_prepared)
    denied_provider = MemoryProvider()
    denied = EffectExecutionCoordinator(ReplayBinding()).execute(
        proposal=proposal("effect-request:dw07-denied"),
        prepared=denied_prepared,
        admission=denied_decision,
        provider=denied_provider,
    )

    assert normal["standing"] == "COMMITTED_UNVERIFIED"
    assert replay["standing"] == "RECONCILED_COMMITTED_UNVERIFIED"
    assert normal_provider.apply_count == 1
    assert compensation["standing"] == "COMPENSATED"
    assert normal_provider.value == "off"
    assert transport["standing"] == "TRANSPORT_LOSS_RECONCILED_UNVERIFIED"
    assert transport_provider.apply_count == 1
    assert changed_error and "reused with different content" in changed_error
    assert denied_decision["admitted"] is False
    assert denied["standing"] == "NOT_ADMITTED"
    assert denied_provider.apply_count == 0

    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dw07-reversible-effect-acceptance-r1",
        "standing": "PASS",
        "opaImage": OPA_IMAGE,
        "normalCommit": normal,
        "exactReplay": replay,
        "compensation": compensation,
        "transportLossAfterCommit": transport,
        "changedContentSameIdentityError": changed_error,
        "deniedAdmission": denied,
        "providerApplyCounts": {
            "normalAndReplay": normal_provider.apply_count,
            "transportAfterCommit": transport_provider.apply_count,
            "denied": denied_provider.apply_count,
        },
        "nonClaims": [
            "All provider effects are in-memory fixture writes; no OS, network, Security or external system is changed.",
            "OPA admission is permission only and does not prove execution or consequence.",
            "Provider receipts keep worldEffectVerified=false.",
            "Compensation proof is fixture-provider capability, not a claim that every production effect is reversible.",
            "Transport-loss recovery demonstrates reconciliation-first semantics and no blind retry.",
            "No verified protection or domain acceptance is established.",
        ],
    }
    evidence["evidenceDigest"] = canonical_digest(evidence)
    path = out / "dw07-reversible-effect-r1-20261001.json"
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "standing": evidence["standing"],
                "evidenceDigest": evidence["evidenceDigest"],
                "normalStanding": normal["standing"],
                "replayStanding": replay["standing"],
                "transportStanding": transport["standing"],
                "deniedStanding": denied["standing"],
                "normalApplyCount": normal_provider.apply_count,
                "transportApplyCount": transport_provider.apply_count,
                "deniedApplyCount": denied_provider.apply_count,
                "compensationStanding": compensation["standing"],
                "worldEffectVerified": normal["worldEffectVerified"],
                "verifiedProtectionEstablished": normal["verifiedProtectionEstablished"],
                "output": str(path.relative_to(repo)),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
