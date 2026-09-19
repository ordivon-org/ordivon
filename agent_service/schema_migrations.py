from __future__ import annotations

import sqlite3

from sqlite_utils import Database, Migrations


MIGRATIONS = Migrations("agent-service")

LEGACY_TABLES = (
    "task_verifications",
    "board_projection_receipts",
    "agent_interface_advertisements",
    "policy_decisions",
    "delivery_receipts",
    "remote_delivery_observations",
    "identity_proof_records",
    "remote_task_verifications",
    "execution_claim_transfers",
    "replay_safety_decisions",
    "execution_quiescence_proofs",
    "transport_credential_bindings",
    "effect_authorization_decisions",
)

CURRENT_TABLE_DDL = (
    """CREATE TABLE IF NOT EXISTS agent_definitions (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS agent_revisions (
        id TEXT PRIMARY KEY,
        definition_id TEXT NOT NULL REFERENCES agent_definitions(id),
        spec_json TEXT NOT NULL,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS agent_instances (
        id TEXT PRIMARY KEY,
        client_request_id TEXT NOT NULL UNIQUE,
        revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
        state TEXT NOT NULL,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS desired_placements (
        id TEXT PRIMARY KEY,
        agent_instance_id TEXT NOT NULL UNIQUE REFERENCES agent_instances(id),
        desired_state TEXT NOT NULL,
        observed_state TEXT NOT NULL,
        evidence_ref TEXT,
        created_at_ns INTEGER NOT NULL,
        updated_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS service_events (
        id TEXT PRIMARY KEY,
        aggregate_type TEXT NOT NULL,
        aggregate_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at_ns INTEGER NOT NULL,
        UNIQUE(aggregate_type, aggregate_id, sequence)
    )""",
    """CREATE TABLE IF NOT EXISTS service_tasks (
        id TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        required_revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
        execution_json TEXT NOT NULL,
        acceptance_json TEXT NOT NULL,
        state TEXT NOT NULL,
        failure_reason TEXT,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS service_assignments (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL UNIQUE REFERENCES service_tasks(id),
        agent_instance_id TEXT NOT NULL REFERENCES agent_instances(id),
        state TEXT NOT NULL,
        runtime_job_id TEXT,
        client_request_id TEXT NOT NULL UNIQUE,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS service_goals (
        id TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        state TEXT NOT NULL,
        failure_reason TEXT,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS goal_task_links (
        goal_id TEXT NOT NULL REFERENCES service_goals(id),
        task_id TEXT NOT NULL UNIQUE REFERENCES service_tasks(id),
        ordinal INTEGER NOT NULL,
        created_at_ns INTEGER NOT NULL,
        PRIMARY KEY(goal_id, task_id),
        UNIQUE(goal_id, ordinal)
    )""",
    """CREATE TABLE IF NOT EXISTS task_dependencies (
        task_id TEXT NOT NULL REFERENCES service_tasks(id),
        depends_on_task_id TEXT NOT NULL REFERENCES service_tasks(id),
        created_at_ns INTEGER NOT NULL,
        PRIMARY KEY(task_id, depends_on_task_id),
        CHECK(task_id <> depends_on_task_id)
    )""",
    """CREATE TABLE IF NOT EXISTS agent_identities (
        id TEXT PRIMARY KEY,
        definition_id TEXT NOT NULL UNIQUE REFERENCES agent_definitions(id),
        stable_name TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS semantic_sessions (
        id TEXT PRIMARY KEY,
        client_session_id TEXT NOT NULL UNIQUE,
        initiator_identity_id TEXT NOT NULL REFERENCES agent_identities(id),
        goal_id TEXT REFERENCES service_goals(id),
        state TEXT NOT NULL CHECK(state IN ('OPEN', 'CLOSED')),
        created_at_ns INTEGER NOT NULL,
        closed_at_ns INTEGER
    )""",
    """CREATE TABLE IF NOT EXISTS session_items (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES semantic_sessions(id),
        client_item_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        role TEXT NOT NULL,
        content_json TEXT NOT NULL,
        producer_identity_id TEXT REFERENCES agent_identities(id),
        created_at_ns INTEGER NOT NULL,
        UNIQUE(session_id, client_item_id),
        UNIQUE(session_id, sequence)
    )""",
    """CREATE TABLE IF NOT EXISTS delegation_envelopes (
        id TEXT PRIMARY KEY,
        client_delegation_id TEXT NOT NULL UNIQUE,
        session_id TEXT NOT NULL REFERENCES semantic_sessions(id),
        source_identity_id TEXT NOT NULL REFERENCES agent_identities(id),
        source_instance_id TEXT NOT NULL REFERENCES agent_instances(id),
        target_identity_id TEXT NOT NULL REFERENCES agent_identities(id),
        target_revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
        task_id TEXT NOT NULL REFERENCES service_tasks(id),
        capability_key TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        evidence_contract_json TEXT NOT NULL,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS transport_bindings (
        id TEXT PRIMARY KEY,
        delegation_id TEXT NOT NULL REFERENCES delegation_envelopes(id),
        policy_receipt_id TEXT NOT NULL,
        policy_revision TEXT NOT NULL,
        granted_permissions_json TEXT NOT NULL,
        interface_id TEXT NOT NULL,
        transport TEXT NOT NULL,
        protocol_version TEXT,
        endpoint TEXT NOT NULL,
        delivery_request_id TEXT NOT NULL UNIQUE,
        security_requirements_json TEXT NOT NULL,
        created_at_ns INTEGER NOT NULL,
        UNIQUE(delegation_id, policy_receipt_id, interface_id)
    )""",
    """CREATE TABLE IF NOT EXISTS credential_references (
        id TEXT PRIMARY KEY,
        client_reference_id TEXT NOT NULL UNIQUE,
        provider TEXT NOT NULL,
        reference TEXT NOT NULL,
        issuer TEXT NOT NULL,
        resource TEXT NOT NULL,
        requested_scopes_json TEXT NOT NULL,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS task_execution_claims (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL UNIQUE REFERENCES service_tasks(id),
        mode TEXT NOT NULL CHECK(mode IN ('LOCAL_ASSIGNMENT', 'REMOTE_BINDING')),
        owner_id TEXT NOT NULL,
        created_at_ns INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS execution_quiescence_requests (
        id TEXT PRIMARY KEY,
        client_quiescence_request_id TEXT NOT NULL UNIQUE,
        task_id TEXT NOT NULL REFERENCES service_tasks(id),
        binding_id TEXT NOT NULL REFERENCES transport_bindings(id),
        state TEXT NOT NULL CHECK(state IN ('REQUESTED', 'PROVED', 'NOT_PROVED')),
        created_at_ns INTEGER NOT NULL,
        updated_at_ns INTEGER NOT NULL
    )""",
)


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }


