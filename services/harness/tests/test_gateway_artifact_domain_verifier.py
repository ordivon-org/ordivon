"""R52: source PG Agent completion is not domain TaskSolved.

The Provider and Gateway MCP envelope are scripted; the physical Python
editor process is REAL. Independent existing HARNESS-EDIT-ADDRESSING-002
hidden QA is used only AFTER the Agent Run and is never model-visible.
"""

from __future__ import annotations

from dataclasses import replace
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.ordivon.model import AgentToolCall, ScriptedTurnAdapter
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.plugin_gateway_effect import PluginGatewayExecutionBridgeFactory
from ordivon_harness.postgres_store import PostgresHarnessStore
from tests.test_plugin_gateway_effect import GatewayTextArtifacts
from tests.test_plugin_gateway_effect import FixedClock, _adapter, _contract, _factory
from tests.pg_test_support import FakeNativeWorkspaceClaimClient

HARNESS = Path(__file__).resolve().parents[1]
TASK = HARNESS / "evals/harness-edit-addressing-002"
FIXTURE = HARNESS / "fixtures/harness-edit-addressing-repeated-v1"


@pytest.mark.parametrize("edit", ("beta-only", "both-enabled"))
def test_original_pg_owner_output_does_not_substitute_for_independent_task_verifier(
    pg_schema,
    tmp_path: Path,
    edit: str,
):
    workspace = tmp_path / "editable-task"
    shutil.copytree(FIXTURE, workspace)
    original_spec = (workspace / "SPEC.md").read_bytes()
    original_test = (workspace / "test_feature_flags.py").read_bytes()

    class LocalEditorGateway(GatewayTextArtifacts):
        process: subprocess.CompletedProcess[str] | None = None
        submitted = 0

        def call_tool(self, name, arguments):
            if name == "execution.submit":
                with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
                    step = EventSourcedRunContinuity.open(
                        store, "harness-run:plugin-h2"
                    ).load_current_tool_step()
                    assert step.fence is not None and step.receipt is None
                assert arguments["executable"] == "/usr/bin/python3"
                self.submitted += 1
                self.process = subprocess.run(
                    [arguments["executable"], *arguments["args"]],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                    check=False,
                    timeout=5,
                )
                self.stdout = self.process.stdout
            return super().call_tool(name, arguments)

    client = LocalEditorGateway()
    standard = _factory(client)
    grant = replace(standard.execution_grant, executable_allowlist=("/usr/bin/python3",))
    factory = PluginGatewayExecutionBridgeFactory(standard.component, client, grant)
    contract = _contract(factory)
    script = """from pathlib import Path
p = Path('feature_flags.py')
source = p.read_text()
assert source.count('return False') == 2
"""
    if edit == "beta-only":
        script += """prefix, found, suffix = source.rpartition('return False')
assert found == 'return False'
p.write_text(prefix + 'return True' + suffix)
"""
    else:
        script += """p.write_text(source.replace('return False', 'return True'))
"""
    script += "print('EDIT_COMPLETED')\n"

    first, last = _adapter()._results
    scripted = ScriptedTurnAdapter(
        (
            replace(
                first,
                tool_calls=(
                    AgentToolCall(
                        tool_call_id="tool-call:plugin-h2",
                        name="execution_submit",
                        arguments={
                            "executable": "/usr/bin/python3",
                            "args": ["-c", script],
                            "cwdRelative": ".",
                        },
                    ),
                ),
            ),
            last,
        )
    )
    clock = FixedClock()
    run = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        contract,
        lambda _: scripted,
        tool_bridge_factory=factory,
        workspace_claim_client=FakeNativeWorkspaceClaimClient(),
        clock_ms=clock,
        monotonic_ms=clock,
    )
    result = run.run(())
    assert result.loop_result.stop_code.value == "candidate_completed"
    assert client.submitted == 1
    assert client.process is not None and client.process.returncode == 0
    assert client.stdout == "EDIT_COMPLETED\n"
    assert (workspace / "SPEC.md").read_bytes() == original_spec
    assert (workspace / "test_feature_flags.py").read_bytes() == original_test
    assert (
        scripted.requests[1].messages[-1]["observation"]["content"]["outputPreviews"]["stdout"]["text"]
        == client.stdout
    )

    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        source_run = EventSourcedRunContinuity.open(store, contract.harness_run_id)
        step = source_run.load_current_tool_step()
        assert step.receipt is not None and step.receipt.status.value == "observed"
        assert step.observation is not None
        assert step.observation["structuredContent"]["outputPreviews"]["stdout"]["text"] == client.stdout
        store.validate_run_history(contract.harness_run_id)

    # INDEPENDENT task verifier is never passed to model or physical Editor.
    spec = importlib.util.spec_from_file_location("domain_task_qa", TASK / "qa.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    accepted = module.run_candidate(edit, workspace / "feature_flags.py")
    assert accepted["visiblePassed"] is True
    assert accepted["hiddenPassed"] is (edit == "beta-only"), (
        "the same candidate_completed + exit0 must NOT be treated as TaskSolved"
    )
