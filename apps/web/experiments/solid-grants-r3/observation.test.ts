import assert from "node:assert/strict";
import {test} from "node:test";
import {initial,begin,suspend,settle,readObservation} from "./observation.ts";
const observed={status:"observed",observation:{principalId:"p",observedAt:1,grants:[]}} as const;
const denied={status:"denied",observation:null} as const;
test("newest refresh invalidates preceding snapshot and late success cannot resurrect it",()=>{
 const first=begin(initial), second=begin(first);
 const end=settle(second,second.generation,denied);
 assert.equal(settle(end,first.generation,observed),end);
 assert.equal(settle(end,second.generation,observed),end);
 assert.equal(end.observation,null);
});
test("newer success is not overwritten by older response or duplicate completion",()=>{
 const first=begin(initial), second=begin(first);
 const end=settle(second,second.generation,observed);
 assert.equal(settle(end,first.generation,denied),end);
 assert.equal(settle(end,second.generation,denied),end);
 assert.equal(begin(end).observation,null);
});
test("read rejects foreign rows and malformed observations",()=>{
 assert.throws(()=>readObservation({principalId:"p",observedAt:0,grants:[{principalId:"q"}]}));
 assert.throws(()=>readObservation({principalId:"p",observedAt:NaN,grants:[]}));
 assert.deepEqual(readObservation(observed.observation),observed.observation);
});

test("consumer retains only the row fields it renders",()=>{
 const result=readObservation({principalId:"p",observedAt:1,grants:[{
   principalId:"p",grantId:"g",agentId:"a",active:true,revision:1,remainingEffects:3,expiresAtEpochSeconds:9,grantDigest:"owner-only-extra"
 }]});
 assert.equal("grantDigest" in result.grants[0]!,false);
});

test("page suspension invalidates visible and in-flight data and is idempotent",()=>{
 const first=begin(initial), prior=settle(first,first.generation,observed);
 const hidden=suspend(prior);
 assert.equal(hidden.status,"suspended");
 assert.equal(hidden.observation,null);
 assert.equal(suspend(hidden),hidden);
 const second=begin(hidden);
 const suspendedPending=suspend(second);
 assert.equal(settle(suspendedPending,second.generation,observed),suspendedPending);
 const resumed=begin(suspendedPending);
 assert.equal(settle(resumed,second.generation,observed),resumed);
 assert.equal(settle(resumed,resumed.generation,observed).status,"observed");
});

/**
 * Executable specification of the reducer, independent of renderer.
 * An observation is evidence at an Owner-supplied time, not admission.
 * Completions in this model belong to requests issued by begin.
 * Caller lifecycle, peer hints and transport are integration obligations
 * of browser-probe.ts and formal/ObservationGenerationR1.tla.
 */
test("bounded observation contract: one eligible request; stale or duplicate completion cannot display", (t) => {
  type Machine = ReturnType<typeof begin>;
  type Result = Parameters<typeof settle>[2];
  type Event = {kind: "begin"} | {kind: "suspend"} |
    {kind: "complete"; request: number; result: Result};
  type Reference = {
    epoch: number; eligible: number | null; phase: Machine["status"];
    visible: Result["observation"]; issued: readonly number[];
  };
  function step(r: Reference, e: Event): Reference {
    switch (e.kind) {
      case "begin": {
        const request = r.epoch + 1;
        return {epoch: request, eligible: request, phase: "loading",
          visible: null, issued: [...r.issued, request]};
      }
      case "suspend":
        return r.phase === "suspended" ? r : {...r, epoch: r.epoch + 1,
          eligible: null, phase: "suspended", visible: null};
      case "complete":
        return e.request !== r.eligible ? r : {...r, eligible: null,
          phase: e.result.status, visible: e.result.observation};
    }
  }
  function run(s: Machine, e: Event): Machine {
    switch (e.kind) {
      case "begin": return begin(s);
      case "suspend": return suspend(s);
      case "complete": return settle(s, e.request, e.result);
    }
  }
  function success(request: number): Result {
    return {status: "observed", observation: {
      principalId: "p", observedAt: request, grants: [{
        principalId: "p", grantId: "grant:" + request, agentId: "a",
        active: true, revision: request, remainingEffects: 1, expiresAtEpochSeconds: 99,
      }],
    }};
  }
  const referenceInitial: Reference = {
    epoch: 0, eligible: null, phase: "loading", visible: null, issued: [],
  };
  const coverage = new Set<string>(), visited = new Set<string>();
  let transitions = 0;
  const frontier: {reference: Reference; implementation: Machine; trace: Event[]}[] = [
    {reference: referenceInitial, implementation: initial, trace: []},
  ];
  while (frontier.length) {
    const {reference: r, implementation: s, trace} = frontier.pop()!;
    assert.deepEqual(s, {generation: r.epoch, status: r.phase, observation: r.visible},
      JSON.stringify(trace));
    const key = JSON.stringify([trace.length, r]);
    if (visited.has(key) || trace.length === 6) continue;
    visited.add(key);
    const events: Event[] = [{kind: "begin"}, {kind: "suspend"}];
    for (const request of r.issued) {
      events.push(
        {kind: "complete", request, result: success(request)},
        {kind: "complete", request, result: {status: "denied", observation: null}},
        {kind: "complete", request, result: {status: "unavailable", observation: null}},
      );
    }
    for (const e of events) {
      transitions++;
      if (e.kind === "complete") {
        if (e.request === r.eligible) coverage.add("accept:" + e.result.status);
        else if (r.phase === "suspended") coverage.add("late-after-suspension");
        else if (r.epoch === e.request) coverage.add("duplicate");
        else coverage.add("old-generation");
      }
      if (e.kind === "suspend" && r.phase === "suspended") coverage.add("idempotent-suspension");
      if (e.kind === "begin" && r.phase === "suspended") coverage.add("resume");
      frontier.push({reference: step(r, e), implementation: run(s, e), trace: [...trace, e]});
    }
  }
  assert.ok(transitions > 1000, "non-vacuous bounded exploration");
  assert.deepEqual([...coverage].sort(), [
    "accept:denied", "accept:observed", "accept:unavailable",
    "duplicate", "idempotent-suspension", "late-after-suspension", "old-generation", "resume",
  ]);
  t.diagnostic(JSON.stringify({transitions, expandedStates: visited.size, depth: 6}));
});
