from __future__ import annotations

import unittest

from agent_service.runtime_mcp import RuntimeMcpAdapter, RuntimeMcpProtocolError


class FakeToolCaller:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, name: str, arguments: dict) -> dict:
        self.calls.append((name, arguments))
        if not self.responses:
            raise AssertionError(f"unexpected Runtime tool call {name}")
        return self.responses.pop(0)


class RuntimeMcpAdapterTests(unittest.TestCase):
    def test_submit_uses_workspace_exec_with_stable_client_request_id(self) -> None:
        caller = FakeToolCaller(
            [{"jobId": "job-1", "semanticCompletionEvaluated": False}]
        )
        adapter = RuntimeMcpAdapter(caller)
        execution = {
            "workspaceId": "ws-test",
            "executable": "/usr/bin/true",
            "args": [],
            "cwdRelative": ".",
            "env": {},
        }

        ref = adapter.submit("agent-service:assignment:a1:run:v1", execution)

        self.assertEqual(ref.job_id, "job-1")
        name, args = caller.calls[0]
        self.assertEqual(name, "workspace.exec")
        self.assertEqual(args["clientRequestId"], "agent-service:assignment:a1:run:v1")
        self.assertEqual(args["execution"], execution)
        self.assertEqual(args["waitMs"], 0)

    def test_observe_projects_only_runtime_mechanical_evidence(self) -> None:
        caller = FakeToolCaller(
            [
                {
                    "jobId": "job-1",
                    "status": "succeeded",
                    "executionTerminal": True,
                    "deliveryDisposition": "committed",
                    "semanticCompletionEvaluated": False,
                    "stdoutTail": "DOMAIN_OK\n",
                    "stderrTail": "",
                    "artifacts": [
                        {"artifactId": "attempt.stdout", "kind": "stdout"},
                        {"artifactId": "attempt.terminal", "kind": "terminal_evidence"},
                    ],
                }
            ]
        )
        adapter = RuntimeMcpAdapter(caller)

        observation = adapter.observe("job-1")

        self.assertEqual(observation.job_id, "job-1")
        self.assertEqual(observation.status, "succeeded")
        self.assertTrue(observation.execution_terminal)
        self.assertFalse(observation.semantic_completion_evaluated)
        self.assertEqual(observation.artifacts, ("attempt.stdout", "attempt.terminal"))
        self.assertEqual(caller.calls[0][0], "task.observe")

    def test_adapter_fails_closed_on_mismatched_runtime_job_identity(self) -> None:
        caller = FakeToolCaller(
            [
                {
                    "jobId": "other-job",
                    "status": "succeeded",
                    "executionTerminal": True,
                    "deliveryDisposition": "committed",
                    "semanticCompletionEvaluated": False,
                    "stdoutTail": "",
                    "stderrTail": "",
                    "artifacts": [],
                }
            ]
        )
        adapter = RuntimeMcpAdapter(caller)

        with self.assertRaises(RuntimeMcpProtocolError):
            adapter.observe("job-1")


if __name__ == "__main__":
    unittest.main()


class AgentServiceR5PublicApiTests(unittest.TestCase):
    def test_package_exports_r5_runtime_surface(self) -> None:
        import agent_service

        self.assertIs(agent_service.RuntimeMcpAdapter, RuntimeMcpAdapter)
        self.assertFalse(hasattr(agent_service, "AgentServiceR5"))
        self.assertTrue(hasattr(agent_service, "open_agent_service"))
        self.assertFalse(hasattr(agent_service, "RuntimeAdapter"))
