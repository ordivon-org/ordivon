/** Durable effect receipt and its audit write. Caller owns the transaction. */
import { randomUUID } from "node:crypto";
import type { DatabaseSync } from "node:sqlite";
import { WebProblem } from "./errors.ts";
import type { AgentEffectReceipt, AgentEffectRequest } from "./model.ts";
import { effectReceiptFromRow, type AgentEffectRow } from "./store-row-projections.ts";
import { assertWrittenEffectAudit, requireSingleEffectWrite } from "./store-effect-postconditions.ts";
import { insertAuditRow, type EffectAuditRow } from "./store-audit.ts";

export class EffectReceiptStore {
  private readonly db: DatabaseSync;

  constructor(db: DatabaseSync) {
    this.db = db;
  }

  private readEffectRow(effectId: string): AgentEffectRow | undefined {
    return this.db
      .prepare("SELECT * FROM agent_effects WHERE effect_id = ?")
      .get(effectId) as AgentEffectRow | undefined;
  }

  getAgentEffect(effectId: string): AgentEffectReceipt | null {
    const row = this.readEffectRow(effectId);
    return row === undefined ? null : effectReceiptFromRow(row);
  }

  // Shared write/audit/readback sequence for the two local business
  // transactions. The caller retains BEGIN/COMMIT/ROLLBACK authority.
  recordNewEffectReceipt(expected: AgentEffectRow): AgentEffectReceipt {
    this.db
      .prepare(`
        INSERT INTO agent_effects (
          effect_id, effect_digest, principal_id, agent_id, grant_id,
          action, resource, result_json, committed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `)
      .run(
        expected.effect_id, expected.effect_digest, expected.principal_id,
        expected.agent_id, expected.grant_id, expected.action,
        expected.resource, expected.result_json, expected.committed_at,
      );
    const audit: EffectAuditRow = {
      event_id: randomUUID(), principal_id: expected.principal_id,
      event_type: "agent.effect.committed", object_type: "effect",
      object_id: expected.effect_id, created_at: expected.committed_at,
      detail_json: JSON.stringify({
        agentId: expected.agent_id, grantId: expected.grant_id, action: expected.action,
      }),
    };
    requireSingleEffectWrite(insertAuditRow(this.db, audit), "audit");
    assertWrittenEffectAudit(this.db, audit);
    return this.readWrittenEffectReceipt(expected);
  }

  // Owner-local write/readback invariant, not a general authenticity proof for
  // historical receipts. Compare the exact bytes and all intended row fields
  // while the caller still owns the business transaction.
  private readWrittenEffectReceipt(expected: AgentEffectRow): AgentEffectReceipt {
    const row = this.readEffectRow(expected.effect_id);
    if (row === undefined) {
      throw new WebProblem(500, "effect-receipt-missing", "Effect receipt missing",
        "The newly written Effect has no readable owner receipt.");
    }
    const receipt = effectReceiptFromRow(row);
    if (row.effect_id !== expected.effect_id ||
        row.effect_digest !== expected.effect_digest ||
        row.principal_id !== expected.principal_id ||
        row.agent_id !== expected.agent_id ||
        row.grant_id !== expected.grant_id ||
        row.action !== expected.action ||
        row.resource !== expected.resource ||
        row.result_json !== expected.result_json ||
        row.committed_at !== expected.committed_at) {
      throw new WebProblem(500, "effect-receipt-mismatch", "Effect receipt mismatch",
        "The newly written Effect does not match its intended owner receipt.");
    }
    return receipt;
  }

  resolveAgentEffectReplay(
    agentId: string,
    effect: AgentEffectRequest,
  ): AgentEffectReceipt | null {
    const existing = this.getAgentEffect(effect.effectId);
    if (existing === null) return null;
    if (existing.agentId !== agentId) {
      throw new WebProblem(
        403,
        "effect-actor-mismatch",
        "Effect actor mismatch",
        "The committed effect belongs to a different Agent.",
      );
    }
    if (
      existing.effectDigest !== effect.effectDigest ||
      existing.action !== effect.action ||
      existing.resource !== effect.resource
    ) {
      throw new WebProblem(
        409,
        "effect-conflict",
        "Effect conflict",
        "The effect identifier is already bound to different content.",
      );
    }
    return existing;
  }

}
