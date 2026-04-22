'use client';

export interface AnalyzeWorkspaceResult {
  status?: string;
  decision?: string;
  summary?: string;
  risk_flags?: string[];
  recommendations?: string[];
  report_path?: string | null;
  audit_event_id?: string | null;
  workflow?: string;
  metadata?: {
    governance_decision?: string;
    governance_source?: string;
    symbol?: string;
    timeframe?: string;
    recommendation_id?: string;
    workflow_run_id?: string;
    [key: string]: unknown;
  };
}
