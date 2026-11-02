"""Gateway-owned execution reference grammar, independent of service dispatch.

This is a source-local, pure wire-reference contract. It does not establish
Runtime/worker ownership, admission, execution, or Security authorization.
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
    if owner_id not in {"runtime.linux", "runtime.windows", "external.pull"} or not native_id:
        raise GatewayError("unsupported execution operationRef owner")
    return owner_id, native_id
