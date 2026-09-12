import { canonicalJson } from "../../../../src/digest.ts";
import type {
  TeamDispatch,
  TeamEffect,
  TeamObservation,
  TeamRound,
  TeamTickPlan,
} from "./model.ts";
import { TeamStore, TeamStoreError } from "./store.ts";

export interface TeamCommitmentProjection {
  state: "ready" | "reconciling" | "verifying" | "completed" | "failed";
  verificationDigest: null;
}

interface JsonRow { value_json: string }

function parse<T>(text: string, label: string): T {
  try { return JSON.parse(text) as T; }
  catch (error) { throw new TeamStoreError("team_corrupt", `${label} is invalid JSON: ${String(error)}`); }
}

/**
 * Derived Game commitment view.
 *
 * Team execution identity is already durably represented by TeamRound/TeamTickPlan
 * plus the authoritative Game command/event journal. This view reconstructs
 * Effect, Dispatch and Observation semantics from those owners instead of
 * persisting a second generic Host lifecycle for the same Game effect.
 */
export class DerivedTeamCommitmentView {
  readonly team: TeamStore;

  constructor(team: TeamStore) {
    this.team = team;
  }

  projection(runId: string, roundId: string): TeamCommitmentProjection {
    const round = this.round(roundId);
    if (round.runId !== runId) throw new TeamStoreError("team_corrupt", `Team Round ${roundId} belongs to another Run`);
    const state = round.status === "blocked"
      ? "failed"
      : round.status === "completed"
        ? this.findObservation(round)?.verificationSuccess === true ? "completed" : "failed"
        : round.status === "observed"
          ? "verifying"
          : round.status === "dispatched"
            ? "reconciling"
            : "ready";
    return { state, verificationDigest: null };
  }

  verify(runId: string): void {
    for (const round of this.rounds(runId)) {
      if (["observed", "completed"].includes(round.status)) {
        const observation = this.findObservation(round);
        if (!observation || observation.observationId !== round.observationId) {
          throw new TeamStoreError("team_corrupt", `Team Round ${round.roundId} has no derivable Observation`);
        }
        if (round.status === "completed" && !observation.verificationSuccess) {
          throw new TeamStoreError("team_corrupt", `completed Team Round ${round.roundId} has rejected Game evidence`);
        }
      }
    }
  }

  contractTranscript(_runId: string): [] {
    return [];
  }

  dispatchCount(runId: string): number {
    return this.rounds(runId).filter((round) => round.dispatchId !== null).length;
  }

  observationCount(runId: string): number {
    return this.rounds(runId).filter((round) => round.observationId !== null).length;
  }

  prepare(dispatch: TeamDispatch, effect: TeamEffect, plan: TeamTickPlan): TeamCommitmentProjection {
    if (dispatch.runId !== effect.runId || dispatch.runId !== plan.runId) throw new TeamStoreError("team_conflict", "Team commitment Run identity changed");
    if (dispatch.roundId !== effect.roundId || dispatch.roundId !== plan.roundId) throw new TeamStoreError("team_conflict", "Team commitment Round identity changed");
    if (dispatch.tickPlanId !== plan.tickPlanId || effect.tickPlanId !== plan.tickPlanId) throw new TeamStoreError("team_conflict", "Team commitment TickPlan identity changed");
    if (effect.effectId !== `team-effect:${plan.tickPlanId}`) throw new TeamStoreError("team_conflict", "Team Effect identity is not deterministic from TickPlan");
    if (dispatch.dispatchId !== `team-dispatch:${effect.effectId}`) throw new TeamStoreError("team_conflict", "Team Dispatch identity is not deterministic from Effect");
    if (dispatch.commandId !== `team-tick:${plan.tickPlanId}`) throw new TeamStoreError("team_conflict", "Team Dispatch command identity is not deterministic from TickPlan");
    if (effect.requiredWorldRevision !== plan.worldRevision || effect.requiredWorldDigest !== plan.worldDigest) {
      throw new TeamStoreError("team_conflict", "Team Effect world requirement differs from TickPlan");
    }
    return { state: "reconciling", verificationDigest: null };
  }

