from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from anc_canonical import canonical_digest
from ordivon_harness.api import AgentTurnRequest, DeepSeekSettings, DeepSeekTurnAdapter

MODELS = ("deepseek-flash", "deepseek-v4-pro")
PROBES_PER_MODEL = 2
EXPERIMENT_ID = "experiment:experimental-fabric-model-harness-pilot-r2-20260929"
PREFLIGHT_ID = "preflight:experimental-fabric-r2:deepseek-model-identity:v1"
COMPLETION_CONTRACT = {
    "mode": "structured-result-v1",
    "resultKind": "provider-model-identity-preflight",
    "resultSchema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"ack": {"type": "string"}},
        "required": ["ack"],
    },
}


def _sha(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def plan() -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-provider-model-identity-preflight-plan",
        "preflightId": PREFLIGHT_ID,
        "experimentId": EXPERIMENT_ID,
        "provider": "deepseek",
        "requestedModels": list(MODELS),
        "probesPerModel": PROBES_PER_MODEL,
        "totalProviderCalls": len(MODELS) * PROBES_PER_MODEL,
        "completionContractDigest": canonical_digest(COMPLETION_CONTRACT),
        "acceptance": {
            "withinRequestedLevel": "all probes must report one identical effectiveModelId and providerModel",
            "betweenRequestedLevels": "effectiveModelId must differ across requested treatment levels",
            "providerModelAgreement": "providerModel must equal effectiveModelId for every probe",
        },
        "nonClaims": [
            "Preflight establishes observed Provider routing identity only; it is not a model capability evaluation.",
            "Preflight probes are not calibration or inferential task observations and never enter R2 effect estimates.",
        ],
    }
    value["planDigest"] = canonical_digest(value)
    return value


def build_request(model: str, probe_index: int) -> AgentTurnRequest:
    if model not in MODELS:
        raise ValueError(f"unsupported R2 preflight model: {model}")
    if probe_index not in range(1, PROBES_PER_MODEL + 1):
        raise ValueError("preflight probe index is outside preregistered range")
    identity = f"{PREFLIGHT_ID}:{model}:{probe_index}"
    return AgentTurnRequest(
        harness_run_id=f"harness-run:{identity}",
        turn_id=f"turn:{identity}:1",
        sequence=1,
        assignment_id=f"assignment:{identity}",
        context_digest=_sha("context:" + identity),
        tool_catalog_digest=_sha("no-runtime-tools:r2-provider-identity-preflight"),
        messages=(
            {
                "role": "user",
                "content": (
                    "This is a provider identity preflight. Do not solve a task. "
                    "Immediately call submit_run_conclusion with status candidate_completed "
                    "and result {\"ack\":\"identity-observed\"}."
                ),
            },
        ),
        tools=(),
        remaining_budget={
            "modelCalls": 1,
            "toolCalls": 0,
            "totalTokens": 2048,
            "wallTimeMs": 60000,
        },
    )


def settings_for(base: DeepSeekSettings, model: str) -> DeepSeekSettings:
    return DeepSeekSettings(
        api_key=base.api_key,
        base_url=base.base_url,
        model=model,
        credential_scope_id=base.credential_scope_id,
        timeout_seconds=min(base.timeout_seconds, 60.0),
        max_response_bytes=base.max_response_bytes,
        max_output_tokens=min(base.max_output_tokens, 512),
    )


