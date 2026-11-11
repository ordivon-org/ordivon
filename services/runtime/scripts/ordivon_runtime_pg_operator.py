"""Operator-only PostgreSQL Runtime release execution.

Reuse the mature Runtime deployer's immutable candidate, atomically installed
artifacts, systemd readiness, lock, receipt and rollback primitives. The
registry and dispatch fence here are PostgreSQL-native, never SQLite.

This module is NOT an ordinary MCP or workspace.exec Tool. The independently
privileged host operator runs it with its own PostgreSQL role and systemd rights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import runpy
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from mcp_probe import McpClient

_RELEASE_SCRIPT = Path(__file__).with_name("ordivon-runtime-deploy")
# This is the same import strategy used by Runtime's existing deployment
# semantics tests. Keep the one mature implementation of physical primitives.
# The original CLI already uses mcp_probe as an adjacent helper.
sys.path.insert(0, str(_RELEASE_SCRIPT.parent))
try:
    DEPLOY = runpy.run_path(str(_RELEASE_SCRIPT), run_name="ordivon_runtime_deploy_library")
finally:
    sys.path.remove(str(_RELEASE_SCRIPT.parent))

SCHEMA = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,62}$")
DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")
COMMIT = re.compile(r"^[a-f0-9]{40}$")
EFFECT = re.compile(r"^[a-f0-9]{64}$")
REQUEST_DIGEST = re.compile(r"^runtime-release-v1:sha256:[a-f0-9]{64}$")
ADMISSION_LOCK = 79245017
DISPATCH_EVENT = "RELEASE_OPERATOR_DISPATCH_ISSUED"


def canonical_json(value: Any) -> str:
    """Matches serde_json's ordered ASCII record encoding for this contract."""
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


_REQUIRED_NATIVE_RELEASE_BINARIES = frozenset({
    "ordivon-runtime-pg", "ordivon-runtime-runner",
})


def require_complete_native_release(args: argparse.Namespace) -> None:
    """One native PG release owns both executable consumers at every entry."""
    binaries = getattr(args, "binaries", None)
    if (
        not isinstance(binaries, list)
        or len(binaries) != len(_REQUIRED_NATIVE_RELEASE_BINARIES)
        or not all(isinstance(name, str) for name in binaries)
        or set(binaries) != _REQUIRED_NATIVE_RELEASE_BINARIES
    ):
        raise RuntimeError("complete native PG and Runner release binaries required")


def qualify(value: str, expression: re.Pattern[str], name: str) -> str:
    if not expression.fullmatch(value):
        raise RuntimeError(f"invalid {name}")
    return value


def pg_connection(dsn: str, schema: str) -> psycopg.Connection:
    qualify(schema, SCHEMA, "PostgreSQL schema")
    if schema.lower() in {"public", "information_schema"} or schema.startswith("pg_"):
        raise RuntimeError("unsafe PostgreSQL schema")
    conn = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
    conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
    actual = conn.execute("SELECT current_schema() AS name").fetchone()
    if actual is None or actual["name"] != schema:
        conn.close()
        raise RuntimeError("PostgreSQL schema authority mismatch")
    return conn


def qualified_physical_pg_epoch(conn: psycopg.Connection, source: str) -> None:
    # A source-qualified row can survive PostgreSQL PITR onto another WAL
    # timeline. Bind the physical cluster/timeline exactly as the mature
    # PgAdmissionStore::require_pg_writer_epoch does before any host effect.
    physical = conn.execute(
        "SELECT (SELECT system_identifier::text FROM pg_control_system()) AS system_id,"
        " (SELECT timeline_id FROM pg_control_checkpoint()) AS timeline,"
        " (SELECT left(pg_walfile_name(pg_current_wal_lsn()),8)) AS wal_timeline"
    ).fetchone()
    if physical is None or physical["timeline"] < 1 or (
        physical["wal_timeline"] != f'{physical["timeline"]:08X}'
    ):
        raise RuntimeError("PostgreSQL WAL timeline not qualified for release")
    expected_epoch = hashlib.sha256(
        ("ordivon-pg-writer-epoch-v1\0" + source + "\0" +
         str(physical["system_id"]) + "\0" +
         str(physical["timeline"])).encode("utf-8")
    ).hexdigest()
    epoch = conn.execute(
        "SELECT state,source_sha256,promotion_allowed FROM _stage_control "
        "WHERE id='epoch'"
    ).fetchone()
    if (epoch is None or epoch["state"] != "QUALIFIED_EPOCH" or
        epoch["source_sha256"] != expected_epoch or
        not epoch["promotion_allowed"]):
        raise RuntimeError("physical PostgreSQL writer epoch is not operator-qualified")

def qualified_operator(conn: psycopg.Connection, source: str, *, lock: bool) -> None:
    """Operator qualification belongs to PostgreSQL + its privileged role."""
    clause = " FOR UPDATE" if lock else ""
    rows = conn.execute(
        "SELECT id,state,source_sha256,promotion_allowed FROM _stage_control "
        "WHERE id IN ('source','release') ORDER BY id" + clause
    ).fetchall()
    authority = {row["id"]: row for row in rows}
    writer, releaser = authority.get("source"), authority.get("release")
    if (
        writer is None or releaser is None
        or writer["state"] != "QUALIFIED_WRITER"
        or releaser["state"] != "QUALIFIED_RELEASE"
        or not writer["promotion_allowed"]
        or not releaser["promotion_allowed"]
        or writer["source_sha256"] != source
        or releaser["source_sha256"] != source
    ):
        raise RuntimeError("operator-owned PostgreSQL Release qualification absent")
    qualified_physical_pg_epoch(conn,source)
    # Application role may SELECT/lock stage-control but cannot qualify itself.
    allowed = conn.execute(
        "SELECT has_column_privilege(current_user,"
        "  current_schema() || '._stage_control','promotion_allowed','UPDATE') AS allowed"
    ).fetchone()
    if allowed is None or not allowed["allowed"]:
        raise RuntimeError("PostgreSQL role lacks independently granted operator authority")


