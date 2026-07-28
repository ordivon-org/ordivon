import type { DatabaseSync } from "node:sqlite";

import { canonicalJson } from "../digest.ts";
import type {
  ActionProposal,
  TeamContextReference,
  TeamDispatch,
  TeamEffect,
  TeamObservation,
  TeamRound,
  TeamTickPlan,
} from "./model.ts";
import { TeamStore, TeamStoreError } from "./store.ts";

interface JsonRow { value_json: string }

function parse<T>(text: string, label: string): T {
  try { return JSON.parse(text) as T; }
  catch (error) { throw new TeamStoreError("team_corrupt", `${label} is invalid JSON: ${String(error)}`); }
}

export class TeamExecutionStore {
  readonly db: DatabaseSync;
  readonly team: TeamStore;

  constructor(team: TeamStore) {
    this.team = team;
    this.db = team.db;
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
      CREATE TABLE IF NOT EXISTS team_context_refs (
        context_id TEXT PRIMARY KEY,
        round_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
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
      CREATE TABLE IF NOT EXISTS team_effects (
        effect_id TEXT PRIMARY KEY,
        round_id TEXT NOT NULL UNIQUE,
        run_id TEXT NOT NULL,
        status TEXT NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (round_id) REFERENCES team_rounds(round_id)
      );
      CREATE TABLE IF NOT EXISTS team_dispatches (
        dispatch_id TEXT PRIMARY KEY,
        effect_id TEXT NOT NULL UNIQUE,
        round_id TEXT NOT NULL UNIQUE,
        run_id TEXT NOT NULL,
        command_id TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (effect_id) REFERENCES team_effects(effect_id)
      );
      CREATE TABLE IF NOT EXISTS team_observations (
        observation_id TEXT PRIMARY KEY,
        dispatch_id TEXT NOT NULL UNIQUE,
        effect_id TEXT NOT NULL,
        round_id TEXT NOT NULL UNIQUE,
        run_id TEXT NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (dispatch_id) REFERENCES team_dispatches(dispatch_id)
      );
      CREATE INDEX IF NOT EXISTS team_rounds_run_idx ON team_rounds(run_id, world_revision);
      CREATE INDEX IF NOT EXISTS team_proposals_round_idx ON team_proposals(round_id, actor_id);
    `);
  }

  private put<T>(
    table: string,
    idColumn: string,
    id: string,
    record: T,
    insertColumns: string[],
    insertValues: unknown[],
    eventType: string,
    runId: string,
    createdAt: string,
  ): T {
    const existing = this.db.prepare(`SELECT value_json FROM ${table} WHERE ${idColumn} = ?`).get(id) as JsonRow | undefined;
    if (existing) {
      const retained = parse<T>(existing.value_json, table);
      if (canonicalJson(retained) !== canonicalJson(record)) {
        throw new TeamStoreError("team_conflict", `${table} identity is bound to different content`);
      }
      return retained;
    }
    const placeholders = insertColumns.map(() => "?").join(", ");
    this.team.host.withTransaction(runId, () => {
      this.db.prepare(`INSERT INTO ${table} (${insertColumns.join(", ")}, value_json) VALUES (${placeholders}, ?)`)
        .run(...([...insertValues, canonicalJson(record)] as never[]));
      this.team.host.appendEventInTransaction(runId, eventType, `host-event:${id}:created`, { record }, createdAt);
    });
    return record;
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

  saveRound(round: TeamRound, eventType: string): TeamRound {
    const current = this.getRound(round.roundId);
    if (current.runId !== round.runId || current.worldRevision !== round.worldRevision) throw new TeamStoreError("team_conflict", "Team Round identity changed");
    this.team.host.withTransaction(round.runId, () => {
      this.db.prepare("UPDATE team_rounds SET status = ?, value_json = ? WHERE round_id = ?")
        .run(round.status, canonicalJson(round), round.roundId);
      this.team.host.appendEventInTransaction(round.runId, eventType,
        `host-event:${round.roundId}:${eventType}:${round.updatedAt}`, { round }, round.updatedAt);
    });
    return round;
  }

  putContext(reference: TeamContextReference): TeamContextReference {
    return this.put("team_context_refs", "context_id", reference.contextId, reference,
      ["context_id", "round_id", "run_id", "actor_id", "task_id", "world_revision", "artifact_digest"],
      [reference.contextId, reference.roundId, reference.runId, reference.actorId, reference.taskId, reference.worldRevision, reference.artifactDigest],
      "team.context-prepared", reference.runId, reference.createdAt);
  }

  listContexts(roundId: string): TeamContextReference[] {
    const rows = this.db.prepare("SELECT value_json FROM team_context_refs WHERE round_id = ? ORDER BY actor_id").all(roundId) as unknown as JsonRow[];
    return rows.map((row) => parse<TeamContextReference>(row.value_json, "Team Context Reference"));
  }

  findContextForActor(roundId: string, actorId: string): TeamContextReference | null {
    const row = this.db.prepare("SELECT value_json FROM team_context_refs WHERE round_id = ? AND actor_id = ?").get(roundId, actorId) as JsonRow | undefined;
    return row ? parse<TeamContextReference>(row.value_json, "Team Context Reference") : null;
  }

  putProposal(proposal: ActionProposal): ActionProposal {
    return this.put("team_proposals", "proposal_id", proposal.proposalId, proposal,
      ["proposal_id", "round_id", "run_id", "actor_id", "status"],
      [proposal.proposalId, proposal.roundId, proposal.runId, proposal.actorId, proposal.status],
      "team.proposal-recorded", proposal.runId, proposal.createdAt);
  }

  saveProposal(proposal: ActionProposal, eventType: string): ActionProposal {
    const current = this.getProposal(proposal.proposalId);
    if (current.roundId !== proposal.roundId || current.actorId !== proposal.actorId) throw new TeamStoreError("team_conflict", "Team Proposal identity changed");
    this.team.host.withTransaction(proposal.runId, () => {
      this.db.prepare("UPDATE team_proposals SET status = ?, value_json = ? WHERE proposal_id = ?")
        .run(proposal.status, canonicalJson(proposal), proposal.proposalId);
      this.team.host.appendEventInTransaction(proposal.runId, eventType,
        `host-event:${proposal.proposalId}:${eventType}:${proposal.updatedAt}`, { proposal }, proposal.updatedAt);
    });
    return proposal;
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
    return this.put("team_effects", "effect_id", effect.effectId, effect,
      ["effect_id", "round_id", "run_id", "status"], [effect.effectId, effect.roundId, effect.runId, effect.status],
      "team.effect-prepared", effect.runId, effect.createdAt);
  }

  getEffect(effectId: string): TeamEffect {
    const row = this.db.prepare("SELECT value_json FROM team_effects WHERE effect_id = ?").get(effectId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Team Effect: ${effectId}`);
    return parse<TeamEffect>(row.value_json, "Team Effect");
  }

