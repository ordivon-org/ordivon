/** Agent Grant persistence facet. WebStore retains the single SQLite connection and public API. */
import type { DatabaseSync } from "node:sqlite";

import { grantDigest, normalizeStrings } from "./identity-digests.ts";
import { WebProblem } from "./errors.ts";
import { grantFromRow } from "./store-row-projections.ts";
import type { AgentGrantRow } from "./store-row-projections.ts";
import type { AgentGrantCreate, AgentGrantSnapshot } from "./model.ts";

type AuditSink = (
  eventType: string,
  now: number,
  principalId: string | null,
  objectType: string | null,
  objectId: string | null,
  detail: unknown,
) => void;

export class AgentGrantStore {
  private readonly db: DatabaseSync;
  private readonly audit: AuditSink;

  constructor(db: DatabaseSync, audit: AuditSink) {
    this.db = db;
    this.audit = audit;
  }

  createAgentGrant(input: AgentGrantCreate, now: number): AgentGrantSnapshot {
    const digest = grantDigest(input);
    this.db
      .prepare(`
        INSERT INTO agent_grants (
          grant_id, grant_digest, principal_id, agent_id, audience,
          allowed_actions_json, resource_prefixes_json, expires_at,
          max_risk_class, step_up_at_or_above, remaining_effects, active, revision
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
      `)
      .run(
        input.grantId,
        digest,
        input.principalId,
        input.agentId,
        input.audience,
        JSON.stringify(normalizeStrings(input.allowedActions)),
        JSON.stringify(normalizeStrings(input.resourcePrefixes)),
        input.expiresAtEpochSeconds,
        input.maxRiskClass,
        input.stepUpAtOrAbove,
        input.remainingEffects,
      );
    this.audit("agent.grant.issued", now, input.principalId, "agent-grant", input.grantId, {
      agentId: input.agentId,
      grantDigest: digest,
    });
    return this.getAgentGrant(input.grantId);
  }

  getAgentGrant(grantId: string): AgentGrantSnapshot {
    const row = this.db
      .prepare("SELECT * FROM agent_grants WHERE grant_id = ?")
      .get(grantId) as AgentGrantRow | undefined;
    if (row === undefined) {
      throw new WebProblem(
        404,
        "agent-grant-not-found",
        "Agent Grant not found",
        "The requested Agent Grant does not exist.",
      );
    }
    return grantFromRow(row);
  }

  listAgentGrants(principalId: string): AgentGrantSnapshot[] {
    const rows = this.db
      .prepare("SELECT * FROM agent_grants WHERE principal_id = ? ORDER BY grant_id")
      .all(principalId) as unknown as AgentGrantRow[];
    return rows.map(grantFromRow);
  }

  revokeAgentGrant(
    principalId: string,
    grantId: string,
    expectedDigest: string,
    now: number,
  ): AgentGrantSnapshot {
    const current = this.getAgentGrant(grantId);
    if (current.principalId !== principalId) {
      throw new WebProblem(
        403,
        "agent-grant-principal-mismatch",
        "Agent Grant mismatch",
        "The Agent Grant does not belong to this Principal.",
      );
    }
    if (current.grantDigest !== expectedDigest) {
      throw new WebProblem(
        409,
        "agent-grant-changed",
        "Agent Grant changed",
        "The Agent Grant changed before revocation.",
      );
    }
    this.db
      .prepare(
        "UPDATE agent_grants SET active = 0, revision = revision + 1 WHERE grant_id = ?",
      )
      .run(grantId);
    this.audit("agent.grant.revoked", now, principalId, "agent-grant", grantId, {
      agentId: current.agentId,
    });
    return this.getAgentGrant(grantId);
  }

  resolveAgentGrant(
    agentId: string,
    audience: string,
    action: string,
    resource: string,
    now: number,
  ): AgentGrantSnapshot {
    const rows = this.db
      .prepare(`
        SELECT * FROM agent_grants
        WHERE agent_id = ? AND audience = ? AND active = 1 AND expires_at > ?
      `)
      .all(agentId, audience, now) as unknown as AgentGrantRow[];
    const matches = rows
      .map(grantFromRow)
      .filter(
        (grant) =>
          grant.allowedActions.includes(action) &&
          grant.resourcePrefixes.some((prefix) => resource.startsWith(prefix)),
      );
    if (matches.length === 0) {
      throw new WebProblem(
        403,
        "agent-grant-unavailable",
        "Agent authority unavailable",
        "No active Agent Grant authorizes this action and resource.",
      );
    }
    if (matches.length !== 1) {
      throw new WebProblem(
        409,
        "agent-grant-ambiguous",
        "Agent authority ambiguous",
        "More than one Agent Grant matches this action and resource.",
      );
    }
    return matches[0]!;
  }
}
