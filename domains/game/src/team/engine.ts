import { canonicalJson, sha256 } from "../digest.ts";
import type { PrimitiveWorldCommand, WorldState } from "../model.ts";
import { ProviderAdapterError } from "../providers/types.ts";
import type { GameStore } from "../storage.ts";
import { applyWorldTickV3 } from "../world.ts";
import { authorityTargetId, candidateAllowed, evaluateAuthority } from "./authority.ts";
import { compileTeamContext } from "./context.ts";
import { TeamExecutionStore } from "./execution-store.ts";
import type {
  ActionProposal,
  ActorProfile,
  AuthorityGrant,
  AuthorityPolicyMode,
  CompiledTeamContext,
  ResourceClaim,
  TeamContextReference,
  TeamDispatch,
  TeamEffect,
  TeamObservation,
  TeamProjection,
  TeamRound,
  TeamTickPlan,
} from "./model.ts";
import { nextObjectiveForRole } from "./objectives.ts";
import {
  admitTeamProviderDecision,
  TeamDecisionAdmissionError,
  type TeamDecisionProvider,
} from "./providers.ts";
import { coordinatorTaskId, TeamStore } from "./store.ts";

export type TeamFaultPoint =
  | "after_context_persisted"
  | "after_provider_call"
  | "after_proposal_persisted"
  | "after_tick_plan_persisted"
  | "after_dispatch_prepared"
  | "after_world_apply"
  | "after_observation_persisted"
  | "before_task_advance";

export interface TeamHostOptions {
  policyMode?: AuthorityPolicyMode;
  faultInjector?: (point: TeamFaultPoint) => void;
  ownerId?: string;
  tokenBudget?: number;
}

export interface TeamHostStepReceipt {
  runId: string;
  roundId: string | null;
  status:
    | "initialized"
    | "contexts_prepared"
    | "proposals_recorded"
    | "tick_plan_prepared"
    | "dispatch_prepared"
    | "world_tick_observed"
    | "round_verified"
    | "authority_required"
    | "blocked"
    | "terminal"
    | "stable";
  worldRevision: number;
  worldDigest: string;
  actorIds: string[];
  proposalIds: string[];
  selectedProposalIds: string[];
  detail: string;
}

export interface TeamHostRunReceipt {
  runId: string;
  steps: TeamHostStepReceipt[];
  projection: TeamProjection;
  rounds: TeamRound[];
  worldRevision: number;
  worldDigest: string;
}

function now(): string {
  return new Date().toISOString();
}

function commandTarget(command: PrimitiveWorldCommand): string | null {
  switch (command.kind) {
    case "repair_system":
    case "set_power": return `system:${command.targetSystemId}`;
    case "seal_hull":
    case "contain_hazard": return `hazard:${command.targetHazardId}`;
    case "stabilize_crew": return `crew:${command.targetCrewId}`;
    case "send_distress": return "mission:distress";
    case "move":
    case "pickup_item":
    case "wait": return null;
  }
}

function resourceClaims(command: PrimitiveWorldCommand, state: WorldState): ResourceClaim[] {
  const claims: ResourceClaim[] = [{ kind: "actor", resourceId: command.actorId, quantity: 1 }];
  const target = commandTarget(command);
  if (target) claims.push({ kind: "mutable-target", resourceId: target, quantity: 1 });
  if (command.kind === "pickup_item") {
    const roomId = state.agents[command.actorId]?.location ?? "unknown";
    claims.push({ kind: "inventory", resourceId: `${roomId}:${command.itemId}`, quantity: command.quantity });
  }
  if (command.kind === "repair_system") claims.push({ kind: "inventory", resourceId: `${command.actorId}:spare-parts`, quantity: 1 });
  if (command.kind === "seal_hull") claims.push({ kind: "inventory", resourceId: `${command.actorId}:sealant`, quantity: 1 });
  if (command.kind === "stabilize_crew") claims.push({ kind: "inventory", resourceId: `${command.actorId}:medkit`, quantity: 1 });
  return claims;
}


