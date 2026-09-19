from __future__ import annotations

import hashlib
import json
import shlex
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .evidence import RuntimeArtifactPayload
from .task_runtime import (
    RuntimeArtifactDescriptor,
    RuntimeJobObservation,
    RuntimeJobRef,
)


MODERN_PROTOCOL_VERSION = "2026-07-28"
SCHEMA_VERSION = 1


class RuntimeMcpProtocolError(RuntimeError):
    pass


class RuntimeMcpToolError(RuntimeError):
    def __init__(self, tool_name: str, error: object) -> None:
        super().__init__(f"Runtime tool {tool_name} failed")
        self.tool_name = tool_name
        self.error = error


def _parse_response(content_type: str, body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    text = body.decode("utf-8")
    if "text/event-stream" in content_type:
        lines = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")]
        if not lines:
            raise RuntimeMcpProtocolError("Runtime MCP SSE response contained no data event")
        value = json.loads(lines[-1])
    else:
        value = json.loads(text)
    if not isinstance(value, dict):
        raise RuntimeMcpProtocolError("Runtime MCP response must be a JSON object")
    return value


def _env_value(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    try:
        parts = shlex.split(raw, posix=True)
    except ValueError as error:
        raise ValueError("invalid Runtime environment value") from error
    if len(parts) != 1:
        raise ValueError("Runtime environment value must resolve to one token")
    return parts[0]


class RuntimeMcpHttpClient:
    """Minimal stateless MCP 2026-07-28 client for the local Ordivon Runtime.

    Bearer material stays in memory and is never included in repr/output objects.
    """

    def __init__(self, endpoint: str, token: str, *, timeout_seconds: float = 20.0) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("Runtime MCP endpoint must be HTTP(S)")
        if not token:
            raise ValueError("Runtime MCP bearer token must not be empty")
        self.endpoint = endpoint
        self._token = token
        self.timeout_seconds = float(timeout_seconds)
        self._request_id = 0

    def __repr__(self) -> str:
        return f"RuntimeMcpHttpClient(endpoint={self.endpoint!r}, token=<redacted>)"

    @classmethod
    def from_runtime_env(
        cls,
        env_file: str | Path = "/etc/ordivon/ordivon-runtime.env",
        *,
        timeout_seconds: float = 20.0,
    ) -> "RuntimeMcpHttpClient":
        values: dict[str, str] = {}
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, raw = stripped.split("=", 1)
            values[key.strip()] = _env_value(raw)
        bind = values.get("ORDIVON_BIND")
        token_file = values.get("ORDIVON_BEARER_TOKEN_FILE")
        if not bind or not token_file:
            raise ValueError("Runtime environment requires ORDIVON_BIND and ORDIVON_BEARER_TOKEN_FILE")
        token = Path(token_file).read_text(encoding="utf-8").strip()
        if not token:
            raise ValueError("Runtime bearer token file is empty")
        endpoint = bind if bind.startswith(("http://", "https://")) else f"http://{bind}"
        endpoint = endpoint.rstrip("/") + "/mcp"
        return cls(endpoint, token, timeout_seconds=timeout_seconds)

    def tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self._request_id += 1
        request_id = self._request_id
        params = {
            "name": name,
            "arguments": arguments,
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL_VERSION,
                "io.modelcontextprotocol/clientInfo": {
                    "name": "ordivon-agent-service",
                    "version": "r5",
                },
                "io.modelcontextprotocol/clientCapabilities": {},
            },
        }
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": params,
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": MODERN_PROTOCOL_VERSION,
                "Mcp-Method": "tools/call",
                "Mcp-Name": name,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                status = int(response.status)
                message = _parse_response(response.headers.get("Content-Type", ""), response.read())
        except urllib.error.HTTPError as error:
            status = int(error.code)
            message = _parse_response(error.headers.get("Content-Type", ""), error.read())
        if message.get("id") != request_id:
            raise RuntimeMcpProtocolError("Runtime MCP response id mismatch")
        rpc_error = message.get("error")
        if status >= 400 or isinstance(rpc_error, dict):
            raise RuntimeMcpToolError(name, rpc_error if isinstance(rpc_error, dict) else message)
        result = message.get("result")
        if not isinstance(result, dict):
            raise RuntimeMcpProtocolError("Runtime MCP tools/call omitted result object")
        if result.get("isError") is True:
            raise RuntimeMcpToolError(name, result.get("structuredContent", result))
        structured = result.get("structuredContent")
        if not isinstance(structured, dict):
            raise RuntimeMcpProtocolError("Runtime MCP tool omitted structuredContent")
        return structured


ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]


