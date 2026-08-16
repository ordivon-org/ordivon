import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const reset = readFileSync(new URL("../docs/GAME_CORE_RESEARCH_RESET.md", import.meta.url), "utf8");
const space = readFileSync(new URL("../docs/GAME_CORE_DIRECTION_SPACE.md", import.meta.url), "utf8");
const findings = readFileSync(new URL("../docs/GAME_CORE_EXPERIMENT_FINDINGS.md", import.meta.url), "utf8");
const casefile = readFileSync(new URL("../docs/GAME_CORE_EXPERIMENT_CASEFILE.md", import.meta.url), "utf8");
const model = readFileSync(new URL("../docs/DEVELOPMENT_MODEL.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const server = readFileSync(new URL("../src/server.ts", import.meta.url), "utf8");
const lab = readFileSync(new URL("../web-lab/app.js", import.meta.url), "utf8");
const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

test("Game Core research preserves canonical G0-G8 meanings instead of inventing research stages", () => {
  assert.match(reset, /^id: game\.core-research\.reset$/m);
  assert.match(reset, /G0 Define[\s\S]*G8 Release \/ operate \/ learn/);
  assert.match(reset, /Research rounds are search methods/);
  assert.match(reset, /never redefine G0–G8/);
  assert.match(model, /A research round is a \*\*search method\*\*\. It is not a product phase\./);
  assert.match(readme, /No new Ordivon Game product has been selected/);
  assert.match(readme, /Canonical G0–G8 meanings remain exclusively/);
  assert.match(authority, /only authority for G0–G8 product-stage semantics/);
  assert.match(agents, /GAME_CORE_RESEARCH_RESET\.md/);
  assert.doesNotMatch(readme, /G6 Casefile candidate active/);
});

test("direction space keeps materially different research lenses without declaring a winner", () => {
  for (const concept of ["Station Zero", "Casefile", "Last Light", "Echo Hunt", "Living Outpost", "Creative Social World"]) {
    assert.match(space, new RegExp(concept));
  }
  assert.match(space, /These are not candidates competing for product selection/);
  assert.match(space, /Agency topology/);
  assert.match(space, /Consequence type/);
  assert.match(space, /Persistence horizon/);
  assert.match(space, /Player-value mode/);
  assert.match(space, /Agent participation mode/);
  assert.match(findings, /There is \*\*no product winner\*\*/);
});

test("Casefile is retained as an epistemic treatment rather than a G-stage product", () => {
  assert.match(casefile, /^id: game\.core-research\.experiment-casefile$/m);
  assert.match(casefile, /not a product winner and not a G6 candidate/);
  assert.match(casefile, /Product stage:\s+none assigned/);
  assert.match(casefile, /World truth from what subjects observe, believe, say/);
  assert.match(casefile, /do not select Casefile as a product|not a selected product/);
});

test("Concept Lab remains disposable research scaffolding isolated from Station Zero routes", () => {
  assert.match(server, /defaultLabWebRoot/);
  assert.match(server, /"\/lab"/);
  assert.match(server, /labStaticFiles/);
  assert.match(lab, /Casefile/);
  assert.match(lab, /Last Light/);
  assert.match(lab, /Echo Hunt/);
  assert.match(lab, /location\.href='\/v3'/);
  assert.equal(packageJson.scripts["e2e:lab"], "node scripts/e2e-game-core-concept-lab.ts");
  assert.match(packageJson.scripts.webcheck, /web-lab\/\*\.js/);
});