export class TeamHost {
  readonly game: GameStore;
  readonly team: TeamStore;
  readonly execution: TeamExecutionStore;
  readonly policyMode: AuthorityPolicyMode;
  readonly ownerId: string;
  readonly tokenBudget: number;
  readonly faultInjector: ((point: TeamFaultPoint) => void) | undefined;
  private readonly providers: TeamDecisionProvider | Record<string, TeamDecisionProvider>;

  constructor(
    game: GameStore,
    providers: TeamDecisionProvider | Record<string, TeamDecisionProvider>,
    options: TeamHostOptions = {},
  ) {
    this.game = game;
    this.team = new TeamStore(game);
    this.execution = new TeamExecutionStore(this.team);
    this.providers = providers;
    this.policyMode = options.policyMode ?? "autonomous";
    this.ownerId = options.ownerId ?? `team-host:${process.pid}`;
    this.tokenBudget = options.tokenBudget ?? 4_000;
    this.faultInjector = options.faultInjector;
  }

  initialize(runId = this.game.activeRunId): TeamProjection {
    return this.team.initialize(runId);
  }

  private providerFor(actorId: string): TeamDecisionProvider {
    if (typeof (this.providers as TeamDecisionProvider).decide === "function") {
      return this.providers as TeamDecisionProvider;
    }
    const provider = (this.providers as Record<string, TeamDecisionProvider>)[actorId];
    if (!provider) throw new Error(`no Team Provider configured for ${actorId}`);
    return provider;
  }

  private inject(point: TeamFaultPoint): void {
    this.faultInjector?.(point);
  }

  private receipt(
    runId: string,
    status: TeamHostStepReceipt["status"],
    detail: string,
    round: TeamRound | null = null,
  ): TeamHostStepReceipt {
    const state = this.game.loadState(runId);
    const proposals = round ? this.execution.listProposals(round.roundId) : [];
    return {
      runId,
      roundId: round?.roundId ?? null,
      status,
      worldRevision: state.revision,
      worldDigest: sha256(state),
      actorIds: proposals.map((proposal) => proposal.actorId),
      proposalIds: proposals.map((proposal) => proposal.proposalId),
      selectedProposalIds: proposals.filter((proposal) => proposal.status === "selected" || proposal.status === "executed" || proposal.status === "verified").map((proposal) => proposal.proposalId),
      detail,
    };
  }

  async step(runId = this.game.activeRunId): Promise<TeamHostStepReceipt> {
    const projection = this.initialize(runId);
    this.game.verifyStream(runId);
    this.team.verify(runId);
    const state = this.game.loadState(runId);
    const unsettled = [...this.execution.listRounds(runId)].reverse().find((candidate) =>
      candidate.status !== "completed" && candidate.status !== "blocked");
    if (unsettled && unsettled.worldRevision < state.revision) {
      if (unsettled.status === "dispatched") return this.executeAndObserve(runId, unsettled);
      if (unsettled.status === "observed") return this.verifyRound(runId, unsettled);
      const blocked = this.execution.saveRound({
        ...unsettled,
        status: "blocked",
        blocker: "world_drift",
        updatedAt: now(),
      }, "team.round-blocked");
      return this.receipt(runId, "blocked", "World advanced before the Team Round committed", blocked);
    }
    if (state.mission.status !== "running") {
      this.team.synchronizeTerminal(runId);
      return this.receipt(runId, "terminal", state.mission.reason ?? state.mission.status);
    }

    let round = this.execution.findRound(runId, state.revision);
    if (!round) {
      const createdAt = now();
      round = this.execution.putRound({
        roundId: `team-round:${sha256({ runId, worldRevision: state.revision, worldDigest: sha256(state) })}`,
        runId,
        worldRevision: state.revision,
        worldDigest: sha256(state),
        status: "collecting",
        contextIds: [],
        resolvedActorIds: [],
        proposalIds: [],
        tickPlanId: null,
        effectId: null,
        dispatchId: null,
        observationId: null,
        blocker: null,
        createdAt,
        updatedAt: createdAt,
      });
      return this.receipt(runId, "initialized", "Created Team Round", round);
    }

    const eligibleProfiles = projection.profiles.filter((profile) => (state.agents[profile.actorId]?.health ?? 0) > 0);
    const contexts = this.execution.listContexts(round.roundId);
    if (contexts.length < eligibleProfiles.length) return this.prepareContexts(runId, round, eligibleProfiles);
    const proposals = this.execution.listProposals(round.roundId);
    if (round.resolvedActorIds.length < contexts.length) return await this.collectProposals(runId, round, eligibleProfiles, contexts);
    if (!round.tickPlanId) return this.prepareTickPlan(runId, round, proposals);
    if (!round.dispatchId) return this.prepareDispatch(runId, round);
    if (!round.observationId) return this.executeAndObserve(runId, round);
    if (round.status !== "completed") return this.verifyRound(runId, round);
    return this.receipt(runId, "stable", "Team Round already completed", round);
  }

