import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

interface FixturePlan {
  mode: "fixture-security" | "fixture-engineer";
  missionStatus: "victory";
  turn: number;
  terminalDigest: string;
  score: number;
  hazardSealed: boolean;
  hazardContained: boolean;
  providerCalls: number;
  worldEvents: number;
  rounds: number;
  effects: number;
  dispatches: number;
  observations: number;
  replayVerified: boolean;
  replayDigest: string;
  maximumContextTokens: number;
  rawEvaluationFileDigest: string;
}

interface LiveRun {
  mode: "codex" | "mixed" | "hermes" | "codex-hermes-switch";
  sourceRevision: string;
  rawArtifact: { jobId: string; artifactId: string; digest: string };
  rawEvaluationFileDigest: string;
  providerCallCounts: { codex: number; hermes: number; fixture: number };
  providerCallCount: number;
  providerCallsSucceeded: number;
  providerCallsFailed: number;
  allProviderOutputsJsonStructured: boolean;
  allDecisionsAdmitted: boolean;
  humanCorrections: number;
  originalTranscriptLoaded: boolean;
  hiddenFixtureFallback: boolean;
  hiddenManagerModel: boolean;
  firstPhase: { worldRevision: number; worldDigest: string; rounds: number } | null;
  terminal: {
    missionStatus: "victory" | "failure";
    missionReason: string;
    turn: number;
    worldDigest: string;
    score: number;
    lifeSupportOperational: boolean;
    communicationsOperational: boolean;
  };
  evidence: {
    worldEvents: number;
    rounds: number;
    completedRounds: number;
    contexts: number;
    proposals: number;
    verifiedProposals: number;
    effects: number;
    dispatches: number;
    observations: number;
    replayVerified: boolean;
    replayDigest: string;
    allRoundsCompleted: boolean;
    allEffectsVerified: boolean;
    allDispatchesSucceeded: boolean;
    maximumContextTokens: number;
  };
  usage: { reportedEstimatedCostUsd: number | null };
}

interface Evaluation {
  sourceRevision: string;
  contextSchemaVersion: number;
  implementation: Record<string, boolean | number>;
  automatedEvidence: {
    tests: number;
    testsPassed: number;
    coverage: { lines: number; branches: number; functions: number };
    fixturePlans: FixturePlan[];
    interruptionFaultPoints: string[];
    allInterruptionRunsConverged: boolean;
    communicationComparison: {
      local: { initialStatus: string; missionStatus: string; missionReason: string; turn: number; worldDigest: string };
      unavailableRadio: { initialStatus: string; finalStatus: string; missionStatus: string; missionReason: string; turn: number; worldDigest: string };
      outcomeChanged: boolean;
    };
    authority: Record<string, boolean>;
    failureIsolation: Record<string, boolean>;
    conflictResolution: Record<string, boolean>;
  };
  liveRuns: LiveRun[];
  acceptance: Record<string, boolean>;
  conclusions: {
    m3Issue5AcceptancePassed: boolean;
    realVictories: string[];
    providerReplacementContinuityPassed: boolean;
    providerReplacementVictoryObserved: boolean;
    remainingFailureModes: Record<string, string>;
  };
}

