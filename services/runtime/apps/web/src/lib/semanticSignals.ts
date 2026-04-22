import type { TrustTier } from '@/types/experience';

export type SemanticSignalKind = 'trace_detail' | 'outcome_signal' | 'knowledge_hint' | 'report_artifact';

export function trustTierForSignal(kind: SemanticSignalKind): TrustTier {
  if (kind === 'trace_detail') {
    return 'fact';
  }
  if (kind === 'outcome_signal') {
    return 'outcome_signal';
  }
  if (kind === 'knowledge_hint') {
    return 'hint';
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

export function tierLabel(tier: TrustTier): string {
  if (tier === 'fact') {
    return 'Fact Record';
  }
  if (tier === 'artifact') {
    return 'System Artifact';
  }
  if (tier === 'outcome_signal') {
    return 'Outcome Signal';
  }
  if (tier === 'hint') {
    return 'Derived Hint';
  }
  if (tier === 'missing') {
    return 'Missing';
  }
  return 'Unavailable';
}