  async run(runId = this.game.activeRunId, maximumSteps = 256): Promise<TeamHostRunReceipt> {
    if (!Number.isSafeInteger(maximumSteps) || maximumSteps < 1) throw new TypeError("maximumSteps must be positive");
    const steps: TeamHostStepReceipt[] = [];
    for (let index = 0; index < maximumSteps; index += 1) {
      const receipt = await this.step(runId);
      steps.push(receipt);
      const state = this.game.loadState(runId);
      if (state.mission.status !== "running" && (receipt.status === "round_verified" || receipt.status === "terminal")) break;
      if (receipt.status === "authority_required" || receipt.status === "blocked") break;
    }
    const state = this.game.loadState(runId);
    return {
      runId,
      steps,
      projection: this.team.projection(runId),
      rounds: this.execution.listRounds(runId),
      worldRevision: state.revision,
      worldDigest: sha256(state),
    };
  }

  private prepareContexts(runId: string, round: TeamRound, profiles: ActorProfile[]): TeamHostStepReceipt {
    const state = this.game.loadState(runId);
    const messages = this.team.refreshMessages(runId);
    const contextIds = this.execution.listContexts(round.roundId).map((reference) => reference.contextId);
    for (const profile of profiles) {
      if (this.execution.findContextForActor(round.roundId, profile.actorId)) continue;
      const task = this.team.listTasks(runId).find((candidate) => candidate.actorId === profile.actorId);
      if (!task) throw new Error(`Actor Task missing for ${profile.actorId}`);
      if ((state.agents[profile.actorId]?.health ?? 0) <= 0) continue;
      const lease = this.team.acquireLease(task.taskId, this.ownerId);
      try {
        const currentTask = this.team.getTask(task.taskId);
        const context = compileTeamContext({
          store: this.game,
          runId,
          task: currentTask,
          profile,
          goal: this.team.getGoal(runId),
          messages,
          policyMode: this.policyMode,
          tokenBudget: this.tokenBudget,
        });
        const artifact = this.team.host.putArtifact("team-context-v1", context);
        const createdAt = now();
        const reference: TeamContextReference = {
          contextId: context.contextId,
          roundId: round.roundId,
          runId,
          actorId: profile.actorId,
          taskId: currentTask.taskId,
          taskRevision: currentTask.revision,
          worldRevision: state.revision,
          worldDigest: sha256(state),
          artifactDigest: artifact.digest,
          createdAt,
        };
        this.execution.putContext(reference);
        this.team.transitionTask(currentTask.taskId, {
          state: "running",
          preparedContextDigest: artifact.digest,
          admittedProposalId: null,
          wait: null,
          lastWorldRevision: state.revision,
        }, "team.task-context-prepared", { contextId: context.contextId, roundId: round.roundId });
        contextIds.push(context.contextId);
        this.inject("after_context_persisted");
      } finally {
        this.team.releaseLease(lease);
      }
    }
    const updated = this.execution.saveRound({ ...round, contextIds: [...new Set(contextIds)].sort(), updatedAt: now() }, "team.round-contexts-prepared");
    return this.receipt(runId, "contexts_prepared", `Prepared ${updated.contextIds.length} Actor Contexts`, updated);
  }

