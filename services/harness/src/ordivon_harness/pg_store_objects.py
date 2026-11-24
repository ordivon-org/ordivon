"""Original content-addressed immutable object operations.

Original PostgreSQL connection and existing transaction authority are retained.
"""

from __future__ import annotations
from anc_canonical import JsonValue, canonical_bytes, canonical_digest
from .store_errors import (
    HarnessObjectCorrupt,
)
from .store import (
    StoredHarnessObject,
)

from .pg_store_codec import decode_object_row

class PostgresObjects:
    """Original content-addressed immutable object operations."""

    def _object(self, value: JsonValue, kind: str, *, now_ms: int = 0) -> StoredHarnessObject:
        if not isinstance(kind, str) or not kind or kind != kind.strip():
            raise ValueError("Harness object kind must be non-empty and trimmed")
        raw = canonical_bytes(value)
        digest = canonical_digest(value)
        metadata = StoredHarnessObject(digest, len(raw), kind)
        self.connection.execute(
            "INSERT INTO objects(digest,kind,byte_length,content,first_seen_at_ms) "
            "VALUES (%s,%s,%s,%s,%s) ON CONFLICT(digest) DO NOTHING",
            (digest, kind, len(raw), raw, now_ms),
        )
        self._require_object(metadata)
        return metadata

    def _require_object(self, item: StoredHarnessObject) -> None:
        actual = self.inspect_object(item.digest)
        if actual != item:
            raise HarnessObjectCorrupt("Harness object metadata differs from committed digest")

    def put_object(self, value: JsonValue, *, kind: str) -> StoredHarnessObject:
        return self._object(value, kind)

    def get_object(self, digest: str, *, expected_kind: str | None = None) -> JsonValue:
        row = self.connection.execute(
            "SELECT kind,byte_length,content FROM objects WHERE digest=%s", (digest,)
        ).fetchone()
        return decode_object_row(digest, row, expected_kind=expected_kind)

    def inspect_object(self, digest: str) -> StoredHarnessObject:
        row = self.connection.execute(
            "SELECT kind,byte_length,content FROM objects WHERE digest=%s", (digest,)
        ).fetchone()
        decode_object_row(digest, row)
        assert row is not None  # successful decoder proves existence
        return StoredHarnessObject(digest, int(row["byte_length"]), row["kind"])
