"""Pure input-authority ingress request, configuration and digest contracts.

No filesystem mutation, carrier invocation, request ledger or effect authority lives here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

SHA256_PREFIX = "sha256:"


MAX_CONFIGURED_BYTES = 512 * 1024 * 1024


PROVENANCE_KEYS = {
    "provider",
    "providerFileId",
    "providerVersion",
    "libraryFileId",
    "libraryVersion",
    "parentObjectDigest",
    "member",
}


SECRETISH = (
    "token",
    "secret",
    "cookie",
    "credential",
    "oauth",
    "password",
    "signedurl",
    "authorization",
)


class IngressError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _digest(value: Any) -> str:
    return SHA256_PREFIX + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _validate_sha256(value: str, label: str) -> str:
    value = str(value)
    if not value.startswith(SHA256_PREFIX) or len(value) != 71:
        raise IngressError(f"{label} must be one sha256:<64-hex> digest")
    try:
        int(value[7:], 16)
    except ValueError as error:
        raise IngressError(f"{label} must be one sha256:<64-hex> digest") from error
    return value.lower()


def _relative(value: str, label: str) -> str:
    raw = str(value)
    if not raw or "\\" in raw or "\x00" in raw:
        raise IngressError(f"{label} must be a non-empty POSIX relative object")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise IngressError(f"{label} must not be absolute or contain traversal")
    normalized = str(path)
    if normalized != raw:
        raise IngressError(f"{label} must already be normalized")
    return normalized


def _clean_text(value: Any, label: str, *, max_len: int = 512) -> str:
    text = str(value)
    if not text or len(text) > max_len or "\x00" in text or "\n" in text or "\r" in text:
        raise IngressError(f"{label} is invalid")
    return text


def _provenance(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise IngressError("sourceProvenance must be an object")
    unknown = set(value) - PROVENANCE_KEYS
    if unknown:
        raise IngressError("sourceProvenance contains unsupported fields")
    for key in value:
        lowered = key.lower().replace("_", "")
        if any(term in lowered for term in SECRETISH):
            raise IngressError("sourceProvenance may not contain secret-bearing fields")
    result = {key: _clean_text(item, f"sourceProvenance.{key}") for key, item in value.items()}
    if not result.get("provider") or not result.get("providerFileId"):
        raise IngressError("sourceProvenance requires provider and providerFileId")
    if "parentObjectDigest" in result:
        result["parentObjectDigest"] = _validate_sha256(
            result["parentObjectDigest"], "sourceProvenance.parentObjectDigest"
        )
    return result


def _validate_request(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("schemaVersion") != 1:
        raise IngressError("request must be schemaVersion 1")
    allowed = {
        "schemaVersion",
        "requestId",
        "carrier",
        "sourceObject",
        "sourceProvenance",
        "expectedSha256",
        "authority",
        "relativeObject",
    }
    if set(raw) - allowed:
        raise IngressError("request contains unsupported fields")
    request = {
        "schemaVersion": 1,
        "requestId": _clean_text(raw.get("requestId"), "requestId", max_len=256),
        "carrier": _clean_text(raw.get("carrier"), "carrier", max_len=128),
        "sourceObject": _relative(raw.get("sourceObject"), "sourceObject"),
        "sourceProvenance": _provenance(raw.get("sourceProvenance")),
        "expectedSha256": _validate_sha256(raw.get("expectedSha256"), "expectedSha256"),
        "authority": _clean_text(raw.get("authority"), "authority", max_len=128),
        "relativeObject": _relative(raw.get("relativeObject"), "relativeObject"),
    }
    return request


def _validate_config(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("schemaVersion") != 1:
        raise IngressError("config must be schemaVersion 1")
    state_dir = Path(str(raw.get("stateDir") or ""))
    if not state_dir.is_absolute():
        raise IngressError("config stateDir must be absolute")
    max_bytes = int(raw.get("maxBytes") or 0)
    if max_bytes <= 0 or max_bytes > MAX_CONFIGURED_BYTES:
        raise IngressError("config maxBytes is outside the supported bound")
    carriers = raw.get("carriers")
    authorities = raw.get("authorities")
    if not isinstance(carriers, dict) or not carriers:
        raise IngressError("config requires carriers")
    if not isinstance(authorities, dict) or not authorities:
        raise IngressError("config requires authorities")
    clean_carriers: dict[str, dict[str, Any]] = {}
    for name, row in carriers.items():
        name = _clean_text(name, "carrier name", max_len=128)
        if not isinstance(row, dict):
            raise IngressError(f"carrier {name} must be an object")
        kind = row.get("kind")
        if kind == "rclone":
            prefix = _clean_text(
                row.get("sourcePrefix"), f"carrier {name} sourcePrefix", max_len=1024
            )
            clean_carriers[name] = {"kind": "rclone", "sourcePrefix": prefix}
        elif kind == "local-stage":
            root = Path(str(row.get("sourceRoot") or ""))
            if not root.is_absolute():
                raise IngressError(f"carrier {name} sourceRoot must be absolute")
            clean_carriers[name] = {"kind": "local-stage", "sourceRoot": root}
        else:
            raise IngressError(f"carrier {name} uses unsupported kind")
    clean_authorities: dict[str, Path] = {}
    for name, row in authorities.items():
        name = _clean_text(name, "authority name", max_len=128)
        if not isinstance(row, dict):
            raise IngressError(f"authority {name} must be an object")
        root = Path(str(row.get("root") or ""))
        if not root.is_absolute():
            raise IngressError(f"authority {name} root must be absolute")
        clean_authorities[name] = root
    return {
        "schemaVersion": 1,
        "stateDir": state_dir,
        "maxBytes": max_bytes,
        "carriers": clean_carriers,
        "authorities": clean_authorities,
    }