  private async collectProposals(
    runId: string,
    round: TeamRound,
    profiles: ActorProfile[],
    contexts: TeamContextReference[],
  ): Promise<TeamHostStepReceipt> {
    const stateBefore = this.game.loadState(runId);
    const retainedProposals = this.execution.listProposals(round.roundId);
    const resolved = new Set([...round.resolvedActorIds, ...retainedProposals.map((proposal) => proposal.actorId)]);
    const missing = contexts.filter((reference) => !resolved.has(reference.actorId));
    const results = await Promise.allSettled(missing.map(async (reference) => {
      const context = this.team.host.getArtifact<CompiledTeamContext>(reference.artifactDigest).content;
      const decision = await this.providerFor(reference.actorId).decide(context);
      return { reference, context, decision };
    }));
    this.inject("after_provider_call");

    const proposalIds = retainedProposals.map((proposal) => proposal.proposalId);
    const resolvedActorIds = [...resolved];
    for (let index = 0; index < results.length; index += 1) {
      const result = results[index];
      const reference = missing[index];
      if (!result || !reference) continue;
      const profile = profiles.find((candidate) => candidate.actorId === reference.actorId);
      if (!profile) throw new Error(`Team Profile missing for ${reference.actorId}`);
      resolvedActorIds.push(reference.actorId);
      const task = this.team.getTask(reference.taskId);
      if (task.revision !== reference.taskRevision + 1 || task.preparedContextDigest !== reference.artifactDigest) {
        this.team.setWait(task.taskId, {
          kind: "replan",
          subjectId: reference.contextId,
          reason: "Actor Task changed after Context preparation",
          sinceTick: stateBefore.turn,
        });
        continue;
      }
      if (result.status === "rejected") {
        const reason = result.reason instanceof Error ? result.reason.message : String(result.reason);
        this.team.setWait(task.taskId, { kind: "provider", subjectId: reference.contextId, reason, sinceTick: stateBefore.turn });
        continue;
      }
      const { context, decision } = result.value;
      const currentState = this.game.loadState(runId);
      let candidate;
      try {
        candidate = admitTeamProviderDecision(context, currentState, sha256(currentState), decision);
      } catch (error) {
        if (!(error instanceof TeamDecisionAdmissionError)) throw error;
        this.team.setWait(task.taskId, { kind: "replan", subjectId: reference.contextId, reason: error.message, sinceTick: currentState.turn });
        continue;
      }
      if (!candidate) {
        this.team.setWait(task.taskId, { kind: "provider", subjectId: reference.contextId, reason: "Provider declined every admitted Action", sinceTick: currentState.turn });
        continue;
      }
      const actor = currentState.agents[reference.actorId];
      if (!actor) throw new Error(`World Actor disappeared: ${reference.actorId}`);
      const authority = this.team.putAuthorityDecision(evaluateAuthority(
        runId,
        profile,
        actor.capabilities,
        candidate.actionCandidateId,
        context.contextId,
        context.worldDigest,
        currentState,
        candidate.command,
        this.policyMode,
      ));
      const createdAt = now();
      const identity = {
        roundId: round.roundId,
        actorId: reference.actorId,
        actorTaskRevision: task.revision,
        contextId: context.contextId,
        actionCandidateId: candidate.actionCandidateId,
        command: candidate.command,
        authorityDecisionId: authority.decisionId,
        providerId: decision.providerId,
      };
      const proposal: ActionProposal = {
        proposalId: `team-proposal:${sha256(identity)}`,
        roundId: round.roundId,
        runId,
        actorId: reference.actorId,
        actorTaskId: task.taskId,
        actorTaskRevision: task.revision,
        contextId: context.contextId,
        contextDigest: reference.artifactDigest,
        worldDigest: context.worldDigest,
        worldRevision: context.worldRevision,
        actionCandidateId: candidate.actionCandidateId,
        command: candidate.command,
        objectiveIds: task.activeObjectiveId ? [task.activeObjectiveId] : candidate.objectiveIds,
        authorityDecisionId: authority.decisionId,
        authorityOutcome: authority.outcome,
        resourceClaims: resourceClaims(candidate.command, currentState),
        providerId: decision.providerId,
        confidence: decision.confidence,
        rationale: decision.rationale,
        status: "proposed",
        rejectionReason: null,
        createdAt,
        updatedAt: createdAt,
      };
      this.execution.putProposal(proposal);
      this.team.transitionTask(task.taskId, {
        state: authority.outcome === "deny" ? "blocked" : authority.outcome === "require-human" ? "waiting" : "running",
        admittedProposalId: proposal.proposalId,
        wait: authority.outcome === "require-human"
          ? { kind: "authority", subjectId: proposal.proposalId, reason: authority.reason, sinceTick: currentState.turn }
          : authority.outcome === "deny"
            ? { kind: "authority", subjectId: proposal.proposalId, reason: authority.reason, sinceTick: currentState.turn }
            : null,
      }, "team.task-proposal-recorded", { proposalId: proposal.proposalId, authorityDecisionId: authority.decisionId });
      proposalIds.push(proposal.proposalId);
      this.inject("after_proposal_persisted");
    }
    const updated = this.execution.saveRound({
      ...round,
      resolvedActorIds: [...new Set(resolvedActorIds)].sort(),
      proposalIds: [...new Set(proposalIds)].sort(),
      updatedAt: now(),
    }, "team.round-proposals-recorded");
    return this.receipt(runId, "proposals_recorded", `Recorded ${updated.proposalIds.length} Action Proposals`, updated);
  }