test("M3 evidence proves multi-Agent acceptance without hiding Provider failures", () => {
  const evaluation = JSON.parse(readFileSync("docs/M3-EVALUATION.json", "utf8")) as Evaluation;
  assert.equal(evaluation.sourceRevision, "835c11a25fd27d5fbd9cd1c495a82b8c1e7dd9f3");
  assert.equal(evaluation.contextSchemaVersion, 1);
  assert.equal(evaluation.implementation.scenarioVersion, 2);
  assert.equal(evaluation.implementation.rulesetVersion, 3);
  assert.equal(evaluation.implementation.specialistCount, 3);
  assert.equal(evaluation.implementation.atomicMultiActorTick, true);
  assert.equal(evaluation.implementation.environmentAdvancesOncePerTick, true);
  assert.equal(evaluation.implementation.actorScopedContext, true);
  assert.equal(evaluation.implementation.typedDeliveryLimitedMessages, true);
  assert.equal(evaluation.implementation.attributeBasedAuthority, true);
  assert.equal(evaluation.implementation.singleUseAuthorityGrants, true);
  assert.equal(evaluation.implementation.hiddenManagerModelAdded, false);
  assert.equal(evaluation.implementation.providerSessionsRetained, false);
  assert.equal(evaluation.implementation.runtimeDependenciesAdded, 0);
  assert.equal(evaluation.implementation.m2CompatibilityPreserved, true);

  assert.equal(evaluation.automatedEvidence.tests, 159);
  assert.equal(evaluation.automatedEvidence.testsPassed, 159);
  assert.ok(evaluation.automatedEvidence.coverage.lines >= 95);
  assert.ok(evaluation.automatedEvidence.coverage.branches >= 90);
  assert.ok(evaluation.automatedEvidence.coverage.functions >= 95);
  assert.equal(evaluation.automatedEvidence.interruptionFaultPoints.length, 8);
  assert.equal(evaluation.automatedEvidence.allInterruptionRunsConverged, true);

  assert.deepEqual(evaluation.automatedEvidence.fixturePlans.map((run) => run.mode), ["fixture-security", "fixture-engineer"]);
  const containment = evaluation.automatedEvidence.fixturePlans[0];
  const sealing = evaluation.automatedEvidence.fixturePlans[1];
  assert.ok(containment && sealing);
  assert.equal(containment.turn, 18);
  assert.equal(containment.terminalDigest, "a8ef1f491c35720ed02e66f004ccd7f3466f78991dcafecd442ceae66b09ceb7");
  assert.equal(containment.hazardContained, true);
  assert.equal(containment.hazardSealed, false);
  assert.equal(sealing.turn, 22);
  assert.equal(sealing.terminalDigest, "0913c9cacb05af3e1dc1bab3a43e3a3a36efd5277da127c18182d05166939bf4");
  assert.equal(sealing.hazardSealed, true);
  assert.equal(sealing.hazardContained, false);
  for (const run of evaluation.automatedEvidence.fixturePlans) {
    assert.equal(run.missionStatus, "victory", run.mode);
    assert.equal(run.worldEvents, run.rounds, run.mode);
    assert.equal(run.worldEvents, run.effects, run.mode);
    assert.equal(run.worldEvents, run.dispatches, run.mode);
    assert.equal(run.worldEvents, run.observations, run.mode);
    assert.equal(run.replayVerified, true, run.mode);
    assert.equal(run.replayDigest, run.terminalDigest, run.mode);
    assert.ok(run.maximumContextTokens <= 4_000, run.mode);
    assert.match(run.rawEvaluationFileDigest, /^sha256:[a-f0-9]{64}$/);
  }

  const communication = evaluation.automatedEvidence.communicationComparison;
  assert.equal(communication.local.initialStatus, "delivered");
  assert.equal(communication.local.missionStatus, "victory");
  assert.equal(communication.local.missionReason, "rescue_signal_verified");
  assert.equal(communication.unavailableRadio.initialStatus, "pending");
  assert.equal(communication.unavailableRadio.finalStatus, "delivered");
  assert.equal(communication.unavailableRadio.missionStatus, "failure");
  assert.equal(communication.unavailableRadio.missionReason, "power_exhausted");
  assert.notEqual(communication.local.worldDigest, communication.unavailableRadio.worldDigest);
  assert.equal(communication.outcomeChanged, true);
  assert.ok(Object.values(evaluation.automatedEvidence.authority).every(Boolean));
  assert.ok(Object.values(evaluation.automatedEvidence.failureIsolation).every(Boolean));
  assert.ok(Object.values(evaluation.automatedEvidence.conflictResolution).every(Boolean));

  assert.deepEqual(evaluation.liveRuns.map((run) => run.mode), ["codex", "mixed", "hermes", "codex-hermes-switch"]);
  for (const run of evaluation.liveRuns) {
    assert.equal(run.sourceRevision, evaluation.sourceRevision, run.mode);
    assert.equal(run.providerCallCount, run.providerCallCounts.codex + run.providerCallCounts.hermes + run.providerCallCounts.fixture, run.mode);
    assert.equal(run.providerCallsSucceeded + run.providerCallsFailed, run.providerCallCount, run.mode);
    assert.equal(run.allProviderOutputsJsonStructured, true, run.mode);
    assert.equal(run.humanCorrections, 0, run.mode);
    assert.equal(run.originalTranscriptLoaded, false, run.mode);
    assert.equal(run.hiddenFixtureFallback, false, run.mode);
    assert.equal(run.hiddenManagerModel, false, run.mode);
    assert.match(run.rawArtifact.jobId, /^job-/);
    assert.match(run.rawArtifact.artifactId, /\.stdout$/);
    assert.match(run.rawArtifact.digest, /^sha256:[a-f0-9]{64}$/);
    assert.match(run.rawEvaluationFileDigest, /^sha256:[a-f0-9]{64}$/);
    assert.equal(run.evidence.worldEvents, run.evidence.rounds, run.mode);
    assert.equal(run.evidence.rounds, run.evidence.completedRounds, run.mode);
    assert.equal(run.evidence.worldEvents, run.evidence.effects, run.mode);
    assert.equal(run.evidence.worldEvents, run.evidence.dispatches, run.mode);
    assert.equal(run.evidence.worldEvents, run.evidence.observations, run.mode);
    assert.equal(run.evidence.proposals, run.evidence.verifiedProposals, run.mode);
    assert.equal(run.evidence.replayVerified, true, run.mode);
    assert.equal(run.evidence.replayDigest, run.terminal.worldDigest, run.mode);
    assert.equal(run.evidence.allRoundsCompleted, true, run.mode);
    assert.equal(run.evidence.allEffectsVerified, true, run.mode);
    assert.equal(run.evidence.allDispatchesSucceeded, true, run.mode);
    assert.ok(run.evidence.maximumContextTokens <= 4_000, run.mode);
  }

  const codex = evaluation.liveRuns.find((run) => run.mode === "codex");
  const mixed = evaluation.liveRuns.find((run) => run.mode === "mixed");
  const hermes = evaluation.liveRuns.find((run) => run.mode === "hermes");
  const switched = evaluation.liveRuns.find((run) => run.mode === "codex-hermes-switch");
  assert.ok(codex && mixed && hermes && switched);
  assert.equal(codex.terminal.missionStatus, "victory");
  assert.equal(codex.providerCallCount, 60);
  assert.equal(codex.providerCallsFailed, 0);
  assert.equal(codex.allDecisionsAdmitted, true);
  assert.equal(codex.usage.reportedEstimatedCostUsd, null);
  assert.equal(mixed.terminal.missionStatus, "victory");
  assert.deepEqual(mixed.providerCallCounts, { codex: 20, hermes: 40, fixture: 0 });
  assert.ok((mixed.usage.reportedEstimatedCostUsd ?? 0) > 0);
  assert.equal(hermes.terminal.missionStatus, "failure");
  assert.equal(hermes.terminal.missionReason, "mission_timeout");
  assert.equal(hermes.providerCallsFailed, 0);
  assert.equal(hermes.allDecisionsAdmitted, true);
  assert.equal(hermes.terminal.lifeSupportOperational, false);
  assert.equal(hermes.terminal.communicationsOperational, false);
  assert.equal(switched.terminal.missionStatus, "failure");
  assert.equal(switched.terminal.missionReason, "mission_timeout");
  assert.deepEqual(switched.providerCallCounts, { codex: 12, hermes: 54, fixture: 0 });
  assert.equal(switched.providerCallsFailed, 1);
  assert.equal(switched.allDecisionsAdmitted, false);
  assert.equal(switched.firstPhase?.worldRevision, 4);
  assert.equal(switched.firstPhase?.rounds, 4);

  assert.ok(Object.values(evaluation.acceptance).every(Boolean));
  assert.equal(evaluation.conclusions.m3Issue5AcceptancePassed, true);
  assert.deepEqual(evaluation.conclusions.realVictories, ["codex", "mixed"]);
  assert.equal(evaluation.conclusions.providerReplacementContinuityPassed, true);
  assert.equal(evaluation.conclusions.providerReplacementVictoryObserved, false);
  assert.match(evaluation.conclusions.remainingFailureModes.hermes ?? "", /spare parts|life support|communications/i);
  assert.match(evaluation.conclusions.remainingFailureModes["codex-hermes-switch"] ?? "", /replacement|spare-part|mission timeout/i);
});
