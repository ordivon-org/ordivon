/** SQLite row projections, deliberately without database or transaction authority. */

import { WebProblem } from "./errors.ts";
import type {
  AgentEffectReceipt,
  AgentGrantSnapshot,
  CanaryNote,
  ChallengePurpose,
  Principal,
  SessionView,
  StoredCredential,
} from "./model.ts";

export interface PrincipalRow {
  principal_id: string;
  user_name: string;
  display_name: string;
}

export interface CredentialRow {
  credential_id: string;
  principal_id: string;
  public_key: Uint8Array;
  counter: number;
  transports_json: string;
  device_type: string;
  backed_up: number;
  created_at: number;
  last_used_at: number;
  revoked_at: number | null;
}

export interface ChallengeRow {
  challenge_id: string;
  purpose: ChallengePurpose;
  principal_id: string;
  challenge: string;
  payload_digest: string;
  payload_json: string;
  expires_at: number;
  consumed_at: number | null;
}

export interface AgentGrantRow {
  grant_id: string;
  grant_digest: string;
  principal_id: string;
  agent_id: string;
  audience: string;
  allowed_actions_json: string;
  resource_prefixes_json: string;
  expires_at: number;
  max_risk_class: AgentGrantSnapshot["maxRiskClass"];
  step_up_at_or_above: AgentGrantSnapshot["stepUpAtOrAbove"];
  remaining_effects: number;
  active: number;
  revision: number;
}

export interface AgentEffectRow {
  effect_id: string;
  effect_digest: string;
  principal_id: string;
  agent_id: string;
  grant_id: string;
  action: string;
  resource: string;
  result_json: string;
  committed_at: number;
}

export interface SessionRow {
  session_id: string;
  token_hash: string;
  principal_id: string;
  created_at: number;
  authenticated_at: number;
  last_seen_at: number;
  idle_expires_at: number;
  absolute_expires_at: number;
  revoked_at: number | null;
  authn_method: "webauthn";
  user_agent: string | null;
}

export interface NoteRow {
  note_id: string;
  principal_id: string;
  content: string;
  state: "DRAFT" | "PUBLISHED";
  created_at: number;
  published_at: number | null;
}

function parseStringArray(value: string): string[] {
  const parsed: unknown = JSON.parse(value);
  if (!Array.isArray(parsed) || parsed.some((item) => typeof item !== "string")) {
    throw new WebProblem(
      500,
      "credential-corrupt",
      "Credential state invalid",
      "Stored credential transports are invalid.",
    );
  }
  return parsed;
}

export function principalFromRow(row: PrincipalRow): Principal {
  return {
    principalId: row.principal_id,
    userName: row.user_name,
    displayName: row.display_name,
  };
}

export function sessionFromRow(row: SessionRow): SessionView {
  return {
    sessionId: row.session_id,
    principalId: row.principal_id,
    createdAt: row.created_at,
    authenticatedAt: row.authenticated_at,
    lastSeenAt: row.last_seen_at,
    idleExpiresAt: row.idle_expires_at,
    absoluteExpiresAt: row.absolute_expires_at,
    revokedAt: row.revoked_at,
    authnMethod: row.authn_method,
    userAgent: row.user_agent,
  };
}

export function credentialFromRow(row: CredentialRow): StoredCredential {
  return {
    credentialId: row.credential_id,
    principalId: row.principal_id,
    publicKey: Uint8Array.from(row.public_key),
    counter: row.counter,
    transports: parseStringArray(row.transports_json),
    deviceType: row.device_type,
    backedUp: row.backed_up === 1,
    createdAt: row.created_at,
    lastUsedAt: row.last_used_at,
    revokedAt: row.revoked_at,
  };
}

export function noteFromRow(row: NoteRow): CanaryNote {
  return {
    noteId: row.note_id,
    principalId: row.principal_id,
    content: row.content,
    state: row.state,
    createdAt: row.created_at,
    publishedAt: row.published_at,
  };
}

export function grantFromRow(row: AgentGrantRow): AgentGrantSnapshot {
  return {
    grantId: row.grant_id,
    grantDigest: row.grant_digest,
    principalId: row.principal_id,
    agentId: row.agent_id,
    audience: row.audience,
    allowedActions: parseStringArray(row.allowed_actions_json),
    resourcePrefixes: parseStringArray(row.resource_prefixes_json),
    expiresAtEpochSeconds: row.expires_at,
    maxRiskClass: row.max_risk_class,
    stepUpAtOrAbove: row.step_up_at_or_above,
    remainingEffects: row.remaining_effects,
    active: row.active === 1,
    revision: row.revision,
  };
}

export function effectReceiptFromRow(row: AgentEffectRow): AgentEffectReceipt {
  return {
    effectId: row.effect_id,
    effectDigest: row.effect_digest,
    principalId: row.principal_id,
    agentId: row.agent_id,
    grantId: row.grant_id,
    action: row.action,
    resource: row.resource,
    result: JSON.parse(row.result_json) as unknown,
    committedAt: row.committed_at,
  };
}
