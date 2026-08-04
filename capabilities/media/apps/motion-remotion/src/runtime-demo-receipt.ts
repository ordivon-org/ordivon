import rawReceipt from '../../../productions/runtime-introduction/evidence/runtime-demo.receipt.json';

export interface RuntimeDemoReceipt {
  schemaVersion: 1;
  kind: 'ordivon-runtime-demo-receipt';
  status: 'passed';
  source: {revision: string};
  workspace: {
    workspaceId: string;
    sourceRevision: string;
    sourceStateDigest: string;
    closed: true;
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
    }>;
  };
  evidence: {
    artifactId: string;
    digest: string;
    jobId: string;
    attemptId: string;
    workspaceId: string;
    sourceRevision: string;
  };
  diff: {
    changedPaths: string[];
    modifiedPaths: string[];
  };
  close: {
    removed: true;
    sourceStateDigest: string;
    exactStateMatched: true;
  };
}

export const runtimeDemoReceipt = rawReceipt as RuntimeDemoReceipt;

export function compactProofValue(value: string, head = 14, tail = 8): string {
  if (value.length <= head + tail + 1) return value;
  return `${value.slice(0, head)}…${value.slice(-tail)}`;
}
