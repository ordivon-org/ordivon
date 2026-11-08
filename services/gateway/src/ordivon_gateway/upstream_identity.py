"""Owner endpoint identity and private credential-file policy, separate from MCP transport.

The Gateway still owns only its upstream connection policy; this module does
not issue tokens, own credentials, or become a separate authentication service.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class OwnerCallError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        owner_id: str | None = None,
        tool_name: str | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.owner_id = owner_id
        self.tool_name = tool_name
        self.error = dict(error) if error is not None else None


@dataclass(frozen=True)
class OwnerEndpoint:
    url: str
    bearer_token_file: str | None = None
    access_client_id_file: str | None = None
    access_client_secret_file: str | None = None
    # Delegate protocol negotiation entirely to the upstream MCP Python SDK.
    # "auto" remains the compatibility default; opt in only for a verified Owner.
    mcp_mode: str = "auto"


def _runtime_identity_configured(endpoint: OwnerEndpoint) -> bool:
    return endpoint.bearer_token_file is not None or endpoint.access_client_id_file is not None


def _validate_windows_private_secret_file(path: Path, label: str) -> None:
    try:
        import ntsecuritycon
        import win32security
    except ImportError as exc:  # pragma: no cover - exercised on Windows acceptance lane
        raise OwnerCallError(f"{label} Windows ACL verifier is unavailable") from exc

    service_name = os.environ.get("ORDIVON_GATEWAY_WINDOWS_SERVICE_NAME", "").strip()
    if not service_name:
        raise OwnerCallError(
            f"{label} Windows credential validation requires ORDIVON_GATEWAY_WINDOWS_SERVICE_NAME"
        )

    try:
        service_sid = win32security.LookupAccountName(None, rf"NT SERVICE\{service_name}")[0]
    except Exception as exc:
        raise OwnerCallError(f"{label} cannot resolve Gateway Windows service identity") from exc

    service_sid_text = win32security.ConvertSidToStringSid(service_sid)
    system_sid_text = "S-1-5-18"
    administrators_sid_text = "S-1-5-32-544"
    allowed_sids = {
        system_sid_text,
        administrators_sid_text,
        service_sid_text,
    }

    try:
        descriptor = win32security.GetFileSecurity(
            str(path), win32security.DACL_SECURITY_INFORMATION
        )
        control, _revision = descriptor.GetSecurityDescriptorControl()
        dacl = descriptor.GetSecurityDescriptorDacl()
    except Exception as exc:
        raise OwnerCallError(f"{label} Windows security descriptor read failed") from exc

    if control & win32security.SE_DACL_PROTECTED == 0:
        raise OwnerCallError(f"{label} Windows credential DACL must be protected")
    if dacl is None:
        raise OwnerCallError(f"{label} Windows credential has no DACL")

    seen_sids: set[str] = set()
    service_read = False
    service_forbidden_mask = (
        0x00000002
        | 0x00000004
        | 0x00000010
        | 0x00000100
        | 0x00010000
        | 0x00040000
        | 0x00080000
        | 0x10000000
        | 0x40000000
    )

    for index in range(dacl.GetAceCount()):
        header, access_mask, sid = dacl.GetAce(index)
        ace_type, ace_flags = header
        sid_text = win32security.ConvertSidToStringSid(sid)
        if ace_type != win32security.ACCESS_ALLOWED_ACE_TYPE:
            raise OwnerCallError(f"{label} Windows credential has non-allow ACE")
        if ace_flags & 0x10:
            raise OwnerCallError(f"{label} Windows credential has inherited ACE")
        if sid_text not in allowed_sids:
            raise OwnerCallError(f"{label} Windows credential grants an unexpected principal")
        seen_sids.add(sid_text)
        if sid_text == service_sid_text:
            if (access_mask & ntsecuritycon.FILE_GENERIC_READ) != ntsecuritycon.FILE_GENERIC_READ:
                raise OwnerCallError(f"{label} Gateway service SID lacks generic read access")
            if access_mask & service_forbidden_mask:
                raise OwnerCallError(f"{label} Gateway service SID has write/control access")
            service_read = True

    if seen_sids != allowed_sids:
        raise OwnerCallError(
            f"{label} Windows credential ACL must name only and all required principals"
        )
    if not service_read:
        raise OwnerCallError(f"{label} Gateway service SID lacks readable ACE")


def _read_private_secret_file(path_text: str, label: str) -> str:
    path = Path(path_text)
    if not path.is_absolute():
        raise OwnerCallError(f"{label} file must be absolute")
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise OwnerCallError(f"{label} path must be a regular file")
    if os.name == "nt":
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if reparse_flag and getattr(metadata, "st_file_attributes", 0) & reparse_flag:
            raise OwnerCallError(f"{label} Windows credential must not be a reparse point")
        _validate_windows_private_secret_file(path, label)
    else:
        mode = stat.S_IMODE(metadata.st_mode)
        credential_directory = os.environ.get("CREDENTIALS_DIRECTORY", "").strip()
        is_systemd_credential = bool(
            credential_directory
            and Path(credential_directory).is_absolute()
            and path.parent == Path(credential_directory)
            and not Path(credential_directory).is_symlink()
        )
        if is_systemd_credential:
            if mode & 0o037:
                raise OwnerCallError(
                    f"{label} systemd credential must not be world accessible "
                    "or group writable/executable"
                )
        elif mode & 0o077:
            raise OwnerCallError(f"{label} file must not be group/world accessible")
    if metadata.st_size > 16_384:
        raise OwnerCallError(f"{label} file exceeds size bound")
    value = path.read_text(encoding="utf-8").strip()
    if not value or any(character.isspace() for character in value):
        raise OwnerCallError(f"{label} file must contain one non-whitespace value")
    return value


def _read_private_token_file(path_text: str) -> str:
    return _read_private_secret_file(path_text, "owner bearer token")


def _headers_for_endpoint(endpoint: OwnerEndpoint) -> dict[str, str] | None:
    if endpoint.bearer_token_file is not None:
        token = _read_private_token_file(endpoint.bearer_token_file)
        return {"Authorization": f"Bearer {token}"}
    if endpoint.access_client_id_file is not None:
        client_id = _read_private_secret_file(
            endpoint.access_client_id_file, "Cloudflare Access client ID"
        )
        client_secret = _read_private_secret_file(
            endpoint.access_client_secret_file or "",
            "Cloudflare Access client secret",
        )
        return {
            "CF-Access-Client-Id": client_id,
            "CF-Access-Client-Secret": client_secret,
        }
    return None
