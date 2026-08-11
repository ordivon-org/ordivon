from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.research_validity import (
    TrialLedger,
    build_null_registration,
    calibration_experiment,
    evaluate_sealed_holdout,
    run_registered_search,
    search_replay_correction,
    seed_commitment,
    validate_registration,
)


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

    def test_trial_ledger_is_hash_chained_and_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trials.sqlite"
            ledger = TrialLedger(path, search_id="experiment:test")
            ledger.append("attempt:1", "candidate:1", "trial.proposed", {"x": 1})
            ledger.append("attempt:1", "candidate:1", "trial.evaluated", {"z": 2.0})
            self.assertTrue(ledger.verify())
            self.assertEqual(ledger.summary()["eventCounts"]["trial.evaluated"], 1)
            with self.assertRaises(sqlite3.DatabaseError):
                ledger.db.execute("DELETE FROM trial_events")
            ledger.close()

    def test_visible_search_never_contains_holdout_seed_and_freezes_winner(self) -> None:
        registration = self.registration(budget=300)
        winner = run_registered_search(registration)
        self.assertEqual(winner["holdoutStatus"], "sealed-not-observed")
        self.assertNotIn("sealed-fixture", str(winner))
        self.assertEqual(winner["attemptBudget"], 300)
        self.assertLessEqual(winner["naiveOneSidedP"], 1.0)

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
