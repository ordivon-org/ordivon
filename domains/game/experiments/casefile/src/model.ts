export const CASEFILE_PERSON_IDS = ["mira", "sol", "ivo", "nera"] as const;
export type CasefilePersonId = (typeof CASEFILE_PERSON_IDS)[number];

export type CasefileStatus = "investigating" | "solved" | "failed";

export interface CasefilePersonDefinition {
  personId: CasefilePersonId;
  name: string;
  role: string;
}

export interface CasefileTraceDefinition {
  traceId: string;
  label: string;
  location: string;
  subjectId: CasefilePersonId;
  clue: string;
}

export interface CasefilePersonBehavior {
  initialStatement: string;
  repeatStatement: string;
  confrontStatements: Record<string, string>;
}

export interface CasefileScenarioDefinition {
  scenarioId: string;
  title: string;
  hook: string;
  setup: string;
  culpritId: CasefilePersonId;
  motive: string;
  reconstruction: string;
  people: CasefilePersonDefinition[];
  traces: CasefileTraceDefinition[];
  behavior: Record<CasefilePersonId, CasefilePersonBehavior>;
}

export interface CasefileStatement {
  sequence: number;
  kind: "system" | "trace" | "testimony" | "confrontation";
  speakerId: CasefilePersonId | null;
  actionId: string | null;
  text: string;
}

export interface CasefileOutcome {
  accusedPersonId: CasefilePersonId;
  correct: boolean;
}

export interface CasefileRunState {
  schemaVersion: 1;
  kind: "ordivon.game.casefile-run-state";
  runId: string;
  scenarioId: string;
  revision: number;
  movesRemaining: number;
  status: CasefileStatus;
  inspectedTraceIds: string[];
  askedCount: Record<CasefilePersonId, number>;
  confrontedKeys: string[];
  statements: CasefileStatement[];
  outcome: CasefileOutcome | null;
}

export type CasefileActionKind = "inspect" | "question" | "confront" | "accuse";

export interface CasefileAction {
  actionId: string;
  kind: CasefileActionKind;
  label: string;
  personId: CasefilePersonId | null;
  traceId: string | null;
  cost: 0 | 1;
}

export interface CasefilePublicPerson {
  personId: CasefilePersonId;
  name: string;
  role: string;
  questioned: number;
  lastStatement: string | null;
}

export interface CasefilePublicTrace {
  traceId: string;
  label: string;
  location: string;
  inspected: boolean;
  clue: string | null;
}

export interface CasefilePublicOutcome {
  accusedPersonId: CasefilePersonId;
  accusedPersonName: string;
  correct: boolean;
  culpritId: CasefilePersonId;
  culpritName: string;
  motive: string;
  reconstruction: string;
}

export interface CasefilePublicView {
  schemaVersion: 1;
  kind: "ordivon.game.casefile-public-view";
  run: {
    runId: string;
    scenarioId: string;
    revision: number;
    status: CasefileStatus;
    movesRemaining: number;
  };
  case: {
    title: string;
    hook: string;
    setup: string;
  };
  people: CasefilePublicPerson[];
  traces: CasefilePublicTrace[];
  statements: CasefileStatement[];
  actions: CasefileAction[];
  outcome: CasefilePublicOutcome | null;
}

export interface CasefileCatalogEntry {
  scenarioId: string;
  title: string;
  hook: string;
}

export interface CasefileCatalog {
  schemaVersion: 1;
  kind: "ordivon.game.casefile-catalog";
  defaultScenarioId: string;
  scenarios: CasefileCatalogEntry[];
}
