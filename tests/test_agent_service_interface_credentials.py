from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from agent_service import open_agent_service
from agent_service.transport_credentials import CredentialHeaderMaterial
from agent_service.trust import IdentityProofObservation
from tests.test_agent_service_provider_adapters import (
    AllowPolicy,
    Delivery,
    DynamicNoEffectsReader,
    FakeRuntime,
    NoopArtifactReader,
    ReadyCarrier,
)


class ProofAdapter:
    def __init__(self) -> None:
        self.calls = 0

    def verify(self, request, credential_reference):
        self.calls += 1
        return IdentityProofObservation(
            authenticated=True,
            principal_id="principal:caller",
            issuer=credential_reference.issuer,
            auth_method="oauth2",
            expires_at_ms=9_999_999_999_999,
            evidence_ref=f"proof://{request.credential_reference_id}",
        )


class MaterialProvider:
    def __init__(self, *, secret: str = "secret-token") -> None:
        self.secret = secret
        self.calls = 0
        self.override_issuer = None
        self.override_resource = None
        self.override_scopes = None

    def resolve_headers(
        self,
        *,
        credential_reference,
        binding,
        security_scheme,
        identity_proof,
    ):
        self.calls += 1
        return CredentialHeaderMaterial(
            headers={"Authorization": f"Bearer {self.secret}"},
            issuer=self.override_issuer or credential_reference.issuer,
            resource=self.override_resource or credential_reference.resource,
            granted_scopes=(
                tuple(self.override_scopes)
                if self.override_scopes is not None
                else credential_reference.requested_scopes
            ),
            expires_at_ms=9_999_999_999_999,
            evidence_ref=f"material://{credential_reference.id}",
        )


