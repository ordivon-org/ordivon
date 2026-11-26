"""Native disposable PG release-operator tests (never touch production)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import psycopg

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
try:
    import ordivon_runtime_pg_operator as op
finally:
    sys.path.remove(str(SCRIPTS))


def binary(name: str) -> str:
    from shutil import which
    found = which(name)
    if not found:
        raise unittest.SkipTest(f"{name} not installed")
    return found


def unprivileged():
    if os.geteuid() == 0:
        os.setgid(65534)
        os.setuid(65534)


class OperatorBinaryProfileGuards(unittest.TestCase):
    def test_direct_entrypoints_reject_incomplete_native_profile_before_pg(self) -> None:
        invalid = (
            ["ordivon-runtime-pg"],
            ["ordivon-runtime-runner"],
            ["ordivon-runtime-pg", "ordivon-runtime-pg"],
            ["ordivon-runtime-pg", "ordivon-runtime-runner", "ordivon-runtime-runner"],
            ["ordivon-runtime-pg", "ordivon-runtime-runner", "/usr/bin/sh"],
            [],
            None,
            "ordivon-runtime-pg",
        )
        for binaries in invalid:
            with self.subTest(binaries=binaries):
                args = Namespace(
                    binaries=binaries,
                    install_dir=Path("/var/tmp/no-real-release"),
                    action="inspect",
                )
                with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                    op.expected_runner_path(args)
                with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                    op.apply_release(args)
                with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                    op.physical_preflight(args, {})
                with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                    op.pg_mcp_readiness(args)
                with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                    op.finalize_receipted_release(None, args, {})
                with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                    op.verified_release_consumer(args, {})
                with patch.object(op, "arguments", return_value=args), \
                     patch.object(op, "pg_connection") as pg_connection:
                    with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                        op.main()
                    pg_connection.assert_not_called()

    def test_direct_profile_accepts_both_required_native_consumers(self) -> None:
        args = Namespace(
            binaries=["ordivon-runtime-runner", "ordivon-runtime-pg"],
            install_dir=Path("/var/tmp/no-real-release"),
        )
        self.assertEqual(
            op.expected_runner_path(args),
            args.install_dir / "ordivon-runtime-runner",
        )

    def test_backend_neutral_restore_prefers_explicit_pg_probe(self) -> None:
        # PG-only service environment has no legacy ORDIVON_BIND. Reusing
        # generic restore_previous must NOT invoke the SQLite probe.
        with tempfile.TemporaryDirectory(prefix="pg-rollback-probe-") as root:
            directory = Path(root)
            previous = directory / "previous"
            installed = directory / "installed"
            previous.mkdir()
            installed.mkdir()
            (previous / "ordivon-runtime-pg").write_bytes(b"previous-native-pg")
            (installed / "ordivon-runtime-pg").write_bytes(b"new-native-pg")
            env = directory / "pg.env"
            env.write_text("ORDIVON_PG_BIND=127.0.0.1:65501\n")
            original = op.DEPLOY["restore_previous"]
            command_calls: list[tuple[str, ...]] = []
            probe_calls: list[str] = []

            def physical(command, **_kwargs):
                command_calls.append(tuple(str(part) for part in command))
                return None

            def native_probe(slice_seconds):
                self.assertGreater(slice_seconds, 0)
                probe_calls.append("pg")
                self.assertEqual(
                    (installed / "ordivon-runtime-pg").read_bytes(),
                    b"previous-native-pg",
                )
                if len(probe_calls) == 1:
                    raise RuntimeError("PG listener not ready yet")
                return {"toolCount": 21, "nativePg": True}

            # Reuse the ORIGINAL bounded wait, but invoke the PG-native
            # callback instead of legacy ORDIVON_BIND/SQLite inspection.
            ready = op.DEPLOY["wait_for_service_mcp_ready"]
            with patch.dict(original.__globals__, {"run": physical}), patch.dict(
                ready.__globals__, {
                    "service_active": lambda *_a: True,
                    "wait_service_active": lambda *_a: None,
                    "probe_mcp": lambda *_a, **_kw: self.fail(
                        "PG rollback must not invoke SQLite ORDIVON_BIND probe"
                    ),
                },
            ):
                result = original(
                    previous,
                    installed,
                    [{"name": "ordivon-runtime-pg", "mode": 0o755}],
                    Path("/usr/bin/true"),
                    "ordivon-runtime.service",
                    env,
                    1.0,
                    readiness_probe=native_probe,
                )
                self.assertEqual(
                    [cmd[1] for cmd in command_calls], ["stop", "start"]
                )
                self.assertEqual(probe_calls, ["pg", "pg"])
                self.assertEqual(result["probe"]["toolCount"], 21)
                with self.assertRaisesRegex(
                    RuntimeError, "no qualified evidence"
                ):
                    original(
                        previous,
                        installed,
                        [{"name": "ordivon-runtime-pg", "mode": 0o755}],
                        Path("/usr/bin/true"),
                        "ordivon-runtime.service",
                        env,
                        1.0,
                        readiness_probe=lambda _slice: {},
                    )

    def test_restored_pg_catalog_accepts_prior_count_but_checks_runner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pg-catalog-") as root:
            installed = Path(root)
            runner = installed / "ordivon-runtime-runner"
            runner.write_bytes(b"previous-runner")
            provider_digest = op.DEPLOY["sha256"](runner)
            calls = []

            def catalog(_url, _token, **kwargs):
                calls.append(kwargs)
                return {"toolCount": 21, "toolCatalogDigest": "sha256:" + "a" * 64}

            class NativeMcp:
                def __init__(self, *_a, **_kw):
                    pass

                def call_tool(self, name, _arguments):
                    if name != "runtime.describe":
                        raise AssertionError(name)
                    return {"targets": [{
                        "target": "local_linux",
                        "executionProvider": {
                            "contract": "local_linux_runner_v1",
                            "executableDigest": provider_digest,
                        },
                    }]}

            args = Namespace(
                binaries=["ordivon-runtime-pg", "ordivon-runtime-runner"],
                install_dir=installed,
                env_file=installed / "pg.env",
                systemctl=Path("/usr/bin/true"),
                service="ordivon-runtime.service",
                expected_tool_count=24,
                required_tools=["job.exec"],
                wait_seconds=1.0,
            )
            with patch.dict(op.DEPLOY, {
                "load_environment_file": lambda _p: {
                    "ORDIVON_PG_BIND": "127.0.0.1:65501",
                    "ORDIVON_PG_TOKEN": "x" * 32,
                },
                "service_active": lambda *_a: True,
                "probe_catalog": catalog,
            }), patch.object(op, "McpClient", NativeMcp), patch.object(
                op, "verified_live_service_executable",
                return_value={"path": str(installed / "ordivon-runtime-pg")},
            ):
                previous = op.pg_mcp_readiness(args, previous_image=True)
                self.assertEqual(previous["toolCount"], 21)
                self.assertEqual(
                    previous["activeRuntimeImage"]["runnerDigest"],
                    provider_digest,
                )
                self.assertIsNone(calls[-1]["expected_tool_count"])
                self.assertEqual(calls[-1]["required_tools"], ())
                bounded = op.pg_mcp_readiness(
                    args, previous_image=True, probe_wait_seconds=0.4
                )
                self.assertEqual(bounded["toolCount"], 21)
                self.assertEqual(calls[-1]["wait_seconds"], 0.4)
                current = op.pg_mcp_readiness(args)
                self.assertEqual(current["toolCount"], 21)
                self.assertEqual(calls[-1]["expected_tool_count"], 24)
                self.assertEqual(calls[-1]["required_tools"], ("job.exec",))


class NativePgReleaseOperator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(tempfile.mkdtemp(prefix="pg-operator-native-",dir="/var/tmp"))
        cls.root.chmod(0o777)
        cls.source_sha = "a" * 64
        env = dict(os.environ)
        env["HOME"] = str(cls.root)
        init = subprocess.run([
            binary("initdb"),"-A","trust","-U","postgres","--no-locale",
            "--encoding=UTF8","-D",str(cls.root / "data"),
        ],preexec_fn=unprivileged if os.geteuid()==0 else None,
        env=env,capture_output=True,text=True)
        if init.returncode != 0:
            raise RuntimeError("initdb failed: "+init.stderr)
        log = (cls.root/"postgres.log").open("wb")
        cls.postgres = subprocess.Popen([
            binary("postgres"),"-D",str(cls.root/"data"),
            "-k",str(cls.root),"-h","","-p","5432","-c","fsync=off",
        ],preexec_fn=unprivileged if os.geteuid()==0 else None,
        stdout=log,stderr=log,env=env)
        cls.log=log
        cls.dsn=f"host={cls.root} user=postgres dbname=postgres"
        for i in range(150):
            try:
                cls.db=op.pg_connection(cls.dsn,"fresh")
                break
            except Exception:
                # Before CREATE SCHEMA fresh, use bare PG connection.
                try:
                    cls.db=psycopg.connect(cls.dsn,autocommit=True)
                    cls.db.execute("CREATE SCHEMA fresh")
                    cls.db.close()
                except Exception:
                    pass
                time.sleep(.06)
        else:
            raise RuntimeError("disposable postgres did not start")
        cls.db.execute(
            (SCRIPTS.parent / "crates" /
             "ordivon-runtime-core/sql/pg_fresh_epoch.sql").read_text()
        )
        physical = cls.db.execute(
            "SELECT (SELECT system_identifier::text FROM pg_control_system()) AS system_id,"
            " (SELECT timeline_id FROM pg_control_checkpoint()) AS timeline"
        ).fetchone()
        cls.epoch = hashlib.sha256(
            ("ordivon-pg-writer-epoch-v1\0" + cls.source_sha + "\0" +
             physical["system_id"] + "\0" + str(physical["timeline"])).encode()
        ).hexdigest()
        cls.db.execute(
            "INSERT INTO _stage_control(id,state,source_sha256,promotion_allowed) "
            "VALUES('source','QUALIFIED_WRITER',%s,true),"
            "('release','QUALIFIED_RELEASE',%s,true),"
            "('epoch','QUALIFIED_EPOCH',%s,true)",
            (cls.source_sha,cls.source_sha,cls.epoch),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if getattr(cls,"db",None):
            cls.db.close()
        if getattr(cls,"postgres",None):
            cls.postgres.terminate()
            cls.postgres.wait(timeout=12)
        if getattr(cls,"log",None):
            cls.log.close()
        import shutil
        if getattr(cls,"root",None):
            shutil.rmtree(cls.root,ignore_errors=True)

    def setUp(self) -> None:
        self.work=Path(tempfile.mkdtemp(prefix="effect-",dir=self.root))
        self.repo=self.work/"source"
        self.repo.mkdir()
        subprocess.run([binary("git"),"init",str(self.repo)],check=True,
                       capture_output=True)
        subprocess.run([binary("git"),"-C",str(self.repo),"-c",
                        "user.name=Operator Test","-c",
                        "user.email=operator@test.invalid","commit","--allow-empty",
                        "-m","init"],check=True,capture_output=True)
        commit=subprocess.check_output([binary("git"),"-C",str(self.repo),
                                        "rev-parse","HEAD"],text=True).strip()
        self.candidate=self.work/"release"
        self.candidate.mkdir()
        self.install=self.work/"installed"
        self.install.mkdir()
        (self.candidate/"ordivon-runtime-pg").write_bytes(b"new-pg-runtime")
        (self.install/"ordivon-runtime-pg").write_bytes(b"old-pg-runtime")
        (self.candidate/"ordivon-runtime-runner").write_bytes(b"new-runner")
        (self.install/"ordivon-runtime-runner").write_bytes(b"old-runner")
        qualified_helper = self._testMethodName in {
            "test_pg_reclaimer_helper_installs_with_native_pair_and_receipt",
            "test_pg_reclaimer_helper_rolls_back_with_native_pair",
            "test_pg_reclaimer_helper_candidate_digest_fails_before_dispatch",
            "test_actual_systemd_pg_binary_replacement_and_http_mcp_readback",
        }
        if qualified_helper:
            (self.candidate/"ordivon-runtime-pg-reclaim").write_bytes(
                b"new-qualified-pg-reclaimer"
            )
            (self.install/"ordivon-runtime-pg-reclaim").write_bytes(
                b"old-qualified-pg-reclaimer"
            )
        installed_names = ("ordivon-runtime-pg", "ordivon-runtime-runner")
        if qualified_helper:
            installed_names += ("ordivon-runtime-pg-reclaim",)
        for name in installed_names:
            (self.candidate/name).chmod(0o755)
            (self.install/name).chmod(0o755)
        self.manifest=self.work/"candidate.json"
        self.env_file=self.work/"runtime.env"
        self.env_file.write_text("ORDIVON_PG_BIND=127.0.0.1:65500\n")
        artifacts=[
            op.DEPLOY["artifact_description"](
                self.candidate/name,
                {"name":name,"kind":"binary","mode":0o755},
            )
            for name in ("ordivon-runtime-pg", "ordivon-runtime-runner")
        ]
        if qualified_helper:
            artifacts.append(
                op.DEPLOY["artifact_description"](
                    self.candidate/"ordivon-runtime-pg-reclaim",
                    {"name": "ordivon-runtime-pg-reclaim",
                     "kind": "operator", "mode": 0o755},
                )
            )
        tool={"version":"test","resolvedPath":"/usr/bin/true",
              "digest":"sha256:"+"b"*64}
        candidate_json={
            "schemaVersion":2,
            "commit":commit,
            "sourceRepo":str(self.repo.resolve()),
            "sourceOwnerPrefix":"",
            "sourceMaterialization":"detached_git_checkout",
            "candidateDir":str(self.candidate.resolve()),
            "builtAtMs":1234,
            "toolchain":{"cargo":tool,"rustc":tool,"host":"x86_64-unknown-linux-gnu"},
            "artifacts":artifacts,
            "binaries":[item for item in artifacts if item["kind"] == "binary"],
        }
        self.manifest.write_text(json.dumps(candidate_json),encoding="utf-8")
        request_id="native-operator-"+uuid.uuid4().hex[:20]
        principal="pg-operator-test"
        effect=hashlib.sha256(
            ("runtime-release-effect-v1\0"+principal+"\0"+request_id).encode()
        ).hexdigest()
        manifest_digest=op.DEPLOY["sha256"](self.manifest)
        self.args=Namespace(
            pg_dsn=self.dsn,pg_schema="fresh",
            source_sha256=self.source_sha,principal=principal,
            client_request_id=request_id,effect_id=effect,
            commit=commit,confirm_commit=commit,
            candidate_manifest_digest=manifest_digest,expected_tool_count=20,
            source_repo=self.repo,candidate_dir=self.candidate,
            candidate_manifest=self.manifest,install_dir=self.install,
            receipt_root=self.work/"receipts",env_file=self.env_file,
            service="ordivon-test-runtime.service",
            allowed_services=["ordivon-test-runtime.service"],
            required_tools=["runtime.describe","release.get"],
            binaries=["ordivon-runtime-pg","ordivon-runtime-runner"],
            include_pg_reclaimer=qualified_helper,
            require_ref="HEAD",
            drain_seconds=3.,wait_seconds=2.,
            lock_file=self.work/"operator.lock",
            systemctl=Path("/usr/bin/systemctl"),git=Path(binary("git")),
        )
        self.args.receipt_root.mkdir()
        if self._testMethodName != (
            "test_actual_systemd_pg_binary_replacement_and_http_mcp_readback"
        ):
            # Most unit tests substitute systemd mutations; only the dedicated
            # native acceptance test exercises the *real* effective ExecStart.
            service=patch.object(op,"qualified_service_executable_path",
                                 return_value=self.install/"ordivon-runtime-pg")
            service.start()
            self.addCleanup(service.stop)
            runner_binding=patch.object(op,"qualified_runner_binding")
            runner_binding.start()
            self.addCleanup(runner_binding.stop)
        # Production approval comes from privileged operator environment, not
        # caller-controlled CLI arguments. Test-scoped patch is fully restored.
        approved=patch.dict(os.environ, {
            "ORDIVON_PG_RELEASE_ALLOWED_SERVICES_JSON":
                json.dumps([self.args.service])
        })
        approved.start()
        self.addCleanup(approved.stop)
        identity={
            "schemaVersion":1,"principal":principal,
            "workspaceId":"ws-test-release",
            "commit":commit,"candidateManifestDigest":manifest_digest,
            "expectedToolCount":20,
        }
        request_digest="runtime-release-v1:"+op.digest(op.canonical_json(identity).encode())
        receipt=str(self.args.receipt_root / f"effect-{effect}")
        binding={
            "contract":"runtime_release_v1","effectId":effect,
            "requestDigest":request_digest,"workspaceId":"ws-test-release",
            "commit":commit,"candidateManifestDigest":manifest_digest,
            "expectedToolCount":20,"receiptPath":receipt,
        }
        binding_digest=op.digest(op.canonical_json(binding).encode())
        self.job_id="job-test-"+uuid.uuid4().hex
        self.attempt_id="attempt-test-"+uuid.uuid4().hex
        plan=op.canonical_json({
            "schemaVersion":1,
            "workspaceId":"ws-test-release",
            "workspacePath":str(self.work),
            "sourceRevision":commit,
            "executable":"/usr/bin/true",
            "executableDigest":"sha256:"+"f"*64,
            "cwd":str(self.work),
            "timeoutMs":5000,
            "stdoutLimitBytes":4096,
            "stderrLimitBytes":4096,
            "principal":principal,
        })
        with self.db.transaction():
            self.db.execute(
                "INSERT INTO jobs(job_id,principal,client_request_id,request_digest,"
                "operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,"
                "execution_plan_digest,created_at_ms,desired_state,current_attempt_id)"
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,123,'run',%s)",
                (self.job_id,principal,request_id,request_digest,
                 "sha256:"+"c"*64,"ws-test-release",
                 json.dumps({"runtimeReleaseEffectDigest":binding_digest}),
                 plan,op.digest(plan.encode()),self.attempt_id),
            )
            self.db.execute(
                "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,"
                "termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms)"
                "VALUES(%s,%s,1,'accepted','natural',%s,%s,%s,123)",
                (self.attempt_id,self.job_id,"sha256:"+"d"*64,
                 str(self.work/"pg-store"/"pg-attempts"/self.attempt_id),
                 "operator-test-"+uuid.uuid4().hex+".service"),
            )
            self.db.execute(
                "INSERT INTO concurrency_reservations(reservation_id,attempt_id,"
                "global_limit,state,acquired_at_ms,state_observed_at_ms)"
                "VALUES(%s,%s,1,'active',123,123)",
                ("reservation-"+uuid.uuid4().hex,self.attempt_id),
            )
            self.db.execute(
                "INSERT INTO job_runtime_release_effects(job_id,effect_id,contract,"
                "request_digest,workspace_id,commit_revision,candidate_manifest_digest,"
                "expected_tool_count,receipt_path,binding_digest)"
                "VALUES(%s,%s,'runtime_release_v1',%s,%s,%s,%s,20,%s,%s)",
                (self.job_id,effect,request_digest,"ws-test-release",
                 commit,manifest_digest,receipt,binding_digest),
            )
        self.calls=[]

    def tearDown(self) -> None:
        # Each operator test owns one disposable PG Job. Do not allow its
        # accepted or unknown state to contaminate another test's drain.
        for table in ("job_events","concurrency_reservations",
                      "job_runtime_release_effects","idempotency_keys",
                      "attempts","jobs"):
            key = "attempt_id" if table=="concurrency_reservations" else "job_id"
            if table=="idempotency_keys":
                key="job_id"
            self.db.execute(f"DELETE FROM {table} WHERE {key}=%s",
                            (self.attempt_id if key=="attempt_id" else self.job_id,))
        import shutil
        shutil.rmtree(self.work,ignore_errors=True)


    def test_release_consumer_rejects_foreign_effect_and_inconclusive_mcp(self) -> None:
        # The Operator does not infer terminal Standing from a physical
        # receipt if the canonical authenticated release.get disagrees.
        receipt=self.args.receipt_root/f"effect-{self.args.effect_id}"
        receipt.mkdir()
        op.DEPLOY["write_json_atomic"](receipt/"result.json",{
            "schemaVersion":2,"status":"deployed",
        })
        terminal={"status":"deployed","pgTerminal":"succeeded"}
        environment={
            "ORDIVON_PG_BIND":"127.0.0.1:65500",
            "ORDIVON_PG_TOKEN":"p"*32,
        }
        with patch.dict(op.DEPLOY,{"load_environment_file":lambda path:environment}),\
             patch.object(op,"McpClient") as client:
            client.return_value.call_tool.return_value={
                "effectId":"foreign-or-unverified",
            }
            with self.assertRaisesRegex(RuntimeError,"RECONCILIATION_REQUIRED"):
                op.verified_release_consumer(self.args,terminal)
            client.return_value.call_tool.side_effect=TimeoutError(
                "injected canonical consumer outage"
            )
            with self.assertRaisesRegex(RuntimeError,"RECONCILIATION_REQUIRED"):
                op.verified_release_consumer(self.args,terminal)
            self.assertEqual(client.return_value.call_tool.call_count,2)
            self.assertEqual(
                client.return_value.call_tool.call_args.args[0],"release.get"
            )

    def test_release_drain_does_not_hold_source_lock_while_waiting(self) -> None:
        """Native PG proof: a terminal writer must progress during Release drain.

        The active-job projection is simulated, but a second *real* PG session
        must acquire the production source row lock to clear that condition.
        Holding FOR UPDATE while waiting creates a self-inflicted timeout.
        """
        from threading import Event, Thread

        cleared = Event()
        started = Event()
        worker_errors: list[str] = []
        workers: list[Thread] = []
        self.args.drain_seconds = 0.8

        def terminal_writer() -> None:
            try:
                with op.pg_connection(self.dsn, "fresh") as other:
                    with other.transaction():
                        other.execute(
                            "SELECT state FROM _stage_control WHERE id='source' FOR UPDATE"
                        )
                    cleared.set()
            except Exception as error:
                worker_errors.append(str(error))
                cleared.set()

        def observed_active(conn, release_job_id):
            if not started.is_set():
                started.set()
                thread = Thread(target=terminal_writer, daemon=True)
                workers.append(thread)
                thread.start()
            return [] if cleared.is_set() else ["agent-finishing-in-pg"]

        try:
            with patch.object(op, "active_executions", side_effect=observed_active), \
                 patch.object(op, "pg_mcp_readiness", return_value={
                     "toolCount": 20,
                     "toolCatalogDigest": "sha256:" + "f" * 64,
                 }), patch.dict(op.DEPLOY, {"run": lambda _args: None}), \
                 patch.object(op, "verified_release_consumer"):
                outcome = op.apply_release(self.args)
            self.assertEqual(outcome["status"], "deployed")
            self.assertTrue(cleared.is_set(), "PG terminal writer must progress during drain")
            self.assertFalse(worker_errors, worker_errors)
        finally:
            for thread in workers:
                thread.join(timeout=3)

    def test_pg_reclaimer_helper_installs_with_native_pair_and_receipt(self) -> None:
        """The same PG ReleaseEffect must own every installed consumer byte."""
        self.args.include_pg_reclaimer = True
        calls = []
        with patch.object(op, "pg_mcp_readiness", return_value={
            "toolCount": 20, "toolCatalogDigest": "sha256:" + "f" * 64,
        }), patch.dict(op.DEPLOY, {"run": lambda command: calls.append(tuple(command))}), (
            patch.object(op, "verified_release_consumer")
        ):
            result = op.apply_release(self.args)
            self.assertEqual(result["status"], "deployed")
            self.assertEqual(result["pgTerminal"], "succeeded")
            self.assertEqual((self.install / "ordivon-runtime-pg-reclaim").read_bytes(),
                             b"new-qualified-pg-reclaimer")
            self.assertEqual((self.install / "ordivon-runtime-pg").read_bytes(),
                             b"new-pg-runtime")
            self.assertEqual((self.install / "ordivon-runtime-runner").read_bytes(),
                             b"new-runner")
            self.assertEqual(len(calls), 2)
            receipt = self.args.receipt_root / f"effect-{self.args.effect_id}"
            previous = json.loads((receipt / "manifest.json").read_text())
            self.assertEqual(
                {record["name"] for record in previous["previous"]},
                {"ordivon-runtime-pg", "ordivon-runtime-runner",
                 "ordivon-runtime-pg-reclaim"},
            )
            self.assertEqual((receipt / "previous" /
                              "ordivon-runtime-pg-reclaim").read_bytes(),
                             b"old-qualified-pg-reclaimer")
            self.assertEqual(
                {record["name"] for record in result["installed"]},
                {"ordivon-runtime-pg", "ordivon-runtime-runner",
                 "ordivon-runtime-pg-reclaim"},
            )
            replay = op.apply_release(self.args)
            self.assertTrue(replay["replayed"])
            self.assertEqual(len(calls), 2, "receipt replay must not reinstall helper")

    def test_pg_reclaimer_helper_rolls_back_with_native_pair(self) -> None:
        """Systemd start failure must roll back the helper, not just binaries."""
        self.args.include_pg_reclaimer = True
        calls = []

        def failed_start(command):
            calls.append(tuple(command))
            if command[-2:] == ["start", self.args.service]:
                raise RuntimeError("injected start failure")

        def restore(previous, install_dir, records, systemctl, service, env_file, wait_seconds, *, readiness_probe=None):
            self.assertEqual(
                {item["name"] for item in records},
                {"ordivon-runtime-pg", "ordivon-runtime-runner",
                 "ordivon-runtime-pg-reclaim"},
            )
            for item in records:
                op.DEPLOY["atomic_copy"](
                    previous / item["name"], install_dir / item["name"],
                    mode=item["mode"],
                )
            return {"serviceActive": True, "probe": {"recovered": True}}

        with patch.dict(op.DEPLOY, {
            "run": failed_start,
            "restore_previous": restore,
        }):
            with self.assertRaisesRegex(RuntimeError, "rolled_back"):
                op.apply_release(self.args)
        self.assertEqual((self.install / "ordivon-runtime-pg-reclaim").read_bytes(),
                         b"old-qualified-pg-reclaimer")
        self.assertEqual((self.install / "ordivon-runtime-pg").read_bytes(),
                         b"old-pg-runtime")
        self.assertEqual((self.install / "ordivon-runtime-runner").read_bytes(),
                         b"old-runner")
        self.assertEqual(len(calls), 2)
        receipt = self.args.receipt_root / f"effect-{self.args.effect_id}"
        result = json.loads((receipt / "result.json").read_text())
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(
            self.db.execute("SELECT resolution FROM jobs WHERE job_id=%s",
                            (self.job_id,)).fetchone()["resolution"], "failed",
        )

    def test_pg_reclaimer_helper_candidate_digest_fails_before_dispatch(self) -> None:
        """A changed helper cannot borrow an older two-binary ReleaseEffect."""
        self.args.include_pg_reclaimer = True
        (self.candidate / "ordivon-runtime-pg-reclaim").write_bytes(
            b"candidate-changed-after-manifest"
        )
        with self.assertRaisesRegex(RuntimeError, "release artifact"):
            op.apply_release(self.args)
        self.assertEqual((self.install / "ordivon-runtime-pg-reclaim").read_bytes(),
                         b"old-qualified-pg-reclaimer")
        self.assertFalse((self.args.receipt_root /
                          f"effect-{self.args.effect_id}").exists())
        self.assertEqual(
            self.db.execute(
                "SELECT count(*) AS n FROM job_events WHERE job_id=%s "
                "AND event_type=%s", (self.job_id, op.DISPATCH_EVENT),
            ).fetchone()["n"], 0,
        )

    def test_release_exactly_once_and_terminal_receipt(self) -> None:
        def run(args):
            self.calls.append(tuple(args))
        with patch.object(op,"pg_mcp_readiness",return_value={
            "toolCount":20,"toolCatalogDigest":"sha256:"+"f"*64,
        }),patch.dict(op.DEPLOY, {"run":run}),\
             patch.object(op,"verified_release_consumer") as consumer:
            result=op.apply_release(self.args)
            self.assertEqual(result["status"],"deployed")
            self.assertEqual(result["pgTerminal"],"succeeded")
            self.assertEqual((self.install/"ordivon-runtime-pg").read_bytes(),b"new-pg-runtime")
            self.assertEqual(len(self.calls),2)
            replay=op.apply_release(self.args)
            self.assertTrue(replay["replayed"])
            self.assertEqual(replay["pgTerminal"],"succeeded")
            self.assertEqual(len(self.calls),2,
                             "exact release replay cannot invoke systemd again")
            # Even after a real terminal PG receipt, a forged partial native
            # profile must not bypass Runner qualification on replay.
            partial = Namespace(**vars(self.args))
            partial.binaries = ["ordivon-runtime-pg"]
            with patch.object(op, "pg_connection") as connect:
                with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                    op.apply_release(partial)
                connect.assert_not_called()
            self.assertEqual(len(self.calls),2, "rejected replay must not touch systemd")
            # Do not requalify the physical effect just to replay its exact
            # previously terminal admission after operator revocation.
            self.db.execute(
                "UPDATE _stage_control SET promotion_allowed=false WHERE id='release'"
            )
            try:
                revoked_replay=op.apply_release(self.args)
                self.assertTrue(revoked_replay["replayed"])
                self.assertEqual(len(self.calls),2)
                self.assertEqual(consumer.call_count,3)
            finally:
                self.db.execute(
                    "UPDATE _stage_control SET promotion_allowed=true WHERE id='release'"
                )
        self.assertEqual(
            self.db.execute("SELECT resolution FROM jobs WHERE job_id=%s",
                            (self.job_id,)).fetchone()["resolution"],"succeeded")
        self.assertEqual(
            self.db.execute("SELECT state FROM concurrency_reservations WHERE attempt_id=%s",
                            (self.attempt_id,)).fetchone()["state"],"released")
        self.assertEqual(
            self.db.execute("SELECT count(*) AS n FROM job_events WHERE job_id=%s "
                            "AND event_type=%s",(self.job_id,op.DISPATCH_EVENT)
                            ).fetchone()["n"],1)

    def test_systemd_start_failure_restores_preimage_and_terminal_failure(self) -> None:
        calls=[]
        def failed_start(cmd):
            calls.append(tuple(cmd))
            if cmd[-2:]==["start",self.args.service]:
                raise RuntimeError("injected systemd start failure")
        def restore(previous,install_dir,records,systemctl,service,env_file,wait_seconds,*,readiness_probe=None):
            for record in records:
                op.DEPLOY["atomic_copy"](
                    previous/record["name"], install_dir/record["name"],
                    mode=record["mode"],
                )
            self.assertTrue(callable(readiness_probe))
            return {"serviceActive":True,"probe":{"recovered":True}}
        with patch.dict(op.DEPLOY,{
            "run":failed_start,
            "restore_previous":restore,
        }):
            with self.assertRaisesRegex(RuntimeError,"rolled_back"):
                op.apply_release(self.args)
        self.assertEqual((self.install/"ordivon-runtime-pg").read_bytes(),
                         b"old-pg-runtime")
        result=json.loads((self.args.receipt_root/
             f"effect-{self.args.effect_id}"/"result.json").read_text())
        self.assertEqual(result["status"],"rolled_back")
        self.assertEqual(
            self.db.execute("SELECT resolution FROM jobs WHERE job_id=%s",
                            (self.job_id,)).fetchone()["resolution"],"failed")
        self.assertEqual(len(calls),2)

    def test_atomic_replace_failure_is_not_marked_not_committed(self) -> None:
        original_replace=op.os.replace
        def fail_one(source,target):
            if str(target)==str(self.install/"ordivon-runtime-pg") and str(source).endswith(".next"):
                raise OSError("injected mid-rename failure")
            return original_replace(source,target)
        def restore(previous,install_dir,records,systemctl,service,env_file,wait_seconds,*,readiness_probe=None):
            op.DEPLOY["atomic_copy"](
                previous/"ordivon-runtime-pg",
                install_dir/"ordivon-runtime-pg",mode=0o755,
            )
            return {"serviceActive":True}
        with patch.object(op.os,"replace",side_effect=fail_one),patch.dict(op.DEPLOY,{
            "run":lambda cmd: None,
            "restore_previous":restore,
        }):
            with self.assertRaisesRegex(RuntimeError,"rolled_back"):
                op.apply_release(self.args)
        result=json.loads((self.args.receipt_root/
             f"effect-{self.args.effect_id}"/"result.json").read_text())
        self.assertNotEqual(result["status"],"not_committed",
                            "rename attempt is already a physical effect boundary")

    def test_forged_terminal_receipt_cannot_finalize_pg_success(self) -> None:
        with op.pg_connection(self.dsn,"fresh") as conn:
            _,bound=op.dispatch_claim(conn,self.args)
        request=op.effect_request(self.args,bound)
        receipt=self.args.receipt_root/f"effect-{self.args.effect_id}"
        receipt.mkdir()
        op.DEPLOY["write_json_atomic"](receipt/"effect-request.json",request)
        op.DEPLOY["write_json_atomic"](receipt/"result.json",{
            "schemaVersion":2,"status":"deployed","commit":self.args.commit,
            "serviceActive":True,
            "probe":{"toolCount":999,"toolCatalogDigest":"sha256:"+"a"*64},
            "releaseEffect":request,
        })
        with self.assertRaisesRegex(RuntimeError,"no qualified deployed MCP receipt"):
            op.apply_release(self.args)
        self.assertEqual(
            self.db.execute("SELECT resolution FROM jobs WHERE job_id=%s",
                            (self.job_id,)).fetchone()["resolution"],None)
        self.assertEqual((self.install/"ordivon-runtime-pg").read_bytes(),b"old-pg-runtime")

    def test_release_qualification_revocation_blocks_dispatch(self) -> None:
        self.db.execute(
            "UPDATE _stage_control SET promotion_allowed=false WHERE id='release'"
        )
        try:
            with self.assertRaisesRegex(RuntimeError,"qualification absent"):
                op.apply_release(self.args)
            self.assertEqual((self.install/"ordivon-runtime-pg").read_bytes(),b"old-pg-runtime")
        finally:
            self.db.execute(
                "UPDATE _stage_control SET promotion_allowed=true WHERE id='release'"
            )

    def test_post_commit_dispatch_loss_never_reinstalls(self) -> None:
        with op.pg_connection(self.dsn,"fresh") as conn:
            op.dispatch_claim(conn,self.args)
        with self.assertRaisesRegex(RuntimeError,"RECONCILIATION_REQUIRED"):
            op.apply_release(self.args)
        self.assertEqual((self.install/"ordivon-runtime-pg").read_bytes(),b"old-pg-runtime")
        self.assertFalse((self.args.receipt_root/f"effect-{self.args.effect_id}").exists())

    def test_wrong_manifest_and_receipt_root_fail_before_dispatch(self) -> None:
        bad=Namespace(**vars(self.args))
        bad.candidate_manifest_digest="sha256:"+"f"*64
        with self.assertRaisesRegex(RuntimeError,"intent does not match"):
            op.apply_release(bad)
        bad=Namespace(**vars(self.args))
        bad.receipt_root=self.work/"wrong"
        bad.receipt_root.mkdir()
        with self.assertRaisesRegex(RuntimeError,"receipt path differs"):
            op.apply_release(bad)
        self.assertEqual(
            self.db.execute("SELECT count(*) AS n FROM job_events "
                            "WHERE job_id=%s AND event_type=%s",
                            (self.job_id,op.DISPATCH_EVENT)).fetchone()["n"],0)

    @unittest.skipUnless(
        os.environ.get("ORDIVON_RUN_NATIVE_PG_SYSTEMD_RELEASE")=="1",
        "requires explicitly selected disposable real systemd/PG release acceptance",
    )
    def test_actual_systemd_pg_binary_replacement_and_http_mcp_readback(self) -> None:
        """Real disposable PG cluster + systemd unit + network MCP release.

        No production service, unit, database, binary path or environment file
        is modified. The source Git checkout is test-only, so this proves
        physical systemd/PG refinement, not signed production supply chain.
        """
        from shutil import copy2
        import socket
        # The default-deny ordinary PG route removes the dangerous direct
        # Claim release tool even without a dedicated Harness issuer:
        # 21 portable + 3 Claim - release.apply - claim.release = 22.
        # Preserve an exact source-bound catalog assertion in native E2E.
        native_tool_count = 22
        self.args.expected_tool_count = native_tool_count
        runner=SCRIPTS.parent/"target/debug/ordivon-runtime-runner"
        pg_binary=SCRIPTS.parent/"target/debug/ordivon-runtime-pg"
        if not runner.is_file() or not pg_binary.is_file():
            raise RuntimeError("build native PG Runner and MCP binaries before test")
        original=(self.install/"ordivon-runtime-pg")
        original.write_text(
            "#!/usr/bin/python3\n"
            "import time\n"
            "while True: time.sleep(0.5)\n",encoding="utf-8"
        )
        original.chmod(0o755)
        copy2(pg_binary,self.candidate/"ordivon-runtime-pg")
        (self.candidate/"ordivon-runtime-pg").chmod(0o755)
        copy2(runner,self.candidate/"ordivon-runtime-runner")
        copy2(runner,self.install/"ordivon-runtime-runner")
        for path in (self.candidate/"ordivon-runtime-runner",
                     self.install/"ordivon-runtime-runner"):
            path.chmod(0o755)
        self.args.binaries=["ordivon-runtime-pg","ordivon-runtime-runner"]
        obj=json.loads(self.manifest.read_text())
        obj["artifacts"]=[
            op.DEPLOY["artifact_description"](
                self.candidate/name,
                {"name":name,"kind":"binary","mode":0o755},
            ) for name in self.args.binaries
        ]
        if self.args.include_pg_reclaimer:
            obj["artifacts"].append(
                op.DEPLOY["artifact_description"](
                    self.candidate/"ordivon-runtime-pg-reclaim",
                    {"name":"ordivon-runtime-pg-reclaim","kind":"operator","mode":0o755},
                )
            )
        obj["binaries"]=[item for item in obj["artifacts"]
                         if item["kind"]=="binary"]
        self.manifest.write_text(json.dumps(obj),encoding="utf-8")
        fresh_manifest=op.DEPLOY["sha256"](self.manifest)
        self.args.candidate_manifest_digest=fresh_manifest
        identity={
            "schemaVersion":1,"principal":self.args.principal,
            "workspaceId":"ws-test-release","commit":self.args.commit,
            "candidateManifestDigest":fresh_manifest,
            "expectedToolCount":self.args.expected_tool_count,
        }
        request_digest="runtime-release-v1:"+op.digest(op.canonical_json(identity).encode())
        binding={
            "contract":"runtime_release_v1","effectId":self.args.effect_id,
            "requestDigest":request_digest,"workspaceId":"ws-test-release",
            "commit":self.args.commit,"candidateManifestDigest":fresh_manifest,
            "expectedToolCount":native_tool_count,"receiptPath":
                str(self.args.receipt_root/f"effect-{self.args.effect_id}"),
        }
        bd=op.digest(op.canonical_json(binding).encode())
        self.db.execute(
            "UPDATE jobs SET request_digest=%s,workspace_snapshot_json=%s "
            "WHERE job_id=%s",
            (request_digest,json.dumps({"runtimeReleaseEffectDigest":bd}),self.job_id),
        )
        self.db.execute(
            "UPDATE job_runtime_release_effects SET request_digest=%s,"
            "candidate_manifest_digest=%s,binding_digest=%s,"
            "expected_tool_count=%s WHERE job_id=%s",
            (request_digest,fresh_manifest,bd,native_tool_count,self.job_id),
        )
        self.db.execute(
            "CREATE ROLE runtime_app LOGIN"
        )
        self.db.execute("GRANT USAGE ON SCHEMA fresh TO runtime_app")
        self.db.execute("GRANT ALL ON ALL TABLES IN SCHEMA fresh TO runtime_app")
        self.db.execute("REVOKE ALL ON fresh._stage_control FROM runtime_app")
        self.db.execute(
            "GRANT SELECT,UPDATE(id) ON fresh._stage_control TO runtime_app"
        )
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1",0))
            bind=f"127.0.0.1:{sock.getsockname()[1]}"
        service=f"ordivon-pg-release-acceptance-{uuid.uuid4().hex[:13]}.service"
        unit=Path("/run/systemd/system")/service
        self.args.service=service
        os.environ["ORDIVON_PG_RELEASE_ALLOWED_SERVICES_JSON"]=json.dumps([service])
        self.args.wait_seconds=20.
        self.args.required_tools=["runtime.describe","release.get"]
        # PG contract and older Runtime's probe identity are not conflated.
        self.env_file.write_text(
            f'ORDIVON_PG_DSN="host={self.root} user=runtime_app dbname=postgres"\n'
            "ORDIVON_PG_SCHEMA=fresh\n"
            f"ORDIVON_PG_SOURCE_SHA256={self.source_sha}\n"
            f"ORDIVON_PG_STORE_ROOT={self.work/'pg-store'}\n"
            f"ORDIVON_PG_RUNNER={self.install/'ordivon-runtime-runner'}\n"
            'ORDIVON_PG_EXECUTABLE_ROOTS_JSON=["/usr/bin","/bin"]\n'
            f"ORDIVON_PG_BIND={bind}\n"
            f"ORDIVON_PG_TOKEN={'p'*32}\n"
            f"ORDIVON_PG_PRINCIPAL={self.args.principal}\n",
            encoding="utf-8",
        )
        unit.write_text(
            "[Unit]\nDescription=Ordivon temporary PG Release acceptance\n"
            "[Service]\nType=simple\n"
            f"EnvironmentFile={self.env_file}\n"
            f"ExecStart={original}\n"
            "Restart=no\nKillMode=control-group\n",
            encoding="utf-8",
        )
        systemctl=binary("systemctl")
        try:
            subprocess.run([systemctl,"daemon-reload"],check=True,capture_output=True)
            subprocess.run([systemctl,"start",service],check=True,capture_output=True)
            # Real consumer misbinding: the unit can execute a totally
            # different ELF while the operator installs a candidate into
            # installDir, and the MCP tool catalog remains identical.
            shadow=self.work/"shadow-active-ordivon-runtime-pg"
            copy2(pg_binary,shadow)
            with shadow.open("ab") as stream:
                stream.write(b"\nshadow-distinct-active-binary-20261111\n")
            shadow.chmod(0o755)
            self.assertNotEqual(op.DEPLOY["sha256"](shadow),
                                op.DEPLOY["sha256"](self.candidate/"ordivon-runtime-pg"))
            def switch_unit(path, runner_override=None):
                subprocess.run([systemctl,"stop",service],check=True,capture_output=True)
                extra=(f"EnvironmentFile={runner_override}\n"
                       if runner_override is not None else "")
                unit.write_text(
                    "[Unit]\nDescription=Ordivon temporary PG Release acceptance\n"
                    "[Service]\nType=simple\n"
                    f"EnvironmentFile={self.env_file}\n"
                    + extra
                    + f"ExecStart={path}\n"
                    "Restart=no\nKillMode=control-group\n",encoding="utf-8",
                )
                subprocess.run([systemctl,"daemon-reload"],check=True,capture_output=True)
                subprocess.run([systemctl,"start",service],check=True,capture_output=True)
            switch_unit(shadow)
            shadow_catalog=op.DEPLOY["probe_catalog"](
                f"http://{bind}/mcp","p"*32,
                client_name="independent-shadow-process-probe",
                expected_tool_count=native_tool_count,
                required_tools=("runtime.describe","release.get"),
                wait_seconds=10.,require_modern=True,allow_legacy_fallback=False,
            )
            self.assertEqual(shadow_catalog["toolCount"],native_tool_count,
                             "unrelated executable also offers a healthy MCP catalog")
            with self.assertRaisesRegex(RuntimeError,"PG release preflight rejected"):
                op.apply_release(self.args)
            count=self.db.execute(
                "SELECT count(*) AS n FROM job_events WHERE job_id=%s "
                "AND event_type=%s",(self.job_id,op.DISPATCH_EVENT),
            ).fetchone()["n"]
            self.assertEqual(count,0,"mismatched systemd binary cannot dispatch a ReleaseEffect")
            self.assertEqual(original.read_bytes()[:2],b"#!",
                             "mismatched unit must not install candidate")
            # The operator's base envFile says the correct installed Runner,
            # but a *later* systemd EnvironmentFile can silently override it.
            # This is the second production-relevant consumer binding.
            runner_shadow=self.work/"shadow-runner-binary"
            copy2(runner,runner_shadow)
            with runner_shadow.open("ab") as stream:
                stream.write(b"\nshadow-distinct-runner-digest-20261111\n")
            runner_shadow.chmod(0o755)
            self.assertNotEqual(op.DEPLOY["sha256"](runner_shadow),
                                op.DEPLOY["sha256"](self.candidate/"ordivon-runtime-runner"))
            runner_override=self.work/"shadow-runner.env"
            runner_override.write_text(
                f"ORDIVON_PG_RUNNER={runner_shadow}\n",encoding="utf-8",
            )
            switch_unit(original,runner_override=runner_override)
            self.assertEqual(
                op.effective_systemd_runner_binding(self.args),str(runner_shadow),
                "late systemd EnvironmentFile must supersede base Runner path",
            )
            with self.assertRaisesRegex(RuntimeError,"PG release preflight rejected"):
                op.apply_release(self.args)
            count=self.db.execute(
                "SELECT count(*) AS n FROM job_events WHERE job_id=%s "
                "AND event_type=%s",(self.job_id,op.DISPATCH_EVENT),
            ).fetchone()["n"]
            self.assertEqual(count,0,"effective Runner mismatch cannot dispatch")
            switch_unit(original)
            observed=op.apply_release(self.args)
            self.assertEqual(observed["status"],"deployed")
            self.assertEqual(observed["pgTerminal"],"succeeded")
            self.assertEqual(original.read_bytes(),pg_binary.read_bytes())
            self.assertEqual(
                (self.install/"ordivon-runtime-pg-reclaim").read_bytes(),
                (self.candidate/"ordivon-runtime-pg-reclaim").read_bytes(),
            )
            self.assertIn(
                "ordivon-runtime-pg-reclaim",
                {entry["name"] for entry in observed["installed"]},
            )
            self.assertEqual(observed["probe"]["toolCount"],native_tool_count)
            active=observed["probe"]["activeRuntimeImage"]
            self.assertEqual(active["path"],str(original))
            self.assertEqual(active["digest"],op.DEPLOY["sha256"](original))
            self.assertGreater(active["mainPid"],1)
            self.assertEqual(active["runnerWitness"],"authenticated_runtime_describe")
            self.assertEqual(active["runnerDigest"],
                             op.DEPLOY["sha256"](self.install/"ordivon-runtime-runner"))
            replay=op.apply_release(self.args)
            self.assertTrue(replay["replayed"])
            self.assertEqual(replay["pgTerminal"],"succeeded")
            # A historical positive receipt cannot legitimize a new caller
            # bypassing the complete two-binary profile. Fail before PG/OS.
            partial=Namespace(**vars(self.args))
            partial.binaries=["ordivon-runtime-pg"]
            current_pid=op.systemd_property(self.args,"MainPID")
            with patch.object(op,"pg_connection") as connect:
                with self.assertRaisesRegex(RuntimeError,"complete native PG and Runner"):
                    op.apply_release(partial)
                connect.assert_not_called()
            self.assertEqual(op.systemd_property(self.args,"MainPID"),current_pid)
            # The PG binary remains the live MCP client target, unlike mocked
            # readiness. Query from a fresh independent transport session.
            from mcp_probe import McpClient
            client=McpClient(f"http://{bind}/mcp","p"*32,"pg-release-acceptance")
            discovered=client.discover()
            self.assertIsNotNone(discovered)
            observed_release=client.call_tool("release.get", {
                "clientRequestId":self.args.client_request_id
            })
            self.assertEqual(observed_release["effectId"],self.args.effect_id)
            self.assertEqual(observed_release["effectDisposition"],"deployed")
            self.assertEqual(observed_release["receiptAvailable"],True)
            self.assertEqual(observed_release["executionDisposition"],"succeeded")
            self.assertEqual(observed_release["deployedToolCount"],native_tool_count)
            self.assertEqual(observed_release["semanticCompletionEvaluated"],False)
            self.assertEqual(observed_release["commit"],self.args.commit)
            # Direct consumer readback must bind the *same* qualified PG
            # Attempt digest, even when no Python release operator is called.
            # These mutations are confined to the disposable native receipt.
            from mcp_probe import McpToolError
            receipt=self.args.receipt_root/f"effect-{self.args.effect_id}"
            result_path=receipt/"result.json"
            original_bytes=result_path.read_bytes()
            self.assertEqual(observed_release["receiptDigest"],op.digest(original_bytes))
            for variant in ("different_bytes_same_status","uncommitted_rollback"):
                with self.subTest(receipt_mutation=variant):
                    auxiliary=receipt/"rollback-result.json"
                    try:
                        if variant=="different_bytes_same_status":
                            result=json.loads(original_bytes)
                            result["uncommittedObservation"]="not-the-settled-bytes"
                            op.DEPLOY["write_json_atomic"](result_path,result)
                            self.assertNotEqual(op.digest(result_path.read_bytes()),
                                                observed_release["receiptDigest"])
                        else:
                            op.DEPLOY["write_json_atomic"](auxiliary,
                                                          {"status":"restored_previous"})
                            self.assertEqual(result_path.read_bytes(),original_bytes)
                        with self.assertRaisesRegex(McpToolError,"RECONCILIATION_REQUIRED"):
                            client.call_tool("release.get",{
                                "clientRequestId":self.args.client_request_id})
                    finally:
                        result_path.write_bytes(original_bytes)
                        auxiliary.unlink(missing_ok=True)
                    restored=client.call_tool("release.get",{
                        "clientRequestId":self.args.client_request_id})
                    self.assertEqual(restored,observed_release)
                    self.assertEqual(self.db.execute(
                        "SELECT resolution FROM jobs WHERE job_id=%s",(self.job_id,)
                    ).fetchone()["resolution"],"succeeded")
            # After a valid deployment, drift only the effective systemd
            # ExecStart. A release replay MUST NOT turn a matching MCP catalog
            # and disk copy into proof that a different process was installed.
            switch_unit(shadow)
            shadow_catalog=op.DEPLOY["probe_catalog"](
                f"http://{bind}/mcp","p"*32,
                client_name="replay-shadow-process-probe",
                expected_tool_count=native_tool_count,
                required_tools=("runtime.describe","release.get"),
                wait_seconds=10.,require_modern=True,allow_legacy_fallback=False,
            )
            self.assertEqual(shadow_catalog["toolCount"],native_tool_count)
            with self.assertRaisesRegex(RuntimeError,"RECONCILIATION_REQUIRED"):
                op.apply_release(self.args)
            # MainPID now executes the *correct* installed ELF but a fresh
            # systemd restart points only the Runner at an external binary.
            switch_unit(original,runner_override=runner_override)
            self.assertEqual(
                op.effective_systemd_runner_binding(self.args),str(runner_shadow),
            )
            # The systemd start command is a submission, not an HTTP-ready
            # witness. Wait for the independent modern MCP catalog before
            # reading the restarted native Rust execution provider.
            runner_catalog=op.DEPLOY["probe_catalog"](
                f"http://{bind}/mcp","p"*32,
                client_name="independent-runner-drift-process-probe",
                expected_tool_count=native_tool_count,
                required_tools=("runtime.describe","release.get"),
                wait_seconds=10.,require_modern=True,allow_legacy_fallback=False,
            )
            self.assertEqual(runner_catalog["toolCount"],native_tool_count)
            # Read the *actual* Runner provider, not a manifest declaration.
            live_provider=client.call_tool("runtime.describe",{"schemaVersion":1})
            self.assertEqual(
                live_provider["targets"][0]["executionProvider"]["executableDigest"],
                op.DEPLOY["sha256"](runner_shadow),
            )
            with self.assertRaisesRegex(RuntimeError,"RECONCILIATION_REQUIRED"):
                op.apply_release(self.args)
            switch_unit(original)
            # Physical release is immutable, but terminal event standing is
            # independently qualified by the canonical Rust release.get.
            # Tamper ONLY with this disposable PG test schema.
            deleted=self.db.execute(
                "DELETE FROM job_events WHERE job_id=%s AND event_type='JOB_TERMINAL'",
                (self.job_id,),
            ).rowcount
            self.assertEqual(deleted,1)
            with self.assertRaisesRegex(RuntimeError,"RECONCILIATION_REQUIRED"):
                op.apply_release(self.args)
            count=self.db.execute(
                "SELECT count(*) AS n FROM job_events WHERE job_id=%s "
                "AND event_type=%s",(self.job_id,op.DISPATCH_EVENT),
            ).fetchone()["n"]
            self.assertEqual(count,1,"terminal readback failure cannot dispatch again")
        finally:
            subprocess.run([systemctl,"stop",service],capture_output=True)
            unit.unlink(missing_ok=True)
            subprocess.run([systemctl,"daemon-reload"],capture_output=True)

    def test_physical_epoch_drift_fails_closed_before_dispatch(self) -> None:
        self.db.execute(
            "UPDATE _stage_control SET source_sha256=%s WHERE id='epoch'",
            ("f"*64,)
        )
        try:
            with self.assertRaisesRegex(RuntimeError, "physical PostgreSQL writer epoch"):
                op.apply_release(self.args)
            self.assertEqual((self.install/"ordivon-runtime-pg").read_bytes(),
                             b"old-pg-runtime")
            issued=self.db.execute(
                "SELECT count(*) AS n FROM job_events WHERE job_id=%s AND event_type=%s",
                (self.job_id,op.DISPATCH_EVENT),
            ).fetchone()["n"]
            self.assertEqual(issued,0)
        finally:
            self.db.execute(
                "UPDATE _stage_control SET source_sha256=%s WHERE id='epoch'",
                (self.epoch,)
            )

    def test_role_without_operator_authority_is_rejected(self) -> None:
        self.db.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='runtime_release_denied') THEN CREATE ROLE runtime_release_denied LOGIN; END IF; END $$")
        self.db.execute("GRANT USAGE ON SCHEMA fresh TO runtime_release_denied")
        self.db.execute("GRANT SELECT ON ALL TABLES IN SCHEMA fresh TO runtime_release_denied")
        with op.pg_connection(f"host={self.root} user=runtime_release_denied dbname=postgres","fresh") as conn:
            with self.assertRaisesRegex(RuntimeError,"operator authority"):
                op.qualified_operator(conn,self.source_sha,lock=False)


if __name__=="__main__":
    unittest.main()
