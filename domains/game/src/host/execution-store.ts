import type { DatabaseSync } from "node:sqlite";

import { canonicalJson } from "../digest.ts";
import type { VerificationReceipt, WorldCommand, WorldFact } from "../model.ts";
import type { HostStore } from "./store.ts";

export type EffectStatus = "proposed" | "dispatched" | "succeeded" | "rejected";
export type DispatchStatus = "pending" | "unknown" | "succeeded" | "rejected";

export interface HostEffect {
  effectId: string;
  runId: string;
  taskId: string;
  attemptId: string;
  operationCandidateId: string;
  skillStepIndex: number;
  requiredWorldRevision: number;
  requiredWorldDigest: string;
  commandId: string;
  worldCommand: WorldCommand;
  status: EffectStatus;
  createdAt: string;
  updatedAt: string;
}

export interface HostDispatch {
  dispatchId: string;
  effectId: string;
  runId: string;
  attemptId: string;
  skillStepIndex: number;
  commandId: string;
  status: DispatchStatus;
  worldEventId: string | null;
  commandSequence: number | null;
  error: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface HostObservation {
  observationId: string;
  dispatchId: string;
  effectId: string;
  runId: string;
  commandId: string;
  commandSequence: number;
  worldEventId: string;
  worldAfterDigest: string;
  facts: WorldFact[];
  verification: VerificationReceipt | null;
  createdAt: string;
}

interface JsonRow { value_json: string }

function parse<T>(row: JsonRow | undefined, label: string): T {
  if (!row) throw new Error(`${label} is missing`);
  return JSON.parse(row.value_json) as T;
}

export class HostExecutionStore {
  readonly db: DatabaseSync;
  readonly host: HostStore;

  constructor(db: DatabaseSync, host: HostStore) {
    this.db = db;
    this.host = host;
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS host_effects (
        effect_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        attempt_id TEXT NOT NULL,
        skill_step_index INTEGER NOT NULL,
        command_id TEXT NOT NULL,
        status TEXT NOT NULL,
        value_json TEXT NOT NULL,
        UNIQUE (run_id, command_id),
        UNIQUE (attempt_id, skill_step_index),
        FOREIGN KEY (run_id) REFERENCES runs(run_id),
        FOREIGN KEY (attempt_id) REFERENCES host_attempts(attempt_id)
      );
      CREATE TABLE IF NOT EXISTS host_dispatches (
        dispatch_id TEXT PRIMARY KEY,
        effect_id TEXT NOT NULL UNIQUE,
        run_id TEXT NOT NULL,
        attempt_id TEXT NOT NULL,
        skill_step_index INTEGER NOT NULL,
        command_id TEXT NOT NULL,
        status TEXT NOT NULL,
        value_json TEXT NOT NULL,
        UNIQUE (run_id, command_id),
        FOREIGN KEY (effect_id) REFERENCES host_effects(effect_id),
        FOREIGN KEY (attempt_id) REFERENCES host_attempts(attempt_id)
      );
      CREATE TABLE IF NOT EXISTS host_observations (
        observation_id TEXT PRIMARY KEY,
        dispatch_id TEXT NOT NULL UNIQUE,
        effect_id TEXT NOT NULL UNIQUE,
        run_id TEXT NOT NULL,
        command_id TEXT NOT NULL,
        world_event_id TEXT NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (dispatch_id) REFERENCES host_dispatches(dispatch_id),
        FOREIGN KEY (effect_id) REFERENCES host_effects(effect_id)
      );
      CREATE INDEX IF NOT EXISTS host_dispatch_attempt_idx
        ON host_dispatches(attempt_id, skill_step_index);
    `);
  }

  putEffect(effect: HostEffect): HostEffect {
    const existing = this.findEffect(effect.effectId);
    if (existing) {
      if (canonicalJson(existing) !== canonicalJson(effect)) throw new Error("Effect identity is bound to different content");
      return existing;
    }
    return this.host.withTransaction(effect.runId, () => {
      this.db.prepare(`INSERT INTO host_effects
        (effect_id, run_id, attempt_id, skill_step_index, command_id, status, value_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)`)
        .run(effect.effectId, effect.runId, effect.attemptId, effect.skillStepIndex,
          effect.commandId, effect.status, canonicalJson(effect));
      this.host.appendEventInTransaction(effect.runId, "effect_proposed",
        `host-event:${effect.effectId}:proposed`, effect, effect.createdAt);
      return effect;
    });
  }

  findEffect(effectId: string): HostEffect | null {
    const row = this.db.prepare("SELECT value_json FROM host_effects WHERE effect_id = ?").get(effectId) as JsonRow | undefined;
    return row ? JSON.parse(row.value_json) as HostEffect : null;
  }

  getEffect(effectId: string): HostEffect {
    return parse<HostEffect>(
      this.db.prepare("SELECT value_json FROM host_effects WHERE effect_id = ?").get(effectId) as JsonRow | undefined,
      "Effect",
    );
  }

  saveEffect(effect: HostEffect, eventType: string): HostEffect {
    return this.host.withTransaction(effect.runId, () => {
      this.db.prepare("UPDATE host_effects SET status = ?, value_json = ? WHERE effect_id = ?")
        .run(effect.status, canonicalJson(effect), effect.effectId);
      this.host.appendEventInTransaction(effect.runId, eventType,
        `host-event:${effect.effectId}:${eventType}`, effect, effect.updatedAt);
      return effect;
    });
  }

  putDispatch(dispatch: HostDispatch): HostDispatch {
    const existing = this.findDispatch(dispatch.dispatchId);
    if (existing) {
      if (canonicalJson(existing) !== canonicalJson(dispatch)) throw new Error("Dispatch identity is bound to different content");
      return existing;
    }
    return this.host.withTransaction(dispatch.runId, () => {
      this.db.prepare(`INSERT INTO host_dispatches
        (dispatch_id, effect_id, run_id, attempt_id, skill_step_index, command_id, status, value_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
        .run(dispatch.dispatchId, dispatch.effectId, dispatch.runId, dispatch.attemptId,
          dispatch.skillStepIndex, dispatch.commandId, dispatch.status, canonicalJson(dispatch));
      this.host.appendEventInTransaction(dispatch.runId, "dispatch_prepared",
        `host-event:${dispatch.dispatchId}:prepared`, dispatch, dispatch.createdAt);
      return dispatch;
    });
  }

