from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any

from .evidence import RuntimeArtifactPayload
from .task_runtime import (
    RuntimeArtifactDescriptor,
    RuntimeJobObservation,
    RuntimeJobRef,
)

SCHEMA_VERSION = 1


class RuntimeMcpProtocolError(RuntimeError):
    pass


ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]


class RuntimeMcpAdapter:
    """N19 provider: translate Agent Service work into Runtime Job operations."""

    def __init__(self, tool_caller: ToolCaller) -> None:
        self._call = tool_caller

    def submit(
        self, client_request_id: str, execution: dict[str, Any]
    ) -> RuntimeJobRef:
        result = self._call(
            "workspace.exec",
            {
                "schemaVersion": SCHEMA_VERSION,
                "clientRequestId": client_request_id,
                "execution": execution,
                "waitMs": 0,
                "stdoutTailBytes": 4096,
                "stderrTailBytes": 4096,
            },
        )
        job_id = result.get("jobId")
        if not isinstance(job_id, str) or not job_id:
            raise RuntimeMcpProtocolError("workspace.exec omitted Runtime jobId")
        return RuntimeJobRef(job_id=job_id)

    def observe(self, job_id: str) -> RuntimeJobObservation:
        result = self._call(
            "task.observe",
            {
                "schemaVersion": SCHEMA_VERSION,
                "jobId": job_id,
                "waitMs": 0,
                "stdoutTailBytes": 65536,
                "stderrTailBytes": 65536,
            },
        )
        observed_job_id = result.get("jobId")
        if observed_job_id != job_id:
            raise RuntimeMcpProtocolError(
                "task.observe returned a different Runtime job identity"
            )
        status = result.get("status")
        delivery = result.get("deliveryDisposition")
        semantic = result.get("semanticCompletionEvaluated")
        if (
            not isinstance(status, str)
            or not isinstance(delivery, str)
            or not isinstance(semantic, bool)
        ):
            raise RuntimeMcpProtocolError(
                "task.observe omitted required Runtime evidence fields"
            )
        execution_terminal = result.get("executionTerminal")
        if not isinstance(execution_terminal, bool):
            raise RuntimeMcpProtocolError("task.observe omitted executionTerminal")
        artifacts_raw = result.get("artifacts", [])
        if not isinstance(artifacts_raw, list):
            raise RuntimeMcpProtocolError("task.observe artifacts must be a list")
        artifact_ids: list[str] = []
        artifact_descriptors: list[RuntimeArtifactDescriptor] = []
        for item in artifacts_raw:
            if not isinstance(item, dict):
                continue
            artifact_id = item.get("artifactId")
            kind = item.get("kind")
            if isinstance(artifact_id, str):
                artifact_ids.append(artifact_id)
                if isinstance(kind, str):
                    artifact_descriptors.append(
                        RuntimeArtifactDescriptor(artifact_id=artifact_id, kind=kind)
                    )
        stdout_tail = result.get("stdoutTail", "")
        stderr_tail = result.get("stderrTail", "")
        if not isinstance(stdout_tail, str) or not isinstance(stderr_tail, str):
            raise RuntimeMcpProtocolError("task.observe output tails must be strings")
        return RuntimeJobObservation(
            job_id=job_id,
            status=status,
            execution_terminal=execution_terminal,
            delivery_disposition=delivery,
            semantic_completion_evaluated=semantic,
            stdout_tail=stdout_tail,
            stderr_tail=stderr_tail,
            artifacts=tuple(artifact_ids),
            artifact_descriptors=tuple(artifact_descriptors),
        )


class RuntimeMcpArtifactReader:
    """Read one exact Runtime Artifact through the public digest-bound artifact.read surface."""

    def __init__(
        self,
        tool_caller: ToolCaller,
        *,
        chunk_bytes: int = 1_048_576,
        max_total_bytes: int = 4_194_304,
    ) -> None:
        if chunk_bytes <= 0 or chunk_bytes > 1_048_576:
            raise ValueError("chunk_bytes must be in 1..1048576")
        if max_total_bytes <= 0:
            raise ValueError("max_total_bytes must be positive")
        self._call = tool_caller
        self._chunk_bytes = chunk_bytes
        self._max_total_bytes = max_total_bytes

    def read(self, job_id: str, artifact_id: str) -> RuntimeArtifactPayload:
        offset = 0
        parts: list[str] = []
        total_bytes = 0
        expected_digest: str | None = None
        while True:
            result = self._call(
                "artifact.read",
                {
                    "schemaVersion": SCHEMA_VERSION,
                    "jobId": job_id,
                    "artifactId": artifact_id,
                    "offset": offset,
                    "maxBytes": self._chunk_bytes,
                },
            )
            if result.get("jobId") != job_id or result.get("artifactId") != artifact_id:
                raise RuntimeMcpProtocolError(
                    "artifact.read returned mismatched identity"
                )
            reported_offset = result.get("offset")
            next_offset = result.get("nextOffset")
            eof = result.get("eof")
            chunk_digest = result.get("digest")
            content = result.get("content")
            if reported_offset != offset:
                raise RuntimeMcpProtocolError(
                    "artifact.read returned unexpected offset"
                )
            if not isinstance(next_offset, int) or next_offset < offset:
                raise RuntimeMcpProtocolError(
                    "artifact.read returned invalid nextOffset"
                )
            if (
                not isinstance(eof, bool)
                or not isinstance(chunk_digest, str)
                or not isinstance(content, str)
            ):
                raise RuntimeMcpProtocolError(
                    "artifact.read omitted required artifact fields"
                )
            if expected_digest is None:
                expected_digest = chunk_digest
            elif chunk_digest != expected_digest:
                raise RuntimeMcpProtocolError("artifact digest changed across chunks")
            parts.append(content)
            total_bytes += len(content.encode("utf-8"))
            if total_bytes > self._max_total_bytes:
                raise RuntimeMcpProtocolError(
                    "artifact exceeds Agent Service evidence byte ceiling"
                )
            if eof:
                break
            if next_offset <= offset:
                raise RuntimeMcpProtocolError("artifact.read cursor did not advance")
            offset = next_offset

        combined = "".join(parts)
        computed = "sha256:" + hashlib.sha256(combined.encode("utf-8")).hexdigest()
        if expected_digest is None or computed != expected_digest:
            raise RuntimeMcpProtocolError(
                "reassembled artifact digest does not match Runtime digest"
            )
        return RuntimeArtifactPayload(
            job_id=job_id,
            artifact_id=artifact_id,
            digest=expected_digest,
            content=combined,
        )
