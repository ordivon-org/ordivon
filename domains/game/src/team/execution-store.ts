import type { DatabaseSync } from "node:sqlite";

import { canonicalJson } from "../digest.ts";
import { protocolDigest, type ProtocolJson } from "../host-contract/canonical.ts";
import type { GameStore } from "../storage.ts";
import { EmbeddedHostAuthority } from "../host-contract/embedded-authority.ts";
import type {
  DispatchEnvelope,
  ObservationEnvelope,
  TaskDescriptor,
  VerificationReceipt,
} from "../host-contract/model.ts";
import type {
  ActionProposal,
  TeamContextReference,
  TeamDispatch,
  TeamEffect,
  TeamObservation,
  TeamRound,
  TeamTickPlan,
} from "./model.ts";
import { TeamStore, TeamStoreError, coordinatorTaskId } from "./store.ts";

interface JsonRow { value_json: string }

function parse<T>(text: string, label: string): T {
  try { return JSON.parse(text) as T; }
  catch (error) { throw new TeamStoreError("team_corrupt", `${label} is invalid JSON: ${String(error)}`); }
}

export function teamCognitionStarted(
  game: GameStore,
  runId = game.activeRunId,
): boolean {
  const table = game.db.prepare(
    "SELECT 1 AS present FROM sqlite_master WHERE type = 'table' AND name = 'team_rounds'",
  ).get() as { present?: number } | undefined;
  if (table?.present !== 1) return false;
  const row = game.db.prepare(
    "SELECT 1 AS present FROM team_rounds WHERE run_id = ? LIMIT 1",
  ).get(runId) as { present?: number } | undefined;
  return row?.present === 1;
}

function proposalSemanticJson(proposal: ActionProposal): string {
  const { updatedAt: _updatedAt, ...semantic } = proposal;
  return canonicalJson(semantic);
}

function protocolSafe(value: unknown): ProtocolJson {
  if (value === null || typeof value === "boolean" || typeof value === "string") return value;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("non-finite Team value cannot enter Protocol");
    return Number.isSafeInteger(value) ? value : value.toString();
  }
  if (Array.isArray(value)) return value.map(protocolSafe);
  if (typeof value === "object") return Object.fromEntries(
    Object.entries(value as Record<string, unknown>)
      .filter(([, item]) => item !== undefined)
      .map(([key, item]) => [key, protocolSafe(item)]),
  );
  throw new TypeError(`unsupported Team value: ${typeof value}`);
}

function authorityTaskId(roundId: string): string {
  return `task:team-round:${roundId.slice("team-round:".length)}`;
}
function wireEffectId(effectId: string): string {
  return effectId.startsWith("effect:") ? effectId : `effect:${effectId}`;
}
function wireDispatchId(dispatchId: string): string {
  return dispatchId.startsWith("dispatch:") ? dispatchId : `dispatch:${dispatchId}`;
}

export class TeamExecutionStore {
  readonly db: DatabaseSync;
  readonly team: TeamStore;
  readonly authority: EmbeddedHostAuthority;
  private readonly pendingEffects = new Map<string, TeamEffect>();

