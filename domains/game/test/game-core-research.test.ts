import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const reset = readFileSync(new URL("../docs/GAME_CORE_RESEARCH_RESET.md", import.meta.url), "utf8");
const space = readFileSync(new URL("../docs/GAME_CORE_DIRECTION_SPACE.md", import.meta.url), "utf8");
const findings = readFileSync(new URL("../docs/GAME_CORE_EXPERIMENT_FINDINGS.md", import.meta.url), "utf8");
const casefile = readFileSync(new URL("../docs/GAME_CORE_EXPERIMENT_CASEFILE.md", import.meta.url), "utf8");
const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

test("current Game Core frontier is creative-open and process models are optional skills", () => {
  assert.match(reset, /Current Game direction is \*\*creative-open\*\*/);
  assert.match(reset, /any game type, mechanic, rule, representation, control scheme, content structure or interaction may be combined experimentally/);
  assert.match(reset, /D1-D8, G0-G8.*optional repository-local Skills/);
  assert.match(reset, /R1-R29.*research knowledge rather than creative admission law/);
});

test("direction space and findings remain reusable research without selecting a winner", () => {
  for (const concept of ["Station Zero", "Casefile", "Last Light", "Echo Hunt", "Living Outpost", "Creative Social World"]) assert.match(space, new RegExp(concept));
  assert.match(findings, /There is \*\*no product winner\*\*/);
});

test("Casefile remains retained experiment rather than privileged product ancestor", () => {
  assert.match(casefile, /not a product winner|not a selected product/);
});

test("research surfaces remain executable apparatus", () => {
  assert.equal(pkg.scripts["e2e:lab"], "node experiments/concept-lab/scripts/e2e-game-core-concept-lab.ts");
});