def original_release_identity(row: dict[str, Any]) -> dict[str, Any]:
    request = {
        "schemaVersion": 1,
        "principal": row["principal"],
        "workspaceId": row["workspace_id"],
        "commit": row["commit_revision"],
        "candidateManifestDigest": row["candidate_manifest_digest"],
        "expectedToolCount": row["expected_tool_count"],
    }
    request_digest = "runtime-release-v1:" + digest(canonical_json(request).encode("utf-8"))
    effect = hashlib.sha256(
        ("runtime-release-effect-v1\0" + row["principal"] + "\0"
         + row["client_request_id"]).encode("utf-8")
    ).hexdigest()
    binding = {
        "contract": "runtime_release_v1",
        "effectId": effect,
        "requestDigest": request_digest,
        "workspaceId": row["workspace_id"],
        "commit": row["commit_revision"],
        "candidateManifestDigest": row["candidate_manifest_digest"],
        "expectedToolCount": row["expected_tool_count"],
        "receiptPath": row["receipt_path"],
    }
    snapshot = json.loads(row["workspace_snapshot_json"])
    if (
        row["contract"] != "runtime_release_v1"
        or row["effect_id"] != effect
        or row["request_digest"] != request_digest
        or row["side_request_digest"] != request_digest
        or row["side_workspace_id"] != row["workspace_id"]
        or row["binding_digest"] != digest(canonical_json(binding).encode("utf-8"))
        or snapshot.get("runtimeReleaseEffectDigest") != row["binding_digest"]
        or row["execution_plan_digest"] != digest(row["execution_plan_json"].encode("utf-8"))
        or row["desired_state"] != "run"
        or row["attempt_number"] != 1
        or (row["resolution"] is None and
            (row["attempt_state"] != "accepted" or row["reservation_state"] != "active"))
        or (row["resolution"] is not None and
            (row["attempt_state"] != row["resolution"] or
             row["reservation_state"] != "released" or
             row["attempt_result_digest"] is None))
    ):
        raise RuntimeError("Release effect/Job binding is incoherent or not in accepted state")
    return binding


_EFFECT_SELECT = """
SELECT j.job_id,j.principal,j.client_request_id,j.workspace_id,
 j.request_digest,j.workspace_snapshot_json,j.execution_plan_json,
 j.execution_plan_digest,j.desired_state,j.resolution,
 a.attempt_id,a.attempt_number,a.state AS attempt_state,
 a.result_digest AS attempt_result_digest,
 c.state AS reservation_state,
 r.effect_id,r.contract,r.request_digest AS side_request_digest,
 r.workspace_id AS side_workspace_id,r.commit_revision,r.candidate_manifest_digest,
 r.expected_tool_count,r.receipt_path,r.binding_digest
FROM jobs j
JOIN attempts a ON a.attempt_id=COALESCE(j.current_attempt_id,
    (SELECT last.attempt_id FROM attempts last
     WHERE last.job_id=j.job_id ORDER BY last.attempt_number DESC LIMIT 1))
    AND a.job_id=j.job_id
JOIN concurrency_reservations c ON c.attempt_id=a.attempt_id
JOIN job_runtime_release_effects r ON r.job_id=j.job_id
WHERE j.principal=%s AND j.client_request_id=%s
"""


