import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

interface LiveRun {
  mode: string;
  providerCalls: number;
  providerCallCounts: { codex: number; hermes: number };
  allProviderOutputsStructured: boolean;
  allDecisionsAdmitted: boolean;
  allEffectsVerified: boolean;
  humanCorrections: number;
  originalTranscriptLoaded: boolean;
  terminal: { missionStatus: string; worldDigest: string };
  evidence: {
    worldEvents: number;
    effects: number;
    dispatches: number;
    observations: number;
    replayVerified: boolean;
    replayDigest: string;
    maximumContextBytes: number;
  };
}

interface Evaluation {
  sourceRevision: string;
  acceptance: Record<string, boolean>;
  automatedEvidence: {
    fixtureBaseline: { missionStatus: string; terminalDigest: string };
    interruptionFaultPoints: string[];
    allInterruptionRunsConverged: boolean;
  };
  liveRuns: LiveRun[];
  conclusions: {
    m2HostVerticalPathPassed: boolean;
    providerInterchangeabilityPassed: boolean;
    realProviderVictoryObserved: boolean;
    strategyFollowUpIssue: number;
  };
}

test("M2 evaluation evidence is internally consistent and honest about strategy failure", () => {
  const evaluation = JSON.parse(readFileSync("docs/M2-EVALUATION.json", "utf8")) as Evaluation;
  assert.equal(evaluation.sourceRevision, "62fb6d00136baaa6f5c95293529377358aa12d66");
  assert.ok(Object.values(evaluation.acceptance).every(Boolean));
  assert.equal(evaluation.automatedEvidence.fixtureBaseline.missionStatus, "victory");
  assert.equal(
    evaluation.automatedEvidence.fixtureBaseline.terminalDigest,
    "41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2",
  );
  assert.equal(evaluation.automatedEvidence.interruptionFaultPoints.length, 7);
  assert.equal(evaluation.automatedEvidence.allInterruptionRunsConverged, true);
  assert.deepEqual(evaluation.liveRuns.map((run) => run.mode), ["codex", "hermes", "codex-hermes"]);
  for (const run of evaluation.liveRuns) {
    assert.equal(run.allProviderOutputsStructured, true, run.mode);
    assert.equal(run.allDecisionsAdmitted, true, run.mode);
    assert.equal(run.allEffectsVerified, true, run.mode);
    assert.equal(run.humanCorrections, 0, run.mode);
    assert.equal(run.originalTranscriptLoaded, false, run.mode);
    assert.equal(run.providerCalls, run.providerCallCounts.codex + run.providerCallCounts.hermes, run.mode);
    assert.equal(run.evidence.effects, run.evidence.worldEvents, run.mode);
    assert.equal(run.evidence.dispatches, run.evidence.worldEvents, run.mode);
    assert.equal(run.evidence.observations, run.evidence.worldEvents, run.mode);
    assert.equal(run.evidence.replayVerified, true, run.mode);
    assert.equal(run.evidence.replayDigest, run.terminal.worldDigest, run.mode);
    assert.ok(run.evidence.maximumContextBytes <= 16 * 1024, run.mode);
    assert.equal(run.terminal.missionStatus, "failure", run.mode);
  }
  const switched = evaluation.liveRuns.find((run) => run.mode === "codex-hermes");
  assert.ok(switched);
  assert.ok(switched.providerCallCounts.codex > 0);
  assert.ok(switched.providerCallCounts.hermes > 0);
  assert.equal(evaluation.conclusions.m2HostVerticalPathPassed, true);
  assert.equal(evaluation.conclusions.providerInterchangeabilityPassed, true);
  assert.equal(evaluation.conclusions.realProviderVictoryObserved, false);
  assert.equal(evaluation.conclusions.strategyFollowUpIssue, 20);
});