  constructor(team: TeamStore) {
    this.team = team;
    this.db = team.db;
    this.authority = new EmbeddedHostAuthority(team.game);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS team_rounds (
        round_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        world_revision INTEGER NOT NULL,
        status TEXT NOT NULL,
        value_json TEXT NOT NULL,
        UNIQUE (run_id, world_revision),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS team_round_contexts (
        context_id TEXT PRIMARY KEY,
        round_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        world_revision INTEGER NOT NULL,
        artifact_digest TEXT NOT NULL,
        value_json TEXT NOT NULL,
        UNIQUE (round_id, actor_id),
        FOREIGN KEY (round_id) REFERENCES team_rounds(round_id)
      );
      CREATE TABLE IF NOT EXISTS team_proposals (
        proposal_id TEXT PRIMARY KEY,
        round_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        status TEXT NOT NULL,
        value_json TEXT NOT NULL,
        UNIQUE (round_id, actor_id),
        FOREIGN KEY (round_id) REFERENCES team_rounds(round_id)
      );
      CREATE TABLE IF NOT EXISTS team_tick_plans (
        tick_plan_id TEXT PRIMARY KEY,
        round_id TEXT NOT NULL UNIQUE,
        run_id TEXT NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (round_id) REFERENCES team_rounds(round_id)
      );
      CREATE INDEX IF NOT EXISTS team_rounds_run_idx ON team_rounds(run_id, world_revision);
      CREATE INDEX IF NOT EXISTS team_proposals_round_idx ON team_proposals(round_id, actor_id);
    `);
  }

  private put<T>(table: string, idColumn: string, id: string, record: T, insertColumns: string[], insertValues: unknown[], eventType: string, runId: string, createdAt: string): T {
    const existing = this.db.prepare(`SELECT value_json FROM ${table} WHERE ${idColumn} = ?`).get(id) as JsonRow | undefined;
    if (existing) {
      const retained = parse<T>(existing.value_json, table);
      if (canonicalJson(retained) !== canonicalJson(record)) throw new TeamStoreError("team_conflict", `${table} identity is bound to different content`);
      return retained;
    }
    const placeholders = insertColumns.map(() => "?").join(", ");
    const recordJson = canonicalJson(record);
    this.team.host.withTransaction(runId, () => {
      const inserted = this.db.prepare(`INSERT OR IGNORE INTO ${table} (${insertColumns.join(", ")}, value_json) VALUES (${placeholders}, ?)`)
        .run(...([...insertValues, recordJson] as never[]));
      if (Number(inserted.changes) === 1) {
        this.team.host.appendEventInTransaction(runId, eventType, `host-event:${id}:created`, { record }, createdAt);
        return;
      }
      const retained = this.db.prepare(`SELECT value_json FROM ${table} WHERE ${idColumn} = ?`).get(id) as JsonRow | undefined;
      if (!retained || retained.value_json !== recordJson) {
        throw new TeamStoreError("team_conflict", `${table} identity is bound to different content`);
      }
    });
    const retained = this.db.prepare(`SELECT value_json FROM ${table} WHERE ${idColumn} = ?`).get(id) as JsonRow | undefined;
    if (!retained) throw new TeamStoreError("team_corrupt", `${table} record disappeared after insert`);
    return parse<T>(retained.value_json, table);
  }

  findRound(runId: string, worldRevision: number): TeamRound | null {
    const row = this.db.prepare("SELECT value_json FROM team_rounds WHERE run_id = ? AND world_revision = ?").get(runId, worldRevision) as JsonRow | undefined;
    return row ? parse<TeamRound>(row.value_json, "Team Round") : null;
  }
  getRound(roundId: string): TeamRound {
    const row = this.db.prepare("SELECT value_json FROM team_rounds WHERE round_id = ?").get(roundId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Team Round: ${roundId}`);
    return parse<TeamRound>(row.value_json, "Team Round");
  }
  putRound(round: TeamRound): TeamRound {
    return this.put("team_rounds", "round_id", round.roundId, round,
      ["round_id", "run_id", "world_revision", "status"], [round.roundId, round.runId, round.worldRevision, round.status],
      "team.round-created", round.runId, round.createdAt);
  }
  saveRound(expected: TeamRound, round: TeamRound, eventType: string): TeamRound {
    const current = this.getRound(round.roundId);
    if (
      expected.roundId !== round.roundId ||
      expected.runId !== round.runId ||
      expected.worldRevision !== round.worldRevision ||
      current.runId !== round.runId ||
      current.worldRevision !== round.worldRevision
    ) {
      throw new TeamStoreError("team_conflict", "Team Round identity changed");
    }
    const transitions: Record<TeamRound["status"], TeamRound["status"][]> = {
      collecting: ["collecting", "planned", "blocked"],
      planned: ["planned", "dispatched", "blocked"],
      dispatched: ["dispatched", "observed", "blocked"],
      observed: ["observed", "completed", "blocked"],
      blocked: ["blocked", "planned"],
      completed: ["completed"],
    };
    if (!transitions[expected.status].includes(round.status)) {
      throw new TeamStoreError("team_conflict", `invalid Team Round transition: ${expected.status} -> ${round.status}`);
    }
    const expectedJson = canonicalJson(expected);
    const roundJson = canonicalJson(round);
    if (expected.status === "completed" && expectedJson !== roundJson) {
      throw new TeamStoreError("team_conflict", "completed Team Round is immutable");
    }
    const currentJson = canonicalJson(current);
    if (currentJson !== expectedJson) {
      if (currentJson === roundJson) {
        if (current.status === "completed") this.reconcileCompletedRound(current);
        return current;
      }
      throw new TeamStoreError("team_conflict", "Team Round was superseded");
    }
    this.team.host.withTransaction(round.runId, () => {
      const changed = this.db.prepare(
        "UPDATE team_rounds SET status = ?, value_json = ? WHERE round_id = ? AND value_json = ?",
      ).run(round.status, roundJson, round.roundId, expectedJson);
      if (Number(changed.changes) !== 1) {
        throw new TeamStoreError("team_conflict", "Team Round was superseded");
      }
      this.team.host.appendEventInTransaction(round.runId, eventType, `host-event:${round.roundId}:${eventType}:${round.updatedAt}`, { round }, round.updatedAt);
    });
    const retained = this.getRound(round.roundId);
    if (retained.status === "completed") this.reconcileCompletedRound(retained);
    return retained;
  }

