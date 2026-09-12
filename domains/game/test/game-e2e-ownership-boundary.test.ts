import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const RETIRED_BIG_GAME_PRODUCT_PATHS = [
  "src/model.ts",
  "src/world.ts",
  "src/facts.ts",
  "src/scenario.ts",
  "src/scenario-cases.ts",
  "src/run.ts",
  "src/storage.ts",
  "src/scoring.ts",
  "src/registry.ts",
  "src/team",
  "src/mission-control",
  "src/replay",
  "src/deployment",
  "src/comparison",
  "src/integration",
];

function files(root: string): string[] {
  if (!existsSync(root)) return [];
  const out: string[] = [];
  for (const name of readdirSync(root)) {
    const path = join(root, name);
    if (statSync(path).isDirectory()) out.push(...files(path));
    else out.push(path);
  }
  return out;
}

test("Big Game does not own Station Zero v2 runtime implementation", () => {
  assert.equal(existsSync("products/station-zero-v2/src/world.ts"), true);
  assert.equal(existsSync("products/station-zero-v2/src/team/engine.ts"), true);
  for (const path of RETIRED_BIG_GAME_PRODUCT_PATHS) {
    assert.equal(existsSync(path), false, `${path} must not return to Big Game root ownership`);
  }
});

test("research apparatus is enclosed under experiments and does not depend on Station Zero v2 product implementation", () => {
  assert.equal(existsSync("src/station-zero-v3"), false);
  assert.equal(existsSync("src/casefile"), false);
  assert.equal(existsSync("web-v3"), false);
  assert.equal(existsSync("web-casefile"), false);
  assert.equal(existsSync("web-lab"), false);
  assert.equal(existsSync("web-pre-g0"), false);
  assert.equal(existsSync("experiments/station-zero-v3/src/index.ts"), true);
  assert.equal(existsSync("experiments/casefile/src/index.ts"), true);
  const offenders = ["experiments/station-zero-v3/src", "experiments/casefile/src"]
    .flatMap(files)
    .filter((path) => /\.(?:ts|js)$/.test(path))
    .filter((path) => readFileSync(path, "utf8").includes("products/station-zero-v2"));
  assert.deepEqual(offenders, []);
});

test("canonical ownership authority rejects a generic Big Game framework", () => {
  const boundary = readFileSync("docs/GAME_E2E_OWNERSHIP_BOUNDARY.md", "utf8");
  assert.match(boundary, /not.*reusable Game Framework/i);
  assert.match(boundary, /at least two materially different real games/i);
  assert.match(boundary, /A future game is allowed to use none of those mechanisms/);
});