def _column_names(db: Database, table: str) -> set[str]:
    return {row[1] for row in db.execute(f"PRAGMA table_info({table})")}


def validate_schema_compatibility(connection: sqlite3.Connection) -> None:
    present = _table_names(connection)
    for table in LEGACY_TABLES:
        if table in present:
            raise RuntimeError(
                f"legacy {table} schema is unsupported; "
                "perform explicit destructive migration before opening this revision"
            )


@MIGRATIONS(name="001_current_schema")
def current_schema(db: Database) -> None:
    for ddl in CURRENT_TABLE_DDL:
        db.execute(ddl)


@MIGRATIONS(name="002_request_identity")
def request_identity(db: Database) -> None:
    columns = _column_names(db, "agent_instances")
    if "birth_request_id" in columns and "client_request_id" in columns:
        raise RuntimeError(
            "agent_instances contains both legacy and current request identity columns"
        )
    if "birth_request_id" in columns:
        db.execute(
            "ALTER TABLE agent_instances "
            "RENAME COLUMN birth_request_id TO client_request_id"
        )
    elif "client_request_id" not in columns:
        raise RuntimeError("agent_instances has no request identity column")


@MIGRATIONS(name="003_transport_protocol_version")
def transport_protocol_version(db: Database) -> None:
    columns = _column_names(db, "transport_bindings")
    if "protocol_version" not in columns:
        db.execute(
            "ALTER TABLE transport_bindings ADD COLUMN protocol_version TEXT"
        )


def apply_schema_migrations(connection: sqlite3.Connection) -> None:
    validate_schema_compatibility(connection)
    MIGRATIONS.apply(Database(connection))
