'use client';

import { useEffect, useState } from 'react';

export default function EvalStatus() {
  const [evalData, setEvalData] = useState<any>(null);

  useEffect(() => {
    // 实际应调用 /api/v1/evals/latest
    // 模拟数据展示 Step 8.4 成果
    const mockData = {
      run_id: "2026-04-17_run_012001",
      gate_decision: "PASS",
      summary: {
        avg_total_score: 0.9,
        parse_failure_rate: 0.0,
        aggressive_action_rate: 0.08
      }
    };
    setEvalData(mockData);
  }, []);

  if (!evalData) return <div>Loading eval status...</div>;

  return (
    <div className="eval-status glass" style={{
      padding: '1.25rem',
      borderRadius: '12px',
      height: '100%',
      borderLeft: '4px solid var(--primary)'
    }}>
      <h3 style={{ marginBottom: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>📊 Evaluation Quality</h3>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--foreground)' }}>
            {Math.round(evalData.summary.avg_total_score * 100)}%
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>QUALITY SCORE</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span className={`badge badge-${evalData.gate_decision.toLowerCase()}`}>
            {evalData.gate_decision}
          </span>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '4px' }}>GATE STATUS</div>
        </div>
      </div>

      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Parse Failure:</span>
          <span style={{ color: evalData.summary.parse_failure_rate > 0.05 ? 'var(--error)' : 'var(--success)' }}>
            {(evalData.summary.parse_failure_rate * 100).toFixed(1)}%
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Aggressive Action:</span>
          <span style={{ color: evalData.summary.aggressive_action_rate > 0.15 ? 'var(--warn)' : 'var(--foreground)' }}>
            {(evalData.summary.aggressive_action_rate * 100).toFixed(1)}%
          </span>
        </div>
        <div style={{ marginTop: '4px', textAlign: 'center', opacity: 0.6 }}>
          Run ID: {evalData.run_id.slice(-8)}
        </div>
      </div>
    </div>
  );
}
