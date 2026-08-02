import type { DatabaseSync } from "node:sqlite";

import { canonicalJson, sha256 } from "../digest.ts";
import { HostStore } from "../host-contract/journal.ts";
import type { PrimitiveWorldCommand, WorldState } from "../model.ts";
import { ENGINEER_ID, MEDIC_ID, SECURITY_ID } from "../scenario.ts";
import type { GameStore } from "../storage.ts";
import { STATION_ZERO_SPECIALIST_LIMIT } from "./coordination-policy.ts";
import type {
  ActorProfile,
  AuthorityDecision,
  AuthorityPolicyMode,
  AuthorityGrant,
  MessageChannel,
  MessageKind,
  TeamGoal,
  TeamMessage,
  TeamProjection,
  TeamRunConfiguration,
  TeamTaskControl,
  TeamTaskLease,
  TeamTaskProjection,
  TeamTaskState,
  TeamWaitRecord,
} from "./model.ts";
import { TEAM_OBJECTIVE_GRAPH, nextObjectiveForRole, objectiveStatus } from "./objectives.ts";

interface JsonRow { value_json: string }

interface ProjectionHead {
  kind: string;
  id: string;
  revision: number | null;
  digest: string;
}

function projectionHead(kind: string, id: string, value: unknown, revision: number | null = null): ProjectionHead {
  return { kind, id, revision, digest: sha256(value) };
}

function headMatches(head: ProjectionHead | undefined, kind: string, id: string, value: unknown, revision: number | null = null): boolean {
  return Boolean(head && head.kind === kind && head.id === id && head.revision === revision && head.digest === sha256(value));
}

interface TaskRow extends JsonRow { task_id: string; head_event_id: string }
interface LeaseRow { task_id: string; owner_id: string; revision: number; expires_at_ms: number }

export class TeamStoreError extends Error {
  readonly code: "team_corrupt" | "team_conflict" | "team_lease_held";
  constructor(code: TeamStoreError["code"], message: string) {
    super(message);
    this.name = "TeamStoreError";
    this.code = code;
  }
}

function parse<T>(text: string, label: string): T {
  try { return JSON.parse(text) as T; }
  catch (error) { throw new TeamStoreError("team_corrupt", `${label} is invalid JSON: ${String(error)}`); }
}

function suffix(runId: string): string {
  return runId.startsWith("run:") ? runId.slice(4) : runId;
}

function goalId(runId: string): string {
  return `goal:${suffix(runId)}:team-rescue`;
}

export function actorTaskId(runId: string, actorId: string): string {
  return `task:${suffix(runId)}:actor:${actorId}`;
}

export function coordinatorTaskId(runId: string): string {
  return `task:${suffix(runId)}:team-coordinator`;
}

function profilesFor(state: WorldState): ActorProfile[] {
  const requireActor = (actorId: string): void => {
    if (!state.agents[actorId]) throw new TeamStoreError("team_corrupt", `team scenario lacks ${actorId}`);
  };
  requireActor(ENGINEER_ID);
  requireActor(MEDIC_ID);
  requireActor(SECURITY_ID);
  const profiles: ActorProfile[] = [
    { actorId: ENGINEER_ID, role: "engineer", providerOrder: ["fixture"], observationPolicyId: "station-zero-local-v1", authorityPolicyId: "station-zero-abac-v1", riskPreferenceId: "mission-balanced-v1" },
    { actorId: MEDIC_ID, role: "medic", providerOrder: ["fixture"], observationPolicyId: "station-zero-local-v1", authorityPolicyId: "station-zero-abac-v1", riskPreferenceId: "crew-first-v1" },
    { actorId: SECURITY_ID, role: "security", providerOrder: ["fixture"], observationPolicyId: "station-zero-local-v1", authorityPolicyId: "station-zero-abac-v1", riskPreferenceId: "containment-first-v1" },
  ];
  if (profiles.length !== STATION_ZERO_SPECIALIST_LIMIT) {
    throw new TeamStoreError("team_corrupt", "Station Zero specialist profile count drifted");
  }
  return profiles;
}