  reconcileCompletedRound(round: TeamRound): void {
    if (round.status !== "completed") {
      throw new TeamStoreError("team_conflict", "only a completed Team Round can reconcile authority");
    }
    const taskId = authorityTaskId(round.roundId);
    const projection = this.authority.projection(round.runId, taskId);
    if (projection.state === "completed") return;
    if (projection.state === "failed" || projection.state === "cancelled") {
      throw new TeamStoreError("team_corrupt", `completed Team Round has terminal Authority state ${projection.state}`);
    }
    this.completeAuthority(round);
  }

  putContext(reference: TeamContextReference): TeamContextReference {
    return this.put("team_round_contexts", "context_id", reference.contextId, reference,
      ["context_id", "round_id", "run_id", "actor_id", "session_id", "world_revision", "artifact_digest"],
      [reference.contextId, reference.roundId, reference.runId, reference.actorId, reference.taskId, reference.worldRevision, reference.artifactDigest],
      "team.context-prepared", reference.runId, reference.createdAt);
  }
  listContexts(roundId: string): TeamContextReference[] {
    const rows = this.db.prepare("SELECT value_json FROM team_round_contexts WHERE round_id = ? ORDER BY actor_id").all(roundId) as unknown as JsonRow[];
    return rows.map((row) => parse<TeamContextReference>(row.value_json, "Team Context Reference"));
  }
  findContextForActor(roundId: string, actorId: string): TeamContextReference | null {
    const row = this.db.prepare("SELECT value_json FROM team_round_contexts WHERE round_id = ? AND actor_id = ?").get(roundId, actorId) as JsonRow | undefined;
    return row ? parse<TeamContextReference>(row.value_json, "Team Context Reference") : null;
  }

