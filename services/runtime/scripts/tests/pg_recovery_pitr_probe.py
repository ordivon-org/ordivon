#!/usr/bin/env python3
"""Isolated PostgreSQL 18 PITR / Runtime schema counterexample probe.

External effects are only simulated by a file in this disposable private root.
This is a *source/schema* falsifier, not production Runtime, backup-policy,
restore RPO/RTO, or exactly-once external-effect qualification.

Run explicitly: python3 services/runtime/scripts/tests/pg_recovery_pitr_probe.py
Needs root in a trusted, disposable Linux test host and PostgreSQL 18 binaries.
Never passes a production DSN or modifies existing PG/service/HBA.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

RUNTIME = Path(__file__).resolve().parents[2]
SOURCE_SQL = RUNTIME / "crates/ordivon-runtime-core/sql/pg_fresh_epoch.sql"
SCHEMA_SHA = "bc6ad5d04b37fa0a8beb5b3eb1938064e803ef205c7cc2d3c346cca4f57626b9"
SCHEMA = "ordivon_recovery_r1"
PG = "/usr/bin/"
RUNUSER = "/usr/sbin/runuser"


def require(condition: bool, description: str) -> None:
    if not condition:
        raise AssertionError(description)


def run(argv: list[str], *, input_text: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, input=input_text, text=True, capture_output=True, check=check, timeout=70)


def postgres(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run([RUNUSER, "-u", "postgres", "--", *args], check=check)


def chown_tree(path: Path) -> None:
    uid, gid = 0, 0
    import pwd

    entry = pwd.getpwnam("postgres")
    uid, gid = entry.pw_uid, entry.pw_gid
    for directory, dirs, files in os.walk(path):
        os.chown(directory, uid, gid)
        for name in files:
            os.chown(Path(directory) / name, uid, gid)


def execute(root: Path) -> dict[str, object]:
    socket = root / "socket"
    archive = root / "archive"
    socket.mkdir()
    archive.mkdir()
    chown_tree(root)
    root.chmod(0o700)
    socket.chmod(0o700)
    for name in ("initdb", "pg_ctl", "pg_basebackup", "pg_verifybackup", "psql"):
        require(Path(PG + name).exists(), f"missing {name}")
    source_bytes = SOURCE_SQL.read_bytes()
    require(hashlib.sha256(source_bytes).hexdigest() == SCHEMA_SHA, "schema SourceCut changed")
    postgres(
        PG + "initdb", "-D", str(root / "primary"), "--auth-local=trust", "--auth-host=reject", "--no-instructions"
    )
    config = root / "primary/postgresql.conf"
    with config.open("a", encoding="utf-8") as f:
        f.write(
            f"\narchive_mode = on\narchive_command = 'test ! -f {archive}/%f && cp %p {archive}/%f'\narchive_timeout = '1s'\n"
        )

    def ctl(name: str, *args: str, port: int | None = None, pitr: bool = False) -> None:
        path = root / name
        cmd = [PG + "pg_ctl", "-D", str(path)]
        if port is not None:
            opts = f"-c listen_addresses='' -c unix_socket_directories='{socket}' -p {port}"
            if pitr:
                opts += f" -c restore_command='cp {archive}/%f %p'"
                opts += " -c recovery_target_name=ordivon_after_first_extra -c recovery_target_action=promote"
            cmd.extend(["-l", str(root / f"{name}.log"), "-o", opts, "-w", "start"])
        else:
            cmd.extend(["-m", "immediate", "-w", "stop"])
        # PG daemon must not inherit captured stdout/stderr pipes; otherwise
        # subprocess.communicate waits for the live postmaster after pg_ctl exits.
        subprocess.run(
            [RUNUSER, "-u", "postgres", "--", *cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=35,
        )

    active: set[str] = set()

    def start(name: str, port: int, *, pitr: bool = False) -> None:
        ctl(name, port=port, pitr=pitr)
        active.add(name)

    def stop(name: str) -> None:
        if name in active:
            ctl(name)
            active.remove(name)

    def sql(port: int, query: str, db: str = "recovery_lab", *, check: bool = True) -> subprocess.CompletedProcess[str]:
        return postgres(
            "/usr/bin/env",
            f"PGOPTIONS=-c search_path={SCHEMA},public",
            PG + "psql",
            "-X",
            "-qAt",
            "-w",
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            str(socket),
            "-p",
            str(port),
            "-U",
            "postgres",
            "-d",
            db,
            "-c",
            query,
            check=check,
        )

    def value(port: int, query: str) -> str:
        return sql(port, query).stdout.strip()

    def insert(job_id: str, request: str, t: int, *, principal: str = "actor") -> str:
        return (
            "INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,"
            "workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,"
            "created_at_ms,desired_state) VALUES("
            f"'{job_id}','{principal}','{request}','sha256:req','sha256:op','ws-lab',"
            f"'{{}}','{{}}','sha256:plan',{t},'run')"
        )

    started = time.monotonic()
    try:
        start("primary", 55491)
        sql(55491, "CREATE DATABASE recovery_lab", db="postgres")
        sql(55491, f"CREATE SCHEMA {SCHEMA}")
        # Root owns repo; postgres need not be given read access to root/source.
        run(
            [
                RUNUSER,
                "-u",
                "postgres",
                "--",
                "/usr/bin/env",
                f"PGOPTIONS=-c search_path={SCHEMA},public",
                PG + "psql",
                "-X",
                "-q",
                "-w",
                "-v",
                "ON_ERROR_STOP=1",
                "-h",
                str(socket),
                "-p",
                "55491",
                "-U",
                "postgres",
                "-d",
                "recovery_lab",
            ],
            input_text=source_bytes.decode(),
        )
        require(
            value(55491, f"SELECT count(*) FROM information_schema.tables WHERE table_schema='{SCHEMA}'") == "8",
            "schema tables",
        )
        sql(55491, insert("job-base", "request-base", 100))
        sql(
            55491,
            "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,"
            "launch_token_digest,bundle_path,unit_name,created_at_ms) VALUES("
            "'attempt-base','job-base',1,'succeeded','natural','sha256:token','/scratch','unit-base',101)",
        )
        sql(
            55491,
            "INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest)"
            " VALUES('artifact-base','job-base','attempt-base','stdout','out.txt','sha256:body')",
        )
        sql(
            55491,
            "INSERT INTO _stage_control(id,state,source_sha256,promotion_allowed)"
            " VALUES('lab','STAGED','sha256:lab',false)",
        )

        # Deliberately seal the operator-owned "source" qualification BEFORE
        # the base backup.  PITR will restore this row even after branching.
        sql(
            55491,
            "INSERT INTO _stage_control(id,state,source_sha256,promotion_allowed)"
            " VALUES('source','QUALIFIED_WRITER','" + "a" * 64 + "',true)",
        )
        original_system_id = value(55491, "SELECT system_identifier FROM pg_control_system()")
        original_timeline = int(value(55491, "SELECT timeline_id FROM pg_control_checkpoint()"))
        # Hypothetical operator authority (separate from restored PG):
        # only an externally current epoch seal can defeat timeline rollback.
        # This test does NOT install or authorize a production writer.
        seal = {"systemId": original_system_id, "timelineId": original_timeline, "sourceSha": "a" * 64}
        (root / "operator-qualification-seal.json").write_text(json.dumps(seal, sort_keys=True))
        require(
            value(55491, "SELECT source_sha256 FROM _stage_control WHERE id='source'") == seal["sourceSha"],
            "operator seal must match original qualified stage",
        )
        # A physical clone on the original WAL timeline carries the same
        # operator epoch digest. This qualifies *local* SQL authority only,
        # not a global dual-Writer lease or provider exactly-once semantics.
        epoch_digest = hashlib.sha256(
            f"ordivon-pg-writer-epoch-v1\0{'a' * 64}\0{original_system_id}\0{original_timeline}".encode()
        ).hexdigest()
        sql(
            55491,
            "INSERT INTO _stage_control(id,state,source_sha256,promotion_allowed)"
            " VALUES('epoch','QUALIFIED_EPOCH','" + epoch_digest + "',true)",
        )
        before = value(
            55491,
            "SELECT (SELECT count(*) FROM jobs)||'|'||(SELECT count(*) FROM attempts)||'|'||(SELECT count(*) FROM artifacts)",
        )
        require(before == "1|1|1", "seeded schema")
        t_backup = time.monotonic()
        postgres(
            PG + "pg_basebackup",
            "-h",
            str(socket),
            "-p",
            "55491",
            "-U",
            "postgres",
            "-w",
            "-D",
            str(root / "restore"),
            "-Fp",
            "-X",
            "stream",
            "-c",
            "fast",
        )
        postgres(PG + "pg_verifybackup", str(root / "restore"))
        shutil.copytree(root / "restore", root / "pitr")
        shutil.copytree(root / "restore", root / "sibling")
        chown_tree(root / "pitr")
        chown_tree(root / "sibling")
        backup_seconds = time.monotonic() - t_backup
        manifest = root / "restore/backup_manifest"
        original = manifest.read_bytes()
        manifest.write_bytes(original + b"\nTAMPER")
        require(
            postgres(PG + "pg_verifybackup", str(root / "restore"), check=False).returncode != 0,
            "corrupt manifest falsely accepted",
        )
        manifest.write_bytes(original)
        os.chown(manifest, __import__("pwd").getpwnam("postgres").pw_uid, __import__("pwd").getpwnam("postgres").pw_gid)
        postgres(PG + "pg_verifybackup", str(root / "restore"))
        sql(55491, insert("job-pre-target", "request-pre-target", 200))
        sql(55491, "SELECT pg_create_restore_point('ordivon_after_first_extra')")
        sql(55491, insert("job-post-target", "request-post-target", 300))
        # Runtime Release has a specific real effect_id UNIQUE constraint.
        # Persist this after the recovery point so PITR will erase the binding.
        sql(
            55491,
            "INSERT INTO job_runtime_release_effects "
            "(job_id,effect_id,contract,request_digest,workspace_id,"
            "commit_revision,candidate_manifest_digest,expected_tool_count,"
            "receipt_path,binding_digest) VALUES "
            "('job-post-target','effect-r1','release-v1','req-r1',"
            "'ws-lab','sha1','sha256:manifest',0,'/scratch/effect-r1','binding-r1')",
        )
        external_receipt = root / "independent_effect_receipt"
        external_receipt.write_text("effect-after-restore-point\n")
        sql(55491, "SELECT pg_switch_wal()")

        start("restore", 55492)
        start("sibling", 55494)
        for branch_port in (55492, 55494):
            require(
                value(branch_port, "SELECT system_identifier FROM pg_control_system()") == original_system_id,
                "sibling physical clone has a different PG system identifier",
            )
            require(
                int(value(branch_port, "SELECT timeline_id FROM pg_control_checkpoint()")) == original_timeline,
                "sibling clone unexpectedly forked WAL timeline",
            )
            require(
                value(branch_port, "SELECT source_sha256 FROM _stage_control WHERE id='epoch'") == epoch_digest,
                "sibling clone did not inherit identical operator qualification",
            )
        # Two independent databases accept the SAME request and Release
        # effect identities despite their native unique constraints.
        for branch_port, job_id in ((55492, "job-branch-restore"), (55494, "job-branch-sibling")):
            sql(branch_port, insert(job_id, "request-cross-clone", 777, principal="actor-clone"))
            sql(
                branch_port,
                "INSERT INTO job_runtime_release_effects "
                "(job_id,effect_id,contract,request_digest,workspace_id,"
                "commit_revision,candidate_manifest_digest,expected_tool_count,"
                "receipt_path,binding_digest) VALUES "
                f"('{job_id}','effect-cross-clone','release-v1','req-clone',"
                "'ws-lab','sha1','sha256:manifest',0,'/scratch/cloned','binding-clone')",
            )
        for branch_port in (55492, 55494):
            require(
                value(branch_port, "SELECT count(*) FROM jobs WHERE client_request_id='request-cross-clone'") == "1",
                "independent clone rejected same client request identity",
            )
            require(
                value(
                    branch_port, "SELECT count(*) FROM job_runtime_release_effects WHERE effect_id='effect-cross-clone'"
                )
                == "1",
                "independent clone rejected same Release effect identity",
            )
        require(value(55492, "SELECT count(*) FROM jobs") == "2", "base backup leaked post-backup changes")
        require(value(55492, "SELECT count(*) FROM attempts") == "1", "attempt missing")
        require(value(55492, "SELECT count(*) FROM artifacts") == "1", "artifact missing")
        duplicate = sql(55492, insert("duplicate", "request-base", 400), check=False)
        require(duplicate.returncode != 0, "unique request accepted")
        sql(55492, insert("job-crash", "request-crash", 500))
        stop("restore")
        start("restore", 55492)
        require(
            value(55492, "SELECT count(*) FROM jobs WHERE job_id='job-crash'") == "1", "committed crash replay missing"
        )

        # Normal crash restart does not branch WAL timeline.
        require(
            int(value(55492, "SELECT timeline_id FROM pg_control_checkpoint()")) == seal["timelineId"],
            "normal crash-restart should retain exact qualified timeline",
        )

        def race(tag: str) -> bool:
            return sql(55492, insert("race-" + tag, "race-key", 600, principal="race"), check=False).returncode == 0

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(race, ("a", "b")))
        require(outcomes.count(True) == 1, "concurrent requests did not have exactly one winner")
        require(value(55492, "SELECT count(*) FROM jobs WHERE principal='race'") == "1", "race state mismatch")

        (root / "pitr/recovery.signal").touch()
        chown_tree(root / "pitr")
        t_pitr = time.monotonic()
        start("pitr", 55493, pitr=True)
        require(value(55493, "SELECT count(*) FROM jobs WHERE job_id='job-base'") == "1", "PITR base missing")
        require(
            value(55493, "SELECT count(*) FROM jobs WHERE job_id='job-pre-target'") == "1", "WAL before target missing"
        )
        require(
            value(55493, "SELECT count(*) FROM jobs WHERE job_id='job-post-target'") == "0",
            "WAL after target wrongly replayed",
        )
        require(value(55493, "SELECT count(*) FROM jobs") == "2", "PITR cut wrong")

        new_timeline = int(value(55493, "SELECT timeline_id FROM pg_control_checkpoint()"))
        require(
            value(55493, "SELECT system_identifier FROM pg_control_system()") == original_system_id,
            "PITR changed cluster system identifier",
        )
        require(new_timeline != original_timeline, "PITR promotion did not create a new timeline")

        # The persisted operator epoch row itself is restored from the
        # original timeline. The live current-timeline digest differs, so
        # the actual Rust Writer guard must refuse this stale row.
        inherited_epoch = value(55493, "SELECT source_sha256 FROM _stage_control WHERE id='epoch'")
        branch_epoch = hashlib.sha256(
            f"ordivon-pg-writer-epoch-v1\0{'a' * 64}\0{original_system_id}\0{new_timeline}".encode()
        ).hexdigest()
        require(inherited_epoch == epoch_digest, "restored old epoch was unexpectedly replaced")
        require(inherited_epoch != branch_epoch, "PITR old operator epoch would incorrectly qualify new timeline")
        restored_seal = json.loads((root / "operator-qualification-seal.json").read_text())
        require(restored_seal == seal, "independent seal changed across PITR")
        eligible_by_independent_timeline_seal = (
            value(55493, "SELECT system_identifier FROM pg_control_system()") == restored_seal["systemId"]
            and new_timeline == restored_seal["timelineId"]
            and value(55493, "SELECT source_sha256 FROM _stage_control WHERE id='source'") == restored_seal["sourceSha"]
        )
        require(not eligible_by_independent_timeline_seal, "PITR must require operator requalification")
        require(
            value(
                55493, "SELECT state||'|'||source_sha256||'|'||promotion_allowed FROM _stage_control WHERE id='source'"
            )
            == "QUALIFIED_WRITER|" + "a" * 64 + "|true",
            "PITR lost the inherited operator writer qualification",
        )
        require(
            value(55493, "SELECT count(*) FROM job_runtime_release_effects WHERE effect_id='effect-r1'") == "0",
            "PITR should erase the post-target release binding",
        )
        require(
            value(55493, "SELECT promotion_allowed FROM _stage_control WHERE id='lab'") == "f", "stage flag changed"
        )
        require(external_receipt.read_text() == "effect-after-restore-point\n", "external effect receipt missing")
        # Demonstrate the cross-timeline idempotency hazard, not just absence:
        # the restored ledger can now ACCEPT the same client key again while
        # its original external effect receipt still exists outside that DB.
        sql(55493, insert("job-replayed-after-pitr", "request-post-target", 900))
        require(
            value(55493, "SELECT count(*) FROM jobs WHERE client_request_id='request-post-target'") == "1",
            "recovery timeline unexpectedly remembered post-target request",
        )
        require(external_receipt.read_text() == "effect-after-restore-point\n", "effect receipt vanished")
        # The original external receipt is still there but PG's release effect
        # uniqueness does not survive a rollback past its original write.
        sql(
            55493,
            "INSERT INTO job_runtime_release_effects "
            "(job_id,effect_id,contract,request_digest,workspace_id,"
            "commit_revision,candidate_manifest_digest,expected_tool_count,"
            "receipt_path,binding_digest) VALUES "
            "('job-replayed-after-pitr','effect-r1','release-v1','req-r1',"
            "'ws-lab','sha1','sha256:manifest',0,'/scratch/effect-r1','binding-r1')",
        )
        require(
            value(55493, "SELECT count(*) FROM job_runtime_release_effects WHERE effect_id='effect-r1'") == "1",
            "the restored timeline did not admit the original effect identity",
        )
        pitr_seconds = time.monotonic() - t_pitr
        return {
            "status": "PASS",
            "sourceSchemaSha256": SCHEMA_SHA,
            "checks": [
                "manifest_tamper_rejected",
                "base_job_attempt_artifact_readback",
                "unique_request_conflict",
                "crash_wal_replay",
                "concurrent_single_winner",
                "pitr_named_restore_point",
                "post_point_excluded",
                "external_receipt_outlives_restored_job",
                "same_request_readmitted_after_pitr",
                "operator_writer_qualification_revived_after_new_timeline",
                "hypothetical_operator_timeline_seal_rejects_pitr_not_crash",
                "release_effect_id_rebound_after_pitr",
                "lab_stage_flag_unqualified",
                "persisted_old_epoch_rejected_after_pitr_timeline_change",
                "sibling_clones_share_cluster_timeline_and_qualified_epoch",
                "same_request_admitted_on_both_cloned_primaries",
                "same_release_effect_id_bound_on_both_cloned_primaries",
            ],
            "backupAndVerifySeconds": round(backup_seconds, 3),
            "pitrReadbackSeconds": round(pitr_seconds, 3),
            "totalSeconds": round(time.monotonic() - started, 3),
            "originalTimelineId": original_timeline,
            "recoveredTimelineId": new_timeline,
            "clusterSystemIdStable": True,
            "candidateMitigation": "PG timeline-bound Rust source guard merged; installed state UNKNOWN; not globally sufficient",
            "globalWriterExclusion": "NOT_PROVEN: sibling clones share physical ID, timeline, and epoch",
            "externalEffectSemantics": "UNKNOWN; PITR counterexample forbids blind replay",
            "productionRuntimeEffect": "NONE",
            "productionRpoRto": "UNKNOWN",
        }
    finally:
        for name in ("pitr", "sibling", "restore", "primary"):
            try:
                stop(name)
            except Exception:
                pass


def main() -> None:
    if os.geteuid() != 0:
        raise SystemExit("Requires root to initialize postgres-owned *scratch* clusters")
    with tempfile.TemporaryDirectory(prefix="ordivon-pg-pitr-r1-", dir="/var/tmp") as name:
        root = Path(name)
        print(json.dumps(execute(root), sort_keys=True))


if __name__ == "__main__":
    main()
