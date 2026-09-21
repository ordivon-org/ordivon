#!/usr/bin/env python3
"""Immutable source release + quiescent production activation for Agent Automation."""

from __future__ import annotations
import argparse
import fcntl
import hashlib
import io
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import tarfile
import tempfile
import re
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

SOURCE_REPO = Path("/root/projects/ordivon-harness")
RELEASE_ROOT = Path("/opt/ordivon/agent-automation/releases")
CURRENT = Path("/opt/ordivon/agent-automation/current")
TEMPORAL = Path("/opt/ordivon/external/temporal-cli/1.8.3/temporal")
TEMPORAL_ADDRESS = "127.0.0.1:17233"
MCP_PY = Path("/root/.local/share/ordivon-workstation/agent-automation-mcp-v1/.venv/bin/python")
WORKER_PY = Path(
    "/root/.local/share/ordivon-workstation/temporal-agent-automation/.venv/bin/python"
)
BROWSER_SECURITY_PY = Path(
    "/root/.local/share/ordivon-workstation/conversation-relay-playwright-r4/.venv/bin/python"
)
SECURITY_ROOT = Path(os.environ.get("ORDIVON_SECURITY_ROOT", "/root/projects/ordivon/platform/security")).resolve()
MCP_UNIT = "ordivon-agent-automation-mcp.service"
WORKER_UNIT = "ordivon-agent-temporal-worker.service"
SYSTEMD = Path("/etc/systemd/system")
CONFIG = Path("/etc/ordivon/agent-automation-browserless.json")
OPERATOR_CLI = Path("/root/tools/bin/agent-automation")
MARKER = ".ordivon-agent-automation-release.json"
ADMISSION_ROOT = Path("/root/.local/state/ordivon-workstation/agent-automation/state")
ADMISSION_LOCK = ADMISSION_ROOT / "release-admission.lock"
ADMISSION_CLOSED = ADMISSION_ROOT / "release-admission.closed.json"
RELEASE_PATHS = (
    "config/agent-automation.toml",
    "config/agent-automation-mcp-requirements.txt",
    "config/agent-automation-temporal-requirements.txt",
    "containers/ordivon-browserless@.container",
    "schemas/agent-automation/campaign-spec-v2.schema.json",
    "scripts/agent_automation_browserless.py",
    "scripts/agent_automation_browserless_effects.py",
    "scripts/agent_automation_mcp.py",
    "scripts/agent_automation_mcp_deploy.py",
    "scripts/agent_automation_registry.py",
    "scripts/agent_automation_release.py",
    "scripts/browser_use_browserless.py",
    "scripts/browser_security_witness_source.py",
    "scripts/browser_security_pool_runner.py",
    "scripts/browser_security_browserless_canary.py",
    "scripts/browserless_image_promotion.py",
    "scripts/browserless_display_auth.py",
    "scripts/browserless_idle_reaper.py",
    "scripts/browserless_human_handoff.py",
    "scripts/browserless_human_interaction.py",
    "scripts/browserless_materialization_target.py",
    "scripts/browserless_podman_deploy.py",
    "scripts/browserless_substrate.py",
    "scripts/playwright_browserless_binding_reconcile.py",
    "scripts/playwright_browserless_chatgpt_submit.py",
    "scripts/playwright_browserless_conversation_output.py",
    "scripts/playwright_browserless_human_resume.py",
    "scripts/playwright_browserless_provider_preflight.py",
    "scripts/playwright_browserless_turn_once.py",
    "scripts/provider_boundary_diagnosis.py",
    "scripts/temporal_agent_automation.py",
    "scripts/temporal_agent_automation_deploy.py",
    "scripts/temporal_agent_automation_launch.py",
    "scripts/temporal_agent_automation_worker.py",
    "scripts/campaign_materialization.py",
    "scripts/chatgpt_provider_gate.py",
    "scripts/chatgpt_provider_resource.py",
    "scripts/cft_human_session.py",
    "scripts/cft_human_materialization.py",
    "scripts/cft_human_session_auth.py",
    "scripts/cft_human_session_deploy.py",
    "config/browserless-playwright-requirements.txt",
    "scripts/conversation_relay_carrier.py",
    "scripts/sqlite_conversation_materializer.py",
    "scripts/standard_identifiers.py",
    "systemd/ordivon-agent-automation-mcp.service",
    "systemd/ordivon-agent-temporal-worker.service",
    "systemd/ordivon-cft-human-session@.target",
    "systemd/ordivon-cft-human-display@.service",
    "systemd/ordivon-cft-human-browser@.service",
    "systemd/ordivon-cft-human-vnc@.service",
    "systemd/ordivon-cft-human-web@.service",
    "systemd/ordivon-browser-agent.target",
    "systemd/ordivon-browserless-display@.service",
    "systemd/ordivon-browserless-idle-reaper.service",
    "systemd/ordivon-browserless-idle-reaper.timer",
    "systemd/ordivon-browserless-human-vnc@.service",
    "systemd/ordivon-browserless-human-web@.service",
    "systemd/ordivon-browserless-operator-proxy@.service",
)
GATE_SCHEMA_VERSION = 2
WORKER_RUNTIME_VERSIONS = {
    "temporalio": "1.32.0",
    "rfc8785": "0.1.4",
}
PLAYWRIGHT_RUNTIME_VERSIONS = {
    "playwright": "1.63.0",
    "rfc8785": "0.1.4",
}


