import type { DatabaseSync } from "node:sqlite";

import {
  HostStore,
  type HostArtifact,
  type HostJournalEvent,
} from "../host-contract/journal.ts";

/**
 * Narrow Game-consumer durability port.
 *
 * This interface does not assign semantic authority to persistence. It exists so
 * Game/domain code can stop importing the legacy embedded HostStore directly.
 * The current adapter remains local only because Station Zero requires one
 * SQLite transaction to atomically bind Game projections and retained journal
 * evidence. A source-current external Host replacement must preserve that
 * invariant before this compatibility adapter can be deleted.
 */
export interface GameEvidencePort {
  putArtifact<T>(kind: string, content: T): HostArtifact<T>;
  getArtifact<T>(digest: string): HostArtifact<T>;
  putProtocolArtifact<T>(kind: string, content: T, createdAt?: string): HostArtifact<T>;
  getProtocolArtifact<T>(digest: string): HostArtifact<T>;
  appendEvent(runId: string, eventType: string, eventId: string, payload: unknown): HostJournalEvent;
  withTransaction<T>(runId: string, operation: () => T): T;
  appendEventInTransaction(
    runId: string,
    eventType: string,
    eventId: string,
    payload: unknown,
    createdAt: string,
  ): HostJournalEvent;
  getJournalEvent(runId: string, eventId: string): HostJournalEvent | null;
  listJournal(runId: string): HostJournalEvent[];
  listEventTypes(runId: string): string[];
  verifyJournal(runId: string): void;
}

export class LegacyEmbeddedHostEvidenceAdapter implements GameEvidencePort {
  private readonly store: HostStore;

  constructor(db: DatabaseSync) {
    this.store = new HostStore(db);
  }

  putArtifact<T>(kind: string, content: T): HostArtifact<T> {
    return this.store.putArtifact(kind, content);
  }

  getArtifact<T>(digest: string): HostArtifact<T> {
    return this.store.getArtifact<T>(digest);
  }

  putProtocolArtifact<T>(kind: string, content: T, createdAt?: string): HostArtifact<T> {
    return createdAt === undefined
      ? this.store.putProtocolArtifact(kind, content)
      : this.store.putProtocolArtifact(kind, content, createdAt);
  }

  getProtocolArtifact<T>(digest: string): HostArtifact<T> {
    return this.store.getProtocolArtifact<T>(digest);
  }

  appendEvent(runId: string, eventType: string, eventId: string, payload: unknown): HostJournalEvent {
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
  ): HostJournalEvent {
    return this.store.appendEventInTransaction(runId, eventType, eventId, payload, createdAt);
  }

  getJournalEvent(runId: string, eventId: string): HostJournalEvent | null {
    return this.store.getJournalEvent(runId, eventId);
  }

  listJournal(runId: string): HostJournalEvent[] {
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
  return new LegacyEmbeddedHostEvidenceAdapter(db);
}
