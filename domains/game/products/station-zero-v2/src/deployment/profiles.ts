import {
  STANDARD_LOADOUT_PROFILE_ID,
  type CoordinationProfileId,
  type DeploymentCatalog,
} from "./model.ts";

const FIXED_LOADOUT = {
  profileId: STANDARD_LOADOUT_PROFILE_ID,
  label: "Standard emergency loadout",
  description: "Preserves the verified Station Zero Genesis item totals and locations.",
} as const;

const COORDINATION = [
  {
    profileId: "specialist-containment" as const,
    label: "Specialist containment",
    description: "Security contains the breach while Engineer follows the shorter repair route.",
  },
  {
    profileId: "engineer-seal" as const,
    label: "Engineer sealing route",
    description: "Engineer acquires sealant and seals the breach; Security waits. Longer but independently verifiable.",
  },
];

export function deploymentCatalog(): DeploymentCatalog {
  return {
    schemaVersion: 1,
    kind: "ordivon.game.deployment-catalog",
    fixedLoadout: structuredClone(FIXED_LOADOUT),
    coordination: structuredClone(COORDINATION),
  };
}

export function resolveCoordinationProfile(
  profileId: string | undefined,
): CoordinationProfileId {
  const selected = profileId ?? "specialist-containment";
  if (!COORDINATION.some((profile) => profile.profileId === selected)) {
    throw new TypeError(`unsupported coordination profile: ${selected}`);
  }
  return selected as CoordinationProfileId;
}
