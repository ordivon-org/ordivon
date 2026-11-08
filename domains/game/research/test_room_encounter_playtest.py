"""Falsification-only synthetic inputs: NEVER record these as Human evidence."""
import csv
import os
import tempfile
import unittest
from pathlib import Path

import room_encounter_playtest as study


class RoomPlaytestProtocol(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-game-study-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build = self.root / "synthetic-not-a-real-game.zip"
        self.build.write_bytes(b"SYNTHETIC UNIT TEST. Not a playable game or human observation.")
        self.output = self.root / "study"
        self.dest, self.digest, self.count = study.create_plan(
            self.build, "windows", 4, self.output)
        self.plan = self.output / "plan.csv"
        self.obs = self.output / "observations.csv"

    def rows(self):
        return study.read_rows(self.obs, study.read_template_columns())

    def save(self, rows):
        with self.obs.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=study.read_template_columns())
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def complete(row):
        row.update(consent_to_notes="yes", session_seconds="142",
                   outcome="win", controls_discovered="A|G|T|unlock",
                   forecast_interpretation="understood" if row["condition"] == "Trial" else "not_applicable",
                   parry_decision_observed="yes" if row["condition"] == "Trial" else "not_applicable",
                   keyboard_focus_issue="no",
                   blocked_or_clipped_content="unknown")

    def test_private_study_permissions(self):
        if os.name != "posix":
            self.skipTest("POSIX mode checks do not assert Windows ACLs")
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.plan.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.obs.stat().st_mode & 0o777, 0o600)

    def test_plan_exactly_balanced_random_anonymous_pairs(self):
        p = study.read_rows(self.plan, study.PLAN_COLUMNS)
        self.assertEqual(len(p), 8)
        self.assertEqual(len({x["session_code"] for x in p}), 8)
        self.assertEqual(len({x["pair_code"] for x in p}), 4)
        self.assertEqual(sum(x["period"] == "1" and x["condition"] == "Classic" for x in p), 2)
        self.assertEqual(sum(x["period"] == "1" and x["condition"] == "Trial" for x in p), 2)
        self.assertEqual({x["build_sha256"] for x in p}, {self.digest})
        self.assertTrue(all(row["consent_to_notes"] == "" for row in self.rows()))

    def test_blank_plan_is_never_human_evidence(self):
        data = study.inspect(self.plan, self.obs, self.build)
        self.assertEqual((data["planned"], data["pending"], len(data["complete"])), (8, 8, 0))
        self.assertIn("Human evidence: UNKNOWN", study.report(data))

    def test_consented_observer_entry_is_descriptive_only(self):
        rows = self.rows()
        self.complete(rows[0])
        self.save(rows)
        data = study.inspect(self.plan, self.obs)
        self.assertEqual(len(data["complete"]), 1)
        report = study.report(data)
        self.assertIn("Completed consenting observations: 1", report)
        self.assertIn("not a causal estimate", report)
        self.assertIn("n=0", report)

    def test_missing_is_not_negative_and_not_applicable_is_not_no(self):
        rows = self.rows()
        self.complete(rows[0])
        rows[0]["forecast_interpretation"] = "unknown"
        rows[0]["parry_decision_observed"] = "not_applicable"
        self.save(rows)
        report = study.report(study.inspect(self.plan, self.obs))
        self.assertIn("unknown=1/1", report)
        self.assertIn("not_applicable=1/1", report)
        self.assertIn("UNKNOWN and not_applicable are never counted as NO", report)

    def test_tampered_build_or_plan_condition_is_rejected(self):
        rows = self.rows()
        rows[0]["condition"] = "Trial" if rows[0]["condition"] == "Classic" else "Classic"
        self.save(rows)
        with self.assertRaisesRegex(ValueError, "mismatch"):
            study.inspect(self.plan, self.obs)
        self.save(self.rows()[1:])
        self.build.write_bytes(b"tampered release")
        with self.assertRaisesRegex(ValueError, "digest"):
            study.inspect(self.plan, self.obs, self.build)

    def test_duplicate_session_or_unplanned_forged_row_rejected(self):
        rows = self.rows()
        self.save([*rows, dict(rows[0])])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            study.inspect(self.plan, self.obs)
        rows[0]["session_code"] = "S-forged"
        self.save(rows)
        with self.assertRaisesRegex(ValueError, "unplanned"):
            study.inspect(self.plan, self.obs)

    def test_no_consent_has_no_notes_or_measurements(self):
        rows = self.rows()
        rows[0]["consent_to_notes"] = "no"
        self.save(rows)
        data = study.inspect(self.plan, self.obs)
        self.assertEqual(data["declined"], 1)
        self.assertEqual(len(data["complete"]), 0)
        rows[0]["post_session_feedback"] = "this should not be captured"
        self.save(rows)
        with self.assertRaisesRegex(ValueError, "declined"):
            study.inspect(self.plan, self.obs)

    def test_observation_without_consent_fails(self):
        rows = self.rows()
        rows[0]["outcome"] = "win"
        self.save(rows)
        with self.assertRaisesRegex(ValueError, "without consent"):
            study.inspect(self.plan, self.obs)

    def test_invalid_codings_and_csv_formula_injection_fail(self):
        rows = self.rows()
        self.complete(rows[0])
        rows[0]["forecast_interpretation"] = "maybe"
        self.save(rows)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            study.inspect(self.plan, self.obs)
        rows[0]["forecast_interpretation"] = "unknown"
        rows[0]["post_session_feedback"] = "=HYPERLINK('unsafe')"
        self.save(rows)
        with self.assertRaisesRegex(ValueError, "unsafe"):
            study.inspect(self.plan, self.obs)

    def test_plan_balance_or_personally_named_pair_rejected(self):
        rows = study.read_rows(self.plan, study.PLAN_COLUMNS)
        # Keep each pair structurally sound but replace BA with AB,
        # contradicting the promised counterbalanced assignment.
        for row in rows:
            row["condition"] = "Classic" if row["period"] == "1" else "Trial"
        with self.plan.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=study.PLAN_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "counterbalanced"):
            study.inspect(self.plan, self.obs)
        rows[0]["pair_code"] = "P-person-name"
        with self.plan.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=study.PLAN_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "anonymous plan codes"):
            study.inspect(self.plan, self.obs)

    def test_invalid_pair_sequence_and_no_overwrite(self):
        with self.assertRaises(FileExistsError):
            study.create_plan(self.build, "windows", 4, self.output)
        lines = study.read_rows(self.plan, study.PLAN_COLUMNS)
        lines[1]["period"] = lines[0]["period"]
        with self.plan.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=study.PLAN_COLUMNS)
            writer.writeheader()
            writer.writerows(lines)
        with self.assertRaisesRegex(ValueError, "AB or BA"):
            study.inspect(self.plan, self.obs)


if __name__ == "__main__":
    unittest.main()