  saveEffect(effect: TeamEffect, eventType: string): TeamEffect {
    this.getEffect(effect.effectId);
    this.team.host.withTransaction(effect.runId, () => {
      this.db.prepare("UPDATE team_effects SET status = ?, value_json = ? WHERE effect_id = ?")
        .run(effect.status, canonicalJson(effect), effect.effectId);
      this.team.host.appendEventInTransaction(effect.runId, eventType,
        `host-event:${effect.effectId}:${eventType}:${effect.updatedAt}`, { effect }, effect.updatedAt);
    });
    return effect;
  }

  putDispatch(dispatch: TeamDispatch): TeamDispatch {
    return this.put("team_dispatches", "dispatch_id", dispatch.dispatchId, dispatch,
      ["dispatch_id", "effect_id", "round_id", "run_id", "command_id", "status"],
      [dispatch.dispatchId, dispatch.effectId, dispatch.roundId, dispatch.runId, dispatch.commandId, dispatch.status],
      "team.dispatch-prepared", dispatch.runId, dispatch.createdAt);
  }

  getDispatch(dispatchId: string): TeamDispatch {
    const row = this.db.prepare("SELECT value_json FROM team_dispatches WHERE dispatch_id = ?").get(dispatchId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Team Dispatch: ${dispatchId}`);
    return parse<TeamDispatch>(row.value_json, "Team Dispatch");
  }

  saveDispatch(dispatch: TeamDispatch, eventType: string): TeamDispatch {
    this.getDispatch(dispatch.dispatchId);
    this.team.host.withTransaction(dispatch.runId, () => {
      this.db.prepare("UPDATE team_dispatches SET status = ?, value_json = ? WHERE dispatch_id = ?")
        .run(dispatch.status, canonicalJson(dispatch), dispatch.dispatchId);
      this.team.host.appendEventInTransaction(dispatch.runId, eventType,
        `host-event:${dispatch.dispatchId}:${eventType}:${dispatch.updatedAt}`, { dispatch }, dispatch.updatedAt);
    });
    return dispatch;
  }

  findObservationForRound(roundId: string): TeamObservation | null {
    const row = this.db.prepare("SELECT value_json FROM team_observations WHERE round_id = ?").get(roundId) as JsonRow | undefined;
    return row ? parse<TeamObservation>(row.value_json, "Team Observation") : null;
  }

  putObservation(observation: TeamObservation): TeamObservation {
    return this.put("team_observations", "observation_id", observation.observationId, observation,
      ["observation_id", "dispatch_id", "effect_id", "round_id", "run_id"],
      [observation.observationId, observation.dispatchId, observation.effectId, observation.roundId, observation.runId],
      "team.observation-recorded", observation.runId, observation.createdAt);
  }

  listRounds(runId: string): TeamRound[] {
    const rows = this.db.prepare("SELECT value_json FROM team_rounds WHERE run_id = ? ORDER BY world_revision").all(runId) as unknown as JsonRow[];
    return rows.map((row) => parse<TeamRound>(row.value_json, "Team Round"));
  }

  listRoundsPage(
    runId: string,
    beforeRevision: number | null,
    limit: number,
  ): { rounds: TeamRound[]; nextBeforeRevision: number | null } {
    if (beforeRevision !== null && (!Number.isSafeInteger(beforeRevision) || beforeRevision < 0)) {
      throw new TypeError("beforeRevision must be a non-negative integer");
    }
    if (!Number.isSafeInteger(limit) || limit < 1 || limit > 50) {
      throw new TypeError("timeline limit must be an integer from 1 to 50");
    }
    const rows = (beforeRevision === null
      ? this.db.prepare("SELECT world_revision, value_json FROM team_rounds WHERE run_id = ? ORDER BY world_revision DESC LIMIT ?")
          .all(runId, limit + 1)
      : this.db.prepare("SELECT world_revision, value_json FROM team_rounds WHERE run_id = ? AND world_revision < ? ORDER BY world_revision DESC LIMIT ?")
          .all(runId, beforeRevision, limit + 1)) as unknown as Array<{ world_revision: number; value_json: string }>;
    const hasMore = rows.length > limit;
    const selected = rows.slice(0, limit);
    const rounds = selected.map((row) => parse<TeamRound>(row.value_json, "Team Round"));
    return {
      rounds,
      nextBeforeRevision: hasMore ? Number(selected.at(-1)?.world_revision ?? 0) : null,
    };
  }
}