  findDispatch(dispatchId: string): HostDispatch | null {
    const row = this.db.prepare("SELECT value_json FROM host_dispatches WHERE dispatch_id = ?").get(dispatchId) as JsonRow | undefined;
    return row ? JSON.parse(row.value_json) as HostDispatch : null;
  }

  getDispatch(dispatchId: string): HostDispatch {
    return parse<HostDispatch>(
      this.db.prepare("SELECT value_json FROM host_dispatches WHERE dispatch_id = ?").get(dispatchId) as JsonRow | undefined,
      "Dispatch",
    );
  }

  findDispatchForStep(attemptId: string, skillStepIndex: number): HostDispatch | null {
    const row = this.db.prepare(`SELECT value_json FROM host_dispatches
      WHERE attempt_id = ? AND skill_step_index = ?`).get(attemptId, skillStepIndex) as JsonRow | undefined;
    return row ? JSON.parse(row.value_json) as HostDispatch : null;
  }

  saveDispatch(dispatch: HostDispatch, eventType: string): HostDispatch {
    return this.host.withTransaction(dispatch.runId, () => {
      this.db.prepare("UPDATE host_dispatches SET status = ?, value_json = ? WHERE dispatch_id = ?")
        .run(dispatch.status, canonicalJson(dispatch), dispatch.dispatchId);
      this.host.appendEventInTransaction(dispatch.runId, eventType,
        `host-event:${dispatch.dispatchId}:${eventType}`, dispatch, dispatch.updatedAt);
      return dispatch;
    });
  }

  putObservation(observation: HostObservation): HostObservation {
    const existing = this.findObservation(observation.dispatchId);
    if (existing) {
      if (canonicalJson(existing) !== canonicalJson(observation)) throw new Error("Observation identity is bound to different content");
      return existing;
    }
    return this.host.withTransaction(observation.runId, () => {
      this.db.prepare(`INSERT INTO host_observations
        (observation_id, dispatch_id, effect_id, run_id, command_id, world_event_id, value_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)`)
        .run(observation.observationId, observation.dispatchId, observation.effectId,
          observation.runId, observation.commandId, observation.worldEventId, canonicalJson(observation));
      this.host.appendEventInTransaction(observation.runId, "observation_recorded",
        `host-event:${observation.observationId}:recorded`, observation, observation.createdAt);
      return observation;
    });
  }

  findObservation(dispatchId: string): HostObservation | null {
    const row = this.db.prepare("SELECT value_json FROM host_observations WHERE dispatch_id = ?").get(dispatchId) as JsonRow | undefined;
    return row ? JSON.parse(row.value_json) as HostObservation : null;
  }

  listEffects(runId: string): HostEffect[] {
    const rows = this.db.prepare("SELECT value_json FROM host_effects WHERE run_id = ? ORDER BY rowid")
      .all(runId) as unknown as JsonRow[];
    return rows.map((row) => JSON.parse(row.value_json) as HostEffect);
  }

  listDispatches(runId: string): HostDispatch[] {
    const rows = this.db.prepare("SELECT value_json FROM host_dispatches WHERE run_id = ? ORDER BY rowid")
      .all(runId) as unknown as JsonRow[];
    return rows.map((row) => JSON.parse(row.value_json) as HostDispatch);
  }

  listObservations(runId: string): HostObservation[] {
    const rows = this.db.prepare("SELECT value_json FROM host_observations WHERE run_id = ? ORDER BY rowid")
      .all(runId) as unknown as JsonRow[];
    return rows.map((row) => JSON.parse(row.value_json) as HostObservation);
  }
}
