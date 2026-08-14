import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const development = readFileSync(new URL("../docs/DEVELOPMENT_MODEL.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");

test("Agent game development model keeps normal game development as the outer lifecycle", () => {
  for (const stage of [
    "G0 — Define",
    "G1 — Preproduction / core design",
    "G2 — Kernel / graybox prototype",
    "G3 — Playable prototype",
    "G4 — Vertical Slice",
    "G5 — Production / content expansion",
    "G6 — Alpha / content-complete validation",
    "G7 — Beta / polish / release candidate",
    "G8 — Release / operate / learn",
  ]) assert.match(development, new RegExp(stage.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));

  assert.match(development, /A research round is a \*\*search method\*\*\. It is not a product phase\./);
  assert.match(agents, /A research series is a search method inside a development stage; it is never the product lifecycle itself\./);
});

test("classification separates conventional game form from Agent participation", () => {
  assert.match(development, /Conventional Form Profile/);
  assert.match(development, /Agent Participation Profile/);
  assert.match(development, /The \*\*Form Profile determines the normal game-production burden\*\*/);
  assert.match(development, /The \*\*Agent Participation Profile determines the extra cognition\/authority\/feedback burden\*\*/);
});

test("Agentic Consequence Loop preserves World authority and allows cheaper cognition tiers", () => {
  assert.match(development, /OBSERVE\s*\n→ COGNIZE\s*\n→ DECIDE\s*\n→ ADMIT\s*\n→ RESOLVE\s*\n→ FEEDBACK\s*\n→ ADAPT/);
  assert.match(development, /Cognition.*deterministic policy, a model, a human, or a hierarchy/s);
  assert.match(development, /If the Agent mostly adds latency, cost and prose while the trajectory is equivalent, shrink it to the cheaper mechanism\./);
});

test("Game and Studio keep separate production authority", () => {
  assert.match(development, /GAME[\s\S]*owns gameplay meaning and runtime need/);
  assert.match(development, /STUDIO[\s\S]*owns medium-specific editable expression and production/);
  assert.match(development, /Do \*\*not\*\* introduce a cross-repository schema until repeated real productions force one\./);
  assert.match(development, /A polished Output never becomes authoritative game-rule truth\./);
});

test("development model retains nested product/research roles and scoped learning", () => {
  assert.match(development, /ordinary game stages only/);
  assert.match(development, /Agent-first creative loop as the whole lifecycle/);
  assert.match(development, /reachable future space[\s\S]*policy-accessible future space[\s\S]*model-realized future space/);
  assert.match(development, /one trajectory \/ ablation[\s\S]*game-medium prior candidate[\s\S]*durable prior candidate/);
  assert.match(development, /Studio activation follows development stage/);
});

test("development model is canonical navigation but does not register or redesign Station Zero", () => {
  assert.match(readme, /docs\/DEVELOPMENT_MODEL\.md/);
  const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
  assert.match(project, /docs\/DEVELOPMENT_MODEL\.md/);
  assert.match(authority, /DEVELOPMENT_MODEL\.md.*cross-game development process/s);
  assert.match(development, /does \*\*not\*\* reclassify, redesign, balance, register, or replace Station Zero/);
  assert.match(development, /Station Zero-specific Plans, Turns, Commander forms, factions, tactical Zones, sealed enemy Plans and exact Host execution shape do not survive/);
});
