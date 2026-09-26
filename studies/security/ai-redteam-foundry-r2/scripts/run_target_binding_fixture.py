#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry_r2 import EvaluationTargetBinding, ModelRequestBinding, RealizedTargetBinding  # noqa: E402


D = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64
D5 = "sha256:" + "5" * 64
D6 = "sha256:" + "6" * 64
D7 = "sha256:" + "7" * 64


def requested(model: ModelRequestBinding) -> EvaluationTargetBinding:
    return EvaluationTargetBinding(
        security_subject_ref="security-subject:synthetic-agent",
        security_subject_revision="rev-synthetic-001",
        target_kind="agent",
        model=model,
        harness_revision="harness-rev-001",
        harness_config_digest=D,
        instruction_bundle_digest=D2,
        tool_catalog_digest=D3,
        authority_surface_digest=D4,
        monitor_bundle_digest=D5,
        environment_digest=D6,
        adapter_id="synthetic.adapter",
        adapter_revision="adapter-rev-001",
        generation={"max_tokens": 2048, "temperature": 0.0, "reasoning_effort": "fixed"},
    )


def main() -> None:
    local = requested(ModelRequestBinding("local", "open-model", model_artifact_digest=D7))
    provider_versioned = requested(ModelRequestBinding("provider-a", "model-x", provider_model_revision="2026-09-01"))
    provider_opaque = requested(ModelRequestBinding("provider-b", "model-latest"))

    realized = [
        RealizedTargetBinding(local.digest, "open-model", D, model_artifact_digest=D7),
        RealizedTargetBinding(provider_versioned.digest, "model-x", D2, provider_model_revision="2026-09-01"),
        RealizedTargetBinding(provider_opaque.digest, "model-latest", D3, provider_system_fingerprint="fp_fixture_001"),
        RealizedTargetBinding(provider_opaque.digest, "model-latest", D4),
    ]

    report = {
        "schema": "ordivon.ai-redteam.target-binding-fixture.r2",
        "requested": [
            {"targetRef": local.target_ref, "digest": local.digest, "preRunIdentityStrength": local.model.pre_run_identity_strength},
            {"targetRef": provider_versioned.target_ref, "digest": provider_versioned.digest, "preRunIdentityStrength": provider_versioned.model.pre_run_identity_strength},
            {"targetRef": provider_opaque.target_ref, "digest": provider_opaque.digest, "preRunIdentityStrength": provider_opaque.model.pre_run_identity_strength},
        ],
        "realized": [
            {"digest": item.digest, "identityStrength": item.identity_strength, "claimScope": item.claim_scope}
            for item in realized
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
