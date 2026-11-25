"""Opt-in native contract for the existing pgBackRest recovery substrate.

Run as the workstation operator in an isolated Runtime workspace:
ORDIVON_TEST_NATIVE_BACKUP_CHAIN=1 python -m unittest discover -s platform/workstation/tests -p test_pgbackrest_native_recovery_contract.py
This fixture never uses production config, PGDATA, sockets or repository.
"""
from __future__ import annotations

import json
import os
import pwd
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(os.environ.get("ORDIVON_TEST_NATIVE_BACKUP_CHAIN") == "1",
                     "explicit isolated native PG/pgBackRest qualification")
class NativeBackupRecoveryContract(unittest.TestCase):
    def test_exact_backup_status_and_required_wal_are_separate_predicates(self):
        self.assertEqual(os.geteuid(), 0, "explicit native fixture requires operator")
        owner = pwd.getpwnam("postgres")
        root = Path(tempfile.mkdtemp(prefix="ordivon-native-chain-", dir="/var/tmp"))
        data, socket, repo = (root / name for name in ("primary", "socket", "repo"))
        config = root / "pgbackrest.conf"
        port = 55645
        started = False

        def own(path):
            os.chown(path, owner.pw_uid, owner.pw_gid)

        def run(*args, check=True, timeout=70):
            return subprocess.run(
                ["sudo", "-u", "postgres", *map(str, args)], capture_output=True,
                text=True, check=check, timeout=timeout,
            )

        def br(*args, check=True, timeout=70):
            return run("/usr/bin/pgbackrest", f"--config={config}",
                       f"--config-include-path={root / 'conf.d'}", "--stanza=chain",
                       *args, check=check, timeout=timeout)

        def sql(query):
            return run("/usr/bin/psql", "-X", "-v", "ON_ERROR_STOP=1",
                       "-h", socket, "-p", port, "-d", "postgres", "-Atqc", query).stdout.strip()

        def backup(kind):
            br(f"--type={kind}", "backup")
            return json.loads(br("--output=json", "info").stdout)[0]["backup"][-1]

        def verify(label):
            result = br(f"--set={label}", "--output=text", "--verbose",
                        "--io-timeout=2", "verify", check=False, timeout=30)
            print("verify", result.returncode, result.stdout[-3500:], result.stderr[-500:])
            match = re.findall(
                rf"^\s*backup: {re.escape(label)}, status: valid, total files checked: (\d+), "
                r"total valid files: (\d+)\s*$", result.stdout, re.MULTILINE,
            )
            qualified = result.returncode == 0 and len(match) == 1 and (
                int(match[0][0]) > 0 and match[0][0] == match[0][1]
            ) and "status: error" not in result.stdout
            return qualified, result.stdout

        def get_wal(segment, name):
            destination = root / name
            self.assertFalse(destination.exists())
            result = br("--no-archive-async", "--archive-missing-retry=n",
                        "--archive-timeout=3", "archive-get", segment,
                        destination, check=False, timeout=12)
            print("archive-get", name, result.returncode, destination.exists())
            return result.returncode, destination

        try:
            own(root)
            for path in (socket, repo, root / "logs", root / "locks", root / "spool", root / "conf.d"):
                path.mkdir(mode=0o700)
                own(path)
            config.write_text(
                f"[chain]\npg1-path={data}\npg1-port={port}\npg1-socket-path={socket}\n"
                f"[global]\nrepo1-path={repo}\nlog-path={root / 'logs'}\n"
                f"lock-path={root / 'locks'}\nspool-path={root / 'spool'}\n"
                "repo1-retention-full=2\nrepo1-retention-diff=14\n"
                "repo1-retention-archive=2\nrepo1-retention-archive-type=full\n"
                "compress-type=zst\nprocess-max=1\nstart-fast=y\n",
                encoding="utf-8",
            )
            own(config)
            run("/usr/bin/initdb", "-D", data, "--auth-local=peer", "--auth-host=reject", "--no-locale")
            with (data / "postgresql.conf").open("a", encoding="utf-8") as stream:
                stream.write(
                    f"\narchive_mode=on\narchive_command='/usr/bin/pgbackrest --config={config} "
                    f"--config-include-path={root / 'conf.d'} --stanza=chain archive-push %p'\n"
                    "archive_timeout=5s\nwal_level=replica\n"
                )
            started = True
            run("/usr/bin/pg_ctl", "-D", data, "-l", root / "postgres.log",
                "-o", f"-c listen_addresses='' -c unix_socket_directories={socket} -p {port}",
                "-w", "-t", "30", "start")
            br("stanza-create")
            br("check")
            sql("create table witness(id int primary key, body text); insert into witness values(1,'base');")
            base = backup("full")
            sql("insert into witness values(2,'increment');")
            increment = backup("incr")
            self.assertIn(base["label"], increment["reference"])
            run("/usr/bin/pg_ctl", "-D", data, "-m", "fast", "-w", "stop")
            started = False

            label = increment["label"]
            segment = increment["archive"]["start"]
            self.assertEqual(segment, increment["archive"]["stop"], "fixture covers one required segment")
            self.assertTrue(verify(label)[0])
            rc, retrieved = get_wal(segment, "positive-wal")
            self.assertEqual(rc, 0)
            self.assertGreater(retrieved.stat().st_size, 0)

            parent = repo / "backup" / "chain" / base["label"]
            held = root / "held-base"
            parent.rename(held)
            try:
                qualified, report = verify(label)
                self.assertFalse(qualified, "process exit is not backup qualification")
                self.assertIn(f"backup: {label}, status: invalid", report)
                self.assertRegex(report, r"missing: [1-9][0-9]*")
            finally:
                held.rename(parent)

            files = list((repo / "archive" / "chain").rglob(segment + "-*"))
            self.assertEqual(len(files), 1)
            wal = files[0]
            self.assertTrue(wal.is_file() and not wal.is_symlink())
            held_wal = root / "held-wal"
            wal.rename(held_wal)
            try:
                rc, missing = get_wal(segment, "negative-wal")
                self.assertEqual(rc, 1, "native archive-get missing result")
                self.assertFalse(missing.exists())
            finally:
                held_wal.rename(wal)
            self.assertTrue(verify(label)[0])
            rc, recovered = get_wal(segment, "recovered-wal")
            self.assertEqual(rc, 0)
            self.assertEqual(retrieved.read_bytes(), recovered.read_bytes())
        finally:
            if started or (data / "postmaster.pid").exists():
                stop = run("/usr/bin/pg_ctl", "-D", data, "-m", "fast", "-w", "stop", check=False)
                if stop.returncode or (data / "postmaster.pid").exists():
                    raise RuntimeError(f"private postmaster stop unqualified; retaining {root}")
            shutil.rmtree(root)
            print("private fixture removed", not root.exists())
