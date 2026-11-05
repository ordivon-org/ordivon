from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat
import uuid

from anc_canonical import JsonValue, canonical_bytes, canonical_digest, loads_strict

from .store import StoredHarnessObject
from .store_errors import HarnessObjectCorrupt, HarnessObjectMissing


@dataclass(frozen=True, slots=True)
class _ObjectFileIdentity:
    device: int
    inode: int
    byte_length: int
    modified_at_ns: int
    changed_at_ns: int
    mode: int

    @classmethod
    def from_stat(cls, value: os.stat_result) -> _ObjectFileIdentity:
        return cls(
            device=int(value.st_dev),
            inode=int(value.st_ino),
            byte_length=int(value.st_size),
            modified_at_ns=int(value.st_mtime_ns),
            changed_at_ns=int(value.st_ctime_ns),
            mode=stat.S_IMODE(value.st_mode),
        )

    def to_sql(self) -> tuple[int, int, int, int, int, int]:
        return (
            self.device,
            self.inode,
            self.byte_length,
            self.modified_at_ns,
            self.changed_at_ns,
            self.mode,
        )

    def stable_read_identity(self) -> tuple[int, int, int, int, int]:
        # ctime changes when an already-published inode loses a temporary hard-link.
        # Content address, inode, size, mtime and mode are the stable read facts.
        return (
            self.device,
            self.inode,
            self.byte_length,
            self.modified_at_ns,
            self.mode,
        )


class _ContentAddressedStore:
    def __init__(self, root: Path) -> None:
        if root.exists() and root.is_symlink():
            raise HarnessObjectCorrupt("Harness object root cannot be a symlink")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not root.is_dir():
            raise HarnessObjectCorrupt("Harness object root is not a directory")
        os.chmod(root, 0o700)
        self.root = root
        for path in self.root.glob("*.json"):
            flags = os.O_RDONLY | os.O_NONBLOCK
            flags |= getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            try:
                descriptor = os.open(path, flags)
            except OSError as error:
                raise HarnessObjectCorrupt(
                    f"Harness object path cannot be safely opened: {path.name}"
                ) from error
            try:
                file_stat = os.fstat(descriptor)
                if not stat.S_ISREG(file_stat.st_mode):
                    raise HarnessObjectCorrupt(
                        f"Harness object path is not a regular file: {path.name}"
                    )
                if stat.S_IMODE(file_stat.st_mode) != 0o600:
                    os.fchmod(descriptor, 0o600)
            finally:
                os.close(descriptor)

    def put(self, value: JsonValue, *, kind: str) -> StoredHarnessObject:
        if not kind or kind != kind.strip():
            raise ValueError("Harness object kind must be non-empty and trimmed")
        envelope: JsonValue = {
            "schemaVersion": 1,
            "kind": kind,
            "payload": value,
        }
        encoded = canonical_bytes(envelope)
        digest = canonical_digest(envelope)
        path = self._path(digest)
        try:
            existing_envelope, existing, _ = self._load(digest)
        except HarnessObjectMissing:
            pass
        else:
            if canonical_bytes(existing_envelope) != encoded:
                raise HarnessObjectCorrupt(
                    "Harness content address maps to different bytes"
                )
            return existing

        temporary = path.with_suffix(f".tmp-{os.getpid()}-{uuid.uuid4().hex}")
        directory_fd: int | None = None
        try:
            with temporary.open("xb") as handle:
                os.chmod(temporary, 0o600)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError:
                existing_envelope, existing, _ = self._load(digest)
                if canonical_bytes(existing_envelope) != encoded:
                    raise HarnessObjectCorrupt(
                        "Harness content address maps to different bytes"
                    )
                return existing
            temporary.unlink()
            directory_fd = os.open(
                self.root,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
            )
            os.fsync(directory_fd)
        finally:
            if directory_fd is not None:
                os.close(directory_fd)
            temporary.unlink(missing_ok=True)
        return StoredHarnessObject(digest, len(encoded), kind)

    def get(self, digest: str, *, expected_kind: str | None = None) -> JsonValue:
        envelope, stored, _ = self._load(digest)
        if expected_kind is not None and stored.kind != expected_kind:
            raise HarnessObjectCorrupt(
                f"Harness object kind is {stored.kind}, expected {expected_kind}"
            )
        return envelope["payload"]

    def inspect(self, digest: str) -> StoredHarnessObject:
        _, stored, _ = self._load(digest)
        return stored

    def inspect_with_identity(self, digest: str) -> tuple[StoredHarnessObject, _ObjectFileIdentity]:
        _, stored, identity = self._load(digest)
        return stored, identity

    def _load(
        self, digest: str
    ) -> tuple[dict[str, JsonValue], StoredHarnessObject, _ObjectFileIdentity]:
        path = self._path(digest)
        flags = os.O_RDONLY | os.O_NONBLOCK
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags)
        except FileNotFoundError as error:
            raise HarnessObjectMissing(f"Harness object is missing: {digest}") from error
        except OSError as error:
            raise HarnessObjectCorrupt(f"Harness object cannot be read: {digest}") from error
        try:
            before = _ObjectFileIdentity.from_stat(os.fstat(descriptor))
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                encoded = handle.read()
            after = _ObjectFileIdentity.from_stat(os.fstat(descriptor))
        except OSError as error:
            raise HarnessObjectCorrupt(f"Harness object cannot be read: {digest}") from error
        finally:
            os.close(descriptor)
        if (
            before.stable_read_identity() != after.stable_read_identity()
            or before.byte_length != len(encoded)
        ):
            raise HarnessObjectCorrupt(f"Harness object changed while read: {digest}")
        if before.mode != 0o600:
            raise HarnessObjectCorrupt(f"Harness object mode is not private: {digest}")
        try:
            value = loads_strict(encoded)
        except ValueError as error:
            raise HarnessObjectCorrupt(f"Harness object cannot be decoded: {digest}") from error
        if canonical_digest(value) != digest:
            raise HarnessObjectCorrupt("Harness object content differs from its address")
        if not isinstance(value, dict) or set(value) != {
            "schemaVersion",
            "kind",
            "payload",
        }:
            raise HarnessObjectCorrupt("Harness object envelope fields differ")
        if value["schemaVersion"] != 1 or not isinstance(value["kind"], str):
            raise HarnessObjectCorrupt("Harness object envelope version or kind is invalid")
        stored = StoredHarnessObject(digest, len(encoded), value["kind"])
        return value, stored, after

    def _path(self, digest: str) -> Path:
        if (
            not isinstance(digest, str)
            or len(digest) != 71
            or not digest.startswith("sha256:")
            or any(character not in "0123456789abcdef" for character in digest[7:])
        ):
            raise ValueError("Harness object key must be a sha256 digest")
        return self.root / f"{digest[7:]}.json"
