from __future__ import annotations

import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/ordivon-runtime-pressure-control"
POLICY = REPO / "packaging/systemd/ordivon-storage-pressure-control.json"
SERVICE = REPO / "packaging/systemd/ordivon-runtime-storage-pressure.service"
TIMER = REPO / "packaging/systemd/ordivon-runtime-storage-pressure.timer"


class PressureControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = runpy.run_path(str(SCRIPT))
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))

    def decision(self, free: int, *, state=None, registry=None, samples=None, now=10_000_000):
        state = dict(state or {})
        samples = list(samples or [{"observedAtMs": now, "freeBytes": free}])
        registry = dict(registry or {"jobsTotal": 100, "activeReservations": 0, "heldReservations": 0, "recoveryRequired": 0, "migrationVersion": 6})
        return self.module["decide"](
            now_ms=now,
            free_bytes=free,
            registry=registry,
            state=state,
            policy=self.policy,
            samples=samples,
        )

    def test_policy_rejects_unknown_fields_instead_of_defaulting_silently(self):
        policy = dict(self.policy)
        policy["hardFl00rBytes"] = policy["hardFloorBytes"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "unknown.*hardFl00rBytes"):
                self.module["load_policy"](path)

    def test_policy_rejects_duplicate_json_keys_at_source_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            policy = POLICY.read_text(encoding="utf-8").rstrip()
            self.assertTrue(policy.endswith("}"))
            policy = policy[:-1] + ', "hardFloorBytes": 1}'
            path.write_text(policy, encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "duplicate JSON key.*hardFloorBytes"):
                self.module["load_policy"](path)

    def test_schema_version_boolean_alias_does_not_pass_integer_const(self):
        policy = dict(self.policy)
        policy["schemaVersion"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "schemaVersion"):
                self.module["load_policy"](path)

    def test_policy_separates_hard_floor_from_soft_trigger(self):
        self.assertEqual(self.policy["hardFloorBytes"], 20 * 1024**3)
        self.assertEqual(self.policy["softTriggerBytes"], 28 * 1024**3)
        self.assertGreater(self.policy["softTriggerBytes"], self.policy["hardFloorBytes"])

    def test_above_soft_trigger_is_cheap_no_action(self):
        decision = self.decision(30 * 1024**3)
        self.assertFalse(decision["action"])
        self.assertEqual(decision["reason"], "NORMAL_ABOVE_SOFT_TRIGGER")

    def test_above_soft_forecast_wakes_preemptive_cache_probe(self):
        """The 2h hard-floor forecast must not disappear above the 28GiB gate."""
        now = 20_000_000
        free = 50 * 1024**3
        samples = [
            {"observedAtMs": now - 1800 * 1000, "freeBytes": 68 * 1024**3},
            {"observedAtMs": now, "freeBytes": free},
        ]
        decision = self.decision(free, samples=samples, now=now)
        self.assertLess(decision["timeToHardFloorSeconds"], self.policy["reactionHorizonSeconds"])
        self.assertTrue(decision["action"])
        self.assertEqual(decision["reason"], "TIME_TO_FLOOR_WITHIN_REACTION_HORIZON")

    def test_above_soft_forecast_respects_expensive_probe_cooldown(self):
        now = 20_000_000
        free = 50 * 1024**3
        samples = [
            {"observedAtMs": now - 1800 * 1000, "freeBytes": 68 * 1024**3},
            {"observedAtMs": now, "freeBytes": free},
        ]
        decision = self.decision(
            free, samples=samples, now=now,
            state={"lastExpensiveProbeAtMs": now - 60_000,
                   "nextExpensiveProbeAfterMs": now + 600 * 1000},
        )
        self.assertFalse(decision["action"])
        self.assertEqual(decision["reason"], "FORECAST_PRESSURE_COOLDOWN")

    def test_above_soft_cooldown_cannot_extend_past_forecast_hard_floor(self):
        now = 20_000_000
        free = 50 * 1024**3
        samples = [
            {"observedAtMs": now - 1800 * 1000, "freeBytes": 68 * 1024**3},
            {"observedAtMs": now, "freeBytes": free},
        ]
        decision = self.decision(
            free, samples=samples, now=now,
            state={"lastExpensiveProbeAtMs": now - 60_000,
                   "nextExpensiveProbeAfterMs": now + 3600 * 1000},
        )
        self.assertTrue(decision["action"])
        self.assertEqual(decision["reason"], "TIME_TO_FLOOR_WITHIN_REACTION_HORIZON")

    def test_hard_floor_forces_action_even_during_cooldown(self):
        decision = self.decision(19 * 1024**3, state={"nextExpensiveProbeAfterMs": 99_000_000})
        self.assertTrue(decision["action"])
        self.assertEqual(decision["reason"], "HARD_FLOOR_REACHED")

    def test_soft_pressure_stable_state_respects_cooldown(self):
        state = {
            "registrySignal": {"jobsTotal": 100, "activeReservations": 0, "heldReservations": 0, "recoveryRequired": 0, "migrationVersion": 6},
            "lastExpensiveProbeAtMs": 9_000_000,
            "nextExpensiveProbeAfterMs": 20_000_000,
        }
        decision = self.decision(26 * 1024**3, state=state)
        self.assertFalse(decision["action"])
        self.assertEqual(decision["reason"], "SOFT_PRESSURE_COOLDOWN")

    def test_registry_change_wakes_controller_after_min_event_interval(self):
        now = 20_000_000
        state = {
            "registrySignal": {"jobsTotal": 99, "activeReservations": 0, "heldReservations": 0, "recoveryRequired": 0, "migrationVersion": 6},
            "lastExpensiveProbeAtMs": now - (self.policy["eventProbeMinIntervalSeconds"] + 1) * 1000,
            "nextExpensiveProbeAfterMs": now + 99_000_000,
        }
        decision = self.decision(26 * 1024**3, state=state, registry={"jobsTotal": 100, "activeReservations": 0, "heldReservations": 0, "recoveryRequired": 0, "migrationVersion": 6}, now=now)
        self.assertTrue(decision["action"])
        self.assertEqual(decision["reason"], "REGISTRY_ACTIVITY_CHANGED")

    def test_time_to_floor_wakes_controller(self):
        now = 20_000_000
        before = now - 3600 * 1000
        samples = [
            {"observedAtMs": before, "freeBytes": 27 * 1024**3},
            {"observedAtMs": now, "freeBytes": 24 * 1024**3},
        ]
        state = {
            "registrySignal": {"jobsTotal": 100, "activeReservations": 0, "heldReservations": 0, "recoveryRequired": 0, "migrationVersion": 6},
            "lastExpensiveProbeAtMs": now,
            "nextExpensiveProbeAfterMs": now + 99_000_000,
        }
        decision = self.decision(24 * 1024**3, state=state, samples=samples, now=now)
        self.assertTrue(decision["action"])
        self.assertEqual(decision["reason"], "TIME_TO_FLOOR_WITHIN_REACTION_HORIZON")
        self.assertLessEqual(decision["timeToHardFloorSeconds"], self.policy["reactionHorizonSeconds"])

    def test_zero_yield_backoff_grows_and_effective_yield_resets(self):
        state = {}
        update = self.module["update_backoff"]
        update(state, now_ms=1_000, yield_bytes=0, policy=self.policy)
        first = state["lastCooldownSeconds"]
        self.assertEqual(state["zeroYieldStreak"], 1)
        update(state, now_ms=2_000, yield_bytes=0, policy=self.policy)
        self.assertEqual(state["zeroYieldStreak"], 2)
        self.assertGreater(state["lastCooldownSeconds"], first)
        update(state, now_ms=3_000, yield_bytes=self.policy["minimumEffectiveYieldBytes"], policy=self.policy)
        self.assertEqual(state["zeroYieldStreak"], 0)
        self.assertEqual(state["lastCooldownSeconds"], self.policy["baseCooldownSeconds"])

    def test_corrupted_backoff_streak_cannot_escape_bounded_integer_state(self):
        """A corrupt historical counter must not become a negative/float cooldown."""
        update = self.module["update_backoff"]
        for bad in (-10, True, 1.5, "10"):
            with self.subTest(value=bad):
                state = {"zeroYieldStreak": bad}
                update(state, now_ms=10_000, yield_bytes=0, policy=self.policy)
                self.assertEqual(state["zeroYieldStreak"], 1)
                self.assertIs(type(state["lastCooldownSeconds"]), int)
                self.assertIs(type(state["nextExpensiveProbeAfterMs"]), int)
                self.assertGreaterEqual(
                    state["nextExpensiveProbeAfterMs"], 10_000
                )

    def test_pg_carrier_rejects_legacy_cycle_before_lock_or_actuation(self):
        cycle = self.module["cycle"]
        namespace = cycle.__globals__
        with (
            patch.object(namespace["subprocess"], "run", return_value=SimpleNamespace(returncode=0, stdout="123\n")),
            patch.object(namespace["os"], "readlink", return_value="/usr/local/libexec/ordivon/ordivon-runtime-pg"),
            patch.dict(namespace, {"exclusive_lock": lambda _path: self.fail("legacy cycle acquired its lock on PG")}),
            self.assertRaisesRegex(RuntimeError, "legacy Runtime authority"),
        ):
            cycle(SimpleNamespace(lock_file=Path("/unused-pressure-lock")))

    def test_legacy_authority_requires_stable_native_pid_and_image(self):
        check = self.module["require_legacy_runtime_authority"]
        namespace = check.__globals__
        legacy = "/usr/local/libexec/ordivon/ordivon-runtime"
        pg = legacy + "-pg"
        for pids, images, accepted in (
            (["123", "123"], [legacy, legacy], True),
            (["123"], [pg], False),
            (["123", "124"], [legacy], False),
            (["123", "123"], [legacy, pg], False),
            (["0"], [], False),
            (["unknown"], [], False),
        ):
            with self.subTest(pids=pids, images=images):
                with (
                    patch.object(
                        namespace["subprocess"], "run",
                        side_effect=[SimpleNamespace(returncode=0, stdout=pid) for pid in pids],
                    ),
                    patch.object(namespace["os"], "readlink", side_effect=images),
                ):
                    if accepted:
                        check()
                    else:
                        with self.assertRaisesRegex(RuntimeError, "legacy Runtime authority"):
                            check()

    def test_pg_drift_after_cache_does_not_admit_legacy_reclaim(self):
        actuate = self.module["actuate"]
        calls = []
        def require_legacy():
            if calls:
                raise RuntimeError("legacy Runtime authority drift")

        with patch.dict(actuate.__globals__, {
            "require_legacy_runtime_authority": require_legacy,
            "run_json": lambda command, _accepted: calls.append(command) or {"status": "completed"},
            "physical_free_bytes": lambda _path: 1,
            "operator_program": lambda name: Path("/fake") / name,
        }):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                args = SimpleNamespace(
                    database=root / "registry.sqlite3",
                    registry_root=root,
                    runtime_store_root=root / "runtime",
                    env_file=root / "runtime.env",
                    cache_lock_file=root / "cache.lock",
                    reclaim_lock_file=root / "reclaim.lock",
                )
                with self.assertRaisesRegex(RuntimeError, "legacy Runtime authority"):
                    actuate(args, self.policy, root / "receipt", 1)
        self.assertEqual(len(calls), 1)
        self.assertIn("ordivon-runtime-cache", " ".join(map(str, calls[0])))

    def test_cycle_retains_partial_receipt_when_authority_drifts_after_cache(self):
        cycle = self.module["cycle"]
        calls = []
        guards = []

        def require_legacy():
            guards.append(len(calls))
            if calls:
                raise RuntimeError("controlled post-cache authority drift")

        def cache_fixture(command, _accepted):
            calls.append(command)
            self.assertIn("ordivon-runtime-cache", " ".join(command))
            destination = Path(command[command.index("--receipt-root") + 1])
            destination.mkdir(parents=True)
            (destination / "result.json").write_text(
                '{"fixture":"cache-receipt","status":"completed"}',
                encoding="utf-8",
            )
            return {"status": "completed"}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy_file = root / "policy.json"
            policy_file.write_text(
                json.dumps(dict(self.policy, hostStoragePath=str(root))), encoding="utf-8"
            )
            args = SimpleNamespace(
                policy_file=policy_file,
                state_file=root / "state.json",
                lock_file=root / "cycle.lock",
                database=root / "registry.sqlite3",
                busy_timeout_ms=100,
                receipt_root=root / "receipts",
                registry_root=root,
                runtime_store_root=root / "runtime",
                env_file=root / "runtime.env",
                cache_lock_file=root / "cache.lock",
                reclaim_lock_file=root / "reclaim.lock",
            )
            registry = {
                "jobsTotal": 100,
                "activeReservations": 0,
                "heldReservations": 0,
                "recoveryRequired": 0,
                "migrationVersion": 6,
            }
            with patch.dict(cycle.__globals__, {
                "require_legacy_runtime_authority": require_legacy,
                "physical_free_bytes": lambda _: 19 * 1024**3,
                "registry_signal": lambda *_: registry,
                "run_json": cache_fixture,
                "operator_program": lambda name: Path("/fixture") / name,
            }):
                result = cycle(args)
            receipt = Path(result["receipt"])
            self.assertEqual(result["status"], "partial")
            self.assertIsNone(result["action"])
            self.assertEqual(result["failures"], ["controlled post-cache authority drift"])
            self.assertEqual(guards, [0, 0, 1])
            self.assertEqual(len(calls), 1)
            self.assertTrue((receipt / "cache" / "result.json").is_file())
            self.assertFalse((receipt / "reclaim").exists())
            self.assertEqual(json.loads((receipt / "result.json").read_text()), result)
            self.assertEqual(json.loads(args.state_file.read_text()), result["stateAfter"])
            self.assertEqual(result["stateAfter"]["zeroYieldStreak"], 1)
            self.assertEqual(result["stateAfter"]["lastYieldBytes"], 0)

    def test_actuator_tries_cache_before_semantic_reclaim_and_skips_reclaim_when_enough(self):
        actuate = self.module["actuate"]
        globals_ = actuate.__globals__
        saved = {name: globals_[name] for name in ("run_json", "physical_free_bytes", "operator_program", "require_legacy_runtime_authority")}
        calls = []
        free_values = iter((31 * 1024**3, 31 * 1024**3))
        try:
            globals_["require_legacy_runtime_authority"] = lambda: None
            globals_["run_json"] = lambda command, accepted: calls.append(command) or {"status": "completed"}
            globals_["physical_free_bytes"] = lambda _path: next(free_values)
            globals_["operator_program"] = lambda name: Path("/fake") / name
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                args = SimpleNamespace(
                    database=root / "registry.sqlite3",
                    registry_root=root,
                    runtime_store_root=root / "runtime",
                    env_file=root / "runtime.env",
                    cache_lock_file=root / "cache.lock",
                    reclaim_lock_file=root / "reclaim.lock",
                )
                result = actuate(args, self.policy, root / "receipt", 26 * 1024**3)
            self.assertEqual(len(calls), 1)
            self.assertIn("ordivon-runtime-cache", " ".join(map(str, calls[0])))
            self.assertIsNone(result["reclaim"])
        finally:
            globals_.update(saved)

    def test_policy_integer_fields_fail_closed_on_coerced_json_values(self):
        """A disk-pressure safety threshold must never use a rounded or text value."""
        load = self.module["load_policy"]
        with tempfile.TemporaryDirectory() as temporary:
            policy_file = Path(temporary) / "policy.json"
            for bad in (1.9, 1.0, "21474836480", True):
                with self.subTest(value=bad):
                    candidate = dict(self.policy)
                    candidate["hardFloorBytes"] = bad
                    policy_file.write_text(json.dumps(candidate), encoding="utf-8")
                    with self.assertRaisesRegex(RuntimeError, "hardFloorBytes.*positive integer"):
                        load(policy_file)

    def test_historical_samples_drop_non_integer_and_negative_observations(self):
        """Malformed persisted samples cannot invent a consumption rate."""
        normalize = self.module["normalized_samples"]
        now = 20_000_000
        valid_before = now - 3_600_000
        state = {
            "samples": [
                {"observedAtMs": True, "freeBytes": 99 * 1024**3},
                {"observedAtMs": valid_before, "freeBytes": True},
                {"observedAtMs": valid_before, "freeBytes": -1},
                {"observedAtMs": valid_before + 1, "freeBytes": 0.5},
                {"observedAtMs": "19000000", "freeBytes": 10},
                {"observedAtMs": -10, "freeBytes": 10},
                {"observedAtMs": valid_before, "freeBytes": 28 * 1024**3},
            ]
        }
        samples = normalize(state, now, 26 * 1024**3, 7200)
        self.assertEqual(
            samples,
            [
                {"observedAtMs": valid_before, "freeBytes": 28 * 1024**3},
                {"observedAtMs": now, "freeBytes": 26 * 1024**3},
            ],
        )
        self.assertGreater(self.module["conservative_consumption_rate"](samples), 0)

    def test_pg_activity_is_not_compared_across_backend_or_writer_epoch(self):
        changed = self.module["registry_activity_changed"]
        pg = {
            "backend": "postgresql", "writerEpoch": "a" * 64,
            "jobsTotal": 3, "activeReservations": 1, "heldReservations": 0,
            "unfinishedTransitionAttempts": 0,
        }
        self.assertTrue(changed({"jobsTotal": 100, "migrationVersion": 6}, pg))
        self.assertTrue(changed({**pg, "writerEpoch": "b" * 64}, pg))
        self.assertFalse(changed(pg, pg))
        self.assertTrue(changed({**pg, "jobsTotal": 2}, pg))
        self.assertTrue(changed({**pg, "unfinishedTransitionAttempts": 1}, pg))

    def test_pg_observation_is_separate_from_effectful_legacy_cycle(self):
        parse = self.module["parse_args"]
        args = ["--env-file", "/tmp/pg.env", "--policy-file", "/tmp/policy.json",
                "--state-file", "/tmp/state.json"]
        self.assertEqual(parse(["observe-pg", *args]).command, "observe-pg")
        with self.assertRaises(SystemExit):
            parse(["cycle", *args])
        with self.assertRaises(SystemExit):
            parse(["observe-pg", *args, "--apply"])

    def test_pg_observation_native_qualified_epoch_counts_and_no_effect(self):
        # Reuse the existing native release fixture's private socket-only PG
        # cluster and exact Runtime schema, not a production connection.
        from scripts.tests.test_pg_operator_release import NativePgReleaseOperator

        class ScratchPg(NativePgReleaseOperator):
            root = db = postgres = log = None

        self.addCleanup(ScratchPg.tearDownClass)
        ScratchPg.setUpClass()
        scratch = ScratchPg.root
        base = scratch / "pressure.env"
        overlay = scratch / "pressure-overlay.env"
        base.write_text(
            f"ORDIVON_PG_DSN={ScratchPg.dsn}\nORDIVON_PG_SCHEMA=fresh\n"
            f"ORDIVON_PG_SOURCE_SHA256={'b' * 64}\n", encoding="utf-8",
        )
        # The base may be stale; later installed overlays are authoritative.
        overlay.write_text(f"ORDIVON_PG_SOURCE_SHA256={ScratchPg.source_sha}\n",
                           encoding="utf-8")
        policy = scratch / "pressure-policy.json"
        policy.write_text(json.dumps({**self.policy, "hostStoragePath": str(scratch)}),
                          encoding="utf-8")
        state = scratch / "pressure-state.json"
        command = [sys.executable, str(SCRIPT), "observe-pg",
                   "--env-file", str(base), "--env-overlay", str(overlay),
                   "--policy-file", str(policy), "--state-file", str(state)]

        def observe():
            result = subprocess.run(command, capture_output=True, text=True, timeout=25)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(state.exists(), "observe-pg must not persist or actuate")
            return json.loads(result.stdout)["decision"]["registrySignal"]

        initial = observe()
        self.assertEqual(initial, {
            "backend": "postgresql", "writerEpoch": ScratchPg.epoch,
            "jobsTotal": 0, "activeReservations": 0, "heldReservations": 0,
            "unfinishedTransitionAttempts": 0,
        })
        for n, attempt_state, reservation_state, finished in (
            (1, "starting", "active", None),
            (2, "succeeded", "held_orphaned", 20),
        ):
            ScratchPg.db.execute(
                "INSERT INTO jobs(job_id,principal,client_request_id,request_digest,"
                "operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,"
                "execution_plan_digest,created_at_ms,desired_state,current_attempt_id) "
                "VALUES(%s,'pressure-fixture',%s,'r','o','ws-pressure-fixture','{}','{}','p',"
                "10,'run',%s)", (f"j{n}", f"r{n}", f"a{n}"),
            )
            ScratchPg.db.execute(
                "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,"
                "termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,"
                "finished_at_ms) VALUES(%s,%s,1,%s,'natural','d','fixture',%s,10,%s)",
                (f"a{n}", f"j{n}", attempt_state, f"fixture{n}.service", finished),
            )
            ScratchPg.db.execute(
                "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,"
                "state,acquired_at_ms,state_observed_at_ms) VALUES(%s,%s,1,%s,10,10)",
                (f"v{n}", f"a{n}", reservation_state),
            )
        self.assertEqual(observe(), {
            **initial, "jobsTotal": 2, "activeReservations": 1, "heldReservations": 1,
            "unfinishedTransitionAttempts": 1,
        })
        # A stale base source and a mismatched physical epoch both fail closed.
        stale = subprocess.run(command[:5] + command[7:],
                               capture_output=True, text=True, timeout=25)
        self.assertEqual(stale.returncode, 1)
        self.assertIn("qualified PostgreSQL pressure observation unavailable", stale.stderr)
        ScratchPg.db.execute("UPDATE _stage_control SET source_sha256=%s WHERE id='epoch'",
                             ("c" * 64,))
        invalid = subprocess.run(command, capture_output=True, text=True, timeout=25)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("qualified PostgreSQL pressure observation unavailable", invalid.stderr)
        self.assertNotIn(ScratchPg.dsn, invalid.stderr)
        self.assertFalse(state.exists())

    def test_systemd_timer_samples_often_but_service_calls_only_controller(self):
        service = SERVICE.read_text(encoding="utf-8")
        timer = TIMER.read_text(encoding="utf-8")
        self.assertIn("ordivon-runtime-pressure-control cycle", service)
        self.assertNotIn("ordivon-runtime-reclaim apply", service)
        self.assertNotIn("ordivon-runtime-cache prune", service)
        self.assertIn("OnActiveSec=5min", timer)
        self.assertIn("OnUnitInactiveSec=5min", timer)


if __name__ == "__main__":
    unittest.main()
