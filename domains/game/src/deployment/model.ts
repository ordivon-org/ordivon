import type { AuthorityPolicyMode } from "../team/model.ts";

export const STANDARD_LOADOUT_PROFILE_ID = "standard-loadout" as const;
export type CoordinationProfileId = "specialist-containment" | "engineer-seal";

export interface DeploymentActor {
  actorId: string;
  providerOrder: string[];
}

export interface DeploymentManifest {
  schemaVersion: 1;
  kind: "ordivon.game.deployment-manifest";
  runId: string;
  scenarioId: string;
  scenarioVersion: number;
  scenarioCaseId: string;
  rulesetId: string;
  rulesetVersion: number;
  genesisDigest: string;
  evaluatedInputsDigest: string;
  loadoutProfileId: typeof STANDARD_LOADOUT_PROFILE_ID;
  coordinationProfileId: CoordinationProfileId;
  authorityPolicyMode: AuthorityPolicyMode;
  actors: DeploymentActor[];
  manifestDigest: string;
}

export interface DeploymentProviderOptions {
  coordinationProfileId: CoordinationProfileId;
}

export interface DeploymentProfileDefinition<T extends string> {
  profileId: T;
  label: string;
  description: string;
}

export interface DeploymentCatalog {
  schemaVersion: 1;
  kind: "ordivon.game.deployment-catalog";
  fixedLoadout: DeploymentProfileDefinition<typeof STANDARD_LOADOUT_PROFILE_ID>;
  coordination: DeploymentProfileDefinition<CoordinationProfileId>[];
}
