#!/usr/bin/env python3
"""Digest-fenced ingress into operator-owned Runtime input authorities.

This is a Workstation/node materialization owner. It fetches an exact object through one
operator-configured read-only carrier, verifies size and SHA-256, then atomically admits the
bytes beneath one operator-configured named authority. Runtime remains the independent
consumer and re-verifies the same digest through workspace.execBound.

The durable request ledger contains metadata/provenance only. It never stores source bytes,
credentials, bearer tokens, signed URLs, OAuth material, or provider stderr.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

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
SECRETISH = ("token", "secret", "cookie", "credential", "oauth", "password", "signedurl", "authorization")


class IngressError(RuntimeError):
    pass


class IngressConflict(IngressError):
    pass


class Fetcher(Protocol):
    def fetch(self, source: str, target: Path, *, max_bytes: int) -> None: ...


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


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
        result["parentObjectDigest"] = _validate_sha256(result["parentObjectDigest"], "sourceProvenance.parentObjectDigest")
    return result


def _validate_request(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("schemaVersion") != 1:
        raise IngressError("request must be schemaVersion 1")
    allowed = {
        "schemaVersion", "requestId", "carrier", "sourceObject", "sourceProvenance",
        "expectedSha256", "authority", "relativeObject",
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
            prefix = _clean_text(row.get("sourcePrefix"), f"carrier {name} sourcePrefix", max_len=1024)
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


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_json_atomic(path: Path, value: dict[str, Any], mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(_canonical_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
        _fsync_dir(path.parent)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _state_paths(state_dir: Path, request_id: str) -> tuple[Path, Path, Path]:
    key = hashlib.sha256(request_id.encode("utf-8")).hexdigest()
    request_dir = state_dir / "requests"
    staging_dir = state_dir / "staging"
    return request_dir / f"{key}.intent.json", request_dir / f"{key}.receipt.json", staging_dir / f"{key}.source.part"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_file(path: Path, max_bytes: int) -> tuple[int, str]:
    size = 0
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise IngressError("source object exceeds configured maximum size")
            digest.update(chunk)
    return size, SHA256_PREFIX + digest.hexdigest()


def _open_root(root: Path) -> int:
    try:
        st = os.lstat(root)
    except FileNotFoundError as error:
        raise IngressError("configured authority root does not exist") from error
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise IngressError("configured authority root must be one real directory, not a symlink")
    return os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def _open_parent(root: Path, relative_object: str, *, create: bool) -> tuple[int | None, str]:
    parts = PurePosixPath(relative_object).parts
    root_fd = _open_root(root)
    current = root_fd
    try:
        for part in parts[:-1]:
            try:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    os.close(current)
                    return None, parts[-1]
                os.mkdir(part, 0o755, dir_fd=current)
                os.fsync(current)
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            except OSError as error:
                raise IngressError("authority path contains a symlink or non-directory component") from error
            os.close(current)
            current = child
        return current, parts[-1]
    except Exception:
        try:
            os.close(current)
        except OSError:
            pass
        raise


def _hash_openat(parent_fd: int, name: str, max_bytes: int) -> tuple[int, str]:
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except OSError as error:
        raise IngressError("destination object is not a safe regular file") from error
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise IngressError("destination object is not a regular file")
        size = 0
        digest = hashlib.sha256()
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise IngressError("destination object exceeds configured maximum size")
            digest.update(chunk)
        return size, SHA256_PREFIX + digest.hexdigest()
    finally:
        os.close(fd)


def _destination_state(root: Path, relative_object: str, expected: str, max_bytes: int) -> tuple[str, int | None, str | None]:
    parent_fd, name = _open_parent(root, relative_object, create=False)
    if parent_fd is None:
        return "absent", None, None
    try:
        try:
            os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return "absent", None, None
        size, digest = _hash_openat(parent_fd, name, max_bytes)
        return ("exact" if digest == expected else "conflict"), size, digest
    finally:
        os.close(parent_fd)


def _commit_verified(source: Path, root: Path, relative_object: str, expected: str, max_bytes: int, request_digest: str) -> tuple[str, int, str]:
    parent_fd, name = _open_parent(root, relative_object, create=True)
    assert parent_fd is not None
    temp_name = f".ordivon-ingress-{request_digest[7:23]}.tmp"
    try:
        try:
            existing_size, existing_digest = _hash_openat(parent_fd, name, max_bytes)
            if existing_digest == expected:
                return "existing", existing_size, existing_digest
            raise IngressConflict("destination already exists with a different digest")
        except FileNotFoundError:
            pass
        except IngressError as error:
            # _hash_openat wraps unsafe destination opens. Distinguish ordinary absence above.
            try:
                os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise error

        try:
            os.unlink(temp_name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o640, dir_fd=parent_fd)
        size = 0
        digest = hashlib.sha256()
        try:
            with source.open("rb") as input_handle:
                while True:
                    chunk = input_handle.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise IngressError("source object exceeds configured maximum size during commit")
                    digest.update(chunk)
                    view = memoryview(chunk)
                    while view:
                        written = os.write(fd, view)
                        view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        actual = SHA256_PREFIX + digest.hexdigest()
        if actual != expected:
            raise IngressError("source changed after verification before local commit")
        try:
            os.link(temp_name, name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd, follow_symlinks=False)
            standing = "created"
        except FileExistsError:
            existing_size, existing_digest = _hash_openat(parent_fd, name, max_bytes)
            if existing_digest != expected:
                raise IngressConflict("destination appeared concurrently with a different digest")
            size = existing_size
            actual = existing_digest
            standing = "existing"
        os.fsync(parent_fd)
        return standing, size, actual
    finally:
        try:
            os.unlink(temp_name, dir_fd=parent_fd)
            os.fsync(parent_fd)
        except FileNotFoundError:
            pass
        finally:
            os.close(parent_fd)


class LocalStageFetcher:
    """Read one exact regular object beneath an operator-configured local staging root.

    Callers provide only a normalized relative source object. The root is configuration
    authority, never request authority. Symlinked roots, parent components, and terminal
    objects fail closed.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def fetch(self, source: str, target: Path, *, max_bytes: int) -> None:
        relative = _relative(source, "local-stage sourceObject")
        parts = PurePosixPath(relative).parts
        root_fd = _open_root(self.root)
        current = root_fd
        fd: int | None = None
        try:
            for part in parts[:-1]:
                try:
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
                except OSError as error:
                    raise IngressError("local-stage source path contains an unavailable, symlink, or non-directory component") from error
                os.close(current)
                current = child
            try:
                fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=current)
            except OSError as error:
                raise IngressError("local-stage source object is unavailable or unsafe") from error
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise IngressError("local-stage source object must be a regular file")
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                target.unlink()
            except FileNotFoundError:
                pass
            out_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            copied = 0
            try:
                while True:
                    chunk = os.read(fd, min(1024 * 1024, max_bytes + 1 - copied))
                    if not chunk:
                        break
                    copied += len(chunk)
                    view = memoryview(chunk)
                    while view:
                        written = os.write(out_fd, view)
                        view = view[written:]
                    if copied > max_bytes:
                        break
                os.fsync(out_fd)
            finally:
                os.close(out_fd)
        finally:
            if fd is not None:
                os.close(fd)
            os.close(current)


