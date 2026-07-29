import type { ProtocolJson } from "./canonical.ts";
import { protocolDigest, validateProtocolJson } from "./canonical.ts";
import type { HostWorkloadObject } from "./model.ts";
import { validateHostWorkloadObject } from "./validate.ts";
import type { HostArtifact, HostJournalEvent } from "../host/model.ts";
import type { HostStore } from "../host/store.ts";

export interface HostContractEventPayload {
  schemaVersion: 1;
  kind: "ordivon.game.host-contract-event";
  contractDigest: `sha256:${string}`;
  contractKind: string;
  subjectRef: string;
  relatedDigests: `sha256:${string}`[];
}

export interface HostContractTranscriptEntry {
  eventId: string;
  eventType: string;
  subjectRef: string;
  contractDigest: `sha256:${string}`;
  contractKind: string;
  relatedDigests: `sha256:${string}`[];
  object: ProtocolJson;
  sequence: number;
}

export class HostContractStore {
  readonly host: HostStore;
  private activeRunId: string | null = null;

  constructor(host: HostStore) {
    this.host = host;
  }

  batch<T>(runId: string, operation: () => T): T {
    if (this.activeRunId === runId) return operation();
    if (this.activeRunId !== null) throw new Error("Host Contract Store cannot nest batches for different Runs");
    return this.host.withTransaction(runId, () => {
      this.activeRunId = runId;
      try {
        return operation();
      } finally {
        this.activeRunId = null;
      }
    });
  }

  putWireObject(
    runId: string,
    eventType: string,
    eventId: string,
    subjectRef: string,
    value: HostWorkloadObject,
    options: {
      relatedDigests?: `sha256:${string}`[];
      createdAt?: string;
    } = {},
  ): HostArtifact<HostWorkloadObject> {
    const validated = validateHostWorkloadObject(value);
    return this.putProtocolObject(runId, eventType, eventId, subjectRef, validated, options);
  }

  putProtocolObject<T>(
    runId: string,
    eventType: string,
    eventId: string,
    subjectRef: string,
    value: T,
    options: {
      relatedDigests?: `sha256:${string}`[];
      createdAt?: string;
      artifactKind?: string;
    } = {},
  ): HostArtifact<T> {
    validateProtocolJson(value);
    if (!eventType.startsWith("host-contract.")) {
      throw new TypeError("Host Contract event type must start with host-contract.");
    }
    if (!eventId.startsWith("host-contract:")) {
      throw new TypeError("Host Contract event identity must start with host-contract:");
    }
    if (!subjectRef.trim()) throw new TypeError("Host Contract subjectRef is required");
    const contractKind = typeof value === "object" && value !== null && !Array.isArray(value)
      && typeof value.kind === "string"
      ? value.kind
      : options.artifactKind ?? "ordivon.protocol-object";
    const createdAt = options.createdAt ?? new Date().toISOString();
    const write = (): HostArtifact<T> => {
      const artifact = this.host.putProtocolArtifact(
        options.artifactKind ?? contractKind,
        value,
        createdAt,
      );
      const payload: HostContractEventPayload = {
        schemaVersion: 1,
        kind: "ordivon.game.host-contract-event",
        contractDigest: artifact.digest as `sha256:${string}`,
        contractKind,
        subjectRef,
        relatedDigests: [...new Set(options.relatedDigests ?? [])].sort(),
      };
      this.host.appendEventInTransaction(
        runId,
        eventType,
        eventId,
        payload,
        createdAt,
      );
      return artifact;
    };
    return this.activeRunId === runId ? write() : this.batch(runId, write);
  }

  get<T extends ProtocolJson>(digest: string): HostArtifact<T> {
    return this.host.getProtocolArtifact<T>(digest);
  }

  transcript(runId: string): HostContractTranscriptEntry[] {
    return this.host.listJournal(runId)
      .filter((event) => event.eventType.startsWith("host-contract."))
      .map((event) => this.entry(event));
  }

  count(runId: string, contractKind: string): number {
    return this.transcript(runId).filter((entry) => entry.contractKind === contractKind).length;
  }

  latest(runId: string, subjectRef: string, contractKind: string): HostContractTranscriptEntry | null {
    return this.transcript(runId)
      .filter((entry) => entry.subjectRef === subjectRef && entry.contractKind === contractKind)
      .at(-1) ?? null;
  }

  private entry(event: HostJournalEvent): HostContractTranscriptEntry {
    const payload = event.payload as Partial<HostContractEventPayload>;
    if (
      payload.schemaVersion !== 1 ||
      payload.kind !== "ordivon.game.host-contract-event" ||
      typeof payload.contractDigest !== "string" ||
      typeof payload.contractKind !== "string" ||
      typeof payload.subjectRef !== "string" ||
      !Array.isArray(payload.relatedDigests)
    ) {
      throw new Error(`invalid Host Contract journal payload: ${event.eventId}`);
    }
    const artifact = this.host.getProtocolArtifact<ProtocolJson>(payload.contractDigest);
    if (protocolDigest(artifact.content) !== payload.contractDigest) {
      throw new Error(`Host Contract Artifact digest mismatch: ${event.eventId}`);
    }
    return {
      eventId: event.eventId,
      eventType: event.eventType,
      subjectRef: payload.subjectRef,
      contractDigest: payload.contractDigest as `sha256:${string}`,
      contractKind: payload.contractKind,
      relatedDigests: payload.relatedDigests as `sha256:${string}`[],
      object: artifact.content,
      sequence: event.sequence,
    };
  }
}