  putProposal(proposal: ActionProposal): ActionProposal {
    return this.put("team_proposals", "proposal_id", proposal.proposalId, proposal,
      ["proposal_id", "round_id", "run_id", "actor_id", "status"],
      [proposal.proposalId, proposal.roundId, proposal.runId, proposal.actorId, proposal.status],
      "team.proposal-recorded", proposal.runId, proposal.createdAt);
  }
  saveProposal(expected: ActionProposal, proposal: ActionProposal, eventType: string): ActionProposal {
    const current = this.getProposal(proposal.proposalId);
    if (
      expected.proposalId !== proposal.proposalId ||
      expected.roundId !== proposal.roundId ||
      expected.actorId !== proposal.actorId ||
      current.roundId !== proposal.roundId ||
      current.actorId !== proposal.actorId
    ) {
      throw new TeamStoreError("team_conflict", "Team Proposal identity changed");
    }
    const transitions: Record<ActionProposal["status"], ActionProposal["status"][]> = {
      proposed: ["proposed", "selected", "rejected"],
      selected: ["selected", "executed", "verified", "rejected"],
      executed: ["executed", "verified", "rejected"],
      rejected: ["rejected"],
      verified: ["verified"],
    };
    if (!transitions[expected.status].includes(proposal.status)) {
      throw new TeamStoreError("team_conflict", `invalid Team Proposal transition: ${expected.status} -> ${proposal.status}`);
    }
    const expectedJson = canonicalJson(expected);
    const proposalJson = canonicalJson(proposal);
    const currentJson = canonicalJson(current);
    if (currentJson !== expectedJson) {
      if (currentJson === proposalJson) return current;
      throw new TeamStoreError("team_conflict", "Team Proposal was superseded");
    }
    if (["rejected", "verified"].includes(expected.status) && expectedJson !== proposalJson) {
      if (proposalSemanticJson(expected) !== proposalSemanticJson(proposal)) {
        throw new TeamStoreError("team_conflict", `terminal Team Proposal is immutable: ${expected.status}`);
      }
      return current;
    }
    this.team.host.withTransaction(proposal.runId, () => {
      const changed = this.db.prepare(
        "UPDATE team_proposals SET status = ?, value_json = ? WHERE proposal_id = ? AND value_json = ?",
      ).run(proposal.status, proposalJson, proposal.proposalId, expectedJson);
      if (Number(changed.changes) !== 1) {
        throw new TeamStoreError("team_conflict", "Team Proposal was superseded");
      }
      this.team.host.appendEventInTransaction(proposal.runId, eventType, `host-event:${proposal.proposalId}:${eventType}:${proposal.updatedAt}`, { proposal }, proposal.updatedAt);
    });
    return this.getProposal(proposal.proposalId);
  }
  getProposal(proposalId: string): ActionProposal {
    const row = this.db.prepare("SELECT value_json FROM team_proposals WHERE proposal_id = ?").get(proposalId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Team Proposal: ${proposalId}`);
    return parse<ActionProposal>(row.value_json, "Team Proposal");
  }
  findProposalForActor(roundId: string, actorId: string): ActionProposal | null {
    const row = this.db.prepare("SELECT value_json FROM team_proposals WHERE round_id = ? AND actor_id = ?").get(roundId, actorId) as JsonRow | undefined;
    return row ? parse<ActionProposal>(row.value_json, "Team Proposal") : null;
  }
  listProposals(roundId: string): ActionProposal[] {
    const rows = this.db.prepare("SELECT value_json FROM team_proposals WHERE round_id = ? ORDER BY actor_id").all(roundId) as unknown as JsonRow[];
    return rows.map((row) => parse<ActionProposal>(row.value_json, "Team Proposal"));
  }

  putTickPlan(plan: TeamTickPlan): TeamTickPlan {
    return this.put("team_tick_plans", "tick_plan_id", plan.tickPlanId, plan,
      ["tick_plan_id", "round_id", "run_id"], [plan.tickPlanId, plan.roundId, plan.runId],
      "team.tick-plan-prepared", plan.runId, plan.createdAt);
  }
  getTickPlan(tickPlanId: string): TeamTickPlan {
    const row = this.db.prepare("SELECT value_json FROM team_tick_plans WHERE tick_plan_id = ?").get(tickPlanId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Team TickPlan: ${tickPlanId}`);
    return parse<TeamTickPlan>(row.value_json, "Team TickPlan");
  }

  putEffect(effect: TeamEffect): TeamEffect {
    this.pendingEffects.set(effect.effectId, effect);
    this.team.host.putProtocolArtifact("ordivon.game.team-tick-effect", {
      schemaVersion: 1, kind: "ordivon.game.team-tick-effect", ...protocolSafe(effect) as Record<string, ProtocolJson>,
    });
    return effect;
  }
  getEffect(effectId: string): TeamEffect {
    const pending = this.pendingEffects.get(effectId);
    if (pending) return pending;
    const round = this.allRounds().find((candidate) => candidate.effectId === effectId);
    if (!round) throw new Error(`unknown Team Effect: ${effectId}`);
    const artifact = this.authority.relatedObjects(round.runId, authorityTaskId(round.roundId)).find((item) => item.kind === "ordivon.game.team-tick-effect");
    if (!artifact || typeof artifact.content !== "object" || artifact.content === null || Array.isArray(artifact.content)) throw new Error(`Team Effect Artifact is missing: ${effectId}`);
    const { schemaVersion: _schemaVersion, kind: _kind, ...effect } = artifact.content;
    const projection = this.authority.projection(round.runId, authorityTaskId(round.roundId));
    const status = projection.state === "failed" ? "rejected" : projection.state === "ready" ? "prepared" : projection.state === "reconciling" ? "dispatched" : "succeeded";
    const domainEffectId = round.effectId;
    if (!domainEffectId) throw new Error(`Team Round omitted Effect identity: ${round.roundId}`);
    return { ...(effect as unknown as TeamEffect), effectId: domainEffectId, status, updatedAt: round.updatedAt };
  }
  saveEffect(effect: TeamEffect, _eventType: string): TeamEffect {
    return { ...this.getEffect(effect.effectId), status: effect.status, updatedAt: effect.updatedAt };
  }

