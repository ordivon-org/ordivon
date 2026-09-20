#!/usr/bin/env python3
"""Back up compact Agent semantic recovery state without promoting caches or domain evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = tomllib.loads(Path(__file__).with_name("recovery.toml").read_text())
REC = CFG["recovery"]
RESTIC = "/usr/bin/restic"
GIT = "/usr/bin/git"
DIRECT_WITNESS_MAX_BYTES = 1024 * 1024


def restic_command(*args: str) -> list[str]:
    return [RESTIC, "--no-cache", *args]


def semantic_retention_command() -> list[str]:
    """Retain semantic generations across random staging-path identities."""
    return restic_command(
        "forget",
        "--tag", str(REC["semantic_tag"]),
        "--group-by", "host,tags",
        "--keep-last", str(REC["retain_semantic_snapshots"]),
        "--prune",
    )


class RecoveryOperationBusy(RuntimeError):
    def __init__(self, operation: str, holder: dict[str, object] | None = None) -> None:
        self.operation = operation
        self.holder = holder
        super().__init__(f"semantic recovery operation is already running: {holder or 'unknown holder'}")


class OperationLock:
    def __init__(
        self,
        operation: str,
        path: str = "/run/lock/ordivon-semantic-recovery.lock",
    ) -> None:
        self.operation = operation
        self.path = Path(path)
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.handle.seek(0)
            raw_holder = self.handle.read().strip()
            holder = None
            if raw_holder:
                try:
                    parsed = json.loads(raw_holder)
                    holder = parsed if isinstance(parsed, dict) else {"raw": raw_holder}
                except json.JSONDecodeError:
                    holder = {"raw": raw_holder}
            self.handle.close()
            self.handle = None
            raise RecoveryOperationBusy(self.operation, holder) from error
        holder = {
            "pid": os.getpid(),
            "operation": self.operation,
            "startedUtc": dt.datetime.now(dt.UTC).isoformat(),
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


def run(args: list[str], *, env: dict[str, str] | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=timeout,
        check=False,
    )
    return proc


def checked(args: list[str], *, env: dict[str, str] | None = None, timeout: int = 60) -> str:
    proc = run(args, env=env, timeout=timeout)
    if proc.returncode != 0:
        command = " ".join(args)
        raise RuntimeError(f"command failed ({proc.returncode}): {command}\n{proc.stdout}{proc.stderr}")
    return proc.stdout


def checked_bytes(args: list[str], *, env: dict[str, str] | None = None, timeout: int = 60) -> bytes:
    proc = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        command = " ".join(args)
        stderr = proc.stderr.decode(errors="replace")
        raise RuntimeError(f"command failed ({proc.returncode}): {command}\n{stderr}")
    return proc.stdout


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_direct_path_witness(root: Path) -> dict[str, object]:
    if root.is_file():
        size = root.stat().st_size
        if size > DIRECT_WITNESS_MAX_BYTES:
            raise RuntimeError(f"direct recovery file exceeds witness bound: {root} ({size} bytes)")
        return {
            "root": str(root),
            "witnessPath": str(root),
            "bytes": size,
            "sha256": sha256_file(root),
            "kind": "file",
        }
    if not root.is_dir():
        raise RuntimeError(f"direct recovery root is not a regular file or directory: {root}")
    for current, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            candidate = Path(current) / name
            if not candidate.is_file() or candidate.is_symlink():
                continue
            size = candidate.stat().st_size
            if size > DIRECT_WITNESS_MAX_BYTES:
                continue
            return {
                "root": str(root),
                "witnessPath": str(candidate),
                "bytes": size,
                "sha256": sha256_file(candidate),
                "kind": "directory-file",
            }
    raise RuntimeError(f"direct recovery directory has no bounded regular-file witness: {root}")


def verify_snapshot_witness(
    env: dict[str, str], snapshot_id: str, witness: dict[str, object]
) -> dict[str, object]:
    path = str(witness["witnessPath"])
    content = checked_bytes(
        restic_command("dump", snapshot_id, path),
        env=env,
        timeout=int(REC["semantic_restore_timeout_seconds"]),
    )
    observed_digest = hashlib.sha256(content).hexdigest()
    expected_digest = str(witness["sha256"])
    expected_bytes = int(witness["bytes"])
    if len(content) != expected_bytes or observed_digest != expected_digest:
        raise RuntimeError(
            "direct-path witness readback mismatch: "
            f"{path}: bytes {len(content)} != {expected_bytes} or sha256 {observed_digest} != {expected_digest}"
        )
    return {
        "root": str(witness["root"]),
        "witnessPath": path,
        "bytes": len(content),
        "sha256": observed_digest,
        "digestMatches": True,
    }


def restic_env() -> dict[str, str]:
    env = os.environ.copy()
    env["RESTIC_REPOSITORY"] = str(REC["semantic_repository"])
    env["RESTIC_PASSWORD_FILE"] = str(REC["restic_password_file"])
    return env


def require_mount(path: Path) -> None:
    mount = Path("/mnt/d")
    if not mount.is_mount():
        raise RuntimeError("/mnt/d is not mounted")
    try:
        path.resolve().relative_to(mount.resolve())
    except ValueError as error:
        raise RuntimeError(f"semantic recovery path must live on /mnt/d: {path}") from error


def semantic_staging_parent() -> Path:
    raw = REC.get("semantic_staging_parent")
    if not isinstance(raw, str) or not raw:
        raise RuntimeError("semantic_staging_parent is not configured")
    parent = Path(raw)
    if parent.is_symlink():
        raise RuntimeError(f"semantic recovery staging parent must not be a symlink: {parent}")
    parent.mkdir(parents=True, exist_ok=True)
    if not parent.is_dir():
        raise RuntimeError(f"semantic recovery staging parent is not a directory: {parent}")
    os.chmod(parent, 0o700)
    return parent


def canonical_repositories() -> list[Path]:
    repos: list[Path] = []
    control = Path(str(REC.get("control_repository") or ROOT))
    if (control / ".git").exists():
        repos.append(control)
    parent = Path(REC["semantic_project_parent"])
    for candidate in sorted(parent.iterdir() if parent.exists() else []):
        if candidate.is_dir() and (candidate / ".git").exists():
            repos.append(candidate)
    return repos


def git_text(repo: Path, *args: str, timeout: int = 20) -> str:
    return checked([GIT, "-C", str(repo), *args], timeout=timeout).strip()


def git_refs_digest(repo: Path) -> str:
    """Digest committed Git ref authority without depending on worktree cleanliness."""
    refs = git_text(repo, "for-each-ref", "--format=%(refname) %(objectname)")
    return hashlib.sha256((refs + "\n").encode()).hexdigest()


def git_record(repo: Path) -> dict[str, object]:
    status = git_text(repo, "status", "--porcelain=v1")
    head = git_text(repo, "rev-parse", "HEAD")
    refs_digest = git_refs_digest(repo)
    branch_proc = run([GIT, "-C", str(repo), "symbolic-ref", "--short", "-q", "HEAD"], timeout=10)
    branch = branch_proc.stdout.strip() if branch_proc.returncode == 0 else None
    upstream_proc = run([GIT, "-C", str(repo), "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], timeout=10)
    upstream = upstream_proc.stdout.strip() if upstream_proc.returncode == 0 else None
    ahead = behind = None
    if upstream:
        counts = git_text(repo, "rev-list", "--left-right", "--count", f"{upstream}...HEAD").split()
        if len(counts) == 2:
            behind, ahead = (int(counts[0]), int(counts[1]))
    worktrees: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line in git_text(repo, "worktree", "list", "--porcelain").splitlines():
        if not line:
            if current:
                worktrees.append(current)
                current = None
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            if current:
                worktrees.append(current)
            current = {"path": value}
        elif current is not None:
            if key in {"HEAD", "branch"}:
                current[key.lower()] = value
            elif key == "detached":
                current["detached"] = True
    if current:
        worktrees.append(current)
    return {
        "path": str(repo),
        "head": head,
        "refsDigest": refs_digest,
        "branch": branch,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "clean": not bool(status),
        "status": status.splitlines(),
        "worktrees": worktrees,
    }


def create_git_bundle(repo: Path, target: Path) -> dict[str, object]:
    # A dirty worktree is orthogonal to committed Git authority: `git bundle --all`
    # serializes refs/objects, not uncommitted files. Preserve dirty state as evidence,
    # but do not let unrelated owner work block committed-source recovery.
    before = git_record(repo)
    target.parent.mkdir(parents=True, exist_ok=True)
    checked([GIT, "-C", str(repo), "bundle", "create", str(target), "--all"], timeout=60)
    checked([GIT, "-C", str(repo), "bundle", "verify", str(target)], timeout=60)
    after = git_record(repo)
    if before["head"] != after["head"] or before["refsDigest"] != after["refsDigest"]:
        raise RuntimeError(f"committed Git authority changed while bundling: {repo}")
    heads = checked([GIT, "bundle", "list-heads", str(target)], timeout=30).splitlines()
    return {
        **after,
        "bundle": target.name,
        "bundleBytes": target.stat().st_size,
        "bundleSha256": sha256_file(target),
        "bundleRefs": len(heads),
    }


def sqlite_backup(source: Path, target: Path) -> dict[str, object]:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True, timeout=20) as src:
        with sqlite3.connect(target, timeout=20) as dst:
            src.backup(dst, pages=4096, sleep=0.01)
    with sqlite3.connect(target, timeout=20) as check:
        integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
        user_version = check.execute("PRAGMA user_version").fetchone()[0]
        page_count = check.execute("PRAGMA page_count").fetchone()[0]
        page_size = check.execute("PRAGMA page_size").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"SQLite backup integrity failed for {source}: {integrity}")
    return {
        "source": str(source),
        "backup": target.name,
        "sourceBytes": source.stat().st_size,
        "backupBytes": target.stat().st_size,
        "sha256": sha256_file(target),
        "integrity": integrity,
        "userVersion": user_version,
        "pageCount": page_count,
        "pageSize": page_size,
    }


def latest_authority() -> dict[str, object] | None:
    directory = Path(REC["authority_dir"])
    bundles = sorted(directory.glob(REC["authority_bundle_glob"]), key=lambda item: item.stat().st_mtime, reverse=True)
    if not bundles:
        return None
    bundle = bundles[0]
    return {
        "path": str(bundle),
        "sha256": sha256_file(bundle),
        "mtimeUtc": dt.datetime.fromtimestamp(bundle.stat().st_mtime, dt.UTC).isoformat(),
    }


def ensure_repository(env: dict[str, str]) -> None:
    repository = Path(REC["semantic_repository"])
    require_mount(repository)
    password = Path(REC["restic_password_file"])
    if not password.is_file() or password.stat().st_size == 0:
        raise RuntimeError(f"restic password file missing: {password}")
    config = repository / "config"
    if config.is_file():
        # Default restic unlock removes only stale locks. Never use --remove-all here:
        # a live repository user must remain authoritative over its active lock.
        # Unlock must precede any lock-taking repository probe, otherwise a stale
        # exclusive lock can prevent the recovery path from reaching its own repair.
        checked(restic_command("unlock"), env=env, timeout=30)
        checked(restic_command("cat", "config"), env=env, timeout=30)
        return
    if repository.exists() and any(repository.iterdir()):
        raise RuntimeError(f"refusing to initialize non-empty semantic repository: {repository}")
    repository.mkdir(parents=True, exist_ok=True)
    checked(restic_command("init"), env=env, timeout=60)


def snapshots(env: dict[str, str]) -> list[dict[str, object]]:
    raw = checked(restic_command("snapshots", "--json", "--tag", str(REC["semantic_tag"])), env=env, timeout=60)
    parsed = json.loads(raw or "[]")
    return parsed if isinstance(parsed, list) else []


def latest_snapshot(env: dict[str, str]) -> dict[str, object] | None:
    rows = snapshots(env)
    if not rows:
        return None
    return max(rows, key=lambda row: str(row.get("time", "")))


def write_receipt(path: Path, receipt: dict[str, object]) -> None:
    require_mount(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def write_attempt(attempt: dict[str, object]) -> None:
    write_receipt(Path(REC["semantic_attempt"]), attempt)


def build_plan() -> dict[str, object]:
    repos = [git_record(repo) for repo in canonical_repositories()]
    return {
        "schemaVersion": 1,
        "semanticRepository": str(REC["semantic_repository"]),
        "stagingParent": str(REC["semantic_staging_parent"]),
        "receipt": str(REC["semantic_receipt"]),
        "tag": str(REC["semantic_tag"]),
        "repositories": repos,
        "sqliteSources": list(REC["semantic_sqlite_sources"]),
        "directPaths": list(REC["semantic_direct_paths"]),
        "excludedByDesign": list(REC["semantic_excluded_by_design"]),
        "authority": latest_authority(),
    }


def apply_locked() -> dict[str, object]:
    plan = build_plan()
    for raw in list(REC["semantic_sqlite_sources"]) + list(REC["semantic_direct_paths"]):
        if not Path(raw).exists():
            raise FileNotFoundError(raw)
    env = restic_env()
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    with tempfile.TemporaryDirectory(prefix="ordivon-semantic-recovery-", dir=semantic_staging_parent()) as temp:
        stage = Path(temp) / "semantic-recovery"
        git_dir = stage / "git"
        db_dir = stage / "sqlite"
        git_rows = []
        for repo in canonical_repositories():
            git_rows.append(create_git_bundle(repo, git_dir / f"{repo.name}.bundle"))
        sqlite_rows = []
        for raw in REC["semantic_sqlite_sources"]:
            source = Path(raw)
            sqlite_rows.append(sqlite_backup(source, db_dir / source.name))
        direct_witnesses = [select_direct_path_witness(Path(raw)) for raw in REC["semantic_direct_paths"]]
        manifest = {
            **plan,
            "createdUtc": stamp,
            "host": socket.gethostname(),
            "git": git_rows,
            "sqlite": sqlite_rows,
            "directWitnesses": direct_witnesses,
        }
        manifest_path = stage / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        os.chmod(manifest_path, 0o600)
        sources = [str(stage)] + [str(Path(raw)) for raw in REC["semantic_direct_paths"]]
        for source in sources:
            if not Path(source).exists():
                raise FileNotFoundError(source)
        ensure_repository(env)
        checked(
            restic_command("backup", *sources, "--tag", str(REC["semantic_tag"])),
            env=env,
            timeout=int(REC["semantic_backup_timeout_seconds"]),
        )
        snapshot = latest_snapshot(env)
        if snapshot is None:
            raise RuntimeError("semantic restic snapshot was not discoverable after backup")
        snapshot_id = str(snapshot["id"])
        direct_readbacks = [verify_snapshot_witness(env, snapshot_id, row) for row in direct_witnesses]
        checked(
            semantic_retention_command(),
            env=env,
            timeout=int(REC["semantic_check_timeout_seconds"]),
        )
        receipt = {
            "schemaVersion": 1,
            "status": "completed",
            "createdUtc": stamp,
            "snapshotId": snapshot_id,
            "repository": str(REC["semantic_repository"]),
            "tag": str(REC["semantic_tag"]),
            "manifestSha256": sha256_file(manifest_path),
            "gitRepositories": len(git_rows),
            "gitBundleBytes": sum(int(row["bundleBytes"]) for row in git_rows),
            "sqliteBackupBytes": sum(int(row["backupBytes"]) for row in sqlite_rows),
            "directPaths": list(REC["semantic_direct_paths"]),
            "directWitnessesVerified": len(direct_readbacks),
            "authority": manifest["authority"],
        }
        write_receipt(Path(REC["semantic_receipt"]), receipt)
        write_attempt({**receipt, "effectAttempted": True})
        return receipt


def apply() -> dict[str, object]:
    with OperationLock("apply"):
        return apply_locked()


def snapshot_metadata(env: dict[str, str], snapshot_id: str) -> dict[str, object]:
    raw = checked(restic_command("cat", "snapshot", snapshot_id), env=env, timeout=60)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid snapshot metadata for {snapshot_id}")
    return value


def restore_test_locked(snapshot_id: str | None = None) -> dict[str, object]:
    env = restic_env()
    ensure_repository(env)
    if snapshot_id is None:
        snapshot = latest_snapshot(env)
        if snapshot is None:
            raise RuntimeError("no semantic recovery snapshot exists")
        snapshot_id = str(snapshot["id"])
    metadata = snapshot_metadata(env, snapshot_id)
    paths = [str(path) for path in metadata.get("paths", [])]
    semantic_roots = [path for path in paths if path.rstrip("/").endswith("/semantic-recovery")]
    if len(semantic_roots) != 1:
        raise RuntimeError(f"expected one semantic recovery root in snapshot metadata, found {semantic_roots}")
    semantic_prefix = semantic_roots[0].rstrip("/")
    normalized_roots = {path.rstrip("/") for path in paths}
    missing_roots = [raw for raw in REC["semantic_direct_paths"] if str(Path(raw)).rstrip("/") not in normalized_roots]
    if missing_roots:
        raise RuntimeError(f"semantic snapshot metadata omitted direct roots: {missing_roots}")
    with tempfile.TemporaryDirectory(prefix="ordivon-semantic-restore-", dir=semantic_staging_parent()) as temp:
        target = Path(temp)
        checked(
            restic_command("restore", snapshot_id, "--target", str(target), "--include", semantic_prefix + "/**"),
            env=env,
            timeout=int(REC["semantic_restore_timeout_seconds"]),
        )
        manifests = list(target.rglob("semantic-recovery/manifest.json"))
        if len(manifests) != 1:
            raise RuntimeError(f"expected one restored semantic manifest, found {len(manifests)}")
        manifest = json.loads(manifests[0].read_text())
        direct_witnesses = manifest.get("directWitnesses") if isinstance(manifest, dict) else None
        if not isinstance(direct_witnesses, list):
            raise RuntimeError("restored semantic manifest has no direct-path readback witnesses")
        expected_direct_roots = {str(Path(raw)) for raw in REC["semantic_direct_paths"]}
        witness_roots = {
            str(Path(str(row.get("root"))))
            for row in direct_witnesses
            if isinstance(row, dict) and row.get("root")
        }
        if witness_roots != expected_direct_roots or len(direct_witnesses) != len(expected_direct_roots):
            raise RuntimeError(
                "restored semantic manifest direct-path witnesses do not match current recovery roots: "
                f"expected={sorted(expected_direct_roots)} observed={sorted(witness_roots)}"
            )
        receipt_path = Path(REC["semantic_receipt"])
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text())
            if receipt.get("snapshotId") == snapshot_id and receipt.get("manifestSha256") != sha256_file(manifests[0]):
                raise RuntimeError("restored semantic manifest does not match latest receipt")
        base = manifests[0].parent
        git_verified = 0
        verify_root = target / "git-verify"
        verify_root.mkdir()
        for index, row in enumerate(manifest["git"]):
            bundle = base / "git" / row["bundle"]
            if sha256_file(bundle) != row["bundleSha256"]:
                raise RuntimeError(f"git bundle digest mismatch: {bundle}")
            verify_repo = verify_root / f"repo-{index}.git"
            checked([GIT, "init", "--bare", str(verify_repo)], timeout=30)
            checked([GIT, "--git-dir", str(verify_repo), "bundle", "verify", str(bundle)], timeout=60)
            git_verified += 1
        sqlite_verified = 0
        for row in manifest["sqlite"]:
            backup = base / "sqlite" / row["backup"]
            if sha256_file(backup) != row["sha256"]:
                raise RuntimeError(f"SQLite backup digest mismatch: {backup}")
            with sqlite3.connect(backup, timeout=20) as db:
                integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError(f"restored SQLite integrity failed: {backup}: {integrity}")
            sqlite_verified += 1
        direct_readbacks = [verify_snapshot_witness(env, snapshot_id, row) for row in direct_witnesses]
        return {
            "schemaVersion": 1,
            "status": "pass",
            "snapshotId": snapshot_id,
            "gitVerified": git_verified,
            "sqliteVerified": sqlite_verified,
            "directRootsDeclared": len(expected_direct_roots),
            "directWitnessesVerified": len(direct_readbacks),
            "snapshotRootsVerified": len(paths),
        }


def restore_test(snapshot_id: str | None = None) -> dict[str, object]:
    with OperationLock("restore-test"):
        return restore_test_locked(snapshot_id)


def repository_check_locked() -> dict[str, object]:
    env = restic_env()
    ensure_repository(env)
    output = checked(restic_command("check"), env=env, timeout=int(REC["semantic_check_timeout_seconds"]))
    return {"schemaVersion": 1, "status": "pass", "output": output.strip()}


def repository_check() -> dict[str, object]:
    with OperationLock("check"):
        return repository_check_locked()


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore-test", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--snapshot-id")
    args = parser.parse_args()
    try:
        if args.apply:
            result = apply()
        elif args.restore_test:
            result = restore_test(args.snapshot_id)
        elif args.check:
            result = repository_check()
        else:
            result = build_plan()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except RecoveryOperationBusy as error:
        deferred = {
            "schemaVersion": 1,
            "status": "deferred",
            "operation": error.operation,
            "effectAttempted": False,
            "reason": "semantic-recovery-operation-busy",
            "holder": error.holder,
        }
        if args.apply:
            try:
                write_attempt(deferred)
            except Exception:
                pass
        print(json.dumps(deferred, indent=2, sort_keys=True))
        return 0
    except Exception as error:
        failure = {"schemaVersion": 1, "status": "failed", "effectAttempted": bool(args.apply), "error": str(error)}
        if args.apply:
            try:
                write_attempt(failure)
            except Exception:
                pass
        print(json.dumps(failure, indent=2), file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
