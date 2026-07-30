import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  assertSafeReleasePath,
  checksumText,
  createReleaseManifest,
  parseChecksumText,
  RELEASE_ARCHIVE_NAME,
  RELEASE_TAG,
  RELEASE_VERSION,
  releaseFileRecord,
  releaseReceiptMarkdown,
  validateReleaseIdentity,
  type M5Evaluation,
} from "../src/release/artifact.ts";
import type { EvaluatedInputManifest } from "../src/release/inputs.ts";

const commit = "a".repeat(40);
const tree = "b".repeat(40);
const evaluatedInputs: EvaluatedInputManifest = {
  schemaVersion: 1,
  product: "ordivon-game",
  packageVersion: RELEASE_VERSION,
  scenarioContracts: [{ id: "station-zero", version: 2 }],
  rulesetContracts: [{ id: "station-zero-core", version: 3 }],
  files: [],
  evaluatedInputsDigest: "digest:inputs",
  sourceCommit: commit,
  sourceTree: tree,
};

function record(path: string, sha = "c".repeat(64), bytes = 1) {
  return { path, sha256: sha, bytes };
}

test("release identity and paths fail closed", () => {
  assert.doesNotThrow(() => validateReleaseIdentity(RELEASE_VERSION, RELEASE_TAG));
  assert.throws(() => validateReleaseIdentity("0.1.0", RELEASE_TAG), /package version/);
  assert.throws(() => validateReleaseIdentity(RELEASE_VERSION, "v0.1.0"), /release tag/);
  for (const path of ["", "/absolute", "C:\\escape", "../escape", "docs/../escape", "docs//file", "."]) {
    assert.throws(() => assertSafeReleasePath(path), /unsafe release path/);
  }
  assert.equal(assertSafeReleasePath("docs/M5-RELEASE.json"), "docs/M5-RELEASE.json");
});

test("SHA256SUMS is sorted, unique, parseable, and never self-referential", () => {
  const text = checksumText([
    record("docs/M5-RELEASE.json", "b".repeat(64)),
    record(RELEASE_ARCHIVE_NAME, "a".repeat(64)),
  ]);
  assert.match(text.split("\n")[0]!, /docs\/M5-RELEASE\.json/);
  assert.deepEqual(parseChecksumText(text), [
    { sha256: "b".repeat(64), path: "docs/M5-RELEASE.json" },
    { sha256: "a".repeat(64), path: RELEASE_ARCHIVE_NAME },
  ]);
  assert.throws(() => checksumText([record("same"), record("same")]), /duplicate/);
  assert.throws(() => checksumText([record("bad", "not-a-digest")]), /invalid SHA-256/);
  assert.throws(() => parseChecksumText("bad line\n"), /invalid SHA256SUMS/);
  assert.throws(
    () => parseChecksumText(`${"a".repeat(64)}  SHA256SUMS\n`),
    /cannot checksum itself/,
  );
  assert.throws(
    () => parseChecksumText(`${"a".repeat(64)}  same\n${"b".repeat(64)}  same\n`),
    /duplicate/,
  );
});

test("release manifest and receipt bind source, archive, evaluation, and inputs", () => {
  const release = createReleaseManifest({
    sourceCommit: commit,
    sourceTree: tree,
    evaluatedInputs,
    evaluatedInputsFile: record("evaluated-inputs.json"),
    evaluationFile: record("docs/M5-EVALUATION.json"),
    archiveFile: record(RELEASE_ARCHIVE_NAME),
  });
  assert.equal(release.source.commit, commit);
  assert.equal(release.evaluatedInputs.digest, evaluatedInputs.evaluatedInputsDigest);
  assert.match(release.releaseDigest, /^[0-9a-f]{64}$/);
  const evaluation = {
    runs: {
      specialistContainment: { status: "victory" },
      engineerSeal: { reason: "power_exhausted" },
    },
  } as unknown as M5Evaluation;
  const receipt = releaseReceiptMarkdown(release, evaluation);
  assert.match(receipt, new RegExp(commit));
  assert.match(receipt, /power_exhausted/);
  assert.match(receipt, /same bytes/);
  assert.throws(
    () => createReleaseManifest({
      sourceCommit: "short",
      sourceTree: tree,
      evaluatedInputs,
      evaluatedInputsFile: record("evaluated-inputs.json"),
      evaluationFile: record("docs/M5-EVALUATION.json"),
      archiveFile: record(RELEASE_ARCHIVE_NAME),
    }),
    /full SHA-1/,
  );
  assert.throws(
    () => createReleaseManifest({
      sourceCommit: commit,
      sourceTree: "short",
      evaluatedInputs,
      evaluatedInputsFile: record("evaluated-inputs.json"),
      evaluationFile: record("docs/M5-EVALUATION.json"),
      archiveFile: record(RELEASE_ARCHIVE_NAME),
    }),
    /full SHA-1/,
  );
  assert.throws(
    () => createReleaseManifest({
      sourceCommit: "d".repeat(40),
      sourceTree: tree,
      evaluatedInputs,
      evaluatedInputsFile: record("evaluated-inputs.json"),
      evaluationFile: record("docs/M5-EVALUATION.json"),
      archiveFile: record(RELEASE_ARCHIVE_NAME),
    }),
    /source commit differs/,
  );
  assert.throws(
    () => createReleaseManifest({
      sourceCommit: commit,
      sourceTree: "d".repeat(40),
      evaluatedInputs,
      evaluatedInputsFile: record("evaluated-inputs.json"),
      evaluationFile: record("docs/M5-EVALUATION.json"),
      archiveFile: record(RELEASE_ARCHIVE_NAME),
    }),
    /source tree differs/,
  );
});

test("release file records hash exact bytes", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-release-record-"));
  try {
    writeFileSync(join(directory, "file.txt"), "release-bytes\n");
    const first = releaseFileRecord(directory, "file.txt");
    const second = releaseFileRecord(directory, "file.txt");
    assert.deepEqual(second, first);
    assert.equal(first.bytes, 14);
    assert.match(first.sha256, /^[0-9a-f]{64}$/);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});


test("release digest changes when any bound release record changes", () => {
  const base = createReleaseManifest({
    sourceCommit: commit,
    sourceTree: tree,
    evaluatedInputs,
    evaluatedInputsFile: record("evaluated-inputs.json"),
    evaluationFile: record("docs/M5-EVALUATION.json"),
    archiveFile: record(RELEASE_ARCHIVE_NAME),
  });
  const changed = createReleaseManifest({
    sourceCommit: commit,
    sourceTree: tree,
    evaluatedInputs,
    evaluatedInputsFile: record("evaluated-inputs.json"),
    evaluationFile: record("docs/M5-EVALUATION.json", "d".repeat(64), 2),
    archiveFile: record(RELEASE_ARCHIVE_NAME),
  });
  assert.notEqual(changed.releaseDigest, base.releaseDigest);
});
