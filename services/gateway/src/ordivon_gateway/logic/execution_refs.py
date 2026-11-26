"""Gateway-owned execution reference and local input grammar, independent of dispatch.

This is a source-local, pure wire-reference contract. It does not establish
Runtime ownership, admission, execution, or Security authorization.
"""

from __future__ import annotations


class GatewayError(RuntimeError):
    pass


def format_execution_ref(owner_id: str, native_id: str) -> str:
    return f"ordivon-exec:v1:{owner_id}:{native_id}"


def parse_execution_ref(value: str) -> tuple[str, str]:
    prefix = "ordivon-exec:v1:"
    if not value.startswith(prefix):
        raise GatewayError("invalid execution operationRef")
    rest = value[len(prefix) :]
    try:
        owner_id, native_id = rest.rsplit(":", 1)
    except ValueError as exc:
        raise GatewayError("invalid execution operationRef") from exc
    if owner_id not in {"runtime.linux", "runtime.windows", "runtime.harness"} or not native_id:
        raise GatewayError("unsupported execution operationRef owner")
    return owner_id, native_id


def validate_observation_wait(wait_ms: int) -> None:
    if type(wait_ms) is not int or not 0 <= wait_ms <= 30_000:
        raise GatewayError("waitMs must be an integer between 0 and 30000")


def validate_artifact_cursor(offset: int, max_bytes: int) -> None:
    if (
        type(offset) is not int
        or offset < 0
        or type(max_bytes) is not int
        or not 1 <= max_bytes <= 1_048_576
    ):
        raise GatewayError("artifact read requested an invalid range/cursor")
