from __future__ import annotations

import json
import runpy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

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

    def test_policy_separates_hard_floor_from_soft_trigger(self):
        self.assertEqual(self.policy["hardFloorBytes"], 20 * 1024**3)
        self.assertEqual(self.policy["softTriggerBytes"], 28 * 1024**3)
        self.assertGreater(self.policy["softTriggerBytes"], self.policy["hardFloorBytes"])

    def test_above_soft_trigger_is_cheap_no_action(self):
        decision = self.decision(30 * 1024**3)
        self.assertFalse(decision["action"])
        self.assertEqual(decision["reason"], "NORMAL_ABOVE_SOFT_TRIGGER")

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

    def test_actuator_tries_cache_before_semantic_reclaim_and_skips_reclaim_when_enough(self):
        actuate = self.module["actuate"]
        globals_ = actuate.__globals__
        saved = {name: globals_[name] for name in ("run_json", "physical_free_bytes", "operator_program")}
        calls = []
        free_values = iter((31 * 1024**3, 31 * 1024**3))
        try:
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
