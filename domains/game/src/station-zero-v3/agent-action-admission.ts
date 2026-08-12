import { sha256 } from "../digest.ts";

export const STATION_ZERO_V3_AGENT_ACTION_BINDING_KIND =
  "ordivon.game.station-zero-v3-agent-action-binding" as const;

export interface StationZeroV3AgentActionBinding {
  schemaVersion: 1;
  kind: typeof STATION_ZERO_V3_AGENT_ACTION_BINDING_KIND;
  subjectRef: string;
  cognitionRef: string;
  sourceAuthorityId: string;
  sourceEvidenceDigest: `sha256:${string}`;
  runId: string;
  planningId: string;
  worldRevision: number;
  worldDigest: string;
  actorId: string;
  intentDigest: `sha256:${string}`;
}

const BINDING_KEYS = [
  "schemaVersion",
  "kind",
  "subjectRef",
  "cognitionRef",
  "sourceAuthorityId",
  "sourceEvidenceDigest",
  "runId",
  "planningId",
  "worldRevision",
  "worldDigest",
  "actorId",
  "intentDigest",
] as const;

const DIGEST = /^sha256:[0-9a-f]{64}$/;

function record(value: unknown): Record<string, unknown> {
  if (value === null || Array.isArray(value) || typeof value !== "object") {
    throw new TypeError("Agent Action Binding must be an object");
  }
  return value as Record<string, unknown>;
}

function requiredString(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new TypeError(`${label} is required`);
  }
  return value;
}

function digestString(value: unknown, label: string): `sha256:${string}` {
  const retained = requiredString(value, label);
  if (!DIGEST.test(retained)) throw new TypeError(`${label} must be one sha256 digest`);
  return retained as `sha256:${string}`;
}

export function canonicalizeStationZeroV3AgentActionBinding(
  input: unknown,
): StationZeroV3AgentActionBinding {
  const value = record(input);
  const observedKeys = Object.keys(value).sort();
  const expectedKeys = [...BINDING_KEYS].sort();
  if (
    observedKeys.length !== expectedKeys.length ||
    observedKeys.some((key, index) => key !== expectedKeys[index])
  ) {
    throw new TypeError("Agent Action Binding has unexpected or missing fields");
  }
  if (value.schemaVersion !== 1) throw new TypeError("Agent Action Binding schemaVersion must be 1");
  if (value.kind !== STATION_ZERO_V3_AGENT_ACTION_BINDING_KIND) {
    throw new TypeError("Agent Action Binding kind is invalid");
  }
  if (!Number.isSafeInteger(value.worldRevision) || (value.worldRevision as number) < 0) {
    throw new TypeError("Agent Action Binding worldRevision must be a non-negative integer");
  }
  return {
    schemaVersion: 1,
    kind: STATION_ZERO_V3_AGENT_ACTION_BINDING_KIND,
    subjectRef: requiredString(value.subjectRef, "Agent Action Binding subjectRef"),
    cognitionRef: requiredString(value.cognitionRef, "Agent Action Binding cognitionRef"),
    sourceAuthorityId: requiredString(
      value.sourceAuthorityId,
      "Agent Action Binding sourceAuthorityId",
    ),
    sourceEvidenceDigest: digestString(
      value.sourceEvidenceDigest,
      "Agent Action Binding sourceEvidenceDigest",
    ),
    runId: requiredString(value.runId, "Agent Action Binding runId"),
    planningId: requiredString(value.planningId, "Agent Action Binding planningId"),
    worldRevision: value.worldRevision as number,
    worldDigest: requiredString(value.worldDigest, "Agent Action Binding worldDigest"),
    actorId: requiredString(value.actorId, "Agent Action Binding actorId"),
    intentDigest: digestString(value.intentDigest, "Agent Action Binding intentDigest"),
  };
}

export function stationZeroV3AgentActionBindingDigest(
  input: StationZeroV3AgentActionBinding,
): `sha256:${string}` {
  return `sha256:${sha256(canonicalizeStationZeroV3AgentActionBinding(input))}`;
}