class RcloneFetcher:
    def __init__(self, executable: str = "/usr/bin/rclone") -> None:
        self.executable = executable

    def fetch(self, source: str, target: Path, *, max_bytes: int) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.unlink()
        except FileNotFoundError:
            pass
        # rclone's single-file copyto rejects filter-style --max-size on some maintained
        # versions. cat --count gives a stronger byte ceiling: the carrier emits at most
        # max_bytes+1 bytes, allowing the caller to distinguish exact-fit from oversized
        # without downloading an unbounded object or buffering it in memory.
        with target.open("wb") as handle:
            proc = subprocess.run(
                [self.executable, "cat", "--count", str(max_bytes + 1), source],
                stdout=handle,
                stderr=subprocess.DEVNULL,
                timeout=300,
                check=False,
            )
            handle.flush()
            os.fsync(handle.fileno())
        if proc.returncode != 0:
            try:
                target.unlink()
            except FileNotFoundError:
                pass
            raise IngressError(f"rclone source fetch failed with exit code {proc.returncode}")


def _receipt_body(request: dict[str, Any], request_digest: str, *, standing: str, byte_size: int | None = None, observed_digest: str | None = None, recovered: bool = False) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.input-authority-ingress-receipt",
        "truthRole": "byte-materialization-only-not-domain-acceptance",
        "requestId": request["requestId"],
        "requestDigest": request_digest,
        "source": {
            "carrier": request["carrier"],
            "sourceObject": request["sourceObject"],
            "provenance": request["sourceProvenance"],
            "provenanceStanding": "DECLARED_UNVERIFIED",
        },
        "expectedSha256": request["expectedSha256"],
        "authority": request["authority"],
        "relativeObject": request["relativeObject"],
        "byteSize": byte_size,
        "observedSha256": observed_digest,
        "commitStanding": standing,
        "recoveredAfterResponseLoss": recovered,
        "recordedAtMs": int(time.time() * 1000),
        "nonClaims": ["domain acceptance", "consumer execution success", "provider authorization beyond source fetch"],
    }


