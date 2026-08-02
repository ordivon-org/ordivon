import { canonicalJson, sha256 } from "../digest.ts";
import { HostStore } from "../host-contract/journal.ts";
import type { GameStore } from "../storage.ts";
import { teamCognitionStarted } from "../team/execution-store.ts";
import type { AuthorityPolicyMode } from "../team/model.ts";
import {
  STANDARD_LOADOUT_PROFILE_ID,
  type DeploymentManifest,
} from "./model.ts";
import { resolveCoordinationProfile } from "./profiles.ts";

export class DeploymentError extends Error {
  readonly code: "deployment_conflict" | "deployment_corrupt";

  constructor(code: DeploymentError["code"], message: string) {
    super(message);
    this.name = "DeploymentError";
    this.code = code;
  }
}

export interface BindDeploymentInput {
  runId: string;
  coordinationProfileId?: string;
  authorityPolicyMode: AuthorityPolicyMode;
  actors: Array<{ actorId: string; providerOrder: string[] }>;
}

function baseManifest(store: GameStore, input: BindDeploymentInput) {
  const run = store.getRun(input.runId);
  return {
    schemaVersion: 1 as const,
    kind: "ordivon.game.deployment-manifest" as const,
    runId: run.runId,
    scenarioId: run.scenarioId,
    scenarioVersion: run.scenarioVersion,
    scenarioCaseId: run.scenarioCaseId,
    rulesetId: run.rulesetId,
    rulesetVersion: run.rulesetVersion,
    genesisDigest: run.genesisDigest,
    evaluatedInputsDigest: run.evaluatedInputsDigest,
    loadoutProfileId: STANDARD_LOADOUT_PROFILE_ID,
    coordinationProfileId: resolveCoordinationProfile(input.coordinationProfileId),
    authorityPolicyMode: input.authorityPolicyMode,
    actors: input.actors
      .map((actor) => ({
        actorId: actor.actorId,
        providerOrder: [...actor.providerOrder],
      }))
      .sort((left, right) => left.actorId.localeCompare(right.actorId)),
  };
}

export class DeploymentStore {
  readonly game: GameStore;
  readonly host: HostStore;

  constructor(game: GameStore) {
    this.game = game;
    this.host = new HostStore(game.db);
  }

  get(runId = this.game.activeRunId): DeploymentManifest | null {
    const events = this.host.listJournal(runId).filter(
      (event) => event.eventType === "game.deployment-bound",
    );
    if (events.length === 0) return null;
    if (events.length !== 1) {
      throw new DeploymentError(
        "deployment_corrupt",
        "Run has multiple deployment bindings",
      );
    }

    const payload = events[0]!.payload as {
      artifactDigest?: string;
      manifestDigest?: string;
    };
    if (!payload.artifactDigest || !payload.manifestDigest) {
      throw new DeploymentError(
        "deployment_corrupt",
        "Deployment binding payload is incomplete",
      );
    }

    const artifact = this.host.getArtifact<DeploymentManifest>(payload.artifactDigest);
    if (artifact.kind !== "game-deployment-manifest") {
      throw new DeploymentError(
        "deployment_corrupt",
        "Deployment Artifact kind differs",
      );
    }
    const manifest = artifact.content;
    const { manifestDigest, ...base } = manifest;
    if (sha256(base) !== manifestDigest || manifestDigest !== payload.manifestDigest) {
      throw new DeploymentError(
        "deployment_corrupt",
        "Deployment Manifest digest mismatch",
      );
    }

    const run = this.game.getRun(runId);
    if (
      manifest.runId !== runId ||
      manifest.genesisDigest !== run.genesisDigest ||
      manifest.evaluatedInputsDigest !== run.evaluatedInputsDigest ||
      manifest.loadoutProfileId !== STANDARD_LOADOUT_PROFILE_ID
    ) {
      throw new DeploymentError(
        "deployment_corrupt",
        "Deployment Manifest differs from retained Run identity",
      );
    }
    return manifest;
  }

  bind(input: BindDeploymentInput): DeploymentManifest {
    const base = baseManifest(this.game, input);
    const manifest: DeploymentManifest = {
      ...base,
      manifestDigest: sha256(base),
    };
    const existing = this.get(input.runId);
    if (existing) {
      if (canonicalJson(existing) !== canonicalJson(manifest)) {
        throw new DeploymentError(
          "deployment_conflict",
          "Deployment Manifest is immutable and differs from the retained binding",
        );
      }
      return existing;
    }

    if (this.game.loadState(input.runId).revision !== 0) {
      throw new DeploymentError(
        "deployment_conflict",
        "Deployment must bind before World execution begins",
      );
    }
    if (teamCognitionStarted(this.game, input.runId)) {
      throw new DeploymentError(
        "deployment_conflict",
        "Deployment must bind before cognition creates a Round",
      );
    }

    const artifact = this.host.putArtifact("game-deployment-manifest", manifest);
    this.host.appendEvent(
      input.runId,
      "game.deployment-bound",
      `host-event:deployment:${manifest.manifestDigest}`,
      {
        artifactDigest: artifact.digest,
        manifestDigest: manifest.manifestDigest,
      },
    );
    return this.get(input.runId)!;
  }
}
