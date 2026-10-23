from __future__ import annotations

import json
from pathlib import Path
import tempfile

from anc_canonical import canonical_digest

from ordivon_harness.agent_plugin import AgentPluginComposition
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.core_contracts import (
    HarnessBoundReference,
    HarnessPrivacyPolicy,
    HarnessRunContract,
)
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentToolCall,
    AgentTurnResult,
    ScriptedTurnAdapter,
)
from ordivon_harness.plugin_mcp import PluginMcpObservationBridge
from ordivon_harness.standalone import (
    HarnessCognitionProfile,
    HarnessCognitionSeed,
    HarnessCognitionSeedSource,
)


class FixedClock:
    def __init__(self) -> None:
        self.value = 10_000

    def __call__(self) -> int:
        self.value += 1
        return self.value


class GatewayFixtureClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def list_tools(self):
        return (
            {
                "name": "system.describe",
                "description": "Describe the public Ordivon system surface.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
            {
                "name": "execution.submit",
                "description": "Effectful execution; must not enter H1.",
                "inputSchema": {"type": "object"},
            },
        )

    def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        if name != "system.describe":
            raise AssertionError(f"unexpected effectful call: {name}")
        return False, {
            "schemaVersion": 1,
            "kind": "ordivon.system-description",
            "gateway": {"truthRole": "non-authoritative"},
        }


def _write_plugin(root: Path) -> None:
    (root / "plugin.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": "ordivon-control-plane",
                "version": "0.2.0",
            }
        ),
        encoding="utf-8",
    )
    (root / "mcp.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
                "mcpServers": {
                    "ordivon-gateway": {
                        "type": "streamable-http",
                        "url": "https://gateway-mcp.ordivon.com/mcp",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    skill = root / "skills" / "method-router"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: method-router\n---\nUse the smallest standards-backed method set.\n",
        encoding="utf-8",
    )


def _digest(label: str) -> str:
    return canonical_digest({"harness-plugin-e2e": label})


def _contract(
    bridge: PluginMcpObservationBridge,
) -> HarnessRunContract:
    return HarnessRunContract(
        harness_run_id="harness-run:plugin-e2e",
        harness_implementation_id="ordivon-harness@plugin-h1",
        caller_id="caller:plugin-e2e",
        caller_run_ref="trial:plugin-e2e",
        objective_ref=HarnessBoundReference(
            "objective:plugin-e2e", "objective", _digest("objective")
        ),
        context_refs=(HarnessBoundReference("context:plugin-e2e", "context", _digest("context")),),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=bridge.catalog_digest,
        tool_grant_digest=bridge.grant_digest,
        budget={
            "maxModelCalls": 2,
            "maxToolCalls": 1,
            "maxObservationBytes": 65_536,
            "maxWallTimeMs": 30_000,
            "maxTotalTokens": 4_096,
            "maxModelRetries": 0,
            "maxToolCorrections": 1,
            "maxConclusionCorrections": 1,
            "maxObservationOnlyTurns": 2,
            "maxNoProgressTurns": 2,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "manifest:plugin-e2e", "system-manifest", _digest("manifest")
        ),
        created_at_ms=10_000,
        privacy=HarnessPrivacyPolicy(
            content_policy="bounded-private-content",
            allow_model_content=True,
            allow_tool_content=True,
        ),
    )


def test_harness_agent_run_consumes_plugin_skill_and_gateway_observation_tool() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        plugin_root = root / "plugin"
        plugin_root.mkdir()
        _write_plugin(plugin_root)
        plugin = AgentPluginComposition.load(plugin_root)

        gateway = GatewayFixtureClient()
        bridge = PluginMcpObservationBridge(
            plugin.mcp("ordivon-gateway"),
            gateway,
            allowed_tools=("system.describe",),
        )
        contract = _contract(bridge)

        tool_turn = AgentTurnResult(
            model_call_id="model-call:plugin-tool",
            model_id=ScriptedTurnAdapter.model_id,
            content="inspect system",
            tool_calls=(
                AgentToolCall(
                    tool_call_id="tool-call:plugin-system",
                    name="system.describe",
                    arguments={},
                ),
            ),
            conclusion=None,
            usage={"inputTokens": 1, "outputTokens": 1},
            finish_reason="tool_calls",
            raw_response_digest=_digest("tool-turn"),
        )
        done_turn = AgentTurnResult(
            model_call_id="model-call:plugin-done",
            model_id=ScriptedTurnAdapter.model_id,
            content="done",
            tool_calls=(),
            conclusion=AgentRunConclusion(
                status="candidate_completed",
                summary="Observed the Gateway system projection.",
            ),
            usage={"inputTokens": 1, "outputTokens": 1},
            finish_reason="stop",
            raw_response_digest=_digest("done-turn"),
        )
        adapter = ScriptedTurnAdapter((tool_turn, done_turn))
        clock = FixedClock()

        run = HarnessAgentRun.create(
            root / "state",
            contract,
            lambda _contract: adapter,
            tool_bridge=bridge,
            cognition_profile=HarnessCognitionProfile(
                working_set_transitions=True,
                caller_ingress_promotions=False,
                working_set_history=False,
            ),
            clock_ms=clock,
            monotonic_ms=clock,
        )
        skill_source = plugin.skill("method-router").to_working_view_source()
        result = run.run(
            (),
            cognition_seed=HarnessCognitionSeed(
                attempt_id="working-attempt:plugin-e2e",
                sources=(
                    HarnessCognitionSeedSource(
                        slot="procedure",
                        source=skill_source,
                    ),
                ),
                basis="caller selected the exact Plugin Skill for this bounded Run",
            ),
        )

        assert result.loop_result.stop_code.value == "candidate_completed"
        assert result.loop_result.usage["toolCalls"] == 1
        assert gateway.calls == [("system.describe", {})]
        assert len(adapter.requests) == 2
        assert (
            "CALLER-SELECTED AGENT SKILL [method-router]"
            in adapter.requests[0].messages[0]["content"]
        )
        tool_messages = [
            message for message in adapter.requests[1].messages if message.get("role") == "tool"
        ]
        assert len(tool_messages) == 1
        assert tool_messages[0]["name"] == "system.describe"
        assert (
            tool_messages[0]["observation"]["content"]["gateway"]["truthRole"]
            == "non-authoritative"
        )

        explanation = run.explain()
        assert explanation["processLocal"]["customToolBridge"]["supplied"] is True
        assert (
            explanation["processLocal"]["customToolBridge"]["catalogDigest"]
            == bridge.catalog_digest
        )
        assert explanation["processLocal"]["customToolBridge"]["grantDigest"] == bridge.grant_digest