def _finalize_receipt(path: Path, body: dict[str, Any]) -> dict[str, Any]:
    receipt = {**body, "receiptDigest": _digest(body)}
    _write_json_atomic(path, receipt)
    return receipt


def _ingest_locked(
    config: dict[str, Any],
    request: dict[str, Any],
    request_digest: str,
    fetcher: Fetcher | None,
    *,
    reconcile_only: bool = False,
) -> dict[str, Any]:
    state_dir: Path = config["stateDir"]
    intent_path, receipt_path, staging_path = _state_paths(state_dir, request["requestId"])
    intent = {"schemaVersion": 1, "kind": "ordivon.workstation.input-authority-ingress-intent", "requestDigest": request_digest, "request": request}
    if intent_path.exists():
        retained = _read_json(intent_path)
        if retained.get("requestDigest") != request_digest or retained.get("request") != request:
            raise IngressConflict("same durable requestId changed ingress request")
    else:
        _write_json_atomic(intent_path, intent)

    root: Path = config["authorities"][request["authority"]]
    max_bytes: int = config["maxBytes"]
    if receipt_path.exists():
        receipt = _read_json(receipt_path)
        if receipt.get("requestDigest") != request_digest:
            raise IngressConflict("durable receipt identity conflicts with request")
        if str(receipt.get("commitStanding", "")).startswith("COMMITTED"):
            state, _size, _digest_value = _destination_state(root, request["relativeObject"], request["expectedSha256"], max_bytes)
            if state != "exact":
                raise IngressConflict("committed receipt no longer matches destination bytes")
        return receipt

    try:
        state, existing_size, existing_digest = _destination_state(root, request["relativeObject"], request["expectedSha256"], max_bytes)
    except IngressError:
        return _finalize_receipt(receipt_path, _receipt_body(request, request_digest, standing="REJECTED_DESTINATION_UNSAFE"))
    if state == "exact":
        return _finalize_receipt(receipt_path, _receipt_body(request, request_digest, standing="COMMITTED_RECOVERED", byte_size=existing_size, observed_digest=existing_digest, recovered=True))
    if state == "conflict":
        return _finalize_receipt(receipt_path, _receipt_body(request, request_digest, standing="REJECTED_DESTINATION_CONFLICT", byte_size=existing_size, observed_digest=existing_digest))

    if reconcile_only:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.workstation.input-authority-ingress-reconciliation",
            "truthRole": "source-fetch-admission-only-not-byte-materialization",
            "requestId": request["requestId"],
            "requestDigest": request_digest,
            "authority": request["authority"],
            "relativeObject": request["relativeObject"],
            "expectedSha256": request["expectedSha256"],
            "standing": "SOURCE_REQUIRED",
            "nonClaims": [
                "source availability",
                "source authorization",
                "byte materialization",
                "domain acceptance",
            ],
        }

    carrier = config["carriers"][request["carrier"]]
    if fetcher is not None:
        source = request["sourceObject"]
        selected_fetcher = fetcher
    elif carrier["kind"] == "rclone":
        source = carrier["sourcePrefix"] + request["sourceObject"]
        selected_fetcher = RcloneFetcher()
    elif carrier["kind"] == "local-stage":
        source = request["sourceObject"]
        selected_fetcher = LocalStageFetcher(carrier["sourceRoot"])
    else:  # validation makes this unreachable; retain fail-closed dispatch.
        raise IngressError("unsupported configured carrier kind")
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        selected_fetcher.fetch(source, staging_path, max_bytes=max_bytes)
        try:
            byte_size, observed = _hash_file(staging_path, max_bytes)
        except IngressError:
            return _finalize_receipt(receipt_path, _receipt_body(request, request_digest, standing="REJECTED_OVERSIZED"))
        if observed != request["expectedSha256"]:
            return _finalize_receipt(receipt_path, _receipt_body(request, request_digest, standing="REJECTED_SOURCE_DIGEST", byte_size=byte_size, observed_digest=observed))
        try:
            disposition, byte_size, observed = _commit_verified(staging_path, root, request["relativeObject"], request["expectedSha256"], max_bytes, request_digest)
        except IngressConflict:
            state, existing_size, existing_digest = _destination_state(root, request["relativeObject"], request["expectedSha256"], max_bytes)
            if state == "exact":
                return _finalize_receipt(receipt_path, _receipt_body(request, request_digest, standing="COMMITTED_CONCURRENT_REPLAY", byte_size=existing_size, observed_digest=existing_digest, recovered=True))
            return _finalize_receipt(receipt_path, _receipt_body(request, request_digest, standing="REJECTED_DESTINATION_CONFLICT", byte_size=existing_size, observed_digest=existing_digest))
        standing = "COMMITTED_NEW" if disposition == "created" else "COMMITTED_EXISTING"
        return _finalize_receipt(receipt_path, _receipt_body(request, request_digest, standing=standing, byte_size=byte_size, observed_digest=observed))
    finally:
        try:
            staging_path.unlink()
        except FileNotFoundError:
            pass


