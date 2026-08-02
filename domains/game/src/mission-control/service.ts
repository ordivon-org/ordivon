import type { GameStore } from "../storage.ts";
import type { DeploymentProviderOptions } from "../deployment/model.ts";
import { resolveCoordinationProfile } from "../deployment/profiles.ts";
import { DeploymentStore } from "../deployment/store.ts";
import { TeamExecutionStore } from "../team/execution-store.ts";
import { authorityTargetId } from "../team/authority.ts";
import { TeamHost } from "../team/engine.ts";
import type { AuthorityPolicyMode, MessageChannel, MessageKind } from "../team/model.ts";
import { objectivesForRole, TEAM_OBJECTIVE_GRAPH } from "../team/objectives.ts";
import type { TeamDecisionProvider } from "../team/providers.ts";
import { TeamStore, TeamStoreError, teamRunInitialized } from "../team/store.ts";
import { isMissionProviderName, type MissionProviderName } from "./catalog.ts";
import { policyForDoctrine } from "./experience.ts";
import type { DoctrineId, MissionAdvanceMode, MissionControlAdvanceResult, MissionControlView, MissionTimelineItem } from "./model.ts";
import { createMissionControlView, missionTimelineItems } from "./projection.ts";

export type { MissionProviderName } from "./catalog.ts";
export type MissionProviderFactory = (name: MissionProviderName, options?: DeploymentProviderOptions) => TeamDecisionProvider;

export interface MissionControlInitializeInput {
  runId: string;
  scenarioCaseId?: string;
  authorityPolicyMode?: AuthorityPolicyMode;
  doctrineId?: DoctrineId;
  providers?: Record<string, MissionProviderName>;
  coordinationProfileId?: string;
}

export type MissionControlCommand =
  | { action: "approve"; proposalId: string; issuedBy?: string; expiresAtTick?: number }
  | { action: "deny"; proposalId: string }
  | { action: "redirect-objective"; actorId: string; objectiveId: string }
  | { action: "pause" | "resume" | "cancel"; actorId: string }
  | { action: "set-provider"; actorId: string; provider: MissionProviderName }
  | { action: "set-authority-policy"; policyMode: AuthorityPolicyMode }
  | { action: "send-message"; senderActorId: string; recipientActorIds: string[]; kind: MessageKind; boundedSummary: string; channel: MessageChannel; ttlTicks?: number };

function providerName(value: string | undefined): MissionProviderName {
  return isMissionProviderName(value) ? value : "fixture";
}

function providerForOrder(order: string[], factory: MissionProviderFactory, options: DeploymentProviderOptions): TeamDecisionProvider {
  if (order.length >= 2) {
    const pair = `${order[0]}-${order[1]}`;
    if (pair === "codex-hermes" || pair === "hermes-codex") return factory(pair, options);
  }
  return factory(providerName(order[0]), options);
}

export class MissionControlService {
  readonly store: GameStore;
  readonly providerFactory: MissionProviderFactory;

  constructor(store: GameStore, providerFactory: MissionProviderFactory) {
    this.store = store;
    this.providerFactory = providerFactory;
  }

  private teamStore(): TeamStore {
    return new TeamStore(this.store);
  }

  private host(runId: string): TeamHost {
    const team = this.teamStore();
    team.initialize(runId);
    const configuration = team.getConfiguration(runId);
    const deployment = new DeploymentStore(this.store).get(runId);
    const providerOptions = { coordinationProfileId: deployment?.coordinationProfileId ?? "specialist-containment" } as const;
    const providers: Record<string, TeamDecisionProvider> = {};
    for (const task of team.listTasks(runId).filter((candidate) => candidate.actorId)) {
      providers[task.actorId!] = providerForOrder(task.providerOrder, this.providerFactory, providerOptions);
    }
    return new TeamHost(this.store, providers, { policyMode: configuration.authorityPolicyMode });
  }

  state(runId: string): MissionControlView {
    return createMissionControlView(this.store, runId);
  }

