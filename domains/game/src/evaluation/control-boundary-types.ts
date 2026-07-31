export type BoundaryPhase = "pre-commit" | "post-commit" | "terminal";

export interface BoundaryArmResult {
  shouldAct: boolean;
  acted: boolean;
  correct: boolean;
  phase: BoundaryPhase;
  reasonCode: string;
  worldEvents: number;
  hostEffects: number;
  duplicateEffects: number;
  modelCalls: number;
  authorityChecks: number;
  operatorInterventions: number;
  taskState: string;
  details: Record<string, string | number | boolean | null>;
}

export interface BoundaryPairResult {
  id: string;
  changedCondition: string;
  act: BoundaryArmResult;
  hold: BoundaryArmResult;
}

export interface ControlBoundaryReport {
  schemaVersion: 1;
  kind: "ordivon.game.control-boundary-evaluation";
  sourceRevision: string;
  pairs: BoundaryPairResult[];
  metrics: {
    pairCount: number;
    shouldActSuccess: number;
    shouldHoldAccuracy: number;
    preCommitCorrectHolds: number;
    postCommitCorrectRefusals: number;
    terminalCorrectHolds: number;
    falseCompletions: number;
    duplicateEffects: number;
    operatorInterventions: number;
    totalModelCalls: number;
    totalAuthorityChecks: number;
  };
  dispositions: {
    newControlPlatform: "not-required";
    falseCompletionInvariant: "retain-in-embedded-host-authority";
    terminalTaskInvariant: "retain-in-team-store";
    existingMechanisms: "retain-and-compose";
  };
}
