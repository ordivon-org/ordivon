import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const development = readFileSync(new URL("../docs/DEVELOPMENT_MODEL.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const frontHalf = readFileSync(new URL("../docs/GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md", import.meta.url), "utf8");

test("Game development model keeps canonical G0-G8 stages while exposing deeper development standing", () => {
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


test("product discovery before G0 is external-reference-first without creating new G-stages", () => {
  assert.match(frontHalf, /canonical-front-half-profile/);
  assert.match(frontHalf, /success-universe census without feasibility filtering/);
  assert.match(frontHalf, /archetype\/reference coverage sufficient for the current decision/);
  assert.match(frontHalf, /Reference learning\s+<->\s+Product theses\s+<->\s+Throwaway prototypes/);
  assert.match(frontHalf, /claim-specific evidence/i);
  assert.match(frontHalf, /Structured Decision Making \/ Value of Information/);
  assert.match(frontHalf, /Human participant evidence when the claim requires it/i);
  assert.match(frontHalf, /R4 controlled comparison\/variation/);
  assert.match(frontHalf, /canonical G0 Game Definition only when a specific game is justified/);
  assert.match(frontHalf, /Universe membership:[\s\S]*not filtered[\s\S]*team size[\s\S]*expected reproduction cost/i);
  assert.match(frontHalf, /R0-R4 are.*profile activities\/lenses.*not mandatory sequential gates and not additional G-stages/is);
  assert.match(frontHalf, /Innovation is not the required input/);
  assert.match(frontHalf, /They may not answer:[\s\S]*what product to make/);
  assert.match(development, /Product selection now begins with the external-reference front-half profile/);
  assert.match(authority, /GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE\.md.*product-discovery profile before G0/s);
  assert.match(readme, /GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE\.md/);
});

test("classification separates conventional game form, Production Agents, and Runtime Agents", () => {
  assert.match(development, /Conventional Form Profile/);
  assert.match(development, /Production Agent Profile/);
  assert.match(development, /Runtime Agent Participation Profile/);
  assert.match(development, /The \*\*Form Profile determines the conventional game and its baseline production burden\*\*/);
  assert.match(development, /The \*\*Production Agent Profile measures how Agent tooling changes the reachable production frontier\*\*/);
  assert.match(development, /The \*\*Runtime Agent Participation Profile determines any extra shipped cognition\/authority\/feedback burden\*\*/);
  assert.match(development, /AgentBuiltGame != AgentGame/);
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
  assert.match(authority, /DEVELOPMENT_MODEL\.md.*G0–G8 commitment\/stage projection/s);
  assert.match(development, /ISO\/IEC\/IEEE 12207:2026/);
  assert.match(development, /not a replacement for ISO\/IEC\/IEEE 12207 lifecycle processes/);
  assert.match(development, /does \*\*not\*\* reclassify, redesign, balance, register, or replace Station Zero/);
  assert.match(development, /Station Zero-specific Plans, Turns, Commander forms, factions, tactical Zones, sealed enemy Plans and exact Host execution shape do not survive/);
});
