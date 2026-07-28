import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

interface M4Evaluation {
  schemaVersion: 1;
  kind: "ordivon.game.m4-evaluation";
  sourceRevision: string;
  fixture: {
    initialized: {
      status: string;
      actorCount: number;
      authorityPolicyMode: string;
      providerOrders: Record<string, string[]>;
    };
    readPurity: { identicalViews: boolean; journalDelta: number };
    proposalReview: {
      boundary: string;
      worldRevision: number;
      phase: string;
      actorProposalCount: number;
      worldMutationBeforeReview: boolean;
    };
    firstVerifiedTick: {
      boundary: string;
      revisionDelta: number;
      phase: string;
      verifiedFactCount: number;
    };
    terminal: {
      status: string;
      reason: string;
      turn: number;
      worldDigest: string;
      score: number;
      encodedBytes: number;
      under64KiB: boolean;
      actorCount: number;
      objectiveProgress: { resolved: number; satisfied: number; superseded: number; total: number };
      terminalPathResolved: boolean;
      timelineItems: number;
      worldStatus: string;
    };
    replay: {
      verified: boolean;
      eventCount: number;
      digestMatchesTerminal: boolean;
      recoveredDigestMatches: boolean;
    };
  };
  controlAndReload: Record<string, boolean>;
  intervention: {
    authority: {
      reached: boolean;
      severity: string;
      explanationPresent: boolean;
      consequencePresent: boolean;
      urgencyPresent: boolean;
      approvalAndDenialCommands: string[];
    };
    denial: {
      proposalId: string;
      selectedAfterDenial: boolean;
      admittedPathChanged: boolean;
      resultingBoundary: string;
    };
    resourceMismatch: {
      detectedBeforeCommit: boolean;
      severity: string;
      actorIds: string[];
      commands: string[];
    };
  };
  web: {
    renderSmokePassed: boolean;
    productMarkers: Record<string, boolean>;
    debugMarkers: Record<string, boolean>;
    files: Record<string, string>;
    runtimeDependencyCount: number;
    devDependencyCount: number;
  };
  conclusions: {
    m4Issue6AcceptancePassed: boolean;
    mainProductUsesPrimitiveWorldCommands: boolean;
    mainProductUsesRawHostLogs: boolean;
    hiddenManagerModelAdded: boolean;
    runtimeDependenciesAdded: boolean;
    liveProviderReevaluationRequired: boolean;
    liveProviderEvidenceReusedFrom: string;
    nextMilestone: string;
  };
}

