from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from campaign_materialization import CampaignLaunchSpec, RoleCard, campaign_census, compile_campaign  # noqa: E402


class CampaignCensusFreshnessTests(unittest.TestCase):
    def _spec(self) -> CampaignLaunchSpec:
        return CampaignLaunchSpec(
            campaign_id="campaign:freshness",
            shared_prompt="Do one bounded task.",
            roster=(RoleCard(agent_id="A01", role_card="Verifier."),),
        )

    def test_projects_effect_generation_and_updated_at_ms_from_ledger(self):
        spec = self._spec()
        request = compile_campaign(spec)["A01"]
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "birth.sqlite"
            db = sqlite3.connect(ledger)
            db.execute(
                """
                CREATE TABLE requests(
                    request_id TEXT PRIMARY KEY,
                    request_digest TEXT NOT NULL,
                    standing TEXT NOT NULL,
                    provider_coordinate TEXT,
                    effect_generation INTEGER,
                    updated_at_ms INTEGER
                )
                """
            )
            db.execute(
                "INSERT INTO requests VALUES (?,?,?,?,?,?)",
                (request.request_id, request.request_digest, "bound", None, 7, 123456789),
            )
            db.commit()
            db.close()

            census = campaign_census(spec, ledger)
            row = census["occurrences"][0]
            self.assertEqual(row["effectGeneration"], 7)
            self.assertEqual(row["updatedAtMs"], 123456789)

    def test_unrecorded_occurrence_has_no_fabricated_freshness(self):
        spec = self._spec()
        with tempfile.TemporaryDirectory() as d:
            census = campaign_census(spec, Path(d) / "missing.sqlite")
            row = census["occurrences"][0]
            self.assertIsNone(row["effectGeneration"])
            self.assertIsNone(row["updatedAtMs"])


if __name__ == "__main__":
    unittest.main()

class CampaignCompilationStandardBoundaryTests(unittest.TestCase):
    def test_campaign_compiles_directly_to_carrier_requests_without_occurrence_wrapper(self):
        spec = CampaignLaunchSpec(
            campaign_id="campaign:standard-boundary",
            shared_prompt="Do the work",
            roster=(RoleCard(agent_id="A01", role_card="Researcher"),),
        )
        compiled = compile_campaign(spec)
        self.assertIsInstance(compiled, dict)
        self.assertEqual(set(compiled), {"A01"})
        request = compiled["A01"]
        self.assertEqual(request.request_id, request.request_id)
        self.assertFalse(hasattr(request, "materialization_request"))

    def test_current_carrier_request_has_no_successor_occurrence_compatibility_field(self):
        from dataclasses import fields
        from conversation_relay_carrier import CarrierMaterializationRequest

        self.assertNotIn("successor_occurrence_id", {field.name for field in fields(CarrierMaterializationRequest)})
