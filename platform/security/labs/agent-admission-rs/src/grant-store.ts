import { createHash, randomUUID } from "node:crypto";
import { DatabaseSync } from "node:sqlite";

import { AdmissionLabError } from "./errors.ts";
import type {
  CommentReceipt,
  EffectRequest,
  GrantCreate,
  GrantSnapshot,
} from "./model.ts";

interface GrantRow {
  grant_id: string;
  grant_digest: string;
  principal_id: string;
  agent_id: string;
  audience: string;
  allowed_actions: string;
  resource_prefixes: string;
  expires_at: number;
  max_risk_class: GrantSnapshot["maxRiskClass"];
  step_up_at_or_above: GrantSnapshot["stepUpAtOrAbove"];
  remaining_effects: number;
  active: number;
  revision: number;
}

interface EffectRow {
  effect_digest: string;
  response_json: string;
}

function sha256Json(value: unknown): string {
  return `sha256:${createHash("sha256").update(JSON.stringify(value)).digest("hex")}`;
}

function normalizeList(values: readonly string[]): string[] {
  return [...new Set(values)].sort();
}

function grantDigest(input: GrantCreate): string {
  return sha256Json({
    grantId: input.grantId,
    principalId: input.principalId,
    agentId: input.agentId,
    audience: input.audience,
    allowedActions: normalizeList(input.allowedActions),
    resourcePrefixes: normalizeList(input.resourcePrefixes),
    expiresAtEpochSeconds: input.expiresAtEpochSeconds,
    maxRiskClass: input.maxRiskClass,
    stepUpAtOrAbove: input.stepUpAtOrAbove,
  });
}

function parseStringArray(value: string): string[] {
  const parsed: unknown = JSON.parse(value);
  if (!Array.isArray(parsed) || parsed.some((item) => typeof item !== "string")) {
    throw new AdmissionLabError("grant_corrupt", "Stored grant is invalid.", 500);
  }
  return parsed;
}

function toSnapshot(row: GrantRow): GrantSnapshot {
  return {
    grantId: row.grant_id,
    grantDigest: row.grant_digest,
    principalId: row.principal_id,
    agentId: row.agent_id,
    audience: row.audience,
    allowedActions: parseStringArray(row.allowed_actions),
    resourcePrefixes: parseStringArray(row.resource_prefixes),
    expiresAtEpochSeconds: row.expires_at,
    maxRiskClass: row.max_risk_class,
    stepUpAtOrAbove: row.step_up_at_or_above,
    remainingEffects: row.remaining_effects,
    active: row.active === 1,
    revision: row.revision,
  };
}

function prefixMatches(resource: string, prefixes: readonly string[]): boolean {
  return prefixes.some((prefix) => resource.startsWith(prefix));
}

export class GrantStore {
  readonly db: DatabaseSync;

