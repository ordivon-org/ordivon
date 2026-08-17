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
const r24 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R24.md", import.meta.url),
  "utf8",
);
const r25 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R25.md", import.meta.url),
  "utf8",
);
const r26 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R26.md", import.meta.url),
  "utf8",
);
const r27 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R27.md", import.meta.url),
  "utf8",
);
const r28 = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R28.md", import.meta.url),
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

test("R24 preserves identity, continuity, recognition and implementation boundaries without selecting a product", () => {
  assert.match(r24, /QualitativeSimilarity != NumericalIdentity|Numerical Identity != Qualitative Similarity/);
  assert.match(r24, /Memory != Identity/);
  assert.match(r24, /ContinuityProfile/);
  assert.match(r24, /IdentityAuthority/);
  assert.match(r24, /IdentityTopology/);
  assert.match(r24, /RecognitionTopology/);
  assert.match(r24, /IdentityCausality/);
  assert.match(r24, /SameModel != SameAgentIdentity/);
  assert.match(r24, /DifferentModel != IdentityBreak/);
  assert.match(r24, /PlayableIdentity/);
  assert.match(r24, /PlayableContinuity/);
  assert.match(r24, /No product is selected by R24\./);
});

test("R25 preserves relational-state, trust, intimacy, reciprocity and AI-boundary distinctions without selecting a product", () => {
  assert.match(r25, /Interaction != Relationship/);
  assert.match(r25, /Relationship != OneScalar/);
  assert.match(r25, /Mutuality != Symmetry != Reciprocity/);
  assert.match(r25, /Trust != Liking/);
  assert.match(r25, /Intimacy != InformationQuantity/);
  assert.match(r25, /RelationshipCausality/);
  assert.match(r25, /RelationshipTopology/);
  assert.match(r25, /RelationalAuthority/);
  assert.match(r25, /GeneratedWarmth != RelationshipHistory/);
  assert.match(r25, /HumanExperiencedRelation/);
  assert.match(r25, /PlayableRelationship/);
  assert.match(r25, /No product is selected by R25\./);
});



test("R27 preserves learning, memory, adaptation and self-model distinctions without selecting a product", () => {
  assert.match(r27, /PerformanceChange != Learning/);
  assert.match(r27, /Learning != Adaptation/);
  assert.match(r27, /Memory != Storage/);
  assert.match(r27, /BeliefRevision != InformationAcquisition/);
  assert.match(r27, /PersistentSubjectChange/);
  assert.match(r27, /LearningTargetTopology/);
  assert.match(r27, /UpdateAuthority/);
  assert.match(r27, /LearningCausality/);
  assert.match(r27, /LearningContract/);
  assert.match(r27, /PlayableLearning/);
  assert.match(r27, /ModelFineTuning != CharacterLearning by default/);
  assert.match(r27, /No product is selected by R27\./);
});



test("R28 preserves culture, convention, ritual, meaning, legitimacy and memory distinctions without selecting a product", () => {
  assert.match(r28, /Culture != Lore/);
  assert.match(r28, /Culture != Institution/);
  assert.match(r28, /Convention != Norm/);
  assert.match(r28, /RepeatedBehavior != Tradition/);
  assert.match(r28, /Routine != Ritual/);
  assert.match(r28, /Symbol != Meaning/);
  assert.match(r28, /SharedBelief != SharedMeaning/);
  assert.match(r28, /Legality != Legitimacy/);
  assert.match(r28, /History != CollectiveMemory/);
  assert.match(r28, /CulturalTransmission != ExactCopy/);
  assert.match(r28, /CulturalCausality/);
  assert.match(r28, /CulturalTransmissionTopology/);
  assert.match(r28, /LegitimacyTopology/);
  assert.match(r28, /PlayableCulture/);
  assert.match(r28, /PopulationPrompt \/ SharedWeights/);
  assert.match(r28, /No product is selected by R28\./);
});

test("foundation navigation advances the exact post-R28 synthesis frontier", () => {
  const frontier = /R29 — Whole-Corpus Synthesis, Redundancy Audit, Causal Closure and Foundation Falsification/;
  assert.match(map, frontier);
  assert.match(continuation, frontier);
  assert.match(continuation, /R29 should \*\*attack and compress\*\* the corpus rather than extend it/);
  assert.match(continuation, /Do not begin intentional new-product G0/);
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
    "docs/GAME_FOUNDATIONS_RESEARCH_R24.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_R25.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_R26.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_R27.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_R28.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_MAP.md",
    "docs/GAME_FOUNDATIONS_CONTINUATION.md",
  ]) {
    assert.match(project, new RegExp(path.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});


test("R26 preserves affective-process, regulation, expression and empathy distinctions without selecting a product", () => {
  assert.match(r26, /Affect != Emotion/);
  assert.match(r26, /Emotion != OneScalar/);
  assert.match(r26, /Valence != Value/);
  assert.match(r26, /Arousal != Motivation/);
  assert.match(r26, /ActionTendency != Action/);
  assert.match(r26, /Feeling != EmotionWhole/);
  assert.match(r26, /Mood != LongEmotion/);
  assert.match(r26, /Appraisal != GenericThought/);
  assert.match(r26, /EmotionRegulation != Suppression/);
  assert.match(r26, /Expression != InternalAffect/);
  assert.match(r26, /Expression != EmotionTruth/);
  assert.match(r26, /EmotionRecognition != EmotionAccess/);
  assert.match(r26, /Empathy != Contagion/);
  assert.match(r26, /Empathy != PerspectiveTaking/);
  assert.match(r26, /Empathy != Compassion/);
  assert.match(r26, /Empathy != Care/);
  assert.match(r26, /Emotion becomes gameplay when affective counterfactuals change meaningful futures/);
  assert.match(r26, /R26 does not select a product/);
});
