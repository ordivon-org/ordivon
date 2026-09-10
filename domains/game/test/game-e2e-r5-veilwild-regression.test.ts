import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const ROOT = "experiments/veilwild-r1";
const INVENTORY_PATH = `${ROOT}/round4/A17/A17_R4A_SELECTED_RUNTIME_INVENTORY.json`;
const GODOT_ROOT = `${ROOT}/godot`;

function sha256(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function json(path: string): any {
  return JSON.parse(readFileSync(path, "utf8"));
}

function filesBelow(root: string, suffix: string): string[] {
  const result: string[] = [];
  for (const name of readdirSync(root)) {
    const path = join(root, name);
    if (statSync(path).isDirectory()) result.push(...filesBelow(path, suffix));
    else if (path.endsWith(suffix)) result.push(path);
  }
  return result.sort();
}

test("R5 preserves exact Veilwild R4 selected-runtime byte identity", () => {
  const inventory = json(INVENTORY_PATH);
  assert.equal(
    sha256(`${GODOT_ROOT}/project.godot`),
    inventory.sourceIdentity.projectGodotSha256,
  );
  assert.equal(
    sha256(`${GODOT_ROOT}/main.tscn`),
    inventory.sourceIdentity.mainSceneSha256,
  );
  assert.equal(
    sha256(`${GODOT_ROOT}/export_presets.cfg`),
    inventory.sourceIdentity.exportPresetSha256,
  );

  for (const artifact of inventory.selectedArtifacts) {
    assert.equal(
      sha256(artifact.candidateRepoPath),
      artifact.runtimeArtifactSha256,
      `${artifact.artifactId} selected-runtime bytes drifted`,
    );
    assert.equal(artifact.byteIdentity, "EXACT", artifact.artifactId);
  }
  for (const companion of inventory.sourceFixedCompanions ?? []) {
    assert.equal(
      sha256(companion.candidateRepoPath),
      companion.sha256,
      `${companion.candidateRepoPath} source-fixed companion drifted`,
    );
  }
  for (const glue of inventory.a17IntegrationGlue) {
    assert.equal(sha256(glue.path), glue.sha256, `${glue.path} integration glue drifted`);
  }
});

test("R5 preserves the R4 Godot scene identity falsifier", () => {
  const scenes = filesBelow(GODOT_ROOT, ".tscn");
  let nodes = 0;
  const missing: string[] = [];
  for (const scene of scenes) {
    const lines = readFileSync(scene, "utf8").split(/\r?\n/);
    lines.forEach((line, index) => {
      if (!line.startsWith("[node ")) return;
      nodes += 1;
      if (!line.includes("unique_id=")) missing.push(`${scene}:${index + 1}`);
    });
  }
  assert.equal(scenes.length, 9, "R4 selected project scene count drifted");
  assert.equal(nodes, 71, "R4 selected project node count drifted");
  assert.deepEqual(missing, [], "a selected Godot node lost its unique_id");
});

test("R5 cannot launder R4 technical evidence into candidate, rights, or Human standing", () => {
  const inventory = json(INVENTORY_PATH);
  const boundary = inventory.candidateBoundary;
  assert.equal(boundary.candidateId, null);
  assert.equal(boundary.buildId, null);
  assert.equal(boundary.buildArtifactId, null);
  assert.equal(boundary.nominationStatus, "NOT_YET_NOMINATED");
  assert.equal(boundary.rightsStanding, "INCONCLUSIVE");
  assert.equal(boundary.humanClaims, "UNKNOWN");
  assert.equal(inventory.mechanicalAcceptance.hiddenTargetCoordinatesExposed, false);
});

test("R5 preserves telemetry-as-transport and Human UNKNOWN guards", () => {
  const f22 = json(`${ROOT}/contracts/F22_TELEMETRY_EVIDENCE_CONTRACT_R1.json`);
  const f24 = json(`${ROOT}/contracts/F24_PLAYER_EVIDENCE_CONTRACT_R1.json`);

  for (const [claim, standing] of Object.entries(f22.humanClaims ?? {})) {
    assert.equal(standing, "UNKNOWN", `F22 Human claim ${claim} was upgraded without Human evidence`);
  }
  for (const [claim, standing] of Object.entries(f24.humanClaimsBeforeExecution ?? {})) {
    assert.equal(standing, "UNKNOWN", `F24 Human claim ${claim} was upgraded before execution`);
  }

  const guards = new Set(f22.privacyAndHumanBoundary?.humanInferenceGuards ?? []);
  assert.ok(guards.has("detection_opportunity != Human_detected"));
  assert.ok(guards.has("observation_committed != Human_comprehension"));
  assert.ok(guards.has("mechanical_telemetry != Human_comfort"));

  const event = f22.eventTypes?.find?.((item: any) => item.eventType === "reacquisition_opportunity");
  if (event) {
    assert.match(String(event.semanticMeaning ?? ""), /mechanical|does NOT prove|not Human/i);
  }
});
