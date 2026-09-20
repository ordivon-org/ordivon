import { deploymentCatalog } from "../deployment/profiles.ts";
import { listScenarioCases } from "../scenario-cases.ts";
import { initialTeamWorld } from "../scenario.ts";
import type { ActorRole, AuthorityPolicyMode } from "../team/model.ts";
import { objectivesForRole, TEAM_OBJECTIVE_GRAPH } from "../team/objectives.ts";
import { DOCTRINES } from "./experience.ts";

export interface MissionProviderOption {
  providerId: string;
  label: string;
  deterministic: boolean;
  executionOwner: "game" | "external";
}

export const MISSION_PROVIDER_OPTIONS: readonly MissionProviderOption[] = [
  { providerId: "fixture", label: "Fixture baseline", deterministic: true, executionOwner: "game" },
] as const;

export type MissionProviderName = string;

export function validateMissionProviderOptions(
  providers: readonly MissionProviderOption[],
): MissionProviderOption[] {
  if (providers.length === 0) throw new TypeError("Mission Provider catalog must not be empty");
  const ids = new Set<string>();
  const normalized = providers.map((provider) => {
    if (!provider.providerId || provider.providerId !== provider.providerId.trim()) {
      throw new TypeError("Mission Provider identity must be non-empty and trimmed");
    }
    if (!provider.label || provider.label !== provider.label.trim()) {
      throw new TypeError(`Mission Provider ${provider.providerId} label must be non-empty and trimmed`);
    }
    if (ids.has(provider.providerId)) throw new TypeError(`duplicate Mission Provider identity: ${provider.providerId}`);
    ids.add(provider.providerId);
    return { ...provider };
  });
  if (!ids.has("fixture")) throw new TypeError("Mission Provider catalog must retain the fixture baseline");
  return normalized;
}

export function isMissionProviderName(
  value: unknown,
  providers: readonly MissionProviderOption[] = MISSION_PROVIDER_OPTIONS,
): value is MissionProviderName {
  return typeof value === "string" && value.length > 0 && value === value.trim()
    && providers.some((option) => option.providerId === value);
}

export const AUTHORITY_POLICY_OPTIONS: Array<{
  policyMode: AuthorityPolicyMode;
  label: string;
}> = [
  { policyMode: "autonomous", label: "Autonomous" },
  { policyMode: "supervised", label: "Supervised" },
  { policyMode: "locked", label: "Locked" },
];

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
  providers: MissionProviderOption[];
  authorityPolicies: typeof AUTHORITY_POLICY_OPTIONS;
  doctrines: typeof DOCTRINES;
  playDefaults: { doctrineId: "critical-approval"; scenarioCaseId: "baseline"; coordinationProfileId: "specialist-containment" };
  objectives: typeof TEAM_OBJECTIVE_GRAPH.nodes;
  evidenceOrdering: {
    authoritative: ["world-revision", "host-sequence", "projection-revision"];
    timestamp: "metadata-only";
  };
}

export function createMissionControlCatalog(
  providerOptions: readonly MissionProviderOption[] = MISSION_PROVIDER_OPTIONS,
): MissionControlCatalog {
  const providers = validateMissionProviderOptions(providerOptions);
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
    providers: providers.map((option) => ({ ...option })),
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
