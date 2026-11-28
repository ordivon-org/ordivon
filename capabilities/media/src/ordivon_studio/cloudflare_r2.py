"""Cloudflare R2 exact-digest Blob replication and restore policy.

Transport and credential materialization are delegated to the native curl
provider, without promoting R2 to Media source truth or a general Blob store.
"""

from __future__ import annotations

import os
from pathlib import Path

from .assets import hash_file, r2_object_key
from .cloudflare_r2_transport import (
    _PROVIDER,
    _curl_upload,
    _load_credentials,
    _object_url,
    _verified_remote_download,
)


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
