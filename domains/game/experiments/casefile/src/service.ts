import {
  CASEFILE_PERSON_IDS,
  type CasefileAction,
  type CasefileCatalog,
  type CasefilePersonId,
  type CasefilePublicOutcome,
  type CasefilePublicView,
  type CasefileRunState,
  type CasefileStatement,
} from "./model.ts";
import {
  CASEFILE_SCENARIOS,
  DEFAULT_CASEFILE_SCENARIO_ID,
  casefilePersonName,
  casefileScenario,
} from "./content.ts";
import { CasefileStore } from "./store.ts";

function initialAskedCount(): Record<CasefilePersonId, number> {
  return Object.fromEntries(CASEFILE_PERSON_IDS.map((personId) => [personId, 0])) as Record<CasefilePersonId, number>;
}

function initialState(runId: string, scenarioId: string): CasefileRunState {
  const scenario = casefileScenario(scenarioId);
  return {
    schemaVersion: 1,
    kind: "ordivon.game.casefile-run-state",
    runId,
    scenarioId: scenario.scenarioId,
    revision: 0,
    movesRemaining: 8,
    status: "investigating",
    inspectedTraceIds: [],
    askedCount: initialAskedCount(),
    confrontedKeys: [],
    statements: [{
      sequence: 0,
      kind: "system",
      speakerId: null,
      actionId: null,
      text: scenario.hook,
    }],
    outcome: null,
  };
}

function statement(state: CasefileRunState, input: Omit<CasefileStatement, "sequence">): CasefileStatement {
  return { sequence: state.statements.length, ...input };
}

function legalActions(state: CasefileRunState): CasefileAction[] {
  if (state.status !== "investigating") return [];
  const scenario = casefileScenario(state.scenarioId);
  const actions: CasefileAction[] = [];
  if (state.movesRemaining > 0) {
    for (const trace of scenario.traces) {
      if (state.inspectedTraceIds.includes(trace.traceId)) continue;
      actions.push({ actionId: `inspect:${trace.traceId}`, kind: "inspect", label: `Inspect ${trace.label}`, personId: null, traceId: trace.traceId, cost: 1 });
    }
    for (const person of scenario.people) {
      if (state.askedCount[person.personId] >= 2) continue;
      const label = state.askedCount[person.personId] === 0 ? `Ask ${person.name} for an account` : `Press ${person.name} on the account`;
      actions.push({ actionId: `question:${person.personId}`, kind: "question", label, personId: person.personId, traceId: null, cost: 1 });
    }
    for (const traceId of state.inspectedTraceIds) {
      const trace = scenario.traces.find((entry) => entry.traceId === traceId);
      if (!trace) continue;
      const key = `${trace.subjectId}:${trace.traceId}`;
      if (state.confrontedKeys.includes(key)) continue;
      actions.push({
        actionId: `confront:${trace.subjectId}:${trace.traceId}`,
        kind: "confront",
        label: `Confront ${casefilePersonName(scenario, trace.subjectId)} with ${trace.label}`,
        personId: trace.subjectId,
        traceId: trace.traceId,
        cost: 1,
      });
    }
  }
  for (const person of scenario.people) {
    actions.push({ actionId: `accuse:${person.personId}`, kind: "accuse", label: `Accuse ${person.name}`, personId: person.personId, traceId: null, cost: 0 });
  }
  return actions;
}

function lastStatement(state: CasefileRunState, personId: CasefilePersonId): string | null {
  for (let index = state.statements.length - 1; index >= 0; index -= 1) {
    const entry = state.statements[index];
    if (entry?.speakerId === personId) return entry.text;
  }
  return null;
}

function outcomeProjection(state: CasefileRunState): CasefilePublicOutcome | null {
  if (!state.outcome) return null;
  const scenario = casefileScenario(state.scenarioId);
  return {
    accusedPersonId: state.outcome.accusedPersonId,
    accusedPersonName: casefilePersonName(scenario, state.outcome.accusedPersonId),
    correct: state.outcome.correct,
    culpritId: scenario.culpritId,
    culpritName: casefilePersonName(scenario, scenario.culpritId),
    motive: scenario.motive,
    reconstruction: scenario.reconstruction,
  };
}

