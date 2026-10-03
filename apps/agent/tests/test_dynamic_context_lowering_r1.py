from __future__ import annotations

import json

import pytest
from ordivon_composition import canonical_digest
from ordivon_harness.api import (
    AgentTurnResult,
    HarnessBoundReference,
    HarnessPrivacyPolicy,
)
from ordivon_harness.ordivon.model import AgentRunConclusion, ScriptedTurnAdapter

from ordivon_agent import (
    AgentRunLoweringError,
    compile_no_tool_agent_environment_refresh,
    compile_no_tool_agent_environment_seed,
    compile_no_tool_harness_binding,
    compile_no_tool_harness_run_contract,
    create_no_tool_harness_run,
    project_agent_cognitive_environment,
    project_agent_orientation_view,
)


def _digest(label: str) -> str:
    return canonical_digest({"dynamic-context": label})


def _manifest() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:dynamic-context-r1",
        "objectiveRef": {"id": "objective:dynamic-context", "digest": _digest("objective")},
        "methodBindings": [],
        "capabilityBindings": [],
        "stages": [
            {
                "id": "stage:agent-run",
                "ownerId": "agent-app",
                "responsibility": "Run one exact cognition-bound no-Tool task.",
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["objective", "environment"],
                "outputs": ["candidate"],
            }
        ],
        "edges": [],
        "gateRequirements": [],
        "unresolvedAssumptions": [],
        "nonClaims": [
            "Circuit compilation does not grant provider, Tool, execution, or completion authority."
        ],
    }


def _contract():
    return compile_no_tool_harness_run_contract(
        _manifest(),
        harness_run_id="harness-run:dynamic-context-r1",
        harness_implementation_id="ordivon-harness@dynamic-context",
        caller_id="caller:dynamic-context",
        caller_run_ref="work:test:dynamic-context",
        context_refs=(
            HarnessBoundReference(
                "context:dynamic-context",
                "context",
                _digest("context"),
            ),
        ),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        budget={
            "maxModelCalls": 4,
            "maxToolCalls": 0,
            "maxObservationBytes": 65536,
            "maxWallTimeMs": 10000,
            "maxTotalTokens": 10000,
            "maxModelRetries": 1,
            "maxToolCorrections": 2,
            "maxConclusionCorrections": 3,
            "maxObservationOnlyTurns": 4,
            "maxNoProgressTurns": 3,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "manifest:dynamic-context",
            "system-manifest",
            _digest("manifest"),
        ),
        created_at_ms=1000,
        privacy=HarnessPrivacyPolicy(
            content_policy="bounded-private-content",
            allow_model_content=True,
            allow_tool_content=False,
        ),
    )


def _adapter_ref() -> dict[str, str]:
    return {
        "id": "adapter-binding:dynamic-context",
        "digest": _digest("adapter"),
    }


def _work(revision: int = 1) -> dict:
    return {
        "workRef": "work:test:dynamic-context",
        "revision": revision,
        "snapshotDigest": _digest(f"work-{revision}"),
        "snapshot": {
            "objective": "maintain one owner-qualified dynamic cognition environment",
            "frontier": f"environment-frontier-{revision}",
            "established": ["R1 projection is non-authoritative"],
            "unresolved": ["fresh external owner state"],
            "constraints": ["context refresh never grants effect authority"],
            "nextActions": ["continue from the current selected environment"],
            "referenceRefs": ["runtime:workspace:dynamic-context"],
        },
    }


def _observation(version: int = 1) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.living-owner-observation",
        "subjectRef": "runtime:workspace:dynamic-context",
        "ownerRef": "ordivon.runtime",
        "observedAt": f"2026-10-03T11:4{version}:00+08:00",
        "operation": "workspace.get",
        "standing": f"available-v{version}",
        "evidenceRefs": [f"runtime:job:dynamic-context-{version}"],
        "attributes": {"version": version},
        "sourceRevision": f"source-{version}",
        "sourceDigest": _digest(f"owner-{version}"),
        "truthBoundary": "Runtime owner observation only",
    }


def _projection(*, work_revision: int = 1, owner_version: int = 1) -> dict:
    return project_agent_cognitive_environment(
        _work(work_revision),
        owner_observations=[_observation(owner_version)],
    )


def _binding(projection: dict, *, digest: str | None = None) -> dict:
    orientation = project_agent_orientation_view(projection)
    cognition_ref = {
        "id": "cognition:environment:dynamic-context-r1",
        "digest": digest if digest is not None else orientation["viewDigest"],
    }
    return compile_no_tool_harness_binding(
        _manifest(),
        _contract(),
        adapter_binding_ref=_adapter_ref(),
        cognition_binding_refs=(cognition_ref,),
    )


