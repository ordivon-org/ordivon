"""R58: actual Host reference, Work, Attention and health module boundaries.

Source-only contract tests detect accidental re-coupling. Database transactional
and MCP negative/positive tests remain the authority for behavior.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.errors import ActorRefNotFound
from ordivon_host_v2.health.diagnostics import HostStatusQueries
from ordivon_host_v2.references.actor_refs import ActorReferenceLookup, ActorReferenceRegistry
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.service import HostV2
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_store import WorkStore


def test_actor_reference_lookup_is_shared_not_three_copies() -> None:
    assert SocialStore._require_actor is ActorReferenceLookup._require_actor
    assert ActorReferenceStore.declare_actor is ActorReferenceRegistry.declare_actor
    assert not hasattr(WorkStore, "declare_actor")
    assert not hasattr(SocialStore, "declare_actor")
    assert not hasattr(AttentionStore, "declare_actor")


def test_nonexistent_actor_is_domain_reference_error_not_access_denial() -> None:
    class FakeConnection:
        def execute(self, query: str, args: tuple[str]) -> FakeConnection:
            assert query == "SELECT 1 FROM actor_refs WHERE actor_ref=%s"
            assert args == ("actor:missing",)
            return self

        def fetchone(self) -> None:
            return None

    with pytest.raises(ActorRefNotFound):
        ActorReferenceLookup._require_actor(FakeConnection(), "actor:missing")


def test_doctor_is_read_only_health_facet_not_public_business_mutation() -> None:
    assert HostV2.status is HostStatusQueries.status
    assert "initialize" in HostV2.__dict__
    assert "status" not in HostV2.__dict__

    root = Path(__file__).resolve().parents[1] / "src" / "ordivon_host_v2"
    business = (root / "service.py").read_text(encoding="utf-8")
    references = (root / "references" / "actor_refs.py").read_text(encoding="utf-8")
    health = (root / "health" / "diagnostics.py").read_text(encoding="utf-8")
    assert "FROM work_snapshots" not in business
    assert "FROM messages" not in business
    assert "SELECT schema_version FROM host_v2_schema" in business
    assert "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY" in health
    assert "INSERT INTO actor_refs" in references
    assert "CloudflareAccess" not in references
    assert "AuthZen" not in references
