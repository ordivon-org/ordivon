"""Isolated PG18 -> PG19 native copy upgrade with exact Host consumer replay.

No live DSN is accepted. Native pg_upgrade owns physical migration; the
synthetic application witness checks only this source/build/locale cut.
The old copy is a pre-cutover rollback, not a post-write recovery mechanism.
"""

from __future__ import annotations

import argparse
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from host_pg19_search_verify import observe_search, reindex_and_verify, seed_search

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.collaboration_inputs import MessageInput, SpaceInput, TopicInput
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.service import HostV2
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput, WorkCreateInput, WorkSnapshotInput
from ordivon_host_v2.work_store import WorkStore

ROOT = Path(__file__).resolve().parents[1]
ACTOR = "actor:pg19:consumer"
PEER = "actor:pg19:peer"
WORK = "work:pg19:synthetic"
SPACE = "space:pg19:synthetic"
TOPIC = "topic:pg19:synthetic"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def run(args: list[str], *, cwd: Path, capture: bool = False, **kwargs: Any) -> str:
    return (
        subprocess.run(
            args, cwd=cwd, check=True, text=True, capture_output=capture, timeout=120, **kwargs
        ).stdout
        or ""
    )


@dataclass(frozen=True)
class Cluster:
    bin: Path
    data: Path
    socket: Path
    port: int
    runner: tuple[str, ...]

    def command(self, name: str, *args: str, capture: bool = False) -> str:
        return run(
            [*self.runner, str(self.bin / name), *args],
            cwd=self.data.parent,
            capture=capture,
        )

    def initialize(self, *, icu: bool = False) -> None:
        locale_args = ("--locale-provider=icu", "--icu-locale=und") if icu else ()
        self.command(
            "initdb",
            "-D",
            str(self.data),
            "-U",
            "ordivon_ci",
            "--locale=C",
            *locale_args,
            "--encoding=UTF8",
            "--auth-local=trust",
            "--auth-host=reject",
            capture=True,
        )

    def start(self) -> None:
        self.command(
            "pg_ctl",
            "-D",
            str(self.data),
            "-l",
            str(self.data.with_suffix(".log")),
            "-o",
            f"-c listen_addresses='' -c unix_socket_directories={self.socket} "
            f"-c port={self.port} -c shared_buffers=64MB",
            "-w",
            "start",
        )

    def stop(self) -> None:
        if (self.data / "postmaster.pid").exists():
            self.command("pg_ctl", "-D", str(self.data), "-m", "fast", "-w", "stop")

    def dsn(self, database: str = "ordivon_ci") -> str:
        return f"postgresql://ordivon_ci@/{database}?host={self.socket}&port={self.port}"

    def verify_major(self, major: int) -> None:
        version = self.command(
            "psql",
            "-X",
            "-Atq",
            self.dsn("postgres"),
            "-c",
            "SHOW server_version_num",
            capture=True,
        ).strip()
        require(
            version.isdecimal() and int(version) // 10000 == major, "unexpected running PG major"
        )
        print(f"native_server_version_num={version}", flush=True)


def create_input() -> WorkCreateInput:
    return WorkCreateInput(
        work_ref=WORK,
        kind="qualification",
        actor_ref=ACTOR,
        initial_snapshot=WorkSnapshotInput(objective="cross-major synthetic", frontier="r1"),
    )


def commit_input() -> WorkSnapshotInput:
    return WorkSnapshotInput(
        objective="cross-major synthetic",
        frontier="r2",
        established=["exact evidence"],
        unresolved=["next independent receiver"],
        reference_refs=["message:pg19:one"],
    )


def message_input(n: str) -> MessageInput:
    return MessageInput(
        message_ref=f"message:pg19:{n}",
        client_request_id=f"pg19:post:{n}",
        space_ref=SPACE,
        topic_ref=TOPIC,
        author_actor_ref=PEER,
        body=f"迁移证据𠀀 {n}",
        recorded_at_ms=1 if n == "one" else 2,
    )


