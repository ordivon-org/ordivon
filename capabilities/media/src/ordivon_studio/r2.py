from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

from .assets import hash_file, r2_object_key


_PROVIDER = "cloudflare-r2-account-api"
_DEFAULT_API_BASE = "https://api.cloudflare.com/client/v4"


def _load_credentials(path: Path) -> tuple[str, str, str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    account_id = document.get("account_id")
    api_token = document.get("api_token")
    api_base = document.get("api_base", _DEFAULT_API_BASE)
    if not isinstance(account_id, str) or not account_id:
        raise ValueError(f"R2 credential file lacks account_id: {path}")
    if not isinstance(api_token, str) or not api_token:
        raise ValueError(f"R2 credential file lacks api_token: {path}")
    if not isinstance(api_base, str) or not api_base.startswith("https://"):
        raise ValueError(f"R2 credential file has unsupported api_base: {path}")
    return account_id, api_token, api_base.rstrip("/")


def _object_url(*, api_base: str, account_id: str, bucket: str, object_key: str) -> str:
    return (
        f"{api_base}/accounts/{quote(account_id, safe='')}/r2/buckets/"
        f"{quote(bucket, safe='-')}/objects/{quote(object_key, safe='/')}"
    )


def _auth_header_file(api_token: str) -> tempfile.NamedTemporaryFile[str]:
    handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix=".ordivon-r2-auth-", delete=False)
    try:
        os.chmod(handle.name, 0o600)
        handle.write(f"Authorization: Bearer {api_token}\n")
        handle.flush()
        os.fsync(handle.fileno())
        return handle
    except Exception:
        handle.close()
        Path(handle.name).unlink(missing_ok=True)
        raise


def _curl_download(*, url: str, api_token: str, destination: Path, curl: str) -> int:
    auth = _auth_header_file(api_token)
    auth.close()
    try:
        result = subprocess.run(
            [
                curl,
                "-sS",
                "--connect-timeout",
                "8",
                "--max-time",
                "120",
                "-o",
                str(destination),
                "-w",
                "%{http_code}",
                "-H",
                f"@{auth.name}",
                url,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        Path(auth.name).unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"R2 download transport failed with curl exit {result.returncode}")
    try:
        return int(result.stdout.strip())
    except ValueError as error:
        raise RuntimeError("R2 download returned no HTTP status") from error


def _curl_upload(*, url: str, api_token: str, source: Path, curl: str) -> int:
    auth = _auth_header_file(api_token)
    auth.close()
    response_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".ordivon-r2-upload-response-", delete=False) as response:
            response_path = Path(response.name)
        result = subprocess.run(
            [
                curl,
                "-sS",
                "--connect-timeout",
                "8",
                "--max-time",
                "120",
                "-o",
                str(response_path),
                "-w",
                "%{http_code}",
                "-X",
                "PUT",
                "-H",
                f"@{auth.name}",
                "-H",
                "Content-Type: application/octet-stream",
                "-H",
                f"Content-Length: {source.stat().st_size}",
                "--data-binary",
                f"@{source}",
                url,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        Path(auth.name).unlink(missing_ok=True)
        if response_path is not None:
            response_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"R2 upload transport failed with curl exit {result.returncode}")
    try:
        return int(result.stdout.strip())
    except ValueError as error:
        raise RuntimeError("R2 upload returned no HTTP status") from error


def _verified_remote_download(
    *,
    url: str,
    api_token: str,
    expected_digest: str,
    expected_size: int | None,
    directory: Path,
    curl: str,
) -> tuple[int, Path | None]:
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".ordivon-r2-download-", dir=directory, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    status = _curl_download(url=url, api_token=api_token, destination=temporary_path, curl=curl)
    if status == 404:
        temporary_path.unlink(missing_ok=True)
        return status, None
    if status != 200:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"R2 object request failed with HTTP {status}")
    remote = hash_file(temporary_path)
    if remote.digest != expected_digest or (expected_size is not None and remote.size_bytes != expected_size):
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError("R2 digest address contains different bytes")
    return status, temporary_path


def replicate_r2_blob(
    path: Path,
    *,
    bucket: str,
    credentials_path: Path,
    curl: str = "/usr/bin/curl",
) -> dict[str, object]:
    """Copy one exact local Blob to Cloudflare R2 without overwriting divergent bytes."""
    blob = hash_file(path)
    object_key = r2_object_key(blob.digest)
    account_id, api_token, api_base = _load_credentials(credentials_path)
    url = _object_url(api_base=api_base, account_id=account_id, bucket=bucket, object_key=object_key)

    _, existing_path = _verified_remote_download(
        url=url,
        api_token=api_token,
        expected_digest=blob.digest,
        expected_size=blob.size_bytes,
        directory=path.parent,
        curl=curl,
    )
    if existing_path is not None:
        existing_path.unlink(missing_ok=True)
        disposition = "existing"
    else:
        status = _curl_upload(url=url, api_token=api_token, source=path, curl=curl)
        if status != 200:
            raise RuntimeError(f"R2 upload failed with HTTP {status}")
        _, verified_path = _verified_remote_download(
            url=url,
            api_token=api_token,
            expected_digest=blob.digest,
            expected_size=blob.size_bytes,
            directory=path.parent,
            curl=curl,
        )
        if verified_path is None:
            raise RuntimeError("R2 object disappeared after successful upload")
        verified_path.unlink(missing_ok=True)
        disposition = "created"

    return {
        "blob": blob.as_dict(),
        "replica": {"provider": _PROVIDER, "bucket": bucket, "objectKey": object_key},
        "disposition": disposition,
        "verified": True,
        "remoteWriteModel": "single-writer-preflight-plus-redownload-verification",
    }


def restore_r2_blob(
    digest: str,
    cache_root: Path,
    *,
    bucket: str,
    credentials_path: Path,
    curl: str = "/usr/bin/curl",
) -> dict[str, object]:
    """Restore one exact R2 Blob into the verified local content-addressed cache."""
    object_key = r2_object_key(digest)
    destination = cache_root / object_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    account_id, api_token, api_base = _load_credentials(credentials_path)
    url = _object_url(api_base=api_base, account_id=account_id, bucket=bucket, object_key=object_key)

    _, remote_path = _verified_remote_download(
        url=url,
        api_token=api_token,
        expected_digest=digest,
        expected_size=None,
        directory=destination.parent,
        curl=curl,
    )
    if remote_path is None:
        raise FileNotFoundError(f"R2 object is absent: {bucket}/{object_key}")
    remote = hash_file(remote_path)
    try:
        if destination.exists():
            existing = hash_file(destination)
            if existing.digest != digest or existing.size_bytes != remote.size_bytes:
                raise RuntimeError(f"local digest address contains different bytes: {destination}")
            disposition = "existing"
        else:
            try:
                os.link(remote_path, destination)
                disposition = "created"
            except FileExistsError:
                existing = hash_file(destination)
                if existing.digest != digest or existing.size_bytes != remote.size_bytes:
                    raise RuntimeError(f"local digest address contains different bytes: {destination}")
                disposition = "existing"

        restored = hash_file(destination)
        if restored.digest != digest or restored.size_bytes != remote.size_bytes:
            raise RuntimeError("restored local R2 Blob verification failed")
        return {
            "blob": restored.as_dict(),
            "replica": {"provider": _PROVIDER, "bucket": bucket, "objectKey": object_key},
            "cachePath": str(destination),
            "disposition": disposition,
            "verified": True,
        }
    finally:
        remote_path.unlink(missing_ok=True)