class ReleaseError(RuntimeError):
    pass


def run(
    argv: list[str], *, check: bool = True, timeout: float = 30, env: dict[str, str] | None = None
):
    return subprocess.run(
        argv, capture_output=True, text=True, check=check, timeout=timeout, env=env
    )


def _materialization_ledger_paths(state_root: Path = ADMISSION_ROOT) -> tuple[Path, Path]:
    root = Path(state_root)
    if not root.is_absolute():
        raise ReleaseError("Agent Automation state root must be absolute for ledger migration")
    return root / "birth-ledger.sqlite", root / "materialization-ledger.sqlite"


def _materialization_ledger_snapshot(path: Path) -> dict:
    if not path.is_file():
        raise ReleaseError(f"materialization ledger is missing: {path}")
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        integrity = db.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise ReleaseError(f"materialization ledger integrity check failed: {path}")
        columns = [
            row[1]
            for row in db.execute("PRAGMA table_info(requests)")
        ]
        expected = [
            "request_id",
            "request_digest",
            "request_json",
            "standing",
            "provider_coordinate",
            "evidence_digest",
            "detail",
            "effect_generation",
            "created_at_ms",
            "updated_at_ms",
        ]
        if columns != expected:
            raise ReleaseError(
                f"materialization ledger requests schema mismatch: {path}; observed={columns}"
            )
        rows = [
            list(row)
            for row in db.execute(
                """
                SELECT request_id,request_digest,request_json,standing,provider_coordinate,
                       evidence_digest,detail,effect_generation,created_at_ms,updated_at_ms
                FROM requests ORDER BY request_id
                """
            )
        ]
    finally:
        db.close()
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {
        "requestCount": len(rows),
        "semanticDigest": "sha256:" + hashlib.sha256(payload).hexdigest(),
    }


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def prepare_materialization_ledger_migration(state_root: Path = ADMISSION_ROOT) -> dict:
    legacy, current = _materialization_ledger_paths(state_root)
    legacy_exists = legacy.is_file()
    current_exists = current.is_file()

    if not legacy_exists and not current_exists:
        return {
            "schemaVersion": 1,
            "standing": "NOT_REQUIRED",
            "legacyPath": str(legacy),
            "currentPath": str(current),
            "createdCurrent": False,
            "requestCount": 0,
            "semanticDigest": None,
        }

    if current_exists and not legacy_exists:
        snapshot = _materialization_ledger_snapshot(current)
        return {
            "schemaVersion": 1,
            "standing": "ALREADY_CURRENT",
            "legacyPath": str(legacy),
            "currentPath": str(current),
            "createdCurrent": False,
            **snapshot,
        }

    assert legacy_exists
    legacy_snapshot = _materialization_ledger_snapshot(legacy)

    if current_exists:
        current_snapshot = _materialization_ledger_snapshot(current)
        if current_snapshot != legacy_snapshot:
            raise ReleaseError(
                "legacy/current materialization ledgers diverge; refusing to choose an authority"
            )
        return {
            "schemaVersion": 1,
            "standing": "PREPARED_EXISTING",
            "legacyPath": str(legacy),
            "currentPath": str(current),
            "createdCurrent": False,
            **legacy_snapshot,
        }

    current.parent.mkdir(parents=True, exist_ok=True)
    staging = current.with_name(current.name + ".next")
    staging.unlink(missing_ok=True)
    source = sqlite3.connect(f"file:{legacy}?mode=ro", uri=True)
    destination = sqlite3.connect(staging)
    try:
        source.backup(destination)
        destination.execute("PRAGMA journal_mode=DELETE")
        destination.commit()
    finally:
        destination.close()
        source.close()
    os.chmod(staging, 0o600)
    if _materialization_ledger_snapshot(staging) != legacy_snapshot:
        staging.unlink(missing_ok=True)
        raise ReleaseError("materialization ledger copy verification failed")
    os.replace(staging, current)
    _fsync_directory(current.parent)
    return {
        "schemaVersion": 1,
        "standing": "PREPARED",
        "legacyPath": str(legacy),
        "currentPath": str(current),
        "createdCurrent": True,
        **legacy_snapshot,
    }


def rollback_materialization_ledger_migration(receipt: dict) -> None:
    if receipt.get("createdCurrent") is not True:
        return
    legacy = Path(receipt["legacyPath"])
    current = Path(receipt["currentPath"])
    if not legacy.is_file():
        raise ReleaseError("cannot roll back materialization ledger migration: legacy authority missing")
    for path in (
        current,
        current.with_name(current.name + "-wal"),
        current.with_name(current.name + "-shm"),
    ):
        path.unlink(missing_ok=True)
    _fsync_directory(current.parent)