  initialize(input: MissionControlInitializeInput): MissionControlView {
    if (!input.runId?.trim()) throw new TypeError("runId must be non-empty");
    if (!this.store.listRuns().some((run) => run.runId === input.runId)) {
      this.store.createRun({ runId: input.runId, scenarioVersion: 2, scenarioCaseId: input.scenarioCaseId ?? "baseline", rulesetVersion: 3 });
    }
    const metadata = this.store.getRun(input.runId);
    if (input.scenarioCaseId && metadata.scenarioCaseId !== input.scenarioCaseId) {
      throw new TeamStoreError("team_conflict", "Scenario Case differs from the retained Run");
    }
    if (metadata.scenarioVersion < 2 || metadata.rulesetVersion < 3) throw new TeamStoreError("team_conflict", "Mission Control requires Scenario v2 and Ruleset v3");
    const team = this.teamStore();
    team.initialize(input.runId);
    const deployments = new DeploymentStore(this.store);
    const retained = deployments.get(input.runId);
    const tasks = team.listTasks(input.runId).filter((candidate) => candidate.actorId);
    const authorityPolicyMode = input.authorityPolicyMode ?? (input.doctrineId ? policyForDoctrine(input.doctrineId) : retained?.authorityPolicyMode ?? "autonomous");
    const coordinationProfileId = resolveCoordinationProfile(
      input.coordinationProfileId ?? retained?.coordinationProfileId,
    );
    const actors = tasks.map((task) => {
      const retainedActor = retained?.actors.find((actor) => actor.actorId === task.actorId);
      const selected = input.providers?.[task.actorId!] ?? retainedActor?.providerOrder[0] ?? providerName(task.providerOrder[0]);
      return { actorId: task.actorId!, providerOrder: [selected] };
    });
    const manifest = deployments.bind({
      runId: input.runId,
      coordinationProfileId,
      authorityPolicyMode,
      actors,
    });
    team.saveConfiguration(manifest.authorityPolicyMode, input.runId);
    for (const task of tasks) {
      const desired = manifest.actors.find((actor) => actor.actorId === task.actorId)!.providerOrder;
      if (JSON.stringify(task.providerOrder) !== JSON.stringify(desired)) {
        team.transitionTask(task.taskId, { providerOrder: [...desired] }, "team.task-provider-updated", { actorId: task.actorId, providerOrder: desired });
      }
    }
    return this.state(input.runId);
  }

  async advance(runId: string, until: "proposal-review" | "tick-verified", maximumInternalSteps = 16): Promise<MissionControlAdvanceResult> {
    if (!Number.isSafeInteger(maximumInternalSteps) || maximumInternalSteps < 1 || maximumInternalSteps > 64) throw new TypeError("maximumInternalSteps must be an integer from 1 to 64");
    const initial = this.state(runId);
    if (!initial.initialized) throw new TeamStoreError("team_conflict", "Mission Control is not initialized");
    if (initial.run.status !== "running") return { boundary: "terminal", steps: [], committedRevisions: [], stopReason: "terminal", view: initial };
    if (until === "proposal-review" && initial.currentRound?.phase === "proposal-review") {
      return { boundary: "proposal-review", steps: [], committedRevisions: [], stopReason: "proposal-review", view: initial };
    }
    const startRevision = initial.generatedFrom.worldRevision;
    const host = this.host(runId);
    const steps: string[] = [];
    for (let index = 0; index < maximumInternalSteps; index += 1) {
      const receipt = await host.step(runId);
      steps.push(receipt.status);
      const view = this.state(runId);
      const committedRevisions = view.generatedFrom.worldRevision > startRevision ? [view.generatedFrom.worldRevision] : [];
      if (view.run.status !== "running") return { boundary: "terminal", steps, committedRevisions, stopReason: view.mission.reason ?? "terminal", view };
      if (receipt.status === "authority_required" || view.currentRound?.phase === "authority") return { boundary: "authority", steps, committedRevisions, stopReason: "authority-required", view };
      if (receipt.status === "blocked" || view.currentRound?.phase === "blocked") return { boundary: "blocked", steps, committedRevisions, stopReason: view.currentRound?.blocker ?? "blocked", view };
      if (until === "proposal-review" && view.currentRound?.phase === "proposal-review") return { boundary: "proposal-review", steps, committedRevisions, stopReason: "proposal-review", view };
      if (until === "tick-verified" && view.generatedFrom.worldRevision > startRevision && view.currentRound?.phase === "verified") {
        return { boundary: "tick-verified", steps, committedRevisions, stopReason: "one-tick", view };
      }
    }
    return { boundary: "step-limit", steps, committedRevisions: [], stopReason: "internal-step-limit", view: this.state(runId) };
  }

