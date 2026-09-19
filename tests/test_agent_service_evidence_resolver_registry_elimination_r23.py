from __future__ import annotations

import unittest
from pathlib import Path

import agent_service.evidence as evidence


ROOT = Path(__file__).resolve().parents[1]


class EvidenceResolverRegistryEliminationR23Tests(unittest.TestCase):
    def test_registry_class_and_service_facade_are_deleted(self) -> None:
        self.assertFalse(hasattr(evidence, "EvidenceResolverRegistry"))
        source = (ROOT / "agent_service" / "evidence.py").read_text(encoding="utf-8")
        self.assertNotIn("self.evidence_resolvers", source)

    def test_resolution_is_a_pure_module_function(self) -> None:
        self.assertTrue(callable(evidence._resolve_evidence))
        self.assertTrue(hasattr(evidence, "RuntimeArtifactReader"))
        self.assertTrue(callable(evidence._verify_evidence_semantics))


if __name__ == "__main__":
    unittest.main()
