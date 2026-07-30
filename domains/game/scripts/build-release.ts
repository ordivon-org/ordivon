import { execFileSync } from "node:child_process";
import { gzipSync } from "node:zlib";
import {
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { resolve } from "node:path";

import {
  checksumText,
  createReleaseManifest,
  RELEASE_ARCHIVE_NAME,
  RELEASE_ARCHIVE_PREFIX,
  RELEASE_TAG,
  releaseFileRecord,
  releaseReceiptMarkdown,
  validateReleaseIdentity,
} from "../src/release/artifact.ts";
import { createEvaluatedInputManifest } from "../src/release/inputs.ts";
import { listRulesetContracts, listScenarioContracts } from "../src/registry.ts";
import { createM5Evaluation } from "./m5-evaluation.ts";

function option(name: string, fallback: string): string {
  const index = process.argv.indexOf(name);
  if (index < 0) return fallback;
  const value = process.argv[index + 1];
  if (!value?.trim()) throw new TypeError(`${name} requires a value`);
  return value;
}

function git(args: string[]): string {
  return execFileSync("git", args, { encoding: "utf8" }).trim();
}

const output = resolve(option("--out", "dist/release"));
const ref = option("--ref", "HEAD");
const sourceCommit = git(["rev-parse", `${ref}^{commit}`]);
const sourceTree = git(["rev-parse", `${sourceCommit}^{tree}`]);
const head = git(["rev-parse", "HEAD^{commit}"]);
if (sourceCommit !== head) {
  throw new Error("release build requires the checked-out HEAD to equal the selected ref");
}
if (git(["status", "--porcelain", "--untracked-files=no"])) {
  throw new Error("release build requires a clean tracked working tree");
}
const packageJson = JSON.parse(readFileSync("package.json", "utf8")) as {
  name: string;
  version: string;
};
if (packageJson.name !== "ordivon-game") throw new TypeError("unexpected package name");
validateReleaseIdentity(packageJson.version, RELEASE_TAG);

rmSync(output, { recursive: true, force: true });
mkdirSync(resolve(output, "docs"), { recursive: true });

const evaluatedInputs = createEvaluatedInputManifest({
  scenarioContracts: listScenarioContracts(),
  rulesetContracts: listRulesetContracts(),
  sourceCommit,
  sourceTree,
});
writeFileSync(
  resolve(output, "evaluated-inputs.json"),
  JSON.stringify(evaluatedInputs, null, 2) + "\n",
);

const evaluation = await createM5Evaluation({
  sourceCommit,
  sourceTree,
  evaluatedInputsDigest: evaluatedInputs.evaluatedInputsDigest,
});
writeFileSync(
  resolve(output, "docs/M5-EVALUATION.json"),
  JSON.stringify(evaluation, null, 2) + "\n",
);

const archiveTar = execFileSync(
  "git",
  [
    "archive",
    "--format=tar",
    `--prefix=${RELEASE_ARCHIVE_PREFIX}/`,
    sourceCommit,
  ],
  { maxBuffer: 256 * 1024 * 1024 },
);
writeFileSync(
  resolve(output, RELEASE_ARCHIVE_NAME),
  gzipSync(archiveTar, { level: 9 }),
);

const release = createReleaseManifest({
  sourceCommit,
  sourceTree,
  evaluatedInputs,
  evaluatedInputsFile: releaseFileRecord(output, "evaluated-inputs.json"),
  evaluationFile: releaseFileRecord(output, "docs/M5-EVALUATION.json"),
  archiveFile: releaseFileRecord(output, RELEASE_ARCHIVE_NAME),
});
writeFileSync(
  resolve(output, "docs/M5-RELEASE.json"),
  JSON.stringify(release, null, 2) + "\n",
);
writeFileSync(
  resolve(output, "docs/M5-RECEIPT.md"),
  releaseReceiptMarkdown(release, evaluation),
);

const checksumPaths = [
  RELEASE_ARCHIVE_NAME,
  "evaluated-inputs.json",
  "docs/M5-EVALUATION.json",
  "docs/M5-RELEASE.json",
  "docs/M5-RECEIPT.md",
];
writeFileSync(
  resolve(output, "SHA256SUMS"),
  checksumText(checksumPaths.map((path) => releaseFileRecord(output, path))),
);

process.stdout.write(JSON.stringify({ output, release }, null, 2) + "\n");