  putDispatch(dispatch: TeamDispatch): TeamDispatch {
    const round = this.getRound(dispatch.roundId);
    const plan = this.getTickPlan(dispatch.tickPlanId);
    const effect = this.pendingEffects.get(dispatch.effectId);
    if (!effect) throw new Error(`Team Effect must be prepared before Dispatch: ${dispatch.effectId}`);
    const taskId = authorityTaskId(round.roundId);
    const descriptor: TaskDescriptor = {
      schemaVersion: 1, kind: "ordivon.host-task-descriptor", taskId,
      goalId: this.team.getGoal(dispatch.runId).goalId,
      workloadId: "ordivon.game.team-tick.v1",
      assigneeRef: `coordinator:${coordinatorTaskId(dispatch.runId)}`,
      providerPolicyRef: null, domainRef: `game-run:${dispatch.runId}`,
      configurationDigests: [protocolDigest(protocolSafe(plan))],
    };
    this.authority.ensureTask(dispatch.runId, descriptor);
    const request = { schemaVersion: 1, kind: "ordivon.game.team-tick-request", runId: dispatch.runId, roundId: dispatch.roundId, tickPlan: protocolSafe(plan) } satisfies ProtocolJson;
    const wireEffect = { schemaVersion: 1, kind: "ordivon.game.team-tick-effect", ...protocolSafe(effect) as Record<string, ProtocolJson>, effectId: wireEffectId(effect.effectId) } satisfies ProtocolJson;
    const envelope: DispatchEnvelope = {
      schemaVersion: 1, kind: "ordivon.dispatch-envelope",
      dispatchId: wireDispatchId(dispatch.dispatchId), effectId: wireEffectId(effect.effectId),
      executorId: "executor:game-world-v1", requestDigest: protocolDigest(request),
      idempotencyKey: dispatch.commandId,
      requiredStateRefs: [{ ref: `game-world:${dispatch.runId}`, digest: effect.requiredWorldDigest.startsWith("sha256:") ? effect.requiredWorldDigest as `sha256:${string}` : `sha256:${effect.requiredWorldDigest}` }],
      expectedObservationKind: "ordivon.game.team-tick-observation.v1",
    };
    this.authority.prepare(dispatch.runId, taskId, wireEffect, request as Record<string, ProtocolJson>, envelope);
    this.pendingEffects.delete(effect.effectId);
    return dispatch;
  }
  getDispatch(dispatchId: string): TeamDispatch {
    const round = this.allRounds().find((candidate) => candidate.dispatchId === dispatchId);
    if (!round || !round.effectId || !round.tickPlanId) throw new Error(`unknown Team Dispatch: ${dispatchId}`);
    const projection = this.authority.projection(round.runId, authorityTaskId(round.roundId));
    const observation = this.findObservationForRound(round.roundId);
    return {
      dispatchId, effectId: round.effectId, roundId: round.roundId, runId: round.runId,
      tickPlanId: round.tickPlanId, commandId: `team-tick:${round.tickPlanId}`,
      status: projection.state === "failed" ? "rejected" : observation ? observation.verificationSuccess ? "succeeded" : "rejected" : projection.state === "reconciling" ? "pending" : "unknown",
      worldEventId: observation?.worldEventId ?? null, commandSequence: observation?.commandSequence ?? null,
      error: projection.state === "failed" ? "authority_failed" : null,
      createdAt: round.createdAt, updatedAt: round.updatedAt,
    };
  }
  saveDispatch(dispatch: TeamDispatch, _eventType: string): TeamDispatch {
    if (dispatch.status === "rejected") this.rejectAuthority(dispatch, dispatch.error ?? "dispatch_rejected");
    return { ...this.getDispatch(dispatch.dispatchId), ...dispatch };
  }

