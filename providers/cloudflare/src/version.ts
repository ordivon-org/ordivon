export const CAPABILITY_VERSIONS = {
  fetch: "fetch.v2",
  "browser.run": "browser.snapshot.v2",
  "artifact.get": "artifact.get.v1"
} as const;

export interface WorkerDeploymentIdentity {
  readonly source_commit: string | null;
  readonly worker_release_digest: string | null;
}

const CURRENT_TAG = /^git-([0-9a-f]{12})-src-([0-9a-f]{16})-[0-9]+$/;
const LEGACY_TAG = /^git-([0-9a-f]{12})-[0-9]+$/;

export function workerDeploymentIdentity(
  workerVersion: WorkerVersionMetadata
): WorkerDeploymentIdentity {
  const current = CURRENT_TAG.exec(workerVersion.tag);
  if (current !== null) {
    return {
      source_commit: current[1] ?? null,
      worker_release_digest: current[2] ?? null
    };
  }
  const legacy = LEGACY_TAG.exec(workerVersion.tag);
  return {
    source_commit: legacy?.[1] ?? null,
    worker_release_digest: null
  };
}
