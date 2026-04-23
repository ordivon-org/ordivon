'use client';

import type { AnalyzeWorkspaceResult } from '@/components/features/analyze/types';

export function GovernanceDetailInspector({ data }: { data: AnalyzeWorkspaceResult | null }) {
  const governance = data?.metadata?.governance;
  const advisoryHintStatus =
    typeof data?.metadata?.governance_advisory_hint_status === 'string'
      ? data.metadata.governance_advisory_hint_status
      : 'not_linked_yet';
  const activePolicies = Array.isArray(data?.metadata?.governance_active_policy_ids)
    ? data?.metadata?.governance_active_policy_ids
    : [];
  const defaultRules = Array.isArray(data?.metadata?.governance_default_decision_rule_ids)
    ? data?.metadata?.governance_default_decision_rule_ids
    : [];

  return (
    <div className="glass console-card console-card--soft" style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
      <div className="console-card__title">Governance detail inspector</div>
      <div className="console-card__copy">
        Supporting governance detail only. This inspector explains the current execution decision; it does not become an independent governance console.
      </div>
      <div>Decision source: {typeof data?.metadata?.governance_source === 'string' ? data.metadata.governance_source : 'unavailable'}</div>
      <div>Policy set: {typeof data?.metadata?.governance_policy_set_id === 'string' ? data.metadata.governance_policy_set_id : 'unavailable'}</div>
      <div>Advisory hint status: {advisoryHintStatus}</div>
      <div>Active policies: {activePolicies.length > 0 ? activePolicies.join(', ') : 'unavailable'}</div>
      <div>Default decision rules: {defaultRules.length > 0 ? defaultRules.join(', ') : 'unavailable'}</div>
      {governance && typeof governance === 'object' && Array.isArray((governance as Record<string, unknown>).advisory_hints) ? (
        <div>Advisory hints attached: {((governance as Record<string, unknown>).advisory_hints as unknown[]).length}</div>
      ) : (
        <div>Advisory hints attached: unavailable</div>
      )}
    </div>
  );
}
