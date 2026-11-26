"""Regression: Gateway effect policy is one shared implementation, not Run composition."""

import pytest

from ordivon_harness import gateway_execution_policy as policy
from ordivon_harness import plugin_gateway_effect, run_authority
from ordivon_harness.runtime_port import HarnessWorkspaceAdmissionUnavailable


def test_legacy_exports_reference_one_canonical_policy() -> None:
    assert run_authority.PluginGatewayExecutionGrant is policy.PluginGatewayExecutionGrant
    assert plugin_gateway_effect.PluginGatewayExecutionGrant is policy.PluginGatewayExecutionGrant
    assert run_authority.authorize_gateway_tool_call is policy.authorize_gateway_tool_call
    assert run_authority.require_gateway_workspace_effect is policy.require_gateway_workspace_effect
    assert run_authority.is_original_effect_authority is policy.is_original_effect_authority
    assert plugin_gateway_effect._forward_granted_timeout is policy._forward_granted_timeout


def test_gateway_grant_is_pure_contract_data() -> None:
    grant = policy.PluginGatewayExecutionGrant(
        capability="execution.linux",
        workspace_id="ws-original",
        executable_allowlist=("/usr/bin/rg",),
        env_allowlist=("LANG",),
        max_timeout_ms=1500,
    )
    assert grant.to_dict()["workspaceId"] == "ws-original"
    assert policy._forward_granted_timeout(1500, None) == 1500
    assert policy._forward_granted_timeout(1500, 500) == 500


def test_gateway_replay_requires_native_effect_admission() -> None:
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable):
        policy.require_gateway_workspace_effect(
            workspace_admission=None,
            admission_required=True,
            run_ref="harness-run",
            workspace_id="ws-original",
            grant_digest="sha256:example",
            request_id="request-original",
            replay=True,
        )


def test_gateway_original_effect_identity_is_strict() -> None:
    effect = object()
    issuer = object()
    assert policy.is_original_effect_authority(
        effect_client=effect,
        original_effect_client=effect,
        admission_port=issuer,
        original_admission_port=issuer,
        admission_required=True,
        original_admission_required=True,
    )
    assert not policy.is_original_effect_authority(
        effect_client=effect,
        original_effect_client=object(),
        admission_port=issuer,
        original_admission_port=issuer,
        admission_required=True,
        original_admission_required=True,
    )