export function teamRunInitialized(
  game: GameStore,
  runId = game.activeRunId,
): boolean {
  const table = game.db.prepare(
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'team_actor_sessions'",
  ).get() as { name?: string } | undefined;
  if (table?.name !== "team_actor_sessions") return false;
  const row = game.db.prepare(
    "SELECT 1 AS present FROM team_actor_sessions WHERE run_id = ? LIMIT 1",
  ).get(runId) as { present?: number } | undefined;
  return row?.present === 1;
}

function activeControl(state: WorldState): TeamTaskControl {
  return { mode: "active", reason: null, issuedBy: "system:initialize", issuedAtTick: state.turn };
}

function terminalState(state: WorldState): TeamTaskState {
  if (state.mission.status === "victory") return "completed";
  if (state.mission.status === "failure") return "failed";
  return "ready";
}

export interface SendTeamMessageInput {
  senderActorId: string;
  recipientActorIds: string[];
  kind: MessageKind;
  referencedFactIds?: string[];
  referencedArtifactDigests?: string[];
  boundedSummary: string;
  channel: MessageChannel;
  ttlTicks?: number;
}

export interface IssueGrantInput {
  actorId: string;
  proposalId: string;
  actionCandidateId: string;
  contextDigest: string;
  worldDigest: string;
  policyRevision: number;
  operationKind: PrimitiveWorldCommand["kind"];
  targetId: string;
  expiresAtTick: number;
  issuedBy: string;
}

export class TeamStore {
  readonly game: GameStore;
  readonly db: DatabaseSync;
  readonly host: HostStore;