  private validGrant(proposal: ActionProposal, grants: AuthorityGrant[], tick: number): AuthorityGrant | null {
    return grants.find((grant) =>
      grant.proposalId === proposal.proposalId &&
      grant.actorId === proposal.actorId &&
      grant.actionCandidateId === proposal.actionCandidateId &&
      grant.contextDigest === proposal.contextId &&
      grant.worldDigest === proposal.worldDigest &&
      grant.operationKind === proposal.command.kind &&
      grant.targetId === authorityTargetId(proposal.command) &&
      grant.consumedAtTick === null &&
      tick <= grant.expiresAtTick
    ) ?? null;
  }

  private legalSubsets(runId: string, round: TeamRound, proposals: ActionProposal[]): ActionProposal[][] {
    const state = this.game.loadState(runId);
    const grants = this.team.listAuthorityGrants(runId);
    const eligible = proposals.filter((proposal) => candidateAllowed(
      { authorityOutcome: proposal.authorityOutcome },
      this.validGrant(proposal, grants, state.turn) !== null,
    ));
    const subsets: ActionProposal[][] = [];
    for (let mask = 1; mask < (1 << eligible.length); mask += 1) {
      const subset = eligible.filter((_, index) => (mask & (1 << index)) !== 0);
      const result = applyWorldTickV3(state, {
        tickId: `probe:${round.roundId}:${mask}`,
        expectedWorldRevision: round.worldRevision,
        intents: subset.map((proposal, index) => ({ commandSequence: index, command: proposal.command })),
      });
      if (result.status === "accepted") subsets.push(subset);
    }
    return subsets;
  }