def qualify_probes(probes: list[dict[str, Any]], *, plan_value: dict[str, Any]) -> dict[str, Any]:
    expected_count = len(MODELS) * PROBES_PER_MODEL
    if len(probes) != expected_count:
        raise ValueError(f"expected {expected_count} Provider probes, got {len(probes)}")
    model_rows = []
    effective_by_requested: dict[str, str] = {}
    for requested in MODELS:
        rows = sorted(
            [row for row in probes if row.get("requestedModelId") == requested],
            key=lambda row: row.get("probeIndex", 0),
        )
        if len(rows) != PROBES_PER_MODEL:
            raise ValueError(f"expected {PROBES_PER_MODEL} probes for {requested}, got {len(rows)}")
        if [row.get("probeIndex") for row in rows] != list(range(1, PROBES_PER_MODEL + 1)):
            raise ValueError(f"probe indices differ for {requested}")
        effective = {row.get("effectiveModelId") for row in rows}
        provider_models = {row.get("providerModel") for row in rows}
        if None in effective or None in provider_models:
            raise ValueError(f"incomplete Provider model identity for {requested}")
        stable = len(effective) == 1 and len(provider_models) == 1 and effective == provider_models
        observed_effective = sorted(str(value) for value in effective)
        if stable:
            effective_by_requested[requested] = observed_effective[0]
        model_rows.append(
            {
                "requestedModelId": requested,
                "effectiveModelIds": observed_effective,
                "providerModelIds": sorted(str(value) for value in provider_models),
                "probeCount": len(rows),
                "systemFingerprints": sorted(
                    {str(row["systemFingerprint"]) for row in rows if row.get("systemFingerprint")}
                ),
                "standing": "PASS_DISTINCT_EFFECTIVE_IDENTITY" if stable else "FAIL_UNSTABLE_EFFECTIVE_IDENTITY",
                "probes": rows,
            }
        )
    within_pass = len(effective_by_requested) == len(MODELS)
    distinct_pass = within_pass and len(set(effective_by_requested.values())) == len(MODELS)
    standing = "PASS_DISTINCT_EFFECTIVE_IDENTITIES" if distinct_pass else "FAIL_COLLAPSED_OR_UNSTABLE_EFFECTIVE_IDENTITIES"
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-provider-model-identity-preflight",
        "preflightId": PREFLIGHT_ID,
        "experimentId": EXPERIMENT_ID,
        "provider": "deepseek",
        "planDigest": plan_value["planDigest"],
        "models": model_rows,
        "standing": standing,
        "effectiveIdentityMap": effective_by_requested,
        "nonClaims": [
            "Observed effective identity does not imply model quality or permanence of future Provider routing.",
            "The R2 campaign is invalid to start unless this exact preflight artifact has PASS standing and is bound into the preregistration/schedule.",
        ],
    }
    value["preflightDigest"] = canonical_digest(value)
    return value


def run_live() -> dict[str, Any]:
    plan_value = plan()
    base = DeepSeekSettings.from_secret_file()
    probes = []
    for requested in MODELS:
        adapter = DeepSeekTurnAdapter(
            settings_for(base, requested),
            completion_contract=COMPLETION_CONTRACT,
        )
        for probe_index in range(1, PROBES_PER_MODEL + 1):
            request = build_request(requested, probe_index)
            result = adapter.invoke(request)
            provider_model = result.usage.get("providerModel")
            if not isinstance(provider_model, str):
                raise RuntimeError("Provider probe omitted providerModel usage evidence")
            effective = result.effective_model_id
            if not isinstance(effective, str):
                raise RuntimeError("Provider probe omitted effectiveModelId")
            probes.append(
                {
                    "requestedModelId": result.model_id,
                    "effectiveModelId": effective,
                    "providerModel": provider_model,
                    "probeIndex": probe_index,
                    "requestDigest": request.digest,
                    "resultDigest": result.digest,
                    "rawResponseDigest": result.raw_response_digest,
                    "modelCallId": result.model_call_id,
                    "systemFingerprint": result.usage.get("systemFingerprint"),
                }
            )
    return qualify_probes(probes, plan_value=plan_value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-plan", type=Path)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    plan_value = plan()
    if args.write_plan:
        args.write_plan.parent.mkdir(parents=True, exist_ok=True)
        args.write_plan.write_text(json.dumps(plan_value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.run_live:
        print(json.dumps(plan_value, sort_keys=True))
        return 0
    if args.output is None:
        raise SystemExit("--output is required with --run-live")
    value = run_live()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(value, sort_keys=True))
    return 0 if value["standing"] == "PASS_DISTINCT_EFFECTIVE_IDENTITIES" else 3


if __name__ == "__main__":
    raise SystemExit(main())
