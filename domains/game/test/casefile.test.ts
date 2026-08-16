import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { CASEFILE_SCENARIOS, CasefileService, CasefileStore, casefileLegalActions } from "../src/casefile/index.ts";

function fixture() {
  const store = new CasefileStore(":memory:");
  const service = new CasefileService(store);
  return { store, service };
}

test("Casefile catalog exposes three bounded incidents without choosing a generic game platform", () => {
  const { store, service } = fixture();
  try {
    const catalog = service.catalog();
    assert.equal(catalog.scenarios.length, 3);
    assert.deepEqual(catalog.scenarios.map((scenario) => scenario.scenarioId), ["relay-sabotage", "missing-med-cache", "false-pressure-alarm"]);
    assert.equal(new Set(CASEFILE_SCENARIOS.map((scenario) => scenario.culpritId)).size, 3);
  } finally { store.close(); }
});

test("nonterminal Casefile projection withholds culprit, motive, reconstruction, and uninspected clue text", () => {
  const { store, service } = fixture();
  try {
    const view = service.initialize("case:hidden", "relay-sabotage");
    assert.equal(view.run.status, "investigating");
    assert.equal(view.run.movesRemaining, 8);
    assert.equal(view.outcome, null);
    assert.ok(view.traces.every((trace) => trace.clue === null));
    const json = JSON.stringify(view);
    assert.equal(json.includes("culpritId"), false);
    assert.equal(json.includes("copy embargoed lab results"), false);
    assert.equal(json.includes("At 21:05 Sol left the Lab"), false);
  } finally { store.close(); }
});

test("Casefile legal surface is state-derived and confrontation appears only after its trace is inspected", () => {
  const { store, service } = fixture();
  try {
    service.initialize("case:actions", "relay-sabotage");
    let state = store.read("case:actions");
    assert.equal(casefileLegalActions(state).some((action) => action.kind === "confront"), false);
    let view = service.act("case:actions", "inspect:coolant-fiber");
    assert.equal(view.run.movesRemaining, 7);
    assert.equal(view.traces.find((trace) => trace.traceId === "coolant-fiber")?.inspected, true);
    const confront = view.actions.find((action) => action.actionId === "confront:sol:coolant-fiber");
    assert.ok(confront);
    view = service.act("case:actions", confront.actionId);
    assert.match(view.people.find((person) => person.personId === "sol")?.lastStatement ?? "", /I did cross the corridor/);
    state = store.read("case:actions");
    assert.equal(casefileLegalActions(state).some((action) => action.actionId === confront.actionId), false);
  } finally { store.close(); }
});

test("question policy changes with retained local interaction history without model cognition", () => {
  const { store, service } = fixture();
  try {
    service.initialize("case:testimony", "relay-sabotage");
    const first = service.act("case:testimony", "question:sol");
    assert.match(first.people.find((person) => person.personId === "sol")?.lastStatement ?? "", /never entered the relay corridor/);
    const second = service.act("case:testimony", "question:sol");
    assert.match(second.people.find((person) => person.personId === "sol")?.lastStatement ?? "", /using my shift/);
    assert.notEqual(first.people.find((person) => person.personId === "sol")?.lastStatement, second.people.find((person) => person.personId === "sol")?.lastStatement);
  } finally { store.close(); }
});

test("accusation is an explicit terminal commitment and only then reveals authoritative reconstruction", () => {
  const { store, service } = fixture();
  try {
    service.initialize("case:correct", "relay-sabotage");
    const correct = service.act("case:correct", "accuse:sol");
    assert.equal(correct.run.status, "solved");
    assert.equal(correct.outcome?.correct, true);
    assert.equal(correct.outcome?.culpritId, "sol");
    assert.match(correct.outcome?.reconstruction ?? "", /disabled the relay/);
    assert.equal(correct.actions.length, 0);

    service.initialize("case:wrong", "relay-sabotage");
    const wrong = service.act("case:wrong", "accuse:mira");
    assert.equal(wrong.run.status, "failed");
    assert.equal(wrong.outcome?.correct, false);
    assert.equal(wrong.outcome?.culpritId, "sol");
  } finally { store.close(); }
});

test("Casefile rejects stale or invented action identities without spending investigation time", () => {
  const { store, service } = fixture();
  try {
    service.initialize("case:admission", "relay-sabotage");
    assert.throws(() => service.act("case:admission", "confront:sol:coolant-fiber"), /not legal/);
    assert.throws(() => service.act("case:admission", "inspect:invented"), /not legal/);
    assert.equal(service.state("case:admission").run.movesRemaining, 8);
  } finally { store.close(); }
});

test("short-session Casefile recovers exactly after store reopen", () => {
  const directory = mkdtempSync(join(tmpdir(), "casefile-store-"));
  const path = join(directory, "casefile.sqlite3");
  try {
    let store = new CasefileStore(path);
    let service = new CasefileService(store);
    service.initialize("case:recover", "missing-med-cache");
    service.act("case:recover", "inspect:galley-thread");
    service.act("case:recover", "question:nera");
    const before = service.state("case:recover");
    store.close();

    store = new CasefileStore(path);
    service = new CasefileService(store);
    const after = service.state("case:recover");
    assert.deepEqual(after, before);
    assert.equal(after.run.revision, 2);
    assert.equal(after.run.movesRemaining, 6);
    store.close();
  } finally { rmSync(directory, { recursive: true, force: true }); }
});

test("when the investigation budget reaches zero only accusation commitments remain legal", () => {
  const { store, service } = fixture();
  try {
    service.initialize("case:budget", "relay-sabotage");
    const actions = [
      "inspect:archive-badge", "inspect:coolant-fiber", "inspect:dock-ratchet", "inspect:galley-reflection",
      "question:mira", "question:sol", "question:ivo", "question:nera",
    ];
    for (const action of actions) service.act("case:budget", action);
    const view = service.state("case:budget");
    assert.equal(view.run.movesRemaining, 0);
    assert.ok(view.actions.length > 0);
    assert.ok(view.actions.every((action) => action.kind === "accuse" && action.cost === 0));
    assert.match(view.statements.at(-1)?.text ?? "", /Commit an accusation/);
  } finally { store.close(); }
});
