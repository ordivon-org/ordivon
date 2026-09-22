from __future__ import annotations

import json
from pathlib import Path

from scripts.cognitive_circuit_r1 import compile_manifest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict:
    return json.loads((ROOT / "planning" / name).read_text(encoding="utf-8"))


def test_interactive_admission_keeps_authn_authz_and_owner_truth_separate() -> None:
    manifest = _load("admission-interactive-circuit-r1.json")
    compiled = compile_manifest(manifest)

    assert compiled["stageOrder"] == [
        "stage:transport",
        "stage:interactive-authn",
        "stage:ingress-verification",
        "stage:capability-authorization",
        "stage:gateway-route",
        "stage:natural-owner",
    ]
    assert "capability-scoped authorization" in " ".join(
        manifest["unresolvedAssumptions"]
    )
    assert any(
        gate["id"] == "gate:authn-authz-separation"
        for gate in manifest["gateRequirements"]
    )


def test_workload_admission_has_no_browser_or_human_stage() -> None:
    manifest = _load("admission-workload-circuit-r1.json")
    compiled = compile_manifest(manifest)

    stage_text = json.dumps(manifest["stages"], sort_keys=True).lower()
    assert "browser" in stage_text  # explicit negative responsibility is documented
    assert "without browser or human interaction" in stage_text
    assert all("callback" not in stage["id"] for stage in manifest["stages"])
    assert compiled["stageOrder"] == [
        "stage:workload-authn",
        "stage:security-authorization",
        "stage:gateway-route",
        "stage:natural-owner",
    ]
    assert any(
        "No production workload identity provider" in item
        for item in manifest["unresolvedAssumptions"]
    )


def test_both_profiles_converge_on_security_gateway_and_natural_owner() -> None:
    interactive = _load("admission-interactive-circuit-r1.json")
    workload = _load("admission-workload-circuit-r1.json")

    interactive_owners = [stage["ownerId"] for stage in interactive["stages"]]
    workload_owners = [stage["ownerId"] for stage in workload["stages"]]

    assert "security" in interactive_owners
    assert "security" in workload_owners
    assert interactive_owners[-2:] == ["gateway", "host"]
    assert workload_owners[-2:] == ["gateway", "host"]


def test_h2_debug_port_is_not_architectural_identity() -> None:
    for name in (
        "admission-interactive-circuit-r1.json",
        "admission-workload-circuit-r1.json",
    ):
        text = (ROOT / "planning" / name).read_text(encoding="utf-8")
        assert "28765" not in text