  constructor(game: GameStore) {
    this.game = game;
    this.db = game.db;
    this.host = new HostStore(this.db);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS team_run_configurations (
        run_id TEXT PRIMARY KEY,
        revision INTEGER NOT NULL,
        head_event_id TEXT NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS team_profiles (
        run_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        value_json TEXT NOT NULL,
        PRIMARY KEY (run_id, actor_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS team_actor_sessions (
        task_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        actor_id TEXT,
        role TEXT NOT NULL,
        state TEXT NOT NULL,
        revision INTEGER NOT NULL,
        head_event_id TEXT NOT NULL,
        value_json TEXT NOT NULL,
        UNIQUE (run_id, actor_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS team_actor_leases (
        task_id TEXT PRIMARY KEY,
        owner_id TEXT NOT NULL,
        revision INTEGER NOT NULL,
        expires_at_ms INTEGER NOT NULL,
        FOREIGN KEY (task_id) REFERENCES team_actor_sessions(task_id) ON DELETE CASCADE
      );
      CREATE TABLE IF NOT EXISTS team_messages (
        message_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        status TEXT NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS team_authority_decisions (
        decision_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        outcome TEXT NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS team_authority_grants (
        grant_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        proposal_id TEXT NOT NULL UNIQUE,
        consumed_at_tick INTEGER,
        value_json TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE INDEX IF NOT EXISTS team_actor_sessions_run_idx ON team_actor_sessions(run_id, role, task_id);
      CREATE INDEX IF NOT EXISTS team_messages_run_idx ON team_messages(run_id, status, message_id);
    `);
  }

  isInitialized(runId = this.game.activeRunId): boolean {
    return teamRunInitialized(this.game, runId);
  }

  initialize(runId = this.game.activeRunId): TeamProjection {
    if (this.isInitialized(runId)) return this.projection(runId);
    const metadata = this.game.getRun(runId);
    if (metadata.rulesetVersion < 3 || metadata.scenarioVersion < 2) {
      throw new TeamStoreError("team_conflict", "Team Host requires Scenario v2 and Ruleset v3");
    }
    const state = this.game.loadState(runId);
    const now = new Date().toISOString();
    const objectiveArtifact = this.host.putArtifact("team-objective-graph", TEAM_OBJECTIVE_GRAPH);
    const goal: TeamGoal = {
      goalId: goalId(runId), runId,
      statement: "Stabilize Station Zero through independent specialists and transmit a verified rescue signal.",
      objectiveGraphDigest: objectiveArtifact.digest,
      successPredicateId: "mission:victory",
      status: state.mission.status === "victory" ? "succeeded" : state.mission.status === "failure" ? "failed" : "active",
      revision: 1, createdAt: now, updatedAt: now,
    };
    const configuration: TeamRunConfiguration = {
      schemaVersion: 1, runId, authorityPolicyMode: "autonomous", revision: 1,
      createdAt: now, updatedAt: now,
    };
    const profiles = profilesFor(state);
    const tasks: TeamTaskProjection[] = profiles.map((profile) => ({
      taskId: actorTaskId(runId, profile.actorId), goalId: goal.goalId, runId,
      actorId: profile.actorId, role: profile.role, state: terminalState(state), control: activeControl(state), revision: 1,
      activeObjectiveId: nextObjectiveForRole(state, profile.role), preparedContextDigest: null,
      admittedProposalId: null, wait: null, lastWorldRevision: state.revision,
      providerOrder: [...profile.providerOrder], createdAt: now, updatedAt: now,
    }));
    tasks.push({
      taskId: coordinatorTaskId(runId), goalId: goal.goalId, runId, actorId: null,
      role: "coordinator", state: terminalState(state), control: activeControl(state), revision: 1,
      activeObjectiveId: nextObjectiveForRole(state, "coordinator"), preparedContextDigest: null,
      admittedProposalId: null, wait: null, lastWorldRevision: state.revision,
      providerOrder: [], createdAt: now, updatedAt: now,
    });

    this.host.withTransaction(runId, () => {
      const retained = this.db.prepare(
        "SELECT 1 AS present FROM team_actor_sessions WHERE run_id = ? LIMIT 1",
      ).get(runId) as { present?: number } | undefined;
      if (retained?.present === 1) return;
      const configurationEventId = `host-event:team-configuration:${runId}:revision:1`;
      this.db.prepare("INSERT INTO team_run_configurations (run_id, revision, head_event_id, value_json) VALUES (?, ?, ?, ?)")
        .run(runId, configuration.revision, configurationEventId, canonicalJson(configuration));
      this.host.appendEventInTransaction(runId, "team.configuration-created", configurationEventId, { configuration }, now);
      const goalEventId = `host-event:${goal.goalId}:team-created`;
      this.host.appendEventInTransaction(runId, "team.goal-created", goalEventId, { goal }, now);
      for (const profile of profiles) {
        this.db.prepare("INSERT INTO team_profiles (run_id, actor_id, value_json) VALUES (?, ?, ?)")
          .run(runId, profile.actorId, canonicalJson(profile));
      }
      for (const task of tasks) {
        const eventId = `host-event:${task.taskId}:created`;
        this.db.prepare(`INSERT INTO team_actor_sessions
          (task_id, run_id, actor_id, role, state, revision, head_event_id, value_json)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
          .run(task.taskId, runId, task.actorId, task.role, task.state, task.revision, eventId, canonicalJson(task));
        this.host.appendEventInTransaction(runId, "team.task-created", eventId, {
          head: projectionHead("team-task", task.taskId, task, task.revision),
        }, now);
      }
    });
    return this.projection(runId);
  }

  getGoal(runId = this.game.activeRunId): TeamGoal {
    const session = this.db.prepare("SELECT task_id FROM team_actor_sessions WHERE run_id = ? LIMIT 1").get(runId) as { task_id?: string } | undefined;
    if (!session?.task_id) throw new Error(`Team Goal is not initialized: ${runId}`);
    const metadata = this.game.getRun(runId);
    const state = this.game.loadState(runId);
    const objectiveDigest = sha256({ kind: "team-objective-graph", content: TEAM_OBJECTIVE_GRAPH });
    let objectiveArtifact;
    try {
      objectiveArtifact = this.host.getArtifact<typeof TEAM_OBJECTIVE_GRAPH>(objectiveDigest);
    } catch (error) {
      throw new TeamStoreError("team_corrupt", `Team Objective Graph Artifact is unavailable: ${String(error)}`);
    }
    if (
      objectiveArtifact.kind !== "team-objective-graph" ||
      canonicalJson(objectiveArtifact.content) !== canonicalJson(TEAM_OBJECTIVE_GRAPH)
    ) {
      throw new TeamStoreError("team_corrupt", "Team Objective Graph Artifact differs from the retained contract");
    }
    const tasks = this.listTasks(runId);
    const updatedAt = tasks.reduce((latest, task) => task.updatedAt > latest ? task.updatedAt : latest, metadata.createdAt);
    return {
      goalId: goalId(runId),
      runId,
      statement: "Stabilize Station Zero through independent specialists and transmit a verified rescue signal.",
      objectiveGraphDigest: objectiveArtifact.digest,
      successPredicateId: "mission:victory",
      status: state.mission.status === "victory" ? "succeeded" : state.mission.status === "failure" ? "failed" : "active",
      revision: Math.max(1, ...tasks.map((task) => task.revision)),
      createdAt: metadata.createdAt,
      updatedAt,
    };
  }

  listProfiles(runId = this.game.activeRunId): ActorProfile[] {
    const rows = this.db.prepare("SELECT value_json FROM team_profiles WHERE run_id = ? ORDER BY actor_id").all(runId) as unknown as JsonRow[];
    return rows.map((row) => parse<ActorProfile>(row.value_json, "Actor Profile"));
  }

  getProfile(actorId: string, runId = this.game.activeRunId): ActorProfile {
    const row = this.db.prepare("SELECT value_json FROM team_profiles WHERE run_id = ? AND actor_id = ?").get(runId, actorId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Team Profile: ${actorId}`);
    return parse<ActorProfile>(row.value_json, "Actor Profile");
  }

  getTask(taskId: string): TeamTaskProjection {
    const row = this.db.prepare("SELECT task_id, head_event_id, value_json FROM team_actor_sessions WHERE task_id = ?").get(taskId) as TaskRow | undefined;
    if (!row) throw new Error(`unknown Team Task: ${taskId}`);
    const task = parse<TeamTaskProjection>(row.value_json, "Team Task");
    const event = this.host.getJournalEvent(task.runId, row.head_event_id);
    const payload = event?.payload as { task?: TeamTaskProjection; head?: ProjectionHead } | undefined;
    const valid = payload?.task
      ? canonicalJson(payload.task) === canonicalJson(task)
      : headMatches(payload?.head, "team-task", task.taskId, task, task.revision);
    if (!valid) throw new TeamStoreError("team_corrupt", "Team Task projection differs from event head");
    return task;
  }

  listTasks(runId = this.game.activeRunId): TeamTaskProjection[] {
    const rows = this.db.prepare("SELECT task_id FROM team_actor_sessions WHERE run_id = ? ORDER BY role, task_id").all(runId) as unknown as Array<{ task_id: string }>;
    return rows.map((row) => this.getTask(row.task_id));
  }

  saveTask(next: TeamTaskProjection, eventType: string, eventData: Record<string, unknown> = {}): TeamTaskProjection {
    const current = this.getTask(next.taskId);
    if (next.runId !== current.runId || next.revision !== current.revision + 1) {
      throw new TeamStoreError("team_conflict", "Team Task identity or revision changed");
    }
    if (["completed", "failed", "cancelled"].includes(current.state) && next.state !== current.state) {
      throw new TeamStoreError("team_conflict", "terminal Team Task cannot transition to another state");
    }
    const eventId = `host-event:${next.taskId}:revision:${next.revision}`;
    this.host.withTransaction(next.runId, () => {
      const changed = this.db.prepare(`UPDATE team_actor_sessions SET state = ?, revision = ?, head_event_id = ?, value_json = ?
        WHERE task_id = ? AND revision = ?`)
        .run(next.state, next.revision, eventId, canonicalJson(next), next.taskId, current.revision);
      if (Number(changed.changes) !== 1) throw new TeamStoreError("team_conflict", "Team Task revision was superseded");
      this.host.appendEventInTransaction(next.runId, eventType, eventId, {
        head: projectionHead("team-task", next.taskId, next, next.revision),
        ...eventData,
      }, next.updatedAt);
    });
    return this.getTask(next.taskId);
  }

  transitionTask(
    taskId: string,
    values: Partial<Pick<TeamTaskProjection, "state" | "control" | "activeObjectiveId" | "preparedContextDigest" | "admittedProposalId" | "wait" | "lastWorldRevision" | "providerOrder">>,
    eventType: string,
    eventData: Record<string, unknown> = {},
  ): TeamTaskProjection {
    const current = this.getTask(taskId);
    const next: TeamTaskProjection = {
      ...current, ...values, revision: current.revision + 1, updatedAt: new Date().toISOString(),
    };
    return this.saveTask(next, eventType, eventData);
  }

  acquireLease(taskId: string, ownerId: string, nowMs = Date.now(), ttlMs = 30_000): TeamTaskLease {
    if (!ownerId.trim() || !Number.isSafeInteger(nowMs) || !Number.isSafeInteger(ttlMs) || ttlMs < 1) throw new TypeError("valid lease owner, time, and TTL are required");
    const task = this.getTask(taskId);
    return this.host.withTransaction(task.runId, () => {
      const row = this.db.prepare("SELECT * FROM team_actor_leases WHERE task_id = ?").get(taskId) as LeaseRow | undefined;
      if (row && row.expires_at_ms > nowMs && row.owner_id !== ownerId) {
        throw new TeamStoreError("team_lease_held", `Team Task lease is held by ${row.owner_id}`);
      }
      const revision = Number(row?.revision ?? 0) + 1;
      const lease = { taskId, ownerId, revision, expiresAtMs: nowMs + ttlMs };
      this.db.prepare(`INSERT INTO team_actor_leases (task_id, owner_id, revision, expires_at_ms) VALUES (?, ?, ?, ?)
        ON CONFLICT(task_id) DO UPDATE SET owner_id = excluded.owner_id, revision = excluded.revision, expires_at_ms = excluded.expires_at_ms`)
        .run(taskId, ownerId, revision, lease.expiresAtMs);
      return lease;
    });
  }

  releaseLease(lease: TeamTaskLease): void {
    const task = this.getTask(lease.taskId);
    this.host.withTransaction(task.runId, () => {
      const result = this.db.prepare("DELETE FROM team_actor_leases WHERE task_id = ? AND owner_id = ? AND revision = ?")
        .run(lease.taskId, lease.ownerId, lease.revision);
      if (Number(result.changes) !== 1) throw new TeamStoreError("team_conflict", "Team Task lease identity no longer matches");
    });
  }

  private reachable(state: WorldState, senderActorId: string, recipientActorId: string, channel: MessageChannel): boolean {
    if (channel === "local") return state.agents[senderActorId]?.location === state.agents[recipientActorId]?.location;
    const communications = state.systems.communications;
    return Boolean(communications?.powered && (communications.integrity ?? 0) >= 0.8);
  }

  sendMessage(input: SendTeamMessageInput, runId = this.game.activeRunId): TeamMessage {
    const state = this.game.loadState(runId);
    const recipients = [...new Set(input.recipientActorIds)].sort();
    if (!state.agents[input.senderActorId] || recipients.length === 0 || recipients.some((actorId) => !state.agents[actorId])) throw new TypeError("message actors must exist");
    if (!input.boundedSummary.trim() || Buffer.byteLength(input.boundedSummary) > 512) throw new TypeError("message summary must be non-empty and at most 512 bytes");
    const ttlTicks = input.ttlTicks ?? 6;
    if (!Number.isSafeInteger(ttlTicks) || ttlTicks < 1 || ttlTicks > 64) throw new TypeError("message TTL must be from 1 to 64 ticks");
    const deliveredActorIds = recipients.filter((recipient) => this.reachable(state, input.senderActorId, recipient, input.channel));
    const pendingActorIds = recipients.filter((recipient) => !deliveredActorIds.includes(recipient));
    const identity = {
      runId, senderActorId: input.senderActorId, recipients, kind: input.kind,
      referencedFactIds: [...new Set(input.referencedFactIds ?? [])].sort(),
      referencedArtifactDigests: [...new Set(input.referencedArtifactDigests ?? [])].sort(),
      summary: input.boundedSummary, channel: input.channel, createdTick: state.turn, ttlTicks,
    };
    const now = new Date().toISOString();
    const message: TeamMessage = {
      messageId: `team-message:${sha256(identity)}`, runId, senderActorId: input.senderActorId,
      recipientActorIds: recipients, kind: input.kind,
      referencedFactIds: [...new Set(input.referencedFactIds ?? [])].sort(),
      referencedArtifactDigests: [...new Set(input.referencedArtifactDigests ?? [])].sort(),
      boundedSummary: input.boundedSummary, channel: input.channel,
      createdTick: state.turn, expiryTick: state.turn + ttlTicks,
      deliveredActorIds, pendingActorIds,
      status: pendingActorIds.length === 0 ? "delivered" : "pending",
      createdAt: now, updatedAt: now,
    };
    const existing = this.db.prepare("SELECT value_json FROM team_messages WHERE message_id = ?").get(message.messageId) as JsonRow | undefined;
    if (existing) {
      const retained = parse<TeamMessage>(existing.value_json, "Team Message");
      return retained;
    }
    this.host.withTransaction(runId, () => {
      const inserted = this.db.prepare("INSERT OR IGNORE INTO team_messages (message_id, run_id, status, value_json) VALUES (?, ?, ?, ?)")
        .run(message.messageId, runId, message.status, canonicalJson(message));
      if (Number(inserted.changes) === 1) {
        this.host.appendEventInTransaction(runId, "team.message-created", `host-event:${message.messageId}:created`, { message }, now);
      }
    });
    const retained = this.db.prepare("SELECT value_json FROM team_messages WHERE message_id = ?").get(message.messageId) as JsonRow | undefined;
    if (!retained) throw new TeamStoreError("team_corrupt", "Team Message disappeared after insert");
    return parse<TeamMessage>(retained.value_json, "Team Message");
  }

  listMessages(runId = this.game.activeRunId): TeamMessage[] {
    const rows = this.db.prepare("SELECT value_json FROM team_messages WHERE run_id = ? ORDER BY rowid").all(runId) as unknown as JsonRow[];
    return rows.map((row) => parse<TeamMessage>(row.value_json, "Team Message"));
  }

  refreshMessages(runId = this.game.activeRunId): TeamMessage[] {
    const state = this.game.loadState(runId);
    for (const message of this.listMessages(runId)) {
      if (message.status !== "pending") continue;
      const now = new Date().toISOString();
      const expired = state.turn >= message.expiryTick;
      const newlyDelivered = expired ? [] : message.pendingActorIds.filter((recipient) => this.reachable(state, message.senderActorId, recipient, message.channel));
      if (!expired && newlyDelivered.length === 0) continue;
      const deliveredActorIds = [...new Set([...message.deliveredActorIds, ...newlyDelivered])].sort();
      const pendingActorIds = message.pendingActorIds.filter((recipient) => !newlyDelivered.includes(recipient));
      const next: TeamMessage = {
        ...message, deliveredActorIds, pendingActorIds,
        status: expired ? "expired" : pendingActorIds.length === 0 ? "delivered" : "pending",
        updatedAt: now,
      };
      const expectedJson = canonicalJson(message);
      this.host.withTransaction(runId, () => {
        const changed = this.db.prepare(
          "UPDATE team_messages SET status = ?, value_json = ? WHERE message_id = ? AND value_json = ?",
        ).run(next.status, canonicalJson(next), next.messageId, expectedJson);
        if (Number(changed.changes) !== 1) {
          throw new TeamStoreError("team_conflict", "Team Message was superseded");
        }
        this.host.appendEventInTransaction(runId, `team.message-${next.status}`, `host-event:${next.messageId}:${next.status}:${state.turn}`, { message: next }, now);
      });
    }
    return this.listMessages(runId);
  }

  putAuthorityDecision(decision: AuthorityDecision): AuthorityDecision {
    const existing = this.db.prepare("SELECT value_json FROM team_authority_decisions WHERE decision_id = ?").get(decision.decisionId) as JsonRow | undefined;
    if (existing) {
      const retained = parse<AuthorityDecision>(existing.value_json, "Authority Decision");
      if (canonicalJson(retained) !== canonicalJson(decision)) throw new TeamStoreError("team_conflict", "Authority Decision identity differs");
      return retained;
    }
    const decisionJson = canonicalJson(decision);
    this.host.withTransaction(decision.runId, () => {
      const inserted = this.db.prepare("INSERT OR IGNORE INTO team_authority_decisions (decision_id, run_id, actor_id, outcome, value_json) VALUES (?, ?, ?, ?, ?)")
        .run(decision.decisionId, decision.runId, decision.actorId, decision.outcome, decisionJson);
      if (Number(inserted.changes) === 1) {
        this.host.appendEventInTransaction(decision.runId, "team.authority-decided", `host-event:${decision.decisionId}:recorded`, { decision }, decision.createdAt);
        return;
      }
      const retained = this.db.prepare("SELECT value_json FROM team_authority_decisions WHERE decision_id = ?").get(decision.decisionId) as JsonRow | undefined;
      if (!retained || retained.value_json !== decisionJson) {
        throw new TeamStoreError("team_conflict", "Authority Decision identity differs");
      }
    });
    const retained = this.db.prepare("SELECT value_json FROM team_authority_decisions WHERE decision_id = ?").get(decision.decisionId) as JsonRow | undefined;
    if (!retained) throw new TeamStoreError("team_corrupt", "Authority Decision disappeared after insert");
    return parse<AuthorityDecision>(retained.value_json, "Authority Decision");
  }

  listAuthorityDecisions(runId = this.game.activeRunId): AuthorityDecision[] {
    const rows = this.db.prepare("SELECT value_json FROM team_authority_decisions WHERE run_id = ? ORDER BY rowid").all(runId) as unknown as JsonRow[];
    return rows.map((row) => parse<AuthorityDecision>(row.value_json, "Authority Decision"));
  }

  issueGrant(input: IssueGrantInput, runId = this.game.activeRunId): AuthorityGrant {
    const now = new Date().toISOString();
    const identity = { runId, ...input };
    const grant: AuthorityGrant = {
      grantId: `authority-grant:${sha256(identity)}`, runId, ...input,
      consumedAtTick: null, createdAt: now,
    };
    const existing = this.db.prepare("SELECT value_json FROM team_authority_grants WHERE grant_id = ?").get(grant.grantId) as JsonRow | undefined;
    if (existing) return parse<AuthorityGrant>(existing.value_json, "Authority Grant");
    this.host.withTransaction(runId, () => {
      const inserted = this.db.prepare(`INSERT OR IGNORE INTO team_authority_grants
        (grant_id, run_id, actor_id, proposal_id, consumed_at_tick, value_json) VALUES (?, ?, ?, ?, NULL, ?)`)
        .run(grant.grantId, runId, grant.actorId, grant.proposalId, canonicalJson(grant));
      if (Number(inserted.changes) === 1) {
        this.host.appendEventInTransaction(runId, "team.authority-granted", `host-event:${grant.grantId}:issued`, { grant }, now);
      }
    });
    const retained = this.db.prepare("SELECT value_json FROM team_authority_grants WHERE grant_id = ?").get(grant.grantId) as JsonRow | undefined;
    if (!retained) throw new TeamStoreError("team_corrupt", "Authority Grant disappeared after insert");
    return parse<AuthorityGrant>(retained.value_json, "Authority Grant");
  }

  consumeGrant(grantId: string, proposalId: string, contextDigest: string, worldDigest: string, tick: number): AuthorityGrant {
    const row = this.db.prepare("SELECT value_json FROM team_authority_grants WHERE grant_id = ?").get(grantId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Authority Grant: ${grantId}`);
    const current = parse<AuthorityGrant>(row.value_json, "Authority Grant");
    if (current.proposalId !== proposalId || current.contextDigest !== contextDigest || current.worldDigest !== worldDigest) throw new TeamStoreError("team_conflict", "Authority Grant binding differs");
    if (current.consumedAtTick !== null || tick > current.expiresAtTick) throw new TeamStoreError("team_conflict", "Authority Grant is consumed or expired");
    const next = { ...current, consumedAtTick: tick };
    this.host.withTransaction(current.runId, () => {
      const updated = this.db.prepare("UPDATE team_authority_grants SET consumed_at_tick = ?, value_json = ? WHERE grant_id = ? AND consumed_at_tick IS NULL")
        .run(tick, canonicalJson(next), grantId);
      if (Number(updated.changes) !== 1) throw new TeamStoreError("team_conflict", "Authority Grant was consumed concurrently");
      this.host.appendEventInTransaction(current.runId, "team.authority-consumed", `host-event:${grantId}:consumed`, { grant: next }, new Date().toISOString());
    });
    return next;
  }

  listAuthorityGrants(runId = this.game.activeRunId): AuthorityGrant[] {
    const rows = this.db.prepare("SELECT value_json FROM team_authority_grants WHERE run_id = ? ORDER BY rowid").all(runId) as unknown as JsonRow[];
    return rows.map((row) => parse<AuthorityGrant>(row.value_json, "Authority Grant"));
  }

  getConfiguration(runId = this.game.activeRunId): TeamRunConfiguration {
    const row = this.db.prepare("SELECT head_event_id, value_json FROM team_run_configurations WHERE run_id = ?").get(runId) as { head_event_id: string; value_json: string } | undefined;
    if (!row) {
      const profile = this.db.prepare("SELECT actor_id FROM team_profiles WHERE run_id = ? LIMIT 1").get(runId) as { actor_id?: string } | undefined;
      if (!profile?.actor_id) throw new Error(`Team is not initialized: ${runId}`);
      const createdAt = this.game.getRun(runId).createdAt;
      return { schemaVersion: 1, runId, authorityPolicyMode: "autonomous", revision: 0, createdAt, updatedAt: createdAt };
    }
    const configuration = parse<TeamRunConfiguration>(row.value_json, "Team Run Configuration");
    const event = this.host.getJournalEvent(runId, row.head_event_id);
    const payload = event?.payload as { configuration?: TeamRunConfiguration } | undefined;
    if (!payload?.configuration || canonicalJson(payload.configuration) !== canonicalJson(configuration)) throw new TeamStoreError("team_corrupt", "Team Run Configuration differs from event head");
    return configuration;
  }

  saveConfiguration(authorityPolicyMode: AuthorityPolicyMode, runId = this.game.activeRunId): TeamRunConfiguration {
    const current = this.getConfiguration(runId);
    if (current.authorityPolicyMode === authorityPolicyMode && current.revision > 0) return current;
    const updatedAt = new Date().toISOString();
    const next: TeamRunConfiguration = {
      schemaVersion: 1, runId, authorityPolicyMode, revision: current.revision + 1,
      createdAt: current.createdAt, updatedAt,
    };
    const eventId = `host-event:team-configuration:${runId}:revision:${next.revision}`;
    this.host.withTransaction(runId, () => {
      if (current.revision === 0) {
        this.db.prepare("INSERT INTO team_run_configurations (run_id, revision, head_event_id, value_json) VALUES (?, ?, ?, ?)")
          .run(runId, next.revision, eventId, canonicalJson(next));
      } else {
        const result = this.db.prepare("UPDATE team_run_configurations SET revision = ?, head_event_id = ?, value_json = ? WHERE run_id = ? AND revision = ?")
          .run(next.revision, eventId, canonicalJson(next), runId, current.revision);
        if (Number(result.changes) !== 1) throw new TeamStoreError("team_conflict", "Team Run Configuration revision was superseded");
      }
      this.host.appendEventInTransaction(runId, "team.configuration-updated", eventId, { configuration: next }, updatedAt);
    });
    return this.getConfiguration(runId);
  }

  projection(runId = this.game.activeRunId, refreshMessages = false): TeamProjection {
    const state = this.game.loadState(runId);
    return {
      goal: this.getGoal(runId),
      configuration: this.getConfiguration(runId),
      profiles: this.listProfiles(runId),
      tasks: this.listTasks(runId),
      objectives: TEAM_OBJECTIVE_GRAPH,
      objectiveStatus: objectiveStatus(state),
      messages: refreshMessages ? this.refreshMessages(runId) : this.listMessages(runId),
      authorityDecisions: this.listAuthorityDecisions(runId),
      authorityGrants: this.listAuthorityGrants(runId),
    };
  }

  synchronizeTerminal(runId = this.game.activeRunId): TeamProjection {
    const state = this.game.loadState(runId);
    if (state.mission.status === "running") return this.projection(runId);
    const targetState: TeamTaskState = state.mission.status === "victory" ? "completed" : "failed";
    for (const task of this.listTasks(runId)) {
      if (task.state === targetState) continue;
      this.transitionTask(task.taskId, { state: targetState, wait: null, lastWorldRevision: state.revision }, "team.task-terminal", { mission: state.mission });
    }
    return this.projection(runId);
  }

  setWait(taskId: string, wait: TeamWaitRecord | null): TeamTaskProjection {
    return this.transitionTask(taskId, { state: wait ? "waiting" : "ready", wait }, wait ? "team.task-waiting" : "team.task-ready");
  }

  verify(runId = this.game.activeRunId): void {
    this.host.verifyJournal(runId);
    for (const task of this.listTasks(runId)) this.getTask(task.taskId);
    this.getGoal(runId);
  }
}
