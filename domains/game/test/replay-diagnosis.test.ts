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
test("curves contain exactly one point per revision and conserve items",async()=>{const{store,runId}=await run("baseline","security-contain");try{const graph=buildRunEvidenceGraph(store,runId),curves=buildReplayCurves(store,runId,graph);assert.equal(curves.revisions.length,19);assert.deepEqual(curves.revisions,Array.from({length:19},(_,i)=>i));for(const points of [curves.battery,curves.oxygen,curves.reactorHeat,...Object.values(curves.actorHealth),...Object.values(curves.crewHealth),...Object.values(curves.systems),...Object.values(curves.items),...Object.values(curves.objectives)])assert.equal(points.length,19);for(const points of Object.values(curves.items)){assert.equal(new Set(points.map(point=>point.total)).size,1);}assert.equal(buildReplayCurves(store,runId,graph).curvesDigest,curves.curvesDigest);}finally{store.close();}});
test("victory diagnosis is direct, evidence-linked, deterministic, and bounded",async()=>{const{store,runId}=await run("baseline","security-contain");try{const first=diagnoseRun(store,runId),second=diagnoseRun(store,runId);assert.deepEqual(second,first);assert.equal(first.terminal.status,"victory");assert.equal(first.terminal.reason,"rescue_signal_verified");assert.equal(first.claims[0]?.evidenceClass,"VERIFIED_DIRECT");assert.ok(first.claims[0]?.evidenceNodeIds.every(id=>id.startsWith("world-")));assert.ok(first.keyTurns.length<=12);assert.ok(first.keyTurns.some(turn=>turn.kind==="terminal"&&turn.revision===first.terminal.revision));assert.ok(first.keyTurns.some(turn=>turn.kind==="objective"&&/distress|rescue/i.test(turn.title)));assert.ok(first.claims.some(claim=>claim.evidenceClass==="CONTEXT_ONLY"&&/counterfactual/.test(claim.title)));}finally{store.close();}});
test("power exhaustion reports direct predicate and verified battery contributors without singular causality",async()=>{const{store,runId}=await run("power-constrained","engineer-seal");try{const diagnosis=diagnoseRun(store,runId);assert.equal(diagnosis.terminal.status,"failure");assert.equal(diagnosis.terminal.reason,"power_exhausted");assert.match(diagnosis.claims.find(c=>c.evidenceClass==="VERIFIED_DIRECT")?.title??"",/Battery/);assert.ok(diagnosis.claims.some(c=>c.evidenceClass==="VERIFIED_CONTRIBUTOR"&&/Battery reserve/.test(c.title)));assert.ok(diagnosis.claims.filter(c=>c.evidenceClass!=="CONTEXT_ONLY").every(c=>c.evidenceNodeIds.length>0));const sensitive=boundedFinalRoundSensitivity(store,runId);assert.deepEqual(diagnosis.claims.filter(c=>c.evidenceClass==="COUNTERFACTUAL_SENSITIVE"),sensitive);assert.equal(diagnosis.unsupportedCounterfactualReason===null,sensitive.length>0);}finally{store.close();}});
test("oxygen-constrained failure reports health and oxygen contributors",async()=>{const{store,runId}=await run("oxygen-constrained","engineer-seal");try{const diagnosis=diagnoseRun(store,runId);assert.equal(diagnosis.terminal.reason,"team_incapacitated");assert.ok(diagnosis.claims.some(c=>/Oxygen loss/.test(c.title)));assert.ok(diagnosis.claims.some(c=>/lost health/.test(c.title)));assert.ok(diagnosis.keyTurns.some(turn=>turn.kind==="health-threshold"));}finally{store.close();}});
test("running mission diagnosis never invents a terminal failure",()=>{const store=new GameStore(":memory:");try{const diagnosis=diagnoseRun(store);assert.equal(diagnosis.terminal.status,"running");assert.equal(diagnosis.claims.some(c=>c.evidenceClass==="VERIFIED_DIRECT"),false);assert.ok(diagnosis.claims.some(claim=>/Mission remains active/.test(claim.title)));}finally{store.close();}});
test("one Replay Projection batch-verifies every revision without single-revision calls",async()=>{const{store,runId}=await run("baseline","security-contain");try{const expected=store.statesAtEveryRevision(runId);const batch=store.statesAtEveryRevision.bind(store);const single=store.stateAtRevision.bind(store);let batchCalls=0;let singleCalls=0;(store as any).statesAtEveryRevision=(selectedRunId?:string)=>{batchCalls+=1;return batch(selectedRunId);};(store as any).stateAtRevision=(revision:number,selectedRunId?:string)=>{singleCalls+=1;return single(revision,selectedRunId);};const projection=buildReplayProjection(store,runId);assert.equal(batchCalls,1);assert.equal(singleCalls,0);assert.equal(projection.frames.length,expected.length);projection.frames.forEach((frame,revision)=>assert.equal(frame.digest,expected[revision]!.digest));assert.equal(diagnoseProjection(store,projection).graphDigest,projection.graph.graphDigest);}finally{store.close();}});
test("analysis and diagnosis HTTP APIs are read-only",async()=>{const directory=mkdtempSync(join(tmpdir(),"ordivon-diagnosis-http-"));const game=createGameServer({dbPath:join(directory,"world.sqlite3"),teamProviderFactory:()=>new FixtureTeamProvider()});try{const runId="run:diagnosis:http";game.store.createRun({runId,scenarioVersion:2,scenarioCaseId:"baseline",rulesetVersion:3});await new TeamHost(game.store,new FixtureTeamProvider()).run(runId,512);const before=game.store.eventCount(runId),base=await listen(game);const analysis=await fetch(`${base}/api/replay/analysis?runId=${runId}`);assert.equal(analysis.status,200);const a=await analysis.json() as any;assert.equal(a.curves.revisions.length,19);assert.ok(a.keyTurns.length<=12);const response=await fetch(`${base}/api/replay/diagnosis?runId=${runId}`);assert.equal(response.status,200);const diagnosis=await response.json() as any;assert.equal(diagnosis.terminal.status,"victory");const reportResponse=await fetch(`${base}/api/replay/report?runId=${runId}`);assert.equal(reportResponse.status,200);const report=await reportResponse.json() as any;assert.equal(report.kind,"ordivon.game.replay-report");assert.equal(report.diagnosis.diagnosisDigest,diagnosis.diagnosisDigest);assert.equal(report.summary.graphDigest,report.curves.graphDigest);assert.equal(game.store.eventCount(runId),before);}finally{await game.close();rmSync(directory,{recursive:true,force:true});}});


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