  private prepareTickPlan(runId: string, round: TeamRound, proposals: ActionProposal[]): TeamHostStepReceipt {
    const legal = this.legalSubsets(runId, round, proposals);
    const state = this.game.loadState(runId);
    const grants = this.team.listAuthorityGrants(runId);
    const authorityPending = proposals.some((proposal) =>
      proposal.authorityOutcome === "require-human" && this.validGrant(proposal, grants, state.turn) === null);
    const productiveLegal = legal.filter((subset) => subset.some((proposal) => proposal.command.kind !== "wait"));
    if (legal.length === 0 || (authorityPending && productiveLegal.length === 0)) {
      const updated = this.execution.saveRound({
        ...round,
        status: "blocked",
        blocker: authorityPending ? "authority_required" : "no_legal_proposal_subset",
        updatedAt: now(),
      }, "team.round-blocked");
      return this.receipt(runId, authorityPending ? "authority_required" : "blocked", updated.blocker ?? "blocked", updated);
    }
    legal.sort((left, right) =>
      right.filter((proposal) => proposal.command.kind !== "wait").length - left.filter((proposal) => proposal.command.kind !== "wait").length ||
      right.length - left.length ||
      left.map((proposal) => proposal.proposalId).sort().join("|").localeCompare(right.map((proposal) => proposal.proposalId).sort().join("|"))
    );
    const selected = legal[0] ?? [];
    const selectedIds = new Set(selected.map((proposal) => proposal.proposalId));
    const rejected = proposals.filter((proposal) => !selectedIds.has(proposal.proposalId));
    const createdAt = now();
    const identity = {
      roundId: round.roundId,
      worldRevision: round.worldRevision,
      worldDigest: round.worldDigest,
      selectedProposalIds: [...selectedIds].sort(),
    };
    const plan: TeamTickPlan = {
      tickPlanId: `team-tick-plan:${sha256(identity)}`,
      roundId: round.roundId,
      runId,
      worldRevision: round.worldRevision,
      worldDigest: round.worldDigest,
      selectedProposalIds: [...selectedIds].sort(),
      rejectedProposalIds: rejected.map((proposal) => proposal.proposalId).sort(),
      commands: selected.map((proposal) => proposal.command).sort((a, b) => a.actorId.localeCompare(b.actorId)),
      policyDecisionRefs: selected.map((proposal) => proposal.authorityDecisionId).sort(),
      createdAt,
    };
    this.execution.putTickPlan(plan);
    for (const proposal of selected) {
      const grant = this.validGrant(proposal, this.team.listAuthorityGrants(runId), this.game.loadState(runId).turn);
      if (proposal.authorityOutcome === "require-human" && grant) {
        this.team.consumeGrant(grant.grantId, proposal.proposalId, proposal.contextId, proposal.worldDigest, this.game.loadState(runId).turn);
      }
      this.execution.saveProposal({ ...proposal, status: "selected", updatedAt: createdAt }, "team.proposal-selected");
    }
    for (const proposal of rejected) {
      this.execution.saveProposal({ ...proposal, status: "rejected", rejectionReason: "not_selected_in_compatible_subset", updatedAt: createdAt }, "team.proposal-rejected");
    }
    const updated = this.execution.saveRound({ ...round, status: "planned", tickPlanId: plan.tickPlanId, blocker: null, updatedAt: createdAt }, "team.round-planned");
    this.inject("after_tick_plan_persisted");
    return this.receipt(runId, "tick_plan_prepared", `Selected ${selected.length} compatible Proposals`, updated);
  }