def finalize_materialization_ledger_migration(receipt: dict) -> dict:
    legacy = Path(receipt["legacyPath"])
    current = Path(receipt["currentPath"])
    if receipt["standing"] == "NOT_REQUIRED":
        return {**receipt, "standing": "FINALIZED"}
    current_snapshot = _materialization_ledger_snapshot(current)
    expected = {
        "requestCount": receipt["requestCount"],
        "semanticDigest": receipt["semanticDigest"],
    }
    if current_snapshot != expected:
        raise ReleaseError("current materialization ledger changed before release cutover finalized")
    if legacy.is_file():
        legacy_snapshot = _materialization_ledger_snapshot(legacy)
        if legacy_snapshot != expected:
            raise ReleaseError("legacy materialization ledger changed during closed-admission cutover")
        for path in (
            legacy,
            legacy.with_name(legacy.name + "-wal"),
            legacy.with_name(legacy.name + "-shm"),
        ):
            path.unlink(missing_ok=True)
        _fsync_directory(legacy.parent)
    return {**receipt, "standing": "FINALIZED"}


def _materialization_state_paths(state_root: Path = ADMISSION_ROOT) -> tuple[Path, Path]:
    root = Path(state_root)
    if not root.is_absolute():
        raise ReleaseError("Agent Automation state root must be absolute for state migration")
    return root / "occurrences", root / "materializations"


def _state_tree_snapshot(path: Path) -> dict:
    root = Path(path)
    if not root.is_dir() or root.is_symlink():
        raise ReleaseError(f"state tree must be one real directory: {root}")
    rows: list[list[object]] = []
    file_count = 0
    byte_count = 0
    for entry in sorted(root.rglob("*"), key=lambda value: value.as_posix()):
        relative = entry.relative_to(root).as_posix()
        if entry.is_symlink():
            raise ReleaseError(f"state tree contains symlink: {entry}")
        if entry.is_dir():
            rows.append(["dir", relative])
            continue
        if not entry.is_file():
            raise ReleaseError(f"state tree contains unsupported entry: {entry}")
        raw = entry.read_bytes()
        file_count += 1
        byte_count += len(raw)
        rows.append(["file", relative, len(raw), "sha256:" + hashlib.sha256(raw).hexdigest()])
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {
        "fileCount": file_count,
        "byteCount": byte_count,
        "treeDigest": "sha256:" + hashlib.sha256(payload).hexdigest(),
    }


def prepare_materialization_state_migration(state_root: Path = ADMISSION_ROOT) -> dict:
    legacy, current = _materialization_state_paths(state_root)
    legacy_exists = legacy.is_dir() and not legacy.is_symlink()
    current_exists = current.is_dir() and not current.is_symlink()
    if legacy.exists() and not legacy_exists:
        raise ReleaseError("legacy occurrence state path is not one real directory")
    if current.exists() and not current_exists:
        raise ReleaseError("materialization state path is not one real directory")
    if legacy_exists and current_exists:
        raise ReleaseError("legacy/current materialization state roots both exist")
    if not legacy_exists and not current_exists:
        return {
            "schemaVersion": 1,
            "standing": "NOT_REQUIRED",
            "legacyPath": str(legacy),
            "currentPath": str(current),
            "moved": False,
            "fileCount": 0,
            "byteCount": 0,
            "treeDigest": None,
        }
    if current_exists:
        snapshot = _state_tree_snapshot(current)
        return {
            "schemaVersion": 1,
            "standing": "ALREADY_CURRENT",
            "legacyPath": str(legacy),
            "currentPath": str(current),
            "moved": False,
            **snapshot,
        }

    snapshot = _state_tree_snapshot(legacy)
    os.replace(legacy, current)
    _fsync_directory(current.parent)
    if _state_tree_snapshot(current) != snapshot:
        os.replace(current, legacy)
        _fsync_directory(legacy.parent)
        raise ReleaseError("materialization state directory verification failed after rename")
    return {
        "schemaVersion": 1,
        "standing": "PREPARED",
        "legacyPath": str(legacy),
        "currentPath": str(current),
        "moved": True,
        **snapshot,
    }


def rollback_materialization_state_migration(receipt: dict) -> None:
    if receipt.get("moved") is not True:
        return
    legacy = Path(receipt["legacyPath"])
    current = Path(receipt["currentPath"])
    if legacy.exists() or not current.is_dir() or current.is_symlink():
        raise ReleaseError("cannot roll back materialization state migration safely")
    expected = {
        "fileCount": receipt["fileCount"],
        "byteCount": receipt["byteCount"],
        "treeDigest": receipt["treeDigest"],
    }
    if _state_tree_snapshot(current) != expected:
        raise ReleaseError("materialization state changed before rollback")
    os.replace(current, legacy)
    _fsync_directory(legacy.parent)
    if _state_tree_snapshot(legacy) != expected:
        raise ReleaseError("legacy state verification failed after rollback")