def ingest(
    config_raw: Any,
    request_raw: Any,
    *,
    fetcher: Fetcher | None = None,
    reconcile_only: bool = False,
) -> dict[str, Any]:
    config = _validate_config(config_raw)
    request = _validate_request(request_raw)
    if request["carrier"] not in config["carriers"]:
        raise IngressError("request references an unknown carrier")
    if request["authority"] not in config["authorities"]:
        raise IngressError("request references an unknown authority")
    request_digest = _digest(request)
    state_dir: Path = config["stateDir"]
    state_dir.mkdir(parents=True, exist_ok=True)
    if stat.S_ISLNK(os.lstat(state_dir).st_mode) or not state_dir.is_dir():
        raise IngressError("config stateDir must be one real directory")
    os.chmod(state_dir, 0o700)
    lock_dir = state_dir / "requests"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_key = hashlib.sha256(request["requestId"].encode("utf-8")).hexdigest()
    lock_fd = os.open(lock_dir / f"{lock_key}.lock", os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        return _ingest_locked(
            config,
            request,
            request_digest,
            fetcher,
            reconcile_only=reconcile_only,
        )
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="operator-owned ingress config JSON")
    parser.add_argument("--request", required=True, help="metadata-only ingress request JSON")
    parser.add_argument(
        "--reconcile-only",
        action="store_true",
        help="freeze/reconcile durable request and destination truth without fetching source bytes",
    )
    args = parser.parse_args()
    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        receipt = ingest(config, request, reconcile_only=args.reconcile_only)
    except (IngressError, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"schemaVersion": 1, "kind": "ordivon.workstation.input-authority-ingress-error", "error": type(error).__name__, "detail": str(error)[:500]}, sort_keys=True))
        return 2
    print(json.dumps(receipt, sort_keys=True))
    if str(receipt.get("commitStanding", "")).startswith("COMMITTED"):
        return 0
    if args.reconcile_only and receipt.get("standing") == "SOURCE_REQUIRED":
        return 0
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