def _needs_input() -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id="model-call:dynamic-context-needs-input",
        model_id=ScriptedTurnAdapter.model_id,
        content="need fresh owner-qualified environment",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="needs_input",
            summary="Pause until the selected environment is refreshed.",
            unresolved_unknowns=("fresh external owner state",),
        ),
        usage={"inputTokens": 1, "outputTokens": 1},
        finish_reason="stop",
        raw_response_digest=_digest("needs-input"),
    )


def _completed() -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id="model-call:dynamic-context-completed",
        model_id=ScriptedTurnAdapter.model_id,
        content="candidate",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed",
            summary="Dynamic context continuation completed.",
            unresolved_unknowns=(),
        ),
        usage={"inputTokens": 1, "outputTokens": 1},
        finish_reason="stop",
        raw_response_digest=_digest("completed"),
    )


def test_orientation_binding_lowers_to_exact_environment_seed() -> None:
    projection = _projection()
    binding = _binding(projection)

    seed = compile_no_tool_agent_environment_seed(
        binding,
        projection,
        attempt_id="working-attempt:dynamic-context:a",
        basis="initial owner-qualified environment",
    )

    assert len(seed.sources) == 1
    item = seed.sources[0]
    orientation = project_agent_orientation_view(projection)
    assert item.slot == "environment"
    assert item.source.logical_ref == "cognition:environment:dynamic-context-r1"
    assert item.source.logical_generation == orientation["viewDigest"]
    rendered = json.loads(item.source.messages[0]["content"])
    assert rendered == orientation
    assert all(value is False for value in rendered["authority"].values())


def test_seed_rejects_nonmatching_exact_cognition_binding() -> None:
    projection = _projection()
    binding = _binding(projection, digest=_digest("other-orientation"))

    with pytest.raises(AgentRunLoweringError) as error:
        compile_no_tool_agent_environment_seed(
            binding,
            projection,
            attempt_id="working-attempt:dynamic-context:a",
            basis="initial owner-qualified environment",
        )
    assert error.value.code == "COGNITION_BINDING_MISMATCH"


def test_external_environment_rejects_harness_self_state() -> None:
    projection = _projection()
    binding = _binding(projection)
    projection["agentRun"] = {"kind": "self-state"}

    with pytest.raises(AgentRunLoweringError) as error:
        compile_no_tool_agent_environment_seed(
            binding,
            projection,
            attempt_id="working-attempt:dynamic-context:a",
            basis="must reject self-coupled environment",
        )
    assert error.value.code == "COGNITION_ENVIRONMENT_SELF_STATE_UNSUPPORTED"


def test_unchanged_selected_environment_requires_no_successor() -> None:
    projection = _projection()
    binding = _binding(projection)

    refresh = compile_no_tool_agent_environment_refresh(
        binding,
        projection,
        projection,
        next_attempt_id="working-attempt:dynamic-context:b",
        basis="no selected change",
    )
    assert refresh is None


def test_selected_environment_change_compiles_slot_local_refresh() -> None:
    previous = _projection()
    current = _projection(owner_version=2)
    binding = _binding(previous)

    refresh = compile_no_tool_agent_environment_refresh(
        binding,
        previous,
        current,
        next_attempt_id="working-attempt:dynamic-context:b",
        basis="fresh Runtime owner observation",
    )

    assert refresh is not None
    assert len(refresh.sources) == 1
    item = refresh.sources[0]
    assert item.slot == "environment"
    assert item.expected_source.logical_ref == item.replacement_source.logical_ref
    assert item.expected_source.logical_generation != item.replacement_source.logical_generation
    assert (
        item.replacement_source.logical_generation
        == project_agent_orientation_view(current)["viewDigest"]
    )


def test_dc1_dc2_dc3_compose_across_pause_refresh_and_resume(tmp_path) -> None:
    previous = _projection()
    current = _projection(work_revision=2, owner_version=2)
    binding = _binding(previous)
    contract = _contract()
    run = create_no_tool_harness_run(
        tmp_path,
        _manifest(),
        binding,
        contract,
        lambda _exact: ScriptedTurnAdapter((_needs_input(), _completed())),
        adapter_binding_ref=_adapter_ref(),
    )
    assert run.cognition_profile is not None

    seed = compile_no_tool_agent_environment_seed(
        binding,
        previous,
        attempt_id="working-attempt:dynamic-context:a",
        basis="initial selected environment",
    )
    first = run.run(
        ({"role": "user", "content": "Work from the selected environment."},),
        cognition_seed=seed,
    )
    assert first.paused is True

    refresh = compile_no_tool_agent_environment_refresh(
        binding,
        previous,
        current,
        next_attempt_id="working-attempt:dynamic-context:b",
        basis="selected environment advanced",
    )
    assert refresh is not None
    successor_digest = run.apply_cognition_refresh(refresh)
    assert successor_digest.startswith("sha256:")

    second = run.resume(
        additional_messages=(
            {"role": "user", "content": "Continue after the owner-qualified refresh."},
        )
    )
    assert second.paused is False
    assert second.loop_result.conclusion is not None
    assert second.loop_result.conclusion.status == "candidate_completed"