  constructor(path: string) {
    this.db = new DatabaseSync(path);
    this.db.exec("PRAGMA foreign_keys = ON");
    this.db.exec("PRAGMA journal_mode = WAL");
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS grants (
        grant_id TEXT PRIMARY KEY,
        grant_digest TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        audience TEXT NOT NULL,
        allowed_actions TEXT NOT NULL,
        resource_prefixes TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        max_risk_class TEXT NOT NULL,
        step_up_at_or_above TEXT NOT NULL,
        remaining_effects INTEGER NOT NULL CHECK (remaining_effects >= 0),
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        revision INTEGER NOT NULL CHECK (revision >= 1)
      );

      CREATE INDEX IF NOT EXISTS grants_agent_audience
        ON grants(agent_id, audience, active, expires_at);

      CREATE TABLE IF NOT EXISTS effects (
        effect_id TEXT PRIMARY KEY,
        effect_digest TEXT NOT NULL,
        grant_id TEXT NOT NULL,
        action TEXT NOT NULL,
        resource TEXT NOT NULL,
        response_json TEXT NOT NULL,
        committed_at INTEGER NOT NULL,
        FOREIGN KEY(grant_id) REFERENCES grants(grant_id)
      );

      CREATE TABLE IF NOT EXISTS comments (
        comment_id TEXT PRIMARY KEY,
        article_id TEXT NOT NULL,
        content TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        effect_id TEXT NOT NULL UNIQUE,
        created_at INTEGER NOT NULL,
        FOREIGN KEY(effect_id) REFERENCES effects(effect_id)
      );

      CREATE TABLE IF NOT EXISTS dpop_proofs (
        proof_hash TEXT PRIMARY KEY,
        expires_at INTEGER NOT NULL
      );

      CREATE INDEX IF NOT EXISTS dpop_proofs_expiry
        ON dpop_proofs(expires_at);
    `);
  }

  close(): void {
    this.db.close();
  }

  consumeDpopProof(
    proofId: string,
    nowEpochSeconds: number,
    ttlSeconds = 600,
  ): void {
    const bytes = Buffer.byteLength(proofId, "utf8");
    if (bytes < 1 || bytes > 256 || !Number.isSafeInteger(ttlSeconds) || ttlSeconds < 1) {
      throw new AdmissionLabError(
        "dpop_proof_invalid",
        "DPoP proof identity is invalid.",
        401,
      );
    }
    const proofHash = createHash("sha256").update(proofId).digest("hex");
    this.db.exec("BEGIN IMMEDIATE");
    try {
      this.db.prepare("DELETE FROM dpop_proofs WHERE expires_at <= ?").run(nowEpochSeconds);
      const existing = this.db
        .prepare("SELECT proof_hash FROM dpop_proofs WHERE proof_hash = ?")
        .get(proofHash);
      if (existing !== undefined) {
        throw new AdmissionLabError(
          "dpop_proof_replayed",
          "DPoP proof has already been consumed.",
          401,
        );
      }
      this.db
        .prepare("INSERT INTO dpop_proofs (proof_hash, expires_at) VALUES (?, ?)")
        .run(proofHash, nowEpochSeconds + ttlSeconds);
      this.db.exec("COMMIT");
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }

  createGrant(input: GrantCreate): GrantSnapshot {
    if (!Number.isSafeInteger(input.remainingEffects) || input.remainingEffects < 0) {
      throw new AdmissionLabError("invalid_grant", "remainingEffects is invalid.", 422);
    }
    const allowedActions = normalizeList(input.allowedActions);
    const resourcePrefixes = normalizeList(input.resourcePrefixes);
    if (allowedActions.length === 0 || resourcePrefixes.length === 0) {
      throw new AdmissionLabError(
        "invalid_grant",
        "Grant must contain actions and resources.",
        422,
      );
    }
    const digest = grantDigest({ ...input, allowedActions, resourcePrefixes });
    this.db
      .prepare(`
        INSERT INTO grants (
          grant_id, grant_digest, principal_id, agent_id, audience,
          allowed_actions, resource_prefixes, expires_at, max_risk_class,
          step_up_at_or_above, remaining_effects, active, revision
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
      `)
      .run(
        input.grantId,
        digest,
        input.principalId,
        input.agentId,
        input.audience,
        JSON.stringify(allowedActions),
        JSON.stringify(resourcePrefixes),
        input.expiresAtEpochSeconds,
        input.maxRiskClass,
        input.stepUpAtOrAbove,
        input.remainingEffects,
      );
    return this.getGrant(input.grantId);
  }

  getGrant(grantId: string): GrantSnapshot {
    const row = this.db.prepare("SELECT * FROM grants WHERE grant_id = ?").get(grantId) as
      | GrantRow
      | undefined;
    if (row === undefined) {
      throw new AdmissionLabError("grant_not_found", "Delegation grant was not found.", 403);
    }
    return toSnapshot(row);
  }

  resolveUniqueGrant(
    agentId: string,
    audience: string,
    action: string,
    resource: string,
    nowEpochSeconds: number,
  ): GrantSnapshot {
    const rows = this.db
      .prepare(`
        SELECT * FROM grants
        WHERE agent_id = ?
          AND audience = ?
          AND active = 1
          AND expires_at > ?
      `)
      .all(agentId, audience, nowEpochSeconds) as unknown as GrantRow[];

    const matching = rows
      .map(toSnapshot)
      .filter(
        (grant) =>
          grant.allowedActions.includes(action) &&
          prefixMatches(resource, grant.resourcePrefixes),
      );

    if (matching.length === 0) {
      throw new AdmissionLabError(
        "grant_not_found",
        "No active delegation grant authorizes this action.",
        403,
      );
    }
    if (matching.length !== 1) {
      throw new AdmissionLabError(
        "grant_ambiguous",
        "More than one delegation grant matches this effect.",
        409,
      );
    }
    return matching[0]!;
  }

  revokeGrant(grantId: string): void {
    this.db
      .prepare("UPDATE grants SET active = 0, revision = revision + 1 WHERE grant_id = ?")
      .run(grantId);
  }

  lookupCommittedEffect(
    effectId: string,
    effectDigest: string,
    authenticatedAgentId: string,
  ): CommentReceipt | null {
    const existing = this.db
      .prepare("SELECT effect_digest, response_json FROM effects WHERE effect_id = ?")
      .get(effectId) as EffectRow | undefined;

    if (existing === undefined) return null;
    if (existing.effect_digest !== effectDigest) {
      throw new AdmissionLabError(
        "effect_conflict",
        "Effect identity is already bound to different request content.",
        409,
      );
    }

    const receipt = JSON.parse(existing.response_json) as CommentReceipt;
    if (receipt.agentId !== authenticatedAgentId) {
      throw new AdmissionLabError(
        "effect_actor_mismatch",
        "Effect identity belongs to a different authenticated Agent.",
        403,
      );
    }
    return receipt;
  }

  commitComment(
    grant: GrantSnapshot,
    effect: EffectRequest,
    articleId: string,
    content: string,
    nowEpochSeconds: number,
  ): { readonly replayed: boolean; readonly receipt: CommentReceipt } {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const existing = this.db
        .prepare("SELECT effect_digest, response_json FROM effects WHERE effect_id = ?")
        .get(effect.effectId) as EffectRow | undefined;

      if (existing !== undefined) {
        if (existing.effect_digest !== effect.effectDigest) {
          throw new AdmissionLabError(
            "effect_conflict",
            "Effect identity is already bound to different request content.",
            409,
          );
        }
        const receipt = JSON.parse(existing.response_json) as CommentReceipt;
        if (receipt.agentId !== grant.agentId) {
          throw new AdmissionLabError(
            "effect_actor_mismatch",
            "Effect identity belongs to a different authenticated Agent.",
            403,
          );
        }
        this.db.exec("COMMIT");
        return { replayed: true, receipt };
      }

      const current = this.db.prepare("SELECT * FROM grants WHERE grant_id = ?").get(
        grant.grantId,
      ) as GrantRow | undefined;
      if (
        current === undefined ||
        current.grant_digest !== grant.grantDigest ||
        current.revision !== grant.revision ||
        current.active !== 1 ||
        current.expires_at <= nowEpochSeconds ||
        current.remaining_effects <= 0
      ) {
        throw new AdmissionLabError(
          "grant_changed",
          "Delegation grant changed after policy evaluation.",
          409,
        );
      }

      const update = this.db
        .prepare(`
          UPDATE grants
          SET remaining_effects = remaining_effects - 1,
              revision = revision + 1
          WHERE grant_id = ?
            AND revision = ?
            AND active = 1
            AND remaining_effects > 0
        `)
        .run(grant.grantId, grant.revision);

      if (update.changes !== 1) {
        throw new AdmissionLabError(
          "grant_changed",
          "Delegation budget changed after policy evaluation.",
          409,
        );
      }

      const receipt: CommentReceipt = {
        commentId: randomUUID(),
        articleId,
        content,
        principalId: grant.principalId,
        agentId: grant.agentId,
        effectId: effect.effectId,
      };

      this.db
        .prepare(`
          INSERT INTO effects (
            effect_id, effect_digest, grant_id, action, resource, response_json, committed_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `)
        .run(
          effect.effectId,
          effect.effectDigest,
          grant.grantId,
          effect.action,
          effect.resource,
          JSON.stringify(receipt),
          nowEpochSeconds,
        );

      this.db
        .prepare(`
          INSERT INTO comments (
            comment_id, article_id, content, principal_id, agent_id, effect_id, created_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `)
        .run(
          receipt.commentId,
          articleId,
          content,
          grant.principalId,
          grant.agentId,
          effect.effectId,
          nowEpochSeconds,
        );

      this.db.exec("COMMIT");
      return { replayed: false, receipt };
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }
}