  relatedEffect(round: TeamRound): TeamEffect {
    if (!round.effectId || !round.tickPlanId) throw new Error(`Team Round omitted Effect or TickPlan identity: ${round.roundId}`);
    const plan = this.tickPlan(round.tickPlanId);
    if (plan.roundId !== round.roundId || plan.runId !== round.runId) throw new TeamStoreError("team_corrupt", "Team TickPlan ownership differs from Round");
    const observation = this.findObservation(round);
    const status: TeamEffect["status"] = round.status === "blocked"
      ? "rejected"
      : round.status === "observed" || round.status === "completed"
        ? observation?.verificationSuccess === true ? "succeeded" : "rejected"
        : round.status === "dispatched"
          ? "dispatched"
          : "prepared";
    return {
      effectId: round.effectId,
      roundId: round.roundId,
      runId: round.runId,
      tickPlanId: plan.tickPlanId,
      requiredWorldRevision: plan.worldRevision,
      requiredWorldDigest: plan.worldDigest,
      status,
      createdAt: round.updatedAt,
      updatedAt: round.updatedAt,
    };
  }

  findObservation(round: TeamRound): TeamObservation | null {
    if (!round.dispatchId || !round.effectId || !round.tickPlanId) return null;
    const plan = this.tickPlan(round.tickPlanId);
    const commandId = `team-tick:${plan.tickPlanId}`;
    const receipt = this.team.game.commandReceipt(commandId, round.runId);
    if (!receipt) return null;
    const event = receipt.journalEvent.event;
    const intentCommandIds = plan.commands.map((command) => command.commandId).sort();
    const verifiedIntentCommandIds = (event.intentReceipts ?? [])
      .filter((item) => item.verification.success)
      .map((item) => item.commandId)
      .sort();
    const observedEvent = this.team.evidence.listJournal(round.runId).find((entry) =>
      entry.eventType === "team.round-observed" && entry.eventId.startsWith(`host-event:${round.roundId}:team.round-observed:`),
    );
    return {
      observationId: `team-observation:${round.dispatchId}`,
      dispatchId: round.dispatchId,
      effectId: round.effectId,
      roundId: round.roundId,
      runId: round.runId,
      commandId,
      commandSequence: receipt.commandSequence,
      worldEventId: event.eventId,
      worldAfterDigest: event.afterDigest,
      intentCommandIds,
      verifiedIntentCommandIds,
      facts: event.facts ?? [],
      verificationSuccess: event.verification?.success === true && canonicalJson(intentCommandIds) === canonicalJson(verifiedIntentCommandIds),
      createdAt: observedEvent?.createdAt ?? round.updatedAt,
    };
  }

  recordObservation(observation: TeamObservation): TeamCommitmentProjection {
    const round = this.round(observation.roundId);
    const derived = this.findObservation(round);
    if (!derived) throw new TeamStoreError("team_corrupt", `Observation ${observation.observationId} has no authoritative Game receipt`);
    const { createdAt: _derivedCreatedAt, ...derivedStable } = derived;
    const { createdAt: _providedCreatedAt, ...providedStable } = observation;
    if (canonicalJson(derivedStable) !== canonicalJson(providedStable)) {
      throw new TeamStoreError("team_conflict", `Observation ${observation.observationId} differs from authoritative Game evidence`);
    }
    return { state: observation.verificationSuccess ? "verifying" : "failed", verificationDigest: null };
  }


  reject(_dispatch: TeamDispatch, _reason: string): TeamCommitmentProjection {
    return { state: "failed", verificationDigest: null };
  }

  private round(roundId: string): TeamRound {
    const row = this.team.db.prepare("SELECT value_json FROM team_rounds WHERE round_id = ?").get(roundId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Team Round: ${roundId}`);
    return parse<TeamRound>(row.value_json, "Team Round");
  }

  private rounds(runId: string): TeamRound[] {
    const rows = this.team.db.prepare("SELECT value_json FROM team_rounds WHERE run_id = ? ORDER BY world_revision").all(runId) as unknown as JsonRow[];
    return rows.map((row) => parse<TeamRound>(row.value_json, "Team Round"));
  }

  private tickPlan(tickPlanId: string): TeamTickPlan {
    const row = this.team.db.prepare("SELECT value_json FROM team_tick_plans WHERE tick_plan_id = ?").get(tickPlanId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Team TickPlan: ${tickPlanId}`);
    return parse<TeamTickPlan>(row.value_json, "Team TickPlan");
  }
}
