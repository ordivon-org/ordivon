"""Private PG19/pgBackRest PITR qualification with exact Host consumer cuts.

The repository, WAL archive, database, sockets and restore targets are local
temporary synthetic fixtures. A later valid recovery point is a negative
control: successful database recovery alone is not correct consumer recovery.
"""

from __future__ import annotations

import argparse
import os
import pwd
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import psycopg
from host_pg19_upgrade_verify import (
    ACTOR,
    ROOT,
    WORK,
    Cluster,
    message_input,
    observe,
    require,
    run,
    seed,
)

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import WorkSnapshotInput
from ordivon_host_v2.work_store import WorkStore


def snapshot(revision: int) -> WorkSnapshotInput:
    return WorkSnapshotInput(
        objective="cross-major synthetic",
        frontier=f"PG19 post-backup revision {revision}",
        reference_refs=[f"message:pg19:{'three' if revision == 3 else 'four'}"],
    )


def apply(dsn: str, revision: int) -> None:
    result = WorkStore(dsn).commit_snapshot(
        WORK,
        expected_revision=revision - 1,
        snapshot=snapshot(revision),
        actor_ref=ACTOR,
        client_request_id=f"pitr:commit:{revision}",
    )
    require(result["revision"] == revision, "wrong new revision")
    SocialStore(dsn).post_message(message_input("three" if revision == 3 else "four"))


def consumer_cut(dsn: str, revision: int) -> dict[str, Any]:
    before = observe(dsn, expected_revision=revision)
    work = WorkStore(dsn)
    replay = work.commit_snapshot(
        WORK,
        expected_revision=revision - 1,
        snapshot=snapshot(revision),
        actor_ref=ACTOR,
        client_request_id=f"pitr:commit:{revision}",
    )
    require(replay["admission"] == "existing", "PITR replay was a new commit")
    require(replay["revision"] == revision, "PITR replay revision changed")
    require(WorkStore(dsn).get_work(WORK) == before["current"], "replay changed current Work")
    before["newCommitReplay"] = replay
    return before


def observe_point(dsn: str, name: str) -> str:
    with psycopg.connect(dsn, autocommit=True) as conn:
        lsn = conn.execute("SELECT pg_create_restore_point(%s)", (name,)).fetchone()[0]
        conn.execute("SELECT pg_switch_wal()")
    print(f"restore_point={name} lsn={lsn}", flush=True)
    return str(lsn)


