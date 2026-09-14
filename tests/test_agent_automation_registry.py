from __future__ import annotations
import hashlib
import json
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
if importlib.util.find_spec("rfc8785") is None:
    raise unittest.SkipTest(
        "exact Agent Automation MCP runtime dependencies are not installed in the Harness owner environment"
    )
import rfc8785  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402
from agent_automation_registry import (  # noqa: E402
    AgentAutomationRegistryError,
    CampaignRegistry,
    CURRENT_MEDIA_TYPE,
    CURRENT_SCHEMA_PATH,
)


def spec():
    return {
        "campaignId": "campaign:mcp-test",
        "sharedPrompt": "Do one bounded task.",
        "roster": [{"agentId": "A01", "roleCard": "Verifier."}],
    }


class RegistryTests(unittest.TestCase):
    def test_schema_is_valid_draft_2020_12_and_contract_is_minimal(self):
        schema = json.loads(CURRENT_SCHEMA_PATH.read_text())
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["$id"], "urn:ordivon:schema:agent-campaign-spec:2")
        self.assertEqual(set(schema["required"]), {"campaignId", "sharedPrompt", "roster"})

    def test_register_is_jcs_content_addressed_and_exposes_oci_descriptor(self):
        with tempfile.TemporaryDirectory() as d:
            r = CampaignRegistry(Path(d))
            a = r.register(spec())
            b = r.register(spec())
            self.assertEqual(a["campaignRef"], b["campaignRef"])
            self.assertRegex(a["campaignRef"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual((a["disposition"], b["disposition"]), ("created", "existing"))
            p = r.resolve(a["campaignRef"])
            raw = p.read_bytes()
            value = json.loads(raw)
            self.assertEqual(raw, rfc8785.dumps(value))
            self.assertEqual(value, spec())
            descriptor = a["descriptor"]
            self.assertEqual(descriptor["mediaType"], CURRENT_MEDIA_TYPE)
            self.assertEqual(descriptor["size"], len(raw))
            self.assertEqual(descriptor["digest"], "sha256:" + hashlib.sha256(raw).hexdigest())
            self.assertEqual(r.inspect(a["campaignRef"])["descriptor"], descriptor)

    def test_semantic_change_changes_content_ref(self):
        with tempfile.TemporaryDirectory() as d:
            r = CampaignRegistry(Path(d))
            a = r.register(spec())
            v = spec()
            v["sharedPrompt"] = "Changed bounded task."
            b = r.register(v)
            self.assertNotEqual(a["campaignRef"], b["campaignRef"])

    def test_tampered_blob_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            r = CampaignRegistry(Path(d))
            a = r.register(spec())
            p = r.resolve(a["campaignRef"])
            p.write_bytes(b"{}")
            with self.assertRaises(AgentAutomationRegistryError):
                r.resolve(a["campaignRef"])

    def test_legacy_refs_and_fields_are_not_supported(self):
        with tempfile.TemporaryDirectory() as d:
            r = CampaignRegistry(Path(d))
            for ref in ("sha256:nope", "campaign-spec-v1:" + "1" * 64, "other:abc"):
                with self.assertRaises(AgentAutomationRegistryError):
                    r.resolve(ref)
            for field, value in (
                ("campaignRevision", "r1"),
                ("maxOccurrences", 1),
                ("maxConcurrentBirths", 1),
                ("boardTopic", "old"),
                ("lifecycleProtocol", "board-v1"),
            ):
                v = spec()
                v[field] = value
                with self.assertRaisesRegex(
                    AgentAutomationRegistryError, "JSON Schema validation failed"
                ):
                    r.register(v)
            v = spec()
            v["roster"][0]["occurrenceSlot"] = "old"
            with self.assertRaisesRegex(
                AgentAutomationRegistryError, "JSON Schema validation failed"
            ):
                r.register(v)

    def test_registry_lists_only_current_cas_blobs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            r = CampaignRegistry(root)
            r.register(spec())
            (r.root / "deadbeef.json").write_text("{}")
            census = r.list_registered()
            self.assertEqual(census["registered"], 1)
            self.assertEqual(census["issues"], [])
            self.assertTrue(census["campaigns"][0]["campaignRef"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
