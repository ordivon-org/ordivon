"""Minimal AuthZEN wire adapter over the installed OPA policy engine.

Authentication: exact workload bearer loaded from a systemd credential.
Decision: OPA/Rego, not a Python allowlist. The Gateway remains the PEP.
"""

from __future__ import annotations

import asyncio
import hmac
import os
import secrets
import uuid
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import ClientDisconnect, Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .json_qualification import InvalidJsonObject, qualify_json_object
from .policy_evaluation import EvaluationUnavailable
from .policy_evaluation import evaluate_policy as _opa_decision

MAX_REQUEST_BYTES = 8192


class InvalidRequestBody(ValueError):
    pass


class RequestTooLarge(ValueError):
    pass


async def _read_evaluation(request: Request) -> bytes:
    """Bound retained bytes before parsing, then require a unique JSON object.

    A rejected wire representation never reaches OPA. The ASGI server owns
    network framing and chunk allocation; this is an application buffer bound.
    """
    lengths = request.headers.getlist("content-length")
    declared = None
    if lengths:
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            raise InvalidRequestBody("invalid content length")
        digits = lengths[0].lstrip("0") or "0"
        limit = str(MAX_REQUEST_BYTES)
        if len(digits) > len(limit) or (len(digits) == len(limit) and digits > limit):
            raise RequestTooLarge
        declared = int(digits)
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_REQUEST_BYTES:
            raise RequestTooLarge
        raw.extend(chunk)
    if declared is not None and declared != len(raw):
        raise InvalidRequestBody("content length mismatch")
    captured = bytes(raw)
    qualify_json_object(captured)
    return captured


def make_app(*, token_path: str, policy: str, policy_data: str, opa: str) -> Starlette:
    for value in (token_path, policy, policy_data, opa):
        if not Path(value).is_absolute():
            raise ValueError("Security AuthZEN inputs must be absolute paths")

    instance_id = str(uuid.uuid4())
    commitment_key = secrets.token_bytes(32)

    async def health(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "owner": "security", "policyEngine": "opa"})

    async def evaluate(request: Request) -> JSONResponse:
        authorization = request.headers.get("authorization", "")
        supplied = authorization[7:] if authorization.startswith("Bearer ") else ""
        try:
            expected = Path(token_path).read_text(encoding="utf-8").strip()
        except OSError, UnicodeError:
            return JSONResponse({"error": "credential_unavailable"}, status_code=503)
        if (
            len(expected) < 32
            or not supplied
            or not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))
        ):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        request_id = request.headers.get("x-request-id", "")
        try:
            if str(uuid.UUID(request_id)) != request_id:
                raise ValueError("not canonical UUID")
        except ValueError:
            return JSONResponse({"error": "invalid_request_id"}, status_code=400)
        if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
            return JSONResponse({"error": "unsupported_media_type"}, status_code=415)
        try:
            payload = await _read_evaluation(request)
        except RequestTooLarge:
            return JSONResponse({"error": "request_too_large"}, status_code=413)
        except InvalidRequestBody, InvalidJsonObject:
            return JSONResponse({"error": "invalid_evaluation"}, status_code=400)
        except ValueError, RecursionError, ClientDisconnect:
            return JSONResponse({"error": "invalid_json"}, status_code=400)
        standing_request = request.headers.getlist("x-ordivon-policy-standing")
        if standing_request not in ([], ["v1"]):
            return JSONResponse({"error": "invalid_standing_version"}, status_code=400)
        try:
            observation = await asyncio.to_thread(
                _opa_decision, payload, opa, policy, policy_data, commitment_key
            )
        except EvaluationUnavailable:
            return JSONResponse({"error": "decision_unavailable"}, status_code=503)
        body: dict[str, object] = {"decision": observation.decision}
        if standing_request:
            body["context"] = {
                "ordivonPolicyStanding": observation.standing(
                    request_id=request_id, instance_id=instance_id
                )
            }
        return JSONResponse(body, headers={"X-Request-ID": request_id, "Cache-Control": "no-store"})

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
