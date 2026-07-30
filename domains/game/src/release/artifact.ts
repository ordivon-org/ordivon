import { createHash } from "node:crypto";
import { readFileSync, statSync } from "node:fs";
import { isAbsolute, posix, resolve } from "node:path";

import { sha256 } from "../digest.ts";
import type { EvaluatedInputManifest } from "./inputs.ts";

export const RELEASE_VERSION = "0.1.0-alpha.1";
export const RELEASE_TAG = `v${RELEASE_VERSION}`;
export const RELEASE_ARCHIVE_PREFIX = `ordivon-game-station-zero-${RELEASE_TAG}`;
export const RELEASE_ARCHIVE_NAME = `${RELEASE_ARCHIVE_PREFIX}.tar.gz`;

export interface ReleaseFileRecord {
  path: string;
  sha256: string;
  bytes: number;
}

export interface M5EvaluationRun {
  runId: string;
  coordinationProfileId: string;
  status: string;
  reason: string | null;
  revision: number;
  score: number;
  graphDigest: string;
  curvesDigest: string;
  diagnosisDigest: string;
  frameCount: number;
  keyTurnCount: number;
  evidenceClassCounts: Record<string, number>;
}

export interface M5Evaluation {
  schemaVersion: 1;
  kind: "ordivon.game.m5-evaluation";
  sourceCommit: string;
  sourceTree: string;
  evaluatedInputsDigest: string;
  runs: {
    specialistContainment: M5EvaluationRun;
    engineerSeal: M5EvaluationRun;
  };
  comparison: {
    mode: "exact";
    comparisonDigest: string;
    inputDifferenceFields: string[];
    statusChanged: boolean;
    scoreDelta: number;
    minimumBatteryDelta: number;
  };
  browserJourney: {
    command: "pnpm e2e";
    expectedFirstOutcome: "victory";
    expectedSecondOutcome: "power_exhausted";
    replayRevision: 5;
    diagnosisEvidenceClass: "VERIFIED_DIRECT";
    comparisonMode: "exact";
    reloadRecoveryRequired: true;
  };
  conclusions: {
    deterministicFixtureReleasePathPassed: boolean;
    replayDiagnosisPassed: boolean;
    coordinationOnlyOutcomeDifferencePassed: boolean;
    runtimeDependenciesAdded: boolean;
    liveProvidersReleaseBlocking: boolean;
  };
}

export interface M5ReleaseManifest {
  schemaVersion: 1;
  kind: "ordivon.game.m5-release";
  product: "ordivon-game";
  releaseName: "Station Zero first playable";
  version: typeof RELEASE_VERSION;
  tag: typeof RELEASE_TAG;
  source: {
    commit: string;
    tree: string;
    archivePrefix: typeof RELEASE_ARCHIVE_PREFIX;
  };
  evaluatedInputs: ReleaseFileRecord & { digest: string };
  evaluation: ReleaseFileRecord;
  archive: ReleaseFileRecord;
  receiptPath: "docs/M5-RECEIPT.md";
  checksumPath: "SHA256SUMS";
  verification: {
    node: ">=26.0.0";
    packageManager: "pnpm@10.33.2";
    requiredTools: ["git", "tar"];
    commands: string[];
  };
  releaseDigest: string;
}

