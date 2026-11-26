"""Actual Harness SDK consumer against native northbound fixture and Runtime PG."""

from __future__ import annotations

import json
import select
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

from ordivon_gateway.contracts import ArtifactChunk

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "services/harness/src"))
from ordivon_harness.gateway_execution_port import (  # noqa: E402
    GatewayExecutionPort,
    GatewayExecutionResult,
)
from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient  # noqa: E402


def main():
    probe, owner, owner_credential, job, artifact, request, expected = sys.argv[1:]
    reference = "ordivon-exec:v1:runtime.linux:" + job
    args = {
        "operationRef": reference,
        "artifactId": artifact,
        "requestId": request,
        "capability": "execution.linux",
        "offset": 0,
        "maxBytes": 4,
    }
    properties = {
        key: {"type": "integer" if key in ("offset", "maxBytes") else "string"} for key in args
    }
    with tempfile.TemporaryDirectory(prefix="gateway-r23-northbound-") as tmp:
        root = Path(tmp)
        cred = root / "north"
        cred.write_text("n" * 32, encoding="ascii")
        cred.chmod(0o600)
        config = root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "owner_endpoint": owner,
                    "owner_credential": owner_credential,
                    "ingress_credential": str(cred),
                    "issuer": "fixture-issuer",
                    "principal": "pg-consumer",
                    "tool": {
                        "name": "artifact.read",
                        "description": "R23 private fixture",
                        "inputSchema": {
                            "type": "object",
                            "properties": properties,
                            "required": ["operationRef", "artifactId", "requestId", "capability"],
                            "additionalProperties": False,
                        },
                        "outputSchema": ArtifactChunk.model_json_schema(),
                    },
                }
            ),
            encoding="utf-8",
        )
        process = subprocess.Popen(
            [probe, "serve-artifact-fixture", str(config)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            assert process.stdout is not None
            assert select.select([process.stdout], [], [], 10)[0], "fixture startup timeout"
            address = process.stdout.readline().strip()
            assert address.startswith("127.0.0.1:"), "fixture startup failed"
            url = f"http://{address}/mcp"
            with requests.Session() as client:
                client.trust_env = False
                for headers in ({}, {"Authorization": "Bearer " + "x" * 32}):
                    assert client.post(url, headers=headers, json={}, timeout=5).status_code == 401
            sdk = OfficialMcpClient(
                LoopbackMcpEndpoint(url), bearer_token_file=cred, timeout_seconds=10
            )
            listed = sdk.list_tools()
            assert [t["name"] for t in listed] == ["artifact.read"]
            assert listed[0]["outputSchema"] == ArtifactChunk.model_json_schema()
            result = GatewayExecutionResult(
                operation_ref=reference,
                native_id=job,
                state="succeeded",
                exit_code=0,
                artifact_ids=(artifact,),
                recovery_required=False,
                request_id=request,
                capability="execution.linux",
            )
            assert GatewayExecutionPort(sdk).read_stdout(result, max_bytes=4) == expected
            for mutation in (
                {"requestId": "foreign"},
                {"capability": "execution.windows"},
                {"operationRef": "ordivon-exec:v1:runtime.linux:foreign"},
                {"artifactId": "foreign"},
                {"offset": len(expected.encode("utf-8")) + 1},
                {"maxBytes": 0},
            ):
                is_error, _ = sdk.call_tool("artifact.read", {**args, **mutation})
                assert is_error, mutation
            # Strict input refuses caller-selected authority/descriptor.
            for extra in ({"issuer": "other"}, {"descriptor": {"kind": "stdout"}}):
                try:
                    is_error, _ = sdk.call_tool("artifact.read", {**args, **extra})
                except Exception:
                    pass  # SDK may reject invalid input before sending it.
                else:
                    assert is_error, extra
            print(
                "R23_NATIVE_NORTHBOUND_HARNESS_PG_PASS",
                len(expected.encode("utf-8")),
                "8 negative tool cases + 2 ingress",
            )
        finally:
            process.terminate()
            try:
                _, err = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                _, err = process.communicate(timeout=5)
            assert "n" * 32 not in err and "p" * 32 not in err


if __name__ == "__main__":
    main()
