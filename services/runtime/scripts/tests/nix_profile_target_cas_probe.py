"""Explicit native PG/Nix test of a proposed resource-owner CAS contract.

Only the existing disposable fixture gets a test-only owner row. This is not
a new Runtime registry, migration, deployer, or authorization API. The exact
natural owner must supply its existing resource coordinate and authority.
"""
from __future__ import annotations

import os
import signal
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from nix_profile_generation_probe import NativeNixGenerationProbe, op

# Allocate a new monotonic revision at intent admission; physical settlement
# does not mint a revision. Even a positively aborted/rolled-back operation
# consumes its revision, preventing ABA. A pending effect can never be stolen.
RESERVE = """
UPDATE r17_target_owner_probe
SET revision=revision+1,pending_effect=%s,pending_content=%s
WHERE target_identity=%s AND authority_epoch=%s
  AND revision=%s AND active_content=%s AND pending_effect IS NULL
RETURNING revision
"""
SETTLE = """
UPDATE r17_target_owner_probe
SET active_content=pending_content,pending_effect=NULL,pending_content=NULL
WHERE target_identity=%s AND authority_epoch=%s
  AND revision=%s AND active_content=%s
  AND pending_effect=%s AND pending_content=%s
RETURNING revision
"""


class NativeTargetCasProbe(NativeNixGenerationProbe):
    def setUp(self) -> None:
        super().setUp()
        self.target = str(self.profile)
        self.db.execute("""
            CREATE TABLE r17_target_owner_probe(
                target_identity text PRIMARY KEY,
                authority_epoch text NOT NULL,
                revision bigint NOT NULL CHECK(revision>=0),
                active_content text NOT NULL,
                pending_effect text,
                pending_content text,
                CHECK((pending_effect IS NULL)=(pending_content IS NULL))
            )
        """)
        self.addCleanup(lambda: self.db.execute("DROP TABLE r17_target_owner_probe"))
        self.db.execute(
            "INSERT INTO r17_target_owner_probe VALUES(%s,%s,0,%s,NULL,NULL)",
            (self.target, self.epoch, self.a),
        )

    def reserve(self, effect, desired, revision, previous, *, target=None, epoch=None):
        with op.pg_connection(self.dsn, "fresh") as conn:
            with conn.transaction():
                row = conn.execute(RESERVE, (
                    effect, desired, target or self.target, epoch or self.epoch,
                    revision, previous,
                )).fetchone()
            return None if row is None else row["revision"]

    def settle(self, effect, desired, revision, previous, *, target=None, epoch=None):
        # Mechanical switch is an external effect. This is an observation of
        # exact selected bytes AFTER the synchronous native command returned;
        # an absent child/manager or a matching path alone is not sufficient
        # for general crash-recovery authorization.
        if self.selected()[1] != desired:
            return None
        self.assert_complete(desired, "A" if desired == self.a else "B")
        with op.pg_connection(self.dsn, "fresh") as conn:
            with conn.transaction():
                row = conn.execute(SETTLE, (
                    target or self.target, epoch or self.epoch, revision,
                    previous, effect, desired,
                )).fetchone()
            return None if row is None else row["revision"]

    def standing(self):
        return self.db.execute(
            "SELECT revision,active_content,pending_effect,pending_content "
            "FROM r17_target_owner_probe WHERE target_identity=%s", (self.target,),
        ).fetchone()

    def test_native_rollback_same_pointer_rejects_stale_owner_revision(self):
        original = self.selected()
        with op.DEPLOY["exclusive_lock"](self.args.lock_file):
            self.assertEqual(self.reserve("effect-B", self.b, 0, self.a), 1)
            self.assertIsNone(self.settle("effect-B", self.b, 1, self.a))
            self.switch(self.b)
            self.assertEqual(self.settle("effect-B", self.b, 1, self.a), 1)
            self.assertEqual(self.reserve("effect-A", self.a, 1, self.b), 2)
            self.nix("nix-env", "--profile", str(self.profile), "--rollback")
            self.assertEqual(self.selected(), original)
            self.assertEqual(self.settle("effect-A", self.a, 2, self.b), 2)
            self.assertIsNone(self.reserve("stale", self.b, 0, self.a))
            self.assertEqual(self.reserve("fresh", self.b, 2, self.a), 3)
        print("NATIVE_ABA: exact original profile link, owner revision 2; stale 0 denied", flush=True)

    def test_concurrent_expected_revision_allocates_one_effect(self):
        start = threading.Barrier(2)

        def compete(effect):
            start.wait(timeout=8)
            return effect, self.reserve(effect, self.b, 0, self.a)

        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(compete, ("racing-A", "racing-B")))
        winners = [(effect, revision) for effect, revision in results if revision is not None]
        self.assertEqual(len(winners), 1)
        winner, revision = winners[0]
        self.assertEqual(revision, 1)
        self.assertEqual(self.standing()["pending_effect"], winner)
        self.assertIsNone(self.reserve("newer", self.b, 1, self.a))
        with op.DEPLOY["exclusive_lock"](self.args.lock_file):
            self.switch(self.b)
            loser = next(effect for effect, value in results if value is None)
            self.assertIsNone(self.settle(loser, self.b, 1, self.a))
            self.assertEqual(self.settle(winner, self.b, 1, self.a), 1)
        print("NATIVE_PG_RACE: exactly one of two independent sessions admitted", flush=True)

    def test_identity_and_epoch_are_not_inferred_from_equal_content(self):
        self.assertIsNone(self.reserve("foreign", self.b, 0, self.a, target="wrong-target"))
        self.assertIsNone(self.reserve("foreign", self.b, 0, self.a, epoch="wrong-epoch"))
        self.assertEqual(self.reserve("exact", self.b, 0, self.a), 1)
        with op.DEPLOY["exclusive_lock"](self.args.lock_file):
            self.switch(self.b)
            self.assertIsNone(self.settle("exact", self.b, 1, self.a, epoch="wrong-epoch"))
            self.assertIsNone(self.settle("exact", self.b, 1, self.a, target="wrong-target"))
            self.assertEqual(self.settle("exact", self.b, 1, self.a), 1)
        self.assertIsNone(self.settle("exact", self.b, 1, self.a))
        print("NATIVE_SCOPE: wrong target/epoch and duplicate settlement denied", flush=True)

    def test_killed_after_native_switch_keeps_pending_until_exact_reconciliation(self):
        pid = os.fork()
        if pid == 0:
            try:
                with op.DEPLOY["exclusive_lock"](self.args.lock_file):
                    with op.pg_connection(self.dsn, "fresh") as conn:
                        op.dispatch_claim(conn, self.args)
                    if self.reserve(self.args.effect_id, self.b, 0, self.a) != 1:
                        os._exit(96)
                    self.switch(self.b)  # native command already returned
                    os.kill(os.getpid(), signal.SIGKILL)
            except BaseException:
                os._exit(99)
            os._exit(98)
        _, status = os.waitpid(pid, 0)
        self.assertTrue(os.WIFSIGNALED(status))
        self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)
        self.assert_complete(self.b, "B")
        self.assertEqual(self.standing()["active_content"], self.a)
        self.assertEqual(self.standing()["pending_effect"], self.args.effect_id)
        self.assertIsNone(self.reserve("superseding", self.a, 1, self.a))
        with op.pg_connection(self.dsn, "fresh") as conn:
            with self.assertRaisesRegex(RuntimeError, "dispatch was already committed"):
                op.dispatch_claim(conn, self.args)
        # A separate observer holds the writer fence and has a positive
        # synchronous-child terminal witness in this exact test. Observe the
        # physical pointer; do NOT invoke nix-env a second time.
        with op.DEPLOY["exclusive_lock"](self.args.lock_file):
            before = self.selected()
            self.assertEqual(self.settle(self.args.effect_id, self.b, 1, self.a), 1)
            self.assertEqual(self.selected(), before)
        self.assertIsNone(self.standing()["pending_effect"])
        self.assertEqual(self.standing()["active_content"], self.b)
        # The pre-existing Runtime Job is still intentionally unresolved:
        # test-only owner-row settlement is not the real release ABI.
        self.assertIsNone(self.db.execute(
            "SELECT resolution FROM jobs WHERE job_id=%s",(self.job_id,),
        ).fetchone()["resolution"])
        print("NATIVE_CRASH: pending held, reissue denied, exact readback no second effect", flush=True)


if __name__ == "__main__":
    names = (
        "test_native_rollback_same_pointer_rejects_stale_owner_revision",
        "test_concurrent_expected_revision_allocates_one_effect",
        "test_identity_and_epoch_are_not_inferred_from_equal_content",
        "test_killed_after_native_switch_keeps_pending_until_exact_reconciliation",
    )
    suite = unittest.TestSuite(NativeTargetCasProbe(name) for name in names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun == len(names)
                     and not result.skipped else 1)