  findObservationForRound(roundId: string): TeamObservation | null {
    const round = this.getRound(roundId);
    if (!round.dispatchId) return null;
    let envelope: ObservationEnvelope;
    try { envelope = this.authority.observation(round.runId, authorityTaskId(roundId)); }
    catch { return null; }
    const evidence = envelope.evidenceRefs[0];
    if (!evidence) return null;
    const artifact = this.team.host.getProtocolArtifact<ProtocolJson>(evidence.digest);
    if (typeof artifact.content !== "object" || artifact.content === null || Array.isArray(artifact.content)) return null;
    const { schemaVersion: _schemaVersion, kind: _kind, ...value } = artifact.content;
    return value as unknown as TeamObservation;
  }
  putObservation(observation: TeamObservation): TeamObservation {
    const payload = { schemaVersion: 1, kind: "ordivon.game.team-tick-observation.v1", ...protocolSafe(observation) as Record<string, ProtocolJson> } satisfies ProtocolJson;
    const artifact = this.team.host.putProtocolArtifact("ordivon.game.team-tick-observation.v1", payload);
    const envelope: ObservationEnvelope = {
      schemaVersion: 1, kind: "ordivon.observation-envelope",
      dispatchId: wireDispatchId(observation.dispatchId), executorId: "executor:game-world-v1",
      status: observation.verificationSuccess ? "succeeded" : "rejected",
      payloadDigest: protocolDigest(payload),
      evidenceRefs: [{ ref: observation.worldEventId, kind: "game-world-event", digest: artifact.digest as `sha256:${string}` }],
    };
    this.authority.recordObservation(observation.runId, authorityTaskId(observation.roundId), envelope);
    return observation;
  }

  listRounds(runId: string): TeamRound[] {
    const rows = this.db.prepare("SELECT value_json FROM team_rounds WHERE run_id = ? ORDER BY world_revision").all(runId) as unknown as JsonRow[];
    return rows.map((row) => parse<TeamRound>(row.value_json, "Team Round"));
  }
  private allRounds(): TeamRound[] {
    const rows = this.db.prepare("SELECT value_json FROM team_rounds ORDER BY rowid").all() as unknown as JsonRow[];
    return rows.map((row) => parse<TeamRound>(row.value_json, "Team Round"));
  }
  listRoundsPage(runId: string, beforeRevision: number | null, limit: number): { rounds: TeamRound[]; nextBeforeRevision: number | null } {
    if (beforeRevision !== null && (!Number.isSafeInteger(beforeRevision) || beforeRevision < 0)) throw new TypeError("beforeRevision must be a non-negative integer");
    if (!Number.isSafeInteger(limit) || limit < 1 || limit > 50) throw new TypeError("timeline limit must be an integer from 1 to 50");
    const rows = (beforeRevision === null
      ? this.db.prepare("SELECT world_revision, value_json FROM team_rounds WHERE run_id = ? ORDER BY world_revision DESC LIMIT ?").all(runId, limit + 1)
      : this.db.prepare("SELECT world_revision, value_json FROM team_rounds WHERE run_id = ? AND world_revision < ? ORDER BY world_revision DESC LIMIT ?").all(runId, beforeRevision, limit + 1)) as unknown as Array<{ world_revision: number; value_json: string }>;
    const selected = rows.slice(0, limit);
    return { rounds: selected.map((row) => parse<TeamRound>(row.value_json, "Team Round")), nextBeforeRevision: rows.length > limit ? Number(selected.at(-1)?.world_revision ?? 0) : null };
  }

