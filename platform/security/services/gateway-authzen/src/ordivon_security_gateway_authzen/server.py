"""Minimal AuthZEN wire adapter over the installed OPA policy engine.

Authentication: exact workload bearer loaded from a systemd credential.
Decision: OPA/Rego, not a Python allowlist. The Gateway remains the PEP.
"""

from __future__ import annotations

import asyncio
import hmac
import json
import os
import subprocess
import uuid
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


class EvaluationUnavailable(Exception):
    pass


def _opa_decision(payload: dict, opa: str, policy: str, data: str) -> bool:
    try:
        result = subprocess.run(
            [
                opa,
                "eval",
                "--stdin-input",
                "--format",
                "raw",
                "--data",
                policy,
                "--data",
                data,
                "data.ordivon.security.gateway_artifact.allow",
            ],
            input=json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=2.0,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise EvaluationUnavailable("OPA decision unavailable") from exc
    output = result.stdout.strip()
    if output not in ("true", "false"):
        raise EvaluationUnavailable("OPA returned a nonboolean result")
    return output == "true"


def make_app(*, token_path: str, policy: str, policy_data: str, opa: str) -> Starlette:
    for value in (token_path, policy, policy_data, opa):
        if not Path(value).is_absolute():
            raise ValueError("Security AuthZEN inputs must be absolute paths")

    async def health(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "owner": "security", "policyEngine": "opa"})

    async def evaluate(request: Request) -> JSONResponse:
        authorization = request.headers.get("authorization", "")
        supplied = authorization[7:] if authorization.startswith("Bearer ") else ""
        try:
            expected = Path(token_path).read_text(encoding="utf-8").strip()
        except OSError, UnicodeError:
            return JSONResponse({"error": "credential_unavailable"}, status_code=503)
        if len(expected) < 32 or not supplied or not hmac.compare_digest(supplied, expected):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        request_id = request.headers.get("x-request-id", "")
        try:
            if str(uuid.UUID(request_id)) != request_id:
                raise ValueError("not canonical UUID")
        except ValueError:
            return JSONResponse({"error": "invalid_request_id"}, status_code=400)
        if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
            return JSONResponse({"error": "unsupported_media_type"}, status_code=415)
        if int(request.headers.get("content-length", "0") or "0") > 8192:
            return JSONResponse({"error": "request_too_large"}, status_code=413)
        raw = await request.body()
        if len(raw) > 8192:
            return JSONResponse({"error": "request_too_large"}, status_code=413)
        try:
            payload = json.loads(raw)
        except ValueError, UnicodeDecodeError:
            return JSONResponse({"error": "invalid_json"}, status_code=400)
        if not isinstance(payload, dict):
            return JSONResponse({"error": "invalid_evaluation"}, status_code=400)
        try:
            permitted = await asyncio.to_thread(_opa_decision, payload, opa, policy, policy_data)
        except EvaluationUnavailable:
            return JSONResponse({"error": "decision_unavailable"}, status_code=503)
        return JSONResponse({"decision": permitted}, headers={"X-Request-ID": request_id})

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/access/v1/evaluation", evaluate, methods=["POST"]),
        ]
    )


def _installed_app() -> Starlette:
    return make_app(
        token_path=os.environ["ORDIVON_SECURITY_AUTHZEN_TOKEN_FILE"],
        policy=os.environ["ORDIVON_SECURITY_AUTHZEN_POLICY_FILE"],
        policy_data=os.environ["ORDIVON_SECURITY_AUTHZEN_POLICY_DATA_FILE"],
        opa=os.environ["ORDIVON_SECURITY_AUTHZEN_OPA"],
    )


app = _installed_app() if os.environ.get("ORDIVON_SECURITY_AUTHZEN_TOKEN_FILE") else None