  async advancePlay(
    runId: string,
    mode: MissionAdvanceMode,
    maximumWorldTicks = mode === "three-ticks" ? 3 : mode === "one-tick" ? 1 : 12,
    maximumInternalSteps = 256,
  ): Promise<MissionControlAdvanceResult> {
    if (!Number.isSafeInteger(maximumWorldTicks) || maximumWorldTicks < 1 || maximumWorldTicks > 24) throw new TypeError("maximumWorldTicks must be an integer from 1 to 24");
    if (!Number.isSafeInteger(maximumInternalSteps) || maximumInternalSteps < 1 || maximumInternalSteps > 512) throw new TypeError("maximumInternalSteps must be an integer from 1 to 512");
    const initial = this.state(runId);
    if (!initial.initialized) throw new TeamStoreError("team_conflict", "Mission Control is not initialized");
    if (initial.run.status !== "running") return { boundary: "terminal", steps: [], committedRevisions: [], stopReason: "terminal", view: initial };

    const isActionable = (view: MissionControlView): boolean => view.inbox.some((card) =>
      card.commands.length > 0 || card.kind === "provider-failure");
    if (mode === "until-intervention" && isActionable(initial)) {
      return { boundary: "intervention", steps: [], committedRevisions: [], stopReason: "pending-intervention", view: initial };
    }

    const host = this.host(runId);
    const steps: string[] = [];
    const committedRevisions: number[] = [];
    let previousRevision = initial.generatedFrom.worldRevision;
    for (let index = 0; index < maximumInternalSteps; index += 1) {
      const receipt = await host.step(runId);
      steps.push(receipt.status);
      const view = this.state(runId);
      if (view.generatedFrom.worldRevision > previousRevision) {
        committedRevisions.push(view.generatedFrom.worldRevision);
        previousRevision = view.generatedFrom.worldRevision;
      }
      if (view.run.status !== "running") {
        return { boundary: "terminal", steps, committedRevisions, stopReason: view.mission.reason ?? "terminal", view };
      }
      if (isActionable(view)) {
        return { boundary: "intervention", steps, committedRevisions, stopReason: view.inbox.find((card) => card.commands.length > 0 || card.kind === "provider-failure")?.kind ?? "intervention", view };
      }
      if (receipt.status === "blocked" && view.currentRound?.phase === "blocked") {
        return { boundary: "blocked", steps, committedRevisions, stopReason: view.currentRound.blocker ?? "blocked", view };
      }
      if (committedRevisions.length >= maximumWorldTicks) {
        return {
          boundary: mode === "one-tick" ? "tick-verified" : "maximum-ticks",
          steps,
          committedRevisions,
          stopReason: mode,
          view,
        };
      }
    }
    return { boundary: "step-limit", steps, committedRevisions, stopReason: "internal-step-limit", view: this.state(runId) };
  }


  timeline(
    runId: string,
    beforeRevision: number | null = null,
    limit = 12,
  ): { runId: string; items: MissionTimelineItem[]; nextBeforeRevision: number | null } {
    if (!teamRunInitialized(this.store, runId)) {
      return { runId, items: [], nextBeforeRevision: null };
    }
    const team = this.teamStore();
    const execution = new TeamExecutionStore(team);
    const page = execution.listRoundsPage(runId, beforeRevision, limit);
    return {
      runId,
      items: missionTimelineItems(execution, page.rounds),
      nextBeforeRevision: page.nextBeforeRevision,
    };
  }