  verify(runId: string): void {
    this.authority.verify(runId);
    const rounds = new Map(this.listRounds(runId).map((round) => [round.roundId, round]));
    for (const round of rounds.values()) {
      if (["planned", "dispatched", "observed", "completed"].includes(round.status) && !round.tickPlanId) {
        throw new TeamStoreError("team_corrupt", `Team Round ${round.roundId} omitted TickPlan identity`);
      }
      if (["dispatched", "observed", "completed"].includes(round.status) && (!round.effectId || !round.dispatchId)) {
        throw new TeamStoreError("team_corrupt", `Team Round ${round.roundId} omitted Effect or Dispatch identity`);
      }
      if (["observed", "completed"].includes(round.status)) {
        const observation = this.findObservationForRound(round.roundId);
        if (!round.observationId || !observation || observation.observationId !== round.observationId) {
          throw new TeamStoreError("team_corrupt", `Team Round ${round.roundId} omitted its retained Observation`);
        }
        if (round.status === "completed" && !observation.verificationSuccess) {
          throw new TeamStoreError("team_corrupt", `completed Team Round ${round.roundId} has rejected Verification`);
        }
      }
    }

    for (const event of this.team.host.listJournal(runId)) {
      if (event.eventType === "team.round-completed") {
        const payload = event.payload as { round?: TeamRound };
        const retained = payload.round ? rounds.get(payload.round.roundId) : undefined;
        if (!payload.round || !retained || retained.status !== "completed" || canonicalJson(retained) !== canonicalJson(payload.round)) {
          throw new TeamStoreError("team_corrupt", "completed Team Round event differs from the retained head");
        }
      }
      if (["team.proposal-rejected", "team.proposal-player-denied", "team.proposal-verified"].includes(event.eventType)) {
        const payload = event.payload as { proposal?: ActionProposal };
        if (!payload.proposal) throw new TeamStoreError("team_corrupt", "terminal Team Proposal event omitted Proposal payload");
        const retained = this.getProposal(payload.proposal.proposalId);
        if (canonicalJson(retained) !== canonicalJson(payload.proposal)) {
          throw new TeamStoreError("team_corrupt", "terminal Team Proposal event differs from the retained head");
        }
      }
    }
  }

  private completeAuthority(round: TeamRound): void {
    const taskId = authorityTaskId(round.roundId);
    const observation = this.findObservationForRound(round.roundId);
    if (!observation) throw new Error(`Team Round has no authority Observation: ${round.roundId}`);
    const envelope = this.authority.observation(round.runId, taskId);
    const proposals = this.listProposals(round.roundId);
    const verified = new Set(observation.verifiedIntentCommandIds);
    const receipt: VerificationReceipt = {
      schemaVersion: 1, kind: "ordivon.verification-receipt", dispatchId: envelope.dispatchId,
      method: "game-team-tick.v1", accepted: observation.verificationSuccess,
      observationDigest: protocolDigest(envelope),
      resultItems: proposals.map((proposal) => ({
        subjectRef: proposal.actorTaskId,
        decisionDigest: protocolDigest(protocolSafe(proposal)),
        status: verified.has(proposal.command.commandId) ? "succeeded" : "rejected",
        reason: verified.has(proposal.command.commandId) ? null : proposal.rejectionReason ?? "not_executed",
        evidenceDigest: envelope.payloadDigest,
      })),
    };
    const verifiedProjection = this.authority.recordVerification(round.runId, taskId, receipt);
    this.authority.complete(round.runId, taskId, {
      schemaVersion: 1, kind: "ordivon.task-outcome", taskId,
      goalId: this.team.getGoal(round.runId).goalId,
      status: observation.verificationSuccess ? "completed" : "failed",
      verificationDigest: verifiedProjection.verificationDigest!, artifactRefs: [],
    });
  }
  private rejectAuthority(dispatch: TeamDispatch, reason: string): void {
    const taskId = authorityTaskId(dispatch.roundId);
    const projection = this.authority.projection(dispatch.runId, taskId);
    if (projection.state !== "reconciling") return;
    const payload = { schemaVersion: 1, kind: "ordivon.game.team-tick-rejection", reason } satisfies ProtocolJson;
    const observation: ObservationEnvelope = {
      schemaVersion: 1, kind: "ordivon.observation-envelope",
      dispatchId: wireDispatchId(dispatch.dispatchId), executorId: "executor:game-world-v1",
      status: "rejected", payloadDigest: protocolDigest(payload), evidenceRefs: [],
    };
    this.authority.recordObservation(dispatch.runId, taskId, observation);
    const receipt: VerificationReceipt = {
      schemaVersion: 1, kind: "ordivon.verification-receipt",
      dispatchId: observation.dispatchId, method: "game-team-tick.v1", accepted: false,
      observationDigest: protocolDigest(observation), resultItems: [],
    };
    const verified = this.authority.recordVerification(dispatch.runId, taskId, receipt);
    this.authority.complete(dispatch.runId, taskId, {
      schemaVersion: 1, kind: "ordivon.task-outcome", taskId,
      goalId: this.team.getGoal(dispatch.runId).goalId, status: "failed",
      verificationDigest: verified.verificationDigest!, artifactRefs: [],
    });
  }
}
