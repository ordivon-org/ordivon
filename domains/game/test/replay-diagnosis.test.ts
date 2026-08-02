import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { buildKeyTurns, buildReplayCurves, replayCurvesFromFrames, replayKeyTurnsFromFrames } from "../src/replay/analysis.ts";
import { boundedFinalRoundSensitivity, diagnoseProjection, diagnoseRun, diagnosisDirectExplanation } from "../src/replay/diagnosis.ts";
import { buildRunEvidenceGraph } from "../src/replay/evidence.ts";
import { buildReplayProjection } from "../src/replay/projection.ts";
import { createGameServer } from "../src/server.ts";
import { GameStore } from "../src/storage.ts";
import { TeamHost } from "../src/team/engine.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";
async function run(caseId:string,strategy:"security-contain"|"engineer-seal",store=new GameStore(":memory:")){const runId=`run:diagnosis:${caseId}:${strategy}`;store.createRun({runId,scenarioVersion:2,scenarioCaseId:caseId,rulesetVersion:3});const host=new TeamHost(store,new FixtureTeamProvider({breachStrategy:strategy}));await host.run(runId,512);return{store,runId};}
async function listen(game:ReturnType<typeof createGameServer>){await new Promise<void>(resolve=>game.server.listen(0,"127.0.0.1",resolve));const address=game.server.address();if(!address||typeof address==="string")throw new Error("no address");return`http://127.0.0.1:${address.port}`;}
test("running mission diagnosis never invents a terminal failure",()=>{const store=new GameStore(":memory:");try{const diagnosis=diagnoseRun(store);assert.equal(diagnosis.terminal.status,"running");assert.equal(diagnosis.claims.some(c=>c.evidenceClass==="VERIFIED_DIRECT"),false);assert.ok(diagnosis.claims.some(claim=>/Mission remains active/.test(claim.title)));}finally{store.close();}});

test("direct terminal explanations cover every retained mission reason without upgrading evidence", () => {
  const expectations = new Map<string | null, RegExp>([
    ["power_exhausted", /Battery/], ["engineer_incapacitated", /Engineer/], ["team_incapacitated", /Team/],
    ["crew_lost", /crew/], ["reactor_meltdown", /Reactor/], ["mission_timeout", /turn limit/],
    ["rescue_signal_verified", /Rescue/], ["unknown_reason", /Terminal World/], [null, /Terminal World/],
  ]);
  for (const [reason, pattern] of expectations) {
    const [title, explanation] = diagnosisDirectExplanation(reason);
    assert.match(title, pattern);
    assert.ok(explanation.length > 20);
  }
});

test("pure Replay projection helpers fail closed and expose player and authority key turns", () => {
  const store = new GameStore(":memory:");
  try {
    const projection = buildReplayProjection(store);
    assert.throws(
      () => replayCurvesFromFrames(store.activeRunId, projection.graph, []),
      /Genesis frame/,
    );
    const frame = structuredClone(projection.frames[0]!);
    frame.authorityDecisions = [{ outcome: "require-human" } as any];
    frame.playerInterventions = [{
      nodeId: "host-event:player:test",
      kind: "host-event",
      payloadDigest: "sha256:test",
      summary: "player paused medic",
    }];
    frame.evidenceNodeIds.push("authority-decision:test");
    const turns = replayKeyTurnsFromFrames(store.activeRunId, projection.curves, [frame]);
    assert.ok(turns.some((turn) => turn.kind === "authority"));
    assert.ok(turns.some((turn) => turn.kind === "player"));
    assert.equal(turns.some((turn) => turn.kind === "terminal"), false);
    const thresholdCurves = structuredClone(projection.curves);
    thresholdCurves.oxygen = [
      { revision: 0, value: 60 },
      { revision: 1, value: 40 },
    ];
    assert.throws(
      () => replayKeyTurnsFromFrames(store.activeRunId, thresholdCurves, [frame]),
      /Missing Replay Frame 1/,
    );
  } finally {
    store.close();
  }
});

test("synthetic retained projections cover timeout and incapable item-holder contributors", () => {
  const store = new GameStore(":memory:");
  const runId = "run:diagnosis:synthetic-timeout";
  try {
    store.createRun({
      runId,
      scenarioVersion: 2,
      scenarioCaseId: "baseline",
      rulesetVersion: 3,
    });
    new TeamHost(store, new FixtureTeamProvider()).initialize(runId);
    const projection = buildReplayProjection(store, runId);
    const terminal = projection.frames.at(-1)!;
    terminal.state.mission.status = "failure";
    terminal.state.mission.reason = "mission_timeout";
    terminal.state.agents["security-01"]!.inventory.sealant = 1;
    const diagnosis = diagnoseProjection(store, projection);
    assert.ok(diagnosis.claims.some((claim) =>
      claim.evidenceClass === "VERIFIED_CONTRIBUTOR" &&
      /requirements remained incomplete/.test(claim.title),
    ));
    assert.ok(diagnosis.claims.some((claim) =>
      claim.evidenceClass === "VERIFIED_CONTRIBUTOR" &&
      /sealant remained/.test(claim.title),
    ));
  } finally {
    store.close();
  }
});