  private prepareDispatch(runId: string, round: TeamRound): TeamHostStepReceipt {
    if (!round.tickPlanId) throw new Error("Team Round has no TickPlan");
    const plan = this.execution.getTickPlan(round.tickPlanId);
    const createdAt = now();
    const effect: TeamEffect = {
      effectId: `team-effect:${plan.tickPlanId}`,
      roundId: round.roundId,
      runId,
      tickPlanId: plan.tickPlanId,
      requiredWorldRevision: plan.worldRevision,
      requiredWorldDigest: plan.worldDigest,
      status: "prepared",
      createdAt,
      updatedAt: createdAt,
    };
    this.execution.putEffect(effect);
    const dispatch: TeamDispatch = {
      dispatchId: `team-dispatch:${effect.effectId}`,
      effectId: effect.effectId,
      roundId: round.roundId,
      runId,
      tickPlanId: plan.tickPlanId,
      commandId: `team-tick:${plan.tickPlanId}`,
      status: "pending",
      worldEventId: null,
      commandSequence: null,
      error: null,
      createdAt,
      updatedAt: createdAt,
    };
    this.execution.putDispatch(dispatch);
    const updated = this.execution.saveRound({ ...round, status: "dispatched", effectId: effect.effectId, dispatchId: dispatch.dispatchId, updatedAt: createdAt }, "team.round-dispatch-prepared");
    this.inject("after_dispatch_prepared");
    return this.receipt(runId, "dispatch_prepared", `Prepared ${dispatch.dispatchId}`, updated);
  }

  private executeAndObserve(runId: string, round: TeamRound): TeamHostStepReceipt {
    if (!round.tickPlanId || !round.effectId || !round.dispatchId) throw new Error("Team Round is not dispatchable");
    const plan = this.execution.getTickPlan(round.tickPlanId);
    let effect = this.execution.getEffect(round.effectId);
    let dispatch = this.execution.getDispatch(round.dispatchId);
    let receipt = this.game.commandReceipt(dispatch.commandId, runId);
    if (!receipt) {
      const state = this.game.loadState(runId);
      if (state.revision !== effect.requiredWorldRevision || sha256(state) !== effect.requiredWorldDigest) {
        dispatch = this.execution.saveDispatch({ ...dispatch, status: "rejected", error: "stale_world", updatedAt: now() }, "team.dispatch-rejected");
        effect = this.execution.saveEffect({ ...effect, status: "rejected", updatedAt: now() }, "team.effect-rejected");
        const blocked = this.execution.saveRound({ ...round, status: "blocked", blocker: "stale_world", updatedAt: now() }, "team.round-blocked");
        return this.receipt(runId, "blocked", "World changed before Team Dispatch", blocked);
      }
      const applied = this.game.applyTeamTick({
        tickId: plan.tickPlanId,
        expectedWorldRevision: plan.worldRevision,
        intents: plan.commands.map((command, index) => ({ commandSequence: index, command })),
      }, runId);
      if (applied.result.status !== "accepted") {
        dispatch = this.execution.saveDispatch({ ...dispatch, status: "rejected", error: `${applied.result.code}:${applied.result.reason}`, updatedAt: now() }, "team.dispatch-rejected");
        effect = this.execution.saveEffect({ ...effect, status: "rejected", updatedAt: now() }, "team.effect-rejected");
        const blocked = this.execution.saveRound({ ...round, status: "blocked", blocker: applied.result.code, updatedAt: now() }, "team.round-blocked");
        return this.receipt(runId, "blocked", applied.result.reason, blocked);
      }
      this.inject("after_world_apply");
      receipt = this.game.commandReceipt(dispatch.commandId, runId);
    }
    if (!receipt) throw new Error("accepted Team Tick has no retained receipt");
    const event = receipt.journalEvent.event;
    const intentCommandIds = plan.commands.map((command) => command.commandId).sort();
    const verifiedIntentCommandIds = (event.intentReceipts ?? []).filter((item) => item.verification.success).map((item) => item.commandId).sort();
    const createdAt = now();
    const observation: TeamObservation = {
      observationId: `team-observation:${dispatch.dispatchId}`,
      dispatchId: dispatch.dispatchId,
      effectId: effect.effectId,
      roundId: round.roundId,
      runId,
      commandId: dispatch.commandId,
      commandSequence: receipt.commandSequence,
      worldEventId: event.eventId,
      worldAfterDigest: event.afterDigest,
      intentCommandIds,
      verifiedIntentCommandIds,
      facts: event.facts ?? [],
      verificationSuccess: event.verification?.success === true && canonicalJson(intentCommandIds) === canonicalJson(verifiedIntentCommandIds),
      createdAt,
    };
    this.execution.putObservation(observation);
    dispatch = this.execution.saveDispatch({ ...dispatch, status: "succeeded", worldEventId: event.eventId, commandSequence: receipt.commandSequence, error: null, updatedAt: createdAt }, "team.dispatch-succeeded");
    effect = this.execution.saveEffect({ ...effect, status: observation.verificationSuccess ? "succeeded" : "rejected", updatedAt: createdAt }, observation.verificationSuccess ? "team.effect-succeeded" : "team.effect-rejected");
    const updated = this.execution.saveRound({ ...round, status: "observed", observationId: observation.observationId, updatedAt: createdAt }, "team.round-observed");
    this.inject("after_observation_persisted");
    return this.receipt(runId, "world_tick_observed", `Observed ${verifiedIntentCommandIds.length} verified Intents`, updated);
  }