function publicView(state: CasefileRunState): CasefilePublicView {
  const scenario = casefileScenario(state.scenarioId);
  return {
    schemaVersion: 1,
    kind: "ordivon.game.casefile-public-view",
    run: {
      runId: state.runId,
      scenarioId: state.scenarioId,
      revision: state.revision,
      status: state.status,
      movesRemaining: state.movesRemaining,
    },
    case: { title: scenario.title, hook: scenario.hook, setup: scenario.setup },
    people: scenario.people.map((person) => ({
      personId: person.personId,
      name: person.name,
      role: person.role,
      questioned: state.askedCount[person.personId],
      lastStatement: lastStatement(state, person.personId),
    })),
    traces: scenario.traces.map((trace) => ({
      traceId: trace.traceId,
      label: trace.label,
      location: trace.location,
      inspected: state.inspectedTraceIds.includes(trace.traceId),
      clue: state.inspectedTraceIds.includes(trace.traceId) ? trace.clue : null,
    })),
    statements: structuredClone(state.statements),
    actions: legalActions(state),
    outcome: outcomeProjection(state),
  };
}

export class CasefileService {
  readonly store: CasefileStore;
  constructor(store: CasefileStore) { this.store = store; }

  catalog(): CasefileCatalog {
    return {
      schemaVersion: 1,
      kind: "ordivon.game.casefile-catalog",
      defaultScenarioId: DEFAULT_CASEFILE_SCENARIO_ID,
      scenarios: CASEFILE_SCENARIOS.map((scenario) => ({ scenarioId: scenario.scenarioId, title: scenario.title, hook: scenario.hook })),
    };
  }

  listRuns() { return this.store.list(); }

  initialize(runId: string, scenarioId = DEFAULT_CASEFILE_SCENARIO_ID): CasefilePublicView {
    if (typeof runId !== "string" || !runId.trim()) throw new TypeError("Casefile runId must be non-empty");
    const state = initialState(runId.trim(), scenarioId);
    this.store.create(state);
    return publicView(state);
  }

  state(runId: string): CasefilePublicView { return publicView(this.store.read(runId)); }

  act(runId: string, actionId: string): CasefilePublicView {
    if (typeof actionId !== "string" || !actionId.trim()) throw new TypeError("Casefile actionId must be non-empty");
    const before = this.store.read(runId);
    const action = legalActions(before).find((candidate) => candidate.actionId === actionId);
    if (!action) throw new TypeError(`Casefile action is not legal at revision ${before.revision}: ${actionId}`);
    const state = structuredClone(before);
    const scenario = casefileScenario(state.scenarioId);

    if (action.kind === "inspect") {
      const trace = scenario.traces.find((entry) => entry.traceId === action.traceId)!;
      state.inspectedTraceIds.push(trace.traceId);
      state.statements.push(statement(state, { kind: "trace", speakerId: null, actionId, text: `${trace.label} — ${trace.clue}` }));
    } else if (action.kind === "question") {
      const personId = action.personId!;
      const behavior = scenario.behavior[personId];
      const count = state.askedCount[personId];
      const text = count === 0 ? behavior.initialStatement : behavior.repeatStatement;
      state.askedCount[personId] = count + 1;
      state.statements.push(statement(state, { kind: "testimony", speakerId: personId, actionId, text }));
    } else if (action.kind === "confront") {
      const personId = action.personId!;
      const traceId = action.traceId!;
      const behavior = scenario.behavior[personId];
      const text = behavior.confrontStatements[traceId];
      if (!text) throw new TypeError(`Casefile confrontation has no authored response: ${personId}/${traceId}`);
      state.confrontedKeys.push(`${personId}:${traceId}`);
      state.statements.push(statement(state, { kind: "confrontation", speakerId: personId, actionId, text }));
    } else {
      const accusedPersonId = action.personId!;
      const correct = accusedPersonId === scenario.culpritId;
      state.status = correct ? "solved" : "failed";
      state.outcome = { accusedPersonId, correct };
      state.statements.push(statement(state, {
        kind: "system",
        speakerId: null,
        actionId,
        text: correct
          ? `Accusation confirmed: ${casefilePersonName(scenario, accusedPersonId)} is responsible.`
          : `Accusation rejected: ${casefilePersonName(scenario, accusedPersonId)} is not responsible.`,
      }));
    }

    if (action.cost === 1) {
      if (state.movesRemaining < 1) throw new TypeError("Casefile action requires an investigation move that is no longer available");
      state.movesRemaining -= 1;
      if (state.movesRemaining === 0 && state.status === "investigating") {
        state.statements.push(statement(state, { kind: "system", speakerId: null, actionId: null, text: "Investigation window closed. Commit an accusation." }));
      }
    }

    state.revision += 1;
    this.store.save(before.revision, state);
    return publicView(state);
  }
}

export { legalActions as casefileLegalActions, publicView as casefilePublicView };
