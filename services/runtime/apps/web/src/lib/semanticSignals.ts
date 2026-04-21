export type SemanticSignalKind = 'trace_detail' | 'outcome_signal' | 'knowledge_hint' | 'report_artifact';

export function trustTierForSignal(kind: SemanticSignalKind): 'relation' | 'signal' | 'derived' | 'artifact' {
  if (kind === 'trace_detail') {
    return 'relation';
  }
  if (kind === 'outcome_signal') {
    return 'signal';
  }
  if (kind === 'knowledge_hint') {
    return 'derived';
  }
  return 'artifact';
}

export function semanticNote(kind: SemanticSignalKind): string {
  if (kind === 'trace_detail') {
    return 'This is relation detail from the trace bundle. Missing links remain missing.';
  }
  if (kind === 'outcome_signal') {
    return 'This is the latest recorded outcome signal, not a fully closed loop.';
  }
  if (kind === 'knowledge_hint') {
    return 'These are derived signals, not state truth, policy updates, or system learning.';
  }
  return 'This is a system artifact reference, not a fact record.';
}

export function honestMissingCopy(kind: SemanticSignalKind): string {
  if (kind === 'trace_detail') {
    return 'not linked yet';
  }
  if (kind === 'outcome_signal') {
    return 'unavailable';
  }
  if (kind === 'knowledge_hint') {
    return 'Not prepared yet';
  }
  return 'unavailable';
}