  private verifyRound(runId: string, round: TeamRound): TeamHostStepReceipt {
    const observation = this.execution.findObservationForRound(round.roundId);
    if (!observation || !observation.verificationSuccess) {
      const blocked = this.execution.saveRound({ ...round, status: "blocked", blocker: "verification_failed", updatedAt: now() }, "team.round-blocked");
      return this.receipt(runId, "blocked", "Team Tick Verification failed", blocked);
    }
    this.inject("before_task_advance");
    const state = this.game.loadState(runId);
    const proposals = this.execution.listProposals(round.roundId);
    const verified = new Set(observation.verifiedIntentCommandIds);
    for (const proposal of proposals) {
      const success = verified.has(proposal.command.commandId);
      const updatedAt = now();
      this.execution.saveProposal({
        ...proposal,
        status: success ? "verified" : proposal.status === "rejected" ? "rejected" : "rejected",
        rejectionReason: success ? null : proposal.rejectionReason ?? "not_executed",
        updatedAt,
      }, success ? "team.proposal-verified" : "team.proposal-not-executed");
      const task = this.team.getTask(proposal.actorTaskId);
      const profile = this.team.getProfile(proposal.actorId, runId);
      this.team.transitionTask(task.taskId, {
        state: state.mission.status === "running" ? "ready" : state.mission.status === "victory" ? "completed" : "failed",
        activeObjectiveId: nextObjectiveForRole(state, profile.role),
        preparedContextDigest: null,
        admittedProposalId: null,
        wait: null,
        lastWorldRevision: state.revision,
      }, "team.task-round-verified", { roundId: round.roundId, proposalId: proposal.proposalId, success });
    }
    const coordinator = this.team.getTask(coordinatorTaskId(runId));
    this.team.transitionTask(coordinator.taskId, {
      state: state.mission.status === "running" ? "ready" : state.mission.status === "victory" ? "completed" : "failed",
      activeObjectiveId: nextObjectiveForRole(state, "coordinator"),
      preparedContextDigest: null,
      admittedProposalId: null,
      wait: null,
      lastWorldRevision: state.revision,
    }, "team.coordinator-round-verified", { roundId: round.roundId, observationId: observation.observationId });
    const completed = this.execution.saveRound({ ...round, status: "completed", blocker: null, updatedAt: now() }, "team.round-completed");
    if (state.mission.status !== "running") this.team.synchronizeTerminal(runId);
    return this.receipt(runId, "round_verified", `Advanced Team to world revision ${state.revision}`, completed);
  }
}