class AgentServiceInterfaceCredentialsTests(unittest.TestCase):
    def _open(self, db: Path, *, proof_adapter=None, material_provider=None):
        service = open_agent_service(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=FakeRuntime(),
            artifact_reader=NoopArtifactReader(),
            policy_adapter=AllowPolicy(),
            delivery_adapters={"a2a-jsonrpc": Delivery(), "mcp": Delivery()},
            identity_proof_adapter=proof_adapter,
            effect_ledger_reader=DynamicNoEffectsReader(),
            credential_material_provider=material_provider,
        )
        self.addCleanup(service.close)
        return service

    def _agent(self, service, name, *, routes=None):
        definition = service.definitions.create(name)
        revision = service.revisions.create(definition.id, {
            "name": name,
            "skills": [{
                "id": "review",
                "name": "Review",
                "description": "review",
                "tags": ["review"],
                "inputModes": ["text/plain"],
                "outputModes": ["text/markdown"],
            }],
            "routes": routes or [],
        })
        identity = service.identities.create(definition.id, stable_name=name, description=name)
        instance = service.instances.create(f"request:{name}:r14", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision, identity, instance

    def _setup(
        self,
        service,
        *,
        a2a_version="1.0",
        mcp_version="2026-07-28",
        security=None,
    ):
        sr, si, inst = self._agent(service, "source-r14")
        tr, ti, _ = self._agent(
            service,
            "target-r14",
            routes=[
                {
                    "transport": "a2a-jsonrpc",
                    "protocolVersion": a2a_version,
                    "url": "https://agents.example.test/rpc",
                    "priority": 10,
                    "securityRequirements": security or {},
                },
                {
                    "transport": "mcp",
                    "protocolVersion": mcp_version,
                    "url": "https://agents.example.test/mcp",
                    "priority": 20,
                    "securityRequirements": security or {},
                },
            ],
        )
        a2a, mcp = tr.spec["routes"]
        task = service.tasks.create(
            description="r14",
            required_revision_id=sr.id,
            execution={"workspaceId":"x","executable":"/usr/bin/true","args":[],"cwdRelative":".","env":{}},
            acceptance={"kind":"runtime_artifact_text_contains","artifactKind":"review-markdown","value":"ACCEPTED"},
        )
        session = service.sessions.open(
            client_session_id="r14:session",
            initiator_identity_id=si.id,
        )
        envelope = service.delegations.create(
            client_delegation_id="r14:delegation",
            session_id=session.id,
            source_identity_id=si.id,
            source_instance_id=inst.id,
            target_identity_id=ti.id,
            target_revision_id=tr.id,
            task_id=task.id,
            capability_key="review",
            payload={"text":"review"},
            evidence_contract={"kind":"review-markdown"},
        )
        a2a_binding = service.routes.plan(
            envelope.id,
            client_policy_request_id="r14:policy",
            preferred_transports=["a2a-jsonrpc"],
        )
        mcp_binding = service.routes.plan(
            envelope.id,
            client_policy_request_id="r14:policy",
            preferred_transports=["mcp"],
        )
        return si, envelope, a2a, mcp, a2a_binding, mcp_binding

    def test_interface_requires_explicit_protocol_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp)/"s.db")
            with self.assertRaises(ValueError):
                self._setup(service, a2a_version=None)

    def test_protocol_version_is_immutable_interface_and_binding_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp)/"s.db")
            _, _, iface, _, binding, _ = self._setup(service)
            self.assertEqual(iface["protocolVersion"], "1.0")
            self.assertEqual(binding.protocol_version, "1.0")
            self.assertIn("protocol_version", binding.__dataclass_fields__)

    def test_a2a_protocol_version_must_be_major_minor_without_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp)/"s.db")
            with self.assertRaises(ValueError):
                self._setup(service, a2a_version="1.0.0")

    def test_mcp_protocol_version_must_be_date_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp)/"s.db")
            with self.assertRaises(ValueError):
                self._setup(service, mcp_version="latest")

    def _credential(self, service, source_identity, binding, *, resource="https://agents.example.test", scopes=("review.invoke",)):
        credential = service.credential_references.register(
            client_reference_id="r14:cred",
            provider="vault",
            reference="vault://ordivon/a2a/client",
            issuer="https://auth.example.test",
            resource=resource,
            requested_scopes=list(scopes),
        )
        proof = service.identity_proofs.verify(
            client_proof_request_id="r14:proof",
            identity_id=source_identity.id,
            credential_reference_id=credential.id,
            purpose="outbound-transport-auth",
        )
        record = service.transport_credentials.bind(
            client_binding_request_id="r14:transport-credential",
            binding_id=binding.id,
            security_scheme="oauth2",
            identity_proof_id=proof.id,
        )
        return credential, proof, record

    def test_transport_credential_binding_stores_references_not_secret(self):
        proof_adapter = ProofAdapter()
        provider = MaterialProvider(secret="TOP-SECRET-R14")
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp)/"s.db",
                proof_adapter=proof_adapter,
                material_provider=provider,
            )
            source_identity, _, _, _, binding, _ = self._setup(
                service, security={"oauth2":["review.invoke"]}
            )
            credential, proof, record = self._credential(service, source_identity, binding)
            self.assertEqual(record.binding_id, binding.id)
            self.assertEqual(record.credential_reference_id, credential.id)
            self.assertEqual(record.identity_proof_id, proof.id)
            self.assertFalse(hasattr(record, "access_token"))
            self.assertNotIn("TOP-SECRET-R14", repr(record))
            rows = service._connection.execute(
                """
                SELECT * FROM service_events
                WHERE aggregate_type LIKE 'TransportCredential%'
                """
            ).fetchall()
            self.assertNotIn("TOP-SECRET-R14", repr([dict(row) for row in rows]))

    def test_resource_or_scope_mismatch_blocks_before_secret_resolution(self):
        proof_adapter = ProofAdapter()
        provider = MaterialProvider()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp)/"s.db",
                proof_adapter=proof_adapter,
                material_provider=provider,
            )
            source_identity, _, _, _, binding, _ = self._setup(
                service, security={"oauth2":["review.invoke"]}
            )
            credential = service.credential_references.register(
                client_reference_id="r14:bad-resource",
                provider="vault",
                reference="vault://bad",
                issuer="https://auth.example.test",
                resource="https://other.example.test",
                requested_scopes=["review.invoke"],
            )
            proof = service.identity_proofs.verify(
                client_proof_request_id="r14:bad-resource-proof",
                identity_id=source_identity.id,
                credential_reference_id=credential.id,
                purpose="outbound-transport-auth",
            )
            with self.assertRaises(ValueError):
                service.transport_credentials.bind(
                    client_binding_request_id="r14:bad-resource-bind",
                    binding_id=binding.id,
                    security_scheme="oauth2",
                    identity_proof_id=proof.id,
                )
            self.assertEqual(provider.calls, 0)

    def test_identity_proof_must_belong_to_delegation_source(self):
        proof_adapter = ProofAdapter()
        provider = MaterialProvider()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp)/"s.db",
                proof_adapter=proof_adapter,
                material_provider=provider,
            )
            source_identity, _, _, _, binding, _ = self._setup(
                service, security={"oauth2":["review.invoke"]}
            )
            _, other_identity, _ = self._agent(service, "other-caller")
            credential = service.credential_references.register(
                client_reference_id="r14:other-cred",
                provider="vault",
                reference="vault://other",
                issuer="https://auth.example.test",
                resource="https://agents.example.test",
                requested_scopes=["review.invoke"],
            )
            proof = service.identity_proofs.verify(
                client_proof_request_id="r14:other-proof",
                identity_id=other_identity.id,
                credential_reference_id=credential.id,
                purpose="outbound-transport-auth",
            )
            with self.assertRaises(PermissionError):
                service.transport_credentials.bind(
                    client_binding_request_id="r14:other-bind",
                    binding_id=binding.id,
                    security_scheme="oauth2",
                    identity_proof_id=proof.id,
                )
            self.assertEqual(service.identities.get(source_identity.id).id, source_identity.id)

    def test_header_resolver_validates_material_and_keeps_secret_transient(self):
        proof_adapter = ProofAdapter()
        provider = MaterialProvider(secret="TRANSIENT-R14")
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp)/"s.db",
                proof_adapter=proof_adapter,
                material_provider=provider,
            )
            source_identity, _, _, _, binding, _ = self._setup(
                service, security={"oauth2":["review.invoke"]}
            )
            self._credential(service, source_identity, binding)
            headers = service.credential_headers(binding)
            self.assertEqual(headers["Authorization"], "Bearer TRANSIENT-R14")
            self.assertNotIn("TRANSIENT-R14", repr(service.credential_headers))
            tables = {
                row["name"]
                for row in service._connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            rendered = " ".join(
                repr([dict(row) for row in service._connection.execute(f"SELECT * FROM {table}").fetchall()])
                for table in tables
                if table.startswith(("transport_", "credential_", "identity_"))
            )
            self.assertNotIn("TRANSIENT-R14", rendered)

    def test_material_issuer_resource_or_scope_drift_fails_closed(self):
        proof_adapter = ProofAdapter()
        provider = MaterialProvider()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp)/"s.db",
                proof_adapter=proof_adapter,
                material_provider=provider,
            )
            source_identity, _, _, _, binding, _ = self._setup(
                service, security={"oauth2":["review.invoke"]}
            )
            self._credential(service, source_identity, binding)
            provider.override_issuer = "https://evil.example.test"
            with self.assertRaises(ValueError):
                service.credential_headers(binding)
            provider.override_issuer = None
            provider.override_scopes = ()
            with self.assertRaises(PermissionError):
                service.credential_headers(binding)

    def test_exact_transport_credential_binding_replay_is_historical(self):
        proof_adapter = ProofAdapter()
        provider = MaterialProvider()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp)/"s.db",
                proof_adapter=proof_adapter,
                material_provider=provider,
            )
            source_identity, _, _, _, binding, _ = self._setup(
                service, security={"oauth2":["review.invoke"]}
            )
            _, proof, first = self._credential(service, source_identity, binding)
            second = service.transport_credentials.bind(
                client_binding_request_id="r14:transport-credential",
                binding_id=binding.id,
                security_scheme="oauth2",
                identity_proof_id=proof.id,
            )
            self.assertEqual(first.id, second.id)


    def test_transport_security_scheme_cannot_rebind_to_different_evidence(self):
        proof_adapter = ProofAdapter()
        provider = MaterialProvider()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp)/"s.db",
                proof_adapter=proof_adapter,
                material_provider=provider,
            )
            source_identity, _, _, _, binding, _ = self._setup(
                service, security={"oauth2":["review.invoke"]}
            )
            self._credential(service, source_identity, binding)
            second_credential = service.credential_references.register(
                client_reference_id="r14:cred:conflict",
                provider="vault",
                reference="vault://ordivon/a2a/client-conflict",
                issuer="https://auth.example.test",
                resource="https://agents.example.test",
                requested_scopes=["review.invoke"],
            )
            second_proof = service.identity_proofs.verify(
                client_proof_request_id="r14:proof:conflict",
                identity_id=source_identity.id,
                credential_reference_id=second_credential.id,
                purpose="outbound-transport-auth",
            )
            with self.assertRaisesRegex(
                RuntimeError,
                "already bound to different credential evidence",
            ):
                service.transport_credentials.bind(
                    client_binding_request_id="r14:transport-credential:conflict",
                    binding_id=binding.id,
                    security_scheme="oauth2",
                    identity_proof_id=second_proof.id,
                )


    def test_legacy_interface_table_fails_closed_until_destructive_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp)/"s.db"
            connection = sqlite3.connect(db)
            connection.execute(
                """
                CREATE TABLE agent_interface_advertisements (
                    id TEXT PRIMARY KEY,
                    revision_id TEXT,
                    transport TEXT,
                    protocol_version TEXT,
                    url TEXT,
                    priority INTEGER,
                    security_requirements_json TEXT,
                    created_at_ns INTEGER
                )
                """
            )
            connection.commit()
            connection.close()
            with self.assertRaises(RuntimeError):
                self._open(db)

    def test_credential_requested_scope_must_cover_binding_requirement(self):
        proof_adapter = ProofAdapter()
        provider = MaterialProvider()
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(
                Path(tmp)/"s.db",
                proof_adapter=proof_adapter,
                material_provider=provider,
            )
            source_identity, _, _, _, binding, _ = self._setup(
                service,
                security={"oauth2":["review.invoke"]},
            )
            credential = service.credential_references.register(
                client_reference_id="r14:no-scope",
                provider="vault",
                reference="vault://ordivon/no-scope",
                issuer="https://auth.example.test",
                resource="https://agents.example.test",
                requested_scopes=[],
            )
            proof = service.identity_proofs.verify(
                client_proof_request_id="r14:no-scope-proof",
                identity_id=source_identity.id,
                credential_reference_id=credential.id,
                purpose="outbound-transport-auth",
            )
            with self.assertRaises(PermissionError):
                service.transport_credentials.bind(
                    client_binding_request_id="r14:no-scope-bind",
                    binding_id=binding.id,
                    security_scheme="oauth2",
                    identity_proof_id=proof.id,
                )
            self.assertEqual(provider.calls, 0)


if __name__ == "__main__":
    unittest.main()
