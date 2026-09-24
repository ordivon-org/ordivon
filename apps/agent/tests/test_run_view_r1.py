from __future__ import annotations

import copy

import pytest

from ordivon_agent import (
    AgentRunViewError,
    project_harness_run_view_projection,
)


def _explain(status: str = "created") -> dict[str, object]:
    durable = {
        "harnessRunId": "harness-run:view-r1",
        "contractDigest": "sha256:" + "1" * 64,
        "contractObjectDigest": "sha256:" + "2" * 64,
        "callerId": "caller:view-r1",
        "callerRunRef": "caller-run:view-r1",
        "status": status,
        "revision": 3,
        "createdAtMs": 100,
        "updatedAtMs": 200,
        "terminalEventId": None,
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.harness-process-composition-projection",
        "truthRole": "derived-read-only-composition-projection",
        "run": {
            "harnessRunId": "harness-run:view-r1",
            "contractDigest": "sha256:" + "1" * 64,
            "providerId": "provider:fixture",
            "adapterId": "adapter:fixture",
            "requestedModelId": "model:fixture",
            "toolCatalogDigest": "sha256:" + "3" * 64,
            "toolGrantDigest": "sha256:" + "4" * 64,
            "privacy": {},
            "budget": {},
        },
        "processLocal": {
            "adapter": {"supplied": True},
            "cognition": {"supplied": False},
            "executionBinding": {"supplied": False},
            "runtimeClient": {"supplied": False},
            "customToolBridge": {"supplied": False},
        },
        "proofBoundary": "fixture",
        "durableRun": durable,
    }


@pytest.mark.parametrize(
    ("native", "product"),
    [
        ("created", "ready"),
        ("active", "running"),
        ("paused", "attention_required"),
        ("stopped", "stopped"),
        ("completed", "run_finished"),
        ("failed", "failed"),
    ],
)
def test_run_view_groups_durable_status_without_reinterpreting_truth(
    native: str, product: str
) -> None:
    view = project_harness_run_view_projection(_explain(native))

    assert view["state"] == product
    assert view["nativeStatus"] == native
    assert view["semanticAcceptance"] == {
        "establishedByHarness": False,
        "state": "not-established",
    }
    assert view["externalLiveness"] == "not-probed"


def test_run_finished_never_becomes_task_completed() -> None:
    view = project_harness_run_view_projection(_explain("completed"))

    assert view["state"] == "run_finished"
    assert "completed" not in {view["state"]}
    assert view["semanticAcceptance"]["establishedByHarness"] is False


def test_projection_fails_closed_on_cross_run_mix() -> None:
    value = copy.deepcopy(_explain())
    value["durableRun"]["harnessRunId"] = "harness-run:other"

    with pytest.raises(AgentRunViewError, match="identities differ"):
        project_harness_run_view_projection(value)


def test_projection_fails_closed_on_unknown_harness_status() -> None:
    with pytest.raises(AgentRunViewError, match="unsupported Harness Run status"):
        project_harness_run_view_projection(_explain("mystery"))


def test_product_view_module_imports_only_public_harness_surface() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "src" / "ordivon_agent" / "run_view_r1.py"
    ).read_text(encoding="utf-8")

    assert "from ordivon_harness.api import HarnessAgentRun" in source
    for forbidden in (
        "ordivon_harness.store",
        "ordivon_harness.sqlite_store",
        "ordivon_harness.independent_cli",
        "ordivon_harness.ordivon",
    ):
        assert forbidden not in source
