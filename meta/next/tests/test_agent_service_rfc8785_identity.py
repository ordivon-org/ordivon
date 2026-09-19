from __future__ import annotations

from tests.agent_service_test_support import open_current

import hashlib
import tempfile
import unittest
from pathlib import Path

import rfc8785

from agent_service.carriers.agent_automation import _digest
from agent_service.delivery import _route_profiles_from_revision_spec
from agent_service.local_effect_readers import BrowserlessTurnEffectCoordinate, _evidence_ref
from agent_service.slice1 import ProviderObservation
from agent_service.transport_credentials import _transport_credential_scheme_coordinate


class PlainCarrier:
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(placement_id, "UNKNOWN", None)


class RFC8785IdentityTests(unittest.TestCase):
    def test_runtime_dependency_is_pinned_to_current_rfc8785_release(self) -> None:
        lines = {
            line.strip()
            for line in Path("config/agent-service-mcp-requirements.txt").read_text().splitlines()
            if line.strip() and not line.startswith("#")
        }
        self.assertIn("rfc8785==0.1.4", lines)

    def test_agent_revision_identity_uses_jcs_number_serialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = open_current(Path(tmp) / "s.db", carrier_adapter=PlainCarrier())
            self.addCleanup(service.close)
            definition = service.definitions.create("jcs")
            spec = {"threshold": 1.0, "nested": {"b": 2, "a": 1}}
            revision = service.revisions.create(definition.id, spec)

            material = definition.id.encode() + b"\0" + rfc8785.dumps(spec)
            expected = "arev_" + hashlib.sha256(material).hexdigest()
            self.assertEqual(revision.id, expected)

    def test_route_profile_identity_uses_jcs_utf16_property_order(self) -> None:
        spec = {
            "routes": [
                {
                    "transport": "mcp",
                    "protocolVersion": "2026-07-28",
                    "url": "https://example.test/mcp",
                    "priority": 0,
                    "securityRequirements": {
                        "\ue000": [],
                        "😀": [],
                    },
                }
            ]
        }
        [profile] = _route_profiles_from_revision_spec("arev:jcs", spec)
        material = {
            "revisionId": "arev:jcs",
            "transport": "mcp",
            "protocolVersion": "2026-07-28",
            "url": "https://example.test/mcp",
            "priority": 0,
            "securityRequirements": {
                "\ue000": [],
                "😀": [],
            },
        }
        expected = "iface_" + hashlib.sha256(rfc8785.dumps(material)).hexdigest()
        self.assertEqual(profile["profileId"], expected)

    def test_carrier_evidence_digest_uses_jcs(self) -> None:
        value = {"n": 1.0, "\ue000": "bmp", "😀": "astral"}
        self.assertEqual(
            _digest(value),
            "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest(),
        )

    def test_transport_credential_coordinate_uses_jcs(self) -> None:
        material = ["bind:😀", "scheme:\ue000"]
        self.assertEqual(
            _transport_credential_scheme_coordinate(*material),
            hashlib.sha256(rfc8785.dumps(material)).hexdigest(),
        )

    def test_browserless_evidence_reference_uses_jcs(self) -> None:
        ledger = Path("/tmp/agent-service-jcs-ledger.sqlite")
        coordinate = BrowserlessTurnEffectCoordinate(
            turn_request_id="turn:jcs",
            prompt_digest="sha256:" + "a" * 64,
            target_coordinate="chatgpt://conversation/jcs",
        )
        payload = {
            "ledgerPathDigest": "sha256:"
            + hashlib.sha256(str(ledger.resolve()).encode()).hexdigest(),
            "turnRequestId": coordinate.turn_request_id,
            "promptDigest": coordinate.prompt_digest,
            "targetCoordinate": coordinate.target_coordinate,
            "state": "COMPLETED",
            "updatedAtMs": 1,
            "receiptJsonDigest": None,
        }
        expected = (
            "browserless-turn-ledger://sha256:"
            + hashlib.sha256(rfc8785.dumps(payload)).hexdigest()
        )
        self.assertEqual(
            _evidence_ref(
                ledger,
                coordinate,
                state="COMPLETED",
                updated_at_ms=1,
                receipt_json=None,
            ),
            expected,
        )


    def test_browserless_turn_receipt_verifier_uses_jcs(self) -> None:
        import json
        from agent_service.local_effect_readers import _validate_receipt

        coordinate = BrowserlessTurnEffectCoordinate(
            turn_request_id="turn:jcs-receipt",
            prompt_digest="sha256:" + "b" * 64,
            target_coordinate="chatgpt://conversation/jcs-receipt",
        )
        material = {
            "turnRequestId": coordinate.turn_request_id,
            "promptDigest": coordinate.prompt_digest,
            "targetResource": coordinate.target_coordinate,
            "standing": "COMPLETED",
            "timing": 1.0,
            "\ue000": "bmp",
            "😀": "astral",
        }
        receipt = dict(material)
        receipt["receiptDigest"] = (
            "sha256:" + hashlib.sha256(rfc8785.dumps(material)).hexdigest()
        )
        self.assertEqual(
            _validate_receipt(json.dumps(receipt, ensure_ascii=False), coordinate),
            receipt,
        )

if __name__ == "__main__":
    unittest.main()
