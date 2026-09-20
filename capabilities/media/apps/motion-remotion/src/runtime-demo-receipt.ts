import rawReceipt from '../../../productions/runtime-introduction/evidence/runtime-demo.receipt.json';

export interface RuntimeDemoReceipt {
  schemaVersion: 1;
  kind: 'ordivon-runtime-demo-receipt';
  status: 'passed';
  protocolVersion: string;
  toolCatalogDigest: string;
  source: {revision: string};
  workspace: {
    workspaceId: string;
    sourceRevision: string;
    sourceStateDigest: string;
    closed: true;
  };
  patch: {
    clientRequestId: string;
    operationId: string;
    requestDigest: string;
    replayed: false;
    files: string[];
  };
  execution: {
    clientRequestId: string;
    jobId: string;
    attemptId: string;
    sameJobAfterReplay: true;
    recoveredByTaskList: true;
    status: 'succeeded';
    exitCode: 0;
    elapsedMs: number;
    observations: Array<{
      status: string;
      completedSteps: number;
      totalSteps: number;
      currentStepId?: string;
      currentStepIndex?: number;
      progressRevision?: number;
      elapsedMs?: number;
      exitCode?: number;
    }>;
  };
  evidence: {
    artifactId: string;
    digest: string;
    jobId: string;
    attemptId: string;
    workspaceId: string;
    sourceRevision: string;
    executionDisposition: string;
    deliveryDisposition: string;
    processTreeDisposition: string;
    reasonCode: string;
  };
  diff: {
    changedPaths: string[];
    modifiedPaths: string[];
    truncated: boolean;
    digest: string | null;
  };
  close: {
    removed: true;
    sourceStateDigest: string;
    exactStateMatched: true;
  };
  presentation: Array<{kind: string; detail: string}>;
}

export const runtimeDemoReceipt = rawReceipt as RuntimeDemoReceipt;

export function compactProofValue(value: string, head = 14, tail = 8): string {
  if (value.length <= head + tail + 1) return value;
  return `${value.slice(0, head)}…${value.slice(-tail)}`;
}
