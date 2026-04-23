'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { HealthHistoryResponse } from '@/types/api';
import { LoadingState, UnavailableState } from '@/components/state/SurfaceStates';

export function MonitoringHistoryPanel() {
  const [history, setHistory] = useState<HealthHistoryResponse | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'unavailable'>('loading');

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await apiGet<HealthHistoryResponse>('/api/v1/health/history');
        if (!cancelled) {
          setHistory(response);
          setStatus('ready');
        }
      } catch {
        if (!cancelled) {
          setHistory(null);
          setStatus('unavailable');
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === 'loading') {
    return <LoadingState message="Loading monitoring history..." />;
  }

  if (!history) {
    return (
      <UnavailableState
        message="Monitoring history is unavailable."
        detail="The operational inspector could not confirm /api/v1/health/history."
      />
    );
  }

  const blockedReasons = Object.entries(history.blocked_reason_counts ?? {});
  const recoveryActions = Object.entries(history.recovery_action_counts ?? {});

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <div className="glass console-card console-card--soft" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
        <div>
          <div className="console-card__title">Blocked / Stale Runs</div>
          <div className="console-card__copy">{history.stale_or_blocked_run_count}</div>
        </div>
        <div>
          <div className="console-card__title">Approval Blocked</div>
          <div className="console-card__copy">{history.approval_blocked_count}</div>
        </div>
        <div>
          <div className="console-card__title">Top Workflow Failure</div>
          <div className="console-card__copy">{history.top_workflow_failure_type ?? 'unavailable'}</div>
        </div>
        <div>
          <div className="console-card__title">Top Execution Failure</div>
          <div className="console-card__copy">{history.top_execution_failure_family ?? 'unavailable'}</div>
        </div>
      </div>

      <div className="glass console-card" style={{ display: 'grid', gap: '0.75rem' }}>
        <div className="console-card__title">Blocked Reason Summary</div>
        {blockedReasons.length > 0 ? (
          blockedReasons.map(([reason, count]) => (
            <div key={reason} className="console-card__copy">
              {reason}: {count}
            </div>
          ))
        ) : (
          <div className="console-card__copy">No blocked reason counts were reported.</div>
        )}
      </div>

      <div className="glass console-card" style={{ display: 'grid', gap: '0.75rem' }}>
        <div className="console-card__title">Recovery Actions</div>
        {recoveryActions.length > 0 ? (
          recoveryActions.map(([action, count]) => (
            <div key={action} className="console-card__copy">
              {action}: {count}
            </div>
          ))
        ) : (
          <div className="console-card__copy">No recovery actions were recorded in the current history window.</div>
        )}
      </div>

      <div className="glass console-card" style={{ display: 'grid', gap: '0.75rem' }}>
        <div className="console-card__title">Scheduler Trigger Activity</div>
        <div className="console-card__copy">
          Total: {history.scheduler?.total_trigger_count ?? 0} | Enabled: {history.scheduler?.enabled_trigger_count ?? 0} | Dispatched: {history.scheduler?.dispatched_trigger_count ?? 0}
        </div>
      </div>
    </div>
  );
}