  command(runId: string, command: MissionControlCommand): unknown {
    const host = this.host(runId);
    const team = host.team;
    const state = this.store.loadState(runId);
    switch (command.action) {
      case "approve": {
        const proposal = host.execution.getProposal(command.proposalId);
        if (proposal.runId !== runId || proposal.status !== "proposed" || proposal.authorityOutcome !== "require-human") throw new TeamStoreError("team_conflict", "Proposal is not awaiting human authority");
        const expiresAtTick = command.expiresAtTick ?? state.turn + 2;
        if (!Number.isSafeInteger(expiresAtTick) || expiresAtTick < state.turn) throw new TypeError("expiresAtTick must be a current or future integer Tick");
        return team.issueGrant({
          actorId: proposal.actorId,
          proposalId: proposal.proposalId,
          actionCandidateId: proposal.actionCandidateId,
          contextDigest: proposal.contextId,
          worldDigest: proposal.worldDigest,
          policyRevision: team.getConfiguration(runId).revision,
          operationKind: proposal.command.kind,
          targetId: authorityTargetId(proposal.command),
          expiresAtTick,
          issuedBy: command.issuedBy?.trim() || "player:mission-control",
        }, runId);
      }
      case "deny": {
        const proposal = host.execution.getProposal(command.proposalId);
        if (proposal.runId !== runId || proposal.status !== "proposed") throw new TeamStoreError("team_conflict", "Proposal is not pending player review");
        const updated = host.execution.saveProposal(proposal, { ...proposal, status: "rejected", rejectionReason: "player_denied", updatedAt: new Date().toISOString() }, "team.proposal-player-denied");
        const task = team.getTask(proposal.actorTaskId);
        team.transitionTask(task.taskId, {
          state: task.control.mode === "paused" ? "waiting" : task.control.mode === "cancelled" ? "cancelled" : "blocked",
          admittedProposalId: proposal.proposalId,
          wait: task.control.mode === "active" ? { kind: "authority", subjectId: proposal.proposalId, reason: "Player denied Proposal", sinceTick: state.turn } : task.wait,
        }, "team.task-player-denied", { proposalId: proposal.proposalId });
        return updated;
      }
      case "redirect-objective": {
        if (!TEAM_OBJECTIVE_GRAPH.nodes.some((node) => node.objectiveId === command.objectiveId)) throw new TypeError("unknown Objective");
        const profile = team.getProfile(command.actorId, runId);
        if (!objectivesForRole(profile.role).includes(command.objectiveId)) throw new TeamStoreError("team_conflict", "Objective is outside the Actor role mandate");
        const task = team.listTasks(runId).find((candidate) => candidate.actorId === command.actorId);
        if (!task) throw new TypeError("no matching Actor Task");
        return team.transitionTask(task.taskId, {
          state: task.control.mode === "active" ? "ready" : task.state,
          activeObjectiveId: command.objectiveId,
          preparedContextDigest: null,
          admittedProposalId: null,
          wait: task.control.mode === "active" ? null : task.wait,
          lastWorldRevision: state.revision,
        }, "team.task-player-redirected", { actorId: command.actorId, objectiveId: command.objectiveId });
      }
      case "pause":
      case "resume":
      case "cancel": {
        const task = team.listTasks(runId).find((candidate) => candidate.actorId === command.actorId);
        if (!task) throw new TypeError("no matching Actor Task");
        if (task.control.mode === "cancelled" && command.action !== "cancel") throw new TeamStoreError("team_conflict", "Cancelled Actor Task cannot resume");
        const mode = command.action === "pause" ? "paused" : command.action === "cancel" ? "cancelled" : "active";
        return team.transitionTask(task.taskId, {
          state: mode === "cancelled" ? "cancelled" : mode === "paused" ? "waiting" : "ready",
          control: { mode, reason: mode === "active" ? null : `Player ${command.action}d Actor`, issuedBy: "player:mission-control", issuedAtTick: state.turn },
          preparedContextDigest: null,
          admittedProposalId: null,
          wait: mode === "paused" ? { kind: "replan", subjectId: "player:mission-control", reason: "Player paused Actor", sinceTick: state.turn } : null,
        }, `team.task-player-${command.action}d`, { actorId: command.actorId });
      }
      case "set-provider": {
        if (!isMissionProviderName(command.provider)) throw new TypeError("unsupported Team Provider");
        const task = team.listTasks(runId).find((candidate) => candidate.actorId === command.actorId);
        if (!task) throw new TypeError("no matching Actor Task");
        return team.transitionTask(task.taskId, { providerOrder: [command.provider], preparedContextDigest: null }, "team.task-provider-updated", { actorId: command.actorId, provider: command.provider });
      }
      case "set-authority-policy": return team.saveConfiguration(command.policyMode, runId);
      case "send-message": return team.sendMessage({
        senderActorId: command.senderActorId,
        recipientActorIds: command.recipientActorIds,
        kind: command.kind,
        boundedSummary: command.boundedSummary,
        channel: command.channel,
        ...(command.ttlTicks === undefined ? {} : { ttlTicks: command.ttlTicks }),
      }, runId);
    }
  }
}