def qualify(pg_bin: Path, backrest: Path) -> None:
    require(
        not any(k in os.environ for k in ("ORDIVON_HOST_V2_DSN", "ORDIVON_HOST_V2_TEST_DSN")),
        "inherited Host DSN is forbidden",
    )
    require(os.environ.get("GITHUB_ACTIONS") != "true", "explicit local qualification only")
    # Eliminate ambient database/repository selection before launching any tool.
    for key in tuple(os.environ):
        if key.startswith(("PG", "PGBACKREST_")):
            os.environ.pop(key)
    print(run([str(backrest), "version"], cwd=ROOT, capture=True).strip(), flush=True)
    scratch = Path(tempfile.mkdtemp(prefix="host-pg19-pitr-"))
    for name in ("socket", "repo", "log", "lock", "spool", "include"):
        (scratch / name).mkdir()
    runner: tuple[str, ...] = ()
    if os.geteuid() == 0:
        account = pwd.getpwnam("postgres")
        for path in (scratch, *scratch.iterdir()):
            os.chown(path, account.pw_uid, account.pw_gid)
        runner = ("runuser", "-u", "postgres", "--")
    primary = Cluster(pg_bin, scratch / "primary", scratch / "socket", 55442, runner)
    restored = Cluster(pg_bin, scratch / "restored", scratch / "socket", 55443, runner)
    later = Cluster(pg_bin, scratch / "later", scratch / "socket", 55444, runner)
    config = scratch / "pgbackrest.conf"
    config.write_text(
        f"[global]\nrepo1-path={scratch / 'repo'}\nrepo1-retention-full=2\n"
        f"log-path={scratch / 'log'}\nlock-path={scratch / 'lock'}\nspool-path={scratch / 'spool'}\n"
        "log-level-console=info\nprocess-max=2\nstart-fast=y\narchive-timeout=30\n"
        f"[host-r11]\npg1-path={primary.data}\npg1-port={primary.port}\n"
        f"pg1-socket-path={primary.socket}\npg1-user=ordivon_ci\n"
    )
    cli = [
        str(backrest),
        f"--config={config}",
        f"--config-include-path={scratch / 'include'}",
        "--stanza=host-r11",
    ]

    def br(*args: str) -> str:
        return run([*runner, *cli, *args], cwd=scratch)

    def restore(cluster: Cluster, target: str) -> None:
        br(
            f"--pg1-path={cluster.data}",
            "--type=name",
            f"--target={target}",
            "--target-action=promote",
            "--target-timeline=1",
            "--archive-mode=off",
            "restore",
        )
        cluster.start()
        cluster.verify_major(19)
        # pg_ctl readiness can mean read-only hot standby, not promotion.
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            with psycopg.connect(cluster.dsn(), autocommit=True) as conn:
                if not conn.execute("SELECT pg_is_in_recovery()").fetchone()[0]:
                    return
            time.sleep(0.1)
        print(cluster.data.with_suffix(".log").read_text()[-4000:], file=sys.stderr)
        raise RuntimeError("restore did not reach the target and promote")

    try:
        primary.initialize()
        # Native WAL archive, unique temporary repository; no global pgBackRest config.
        with (primary.data / "postgresql.conf").open("a") as f:
            f.write(
                "\narchive_mode=on\nwal_level=replica\n"
                "archive_command='" + " ".join(cli) + " archive-push %p'\n"
            )
        primary.start()
        primary.verify_major(19)
        primary.command(
            "createdb",
            "-h",
            str(primary.socket),
            "-p",
            str(primary.port),
            "-U",
            "ordivon_ci",
            "ordivon_ci",
        )
        run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=ROOT,
            env={**os.environ, "ORDIVON_HOST_V2_DSN": primary.dsn()},
        )
        seed(primary.dsn())
        observe(primary.dsn())
        br("stanza-create")
        br("check")
        br("--type=full", "backup")
        apply(primary.dsn(), 3)
        expected = consumer_cut(primary.dsn(), 3)
        observe_point(primary.dsn(), "host_verified")
        apply(primary.dsn(), 4)
        expected_later = consumer_cut(primary.dsn(), 4)
        observe_point(primary.dsn(), "host_later")
        br("check")
        primary.stop()

        restore(restored, "host_verified")
        actual = consumer_cut(restored.dsn(), 3)
        require(actual == expected, "target consumer cut differs")
        try:
            WorkStore(restored.dsn()).get_work(WORK, 4)
        except ConflictError:
            pass
        else:
            raise RuntimeError("future revision leaked into earlier recovery point")
        print(f"target_consumer_digest={canonical_digest(actual)}", flush=True)
        restored.stop()

        restore(later, "host_later")
        actual_later = consumer_cut(later.dsn(), 4)
        require(actual_later == expected_later, "later recovery cut differs")
        require(actual_later != expected, "wrong-target negative not detected")
        print(f"later_consumer_digest={canonical_digest(actual_later)}", flush=True)
        print(
            "pitr_exact=true; post_backup_revision=3; future_revision_excluded=true; "
            "wrong_target_negative=true",
            flush=True,
        )
    finally:
        try:
            for cluster in (primary, restored, later):
                cluster.stop()
        except OSError, subprocess.SubprocessError:
            print(f"PRIVATE_CLUSTER_CLEANUP_REQUIRED={scratch}", file=sys.stderr)
            raise
        shutil.rmtree(scratch)
        print("private_pitr_repository_removed=true", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", type=Path, required=True)
    parser.add_argument("--pgbackrest", type=Path, required=True)
    args = parser.parse_args()
    qualify(args.pg_bin.resolve(strict=True), args.pgbackrest.resolve(strict=True))
