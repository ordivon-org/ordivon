"""Consumer tests for an external-world delta proposal, including negative cases."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "catalogs/knowledge/scripts"))
from external_world_delta import examine

SAMPLE = ROOT / "catalogs/knowledge/observations/boe-rate-20261105.json"


class ExternalWorldDeltaTests(unittest.TestCase):
    def example(self):
        return json.loads(SAMPLE.read_text(encoding="utf-8"))

    def test_real_official_rate_baseline_to_new_claim(self):
        errors, result = examine(self.example())
        self.assertEqual(errors, [])
        self.assertEqual(result["valueChange"], "0.25")
        self.assertEqual(result["basisPointChange"], "25.00")
        self.assertEqual(result["knowledgeVerdict"], "OWNER_REVIEW_REQUIRED")
        self.assertFalse(result["domainAcceptanceEstablished"])
        self.assertFalse(result["sourceContentVerifiedByThisProgram"])
        self.assertFalse(result["productionApplied"])

    def test_replay_is_byte_stable(self):
        a = examine(self.example())[1]
        b = examine(self.example())[1]
        self.assertEqual(a, b)
        self.assertEqual(a["sourcePacketDigest"], b["sourcePacketDigest"])

    def test_wrong_delta_fails_closed(self):
        record = self.example()
        record["declaredDelta"] = "0.50"
        self.assertTrue(any("declaredDelta" in v for v in examine(record)[0]))

    def test_baseline_bigger_than_new_rejects_wrong_declared_sign(self):
        record = self.example()
        record["current"]["value"] = "3.50"
        self.assertTrue(examine(record)[0])

    def test_rollback_or_approval_cannot_come_from_catalog(self):
        record = self.example()
        record["ownerVerdict"] = "APPROVED"
        record["productionApplied"] = True
        self.assertTrue(any("cannot issue" in v for v in examine(record)[0]))

    def test_future_claim_and_inverted_event_time_rejected(self):
        record = self.example()
        record["current"]["reportedAt"] = "2026-11-07"
        record["current"]["eventAt"] = "2026-11-08"
        errors, _ = examine(record)
        self.assertTrue(any("reportedAt" in v for v in errors))

    def test_unknown_event_time_is_not_invented(self):
        record = self.example()
        record["current"]["eventAt"] = None
        errors, output = examine(record)
        self.assertEqual(errors, [])
        self.assertIsNone(output["eventAt"])

    def test_mismatched_dimensions_rejected(self):
        record = self.example()
        record["baseline"]["unit"] = "basis-point"
        self.assertTrue(any("mismatched" in v for v in examine(record)[0]))

    def test_unverified_consumer_cannot_be_claimed_as_accepted(self):
        record = self.example()
        record["affectedConsumers"] = [{
            "owner": "domains/capital",
            "consumerRef": "hypothetical-model",
            "acceptance": "SATISFIED",
        }]
        self.assertTrue(any("consumer acceptance" in v for v in examine(record)[0]))

    def test_non_https_source_rejected(self):
        record = self.example()
        record["current"]["evidence"]["url"] = "http://example.invalid/claim"
        self.assertTrue(any("HTTPS" in v for v in examine(record)[0]))


    def test_independent_confirmation_cannot_be_self_certified(self):
        record = self.example()
        record["claimStatus"] = "INDEPENDENTLY_CONFIRMED"
        self.assertTrue(any("claimStatus" in v for v in examine(record)[0]))

    def test_evidence_cannot_be_published_after_check(self):
        record = self.example()
        record["current"]["evidence"]["publishedAt"] = "2026-11-09"
        self.assertTrue(any("publication" in v for v in examine(record)[0]))

    def test_revised_at_after_check_rejected(self):
        record = self.example()
        record["current"]["revisedAt"] = "2026-11-07"
        self.assertTrue(any("revisedAt" in v for v in examine(record)[0]))

    def test_nonfinite_number_rejected(self):
        record = self.example()
        record["current"]["value"] = "NaN"
        self.assertTrue(any("finite" in v for v in examine(record)[0]))


    def test_state_transition_without_numeric_inference(self):
        packet = self.example()
        for record, value in ((packet["baseline"], "MAINTAIN"), (packet["current"], "INCREASE")):
            record.update(valueType="state", value=value, predicate="MPC-decision-kind", unit="decision")
        packet["declaredDelta"] = None
        errors, output = examine(packet)
        self.assertEqual(errors, [])
        self.assertEqual(output["changeKind"], "STATE_CHANGED")
        self.assertEqual(output["baselineValue"], "MAINTAIN")
        self.assertEqual(output["currentValue"], "INCREASE")
        self.assertIsNone(output["basisPointChange"])
        self.assertFalse(output["domainAcceptanceEstablished"])

    def test_state_change_rejects_forged_numeric_delta(self):
        packet = self.example()
        for slot in ("baseline", "current"):
            packet[slot]["valueType"] = "state"
        self.assertTrue(any("arithmetic" in x for x in examine(packet)[0]))

    def test_mixed_value_types_rejected(self):
        packet = self.example()
        packet["current"]["valueType"] = "state"
        self.assertTrue(any("valueType" in x for x in examine(packet)[0]))


if __name__ == "__main__":
    unittest.main()
