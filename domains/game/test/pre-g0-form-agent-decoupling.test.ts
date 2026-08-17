import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const doc = readFileSync(new URL("../docs/GAME_PRE_G0_FORM_AGENT_ROLE_DECOUPLING.md", import.meta.url), "utf8");
const development = readFileSync(new URL("../docs/DEVELOPMENT_MODEL.md", import.meta.url), "utf8");
const ds0 = readFileSync(new URL("../docs/GAME_PRE_G0_DIRECTION_SEARCH.md", import.meta.url), "utf8");
const ds1 = readFileSync(new URL("../docs/GAME_PRE_G0_DS1_CHEAP_FALSIFIERS.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const evidence = JSON.parse(readFileSync(new URL("../evidence/pre-g0/form-agent-role-space.json", import.meta.url), "utf8")) as {
  kind: string;
  productSelected: boolean;
  g0Entered: boolean;
  foundationReopenConditionTriggered: boolean;
  factorization: string[];
  laws: string[];
  gameFormFamilies: Array<{ id: string; name: string }>;
  productionAgentRoles: Array<{ id: string; name: string }>;
  runtimeSystemRoles: Array<{ id: string; name: string }>;
  worldAgentRoles: Array<{ id: string; name: string }>;
  retiredSearchImplication: string;
  nextFrontier: string;
};

test("Pre-G0 search factorizes GameForm from production and runtime Agent roles", () => {
  assert.deepEqual(evidence.factorization, ["GameFormProfile", "ProductionAgentProfile", "RuntimeAgentProfile"]);
  assert.ok(evidence.laws.includes("AgentBuiltGame != AgentGame"));
  assert.ok(evidence.laws.includes("ProductionAgentNeed != RuntimeAgentNeed"));
  assert.match(doc, /OrdivonGameCandidate[\s\S]*GameFormProfile[\s\S]*ProductionAgentProfile[\s\S]*RuntimeAgentProfile/);
  assert.match(doc, /Both Agent profiles may be empty/);
});

test("traditional GameForm coverage is materially broader than the old D-series basis", () => {
  assert.equal(evidence.gameFormFamilies.length, 22);
  for (const id of ["F01", "F03", "F04", "F05", "F06", "F15", "F18", "F21", "F22"]) {
    assert.ok(evidence.gameFormFamilies.some((form) => form.id === id), `missing ${id}`);
  }
  assert.match(doc, /precision platforming, racing, sports, rhythm, fighting, broad shooter\/action/);
});

test("Agent roles distinguish production, runtime-system and world-subject loci", () => {
  assert.equal(evidence.productionAgentRoles.length, 12);
  assert.equal(evidence.runtimeSystemRoles.length, 7);
  assert.equal(evidence.worldAgentRoles.length, 10);
  assert.match(doc, /Layer P — Production Agents/);
  assert.match(doc, /Layer S — Runtime Game-System Intelligence/);
  assert.match(doc, /Layer W — World \/ Subject Agents/);
  assert.match(doc, /SystemIntelligence != WorldAgent/);
});

test("development model no longer assumes a shipped Agent game", () => {
  assert.match(development, /title: Ordivon Game Development Model/);
  assert.match(development, /Production Agent Profile/);
  assert.match(development, /Runtime Agent Participation Profile/);
  assert.match(development, /AgentBuiltGame != AgentGame/);
  assert.match(development, /if runtime Agent participation is claimed/);
});

test("DS0 and DS1 remain evidence but no longer own current search priority", () => {
  assert.match(ds0, /FORM_AGENT_ROLE_DECOUPLING\.md/);
  assert.match(ds1, /survivor portfolio no longer determines the next research budget/);
  assert.match(doc, /structural survivors[\s\S]*automatically receive next playable budget/);
  assert.equal(evidence.retiredSearchImplication, "DS1 structural survivors automatically receive playable budget before untested forms");
});

test("navigation and lifecycle boundaries expose the new authority", () => {
  assert.match(readme, /GAME_PRE_G0_FORM_AGENT_ROLE_DECOUPLING\.md/);
  assert.match(agents, /GAME_PRE_G0_FORM_AGENT_ROLE_DECOUPLING\.md/);
  assert.equal(evidence.productSelected, false);
  assert.equal(evidence.g0Entered, false);
  assert.equal(evidence.foundationReopenConditionTriggered, false);
  assert.equal(evidence.nextFrontier, "Pre-G0 Form Search — broad traditional GameForm portfolio");
});
