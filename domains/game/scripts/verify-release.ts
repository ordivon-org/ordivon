import { execFileSync } from "node:child_process";
import {
  mkdtempSync,
  readFileSync,
  rmSync,
  statSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import {
  digestFile,
  parseChecksumText,
  RELEASE_ARCHIVE_NAME,
  RELEASE_ARCHIVE_PREFIX,
  RELEASE_TAG,
  RELEASE_VERSION,
  type M5Evaluation,
  type M5ReleaseManifest,
  validateReleaseIdentity,
} from "../src/release/artifact.ts";
import { sha256 } from "../src/digest.ts";
import type { EvaluatedInputManifest } from "../src/release/inputs.ts";

function option(name: string, fallback: string): string {
  const index = process.argv.indexOf(name);
  if (index < 0) return fallback;
  const value = process.argv[index + 1];
  if (!value?.trim()) throw new TypeError(`${name} requires a value`);
  return value;
}

function run(
  executable: string,
  args: string[],
  cwd: string,
  env: NodeJS.ProcessEnv = process.env,
): void {
  execFileSync(executable, args, {
    cwd,
    env,
    stdio: "inherit",
    maxBuffer: 256 * 1024 * 1024,
  });
}

const releaseDirectory = resolve(option("--dir", "dist/release"));
const checksumPath = resolve(releaseDirectory, "SHA256SUMS");
const checksums = parseChecksumText(readFileSync(checksumPath, "utf8"));
const expectedChecksumPaths = [
  RELEASE_ARCHIVE_NAME,
  "docs/M5-EVALUATION.json",
  "docs/M5-RECEIPT.md",
  "docs/M5-RELEASE.json",
  "evaluated-inputs.json",
].sort();
if (JSON.stringify(checksums.map((record) => record.path).sort()) !== JSON.stringify(expectedChecksumPaths)) {
  throw new Error("SHA256SUMS does not enumerate the exact release asset set");
}
for (const record of checksums) {
  const path = resolve(releaseDirectory, record.path);
  if (digestFile(path) !== record.sha256) {
    throw new Error(`release checksum differs: ${record.path}`);
  }
}

const release = JSON.parse(
  readFileSync(resolve(releaseDirectory, "docs/M5-RELEASE.json"), "utf8"),
) as M5ReleaseManifest;
const evaluation = JSON.parse(
  readFileSync(resolve(releaseDirectory, "docs/M5-EVALUATION.json"), "utf8"),
) as M5Evaluation;
const evaluatedInputs = JSON.parse(
  readFileSync(resolve(releaseDirectory, "evaluated-inputs.json"), "utf8"),
) as EvaluatedInputManifest;
validateReleaseIdentity(release.version, release.tag);
if (release.version !== RELEASE_VERSION || release.tag !== RELEASE_TAG) {
  throw new Error("release identity differs");
}
const { releaseDigest, ...releaseBase } = release;
if (sha256(releaseBase) !== releaseDigest) throw new Error("release manifest digest differs");
for (const record of [release.evaluatedInputs, release.evaluation]) {
  const path = resolve(releaseDirectory, record.path);
  if (digestFile(path) !== record.sha256 || statSync(path).size !== record.bytes) {
    throw new Error(`release manifest file record differs: ${record.path}`);
  }
}
if (release.archive.path !== RELEASE_ARCHIVE_NAME) throw new Error("archive path differs");
if (release.source.archivePrefix !== RELEASE_ARCHIVE_PREFIX) throw new Error("archive prefix differs");
if (release.archive.sha256 !== digestFile(resolve(releaseDirectory, release.archive.path))) {
  throw new Error("release manifest archive digest differs");
}
if (release.archive.bytes !== statSync(resolve(releaseDirectory, release.archive.path)).size) {
  throw new Error("release manifest archive size differs");
}
if (
  evaluatedInputs.evaluatedInputsDigest !== release.evaluatedInputs.digest ||
  evaluatedInputs.sourceCommit !== release.source.commit ||
  evaluatedInputs.sourceTree !== release.source.tree ||
  evaluation.sourceCommit !== release.source.commit ||
  evaluation.sourceTree !== release.source.tree ||
  evaluation.evaluatedInputsDigest !== release.evaluatedInputs.digest
) {
  throw new Error("release provenance bindings differ");
}
if (
  !evaluation.conclusions.deterministicFixtureReleasePathPassed ||
  !evaluation.conclusions.replayDiagnosisPassed ||
  !evaluation.conclusions.coordinationOnlyOutcomeDifferencePassed ||
  evaluation.conclusions.runtimeDependenciesAdded ||
  evaluation.conclusions.liveProvidersReleaseBlocking ||
  evaluation.runs.specialistContainment.status !== "victory" ||
  evaluation.runs.engineerSeal.reason !== "power_exhausted" ||
  evaluation.comparison.mode !== "exact" ||
  JSON.stringify(evaluation.comparison.inputDifferenceFields) !== JSON.stringify(["coordinationProfileId"]) ||
  evaluation.browserJourney.expectedFirstOutcome !== "victory" ||
  evaluation.browserJourney.expectedSecondOutcome !== "power_exhausted" ||
  evaluation.browserJourney.replayRevision !== 5 ||
  evaluation.browserJourney.diagnosisEvidenceClass !== "VERIFIED_DIRECT" ||
  !evaluation.browserJourney.reloadRecoveryRequired
) {
  throw new Error("M5 evaluation acceptance failed");
}

const directory = mkdtempSync(join(tmpdir(), "ordivon-game-release-verify-"));
try {
  run("tar", ["-xzf", resolve(releaseDirectory, RELEASE_ARCHIVE_NAME), "-C", directory], directory);
  const root = resolve(directory, RELEASE_ARCHIVE_PREFIX);
  const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8")) as {
    name: string;
    version: string;
  };
  if (pkg.name !== "ordivon-game") throw new Error("archive package name differs");
  validateReleaseIdentity(pkg.version, release.tag);

  const installArgs = ["install", "--frozen-lockfile"];
  if (process.env.ORDIVON_RELEASE_OFFLINE === "1") installArgs.push("--offline");
  run("pnpm", installArgs, root);
  run("pnpm", ["check"], root);
  run("pnpm", ["e2e"], root, {
    ...process.env,
    TMPDIR: process.env.ORDIVON_BROWSER_TMPDIR ?? "/tmp",
  });
  run("pnpm", ["receipt"], root);
  run("pnpm", ["measure"], root);
  run("pnpm", ["measure:replay"], root);
  const recomputedPath = resolve(directory, "evaluated-inputs.recomputed.json");
  run("pnpm", ["release:inputs", "--", "--out", recomputedPath], root);
  const recomputed = JSON.parse(readFileSync(recomputedPath, "utf8")) as EvaluatedInputManifest;
  if (
    recomputed.evaluatedInputsDigest !== evaluatedInputs.evaluatedInputsDigest ||
    JSON.stringify(recomputed.files) !== JSON.stringify(evaluatedInputs.files) ||
    JSON.stringify(recomputed.scenarioContracts) !== JSON.stringify(evaluatedInputs.scenarioContracts) ||
    JSON.stringify(recomputed.rulesetContracts) !== JSON.stringify(evaluatedInputs.rulesetContracts)
  ) {
    throw new Error("fresh archive evaluated inputs differ");
  }

  process.stdout.write(JSON.stringify({
    schemaVersion: 1,
    kind: "ordivon.game.release-verification",
    tag: release.tag,
    sourceCommit: release.source.commit,
    sourceTree: release.source.tree,
    archiveSha256: release.archive.sha256,
    evaluatedInputsDigest: release.evaluatedInputs.digest,
    cleanDirectory: true,
    checksumsVerified: checksums.length,
    installPassed: true,
    coreCheckPassed: true,
    browserJourneyPassed: true,
    receiptPassed: true,
    measurementPassed: true,
    replayPerformancePassed: true,
    evaluatedInputsReproduced: true,
  }, null, 2) + "\n");
} finally {
  rmSync(directory, { recursive: true, force: true });
}
