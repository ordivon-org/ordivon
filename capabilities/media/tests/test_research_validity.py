from __future__ import annotations

import json
import os
import runpy
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg

PG_DSN = os.environ.get('ORDIVON_MEDIA_TRIAL_TEST_DSN')

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

    @unittest.skipUnless(PG_DSN, "real PostgreSQL test DSN is required")
    def test_legacy_sqlite_event_chain_migrates_once_to_pg_without_mutating_source(self) -> None:
        migrate = runpy.run_path(
            str(Path(__file__).resolve().parents[1] / "scripts" / "migrate-r6-trials.py")
        )["migrate"]
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "legacy.sqlite"
            source = sqlite3.connect(db)
            source.execute(
                "CREATE TABLE trial_events("
                "seq INTEGER PRIMARY KEY, event_id TEXT, search_id TEXT, attempt_id TEXT,"
                "candidate_id TEXT, event_type TEXT, payload_json TEXT, prev_hash TEXT,"
                "event_hash TEXT)"
            )
            from ordivon_studio.grounded_meaning import canonical_digest

            search_id = f"experiment:legacy:{uuid4().hex}"
            prior = None
            for i in range(3):
                payload = {"trial": i}
                semantic = {
                    "searchId": search_id, "attemptId": f"attempt:{i}",
                    "candidateId": f"candidate:{i}", "eventType": "trial.proposed",
                    "payload": payload, "prevHash": prior,
                }
                event_hash = canonical_digest(semantic)
                source.execute(
                    "INSERT INTO trial_events VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        i + 1, "trial-event://" + event_hash.removeprefix("sha256:"),
                        search_id, f"attempt:{i}", f"candidate:{i}", "trial.proposed",
                        json.dumps(payload), prior, event_hash,
                    ),
                )
                prior = event_hash
            source.commit()
            source.close()
            before = db.read_bytes()
            result = migrate(db, PG_DSN)
            self.assertEqual(result["events"], 3)
            self.assertTrue(result["destinationChainValid"])
            self.assertEqual(db.read_bytes(), before)
            with self.assertRaisesRegex(ValueError, "already contains events"):
                migrate(db, PG_DSN)

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