def seed(dsn: str) -> None:
    a, w, s, t = ActorReferenceStore(dsn), WorkStore(dsn), SocialStore(dsn), AttentionStore(dsn)
    for actor in (ACTOR, PEER):
        a.declare_actor(
            ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT), client_request_id=actor
        )
    w.create_work(create_input(), client_request_id="pg19:create")
    w.commit_snapshot(
        WORK,
        expected_revision=1,
        snapshot=commit_input(),
        actor_ref=ACTOR,
        client_request_id="pg19:commit",
    )
    s.create_space(
        SpaceInput(
            space_ref=SPACE, purpose="synthetic upgrade", actor_ref=ACTOR, subject_refs=[WORK]
        ),
        client_request_id="pg19:space",
    )
    s.create_topic(
        TopicInput(topic_ref=TOPIC, space_ref=SPACE, title="cross major", actor_ref=ACTOR),
        client_request_id="pg19:topic",
    )
    t.follow(
        actor_ref=ACTOR, target_kind="topic", target_ref=TOPIC, client_request_id="pg19:follow"
    )
    one = s.post_message(message_input("one"))
    s.ack_topic_cursor(
        actor_ref=ACTOR, topic_ref=TOPIC, cursor=one["sequence"], client_request_id="pg19:topic-ack"
    )
    high = t.delta(ACTOR, after_sequence=0)["snapshotHighSequence"]
    t.ack(ACTOR, cursor=high, client_request_id="pg19:attention-ack")
    s.post_message(message_input("two"))


def observe(dsn: str, *, expected_revision: int = 2) -> dict[str, Any]:
    """Actual source-bound consumers, including replay and independent negative."""
    h, w, s, t = HostV2(dsn), WorkStore(dsn), SocialStore(dsn), AttentionStore(dsn)
    h.initialize()
    before = h.status(detail="history")
    one, two = s.get_message("message:pg19:one"), s.get_message("message:pg19:two")
    cursor = t.get(ACTOR)["afterSequence"]
    result = {
        "current": w.get_work(WORK),
        "historical": w.get_work(WORK, 1),
        "message1": s.get_message(one["messageRef"], expected_digest=one["messageDigest"]),
        "message2": s.get_message(two["messageRef"], expected_digest=two["messageDigest"]),
        "topic": s.resume_topic(TOPIC),
        "search": s.search_messages("迁移证据𠀀", topic_ref=TOPIC),
        "topicCursor": s.get_topic_cursor(actor_ref=ACTOR, topic_ref=TOPIC),
        "reentry": t.reentry(ACTOR, after_sequence=0),
        "createReplay": w.create_work(create_input(), client_request_id="pg19:create"),
        "commitReplay": w.commit_snapshot(
            WORK,
            expected_revision=1,
            snapshot=commit_input(),
            actor_ref=ACTOR,
            client_request_id="pg19:commit",
        ),
        "postReplay": s.post_message(message_input("one")),
        "topicAckReplay": s.ack_topic_cursor(
            actor_ref=ACTOR,
            topic_ref=TOPIC,
            cursor=one["sequence"],
            client_request_id="pg19:topic-ack",
        ),
        "attentionAckReplay": t.ack(ACTOR, cursor=cursor, client_request_id="pg19:attention-ack"),
    }
    try:
        w.commit_snapshot(
            WORK,
            expected_revision=1,
            snapshot=WorkSnapshotInput(objective="different", frontier="bad"),
            actor_ref=ACTOR,
            client_request_id="pg19:commit",
        )
    except ConflictError:
        result["sameKeyChangedInputRejected"] = True
    else:
        raise RuntimeError("same key changed payload accepted")
    after = h.status(detail="history")
    require(before["authority"] == after["authority"], "replay mutated authority")
    require(after["doctor"]["healthy"], "Doctor unhealthy")
    require(result["current"]["revision"] == expected_revision, "original revision changed")
    return {**result, "authority": after["authority"], "doctor": after["doctor"]}


