from __future__ import annotations

import hmac
import json
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from .external_worker import (
    ExternalPullWorkerTransport,
    WorkerAuthError,
    WorkerConflict,
)


def _json_error(message: str, status: int) -> JSONResponse:
    return JSONResponse(
        {"error": message}, status_code=status, headers={"Cache-Control": "no-store"}
    )


async def _body(request: Request) -> dict[str, Any]:
    try:
        value = await request.json()
    except json.JSONDecodeError as exc:
        raise WorkerConflict("request body must be JSON") from exc
    if not isinstance(value, dict):
        raise WorkerConflict("request body must be a JSON object")
    return value


def _enrollment_token(path: str | None) -> str | None:
    if path is None:
        return None
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise RuntimeError("external worker enrollment token file is empty")
    return value


def attach_worker_routes(
    app,
    transport: ExternalPullWorkerTransport,
    *,
    enrollment_token_file: str | None = None,
) -> None:
    enrollment_token = _enrollment_token(enrollment_token_file)

    async def enroll(request: Request):
        if enrollment_token is None:
            return _json_error("worker enrollment is disabled", 403)
        supplied = request.headers.get("authorization", "")
        expected = f"Bearer {enrollment_token}"
        if not hmac.compare_digest(supplied, expected):
            return _json_error("worker enrollment authorization failed", 401)
        try:
            body = await _body(request)
            transport.enroll(
                worker_id=str(body["worker_id"]),
                provider_id=str(body["provider_id"]),
                generation=int(body["generation"]),
                public_key_b64=str(body["public_key"]),
                capabilities=list(body["capabilities"]),
            )
        except (KeyError, TypeError, ValueError, WorkerConflict) as exc:
            return _json_error(str(exc), 409)
        return JSONResponse({"status": "enrolled"}, status_code=201)

    def authenticate(
        request: Request, body: dict[str, Any], *, expected_worker: str | None = None
    ) -> tuple[str, int]:
        worker_id, generation = transport.verify_signed_request(
            method=request.method,
            path=request.url.path,
            body=body,
            headers=request.headers,
        )
        if expected_worker is not None and worker_id != expected_worker:
            raise WorkerAuthError("signed worker identity does not match request path")
        return worker_id, generation

    async def heartbeat(request: Request):
        try:
            body = await _body(request)
            worker_id, generation = authenticate(
                request, body, expected_worker=request.path_params["worker_id"]
            )
            capabilities = body.get("capabilities")
            transport.heartbeat(
                worker_id,
                generation=generation,
                capabilities=list(capabilities) if capabilities is not None else None,
            )
            cancellations = transport.cancellation_requests(worker_id, generation=generation)
            return JSONResponse({"status": "ok", "cancel_operations": cancellations})
        except WorkerAuthError as exc:
            return _json_error(str(exc), 401)
        except (TypeError, WorkerConflict) as exc:
            return _json_error(str(exc), 409)

    async def claim(request: Request):
        try:
            body = await _body(request)
            worker_id, generation = authenticate(
                request, body, expected_worker=request.path_params["worker_id"]
            )
            parcel = transport.claim(worker_id, generation=generation)
            return JSONResponse({"parcel": parcel})
        except WorkerAuthError as exc:
            return _json_error(str(exc), 401)
        except WorkerConflict as exc:
            return _json_error(str(exc), 409)

    def attempt_fields(body: dict[str, Any]) -> tuple[str, str]:
        try:
            return str(body["attempt_id"]), str(body["lease_id"])
        except KeyError as exc:
            raise WorkerConflict("attempt_id and lease_id are required") from exc

    async def started(request: Request):
        try:
            body = await _body(request)
            worker_id, generation = authenticate(request, body)
            attempt_id, lease_id = attempt_fields(body)
            transport.started(
                worker_id=worker_id,
                generation=generation,
                operation_id=request.path_params["operation_id"],
                attempt_id=attempt_id,
                lease_id=lease_id,
            )
            return JSONResponse({"status": "started"})
        except WorkerAuthError as exc:
            return _json_error(str(exc), 401)
        except WorkerConflict as exc:
            return _json_error(str(exc), 409)

    async def event(request: Request):
        try:
            body = await _body(request)
            worker_id, generation = authenticate(request, body)
            attempt_id, lease_id = attempt_fields(body)
            transport.record_event(
                worker_id=worker_id,
                generation=generation,
                operation_id=request.path_params["operation_id"],
                attempt_id=attempt_id,
                lease_id=lease_id,
                sequence=int(body["sequence"]),
                event=dict(body["event"]),
            )
            return JSONResponse({"status": "recorded"})
        except WorkerAuthError as exc:
            return _json_error(str(exc), 401)
        except (KeyError, TypeError, ValueError, WorkerConflict) as exc:
            return _json_error(str(exc), 409)

    async def artifact(request: Request):
        try:
            body = await _body(request)
            worker_id, generation = authenticate(request, body)
            attempt_id, lease_id = attempt_fields(body)
            transport.put_artifact(
                worker_id=worker_id,
                generation=generation,
                operation_id=request.path_params["operation_id"],
                attempt_id=attempt_id,
                lease_id=lease_id,
                artifact_id=str(body["artifact_id"]),
                content=str(body["content"]),
            )
            return JSONResponse({"status": "recorded"})
        except WorkerAuthError as exc:
            return _json_error(str(exc), 401)
        except (KeyError, WorkerConflict) as exc:
            return _json_error(str(exc), 409)

    async def terminal(request: Request, *, failed: bool):
        try:
            body = await _body(request)
            worker_id, generation = authenticate(request, body)
            attempt_id, lease_id = attempt_fields(body)
            exit_code = int(body.get("exit_code", 1 if failed else 0))
            if failed and exit_code == 0:
                raise WorkerConflict("failed completion must have non-zero exit_code")
            operation = transport.complete(
                worker_id=worker_id,
                generation=generation,
                operation_id=request.path_params["operation_id"],
                attempt_id=attempt_id,
                lease_id=lease_id,
                exit_code=exit_code,
                result=dict(body.get("result", {})),
                artifacts=list(body.get("artifacts", [])),
            )
            return JSONResponse({"status": operation.state})
        except WorkerAuthError as exc:
            return _json_error(str(exc), 401)
        except (TypeError, ValueError, WorkerConflict) as exc:
            return _json_error(str(exc), 409)

    async def complete(request: Request):
        return await terminal(request, failed=False)

    async def fail(request: Request):
        return await terminal(request, failed=True)

    app.add_route("/v1/workers/enroll", enroll, methods=["POST"])
    app.add_route("/v1/workers/{worker_id:str}/heartbeat", heartbeat, methods=["POST"])
    app.add_route("/v1/workers/{worker_id:str}/claim", claim, methods=["POST"])
    app.add_route("/v1/operations/{operation_id:str}/started", started, methods=["POST"])
    app.add_route("/v1/operations/{operation_id:str}/events", event, methods=["POST"])
    app.add_route("/v1/operations/{operation_id:str}/artifacts", artifact, methods=["POST"])
    app.add_route("/v1/operations/{operation_id:str}/complete", complete, methods=["POST"])
    app.add_route("/v1/operations/{operation_id:str}/fail", fail, methods=["POST"])
