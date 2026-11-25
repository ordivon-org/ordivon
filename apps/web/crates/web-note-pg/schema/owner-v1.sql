-- Candidate full owner schema, install only into an empty isolated schema.
-- JSON remains TEXT; do not normalize evidence with JSONB.
CREATE TABLE principals (
  principal_id TEXT COLLATE "C" PRIMARY KEY,
  user_name TEXT COLLATE "C" NOT NULL UNIQUE,
  display_name TEXT COLLATE "C" NOT NULL,
  created_at BIGINT NOT NULL
);

CREATE TABLE webauthn_credentials (
  credential_id TEXT COLLATE "C" PRIMARY KEY,
  principal_id TEXT COLLATE "C" NOT NULL,
  public_key BYTEA NOT NULL,
  counter BIGINT NOT NULL,
  transports_json TEXT COLLATE "C" NOT NULL,
  device_type TEXT COLLATE "C" NOT NULL,
  backed_up BIGINT NOT NULL CHECK (backed_up IN (0, 1)),
  created_at BIGINT NOT NULL,
  last_used_at BIGINT NOT NULL,
  revoked_at BIGINT,
  FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
);

CREATE INDEX webauthn_credentials_principal
  ON webauthn_credentials(principal_id, revoked_at);

CREATE TABLE webauthn_challenges (
  challenge_id TEXT COLLATE "C" PRIMARY KEY,
  purpose TEXT COLLATE "C" NOT NULL,
  principal_id TEXT COLLATE "C" NOT NULL,
  challenge TEXT COLLATE "C" NOT NULL,
  payload_digest TEXT COLLATE "C" NOT NULL,
  payload_json TEXT COLLATE "C" NOT NULL,
  expires_at BIGINT NOT NULL,
  consumed_at BIGINT,
  FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
);

CREATE TABLE sessions (
  session_id TEXT COLLATE "C" PRIMARY KEY,
  token_hash TEXT COLLATE "C" NOT NULL UNIQUE,
  principal_id TEXT COLLATE "C" NOT NULL,
  created_at BIGINT NOT NULL,
  authenticated_at BIGINT NOT NULL,
  last_seen_at BIGINT NOT NULL,
  idle_expires_at BIGINT NOT NULL,
  absolute_expires_at BIGINT NOT NULL,
  revoked_at BIGINT,
  authn_method TEXT COLLATE "C" NOT NULL,
  user_agent TEXT COLLATE "C",
  FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
);

CREATE INDEX sessions_principal
  ON sessions(principal_id, revoked_at, absolute_expires_at);

CREATE TABLE canary_notes (
  note_id TEXT COLLATE "C" PRIMARY KEY,
  principal_id TEXT COLLATE "C" NOT NULL,
  content TEXT COLLATE "C" NOT NULL,
  state TEXT COLLATE "C" NOT NULL CHECK (state IN ('DRAFT', 'PUBLISHED')),
  created_at BIGINT NOT NULL,
  published_at BIGINT,
  FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
);

CREATE INDEX canary_notes_principal_created
  ON canary_notes(principal_id, created_at DESC, note_id ASC);

CREATE TABLE agent_grants (
  grant_id TEXT COLLATE "C" PRIMARY KEY,
  grant_digest TEXT COLLATE "C" NOT NULL,
  principal_id TEXT COLLATE "C" NOT NULL,
  agent_id TEXT COLLATE "C" NOT NULL,
  audience TEXT COLLATE "C" NOT NULL,
  allowed_actions_json TEXT COLLATE "C" NOT NULL,
  resource_prefixes_json TEXT COLLATE "C" NOT NULL,
  expires_at BIGINT NOT NULL,
  max_risk_class TEXT COLLATE "C" NOT NULL,
  step_up_at_or_above TEXT COLLATE "C" NOT NULL,
  remaining_effects BIGINT NOT NULL CHECK (remaining_effects >= 0),
  active BIGINT NOT NULL CHECK (active IN (0, 1)),
  revision BIGINT NOT NULL CHECK (revision >= 1),
  FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
);

CREATE INDEX agent_grants_resolution
  ON agent_grants(agent_id, audience, active, expires_at);

CREATE TABLE agent_effects (
  effect_id TEXT COLLATE "C" PRIMARY KEY,
  effect_digest TEXT COLLATE "C" NOT NULL,
  principal_id TEXT COLLATE "C" NOT NULL,
  agent_id TEXT COLLATE "C" NOT NULL,
  grant_id TEXT COLLATE "C" NOT NULL,
  action TEXT COLLATE "C" NOT NULL,
  resource TEXT COLLATE "C" NOT NULL,
  result_json TEXT COLLATE "C" NOT NULL,
  committed_at BIGINT NOT NULL,
  FOREIGN KEY(principal_id) REFERENCES principals(principal_id),
  FOREIGN KEY(grant_id) REFERENCES agent_grants(grant_id)
);

CREATE TABLE pending_effect_approvals (
  effect_id TEXT COLLATE "C" PRIMARY KEY,
  effect_digest TEXT COLLATE "C" NOT NULL,
  principal_id TEXT COLLATE "C" NOT NULL,
  expires_at BIGINT NOT NULL,
  created_at BIGINT NOT NULL,
  FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
);

CREATE TABLE effect_approvals (
  effect_id TEXT COLLATE "C" PRIMARY KEY,
  effect_digest TEXT COLLATE "C" NOT NULL,
  principal_id TEXT COLLATE "C" NOT NULL,
  credential_id TEXT COLLATE "C" NOT NULL,
  verified_at BIGINT NOT NULL,
  expires_at BIGINT NOT NULL,
  consumed_at BIGINT,
  FOREIGN KEY(principal_id) REFERENCES principals(principal_id),
  FOREIGN KEY(credential_id) REFERENCES webauthn_credentials(credential_id)
);

CREATE TABLE dpop_proofs (
  proof_hash TEXT COLLATE "C" PRIMARY KEY,
  expires_at BIGINT NOT NULL
);

CREATE INDEX dpop_proofs_expiry
  ON dpop_proofs(expires_at);

CREATE TABLE audit_events (
  event_id TEXT COLLATE "C" PRIMARY KEY,
  principal_id TEXT COLLATE "C",
  event_type TEXT COLLATE "C" NOT NULL,
  object_type TEXT COLLATE "C",
  object_id TEXT COLLATE "C",
  detail_json TEXT COLLATE "C" NOT NULL,
  created_at BIGINT NOT NULL
);

CREATE INDEX audit_events_principal_created
  ON audit_events(principal_id, created_at);

-- Non-unique: legacy or unexpected duplicate audit records remain visible
-- to the transaction-local postcondition instead of being silently discarded.
CREATE INDEX audit_events_committed_effect
  ON audit_events(object_id)
  WHERE event_type = 'agent.effect.committed' AND object_type = 'effect';

CREATE INDEX audit_events_created_note
  ON audit_events(object_id)
  WHERE event_type = 'canary.note.created' AND object_type = 'canary-note';