def qualify(old_bin: Path, new_bin: Path, *, icu_search: bool = False) -> None:
    # No caller-supplied DB, no production connection, and no TCP listener.
    require(
        not any(key in os.environ for key in ("ORDIVON_HOST_V2_DSN", "ORDIVON_HOST_V2_TEST_DSN")),
        "inherited Host DSN is forbidden",
    )
    require(os.environ.get("GITHUB_ACTIONS") != "true", "explicit local qualification only")
    for major, bin_dir in ((18, old_bin), (19, new_bin)):
        version = run([str(bin_dir / "postgres"), "--version"], cwd=ROOT, capture=True).strip()
        require(bool(re.search(rf"PostgreSQL\) {major}\.", version)), "unexpected binary PG major")
        print(version, flush=True)

    scratch = Path(tempfile.mkdtemp(prefix="host-pg-major-"))
    socket = scratch / "socket"
    socket.mkdir()
    runner: tuple[str, ...] = ()
    if os.geteuid() == 0:
        account = pwd.getpwnam("postgres")
        os.chown(scratch, account.pw_uid, account.pw_gid)
        os.chown(socket, account.pw_uid, account.pw_gid)
        runner = ("runuser", "-u", "postgres", "--")
    old = Cluster(old_bin, scratch / "old", socket, 55440, runner)
    new = Cluster(new_bin, scratch / "new", socket, 55441, runner)

    try:
        for cluster in (old, new):
            cluster.initialize(icu=icu_search)
        old.start()
        old.verify_major(18)
        old.command(
            "createdb", "-h", str(socket), "-p", str(old.port), "-U", "ordivon_ci", "ordivon_ci"
        )
        run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=ROOT,
            env={**os.environ, "ORDIVON_HOST_V2_DSN": old.dsn()},
        )
        seed(old.dsn())
        if icu_search:
            seed_search(old.dsn(), space=SPACE, topic=TOPIC, actor=PEER)
            original_search = observe_search(old.dsn())
            require(
                original_search["locale"][:4] == ["i", "C", "C", "und"],
                "ICU+C witness locale differs",
            )
        expected = observe(old.dsn())
        digest = canonical_digest(expected)
        print(f"pre_upgrade_digest={digest}", flush=True)
        old.stop()

        upgrade = [
            *runner,
            str(new_bin / "pg_upgrade"),
            f"--old-bindir={old_bin}",
            f"--new-bindir={new_bin}",
            f"--old-datadir={old.data}",
            f"--new-datadir={new.data}",
            "--username=ordivon_ci",
            f"--old-port={old.port}",
            f"--new-port={new.port}",
            f"--socketdir={socket}",
            "--jobs=2",
        ]
        run([*upgrade, "--check"], cwd=scratch)
        run([*upgrade, "--copy"], cwd=scratch)
        new.start()
        new.verify_major(19)
        if icu_search:
            reindex_and_verify(new.dsn(), topic=TOPIC, before=original_search)
        actual = observe(new.dsn())
        require(actual == expected, "upgraded Host consumer/replay mismatch")
        print(f"post_upgrade_digest={canonical_digest(actual)}", flush=True)
        changed = WorkStore(new.dsn()).commit_snapshot(
            WORK,
            expected_revision=2,
            snapshot=WorkSnapshotInput(
                objective="cross-major synthetic", frontier="only PG19 write"
            ),
            actor_ref=ACTOR,
            client_request_id="pg19:new-write",
        )
        require(changed["revision"] == 3, "new-major write missing")
        new.stop()

        old.start()
        old.verify_major(18)
        if icu_search:
            require(observe_search(old.dsn()) == original_search, "old search copy differs")
        restored = observe(old.dsn())
        require(restored == expected, "original PG18 copy differs")
        print(f"old_copy_digest={canonical_digest(restored)}", flush=True)
        print("copy_upgrade_exact=true; new_major_revision=3; old_copy_revision=2")
    finally:
        # Never remove an active data directory. Preserve private evidence if stopping fails.
        try:
            old.stop()
            new.stop()
        except OSError, subprocess.SubprocessError:
            print(f"PRIVATE_CLUSTER_CLEANUP_REQUIRED={scratch}", file=sys.stderr)
            raise
        shutil.rmtree(scratch)
        print("private_clusters_removed=true", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-bin", type=Path, required=True)
    parser.add_argument("--new-bin", type=Path, required=True)
    parser.add_argument(
        "--icu-search",
        action="store_true",
        help="Exercise ICU+C copied FTS index negative and native REINDEX",
    )
    args = parser.parse_args()
    qualify(
        args.old_bin.resolve(strict=True),
        args.new_bin.resolve(strict=True),
        icu_search=args.icu_search,
    )


if __name__ == "__main__":
    main()
