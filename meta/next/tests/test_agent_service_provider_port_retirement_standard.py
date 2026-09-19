from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path

import agent_service


RETIRED = {
    "ExecutionQuiescenceAdapter": "agent_service.failover",
    "ReplaySafetyAdapter": "agent_service.failover",
    "BoardAdapter": "agent_service.goals",
    "EffectLedgerReader": "agent_service.provider_adapters",
    "RemoteArtifactReader": "agent_service.remote_evidence",
    "CredentialMaterialProvider": "agent_service.transport_credentials",
    "IdentityProofAdapter": "agent_service.trust",
    "RemoteDeliveryObserver": "agent_service.trust",
}


class ProviderPortRetirementStandardTests(unittest.TestCase):
    def test_retired_nominal_port_brands_are_absent_from_modules_and_package(self) -> None:
        for name, module_name in RETIRED.items():
            with self.subTest(name=name):
                module = importlib.import_module(module_name)
                self.assertFalse(hasattr(module, name))
                self.assertFalse(hasattr(agent_service, name))

    def test_production_classes_do_not_inherit_retired_port_brands(self) -> None:
        offenders = []
        for path in Path("agent_service").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                bases = {ast.unparse(base) for base in node.bases}
                hit = bases & RETIRED.keys()
                if hit:
                    offenders.append((path.name, node.name, sorted(hit)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()


class StructuralBoundaryValidationTests(unittest.TestCase):
    def test_incomplete_providers_fail_at_composition_boundaries(self) -> None:
        from agent_service.failover import (
            ExecutionQuiescenceCoordinator,
            ReplaySafetyCoordinator,
        )
        from agent_service.goals import GoalBoardProjector
        from agent_service.provider_adapters import EffectLedgerReplaySafetyAdapter
        from agent_service.remote_evidence import RemoteArtifactEvidenceResolver
        from agent_service.transport_credentials import BoundCredentialHeaderProvider
        from agent_service.trust import IdentityProofCoordinator, RemoteCorrelationReconciler

        with self.assertRaises(TypeError):
            GoalBoardProjector(None, None, object())
        with self.assertRaises(TypeError):
            EffectLedgerReplaySafetyAdapter(object())
        with self.assertRaises(TypeError):
            RemoteArtifactEvidenceResolver({"mcp": object()})
        with self.assertRaises(TypeError):
            BoundCredentialHeaderProvider(
                events=None,
                credential_references=None,
                identity_proofs=None,
                material_provider=object(),
            )
        with self.assertRaises(TypeError):
            IdentityProofCoordinator(None, None, None, object())
        with self.assertRaises(TypeError):
            RemoteCorrelationReconciler(None, None, None, {"mcp": object()})
        with self.assertRaises(TypeError):
            ExecutionQuiescenceCoordinator(
                connection=None,
                tasks=None,
                events=None,
                claims=None,
                delegations=None,
                bindings=None,
                receipts=None,
                observations=None,
                requests=None,
                adapters={"mcp": object()},
            )
        with self.assertRaises(TypeError):
            ReplaySafetyCoordinator(
                connection=None,
                tasks=None,
                events=None,
                claims=None,
                delegations=None,
                bindings=None,
                receipts=None,
                observations=None,
                adapter=object(),
            )
