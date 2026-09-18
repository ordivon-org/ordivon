from __future__ import annotations

import hashlib
import unittest

from agent_service.runtime_mcp import (
    RuntimeMcpAdapter,
    RuntimeMcpArtifactReader,
    RuntimeMcpProtocolError,
)


class FakeToolCaller:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, name: str, arguments: dict) -> dict:
        self.calls.append((name, arguments))
        if not self.responses:
            raise AssertionError(f"unexpected call: {name}")
        return self.responses.pop(0)


def digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


class RuntimeArtifactR6Tests(unittest.TestCase):
    def test_runtime_observation_preserves_artifact_kind_descriptors(self) -> None:
        caller = FakeToolCaller(
            [
                {
                    "jobId": "job-1",
                    "status": "succeeded",
                    "executionTerminal": True,
                    "deliveryDisposition": "committed",
                    "semanticCompletionEvaluated": False,
                    "stdoutTail": "OK\n",
                    "stderrTail": "",
                    "artifacts": [
                        {"artifactId": "attempt.stdout", "kind": "stdout"},
                        {"artifactId": "attempt.result", "kind": "execution_result"},
                    ],
                }
            ]
        )

        observation = RuntimeMcpAdapter(caller).observe("job-1")

        self.assertEqual(
            [(item.artifact_id, item.kind) for item in observation.artifact_descriptors],
            [("attempt.stdout", "stdout"), ("attempt.result", "execution_result")],
        )

    def test_artifact_reader_reassembles_digest_bound_chunks(self) -> None:
        content = "alpha βeta gamma\n"
        expected = digest(content)
        caller = FakeToolCaller(
            [
                {
                    "jobId": "job-1",
                    "artifactId": "a.stdout",
                    "offset": 0,
                    "nextOffset": len("alpha ".encode("utf-8")),
                    "eof": False,
                    "digest": expected,
                    "content": "alpha ",
                },
                {
                    "jobId": "job-1",
                    "artifactId": "a.stdout",
                    "offset": len("alpha ".encode("utf-8")),
                    "nextOffset": len(content.encode("utf-8")),
                    "eof": True,
                    "digest": expected,
                    "content": "βeta gamma\n",
                },
            ]
        )

        payload = RuntimeMcpArtifactReader(caller, chunk_bytes=8, max_total_bytes=1024).read(
            "job-1", "a.stdout"
        )

        self.assertEqual(payload.content, content)
        self.assertEqual(payload.digest, expected)
        self.assertEqual([call[0] for call in caller.calls], ["artifact.read", "artifact.read"])
        self.assertEqual(caller.calls[1][1]["offset"], len("alpha ".encode("utf-8")))

    def test_artifact_reader_rejects_digest_change_between_chunks(self) -> None:
        caller = FakeToolCaller(
            [
                {
                    "jobId": "job-1",
                    "artifactId": "a.stdout",
                    "offset": 0,
                    "nextOffset": 2,
                    "eof": False,
                    "digest": digest("abcd"),
                    "content": "ab",
                },
                {
                    "jobId": "job-1",
                    "artifactId": "a.stdout",
                    "offset": 2,
                    "nextOffset": 4,
                    "eof": True,
                    "digest": digest("different"),
                    "content": "cd",
                },
            ]
        )

        with self.assertRaises(RuntimeMcpProtocolError):
            RuntimeMcpArtifactReader(caller, chunk_bytes=2, max_total_bytes=1024).read(
                "job-1", "a.stdout"
            )

    def test_artifact_reader_rejects_stalled_non_eof_cursor(self) -> None:
        caller = FakeToolCaller(
            [
                {
                    "jobId": "job-1",
                    "artifactId": "a.stdout",
                    "offset": 0,
                    "nextOffset": 0,
                    "eof": False,
                    "digest": digest(""),
                    "content": "",
                }
            ]
        )

        with self.assertRaises(RuntimeMcpProtocolError):
            RuntimeMcpArtifactReader(caller, chunk_bytes=8, max_total_bytes=1024).read(
                "job-1", "a.stdout"
            )


if __name__ == "__main__":
    unittest.main()
