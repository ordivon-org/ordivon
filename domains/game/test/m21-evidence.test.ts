import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

interface LiveRun {
  mode: "codex" | "hermes" | "codex-hermes";
  sourceRevision: string;
  providerCallCounts: { codex: number; hermes: number };
  providerCallCount: number;
  humanCorrections: number;
  originalTranscriptLoaded: boolean;
  hiddenFixtureFallback: boolean;
  allProviderOutputsStructured: boolean;
  allDecisionsAdmitted: boolean;
  allEffectsVerified: boolean;
  rawArtifact: { jobId: string; artifactId: string; digest: string };
  terminal: {
    missionStatus: "victory" | "failure";
    missionReason: string;
    turn: number;
    worldDigest: string;
    score: number;
  };
  evidence: {
    worldEvents: number;
    effects: number;
    dispatches: number;
    observations: number;
    replayVerified: boolean;
    replayDigest: string;
    maximumContextBytes: number;
    reportedEstimatedCostUsd: number | null;
  };
  comparisonToM2: {
    previousMissionStatus: "victory" | "failure";
    previousTurn: number;
    previousScore: number;
    verifiedVictoryGained: boolean;
    trajectoryImproved: boolean;
    scoreDelta: number;
  };
}

interface Evaluation {
  sourceRevision: string;
  contextSchemaVersion: number;
  implementation: Record<string, boolean | number>;
  automatedEvidence: {
    tests: number;
    testsPassed: number;
    frozenFixture: { missionStatus: string; turn: number; terminalDigest: string };
    rankOneSemanticBaseline: {
      usesFixture: boolean;
      usesProvider: boolean;
      missionStatus: string;
      turn: number;
      terminalDigest: string;
    };
    fullSearchPrototype: { accepted: boolean; reason: string };
  };
  liveRuns: LiveRun[];
  acceptance: Record<string, boolean>;
  conclusions: {
    realVictories: string[];
    remainingFailureModes: Record<string, string>;
  };
}

test("M2.1 evidence proves real victory without hiding Hermes-only failure", () => {
  const evaluation = JSON.parse(readFileSync("docs/M21-EVALUATION.json", "utf8")) as Evaluation;
  assert.equal(evaluation.sourceRevision, "6be4aa6b8fe88630d6c3659a06de95e0f20c241a");
  assert.equal(evaluation.contextSchemaVersion, 2);
  assert.equal(evaluation.implementation.worldRulesChanged, false);
  assert.equal(evaluation.implementation.providerModelChanged, false);
  assert.equal(evaluation.implementation.hiddenPolicyOverrideAdded, false);
  assert.equal(evaluation.implementation.fullStateSearchUsedAtRuntime, false);
  assert.equal(evaluation.implementation.strategicRankAdvisoryOnly, true);
  assert.equal(evaluation.automatedEvidence.tests, 99);
  assert.equal(evaluation.automatedEvidence.testsPassed, 99);
  assert.deepEqual(evaluation.automatedEvidence.frozenFixture, {
    missionStatus: "victory",
    turn: 25,
    terminalDigest: "41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2",
  });
  assert.equal(evaluation.automatedEvidence.rankOneSemanticBaseline.usesFixture, false);
  assert.equal(evaluation.automatedEvidence.rankOneSemanticBaseline.usesProvider, false);
  assert.equal(evaluation.automatedEvidence.rankOneSemanticBaseline.missionStatus, "victory");
  assert.equal(evaluation.automatedEvidence.rankOneSemanticBaseline.turn, 26);
  assert.equal(evaluation.automatedEvidence.fullSearchPrototype.accepted, false);

  assert.deepEqual(evaluation.liveRuns.map((run) => run.mode), ["codex", "hermes", "codex-hermes"]);
  for (const run of evaluation.liveRuns) {
    assert.equal(run.sourceRevision, evaluation.sourceRevision, run.mode);
    assert.equal(run.providerCallCount, run.providerCallCounts.codex + run.providerCallCounts.hermes, run.mode);
    assert.equal(run.humanCorrections, 0, run.mode);
    assert.equal(run.originalTranscriptLoaded, false, run.mode);
    assert.equal(run.hiddenFixtureFallback, false, run.mode);
    assert.equal(run.allProviderOutputsStructured, true, run.mode);
    assert.equal(run.allDecisionsAdmitted, true, run.mode);
    assert.equal(run.allEffectsVerified, true, run.mode);
    assert.match(run.rawArtifact.jobId, /^job-/);
    assert.match(run.rawArtifact.artifactId, /\.stdout$/);
    assert.match(run.rawArtifact.digest, /^sha256:[a-f0-9]{64}$/);
    assert.equal(run.evidence.worldEvents, run.evidence.effects, run.mode);
    assert.equal(run.evidence.worldEvents, run.evidence.dispatches, run.mode);
    assert.equal(run.evidence.worldEvents, run.evidence.observations, run.mode);
    assert.equal(run.evidence.replayVerified, true, run.mode);
    assert.equal(run.evidence.replayDigest, run.terminal.worldDigest, run.mode);
    assert.ok(run.evidence.maximumContextBytes <= 16 * 1024, run.mode);
    assert.ok(run.comparisonToM2.scoreDelta > 0, run.mode);
    assert.equal(run.comparisonToM2.trajectoryImproved, true, run.mode);
  }

  const codex = evaluation.liveRuns.find((run) => run.mode === "codex");
  const hermes = evaluation.liveRuns.find((run) => run.mode === "hermes");
  const switched = evaluation.liveRuns.find((run) => run.mode === "codex-hermes");
  assert.ok(codex && hermes && switched);
  assert.equal(codex.terminal.missionStatus, "victory");
  assert.equal(codex.terminal.missionReason, "rescue_signal_verified");
  assert.equal(codex.comparisonToM2.verifiedVictoryGained, true);
  assert.equal(codex.evidence.reportedEstimatedCostUsd, null);
  assert.equal(hermes.terminal.missionStatus, "failure");
  assert.equal(hermes.terminal.missionReason, "engineer_incapacitated");
  assert.equal(hermes.comparisonToM2.verifiedVictoryGained, false);
  assert.ok((hermes.evidence.reportedEstimatedCostUsd ?? 0) > 0);
  assert.equal(switched.terminal.missionStatus, "victory");
  assert.equal(switched.providerCallCounts.codex, 5);
  assert.equal(switched.providerCallCounts.hermes, 5);
  assert.equal(switched.comparisonToM2.verifiedVictoryGained, true);
  assert.deepEqual(evaluation.conclusions.realVictories, ["codex", "codex-hermes"]);
  const hermesFailure = evaluation.conclusions.remainingFailureModes.hermes;
  assert.ok(hermesFailure);
  assert.match(hermesFailure, /life support|oxygen/i);
  assert.ok(Object.values(evaluation.acceptance).every(Boolean));
});
