import { deploymentCatalog } from "../deployment/profiles.ts";
import { listScenarioCases } from "../scenario-cases.ts";
import { initialTeamWorld } from "../scenario.ts";
import type { ActorRole, AuthorityPolicyMode } from "../team/model.ts";
import { objectivesForRole, TEAM_OBJECTIVE_GRAPH } from "../team/objectives.ts";
import { DOCTRINES } from "./experience.ts";

export const MISSION_PROVIDER_OPTIONS = [
  { providerId: "fixture", label: "Fixture baseline", deterministic: true },
  { providerId: "codex", label: "Codex", deterministic: false },
  { providerId: "hermes", label: "Hermes / DeepSeek", deterministic: false },
  { providerId: "codex-hermes", label: "Codex → Hermes", deterministic: false },
  { providerId: "hermes-codex", label: "Hermes → Codex", deterministic: false },
] as const;

export type MissionProviderName = typeof MISSION_PROVIDER_OPTIONS[number]["providerId"];

export const AUTHORITY_POLICY_OPTIONS: Array<{
  policyMode: AuthorityPolicyMode;
  label: string;
}> = [
  { policyMode: "autonomous", label: "Autonomous" },
  { policyMode: "supervised", label: "Supervised" },
  { policyMode: "locked", label: "Locked" },
];

export function isMissionProviderName(value: unknown): value is MissionProviderName {
  return MISSION_PROVIDER_OPTIONS.some((option) => option.providerId === value);
}

export interface MissionControlCatalog {
  schemaVersion: 1;
  scenario: {
    scenarioId: "station-zero";
    scenarioVersion: 2;
    rulesetId: "station-zero-core";
    rulesetVersion: 3;
    seedSemantics: "compatibility-label";
  };
  cases: ReturnType<typeof listScenarioCases>;
  fixedLoadout: ReturnType<typeof deploymentCatalog>["fixedLoadout"];
  coordinationProfiles: ReturnType<typeof deploymentCatalog>["coordination"];
  actors: Array<{
    actorId: string;
    name: string;
    role: Exclude<ActorRole, "coordinator">;
    defaultProvider: MissionProviderName;
    objectiveIds: string[];
  }>;
  providers: Array<{ providerId: MissionProviderName; label: string; deterministic: boolean }>;
  authorityPolicies: typeof AUTHORITY_POLICY_OPTIONS;
  doctrines: typeof DOCTRINES;
  playDefaults: { doctrineId: "critical-approval"; scenarioCaseId: "baseline"; coordinationProfileId: "specialist-containment" };
  objectives: typeof TEAM_OBJECTIVE_GRAPH.nodes;
  evidenceOrdering: {
    authoritative: ["world-revision", "host-sequence", "projection-revision"];
    timestamp: "metadata-only";
  };
}

export function createMissionControlCatalog(): MissionControlCatalog {
  const world = initialTeamWorld();
  const roles: Record<string, Exclude<ActorRole, "coordinator">> = {
    "engineer-01": "engineer",
    "medic-01": "medic",
    "security-01": "security",
  };
  const actors = Object.values(world.agents).map((actor) => {
    const role = roles[actor.id];
    if (!role) throw new Error(`Scenario Actor lacks catalog role: ${actor.id}`);
    return {
      actorId: actor.id,
      name: actor.name,
      role,
      defaultProvider: "fixture" as const,
      objectiveIds: objectivesForRole(role),
    };
  });
  const deployment = deploymentCatalog();
  return {
    schemaVersion: 1,
    scenario: {
      scenarioId: "station-zero",
      scenarioVersion: 2,
      rulesetId: "station-zero-core",
      rulesetVersion: 3,
      seedSemantics: "compatibility-label",
    },
    cases: listScenarioCases("station-zero", 2),
    fixedLoadout: deployment.fixedLoadout,
    coordinationProfiles: deployment.coordination,
    actors,
    providers: MISSION_PROVIDER_OPTIONS.map((option) => ({ ...option })),
    authorityPolicies: AUTHORITY_POLICY_OPTIONS.map((option) => ({ ...option })),
    doctrines: DOCTRINES.map((entry) => ({ ...entry })),
    playDefaults: { doctrineId: "critical-approval", scenarioCaseId: "baseline", coordinationProfileId: "specialist-containment" },
    objectives: TEAM_OBJECTIVE_GRAPH.nodes.map((node) => structuredClone(node)),
    evidenceOrdering: {
      authoritative: ["world-revision", "host-sequence", "projection-revision"],
      timestamp: "metadata-only",
    },
  };
}
