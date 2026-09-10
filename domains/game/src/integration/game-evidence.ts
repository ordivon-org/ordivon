import type { DatabaseSync } from "node:sqlite";

import {
  LocalEvidenceJournal,
  type LocalEvidenceArtifact,
  type LocalEvidenceEvent,
} from "./local-evidence-journal.ts";

/**
 * Narrow Game-consumer durability port.
 *
 * This interface does not assign semantic authority to persistence. It exists so
 * Game/domain code consumes a bounded local evidence port instead of treating persistence as domain authority.
 * The current adapter remains local only because Station Zero requires one
 * SQLite transaction to atomically bind Game projections and retained journal
 * evidence. A source-current external Host replacement must preserve that
 * invariant before this compatibility adapter can be deleted.
 */
export interface GameEvidencePort {
  putArtifact<T>(kind: string, content: T): LocalEvidenceArtifact<T>;
  getArtifact<T>(digest: string): LocalEvidenceArtifact<T>;
  appendEvent(runId: string, eventType: string, eventId: string, payload: unknown): LocalEvidenceEvent;
  withTransaction<T>(runId: string, operation: () => T): T;
  appendEventInTransaction(
    runId: string,
    eventType: string,
    eventId: string,
    payload: unknown,
    createdAt: string,
  ): LocalEvidenceEvent;
  getJournalEvent(runId: string, eventId: string): LocalEvidenceEvent | null;
  listJournal(runId: string): LocalEvidenceEvent[];
  listEventTypes(runId: string): string[];
  verifyJournal(runId: string): void;
}

export class LocalEvidenceAdapter implements GameEvidencePort {
  private readonly store: LocalEvidenceJournal;

  constructor(db: DatabaseSync) {
    this.store = new LocalEvidenceJournal(db);
  }

  putArtifact<T>(kind: string, content: T): LocalEvidenceArtifact<T> {
    return this.store.putArtifact(kind, content);
  }

  getArtifact<T>(digest: string): LocalEvidenceArtifact<T> {
    return this.store.getArtifact<T>(digest);
  }


  appendEvent(runId: string, eventType: string, eventId: string, payload: unknown): LocalEvidenceEvent {
    return this.store.appendEvent(runId, eventType, eventId, payload);
  }

  withTransaction<T>(runId: string, operation: () => T): T {
    return this.store.withTransaction(runId, operation);
  }

  appendEventInTransaction(
    runId: string,
    eventType: string,
    eventId: string,
    payload: unknown,
    createdAt: string,
  ): LocalEvidenceEvent {
    return this.store.appendEventInTransaction(runId, eventType, eventId, payload, createdAt);
  }

  getJournalEvent(runId: string, eventId: string): LocalEvidenceEvent | null {
    return this.store.getJournalEvent(runId, eventId);
  }

  listJournal(runId: string): LocalEvidenceEvent[] {
    return this.store.listJournal(runId);
  }

  listEventTypes(runId: string): string[] {
    return this.store.listEventTypes(runId);
  }

  verifyJournal(runId: string): void {
    this.store.verifyJournal(runId);
  }
}

export function createGameEvidencePort(db: DatabaseSync): GameEvidencePort {
  return new LocalEvidenceAdapter(db);
}
