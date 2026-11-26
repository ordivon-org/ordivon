"""Opt-in seven-point recovery retention contract for the native backup engine.

Run in an isolated Runtime workspace as workstation operator:
ORDIVON_TEST_NATIVE_BACKUP_RETENTION=1 python -m unittest discover -s platform/workstation/tests -p test_pgbackrest_native_retention_contract.py
The compressed schedule is a fixture, not a production retention policy.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from native_pgbackrest_fixture import PrivatePostmasters, run_private

# These are test-only oracles for the observed native CLI contract.
# The fixture's schedule, not the CLI's reported dependency graph, supplies
# the independently expected groups and removal identities.
_LABEL = r"[0-9]{8}-[0-9]{6}F(?:_[0-9]{8}-[0-9]{6}[DI])?"


def require(condition, message):
    # The documented unittest entry also works under Python -O.
    if not condition:
        raise AssertionError(message)


def assert_expiration_plan(report, expected_groups):
    groups = []
    removals = []
    completions = 0
    for line in report.splitlines():
        if "expire full backup set" in line:
            match = re.search(r"INFO: \[DRY-RUN\] repo1: expire full backup set (.+)$", line)
            require(match is not None, "unexpected expiration group report")
            labels = tuple(match[1].split(", "))
            require(all(re.fullmatch(_LABEL, x) for x in labels), "invalid plan label")
            groups.append(labels)
        elif "remove expired backup" in line:
            match = re.search(
                rf"INFO: \[DRY-RUN\] repo1: remove expired backup ({_LABEL})$", line
            )
            require(match is not None, "unexpected removal report")
            removals.append(match[1])
        elif "expire command end:" in line:
            require(re.search(
                r"INFO: \[DRY-RUN\] expire command end: completed successfully \(\d+ms\)$",
                line,
            ) is not None, "invalid dry-run completion")
            completions += 1
    expected = [label for group in expected_groups for label in group]
    require(len(expected) == len(set(expected)), "invalid expected schedule")
    require(sorted(groups) == sorted(expected_groups), "expiration groups differ")
    require(sorted(removals) == sorted(expected), "removal identities/multiplicity differ")
    require(completions == 1, "dry-run completion missing or repeated")


def repository_identity(repo):
    # Native primary is stopped before observation, so no archive writer is
    # expected to change this private repository during either dry run.
    result = {}
    for path in repo.rglob("*"):
        if path.is_file():
            with path.open("rb") as stream:
                result[str(path.relative_to(repo))] = (
                    path.stat().st_size, path.stat().st_mtime_ns,
                    hashlib.file_digest(stream, "sha256").hexdigest(),
                )
    return result


def expected_witness(step):
    # Independent model of the fixture, not another query of the primary.
    return [{"id": i, "body": f"revision-{step}" if i == 1 else f"point-{i}"}
            for i in range(1, step + 1)]


@unittest.skipUnless(os.environ.get("ORDIVON_TEST_NATIVE_BACKUP_RETENTION") == "1",
                     "explicit isolated native PG/pgBackRest retention qualification")
class NativeBackupRetentionContract(unittest.TestCase):
    def test_two_full_generations_retain_seven_exact_recovery_points(self):
        import pwd

        self.assertEqual(os.geteuid(), 0, "explicit native fixture requires operator")
        owner = pwd.getpwnam("postgres")
        root = Path(tempfile.mkdtemp(prefix="ordivon-native-retention-", dir="/var/tmp"))
        data, socket, repo = (root / name for name in ("primary", "socket", "repo"))
        config = root / "pgbackrest.conf"
        port = 55647
        lifecycle = PrivatePostmasters(root)

        def own(path):
            os.chown(path, owner.pw_uid, owner.pw_gid)

        def run(*args, timeout=75):
            result = run_private(*args, check=False, timeout=timeout)
            if result.returncode:
                print("native failure", args[0], result.returncode,
                      result.stdout[-2000:], result.stderr[-2000:], flush=True)
            result.check_returncode()
            return result.stdout

        def br(*args, timeout=75):
            return run("/usr/bin/pgbackrest", f"--config={config}",
                       f"--config-include-path={root / 'conf.d'}", "--stanza=retention",
                       *args, timeout=timeout)

        start, stop = lifecycle.start, lifecycle.stop

        def sql(query, sock=socket, bind_port=port):
            return run("/usr/bin/psql", "-X", "-v", "ON_ERROR_STOP=1",
                       "-h", sock, "-p", bind_port, "-d", "postgres", "-Atqc", query).strip()

        def info():
            return json.loads(br("--output=json", "info"))[0]["backup"]

        def witness(sock=socket, bind_port=port):
            return sql("select json_agg(w order by id)::text from witness w", sock, bind_port)

        def label_set(backups):
            return {item["label"] for item in backups}

        try:
            own(root)
            for path in (socket, repo, root / "logs", root / "locks", root / "spool", root / "conf.d"):
                path.mkdir(mode=0o700)
                own(path)
            config.write_text(
                f"[retention]\npg1-path={data}\npg1-port={port}\npg1-socket-path={socket}\n"
                f"[global]\nrepo1-path={repo}\nlog-path={root / 'logs'}\n"
                f"lock-path={root / 'locks'}\nspool-path={root / 'spool'}\n"
                "repo1-retention-full=2\nrepo1-retention-full-type=count\n"
                "repo1-retention-archive=2\nrepo1-retention-archive-type=full\n"
                "compress-type=zst\nprocess-max=1\nstart-fast=y\n", encoding="utf-8",
            )
            own(config)
            print("fixture", root, flush=True)
            run("/usr/bin/initdb", "-D", data, "--auth-local=peer", "--auth-host=reject",
                "--no-locale", "--wal-segsize=16")
            with (data / "postgresql.conf").open("a", encoding="utf-8") as stream:
                stream.write(
                    f"\narchive_mode=on\narchive_command='/usr/bin/pgbackrest --config={config} "
                    f"--config-include-path={root / 'conf.d'} --stanza=retention archive-push %p'\n"
                    "archive_timeout=5s\nwal_level=replica\n"
                )
            start(data, socket, port)
            br("stanza-create")
            br("check")
            sql("create table witness(id int primary key, body text not null)")
            schedule = ["full", "incr", "full", "diff", "incr", "diff", "incr", "incr", "full"]
            saved = []
            for step, kind in enumerate(schedule, 1):
                sql(f"insert into witness values ({step}, 'point-{step}'); "
                    f"update witness set body='revision-{step}' where id=1")
                expected = expected_witness(step)
                self.assertEqual(json.loads(witness()), expected)
                start_time = time.monotonic()
                # The first new full generation must not implicitly expire recovery roots.
                opts = ["--no-expire-auto"] if step == 9 else []
                br(f"--type={kind}", *opts, "backup")
                current = info()
                entry = current[-1]
                self.assertEqual(entry["type"], kind)
                self.assertNotIn(entry["label"], {item[0] for item in saved})
                saved.append((entry["label"], expected))
                print("backup", step, kind, entry["label"],
                      "delta", entry["info"]["repository"]["delta"],
                      "seconds", round(time.monotonic() - start_time, 3),
                      "retained", len(current), flush=True)
                if step == 8:
                    self.assertEqual(label_set(current), {item[0] for item in saved})

            required = dict(saved[2:])
            before_expire = info()
            self.assertEqual(label_set(before_expire), {item[0] for item in saved})

            # Freeze the private repository by stopping the only archive
            # producer, then compare actual file bytes before/after planning.
            stop(data)
            before_files = repository_identity(repo)
            bad = br("--repo1-retention-full=1", "--repo1-retention-archive=1",
                     "--dry-run", "--log-level-console=info", "expire")
            print("ONE_GENERATION_DRY_RUN", bad, flush=True)
            self.assertEqual(info(), before_expire)
            self.assertEqual(repository_identity(repo), before_files)
            good = br("--repo1-retention-full=2", "--repo1-retention-archive=2",
                      "--dry-run", "--log-level-console=info", "expire")
            print("TWO_GENERATION_DRY_RUN", good, flush=True)
            self.assertEqual(info(), before_expire)
            self.assertEqual(repository_identity(repo), before_files)
            first_group = tuple(label for label, _ in saved[:2])
            second_group = tuple(label for label, _ in saved[2:8])
            assert_expiration_plan(bad, [first_group, second_group])
            assert_expiration_plan(good, [first_group])
            br("--repo1-retention-full=2", "--repo1-retention-archive=2", "expire")
            retained = info()
            self.assertEqual(len(required), 7)
            self.assertEqual(label_set(retained), set(required))
            self.assertEqual(sum(b["type"] == "full" for b in retained), 2)
            for item in retained:
                self.assertTrue(set(item.get("reference") or []).issubset(required))
                if item.get("prior") is not None:
                    self.assertIn(item["prior"], required)
            for label, _ in saved[:2]:
                self.assertFalse((repo / "backup" / "retention" / label).exists())
            print("native expiry closure", sorted(required), flush=True)

            # Exact single-timeline WAL coverage across the retained interval.
            first, last = retained[0]["archive"]["start"], retained[-1]["archive"]["stop"]
            self.assertEqual(first[:8], last[:8])
            self.assertEqual(first[:8], "00000001")
            def ordinal(name):
                self.assertEqual(len(name), 24)
                self.assertLess(int(name[16:], 16), 256)
                return int(name[8:16], 16) * 256 + int(name[16:], 16)
            low, high = ordinal(first), ordinal(last)
            self.assertGreaterEqual(high, low)
            self.assertLess(high - low, 128, "bounded native fixture")
            wal_file = root / "retrieved-wal"
            for seq in range(low, high + 1):
                name = f"{first[:8]}{seq // 256:08X}{seq % 256:08X}"
                self.assertFalse(wal_file.exists())
                br("--no-archive-async", "--archive-missing-retry=n", "--archive-timeout=3",
                   "archive-get", name, wal_file, timeout=12)
                self.assertEqual(wal_file.stat().st_size, 16 * 1024 * 1024)
                wal_file.unlink()
            print("WAL interval", first, last, "segments", high - low + 1, flush=True)

            for i, (label, expected) in enumerate(required.items()):
                dest, restore_socket = root / f"restore-{i}", root / f"restore-sock-{i}"
                restore_socket.mkdir(mode=0o700)
                own(restore_socket)
                begin = time.monotonic()
                br(f"--pg1-path={dest}", f"--set={label}", "--type=immediate",
                   "--target-action=promote", "--archive-mode=off", "--no-link-all",
                   "--reset-link-map", "--reset-tablespace-map", "restore")
                self.assertFalse(any(path.is_symlink() for path in dest.rglob("*")))
                start(dest, restore_socket, port + 1)
                # pg_ctl -w reports connection readiness, not completed recovery.
                deadline = time.monotonic() + 30
                while sql("select not pg_is_in_recovery()", restore_socket, port + 1) != "t":
                    if time.monotonic() >= deadline:
                        self.fail(f"recovery did not promote for {label}")
                    time.sleep(0.25)
                actual = witness(restore_socket, port + 1)
                self.assertEqual(json.loads(actual), expected)
                stop(dest)
                print("RESTORE", label, "seconds", round(time.monotonic() - begin, 3),
                      "digest", hashlib.sha256(actual.encode()).hexdigest(), flush=True)
                shutil.rmtree(dest)
                shutil.rmtree(restore_socket)
            print("SEVEN_RETAINED_POINTS_EXACT", len(required), flush=True)
        finally:
            lifecycle.cleanup()
