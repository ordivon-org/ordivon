import assert from "node:assert/strict";
import test from "node:test";

// @ts-expect-error Browser module intentionally has no Node declaration.
import { renderCompare } from "../web/render-compare.js";
// @ts-expect-error Browser module intentionally has no Node declaration.
import { renderDiagnosis } from "../web/render-diagnosis.js";
// @ts-expect-error Browser module intentionally has no Node declaration.
import { renderReplay } from "../web/render-replay.js";
// @ts-expect-error Browser module intentionally has no Node declaration.
import { renderDeployment } from "../web/render-shell.js";
// @ts-expect-error Browser module intentionally has no Node declaration.
import { compareRunIdFromUrl, revisionFromUrl, surfaceFromUrl, urlForState } from "../web/store.js";
// @ts-expect-error Browser module intentionally has no Node declaration.
import { humanize } from "../web/render-utils.js";

test("URL state retains Run, surface, revision, and comparison base", () => {
  const url = urlForState("https://game.test/?source=retained", {
    runId: "run:second",
    surface: "replay",
    revision: 5,
    compareRunId: "run:first",
  });
  assert.equal(url, "/?source=retained&runId=run%3Asecond&view=replay&revision=5&compareRunId=run%3Afirst");
  const full = `https://game.test${url}`;
  assert.equal(surfaceFromUrl(full), "replay");
  assert.equal(revisionFromUrl(full), 5);
  assert.equal(compareRunIdFromUrl(full), "run:first");
  assert.equal(surfaceFromUrl("https://game.test/?view=invalid"), "mission");
  assert.equal(revisionFromUrl("https://game.test/?revision=-1"), null);
});

test("humanize makes persisted camelCase identities readable", () => {
  assert.equal(humanize("coordinationProfileId"), "Coordination Profile Id");
});

test("Deployment renders fixed loadout, measured coordination, and Provider readiness", () => {
  const html = renderDeployment([], {
    catalog: {
      actors: [{ actorId: "engineer-01", name: "Engineer", role: "engineer", defaultProvider: "fixture" }],
      providers: [{ providerId: "fixture", label: "Fixture", deterministic: true }],
      cases: [{ caseId: "baseline", label: "Baseline" }],
      authorityPolicies: [{ policyMode: "autonomous", label: "Autonomous" }],
      doctrines: [{ doctrineId: "delegated-response", label: "Delegated response", description: "Routine work proceeds.", authorityPolicyMode: "autonomous" }],
      playDefaults: { doctrineId: "delegated-response", scenarioCaseId: "baseline", coordinationProfileId: "specialist-containment" },
      fixedLoadout: { profileId: "standard-loadout", label: "Standard loadout", description: "Fixed" },
      coordinationProfiles: [{ profileId: "specialist-containment", label: "Specialist containment" }],
    },
    preflight: { providers: [{ providerId: "fixture", ready: true, summary: "Ready" }] },
  });
  assert.match(html, /Coordination fixture/);
  assert.match(html, /Command doctrine/);
  assert.match(html, /Three persistent specialists/);
  assert.match(html, /Provider readiness/);
});

test("Replay, Diagnosis, and Compare render bounded product evidence", () => {
  const state = {
    turn: 0, mission: { status: "victory", reason: "rescue_signal_verified", turnLimit: 24 },
    resources: { batteryCharge: 10, oxygen: 90, reactorHeat: 20 },
    agents: {}, systems: {},
  };
  const report: any = {
    runId: "run:test",
    summary: { terminalRevision: 0 },
    curves: { battery: [{ revision: 0, value: 10 }], oxygen: [{ revision: 0, value: 90 }], reactorHeat: [{ revision: 0, value: 20 }] },
    keyTurns: [{ revision: 0, kind: "terminal", title: "Rescue verified" }],
    diagnosis: { terminal: { status: "victory", reason: "rescue_signal_verified", revision: 0 }, claims: [{ evidenceClass: "VERIFIED_DIRECT", revision: 0, title: "Rescue", explanation: "Verified", evidenceNodeIds: ["world-state:test:0"] }], unsupportedCounterfactualReason: "None", diagnosisDigest: "sha256:diagnosis" },
  };
  const frame: any = { revision: 0, verified: true, digest: "sha256:world", state, evidenceNodeIds: ["world-state:test:0"], proposals: [], facts: [], authorityGrants: [], authorityDecisions: [], playerInterventions: [], contexts: [], messages: [], hostRecords: [], round: null, effect: null, dispatch: null, observation: null };
  assert.match(renderReplay(report, frame), /data-replay-revision/);
  assert.match(renderDiagnosis(report), /Verified direct/);
  const comparison: any = { mode: "exact", compatibilityReasons: ["Compatible"], comparisonDigest: "sha256:compare", inputDifferences: [{ field: "coordinationProfileId", left: "a", right: "b" }], metricDifferences: [{ metric: "status", left: "victory", right: "failure" }], left: { manifest: { runId: "a", coordinationProfileId: "a", manifestDigest: "sha256:a" }, metrics: { status: "victory", reason: "rescue", score: 1, revisions: 1, minimumBattery: 1 } }, right: { manifest: { runId: "b", coordinationProfileId: "b", manifestDigest: "sha256:b" }, metrics: { status: "failure", reason: "power", score: 0, revisions: 2, minimumBattery: 0 } } };
  assert.match(renderCompare(comparison), /Exact compatible comparison/);
});