def inspect_effect(
    conn: psycopg.Connection, *,
    principal: str, client_request_id: str, effect_id: str,
    commit: str, candidate_manifest_digest: str,
    receipt_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    row = conn.execute(_EFFECT_SELECT, (principal, client_request_id)).fetchone()
    if row is None:
        raise RuntimeError("no independently committed principal-owned ReleaseEffect")
    bound = original_release_identity(row)
    if (
        bound["effectId"] != effect_id or bound["commit"] != commit
        or bound["candidateManifestDigest"] != candidate_manifest_digest
    ):
        raise RuntimeError("ReleaseEffect intent does not match committed PostgreSQL identity")
    expected_path = (receipt_root / f"effect-{effect_id}").absolute()
    if Path(row["receipt_path"]) != expected_path:
        raise RuntimeError("ReleaseEffect receipt path differs from operator-owned root")
    return row, bound


def systemd_property(args: argparse.Namespace, name: str) -> str:
    """Read the effective systemd Unit, including its *last* drop-in override."""
    if name not in {"ExecStart", "MainPID", "EnvironmentFiles"}:
        raise RuntimeError("unsupported systemd process witness")
    try:
        command = subprocess.run(
            [str(args.systemctl), "show", "--no-pager", "--value",
             f"--property={name}", args.service],
            capture_output=True, text=True, check=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(
            f"RECONCILIATION_REQUIRED: systemd {name} is not observable"
        ) from error
    value = command.stdout.strip()
    if not value or len(value) > 4096:
        raise RuntimeError(f"RECONCILIATION_REQUIRED: invalid systemd {name} witness")
    return value


def qualified_service_executable_path(args: argparse.Namespace) -> Path:
    """The actual systemd ExecStart MUST name the same installed native PG binary.

    Installing bytes at installDir without checking effective ExecStart can
    'succeed' while a later systemd drop-in still boots a different immutable
    candidate. Tool catalog equality is not process image identity.
    """
    effective = systemd_property(args, "ExecStart")
    paths = re.findall(r"(?:^|\{)\s*path=([^;{}\n]+?)\s*;", effective)
    if len(paths) != 1:
        raise RuntimeError(
            "PG release preflight rejected: systemd ExecStart is not one native executable"
        )
    path = Path(paths[0].strip())
    expected = args.install_dir / "ordivon-runtime-pg"
    if not path.is_absolute() or path != expected:
        raise RuntimeError(
            "PG release preflight rejected: effective systemd ExecStart "
            "does not consume the Operator's installed PG binary"
        )
    return expected


def expected_runner_path(args: argparse.Namespace) -> Path:
    # A PG release never has a valid MainPID without its native Runner.
    # The actual Runner binding still comes from effective systemd, not a
    # caller-authored manifest or an optional binary list.
    require_complete_native_release(args)
    return args.install_dir / "ordivon-runtime-runner"


def effective_systemd_runner_binding(args: argparse.Namespace) -> str | None:
    """Get the final Runner assignment from systemd's effective EnvironmentFiles.

    EnvironmentFiles are loaded in Unit precedence order, including late
    drop-ins that silently supersede the base envFile. Reuse the mature
    environment parser and refuse ambiguous/non-regular source files.
    """
    files = systemd_property(args, "EnvironmentFiles").splitlines()
    if not files or len(files) > 32:
        raise RuntimeError("unqualified effective systemd EnvironmentFiles")
    paths: list[Path] = []
    runner = None
    for entry in files:
        match = re.fullmatch(
            r"(/[^()\r\n]{1,2048}) \(ignore_errors=(yes|no)\)", entry.strip(),
        )
        if match is None:
            raise RuntimeError("unsupported effective systemd EnvironmentFile")
        path = Path(match[1])
        paths.append(path)
        if not path.exists() and match[2] == "yes":
            continue
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("non-regular effective systemd EnvironmentFile")
        values = DEPLOY["load_environment_file"](path)
        if "ORDIVON_PG_RUNNER" in values:
            runner = values["ORDIVON_PG_RUNNER"]
    if args.env_file not in paths:
        raise RuntimeError("operator EnvironmentFile is not consumed by systemd")
    return runner


def qualified_runner_binding(args: argparse.Namespace) -> None:
    expected = expected_runner_path(args)
    # The declared base file is not authority: a later systemd drop-in can
    # override this value. Compare the effective ordered Unit environment.
    try:
        if (
            DEPLOY["load_environment_file"](args.env_file).get("ORDIVON_PG_RUNNER")
            != str(expected)
            or effective_systemd_runner_binding(args) != str(expected)
        ):
            raise RuntimeError("configured/effective Runner mismatch")
    except (OSError, UnicodeError, RuntimeError, ValueError) as error:
        raise RuntimeError(
            "PG release preflight rejected: effective systemd Runner "
            "does not consume the installed native Runner"
        ) from error


def verified_live_service_executable(args: argparse.Namespace) -> dict[str, Any]:
    """Bind the running systemd MainPID's executable inode+bytes to installDir.

    This is independent of a working network MCP catalog. Reading the live
    /proc/<MainPID>/exe descriptor detects an old deleted inode retained after
    replacement, as well as a different active path or digest.
    """
    try:
        expected = qualified_service_executable_path(args)
        text_pid = systemd_property(args, "MainPID")
        if not re.fullmatch(r"[1-9][0-9]{0,9}", text_pid):
            raise RuntimeError("invalid service MainPID")
        pid = int(text_pid)
        proc = Path(f"/proc/{pid}/exe")
        live_path = os.readlink(proc)
        if live_path != str(expected):
            raise RuntimeError("active process image path differs from installed artifact")
        with proc.open("rb") as active:
            live_hash = hashlib.file_digest(active, "sha256").hexdigest()
        candidate_hash = DEPLOY["sha256"](expected)
        if candidate_hash != f"sha256:{live_hash}":
            raise RuntimeError("active executable bytes differ from installed candidate")
        if systemd_property(args, "MainPID") != text_pid:
            raise RuntimeError("systemd MainPID changed during active image attestation")
    except (OSError, ValueError, UnicodeError, RuntimeError) as error:
        raise RuntimeError(
            "RECONCILIATION_REQUIRED: live systemd process does not consume installed Runtime"
        ) from error
    image = {
        "path": live_path,
        "digest": candidate_hash,
        "mainPid": pid,
        "witness": "systemd_MainPID_proc_exe",
    }
    return image


def physical_preflight(args: argparse.Namespace, effect: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require_complete_native_release(args)
    # Full candidate manifest/ref/installed binary checks are the SAME
    # release primitives that the existing Runtime installer uses.
    specs = list(DEPLOY["release_artifact_specs"](args))
    candidate = DEPLOY["candidate_artifacts"](args)
    summary, blockers = DEPLOY["validate_candidate_manifest"](args, candidate)
    authorisation = DEPLOY["required_ref_authority"](
        args.git, args.source_repo, args.commit, args.require_ref,
    )
    if not authorisation["authorized"]:
        blockers.append("candidate is not authorized by required source ref")
    if effect["candidateManifestDigest"] != DEPLOY["sha256"](args.candidate_manifest):
        blockers.append("effect references different candidate manifest bytes")
    if effect["expectedToolCount"] != args.expected_tool_count:
        blockers.append("operator expectedToolCount differs from committed release")
    if args.confirm_commit != args.commit:
        blockers.append("operator confirm-commit does not match committed source")
    # A configured Unit can be healthy and expose the same MCP catalog while
    # executing a *different* binary from a last-wins systemd drop-in.
    # Fail BEFORE committing the one-use dispatch identity or touching systemd.
    qualified_service_executable_path(args)
    qualified_runner_binding(args)
    for spec in specs:
        name = str(spec["name"])
        path = args.install_dir / name
        if not path.is_file() or path.is_symlink():
            blockers.append(f"installed Runtime artifact missing/unsafe: {name}")
    if blockers:
        raise RuntimeError("PG release preflight rejected: " + "; ".join(blockers))
    return specs, summary


def effect_request(args: argparse.Namespace, bound: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract": "runtime_release_v1",
        "effectId": bound["effectId"],
        "requestDigest": bound["requestDigest"],
        "commit": bound["commit"],
        "candidateManifestDigest": bound["candidateManifestDigest"],
        "expectedToolCount": bound["expectedToolCount"],
        "sourceRepo": str(args.source_repo.absolute()),
        "candidateDir": str(args.candidate_dir.absolute()),
        "candidateManifest": str(args.candidate_manifest.absolute()),
        "installDir": str(args.install_dir.absolute()),
        "envFile": str(args.env_file.absolute()),
        "receiptRoot": str(args.receipt_root.absolute()),
        "service": args.service,
        "requiredRef": args.require_ref,
        "requiredTools": list(args.required_tools),
        "releaseArtifacts": [
            {"name": x["name"], "kind": x["kind"], "mode": x["mode"]}
            for x in DEPLOY["release_artifact_specs"](args)
        ],
    }


def dispatch_claim(
    conn: psycopg.Connection, args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """One durable operator dispatch generation, before any host mutation.

    Repeated invocation is rejected even after an unknown COMMIT; the caller
    must inspect the exact PG row + existing receipt, not redispatch.
    """
    conn.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (ADMISSION_LOCK,))
        qualified_operator(conn, args.source_sha256, lock=True)
        row, bound = inspect_effect(
            conn, principal=args.principal, client_request_id=args.client_request_id,
            effect_id=args.effect_id, commit=args.commit,
            candidate_manifest_digest=args.candidate_manifest_digest,
            receipt_root=args.receipt_root,
        )
        if row["resolution"] is not None:
            raise RuntimeError("ReleaseEffect already terminal; dispatch must not replay")
        existing = conn.execute(
            "SELECT event_sequence FROM job_events WHERE job_id=%s "
            "AND event_type=%s",
            (row["job_id"], DISPATCH_EVENT),
        ).fetchone()
        if existing is not None:
            raise RuntimeError("RECONCILIATION_REQUIRED: operator dispatch was already committed")
        # Source-qualified PG admission serializes on this lock as well.
        # Replay with the same clientRequestId never passes this guard twice.
        observed_ms = int(time.time() * 1000)
        detail = canonical_json({
            "effectId": bound["effectId"],
            "requestDigest": bound["requestDigest"],
            "commit": bound["commit"],
        })
        next_seq = conn.execute(
            "SELECT COALESCE(MAX(event_sequence),0)+1 AS next FROM job_events WHERE job_id=%s",
            (row["job_id"],),
        ).fetchone()["next"]
        event_id = "event-" + os.urandom(16).hex()
        conn.execute(
            "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,"
            "event_type,origin,previous_state,new_state,reason_code,detail_json,"
            "detail_digest,observed_at_ms) "
            "VALUES(%s,%s,%s,%s,%s,'OPERATOR_DERIVED',NULL,NULL,"
            "'RELEASE_OPERATOR_DISPATCH_COMMITTED',%s,%s,%s)",
            (event_id,row["job_id"],row["attempt_id"],next_seq,DISPATCH_EVENT,
             detail,digest(detail.encode()),observed_ms),
        )
    # DB COMMIT acknowledgment is the boundary. A failed/ambiguous COMMIT
    # above is never followed by host installation.
    return row, bound


def active_executions(conn: psycopg.Connection, release_job_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT job_id FROM jobs WHERE resolution IS NULL AND job_id <> %s "
        "ORDER BY created_at_ms LIMIT 64", (release_job_id,),
    ).fetchall()
    return [row["job_id"] for row in rows]


def pg_mcp_readiness(args: argparse.Namespace) -> dict[str, Any]:
    """Reuse the mature MCP catalog probe with native PG configuration."""
    require_complete_native_release(args)
    environment = DEPLOY["load_environment_file"](args.env_file)
    bind = environment.get("ORDIVON_PG_BIND")
    token = environment.get("ORDIVON_PG_TOKEN")
    if not bind or not token or len(token) < 32:
        raise RuntimeError("native PG MCP bind/token missing from operator service")
    if not DEPLOY["service_active"](args.systemctl,args.service):
        raise RuntimeError("qualified PG Runtime service is not active")
    probe = DEPLOY["probe_catalog"](
        f"http://{bind}/mcp",
        token,
        client_name="ordivon-runtime-pg-operator",
        expected_tool_count=args.expected_tool_count,
        required_tools=tuple(args.required_tools),
        wait_seconds=args.wait_seconds,
        require_modern=True,
        allow_legacy_fallback=False,
    )
    # Catalog/HTTP readiness proves a service responds, not which image or
    # actual Runner its execution provider consumes. Use existing OS and
    # authenticated native Runtime consumers, not a second config parser.
    image = verified_live_service_executable(args)
    runner = expected_runner_path(args)
    try:
        described = McpClient(
            f"http://{bind}/mcp", token,
            "ordivon-runtime-pg-operator-runner-witness",
            timeout=min(15.0, max(1.0, args.wait_seconds)),
        ).call_tool("runtime.describe", {"schemaVersion": 1})
        targets = described.get("targets")
        if not isinstance(targets, list) or len(targets) != 1:
            raise RuntimeError("native Runner target projection is incomplete")
        provider = targets[0].get("executionProvider")
        if (
            targets[0].get("target") != "local_linux"
            or not isinstance(provider, dict)
            or provider.get("contract") != "local_linux_runner_v1"
            or provider.get("executableDigest") != DEPLOY["sha256"](runner)
        ):
            raise RuntimeError("native Runner provider digest differs from installed Runner")
        image["runnerDigest"] = provider["executableDigest"]
        image["runnerWitness"] = "authenticated_runtime_describe"
    except (OSError, RuntimeError, ValueError, TypeError) as error:
        raise RuntimeError(
            "RECONCILIATION_REQUIRED: actual Runtime Runner does not match installed candidate"
        ) from error
    return {**probe, "activeRuntimeImage": image}


def operator_fenced_install(
    conn: psycopg.Connection,
    args: argparse.Namespace,
    row: dict[str, Any],
    bound: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, Any]:
    """One immutable physical install under PG admission and OS locks."""
    specs, candidate_summary = physical_preflight(args, bound)
    receipt = args.receipt_root / f"effect-{args.effect_id}"
    previous = receipt / "previous"
    previous.mkdir(parents=True, exist_ok=False)
    baseline: list[dict[str, Any]] = []
    for spec in specs:
        name = str(spec["name"])
        installed = args.install_dir / name
        mode = stat.S_IMODE(installed.stat().st_mode)
        DEPLOY["atomic_copy"](installed, previous / name, mode=mode)
        record = DEPLOY["artifact_description"](previous / name, {
            "name": name, "kind": spec["kind"], "mode": mode,
        })
        record["present"] = True
        baseline.append(record)
    DEPLOY["write_json_atomic"](receipt / "manifest.json", {
        "schemaVersion": 2,
        "commit": args.commit,
        "service": args.service,
        "installDir": str(args.install_dir),
        "envFile": str(args.env_file),
        "previous": baseline,
        "candidate": candidate_summary,
        "releaseEffect": request,
    })
    replaced = False
    stopped = False
    source_epoch = None
    try:
        # This is an independent PostgreSQL connection/transaction from the
        # already COMMITTED operator-dispatch event. Keep the source row
        # FOR UPDATE until the actual systemd cutover is complete, fencing
        # ordinary PG admissions while preserving the immutable issue record.
        conn.isolation_level = psycopg.IsolationLevel.READ_COMMITTED
        with conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (ADMISSION_LOCK,))
            qualified_operator(conn, args.source_sha256, lock=True)
            epoch = conn.execute(
                "SELECT source_sha256 FROM _stage_control WHERE id='epoch'"
            ).fetchone()
            source_epoch = epoch["source_sha256"] if epoch else None
            deadline = time.monotonic() + args.drain_seconds
            while True:
                active = active_executions(conn, row["job_id"])
                if not active:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("PG execution drain timed out: " + ", ".join(active))
                time.sleep(0.1)
            # All ordinary Jobs are drained; new admission is blocked by
            # the PostgreSQL source row lock, not a local SQLite file.
            DEPLOY["run"]([str(args.systemctl), "stop", args.service])
            stopped = True
            if active_executions(conn, row["job_id"]):
                raise RuntimeError("new PG Job found after service stop")
            # The same immutable manifest/ref and installed preimage must still
            # hold at the physical cutover point.
            physical_preflight(args, bound)
            for spec in specs:
                name = str(spec["name"])
                DEPLOY["atomic_copy"](
                    args.candidate_dir / name,
                    args.install_dir / f"{name}.next",
                    mode=int(spec["mode"]),
                )
            # Once the first rename is attempted, a partial physical cutover
            # is possible. The rollback path must cover failures *inside*
            # this loop, not only failures after the last rename.
            replaced = True
            for spec in specs:
                name = str(spec["name"])
                os.replace(args.install_dir / f"{name}.next", args.install_dir / name)
            DEPLOY["run"]([str(args.systemctl), "start", args.service])
            probe = pg_mcp_readiness(args)
            installed = [
                DEPLOY["artifact_description"](args.install_dir / str(spec["name"]), spec)
                for spec in specs
            ]
            observed = {(item["name"],item["digest"]) for item in installed}
            expected = {(item["name"],item["digest"]) for item in
                        DEPLOY["candidate_artifacts"](args)}
            if observed != expected:
                raise RuntimeError("installed artifacts differ from immutable candidate")
            result = {
                "schemaVersion": 2,
                "status": "deployed",
                "commit": args.commit,
                "finishedAtMs": int(time.time() * 1000),
                "serviceActive": True,
                "probe": probe,
                "installed": installed,
                "receipt": str(receipt),
                "releaseEffect": request,
                "pgSourceEpoch": source_epoch,
            }
            DEPLOY["write_json_atomic"](receipt / "result.json", result)
            return result
    except BaseException as failure:
        for spec in specs:
            (args.install_dir / (str(spec["name"]) + ".next")).unlink(missing_ok=True)
        status = "not_committed"
        rollback = None
        if replaced:
            # A closed/failed PG connection is not proof of an unchanged
            # Registry epoch. Never roll back the binary across unknown PG truth.
            try:
                current = conn.execute(
                    "SELECT source_sha256 FROM _stage_control WHERE id='epoch'"
                ).fetchone()
                if not current or current["source_sha256"] != source_epoch:
                    raise RuntimeError("PG epoch changed; binary rollback unsafe")
                rollback = DEPLOY["restore_previous"](
                    previous, args.install_dir, baseline, args.systemctl,
                    args.service,args.env_file,args.wait_seconds,
                )
                status = "rolled_back"
            except Exception as restore_failure:
                status = "reconciliation_required"
                rollback = {"error":str(restore_failure),"suppressed":True}
        elif stopped:
            try:
                DEPLOY["run"]([str(args.systemctl),"start",args.service])
            except Exception as resume_error:
                status = "reconciliation_required"
                rollback = {"error":str(resume_error),"suppressed":True}
        result = {
            "schemaVersion":2,"status":status,"commit":args.commit,
            "finishedAtMs":int(time.time()*1000),
            "deploymentError":str(failure),
            "rollback":rollback,
            "receipt":str(receipt),
            "releaseEffect":request,
            "pgSourceEpoch":source_epoch,
        }
        DEPLOY["write_json_atomic"](receipt / "result.json", result)
        raise RuntimeError(f"PG release {status}: {failure}") from failure


def finalize_receipted_release(
    conn: psycopg.Connection,
    args: argparse.Namespace,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Reconcile an existing terminal installer receipt, never rerun an install."""
    require_complete_native_release(args)
    receipt_dir = args.receipt_root / f"effect-{args.effect_id}"
    result = DEPLOY["existing_structured_release_result"](receipt_dir, request)
    if result is None:
        raise RuntimeError("RECONCILIATION_REQUIRED: operator receipt is missing")
    # The Runtime reader is still the independent receipt verifier. We
    # serialize ONLY the authenticated operator's committed effect outcome.
    status = result.get("status")
    if status == "deployed":
        # External result.json is not a PostgreSQL commit witness by itself.
        # Re-observe the installed bytes and live MCP catalog BEFORE turning
        # accepted release Job into succeeded. This is a read-only physical
        # check and never repeats installation or systemd mutations.
        probe = result.get("probe")
        if (
            result.get("serviceActive") is not True
            or not isinstance(probe,dict)
            or probe.get("toolCount") != args.expected_tool_count
            or not isinstance(probe.get("toolCatalogDigest"),str)
            or not DIGEST.fullmatch(probe["toolCatalogDigest"])
        ):
            raise RuntimeError("RECONCILIATION_REQUIRED: no qualified deployed MCP receipt")
        expected = {
            (item["name"],item["digest"])
            for item in DEPLOY["candidate_artifacts"](args)
        }
        installed = result.get("installed")
        if not isinstance(installed,list) or not all(
            isinstance(entry,dict)
            and isinstance(entry.get("name"),str)
            and isinstance(entry.get("digest"),str)
            for entry in installed
        ):
            raise RuntimeError("RECONCILIATION_REQUIRED: installed artifact attestation absent")
        attested={(entry["name"],entry["digest"]) for entry in installed}
        actual={
            (item["name"],item["digest"])
            for item in [
                DEPLOY["artifact_description"](
                    args.install_dir / spec["name"],spec
                )
                for spec in DEPLOY["release_artifact_specs"](args)
            ]
        }
        if expected != attested or expected != actual:
            raise RuntimeError("RECONCILIATION_REQUIRED: installed bytes or receipt differ from candidate")
        live=pg_mcp_readiness(args)
        if (
            live.get("toolCount") != args.expected_tool_count
            or live.get("toolCatalogDigest") != probe["toolCatalogDigest"]
        ):
            raise RuntimeError("RECONCILIATION_REQUIRED: live PG MCP catalog differs from receipt")
        terminal = "succeeded"
    elif status in {"not_committed", "rolled_back"}:
        terminal = "failed"
    else:
        raise RuntimeError(
            "RECONCILIATION_REQUIRED: unsafe/unknown installer result cannot release PG reservation"
        )
    receipt_bytes = (receipt_dir / "result.json").read_bytes()
    result_digest = digest(receipt_bytes)
    observed = int(time.time() * 1000)
    conn.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (ADMISSION_LOCK,))
        row, bound = inspect_effect(
            conn,principal=args.principal,client_request_id=args.client_request_id,
            effect_id=args.effect_id,commit=args.commit,
            candidate_manifest_digest=args.candidate_manifest_digest,
            receipt_root=args.receipt_root,
        )
        issued = conn.execute(
            "SELECT count(*) AS n FROM job_events WHERE job_id=%s AND event_type=%s",
            (row["job_id"], DISPATCH_EVENT),
        ).fetchone()["n"]
        if issued != 1:
            raise RuntimeError("no independently committed operator dispatch evidence")
        if row["resolution"] is not None:
            # Recover a lost response from the exact immutable operator receipt.
            # No physical installation, new PG event or second terminal update.
            if (row["resolution"] != terminal or
                row["attempt_result_digest"] != result_digest):
                raise RuntimeError("RECONCILIATION_REQUIRED: terminal Job conflicts with receipt")
            return {**result, "replayed":True, "pgTerminal":terminal,
                    "resultDigest":result_digest}
        qualified_operator(conn,args.source_sha256,lock=True)
        changed = conn.execute(
            "UPDATE attempts SET state=%s,result_digest=%s,finished_at_ms=%s,"
            "row_version=row_version+1 WHERE attempt_id=%s AND state='accepted'",
            (terminal,result_digest,observed,row["attempt_id"]),
        ).rowcount
        if changed != 1:
            raise RuntimeError("release Attempt no longer accepted")
        conn.execute(
            "UPDATE concurrency_reservations SET state='released',"
            "released_at_ms=%s,state_observed_at_ms=%s,"
            "release_reason='RELEASE_EFFECT_RECEIPTED' "
            "WHERE attempt_id=%s AND state='active'",
            (observed,observed,row["attempt_id"]),
        )
        changed = conn.execute(
            "UPDATE jobs SET resolution=%s,current_attempt_id=NULL,"
            "row_version=row_version+1 WHERE job_id=%s AND resolution IS NULL",
            (terminal,row["job_id"]),
        ).rowcount
        if changed != 1:
            raise RuntimeError("release Job already terminal or superseded")
        first = conn.execute(
            "SELECT COALESCE(MAX(event_sequence),0)+1 AS seq FROM job_events WHERE job_id=%s",
            (row["job_id"],)
        ).fetchone()["seq"]
        events = [
            ("RELEASE_EFFECT_RECEIPTED","OPERATOR_OBSERVED", {
                "resultDigest":result_digest,
                "receiptDigest":result_digest,
                "effectId":bound["effectId"],
                "requestDigest":bound["requestDigest"],
            }),
            ("JOB_TERMINAL","SYSTEM_DERIVED",{"resolution":terminal}),
        ]
        for idx,(event,origin,detail) in enumerate(events):
            encoded = canonical_json(detail)
            conn.execute(
                "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,"
                "event_type,origin,previous_state,new_state,reason_code,detail_json,"
                "detail_digest,observed_at_ms) "
                "VALUES(%s,%s,%s,%s,%s,%s,'accepted',%s,"
                "'RELEASE_EFFECT_RECEIPTED',%s,%s,%s)",
                ("event-"+os.urandom(16).hex(),row["job_id"],row["attempt_id"],
                 first+idx,event,origin,terminal,encoded,digest(encoded.encode()),observed),
            )
    return {**result,"replayed":True,"pgTerminal":terminal,"resultDigest":result_digest}


def verified_release_consumer(
    args: argparse.Namespace, result: dict[str, Any],
) -> None:
    """Reuse the existing authenticated Rust release.get standing for a terminal effect.

    The Operator owns physical installation and PostgreSQL commit; it does not
    own another independent terminal-event verifier. Only the current native
    MCP projection has already checked the lifecycle, terminal event digests,
    immutable receipt, and owner-bound Attempt in one qualified PG readback.
    A lost reply or corrupted PG event must be inconclusive, not an optimistic
    report of a previously committed systemd effect.
    """
    require_complete_native_release(args)
    terminal = result.get("pgTerminal")
    status = result.get("status")
    expected = {
        "deployed": ("succeeded", "deployed"),
        "not_committed": ("failed", "not_committed"),
        "rolled_back": ("failed", "rolled_back"),
    }.get(status)
    if expected is None or terminal != expected[0]:
        raise RuntimeError("RECONCILIATION_REQUIRED: unqualified release terminal standing")
    environment = DEPLOY["load_environment_file"](args.env_file)
    bind = environment.get("ORDIVON_PG_BIND")
    token = environment.get("ORDIVON_PG_TOKEN")
    if not bind or not token or len(token) < 32:
        raise RuntimeError("RECONCILIATION_REQUIRED: native PG MCP credential missing")
    try:
        client = McpClient(
            f"http://{bind}/mcp", token, "ordivon-runtime-pg-operator-standing",
            timeout=min(15.0, max(1.0, args.wait_seconds)),
        )
        projection = client.call_tool(
            "release.get", {"clientRequestId": args.client_request_id},
        )
    except Exception as error:
        # Do not return a false successful replay if Rust's verified PG
        # terminal journal readback or the actual consumer endpoint is down.
        raise RuntimeError(
            "RECONCILIATION_REQUIRED: canonical release.get did not verify the effect"
        ) from error
    receipt = args.receipt_root / f"effect-{args.effect_id}" / "result.json"
    try:
        receipt_digest = digest(receipt.read_bytes())
    except OSError as error:
        raise RuntimeError(
            "RECONCILIATION_REQUIRED: operator receipt changed during readback"
        ) from error
    required = {
        "effectId": args.effect_id,
        "clientRequestId": args.client_request_id,
        "commit": args.commit,
        "candidateManifestDigest": args.candidate_manifest_digest,
        "expectedToolCount": args.expected_tool_count,
        "effectDisposition": expected[1],
        "executionDisposition": terminal,
        "receiptDigest": receipt_digest,
        "effectTerminal": True,
        "executionTerminal": True,
        "receiptAvailable": True,
        "recoveryRequired": False,
        "semanticCompletionEvaluated": False,
    }
    if any(projection.get(name) != value for name, value in required.items()):
        raise RuntimeError(
            "RECONCILIATION_REQUIRED: canonical release.get disagrees with operator receipt"
        )
    if status == "deployed" and (
        projection.get("deployedToolCount") != args.expected_tool_count
    ):
        raise RuntimeError(
            "RECONCILIATION_REQUIRED: verified release Tool count mismatch"
        )


def operator_approved_systemd_services() -> frozenset[str]:
    """Host-operator-owned authority, never a caller-supplied CLI allowlist."""
    raw = os.environ.get("ORDIVON_PG_RELEASE_ALLOWED_SERVICES_JSON")
    if raw is None:
        raise RuntimeError("independent operator service qualification unavailable")
    try:
        value = json.loads(raw)
    except ValueError as error:
        raise RuntimeError("invalid operator systemd service allowlist") from error
    if (
        not isinstance(value,list)
        or not value
        or len(value)>20
        or not all(isinstance(item,str)
                   and re.fullmatch(r"ordivon-[a-zA-Z0-9-]+\.service",item)
                   for item in value)
        or len(value)!=len(set(value))
    ):
        raise RuntimeError("invalid qualified systemd service allowlist")
    return frozenset(value)


def apply_release(args: argparse.Namespace) -> dict[str, Any]:
    require_complete_native_release(args)
    qualify(args.effect_id,EFFECT,"effectId")
    qualify(args.commit,COMMIT,"commit")
    qualify(args.candidate_manifest_digest,DIGEST,"candidateManifestDigest")
    qualify(args.source_sha256,re.compile(r"^[a-f0-9]{64}$"),"sourceSHA")
    if args.expected_tool_count < 1 or args.expected_tool_count > 1000:
        raise RuntimeError("invalid qualified Tool count")
    if args.service not in operator_approved_systemd_services():
        raise RuntimeError("systemd service is not independently operator-approved")
    if not args.receipt_root.is_absolute() or not args.install_dir.is_absolute():
        raise RuntimeError("operator paths must be absolute")
    if args.receipt_root.is_symlink() or args.install_dir.is_symlink():
        raise RuntimeError("operator release roots cannot be symlinks")
    with DEPLOY["exclusive_lock"](args.lock_file):
        with pg_connection(args.pg_dsn,args.pg_schema) as conn:
            qualified_physical_pg_epoch(conn,args.source_sha256)
            row, bound = inspect_effect(
                conn,principal=args.principal,client_request_id=args.client_request_id,
                effect_id=args.effect_id,commit=args.commit,
                candidate_manifest_digest=args.candidate_manifest_digest,
                receipt_root=args.receipt_root,
            )
            request = effect_request(args,bound)
            receipt = args.receipt_root / f"effect-{args.effect_id}"
            if receipt.exists():
                # Reconcile durable PG metadata once, then require the SAME
                # authenticated terminal standing read by release.get.
                # No binary restart or new effect is performed on this path.
                final = finalize_receipted_release(conn,args,request)
                verified_release_consumer(args, final)
                return final
            qualified_operator(conn,args.source_sha256,lock=False)
            physical_preflight(args,bound)
            dispatch_claim(conn,args)
            # No exceptions or retries across an uncertain dispatch COMMIT.
            receipt.mkdir(parents=True,exist_ok=False)
            DEPLOY["write_json_atomic"](receipt / "effect-request.json",request)
            try:
                result = operator_fenced_install(conn,args,row,bound,request)
            except RuntimeError:
                if (receipt / "result.json").is_file():
                    try:
                        finalize_receipted_release(conn,args,request)
                    except Exception:
                        # Preserve the originally committed release identity
                        # and its receipt for an explicit reconcile attempt.
                        pass
                raise
            # Physical systemd receipt precedes PG terminal commit, and only
            # the canonical native release.get consumer can certify Standing.
            final = finalize_receipted_release(conn,args,request)
            delivered = {**result,"pgTerminal":final["pgTerminal"]}
            verified_release_consumer(args, delivered)
            return delivered


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ordivon-runtime-pg-operator",
        description="Independent PostgreSQL-qualified Runtime release operator. NOT an MCP Tool.",
    )
    parser.add_argument("action",choices=("inspect","apply"))
    parser.add_argument("--pg-schema",required=True)
    parser.add_argument("--source-sha256",required=True)
    parser.add_argument("--principal",required=True)
    parser.add_argument("--client-request-id",required=True)
    parser.add_argument("--effect-id",required=True)
    parser.add_argument("--commit",required=True)
    parser.add_argument("--confirm-commit",required=True)
    parser.add_argument("--candidate-manifest-digest",required=True)
    parser.add_argument("--expected-tool-count",type=int,required=True)
    parser.add_argument("--source-repo",type=Path,required=True)
    parser.add_argument("--candidate-dir",type=Path,required=True)
    parser.add_argument("--candidate-manifest",type=Path,required=True)
    parser.add_argument("--install-dir",type=Path,required=True)
    parser.add_argument("--receipt-root",type=Path,required=True)
    parser.add_argument("--env-file",type=Path,required=True)
    parser.add_argument("--service",required=True)
    parser.add_argument("--required-tool",action="append",dest="required_tools",default=[])
    parser.add_argument("--binary",action="append",dest="binaries",required=True)
    parser.add_argument("--require-ref",default="origin/main")
    parser.add_argument("--drain-seconds",type=float,default=30.0)
    parser.add_argument("--wait-seconds",type=float,default=60.0)
    parser.add_argument("--lock-file",type=Path,required=True)
    parser.add_argument("--systemctl",type=Path,default=Path("/usr/bin/systemctl"))
    parser.add_argument("--git",type=Path,default=Path("/usr/bin/git"))
    args = parser.parse_args()
    # PG service credentials must belong to the qualified operator's
    # environment; never pass secrets from the caller's release request.
    args.pg_dsn = os.environ.get("ORDIVON_PG_RELEASE_OPERATOR_DSN","")
    if not args.pg_dsn:
        parser.error("independent ORDIVON_PG_RELEASE_OPERATOR_DSN required")
    args.source_repo = args.source_repo.absolute()
    args.candidate_dir = args.candidate_dir.absolute()
    args.candidate_manifest = args.candidate_manifest.absolute()
    args.install_dir = args.install_dir.absolute()
    args.receipt_root = args.receipt_root.absolute()
    args.env_file = args.env_file.absolute()
    args.lock_file = args.lock_file.absolute()
    return args


def main() -> int:
    args = arguments()
    require_complete_native_release(args)
    if args.action=="inspect":
        with pg_connection(args.pg_dsn,args.pg_schema) as conn:
            qualified_operator(conn,args.source_sha256,lock=False)
            _row,bound = inspect_effect(
                conn,principal=args.principal,client_request_id=args.client_request_id,
                effect_id=args.effect_id,commit=args.commit,
                candidate_manifest_digest=args.candidate_manifest_digest,
                receipt_root=args.receipt_root,
            )
            physical_preflight(args,bound)
            print(json.dumps({"qualified":True,"effectId":args.effect_id,"commit":args.commit}))
            return 0
    result=apply_release(args)
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PG runtime release operator: {exc}",file=sys.stderr)
        raise SystemExit(1)