test("M4 evidence proves a playable bounded mission-control product", () => {
  const evaluation = JSON.parse(readFileSync("docs/M4-EVALUATION.json", "utf8")) as M4Evaluation;

  assert.equal(evaluation.schemaVersion, 1);
  assert.equal(evaluation.kind, "ordivon.game.m4-evaluation");
  assert.equal(evaluation.sourceRevision, "123e89bfd33f4fcd99149c95d08d6bb86dcaca2f");

  assert.equal(evaluation.fixture.initialized.status, "running");
  assert.equal(evaluation.fixture.initialized.actorCount, 3);
  assert.equal(evaluation.fixture.initialized.authorityPolicyMode, "autonomous");
  assert.deepEqual(evaluation.fixture.initialized.providerOrders, {
    "engineer-01": ["fixture"],
    "medic-01": ["fixture"],
    "security-01": ["fixture"],
  });

  assert.equal(evaluation.fixture.readPurity.identicalViews, true);
  assert.equal(evaluation.fixture.readPurity.journalDelta, 0);

  assert.equal(evaluation.fixture.proposalReview.boundary, "proposal-review");
  assert.equal(evaluation.fixture.proposalReview.phase, "proposal-review");
  assert.equal(evaluation.fixture.proposalReview.worldRevision, 0);
  assert.equal(evaluation.fixture.proposalReview.actorProposalCount, 3);
  assert.equal(evaluation.fixture.proposalReview.worldMutationBeforeReview, false);

  assert.equal(evaluation.fixture.firstVerifiedTick.boundary, "tick-verified");
  assert.equal(evaluation.fixture.firstVerifiedTick.phase, "verified");
  assert.equal(evaluation.fixture.firstVerifiedTick.revisionDelta, 1);
  assert.ok(evaluation.fixture.firstVerifiedTick.verifiedFactCount > 0);

  assert.equal(evaluation.fixture.terminal.status, "victory");
  assert.equal(evaluation.fixture.terminal.worldStatus, "victory");
  assert.equal(evaluation.fixture.terminal.reason, "rescue_signal_verified");
  assert.equal(evaluation.fixture.terminal.turn, 18);
  assert.equal(evaluation.fixture.terminal.worldDigest, "a8ef1f491c35720ed02e66f004ccd7f3466f78991dcafecd442ceae66b09ceb7");
  assert.equal(evaluation.fixture.terminal.score, 2264);
  assert.equal(evaluation.fixture.terminal.actorCount, 3);
  assert.ok(evaluation.fixture.terminal.encodedBytes <= 64 * 1024);
  assert.equal(evaluation.fixture.terminal.under64KiB, true);
  assert.deepEqual(evaluation.fixture.terminal.objectiveProgress, {
    resolved: 12,
    satisfied: 11,
    superseded: 1,
    total: 12,
  });
  assert.equal(evaluation.fixture.terminal.terminalPathResolved, true);
  assert.ok(evaluation.fixture.terminal.timelineItems > 0);

  assert.equal(evaluation.fixture.replay.verified, true);
  assert.equal(evaluation.fixture.replay.eventCount, 18);
  assert.equal(evaluation.fixture.replay.digestMatchesTerminal, true);
  assert.equal(evaluation.fixture.replay.recoveredDigestMatches, true);

  assert.ok(Object.values(evaluation.controlAndReload).every(Boolean));

  assert.equal(evaluation.intervention.authority.reached, true);
  assert.equal(evaluation.intervention.authority.explanationPresent, true);
  assert.equal(evaluation.intervention.authority.consequencePresent, true);
  assert.equal(evaluation.intervention.authority.urgencyPresent, true);
  assert.deepEqual(evaluation.intervention.authority.approvalAndDenialCommands, ["approve", "deny"]);

  assert.match(evaluation.intervention.denial.proposalId, /^team-proposal:[a-f0-9]{64}$/);
  assert.equal(evaluation.intervention.denial.selectedAfterDenial, false);
  assert.equal(evaluation.intervention.denial.admittedPathChanged, true);
  assert.equal(evaluation.intervention.denial.resultingBoundary, "tick-verified");

  assert.equal(evaluation.intervention.resourceMismatch.detectedBeforeCommit, true);
  assert.equal(evaluation.intervention.resourceMismatch.severity, "critical");
  assert.deepEqual(evaluation.intervention.resourceMismatch.actorIds, ["security-01", "engineer-01"]);
  assert.deepEqual(evaluation.intervention.resourceMismatch.commands, ["deny", "pause"]);

  assert.equal(evaluation.web.renderSmokePassed, true);
  assert.ok(Object.values(evaluation.web.productMarkers).every(Boolean));
  assert.ok(Object.values(evaluation.web.debugMarkers).every(Boolean));
  for (const digest of Object.values(evaluation.web.files)) assert.match(digest, /^[a-f0-9]{64}$/);
  assert.equal(evaluation.web.runtimeDependencyCount, 0);

  assert.equal(evaluation.conclusions.m4Issue6AcceptancePassed, true);
  assert.equal(evaluation.conclusions.mainProductUsesPrimitiveWorldCommands, false);
  assert.equal(evaluation.conclusions.mainProductUsesRawHostLogs, false);
  assert.equal(evaluation.conclusions.hiddenManagerModelAdded, false);
  assert.equal(evaluation.conclusions.runtimeDependenciesAdded, false);
  assert.equal(evaluation.conclusions.liveProviderReevaluationRequired, false);
  assert.equal(evaluation.conclusions.liveProviderEvidenceReusedFrom, "M3");
  assert.match(evaluation.conclusions.nextMilestone, /M5/);
});
