import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const corpus = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R1_R17.md", import.meta.url),
  "utf8",
);
const r18 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R18.md", import.meta.url),
  "utf8",
);
const r19 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R19.md", import.meta.url),
  "utf8",
);
const r20 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R20.md", import.meta.url),
  "utf8",
);
const map = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_MAP.md", import.meta.url),
  "utf8",
);
const continuation = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_CONTINUATION.md", import.meta.url),
  "utf8",
);
const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");

test("Game foundations corpus preserves all seventeen completed pre-R18 research rounds", () => {
  for (let round = 1; round <= 17; round += 1) {
    assert.match(corpus, new RegExp(`R${round} \\u2014|R${round} —`));
  }
  assert.match(corpus, /AI Game != Agent World/);
  assert.match(corpus, /No new Ordivon Game product has been selected by R1–R17/);
  assert.match(corpus, /A research round is a search method\. It is not a product phase\./);
});

test("R18 preserves motivational distinctions without selecting a product", () => {
  assert.match(r18, /Need \/ Value \/ Desire/);
  assert.match(r18, /Scalarize late\./);
  assert.match(r18, /Goal proposal != Goal adoption/);
  assert.match(r18, /PlayableMotivation/);
  assert.match(r18, /Generative Persona != Autonomous Agent requirement/);
  assert.match(r18, /No product is selected by R18\./);
});

test("R19 preserves strategic distinctions without equating equilibrium or stronger opponents with product value", () => {
  assert.match(r19, /StrategicInterdependence\(i, j\)/);
  assert.match(r19, /StrategicDepth != SearchDepth/);
  assert.match(r19, /Coordination != Cooperation/);
  assert.match(r19, /Equilibrium != Product Value|Equilibrium != fun/);
  assert.match(r19, /PlayableStrategy/);
  assert.match(r19, /Soft negotiation \/ language proposal/);
  assert.match(r19, /No product is selected by R19\./);
});

test("R20 preserves creation, authorship, expression and generation boundaries without selecting a product", () => {
  assert.match(r20, /Authorial causality|AuthorialCausality/i);
  assert.match(r20, /Creative Contribution Topology|CreativeContributionTopology/);
  assert.match(r20, /PlayableCreation/);
  assert.match(r20, /PlayableExpression/);
  assert.match(r20, /Do not mistake generation for creativity or personalization for expression\./);
  assert.match(r20, /Authorship != Ownership/);
  assert.match(r20, /No product is selected by R20\./);
});

test("foundation navigation advances the exact post-R20 continuation frontier", () => {
  const frontier = /R21 — Embodiment, Control, Input, Skill, Affordance, Game Feel and Presence/;
  assert.match(map, frontier);
  assert.match(continuation, frontier);
  assert.match(continuation, /AI Game != Agent World/);
  assert.match(continuation, /Do not begin intentional new-product G0 merely because the corpus is large\./);
});

test("foundation research records are managed repository documentation", () => {
  for (const path of [
    "docs/GAME_FOUNDATIONS_RESEARCH_R1_R17.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_R18.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_R19.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_R20.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_MAP.md",
    "docs/GAME_FOUNDATIONS_CONTINUATION.md",
  ]) {
    assert.match(project, new RegExp(path.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});
