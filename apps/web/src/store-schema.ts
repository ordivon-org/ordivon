/** Owner-local initialization of the existing WebStore SQLite schema.

This function owns only the schema/bootstrap decision. WebStore retains the
single connection, transaction boundaries, admission and effect authority.
*/

import type { DatabaseSync } from "node:sqlite";

export function initializeWebStoreSchema(db: DatabaseSync): void {
    db.exec("PRAGMA foreign_keys = ON");
    db.exec("PRAGMA journal_mode = WAL");
    db.exec(`
      CREATE TABLE IF NOT EXISTS principals (
        principal_id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        created_at INTEGER NOT NULL
      );

      CREATE TABLE IF NOT EXISTS webauthn_credentials (
        credential_id TEXT PRIMARY KEY,
        principal_id TEXT NOT NULL,
        public_key BLOB NOT NULL,
        counter INTEGER NOT NULL,
        transports_json TEXT NOT NULL,
        device_type TEXT NOT NULL,
        backed_up INTEGER NOT NULL CHECK (backed_up IN (0, 1)),
        created_at INTEGER NOT NULL,
        last_used_at INTEGER NOT NULL,
        revoked_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE INDEX IF NOT EXISTS webauthn_credentials_principal
        ON webauthn_credentials(principal_id, revoked_at);

      CREATE TABLE IF NOT EXISTS webauthn_challenges (
        challenge_id TEXT PRIMARY KEY,
        purpose TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        challenge TEXT NOT NULL,
        payload_digest TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        consumed_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        token_hash TEXT NOT NULL UNIQUE,
        principal_id TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        authenticated_at INTEGER NOT NULL,
        last_seen_at INTEGER NOT NULL,
        idle_expires_at INTEGER NOT NULL,
        absolute_expires_at INTEGER NOT NULL,
        revoked_at INTEGER,
        authn_method TEXT NOT NULL,
        user_agent TEXT,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE INDEX IF NOT EXISTS sessions_principal
        ON sessions(principal_id, revoked_at, absolute_expires_at);

      CREATE TABLE IF NOT EXISTS canary_notes (
        note_id TEXT PRIMARY KEY,
        principal_id TEXT NOT NULL,
        content TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('DRAFT', 'PUBLISHED')),
        created_at INTEGER NOT NULL,
        published_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE TABLE IF NOT EXISTS agent_grants (
        grant_id TEXT PRIMARY KEY,
        grant_digest TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        audience TEXT NOT NULL,
        allowed_actions_json TEXT NOT NULL,
        resource_prefixes_json TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        max_risk_class TEXT NOT NULL,
        step_up_at_or_above TEXT NOT NULL,
        remaining_effects INTEGER NOT NULL CHECK (remaining_effects >= 0),
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        revision INTEGER NOT NULL CHECK (revision >= 1),
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE INDEX IF NOT EXISTS agent_grants_resolution
        ON agent_grants(agent_id, audience, active, expires_at);

      CREATE TABLE IF NOT EXISTS agent_effects (
        effect_id TEXT PRIMARY KEY,
        effect_digest TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        grant_id TEXT NOT NULL,
        action TEXT NOT NULL,
        resource TEXT NOT NULL,
        result_json TEXT NOT NULL,
        committed_at INTEGER NOT NULL,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id),
        FOREIGN KEY(grant_id) REFERENCES agent_grants(grant_id)
      );

      CREATE TABLE IF NOT EXISTS pending_effect_approvals (
        effect_id TEXT PRIMARY KEY,
        effect_digest TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE TABLE IF NOT EXISTS effect_approvals (
        effect_id TEXT PRIMARY KEY,
        effect_digest TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        credential_id TEXT NOT NULL,
        verified_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        consumed_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id),
        FOREIGN KEY(credential_id) REFERENCES webauthn_credentials(credential_id)
      );

      CREATE TABLE IF NOT EXISTS dpop_proofs (
        proof_hash TEXT PRIMARY KEY,
        expires_at INTEGER NOT NULL
      );

      CREATE INDEX IF NOT EXISTS dpop_proofs_expiry
        ON dpop_proofs(expires_at);

      CREATE TABLE IF NOT EXISTS audit_events (
        event_id TEXT PRIMARY KEY,
        principal_id TEXT,
        event_type TEXT NOT NULL,
        object_type TEXT,
        object_id TEXT,
        detail_json TEXT NOT NULL,
        created_at INTEGER NOT NULL
      );

      CREATE INDEX IF NOT EXISTS audit_events_principal_created
        ON audit_events(principal_id, created_at);
    `);
}
