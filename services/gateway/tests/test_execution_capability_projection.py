"""Effect-free Runtime capability projection contract tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

from ordivon_gateway.capability_projection import execution_capability_descriptor
from ordivon_gateway.routes import default_routes


def route(name: str = "execution.linux"):
    return default_routes()[name]


@pytest.mark.parametrize("error", [None, "owner configuration missing"])
def test_unconfigured_never_claims_runtime_available(error: str | None) -> None:
    result = execution_capability_descriptor(
        route(),
        configured_at_gateway=False,
        description={"targets": [{"target": "local_linux", "available": True}]},
        observation_error=error,
    )
    assert not result.configured and not result.available
    assert result.observation_error == error


def test_runtime_observation_failure_preserves_unknown_as_unavailable() -> None:
    result = execution_capability_descriptor(
        route(),
        configured_at_gateway=True,
        description=None,
        observation_error="TimeoutError: upstream did not answer",
    )
    assert result.configured and not result.available
    assert result.observation_error.startswith("TimeoutError")


def test_missing_advertised_target_cannot_promote_other_owner() -> None:
    result = execution_capability_descriptor(
        route("execution.windows"),
        configured_at_gateway=True,
        description={"targets": [{"target": "local_linux", "available": True}]},
        observation_error=None,
    )
    assert not result.configured and not result.available
    assert result.observation_error == "owner did not advertise the routed execution target"


def test_linux_projection_preserves_provider_defined_profiles() -> None:
    result = execution_capability_descriptor(
        route(),
        configured_at_gateway=True,
        description={
            "node": {"nodeId": "node-1"},
            "targets": [
                {
                    "target": "local_linux",
                    "configured": True,
                    "available": True,
                    "executionProfiles": ["trusted_local", 1, "contained_local"],
                }
            ],
        },
        observation_error=None,
    )
    assert result.configured and result.available
    assert result.owner_node_id == "node-1"
    assert result.context_mode == "provider-defined-string"
    assert result.contexts == ["trusted_local", "contained_local"]


@pytest.mark.parametrize(
    ("attrs", "expected_mode", "expected"),
    [
        (
            {"windowsContexts": [{"identity": "active_user"}, "bad", {"identity": "service"}]},
            "provider-defined-json",
            [{"identity": "active_user"}, {"identity": "service"}],
        ),
        (
            {"windowsContexts": [], "windowsAuthorities": ["limited", 7, "elevated"]},
            "provider-defined-string",
            ["limited", "elevated"],
        ),
    ],
)
def test_windows_structured_context_precedence_and_copy(
    attrs: dict,
    expected_mode: str,
    expected: list,
) -> None:
    before = deepcopy(attrs)
    result = execution_capability_descriptor(
        route("execution.windows"),
        configured_at_gateway=True,
        description={
            "targets": [
                {"target": "windows_native", "configured": True, "available": True, **attrs}
            ]
        },
        observation_error=None,
    )
    assert result.context_mode == expected_mode
    assert result.contexts == expected
    assert attrs == before


def test_configured_does_not_imply_available() -> None:
    result = execution_capability_descriptor(
        route(),
        configured_at_gateway=True,
        description={
            "targets": [{"target": "local_linux", "configured": True, "available": False}]
        },
        observation_error=None,
    )
    assert result.configured
    assert not result.available
