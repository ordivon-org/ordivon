from __future__ import annotations

import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg

from ordivon_studio.research.null_attack_scoring import score_null_attack
from ordivon_studio.research.search_calibration import (
    calibration_experiment,
    evaluate_sealed_holdout,
    run_registered_search,
    search_replay_correction,
)
from ordivon_studio.research.trial_ledger import TrialLedger
from ordivon_studio.research.trial_registration import (
    build_null_registration,
    seed_commitment,
    validate_registration,
)

PG_DSN = os.environ.get("ORDIVON_MEDIA_TRIAL_TEST_DSN")


class ResearchValidityTest(unittest.TestCase):
    def registration(self, *, mode: str = "static", budget: int = 200) -> dict:
        return build_null_registration(
            mode=mode,
            attempt_budget=budget,
            visible_seed="visible-fixture",
            holdout_seed_commitment=seed_commitment("sealed-fixture"),
        )

    def test_registration_keeps_outcomes_typed_and_seed_sealed(self) -> None:
        registration = self.registration()
        roles = [item["role"] for item in registration["outcomes"]]
        self.assertEqual(roles.count("primary"), 1)
        self.assertIn("guardrail", roles)
        self.assertNotIn("seed", registration["holdout"])
        self.assertNotIn("sealed-fixture", str(registration))
        self.assertEqual(validate_registration(registration)["registrationDigest"], registration["registrationDigest"])

    def test_sqlite_path_cannot_be_accepted_as_pg_proof(self) -> None:
        """A local SQLite path must not silently masquerade as a PostgreSQL DSN."""
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "PostgreSQL DSN"):
                TrialLedger(Path(temporary) / "legacy.sqlite", search_id="experiment:refuse")



    @unittest.skipUnless(PG_DSN, "real PostgreSQL test DSN is required")
    def test_trial_ledger_is_hash_chained_and_append_only(self) -> None:
        search_id = f"experiment:test:{uuid4().hex}"
        ledger = TrialLedger(PG_DSN, search_id=search_id)
        try:
            ledger.append("attempt:1", "candidate:1", "trial.proposed", {"x": 1})
            ledger.append("attempt:1", "candidate:1", "trial.evaluated", {"z": 2.0})
            self.assertTrue(ledger.verify())
            self.assertEqual(ledger.summary()["eventCounts"]["trial.evaluated"], 1)
            with self.assertRaises(psycopg.Error):
                ledger.db.execute(
                    "DELETE FROM ordivon_media_trial.trial_events WHERE search_id=%s",
                    (search_id,),
                )
            self.assertTrue(ledger.verify())
        finally:
            ledger.close()

    @unittest.skipUnless(PG_DSN, "real PostgreSQL test DSN is required")
    def test_pg_catalog_rejects_disabled_append_only_trigger(self) -> None:
        """A PostgreSQL table without its active UPDATE/DELETE fence is not admitted."""
        ledger = TrialLedger(PG_DSN, search_id=f"experiment:trigger-proof:{uuid4().hex}")
        try:
            class RollbackProbe(Exception):
                pass

            with self.assertRaises(RollbackProbe):
                with ledger.db.transaction():
                    ledger.db.execute(
                        "ALTER TABLE ordivon_media_trial.trial_events "
                        "DISABLE TRIGGER trial_events_no_mutation"
                    )
                    with self.assertRaisesRegex(ValueError, "append-only trigger"):
                        ledger._verify_schema()
                    raise RollbackProbe()
        finally:
            ledger.close()

    @unittest.skipUnless(PG_DSN, "real PostgreSQL test DSN is required")
    def test_pg_catalog_rejects_missing_event_hash_uniqueness(self) -> None:
        """Reused PostgreSQL storage cannot silently weaken event identity."""
        ledger = TrialLedger(PG_DSN, search_id=f"experiment:constraint-proof:{uuid4().hex}")
        try:
            class RollbackProbe(Exception):
                pass

            with self.assertRaises(RollbackProbe):
                with ledger.db.transaction():
                    ledger.db.execute(
                        "ALTER TABLE ordivon_media_trial.trial_events "
                        "DROP CONSTRAINT trial_events_event_hash_key"
                    )
                    with self.assertRaisesRegex(ValueError, "event uniqueness"):
                        ledger._verify_schema()
                    raise RollbackProbe()
        finally:
            ledger.close()

    @unittest.skipUnless(PG_DSN, "real PostgreSQL test DSN is required")
    def test_parallel_trial_appends_commit_one_complete_hash_chain(self) -> None:
        search_id = f"experiment:parallel:{uuid4().hex}"

        def append(index: int) -> str:
            ledger = TrialLedger(PG_DSN, search_id=search_id)
            try:
                return ledger.append(
                    f"attempt:{index}", f"candidate:{index}",
                    "trial.proposed", {"index": index},
                )
            finally:
                ledger.close()

        with ThreadPoolExecutor(max_workers=8) as pool:
            events = list(pool.map(append, range(20)))
        self.assertEqual(len(set(events)), 20)
        ledger = TrialLedger(PG_DSN, search_id=search_id)
        try:
            self.assertTrue(ledger.verify())
            self.assertEqual(ledger.summary()["attemptCount"], 20)
            self.assertEqual(ledger.summary()["uniqueCandidateCount"], 20)
        finally:
            ledger.close()



    def test_visible_search_never_contains_holdout_seed_and_freezes_winner(self) -> None:
        registration = self.registration(budget=300)
        winner = run_registered_search(registration)
        self.assertEqual(winner["holdoutStatus"], "sealed-not-observed")
        self.assertNotIn("sealed-fixture", str(winner))
        self.assertEqual(winner["attemptBudget"], 300)
        self.assertLessEqual(winner["naiveOneSidedP"], 1.0)

    def test_frozen_winner_mutation_is_rejected_by_both_consumers(self) -> None:
        """Counterexample: a reselected candidate cannot inherit the old digest."""
        registration = self.registration(budget=12)
        winner = run_registered_search(registration)
        forged = dict(winner)
        forged["candidateId"] = "creative-candidate://forged-without-winner-rehash"
        with self.assertRaisesRegex(ValueError, "frozen winner digest mismatch"):
            evaluate_sealed_holdout(registration, forged, holdout_seed="sealed-fixture")
        with self.assertRaisesRegex(ValueError, "frozen winner digest mismatch"):
            search_replay_correction(
                registration, forged, replay_seed="replay-fixture", replay_count=100
            )

    @unittest.skipUnless(PG_DSN, "real PostgreSQL test DSN is required")
    def test_sealed_holdout_reuses_same_frozen_pg_selection_atomically(self) -> None:
        """No orphan reveal, missing-ledger fallback or second holdout replay."""
        from ordivon_studio.research.grounded_contracts import canonical_digest

        registration = build_null_registration(
            mode="static",
            attempt_budget=12,
            visible_seed="pg-frozen-visible",
            holdout_seed_commitment=seed_commitment("sealed-fixture"),
            experiment_id=f"experiment:pg-frozen:{uuid4().hex}",
        )
        ledger = TrialLedger(PG_DSN, search_id=registration["experimentId"])
        try:
            winner = run_registered_search(registration, ledger)
            before = ledger.summary()
            with self.assertRaisesRegex(ValueError, "requires its original PostgreSQL ledger"):
                evaluate_sealed_holdout(registration, winner, holdout_seed="sealed-fixture")
            self.assertEqual(ledger.summary(), before)

            # Even rehashing a forged winner cannot pass the native PostgreSQL
            # selected-event/source identity, which is checked under the lock.
            forged = dict(winner)
            forged["candidateId"] = "creative-candidate://forged-and-rehashed"
            forged["winnerDigest"] = canonical_digest(
                {key: value for key, value in forged.items() if key != "winnerDigest"}
            )
            with self.assertRaisesRegex(ValueError, "selected candidate differs"):
                evaluate_sealed_holdout(
                    registration, forged, holdout_seed="sealed-fixture", ledger=ledger
                )
            self.assertEqual(ledger.summary(), before)

            result = evaluate_sealed_holdout(
                registration, winner, holdout_seed="sealed-fixture", ledger=ledger
            )
            self.assertTrue(result["trialLedger"]["eventChainValid"])
            self.assertEqual(result["trialLedger"]["eventCounts"]["trial.holdout_revealed"], 1)
            with self.assertRaisesRegex(ValueError, "no longer matches frozen winner"):
                evaluate_sealed_holdout(
                    registration, winner, holdout_seed="sealed-fixture", ledger=ledger
                )
            self.assertEqual(ledger.summary()["eventCounts"]["trial.holdout_revealed"], 1)
        finally:
            ledger.close()

    def test_holdout_requires_exact_committed_seed(self) -> None:
        registration = self.registration()
        winner = run_registered_search(registration)
        with self.assertRaises(ValueError):
            evaluate_sealed_holdout(registration, winner, holdout_seed="wrong")
        result = evaluate_sealed_holdout(registration, winner, holdout_seed="sealed-fixture")
        self.assertEqual(result["holdoutStatus"], "revealed-contaminated-for-future-tuning")
        self.assertEqual(result["holdoutSeedCommitment"], seed_commitment("sealed-fixture"))

    def test_search_replay_correction_uses_full_registered_search(self) -> None:
        registration = self.registration(mode="adaptive", budget=200)
        winner = run_registered_search(registration)
        correction = search_replay_correction(registration, winner, replay_seed="replay-fixture", replay_count=200)
        self.assertEqual(correction["searchMode"], "adaptive")
        self.assertEqual(correction["attemptBudget"], 200)
        self.assertGreater(correction["searchCorrectedP"], 0.0)
        self.assertLessEqual(correction["searchCorrectedP"], 1.0)

    def test_score_rejects_changed_calibration_or_holdout_source(self) -> None:
        """Score must consume the actual frozen proof artifacts, not edited JSON."""
        registration = self.registration(budget=12)
        winner = run_registered_search(registration)
        correction = search_replay_correction(
            registration, winner, replay_seed="source-score-replay", replay_count=100
        )
        holdout = evaluate_sealed_holdout(
            registration, winner, holdout_seed="sealed-fixture"
        )
        calibration = calibration_experiment(
            mode="static", budgets=[12], worlds=100, reference_replays=400,
            seed="source-score-calibration",
        )
        input_args = {
            "registration": registration, "winner": winner, "correction": correction,
            "holdout": holdout, "calibration": calibration,
        }
        score = score_null_attack(**input_args)
        self.assertEqual(score["registrationDigest"], registration["registrationDigest"])

        forged_holdout = {**holdout, "holdoutOneSidedP": 0.00001}
        with self.assertRaisesRegex(ValueError, "sealed holdout source digest mismatch"):
            score_null_attack(**{**input_args, "holdout": forged_holdout})

        forged_calibration = {
            **calibration,
            "rows": {
                **calibration["rows"],
                "12": {**calibration["rows"]["12"], "naiveFalsePositiveRate": 1.0},
            },
        }
        with self.assertRaisesRegex(ValueError, "calibration source digest mismatch"):
            score_null_attack(**{**input_args, "calibration": forged_calibration})

    def test_null_calibration_exposes_best_of_n_and_corrects_it(self) -> None:
        result = calibration_experiment(
            mode="static",
            budgets=[10, 100, 1000],
            worlds=140,
            reference_replays=500,
            seed="unit-calibration",
        )
        rows = result["rows"]
        self.assertGreater(rows["1000"]["naiveFalsePositiveRate"], 0.90)
        self.assertLess(rows["1000"]["searchCorrectedFalsePositiveRate"], 0.12)
        self.assertLess(rows["1000"]["sealedHoldoutFalsePositiveRate"], 0.12)
        self.assertGreater(rows["1000"]["meanSelectedVisibleZ"], rows["10"]["meanSelectedVisibleZ"])


if __name__ == "__main__":
    unittest.main()
