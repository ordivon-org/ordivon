"""S3-compatible object storage client for Ordivon evidence.

Replaces local evidence files in docs/governance/evidence/ with S3/MinIO storage.
PG stores metadata (object_key, hash, content_type); S3 stores the blobs.

Usage:
    from ordivon_governance_core.s3_client import S3Client

    client = S3Client()
    client.upload_evidence("ev-001", b"content", "text/plain")
    data = client.download_evidence("ev-001")

Environment:
    ORDIVON_S3_ENDPOINT — S3 endpoint (default: http://localhost:9000)
    ORDIVON_S3_ACCESS_KEY — Access key (default: ordivon)
    ORDIVON_S3_SECRET_KEY — Secret key
    ORDIVON_S3_BUCKET — Bucket name (default: ordivon-evidence)
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

# boto3 imported lazily


class S3Client:
    """Minimal S3-compatible client for Ordivon evidence storage."""

    def __init__(
        self,
        endpoint: str = "",
        access_key: str = "",
        secret_key: str = "",
        bucket: str = "",
    ):
        self.endpoint = endpoint or os.environ.get("ORDIVON_S3_ENDPOINT", "http://localhost:9000")
        self.access_key = access_key or os.environ.get("ORDIVON_S3_ACCESS_KEY", "ordivon")
        self.secret_key = secret_key or os.environ.get("ORDIVON_S3_SECRET_KEY", "ordivon123")
        self.bucket = bucket or os.environ.get("ORDIVON_S3_BUCKET", "ordivon-evidence")
        self._client = None

    def _get_client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
        return self._client

    def ensure_bucket(self) -> bool:
        """Create the evidence bucket if it doesn't exist."""
        try:
            client = self._get_client()
            client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:
            try:
                client.create_bucket(Bucket=self.bucket)
                return True
            except Exception:
                return False

    def available(self) -> bool:
        """Check if S3 is reachable."""
        try:
            return self.ensure_bucket()
        except Exception:
            return False

    def upload_evidence(
        self,
        evidence_id: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict | None = None,
    ) -> dict:
        """Upload evidence blob to S3. Returns {object_key, sha256, size_bytes}."""
        client = self._get_client()
        sha = hashlib.sha256(data).hexdigest()
        key = f"evidence/{evidence_id}"

        client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            Metadata={**(metadata or {}), "sha256": sha},
        )

        return {
            "object_key": key,
            "sha256": sha,
            "size_bytes": len(data),
            "bucket": self.bucket,
        }

    def upload_file(self, evidence_id: str, filepath: str | Path) -> dict:
        """Upload a file as evidence."""
        path = Path(filepath)
        data = path.read_bytes()
        ext = path.suffix.lower()
        content_type = {
            ".txt": "text/plain",
            ".json": "application/json",
            ".jsonl": "application/jsonl",
            ".md": "text/markdown",
            ".png": "image/png",
            ".log": "text/plain",
        }.get(ext, "application/octet-stream")

        return self.upload_evidence(evidence_id, data, content_type)

    def download_evidence(self, evidence_id: str) -> bytes | None:
        """Download evidence blob from S3."""
        try:
            client = self._get_client()
            key = f"evidence/{evidence_id}"
            resp = client.get_object(Bucket=self.bucket, Key=key)
            return resp["Body"].read()
        except Exception:
            return None

    def list_evidence(self, prefix: str = "evidence/") -> list[dict]:
        """List evidence objects in the bucket."""
        try:
            client = self._get_client()
            resp = client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [
                {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                }
                for obj in resp.get("Contents", [])
            ]
        except Exception:
            return []

    def delete_evidence(self, evidence_id: str) -> bool:
        """Delete an evidence object."""
        try:
            client = self._get_client()
            key = f"evidence/{evidence_id}"
            client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


def get_client() -> S3Client:
    """Get the global S3 client instance."""
    return S3Client()
