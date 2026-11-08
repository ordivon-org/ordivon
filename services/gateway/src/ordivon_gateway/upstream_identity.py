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
    """Read exact bounded credential bytes from the inode whose access is checked.

    POSIX: O_NOFOLLOW and same-FD fstat/read prevent final-symlink substitution
    and check-then-reopen races. Credential *directory* authority and secret
    immutability still belong to the deployment/OS; this is not a sandbox.
    Windows: correlate the verified path's file ID with the opened handle and
    recheck it afterwards; native ACL acceptance remains platform-scoped.
    """
    path = Path(path_text)
    if not path.is_absolute():
        raise OwnerCallError(f"{label} file must be absolute")

    windows = os.name == "nt"
    checked_path: os.stat_result | None = None
    if windows:
        checked_path = path.lstat()
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if not stat.S_ISREG(checked_path.st_mode) or (
            reparse_flag and getattr(checked_path, "st_file_attributes", 0) & reparse_flag
        ):
            raise OwnerCallError(f"{label} Windows credential must be a non-reparse regular file")
        _validate_windows_private_secret_file(path, label)
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    else:
        if not hasattr(os, "O_NOFOLLOW"):
            raise OwnerCallError(f"{label} requires native O_NOFOLLOW file access")
        # O_NONBLOCK prevents an unexpected FIFO from stalling before fstat.
        flags = (
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
        )

    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise OwnerCallError(f"{label} credential could not be opened securely") from exc

    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            raise OwnerCallError(f"{label} path must be a regular file")
        if windows:
            if checked_path is None or (checked_path.st_dev, checked_path.st_ino) != (
                opened.st_dev,
                opened.st_ino,
            ):
                raise OwnerCallError(f"{label} Windows credential path changed before open")
        else:
            mode = stat.S_IMODE(opened.st_mode)
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

        max_bytes = 16_384
        if opened.st_size > max_bytes:
            raise OwnerCallError(f"{label} file exceeds size bound")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining > 0:
            chunk = os.read(fd, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(fd)
        if len(raw) > max_bytes:
            raise OwnerCallError(f"{label} file exceeds size bound")
        if (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise OwnerCallError(f"{label} credential changed during read")
        if windows:
            # A replaced pathname must not confer credentials from a different
            # previously verified resource. This is not a Windows ACL-on-handle proof.
            current_path = path.lstat()
            if checked_path is None or (checked_path.st_dev, checked_path.st_ino) != (
                current_path.st_dev,
                current_path.st_ino,
            ):
                raise OwnerCallError(f"{label} Windows credential path changed")
    finally:
        os.close(fd)
    try:
        value = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise OwnerCallError(f"{label} file must contain UTF-8") from exc
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
