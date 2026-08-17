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
const r21 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R21.md", import.meta.url),
  "utf8",
);
const r22 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R22.md", import.meta.url),
  "utf8",
);
const r23 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R23.md", import.meta.url),
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

test("R21 preserves control, agency, embodiment and affordance boundaries without selecting a product", () => {
  assert.match(r21, /Intent != Input != Command != Action != Outcome/);
  assert.match(r21, /ActionCausality/);
  assert.match(r21, /ControlLocus/);
  assert.match(r21, /IntentFidelity/);
  assert.match(r21, /ControlContributionTopology/);
  assert.match(r21, /PlayableControl/);
  assert.match(r21, /PlayableEmbodiment/);
  assert.match(r21, /Control != SenseOfAgency/);
  assert.match(r21, /Affordance != Capability != Legality/);
  assert.match(r21, /No product is selected by R21\./);
});

test("R22 preserves uncertainty, risk, luck and fairness boundaries without selecting a product", () => {
  assert.match(r22, /Uncertainty != Randomness != Unpredictability/);
  assert.match(r22, /DecisionQuality != OutcomeQuality/);
  assert.match(r22, /UncertaintyTopology/);
  assert.match(r22, /OutcomeContributionTopology/);
  assert.match(r22, /DistributionalAgency/);
  assert.match(r22, /PlayableUncertainty/);
  assert.match(r22, /PlayableRisk/);
  assert.match(r22, /Fairness != Balance/);
  assert.match(r22, /SampledOutput/);
  assert.match(r22, /No product is selected by R22\./);
});

test("R23 preserves temporal-frame, ordering, concurrency and reversibility boundaries without selecting a product", () => {
  assert.match(r23, /ClockOrder != CausalOrder/);
  assert.match(r23, /Simultaneity != Concurrency/);
  assert.match(r23, /Turn != Tick != Phase/);
  assert.match(r23, /Tempo != Rhythm != Pacing/);
  assert.match(r23, /TemporalCausality/);
  assert.match(r23, /TemporalAgency/);
  assert.match(r23, /PlayableTemporality/);
  assert.match(r23, /Persistence != Continuous Computation|Persistence != ContinuousComputation/);
  assert.match(r23, /Replay != Undo != StateRestore != InWorldRewind/);
  assert.match(r23, /WorldStateReversal/);
  assert.match(r23, /No product is selected by R23\./);
});

test("foundation navigation advances the exact post-R23 continuation frontier", () => {
  const frontier = /R24 — Identity, Character, Role, Persona, Self, Status, Reputation, Continuity and Transformation/;
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
    "docs/GAME_FOUNDATIONS_RESEARCH_R21.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_R22.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_R23.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_MAP.md",
    "docs/GAME_FOUNDATIONS_CONTINUATION.md",
  ]) {
    assert.match(project, new RegExp(path.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});