class RuntimeMcpAdapter:
    """N19 provider: translate Agent Service work into Runtime Job operations."""

    def __init__(self, tool_caller: ToolCaller | RuntimeMcpHttpClient) -> None:
        self._call: ToolCaller = (
            tool_caller.tool if isinstance(tool_caller, RuntimeMcpHttpClient) else tool_caller
        )

    @classmethod
    def from_local_runtime_env(
        cls,
        env_file: str | Path = "/etc/ordivon/ordivon-runtime.env",
    ) -> "RuntimeMcpAdapter":
        return cls(RuntimeMcpHttpClient.from_runtime_env(env_file))

    def submit(self, client_request_id: str, execution: dict[str, Any]) -> RuntimeJobRef:
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
            raise RuntimeMcpProtocolError("task.observe returned a different Runtime job identity")
        status = result.get("status")
        delivery = result.get("deliveryDisposition")
        semantic = result.get("semanticCompletionEvaluated")
        if not isinstance(status, str) or not isinstance(delivery, str) or not isinstance(semantic, bool):
            raise RuntimeMcpProtocolError("task.observe omitted required Runtime evidence fields")
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
        tool_caller: ToolCaller | RuntimeMcpHttpClient,
        *,
        chunk_bytes: int = 1_048_576,
        max_total_bytes: int = 4_194_304,
    ) -> None:
        if chunk_bytes <= 0 or chunk_bytes > 1_048_576:
            raise ValueError("chunk_bytes must be in 1..1048576")
        if max_total_bytes <= 0:
            raise ValueError("max_total_bytes must be positive")
        self._call: ToolCaller = (
            tool_caller.tool if isinstance(tool_caller, RuntimeMcpHttpClient) else tool_caller
        )
        self._chunk_bytes = chunk_bytes
        self._max_total_bytes = max_total_bytes

    @classmethod
    def from_local_runtime_env(
        cls,
        env_file: str | Path = "/etc/ordivon/ordivon-runtime.env",
        *,
        chunk_bytes: int = 1_048_576,
        max_total_bytes: int = 4_194_304,
    ) -> "RuntimeMcpArtifactReader":
        return cls(
            RuntimeMcpHttpClient.from_runtime_env(env_file),
            chunk_bytes=chunk_bytes,
            max_total_bytes=max_total_bytes,
        )

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
                raise RuntimeMcpProtocolError("artifact.read returned mismatched identity")
            reported_offset = result.get("offset")
            next_offset = result.get("nextOffset")
            eof = result.get("eof")
            chunk_digest = result.get("digest")
            content = result.get("content")
            if reported_offset != offset:
                raise RuntimeMcpProtocolError("artifact.read returned unexpected offset")
            if not isinstance(next_offset, int) or next_offset < offset:
                raise RuntimeMcpProtocolError("artifact.read returned invalid nextOffset")
            if not isinstance(eof, bool) or not isinstance(chunk_digest, str) or not isinstance(content, str):
                raise RuntimeMcpProtocolError("artifact.read omitted required artifact fields")
            if expected_digest is None:
                expected_digest = chunk_digest
            elif chunk_digest != expected_digest:
                raise RuntimeMcpProtocolError("artifact digest changed across chunks")
            parts.append(content)
            total_bytes += len(content.encode("utf-8"))
            if total_bytes > self._max_total_bytes:
                raise RuntimeMcpProtocolError("artifact exceeds Agent Service evidence byte ceiling")
            if eof:
                break
            if next_offset <= offset:
                raise RuntimeMcpProtocolError("artifact.read cursor did not advance")
            offset = next_offset

        combined = "".join(parts)
        computed = "sha256:" + hashlib.sha256(combined.encode("utf-8")).hexdigest()
        if expected_digest is None or computed != expected_digest:
            raise RuntimeMcpProtocolError("reassembled artifact digest does not match Runtime digest")
        return RuntimeArtifactPayload(
            job_id=job_id,
            artifact_id=artifact_id,
            digest=expected_digest,
            content=combined,
        )
