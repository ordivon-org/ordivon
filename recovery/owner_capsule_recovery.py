#!/usr/bin/env python3
"""Operations-owned custody for owner-native recovery capsules.

The owner exporter defines capsule semantics. This module owns only generic local
transport: immutable invocation, restic snapshot/read-back, retention, repository
checks, and receipts. Daily backup deliberately excludes prune/full-check work.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "recovery/recovery.toml"
RESTIC = "/usr/bin/restic"
MOUNTPOINT = "/usr/bin/mountpoint"
LOCK_PATH = Path("/run/lock/ordivon-semantic-recovery.lock")


class RecoveryBusy(RuntimeError):
    def __init__(self, holder: dict[str, Any] | None = None) -> None:
        self.holder = holder
        super().__init__(f"recovery repository operation is already running: {holder or 'unknown holder'}")


class OperationLock:
    def __init__(self, operation: str, path: Path = LOCK_PATH) -> None:
        self.operation = operation
        self.path = path
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.handle.seek(0)
            raw = self.handle.read().strip()
            holder = None
            if raw:
                try:
                    value = json.loads(raw)
                    holder = value if isinstance(value, dict) else {"raw": raw}
                except json.JSONDecodeError:
                    holder = {"raw": raw}
            self.handle.close()
            self.handle = None
            raise RecoveryBusy(holder) from error
        holder = {
            "pid": os.getpid(),
            "operation": self.operation,
            "startedUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        self.handle.seek(0)
        self.handle.truncate()
        self.handle.write(json.dumps(holder, sort_keys=True) + "\n")
        self.handle.flush()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.handle is not None:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()
            self.handle = None


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checked(args: list[str], *, env: dict[str, str] | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, timeout=timeout, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stdout}{proc.stderr}")
    return proc


def restic_command(*args: str) -> list[str]:
    return [RESTIC, "--no-cache", *args]


def load_owner(owner: str, path: Path = CONFIG) -> dict[str, Any]:
    doc = tomllib.loads(path.read_text())
    owners = doc.get("owner_capsules")
    if not isinstance(owners, dict) or owner not in owners or not isinstance(owners[owner], dict):
        raise RuntimeError(f"owner capsule recovery config is absent: {owner}")
    value = dict(owners[owner])
    required = {
        "exporter", "repository", "password_file", "tag", "receipt", "attempt", "staging_parent",
        "retain_snapshots", "backup_timeout_seconds", "restore_timeout_seconds",
        "maintenance_timeout_seconds", "check_timeout_seconds",
    }
    missing = sorted(required - set(value))
    if missing:
        raise RuntimeError(f"owner capsule recovery config missing for {owner}: {missing}")
    value["owner"] = owner
    return value


def restic_env(cfg: dict[str, Any]) -> dict[str, str]:
    return {
        **os.environ,
        "RESTIC_REPOSITORY": str(cfg["repository"]),
        "RESTIC_PASSWORD_FILE": str(cfg["password_file"]),
    }


def require_transport(cfg: dict[str, Any]) -> None:
    checked([MOUNTPOINT, "-q", "/mnt/d"], timeout=10)
    password = Path(str(cfg["password_file"]))
    repository = Path(str(cfg["repository"]))
    if not password.is_file() or password.stat().st_size == 0:
        raise RuntimeError(f"restic password file missing: {password}")
    if not (repository / "config").is_file():
        raise RuntimeError(f"owner capsule restic repository is unavailable: {repository}")
    env = restic_env(cfg)
    checked(restic_command("cat", "config"), env=env, timeout=30)
    # Provider-native stale-lock reconciliation. Default unlock removes stale locks;
    # it is intentionally not --remove-all.
    checked(restic_command("unlock"), env=env, timeout=30)


def staging_parent(cfg: dict[str, Any]) -> Path:
    parent = Path(str(cfg["staging_parent"]))
    if parent.is_symlink():
        raise RuntimeError(f"owner capsule staging parent is symlinked: {parent}")
    parent.mkdir(parents=True, exist_ok=True)
    os.chmod(parent, 0o700)
    return parent


def resolved_exporter(cfg: dict[str, Any]) -> Path:
    selected = Path(str(cfg["exporter"]))
    try:
        resolved = selected.resolve(strict=True)
    except FileNotFoundError as error:
        raise RuntimeError(f"owner recovery exporter is unavailable: {selected}") from error
    if resolved.is_symlink() or not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise RuntimeError(f"owner recovery exporter is not executable: {resolved}")
    return resolved


def capsule_tree(root: Path) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"owner capsule root is unavailable or symlinked: {root}")
    rows: list[dict[str, Any]] = []
    total = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise RuntimeError(f"owner capsule contains symlink: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise RuntimeError(f"owner capsule contains unsupported entry: {relative}")
        size = path.stat().st_size
        digest = sha256_file(path)
        total += size
        rows.append({"path": relative, "bytes": size, "sha256": digest})
    if not rows:
        raise RuntimeError("owner capsule contains no files")
    identity = (json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return {"treeSha256": sha256_bytes(identity), "files": len(rows), "bytes": total, "entries": rows}


def snapshot_id_from_backup_json(text: str) -> str:
    found = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("message_type") == "summary" and value.get("snapshot_id"):
            found.append(str(value["snapshot_id"]))
    if len(found) != 1:
        raise RuntimeError(f"restic backup returned {len(found)} summary snapshot ids")
    return found[0]


def snapshot_metadata(cfg: dict[str, Any], snapshot_id: str) -> dict[str, Any]:
    proc = checked(restic_command("cat", "snapshot", snapshot_id), env=restic_env(cfg), timeout=60)
    value = json.loads(proc.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("invalid owner capsule snapshot metadata")
    return value


def write_receipt(path: Path, value: dict[str, Any]) -> None:
    checked([MOUNTPOINT, "-q", "/mnt/d"], timeout=10)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.chmod(temp, 0o600)
    os.replace(temp, path)


def owner_root_suffixes(owner: str) -> tuple[str, ...]:
    suffixes = [f"/owner-capsule-{owner}"]
    if owner == "finance":
        suffixes.append("/finance-recovery-custody")
    return tuple(suffixes)


def restored_owner_root(target: Path, owner: str) -> Path:
    matches: list[Path] = []
    for suffix in owner_root_suffixes(owner):
        matches.extend(target.rglob(suffix.lstrip("/") + "/transport.json"))
    matches = sorted(set(matches))
    if len(matches) != 1:
        raise RuntimeError(f"expected one restored owner capsule transport manifest for {owner}, found {len(matches)}")
    return matches[0].parent


def allowed_transport_kinds(owner: str) -> set[str]:
    kinds = {"ordivon.workstation.owner-capsule-transport.v1"}
    if owner == "finance":
        kinds.add("ordivon.workstation.finance-recovery-transport.v0")
    return kinds


def verify_restored_snapshot(cfg: dict[str, Any], snapshot_id: str, *, exporter: Path) -> dict[str, Any]:
    owner = str(cfg["owner"])
    metadata = snapshot_metadata(cfg, snapshot_id)
    paths = [str(item) for item in metadata.get("paths", [])]
    suffixes = owner_root_suffixes(owner)
    roots = [item.rstrip("/") for item in paths if any(item.rstrip("/").endswith(suffix) for suffix in suffixes)]
    if len(roots) != 1:
        raise RuntimeError(f"expected one {owner} capsule root in snapshot metadata, found {roots}")
    prefix = roots[0]
    with tempfile.TemporaryDirectory(prefix=f"ordivon-owner-{owner}-restore-", dir=staging_parent(cfg)) as raw:
        target = Path(raw)
        checked(
            restic_command("restore", snapshot_id, "--target", str(target), "--include", prefix + "/**"),
            env=restic_env(cfg), timeout=int(cfg["restore_timeout_seconds"]),
        )
        root = restored_owner_root(target, owner)
        transport_path = root / "transport.json"
        transport_bytes = transport_path.read_bytes()
        transport = json.loads(transport_bytes)
        if transport.get("kind") not in allowed_transport_kinds(owner) or transport.get("owner") != owner:
            raise RuntimeError("restored owner capsule transport manifest mismatch")
        capsule = root / "capsule"
        tree = capsule_tree(capsule)
        expected = transport.get("capsule") or {}
        if any((tree["treeSha256"] != expected.get("treeSha256"), tree["bytes"] != expected.get("bytes"), tree["files"] != expected.get("files"))):
            raise RuntimeError("restored owner capsule byte/topology identity mismatch")
        owner_verify = checked([str(exporter), "--verify", str(capsule)], timeout=int(cfg["restore_timeout_seconds"]))
        return {
            "snapshotId": snapshot_id,
            "transportKind": str(transport.get("kind")),
            "transportManifestSha256": sha256_bytes(transport_bytes),
            "capsuleTreeSha256": tree["treeSha256"],
            "capsuleFiles": tree["files"],
            "capsuleBytes": tree["bytes"],
            "ownerVerifyStdoutSha256": sha256_bytes(owner_verify.stdout.encode()),
            "ownerVerifySucceeded": True,
        }


def backup_locked(cfg: dict[str, Any]) -> dict[str, Any]:
    require_transport(cfg)
    owner = str(cfg["owner"])
    exporter = resolved_exporter(cfg)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with tempfile.TemporaryDirectory(prefix=f"ordivon-owner-{owner}-", dir=staging_parent(cfg)) as raw:
        stage = Path(raw) / f"owner-capsule-{owner}"
        stage.mkdir()
        capsule = stage / "capsule"
        owner_export = checked([str(exporter), "--export", str(capsule)], timeout=int(cfg["backup_timeout_seconds"]))
        tree = capsule_tree(capsule)
        transport = {
            "schemaVersion": 1,
            "kind": "ordivon.workstation.owner-capsule-transport.v1",
            "owner": owner,
            "createdUtc": stamp,
            "host": socket.gethostname(),
            "exporterResolved": str(exporter),
            "ownerExportStdoutSha256": sha256_bytes(owner_export.stdout.encode()),
            "capsule": {k: tree[k] for k in ("treeSha256", "files", "bytes")},
        }
        transport_path = stage / "transport.json"
        transport_path.write_text(json.dumps(transport, indent=2, sort_keys=True) + "\n")
        os.chmod(transport_path, 0o600)
        backup = checked(
            restic_command("backup", str(stage), "--tag", str(cfg["tag"]), "--json"),
            env=restic_env(cfg), timeout=int(cfg["backup_timeout_seconds"]),
        )
        snapshot_id = snapshot_id_from_backup_json(backup.stdout)
        readback = verify_restored_snapshot(cfg, snapshot_id, exporter=exporter)
        receipt = {
            "schemaVersion": 1,
            "kind": "ordivon.workstation.owner-capsule-recovery-receipt.v1",
            "status": "completed",
            "createdUtc": stamp,
            "snapshotId": snapshot_id,
            "repository": str(cfg["repository"]),
            "tag": str(cfg["tag"]),
            "owner": owner,
            "exporterResolved": str(exporter),
            "capsuleTreeSha256": tree["treeSha256"],
            "capsuleFiles": tree["files"],
            "capsuleBytes": tree["bytes"],
            "transportManifestSha256": sha256_file(transport_path),
            "ownerExportStdoutSha256": sha256_bytes(owner_export.stdout.encode()),
            "readback": readback,
            "maintenanceDeferred": True,
        }
        write_receipt(Path(str(cfg["receipt"])), receipt)
        write_receipt(Path(str(cfg["attempt"])), {**receipt, "effectAttempted": True})
        return receipt


def backup(cfg: dict[str, Any]) -> dict[str, Any]:
    with OperationLock(f"owner-capsule-backup:{cfg['owner']}"):
        return backup_locked(cfg)


def restore_test(cfg: dict[str, Any], snapshot_id: str | None = None) -> dict[str, Any]:
    with OperationLock(f"owner-capsule-restore-test:{cfg['owner']}"):
        require_transport(cfg)
        exporter = resolved_exporter(cfg)
        if snapshot_id is None:
            rows = json.loads(checked(restic_command("snapshots", "--json", "--tag", str(cfg["tag"])), env=restic_env(cfg), timeout=60).stdout or "[]")
            if not isinstance(rows, list) or not rows:
                raise RuntimeError("no owner capsule snapshot exists")
            snapshot_id = str(max(rows, key=lambda row: str(row.get("time", "")))["id"])
        result = verify_restored_snapshot(cfg, snapshot_id, exporter=exporter)
        return {"schemaVersion": 1, "kind": "ordivon.workstation.owner-capsule-restore-test.v1", "status": "pass", "owner": cfg["owner"], **result}


def retention(cfg: dict[str, Any]) -> dict[str, Any]:
    with OperationLock(f"owner-capsule-retention:{cfg['owner']}"):
        require_transport(cfg)
        checked(
            restic_command("forget", "--tag", str(cfg["tag"]), "--group-by", "host,tags", "--keep-last", str(cfg["retain_snapshots"]), "--prune"),
            env=restic_env(cfg), timeout=int(cfg["maintenance_timeout_seconds"]),
        )
        return {"schemaVersion": 1, "kind": "ordivon.workstation.owner-capsule-retention.v1", "status": "pass", "owner": cfg["owner"], "retainSnapshots": int(cfg["retain_snapshots"])}


def repository_check(cfg: dict[str, Any]) -> dict[str, Any]:
    with OperationLock(f"owner-capsule-check:{cfg['owner']}"):
        require_transport(cfg)
        proc = checked(restic_command("check"), env=restic_env(cfg), timeout=int(cfg["check_timeout_seconds"]))
        return {"schemaVersion": 1, "kind": "ordivon.workstation.owner-capsule-check.v1", "status": "pass", "owner": cfg["owner"], "outputSha256": sha256_bytes(proc.stdout.encode())}


def main() -> int:
    parser = argparse.ArgumentParser(description="Operations-owned transport for owner-native recovery capsules.")
    parser.add_argument("--owner", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--backup", action="store_true")
    mode.add_argument("--restore-test", action="store_true")
    mode.add_argument("--retention", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--snapshot-id")
    args = parser.parse_args()
    cfg = load_owner(args.owner)
    try:
        if args.backup:
            result = backup(cfg)
        elif args.restore_test:
            result = restore_test(cfg, args.snapshot_id)
        elif args.retention:
            result = retention(cfg)
        elif args.check:
            result = repository_check(cfg)
        else:
            exporter = resolved_exporter(cfg)
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.workstation.owner-capsule-plan.v1",
                "owner": cfg["owner"],
                "exporterResolved": str(exporter),
                "repository": str(cfg["repository"]),
                "tag": str(cfg["tag"]),
                "dailyPathIncludesMaintenance": False,
            }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except RecoveryBusy as error:
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.workstation.owner-capsule-attempt.v1",
            "status": "deferred",
            "owner": cfg["owner"],
            "effectAttempted": False,
            "reason": "shared-recovery-repository-busy",
            "holder": error.holder,
        }
        if args.backup:
            try:
                write_receipt(Path(str(cfg["attempt"])), result)
            except Exception:
                pass
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as error:
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.workstation.owner-capsule-attempt.v1",
            "status": "failed",
            "owner": cfg["owner"],
            "effectAttempted": bool(args.backup or args.retention or args.check),
            "error": str(error),
        }
        if args.backup:
            try:
                write_receipt(Path(str(cfg["attempt"])), result)
            except Exception:
                pass
        print(json.dumps(result, indent=2, sort_keys=True), file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
