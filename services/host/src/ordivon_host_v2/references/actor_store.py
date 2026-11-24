"""Actor reference declaration authority, separate from Work state mutation.

Social ActorRef is a stable Host graph reference, never an authenticated
Principal or a Security authorization. Reuses the sole Host PostgreSQL store.
"""
from __future__ import annotations

from ..postgres_connections import HostPostgresConnections
from .actor_refs import ActorReferenceRegistry


class ActorReferenceStore(ActorReferenceRegistry, HostPostgresConnections):
    """PG-backed actor.declare adapter with no Work/Social/Attention ownership."""