export function digestFile(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function releaseFileRecord(root: string, relativePath: string): ReleaseFileRecord {
  const safe = assertSafeReleasePath(relativePath);
  const absolute = resolve(root, safe);
  return {
    path: safe,
    sha256: digestFile(absolute),
    bytes: statSync(absolute).size,
  };
}

export function validateReleaseIdentity(packageVersion: string, tag: string): void {
  if (packageVersion !== RELEASE_VERSION) {
    throw new TypeError(`package version must be ${RELEASE_VERSION}, received ${packageVersion}`);
  }
  if (tag !== RELEASE_TAG) {
    throw new TypeError(`release tag must be ${RELEASE_TAG}, received ${tag}`);
  }
}

export function assertSafeReleasePath(path: string): string {
  const normalized = path.replaceAll("\\", "/");
  if (
    !normalized ||
    isAbsolute(normalized) ||
    normalized.startsWith("/") ||
    /^[A-Za-z]:/.test(normalized) ||
    normalized.split("/").some((part) => part === "" || part === "." || part === "..") ||
    posix.normalize(normalized) !== normalized
  ) {
    throw new TypeError(`unsafe release path: ${path}`);
  }
  return normalized;
}

export function checksumText(records: ReleaseFileRecord[]): string {
  const seen = new Set<string>();
  return [...records]
    .sort((left, right) => left.path.localeCompare(right.path))
    .map((record) => {
      const path = assertSafeReleasePath(record.path);
      if (seen.has(path)) throw new TypeError(`duplicate release path: ${path}`);
      seen.add(path);
      if (!/^[0-9a-f]{64}$/.test(record.sha256)) {
        throw new TypeError(`invalid SHA-256 for ${path}`);
      }
      return `${record.sha256}  ${path}`;
    })
    .join("\n") + "\n";
}

export function parseChecksumText(text: string): Array<{ path: string; sha256: string }> {
  const seen = new Set<string>();
  return text
    .split(/\r?\n/)
    .filter((line) => line.length > 0)
    .map((line) => {
      const match = /^([0-9a-f]{64})  (.+)$/.exec(line);
      if (!match) throw new TypeError(`invalid SHA256SUMS line: ${line}`);
      const path = assertSafeReleasePath(match[2]!);
      if (path === "SHA256SUMS") throw new TypeError("SHA256SUMS cannot checksum itself");
      if (seen.has(path)) throw new TypeError(`duplicate release path: ${path}`);
      seen.add(path);
      return { sha256: match[1]!, path };
    });
}

export function createReleaseManifest(input: {
  sourceCommit: string;
  sourceTree: string;
  evaluatedInputs: EvaluatedInputManifest;
  evaluatedInputsFile: ReleaseFileRecord;
  evaluationFile: ReleaseFileRecord;
  archiveFile: ReleaseFileRecord;
}): M5ReleaseManifest {
  if (!/^[0-9a-f]{40}$/.test(input.sourceCommit)) throw new TypeError("source commit must be a full SHA-1");
  if (!/^[0-9a-f]{40}$/.test(input.sourceTree)) throw new TypeError("source tree must be a full SHA-1");
  if (input.evaluatedInputs.sourceCommit !== input.sourceCommit) {
    throw new TypeError("evaluated inputs source commit differs");
  }
  if (input.evaluatedInputs.sourceTree !== input.sourceTree) {
    throw new TypeError("evaluated inputs source tree differs");
  }
  const base: Omit<M5ReleaseManifest, "releaseDigest"> = {
    schemaVersion: 1,
    kind: "ordivon.game.m5-release",
    product: "ordivon-game",
    releaseName: "Station Zero first playable",
    version: RELEASE_VERSION,
    tag: RELEASE_TAG,
    source: {
      commit: input.sourceCommit,
      tree: input.sourceTree,
      archivePrefix: RELEASE_ARCHIVE_PREFIX,
    },
    evaluatedInputs: {
      ...input.evaluatedInputsFile,
      digest: input.evaluatedInputs.evaluatedInputsDigest,
    },
    evaluation: input.evaluationFile,
    archive: input.archiveFile,
    receiptPath: "docs/M5-RECEIPT.md",
    checksumPath: "SHA256SUMS",
    verification: {
      node: ">=26.0.0",
      packageManager: "pnpm@10.33.2",
      requiredTools: ["git", "tar"],
      commands: [
        "pnpm install --frozen-lockfile",
        "pnpm check",
        "pnpm e2e",
        "pnpm receipt",
        "pnpm measure",
        "pnpm measure:replay",
        "pnpm release:inputs",
      ],
    },
  };
  return { ...base, releaseDigest: sha256(base) };
}

export function releaseReceiptMarkdown(
  release: M5ReleaseManifest,
  evaluation: M5Evaluation,
): string {
  return `# M5 receipt — Station Zero first playable ${release.tag}\n\n` +
    `## Verdict\n\n` +
    `The source-playable Alpha is bound to commit \`${release.source.commit}\`, tree ` +
    `\`${release.source.tree}\`, evaluated-input digest ` +
    `\`${release.evaluatedInputs.digest}\`, and archive SHA-256 ` +
    `\`${release.archive.sha256}\`.\n\n` +
    `The deterministic release journey proves a coordination-only change on the same ` +
    `\`power-constrained\` Case: \`${evaluation.runs.specialistContainment.status}\` versus ` +
    `\`${evaluation.runs.engineerSeal.reason}\`. Replay, evidence-linked diagnosis, exact ` +
    `comparison, and reload recovery are required by the Chromium gate.\n\n` +
    `## Release identity\n\n` +
    `- Version: \`${release.version}\`\n` +
    `- Tag: \`${release.tag}\`\n` +
    `- Release digest: \`${release.releaseDigest}\`\n` +
    `- Archive: \`${release.archive.path}\` (${release.archive.bytes} bytes)\n` +
    `- Evaluation: \`${release.evaluation.path}\`\n` +
    `- Evaluated inputs: \`${release.evaluatedInputs.path}\`\n\n` +
    `## Clean verification contract\n\n` +
    release.verification.commands.map((command) => `- \`${command}\``).join("\n") +
    `\n\nThe tag workflow builds, verifies, and uploads the same bytes. ` +
    `\`SHA256SUMS\` covers every uploaded evidence file except itself.\n`;
}
