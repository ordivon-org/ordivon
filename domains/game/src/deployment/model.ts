import type { AuthorityPolicyMode } from "../team/model.ts";
export type LoadoutProfileId = "standard-loadout";
export type CoordinationProfileId = "specialist-containment" | "engineer-seal";
export interface DeploymentActor { actorId: string; providerOrder: string[]; }
export interface DeploymentManifest { schemaVersion: 1; kind: "ordivon.game.deployment-manifest"; runId: string; scenarioId: string; scenarioVersion: number; scenarioCaseId: string; rulesetId: string; rulesetVersion: number; genesisDigest: string; evaluatedInputsDigest: string; loadoutProfileId: LoadoutProfileId; coordinationProfileId: CoordinationProfileId; authorityPolicyMode: AuthorityPolicyMode; actors: DeploymentActor[]; manifestDigest: string; }
export interface DeploymentProviderOptions { coordinationProfileId: CoordinationProfileId; }
export interface DeploymentProfileDefinition<T extends string> { profileId: T; label: string; description: string; }
export interface DeploymentCatalog { schemaVersion: 1; kind: "ordivon.game.deployment-catalog"; loadouts: DeploymentProfileDefinition<LoadoutProfileId>[]; coordination: DeploymentProfileDefinition<CoordinationProfileId>[]; }
