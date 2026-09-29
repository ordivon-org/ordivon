#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry_r4 import (  # noqa: E402
    ExperimentEnvironmentSpec,
    IsolationVector,
    ResourceBudget,
    SandboxProviderBinding,
    admit_environment,
)

D = lambda c: "sha256:" + c * 64


def provider() -> SandboxProviderBinding:
    return SandboxProviderBinding(
        provider_id="sandbox-provider:fixture",
        provider_revision="fixture-r1",
        provider_kind="fixture",
        provider_evidence_digest=D("7"),
    )


def make(name: str, threat_class: str, isolation: IsolationVector, network_budget: int) -> ExperimentEnvironmentSpec:
    return ExperimentEnvironmentSpec(
        environment_id=name,
        threat_class=threat_class,
        base_image_digest=D("1"),
        synthetic_world_digest=D("2"),
        tool_surface_digest=D("3"),
        observer_spec_digest=D("4"),
        isolation=isolation,
        budget=ResourceBudget(300, 240, 2048, 4096, 256, network_budget),
        provider=provider(),
    )


def main() -> None:
    contained_local = make(
        "fixture:contained-local",
        "hostile_code",
        IsolationVector(
            "separate_process_tree",
            "shared",
            "restricted_host",
            "none",
            "none",
            "explicit_allowlist",
            "none",
            "resettable",
            "same_trust_domain",
        ),
        0,
    )
    synthetic_agent = make(
        "fixture:synthetic-agent",
        "synthetic_agent",
        IsolationVector(
            "separate_process_tree",
            "shared",
            "synthetic",
            "simulated_internet",
            "synthetic_only",
            "none",
            "synthetic_only",
            "resettable",
            "independent",
        ),
        500_000,
    )
    hostile_vm = make(
        "fixture:hostile-vm",
        "hostile_code",
        IsolationVector(
            "vm",
            "separate_guest_kernel",
            "disposable_overlay",
            "simulated_internet",
            "synthetic_only",
            "explicit_allowlist",
            "policy_proxy",
            "disposable",
            "independent",
        ),
        1_000_000,
    )
    open_world_vm = make(
        "fixture:open-world-vm",
        "hostile_code",
        IsolationVector(
            "vm",
            "separate_guest_kernel",
            "disposable_overlay",
            "full_egress",
            "host_ambient",
            "host_default",
            "direct_open_world",
            "persistent",
            "self_reported",
        ),
        10_000_000,
    )

    report = {
        "schema": "ordivon.ai-redteam.sandbox-contract-fixture.r4",
        "cases": [
            {"name": item.environment_id, "threatClass": item.threat_class, "admission": admit_environment(item).to_dict()}
            for item in (contained_local, synthetic_agent, hostile_vm, open_world_vm)
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