def finalize_materialization_state_migration(receipt: dict) -> dict:
    if receipt["standing"] == "NOT_REQUIRED":
        return {**receipt, "standing": "FINALIZED"}
    legacy = Path(receipt["legacyPath"])
    current = Path(receipt["currentPath"])
    if legacy.exists() or not current.is_dir() or current.is_symlink():
        raise ReleaseError("materialization state authority is not uniquely current")
    expected = {
        "fileCount": receipt["fileCount"],
        "byteCount": receipt["byteCount"],
        "treeDigest": receipt["treeDigest"],
    }
    if _state_tree_snapshot(current) != expected:
        raise ReleaseError("materialization state changed during closed-admission cutover")
    return {**receipt, "standing": "FINALIZED"}


def exact_commit(repo: Path, revision: str) -> str:
    p = run(["/usr/bin/git", "-C", str(repo), "rev-parse", "--verify", f"{revision}^{{commit}}"])
    v = p.stdout.strip()
    if len(v) != 40 or any(c not in "0123456789abcdef" for c in v):
        raise ReleaseError("revision is not one exact Git commit")
    return v


def archive_bytes(repo: Path, commit: str) -> bytes:
    p = subprocess.run(
        ["/usr/bin/git", "-C", str(repo), "archive", "--format=tar", commit, "--", *RELEASE_PATHS],
        capture_output=True,
        check=True,
        timeout=60,
    )
    return p.stdout


def sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def marker(path: Path) -> dict | None:
    try:
        v = json.loads((path / MARKER).read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return v if isinstance(v, dict) else None


def materialize(repo: Path, commit: str, release_root: Path = RELEASE_ROOT) -> dict:
    raw = archive_bytes(repo, commit)
    ad = sha(raw)
    target = release_root / commit
    expected = {"schemaVersion": 1, "commit": commit, "archiveDigest": ad}
    if target.exists():
        if marker(target) != expected:
            raise ReleaseError(f"existing release identity differs: {target}")
        return {
            "path": str(target),
            "commit": commit,
            "archiveDigest": ad,
            "disposition": "existing",
        }
    release_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{commit[:12]}.", dir=release_root))
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tf:
            members = tf.getmembers()
            for m in members:
                p = PurePosixPath(m.name)
                if p.is_absolute() or ".." in p.parts or m.ischr() or m.isblk() or m.isfifo():
                    raise ReleaseError(f"unsafe archive member: {m.name}")
            tf.extractall(staging, members=members, filter="data")
        (staging / MARKER).write_text(json.dumps(expected, sort_keys=True) + "\n")
        for p in sorted(staging.rglob("*"), reverse=True):
            if p.is_symlink():
                continue
            mode = stat.S_IMODE(p.stat().st_mode)
            p.chmod(((mode & ~0o222) | 0o500) if p.is_dir() else (mode & ~0o222))
        staging.chmod(0o555)
        os.replace(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return {
        "path": str(target),
        "commit": commit,
        "archiveDigest": ad,
        "disposition": "materialized",
    }


def current_temporal_task_queue() -> str:
    try:
        cfg = json.loads(CONFIG.read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise ReleaseError("Agent Automation runtime config is unavailable for drain scope") from e
    queue = cfg.get("temporalTaskQueue") if isinstance(cfg, dict) else None
    if not isinstance(queue, str) or re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", queue) is None:
        raise ReleaseError("Agent Automation temporalTaskQueue is unavailable or unsafe")
    return queue


def running_workflows() -> list[dict]:
    queue = current_temporal_task_queue()
    query = f'ExecutionStatus="Running" AND TaskQueue="{queue}"'
    p = run(
        [
            str(TEMPORAL),
            "workflow",
            "list",
            "--address",
            TEMPORAL_ADDRESS,
            "--namespace",
            "default",
            "--query",
            query,
            "--limit",
            "1000",
            "--output",
            "json",
        ],
        timeout=20,
    )
    try:
        v = json.loads(p.stdout)
    except json.JSONDecodeError as e:
        raise ReleaseError("Temporal Running observation is not JSON for production") from e
    if not isinstance(v, list):
        raise ReleaseError("Temporal Running observation is not a list for production")
    return [{**x, "temporalAddress": TEMPORAL_ADDRESS} for x in v if isinstance(x, dict)]


def active(unit: str) -> bool:
    return (
        run(
            ["/usr/bin/systemctl", "is-active", "--quiet", unit], check=False, timeout=10
        ).returncode
        == 0
    )


def current_release() -> dict | None:
    try:
        root = CURRENT.resolve(strict=True)
    except OSError:
        return None
    m = marker(root)
    return {**m, "path": str(root)} if m else None


def operator_carrier_available() -> bool:
    """Observe only the Workstation-owned stable carrier boundary.

    Harness must not duplicate or byte-compare Workstation carrier source. The carrier owns its
    own materialization/currentness; Harness requires only the stable executable handoff before
    cutting the immutable release that carrier delegates into.
    """
    try:
        return OPERATOR_CLI.is_file() and os.access(OPERATOR_CLI, os.X_OK)
    except OSError:
        return False


def require_operator_carrier_available() -> None:
    if not operator_carrier_available():
        raise ReleaseError(
            "Workstation-owned stable Agent Automation carrier is unavailable or not executable"
        )


def require_worker_runtime_importable(release: Path) -> None:
    scripts = release / "scripts"
    code = (
        "import sys,json,importlib.metadata as m;"
        "sys.path.insert(0,sys.argv[1]);"
        "import temporal_agent_automation;"
        "names=['temporalio','rfc8785'];"
        "print(json.dumps({n:m.version(n) for n in names},sort_keys=True))"
    )
    p = run([str(WORKER_PY), "-c", code, str(scripts)], check=False, timeout=30)
    if p.returncode != 0:
        detail = (p.stderr or p.stdout or "").strip().replace("\n", " ")[-1200:]
        raise ReleaseError(
            f"candidate is not importable in the exact Temporal worker runtime: {detail or f'rc={p.returncode}'}"
        )
    try:
        versions = json.loads(p.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as error:
        raise ReleaseError("Temporal worker runtime dependency versions are not observable") from error
    if versions != WORKER_RUNTIME_VERSIONS:
        raise ReleaseError(
            f"worker runtime dependency versions differ from release contract: {versions}"
        )


def require_mcp_runtime_importable(release: Path) -> None:
    scripts = release / "scripts"
    code = "import sys; sys.path.insert(0, sys.argv[1]); import agent_automation_registry, agent_automation_browserless"
    p = run([str(MCP_PY), "-c", code, str(scripts)], check=False, timeout=30)
    if p.returncode != 0:
        detail = (p.stderr or p.stdout or "").strip().replace("\n", " ")[-1200:]
        raise ReleaseError(
            f"candidate is not importable in the exact MCP control runtime: {detail or f'rc={p.returncode}'}"
        )


def require_playwright_runtime_importable(release: Path) -> None:
    scripts = release / "scripts"
    code = (
        "import sys,json,importlib.metadata as m;"
        "sys.path.insert(0,sys.argv[1]);"
        "import playwright_browserless_turn_once,playwright_browserless_conversation_output;"
        "names=['playwright','rfc8785'];"
        "print(json.dumps({n:m.version(n) for n in names},sort_keys=True))"
    )
    p = run([str(BROWSER_SECURITY_PY), "-c", code, str(scripts)], check=False, timeout=30)
    if p.returncode != 0:
        detail = (p.stderr or p.stdout or "").strip().replace("\n", " ")[-1200:]
        raise ReleaseError(
            f"candidate is not importable in the exact Playwright runtime: {detail or f'rc={p.returncode}'}"
        )
    try:
        versions = json.loads(p.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as error:
        raise ReleaseError("Playwright runtime dependency versions are not observable") from error
    if versions != PLAYWRIGHT_RUNTIME_VERSIONS:
        raise ReleaseError(
            f"Playwright runtime dependency versions differ from release contract: {versions}"
        )


def candidate_runtime_import_status(release: Path) -> dict:
    try:
        require_mcp_runtime_importable(release)
        require_worker_runtime_importable(release)
        require_playwright_runtime_importable(release)
    except ReleaseError as error:
        return {"ready": False, "detail": str(error)}
    return {"ready": True}


def plan(repo: Path, revision: str) -> dict:
    commit = exact_commit(repo, revision)
    release = RELEASE_ROOT / commit
    materialized = marker(release) is not None
    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-automation-release-plan",
        "candidateCommit": commit,
        "candidateMaterialized": materialized,
        "candidateRuntimeImports": candidate_runtime_import_status(release)
        if materialized
        else {"ready": False, "detail": "candidate release is not materialized"},
        "currentRelease": current_release(),
        "runningWorkflowCount": len(running_workflows()),
        "mcpAdmissionActive": active(MCP_UNIT),
        "workerActive": active(WORKER_UNIT),
        "operatorCarrierAvailable": operator_carrier_available(),
        "operatorCli": str(OPERATOR_CLI),
        "developmentRoot": str(repo.resolve()),
        "productionRoot": str(CURRENT),
    }


def _browser_security_qualification_path(commit: str) -> Path:
    return ADMISSION_ROOT / "browser-security-qualifications" / f"{commit}.json"


def _persist_browser_security_qualification(commit: str, value: dict) -> None:
    write_atomic(
        _browser_security_qualification_path(commit),
        json.dumps(value, sort_keys=True).encode() + b"\n",
        0o600,
    )


def require_browser_security_release_qualification(release: Path, commit: str) -> dict:
    runner = release / "scripts" / "browser_security_pool_runner.py"
    witness = release / "scripts" / "browser_security_witness_source.py"
    if not runner.is_file() or not witness.is_file():
        value = {
            "schemaVersion": 1,
            "kind": "ordivon.agent-automation-browser-security-qualification",
            "standing": "HOLD",
            "candidateCommit": commit,
            "detail": "candidate lacks Browser Security qualification scripts",
        }
        _persist_browser_security_qualification(commit, value)
        raise ReleaseError(value["detail"])

    # Readiness-probe semantics: an explicit OBSERVATION_INVALID means the observer could not
    # establish a valid sample. Re-sample that acquisition failure only. Real drift is evidence,
    # not a transient probe failure, and therefore never gets retried away.
    failure_threshold = 3
    probe_standings: list[str] = []
    for attempt in range(1, failure_threshold + 1):
        run_id = f"release-{commit[:12]}-probe-{attempt}"
        proc = run(
            [
                str(BROWSER_SECURITY_PY),
                str(runner),
                "--run-id",
                run_id,
                "--security-root",
                str(SECURITY_ROOT),
            ],
            check=False,
            timeout=240,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or f"rc={proc.returncode}").strip().replace("\n", " ")[-1600:]
            value = {
                "schemaVersion": 1,
                "kind": "ordivon.agent-automation-browser-security-qualification",
                "standing": "HOLD",
                "candidateCommit": commit,
                "probeAttempts": attempt,
                "probeStandings": probe_standings,
                "detail": f"Browser Security pool runner failed: {detail}",
            }
            _persist_browser_security_qualification(commit, value)
            raise ReleaseError(value["detail"])
        try:
            pool = json.loads(proc.stdout)
        except json.JSONDecodeError as error:
            value = {
                "schemaVersion": 1,
                "kind": "ordivon.agent-automation-browser-security-qualification",
                "standing": "HOLD",
                "candidateCommit": commit,
                "probeAttempts": attempt,
                "probeStandings": probe_standings,
                "detail": "Browser Security pool runner returned non-JSON",
            }
            _persist_browser_security_qualification(commit, value)
            raise ReleaseError(value["detail"]) from error

        classification = pool.get("classification") if isinstance(pool, dict) else None
        valid = (
            isinstance(pool, dict)
            and pool.get("kind") == "ordivon.browser-security-pool-run"
            and pool.get("harnessRevision") == commit
            and isinstance(pool.get("securityRevision"), str)
            and re.fullmatch(r"[0-9a-f]{40}", pool["securityRevision"]) is not None
            and isinstance(pool.get("poolIndexSha256"), str)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", pool["poolIndexSha256"]) is not None
            and pool.get("providerChallengeVisited") is False
            and pool.get("providerSendAttempted") is False
            and isinstance(classification, dict)
            and classification.get("rootCauseEstablished") is False
            and isinstance(classification.get("standing"), str)
        )
        if not valid:
            value = {
                "schemaVersion": 1,
                "kind": "ordivon.agent-automation-browser-security-qualification",
                "standing": "HOLD",
                "candidateCommit": commit,
                "probeAttempts": attempt,
                "probeStandings": probe_standings,
                "detail": "Browser Security pool receipt failed release-binding validation",
            }
            _persist_browser_security_qualification(commit, value)
            raise ReleaseError(value["detail"])

        drift = classification["standing"]
        probe_standings.append(drift)
        value = {
            "schemaVersion": 1,
            "kind": "ordivon.agent-automation-browser-security-qualification",
            "standing": "PASS" if drift == "NO_OBSERVED_DRIFT" else "HOLD",
            "candidateCommit": commit,
            "securityRevision": pool["securityRevision"],
            "poolId": pool.get("poolId"),
            "poolIndexSha256": pool["poolIndexSha256"],
            "classificationStanding": drift,
            "carrierCount": len(pool.get("carrierEvidence") or []),
            "providerChallengeVisited": False,
            "providerSendAttempted": False,
            "rootCauseEstablished": False,
            "probeAttempts": attempt,
            "probeStandings": list(probe_standings),
        }
        _persist_browser_security_qualification(commit, value)
        if drift == "NO_OBSERVED_DRIFT":
            return value
        if drift != "OBSERVATION_INVALID":
            raise ReleaseError(f"Browser Security qualification HOLD: {drift}")

    raise ReleaseError("Browser Security qualification HOLD: OBSERVATION_INVALID")


def atomic_link(target: Path, link: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    tmp = link.with_name(link.name + ".next")
    tmp.unlink(missing_ok=True)
    tmp.symlink_to(target)
    os.replace(tmp, link)


def write_atomic(path: Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".next")
    tmp.write_bytes(raw)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def restore_optional_file(path: Path, raw: bytes | None, mode: int) -> None:
    # A release rollback restores the exact pre-attempt file state, including absence.
    # Remove any abandoned atomic-write temporary before restoring/clearing the target.
    path.with_name(path.name + ".next").unlink(missing_ok=True)
    if raw is None:
        path.unlink(missing_ok=True)
    else:
        write_atomic(path, raw, mode)


def source_repo_identity(repo: Path = SOURCE_REPO) -> str:
    try:
        return str(repo.resolve(strict=True))
    except OSError as e:
        raise ReleaseError(f"Agent Automation source repository unavailable: {repo}") from e


def _close_admission(commit: str, repo: Path = SOURCE_REPO) -> None:
    ADMISSION_ROOT.mkdir(parents=True, exist_ok=True)
    write_atomic(
        ADMISSION_CLOSED,
        json.dumps(
            {
                "schemaVersion": GATE_SCHEMA_VERSION,
                "standing": "HOLD_CLOSED",
                "candidateCommit": commit,
                "sourceRepo": source_repo_identity(repo),
            },
            sort_keys=True,
        ).encode()
        + b"\n",
        0o600,
    )


def _existing_admission_gate() -> dict | None:
    if not ADMISSION_CLOSED.exists():
        return None
    try:
        row = json.loads(ADMISSION_CLOSED.read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise ReleaseError(
            "existing Agent Automation admission gate is unreadable or malformed; preserve HOLD and reconcile explicitly"
        ) from e
    if (
        not isinstance(row, dict)
        or row.get("standing") != "HOLD_CLOSED"
        or not isinstance(row.get("candidateCommit"), str)
    ):
        raise ReleaseError(
            "existing Agent Automation admission gate has an invalid contract; preserve HOLD and reconcile explicitly"
        )
    if row.get("schemaVersion") == 1 and set(row) == {
        "schemaVersion",
        "standing",
        "candidateCommit",
    }:
        return row
    if (
        row.get("schemaVersion") == GATE_SCHEMA_VERSION
        and set(row) == {"schemaVersion", "standing", "candidateCommit", "sourceRepo"}
        and isinstance(row.get("sourceRepo"), str)
        and row["sourceRepo"].startswith("/")
    ):
        return row
    raise ReleaseError(
        "existing Agent Automation admission gate has an invalid contract; preserve HOLD and reconcile explicitly"
    )


def _restore_admission_gate(was_closed: bool) -> None:
    if not was_closed:
        ADMISSION_CLOSED.unlink(missing_ok=True)
        ADMISSION_CLOSED.with_name(ADMISSION_CLOSED.name + ".next").unlink(missing_ok=True)


def candidate_fast_forwards_closed_gate(
    old_commit: str, new_commit: str, repo: Path = SOURCE_REPO
) -> bool:
    if old_commit == new_commit:
        return True
    p = run(
        ["/usr/bin/git", "-C", str(repo), "merge-base", "--is-ancestor", old_commit, new_commit],
        check=False,
        timeout=20,
    )
    return p.returncode == 0


@contextmanager
def release_admission_fence(commit: str):
    ADMISSION_ROOT.mkdir(parents=True, exist_ok=True)
    with ADMISSION_LOCK.open("a+") as handle:
        os.chmod(ADMISSION_LOCK, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        existing = _existing_admission_gate()
        was_closed = existing is not None
        if existing is not None and existing["candidateCommit"] != commit:
            old_commit = existing["candidateCommit"]
            if existing.get("schemaVersion") != GATE_SCHEMA_VERSION:
                raise ReleaseError(
                    f"legacy closed admission gate requires explicit reconciliation before owner migration: {old_commit}"
                )
            current_source = source_repo_identity(SOURCE_REPO)
            if existing.get("sourceRepo") != current_source:
                raise ReleaseError(
                    f"closed admission gate belongs to another source repository: {existing.get('sourceRepo')}"
                )
            if not candidate_fast_forwards_closed_gate(old_commit, commit, SOURCE_REPO):
                raise ReleaseError(
                    f"existing closed admission gate belongs to non-ancestor candidate: {old_commit}"
                )
            # Repair candidates may advance a still-closed gate only within the same exact source repository.
            _close_admission(commit, SOURCE_REPO)
        if not was_closed:
            _close_admission(commit, SOURCE_REPO)
        try:
            yield was_closed
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def activate(repo: Path, revision: str) -> dict:
    if os.geteuid() != 0:
        raise ReleaseError("root authority required")
    commit = exact_commit(repo, revision)
    rel = materialize(repo, commit)
    release = Path(rel["path"])
    require_operator_carrier_available()
    require_mcp_runtime_importable(release)
    require_worker_runtime_importable(release)
    require_playwright_runtime_importable(release)
    with release_admission_fence(commit) as admission_was_closed:
        # Snapshot every rollback-relevant pre-state before the first service/file mutation. Early
        # failures (including quiescence observation or worker stop) must restore the same state.
        mcp_was = active(MCP_UNIT)
        worker_was = active(WORKER_UNIT)
        try:
            old_current = CURRENT.resolve(strict=True)
        except OSError:
            old_current = None
        old_config = CONFIG.read_bytes() if CONFIG.is_file() else None
        old_worker = (
            (SYSTEMD / WORKER_UNIT).read_bytes() if (SYSTEMD / WORKER_UNIT).is_file() else None
        )
        old_mcp = (SYSTEMD / MCP_UNIT).read_bytes() if (SYSTEMD / MCP_UNIT).is_file() else None
        switched = False
        try:
            if mcp_was:
                run(["/usr/bin/systemctl", "stop", MCP_UNIT], timeout=30)
            running = running_workflows()
            if running:
                # Keep the durable CLI gate closed after this process returns. The worker remains active so
                # already-admitted workflows can drain; a later activation re-enters the same closed gate.
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.agent-automation-release-activation",
                    "standing": "HOLD_DRAINING",
                    "candidateCommit": commit,
                    "runningWorkflowCount": len(running),
                    "mcpAdmissionClosed": True,
                    "cliAdmissionClosed": True,
                    "release": rel,
                }
            browser_security_qualification = require_browser_security_release_qualification(
                release, commit
            )
            run(["/usr/bin/systemctl", "stop", WORKER_UNIT], timeout=30)
            ledger_migration = prepare_materialization_ledger_migration()
            state_migration = prepare_materialization_state_migration()
            atomic_link(release, CURRENT)
            switched = True
            worker_source = release / "systemd" / WORKER_UNIT
            if not worker_source.is_file():
                raise ReleaseError("candidate lacks production worker unit")
            write_atomic(SYSTEMD / WORKER_UNIT, worker_source.read_bytes(), 0o644)
            run(["/usr/bin/systemctl", "daemon-reload"], timeout=20)
            run(["/usr/bin/systemctl", "start", WORKER_UNIT], timeout=30)
            env = dict(os.environ)
            env["ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT"] = str(CURRENT)
            deploy = release / "scripts" / "agent_automation_mcp_deploy.py"
            p = run(
                [
                    "/root/.local/share/ordivon-workstation/agent-automation-mcp-v1/.venv/bin/python",
                    str(deploy),
                    "--apply",
                ],
                timeout=180,
                env=env,
            )
            receipt = json.loads(p.stdout.strip().splitlines()[-1])
            if running_workflows():
                raise ReleaseError("new Workflow appeared during closed-admission activation")
            if not active(WORKER_UNIT) or not active(MCP_UNIT):
                raise ReleaseError("production worker/MCP not active after activation")
            # Browserless network lifecycle is owned independently by Network v2; release activation
            # only opens CLI admission after source, worker, MCP, and the materialization ledger
            # authority passed currentness/health.
            state_migration = finalize_materialization_state_migration(state_migration)
            ledger_migration = finalize_materialization_ledger_migration(ledger_migration)
            ADMISSION_CLOSED.unlink(missing_ok=True)
            return {
                "schemaVersion": 1,
                "kind": "ordivon.agent-automation-release-activation",
                "standing": "ACTIVE",
                "candidateCommit": commit,
                "release": rel,
                "productionRoot": str(CURRENT.resolve()),
                "runningWorkflowCount": 0,
                "mcp": receipt,
                "browserSecurityQualification": browser_security_qualification,
                "materializationLedgerMigration": ledger_migration,
                "materializationStateMigration": state_migration,
                "cliAdmissionClosed": False,
            }
        except Exception:
            run(["/usr/bin/systemctl", "stop", MCP_UNIT], check=False, timeout=20)
            run(["/usr/bin/systemctl", "stop", WORKER_UNIT], check=False, timeout=20)
            if "state_migration" in locals():
                rollback_materialization_state_migration(state_migration)
            if "ledger_migration" in locals():
                rollback_materialization_ledger_migration(ledger_migration)
            if switched:
                if old_current is None:
                    CURRENT.unlink(missing_ok=True)
                else:
                    atomic_link(old_current, CURRENT)
            restore_optional_file(CONFIG, old_config, 0o600)
            restore_optional_file(SYSTEMD / WORKER_UNIT, old_worker, 0o644)
            restore_optional_file(SYSTEMD / MCP_UNIT, old_mcp, 0o644)
            run(["/usr/bin/systemctl", "daemon-reload"], check=False, timeout=20)
            if worker_was:
                run(["/usr/bin/systemctl", "start", WORKER_UNIT], check=False, timeout=30)
            if mcp_was:
                run(["/usr/bin/systemctl", "start", MCP_UNIT], check=False, timeout=30)
            _restore_admission_gate(admission_was_closed)
            raise


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=SOURCE_REPO)
    p.add_argument("--revision", default="main")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--materialize", action="store_true")
    g.add_argument("--activate", action="store_true")
    a = p.parse_args()
    try:
        v = (
            plan(a.repo, a.revision)
            if a.plan
            else (
                materialize(a.repo, exact_commit(a.repo, a.revision))
                if a.materialize
                else activate(a.repo, a.revision)
            )
        )
    except (ReleaseError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as e:
        print(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "kind": "ordivon.agent-automation-release-error",
                    "standing": "HOLD",
                    "detail": str(e),
                },
                sort_keys=True,
            )
        )
        return 75
    print(json.dumps(v, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
