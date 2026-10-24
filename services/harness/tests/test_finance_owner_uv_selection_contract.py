"""Finance environment materialization must consume the owner's mise-selected uv."""
import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "finance_readonly_observation.py"
spec = importlib.util.spec_from_file_location("finance_observation_owner_tool", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class Stub:
    def __init__(self, ok=True):
        self.calls = []
        self.ok = ok

    def call_tool(self, name, payload):
        self.calls.append((name, payload))
        return {
            "jobId": "job-fixture",
            "attemptId": "attempt-fixture",
            "status": "succeeded" if self.ok else "failed",
            "executionTerminal": True,
            "exitCode": 0 if self.ok else 2,
            "semanticCompletionEvaluated": False,
        }


def test_finance_lock_preparation_uses_native_mise_owner_tool_and_no_network():
    runtime = Stub()
    receipt = module._prepare_finance_project_environment(
        runtime, finance_workspace_id="finance-ws", client_request_id="native-owner-uv"
    )
    assert receipt["networkAcquisitionAllowed"] is False
    assert receipt["lockfileMutationAllowed"] is False
    assert receipt["agentToolAuthorityGranted"] is False
    name, call = runtime.calls[0]
    assert name == "workspace.exec"
    execution = call["execution"]
    assert execution["executable"] == "/bin/bash"
    assert execution["env"]["MISE_OFFLINE"] == "1"
    assert execution["env"]["UV_OFFLINE"] == "1"
    assert execution["env"]["MISE_AUTO_INSTALL"] == "false"
    assert "mise which uv" in execution["args"][-1]
    assert "sync --locked --offline" in execution["args"][-1]
    assert "/usr/bin/uv" not in execution["args"][-1]
    assert receipt["provider"] == "mise:selected-owner-uv"


def test_finance_lock_preparation_preserves_fail_closed_runtime_failure():
    import pytest
    with pytest.raises(RuntimeError, match="locked offline closure"):
        module._prepare_finance_project_environment(
            Stub(ok=False), finance_workspace_id="finance-ws",
            client_request_id="negative-native-owner-uv",
        )
