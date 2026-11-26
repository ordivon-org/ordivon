-- Additive native login state. Apply once after V1 import in the intended
-- isolated owner schema, before opening any native authentication writers.
-- Legacy challenges intentionally have no eligibility row.
CREATE TABLE webauthn_login_completions (
  challenge_id TEXT COLLATE "C" PRIMARY KEY REFERENCES webauthn_challenges(challenge_id),
  session_id TEXT COLLATE "C" UNIQUE REFERENCES sessions(session_id),
  completed_at BIGINT,
  CHECK ((session_id IS NULL) = (completed_at IS NULL)),
  CHECK (completed_at IS NULL OR completed_at BETWEEN -9007199254740991 AND 9007199254740991)
);
