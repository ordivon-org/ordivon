export interface RecommendationItem {
  id: string;
  status: string;
  created_at: string;
  analysis_id: string | null;
  symbol: string | null;
  action_summary: string | null;
  confidence: number | null;
  decision: string | null;
  decision_reason: string | null;
  adopted: boolean;
  review_status: string | null;
  outcome_status: string | null;
  metadata: Record<string, unknown>;
}

export interface RecommendationListResponse {
  recommendations: RecommendationItem[];
}

export interface HealthHistoryResponse {
  workflow_failures_by_type: Record<string, number>;
  execution_failures_by_family: Record<string, number>;
  stale_or_blocked_run_count: number;
  approval_blocked_count: number;
  blocked_reason_counts?: Record<string, number> | null;
  recovery_action_counts?: Record<string, number> | null;
  top_workflow_failure_type?: string | null;
  top_execution_failure_family?: string | null;
  blocked_run_ids: string[];
  recent_workflow_failures: Array<Record<string, string>>;
  recent_execution_failures: Array<Record<string, string>>;
  blocked_runs: Array<{ run_id: string; blocked_reason: string }>;
  approval_blocked_run_ids: string[];
  scheduler?: {
    total_trigger_count: number;
    enabled_trigger_count: number;
    disabled_trigger_count: number;
    dispatched_trigger_count: number;
  } | null;
}

export interface ValidationMetrics {
  days_used: number;
  analysis_count: number;
  recommendations_count: number;
  reviews_count: number;
  open_p0_count: number;
  open_p1_count: number;
  key_lessons: string[];
  go_no_go: string;
}

export interface ValidationSummaryResponse {
  period_id: string | null;
  days_active: number;
  total_analyses: number;
  total_recommendations: number;
  open_critical_issues: number;
  system_go_no_go: string;
  metrics: ValidationMetrics | null;
  metadata: {
    key_lessons?: string[];
  };
}

export interface EvalSummary {
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  avg_total_score: number;
  parse_failure_rate: number;
  aggressive_action_rate: number;
}

export interface EvalCaseResult {
  case_id: string;
  status: string;
  risk_decision: string;
  scores: Record<string, unknown>;
  notes: string[];
}

export interface EvalRunResponse {
  run_id: string;
  timestamp: string;
  provider: string;
  dataset: string;
  summary: EvalSummary;
  cases: EvalCaseResult[];
  gate_decision: string;
}

export interface ReportItem {
  report_id: string;
  symbol: string | null;
  title: string;
  status: string;
  report_path: string | null;
  created_at: string;
  metadata: {
    query?: string | null;
  };
}

export interface ReportListResponse {
  reports: ReportItem[];
}

export interface DashboardOutcome {
  state: string;
  reason: string;
  symbol: string;
  timestamp: string;
}

export interface DashboardSummaryResponse {
  recommendation_stats: Record<string, number>;
  recent_outcomes: DashboardOutcome[];
  pending_review_count: number;
  system_health: string | null;
  reasoning_provider?: string | null;
  runtime_status?: string | null;
  hermes_status?: string | null;
  last_agent_action?: {
    id: string;
    task_type: string;
    status: string;
    provider: string | null;
    model: string | null;
    created_at: string;
  } | null;
  total_balance_estimate: number | null;
}

export interface AuditEvent {
  event_id: string;
  workflow_name: string;
  stage: string;
  decision: string;
  subject_id: string | null;
  status: string;
  context_summary: string;
  details: Record<string, unknown>;
  report_path: string | null;
  created_at: string;
}

export interface AuditListResponse {
  status: string;
  message?: string | null;
  audits: AuditEvent[];
}

export interface HealthResponse {
  status: string;
  system?: string;
  version?: string;
  reasoning_provider?: string | null;
  runtime_status?: string | null;
  runtime_detail?: string | null;
  runtime_base_url?: string | null;
  hermes_status?: string | null;
  hermes_detail?: string | null;
  hermes_base_url?: string | null;
  runtime_provider?: string | null;
  runtime_model?: string | null;
  monitoring_status?: string | null;
  monitoring_detail?: string | null;
  monitoring_window_hours?: number | null;
  recent_failed_workflow_count?: number | null;
  recent_failed_execution_count?: number | null;
  last_workflow_at?: string | null;
  last_audit_at?: string | null;
  workflow_failures_by_type?: Record<string, number> | null;
  execution_failures_by_family?: Record<string, number> | null;
  stale_or_blocked_run_count?: number | null;
  approval_blocked_count?: number | null;
}

export interface PendingReviewItem {
  id: string;
  recommendation_id: string | null;
  review_type: string;
  status: string;
  expected_outcome: string | null;
  created_at: string;
  workflow_run_id: string | null;
  intelligence_run_id: string | null;
  recommendation_generate_receipt_id: string | null;
  latest_outcome_status: string | null;
  latest_outcome_reason: string | null;
  knowledge_hint_count: number;
}

export interface PendingReviewListResponse {
  reviews: PendingReviewItem[];
}

export interface ReviewDetailResponse {
  id: string;
  recommendation_id: string | null;
  review_type: string;
  status: string;
  expected_outcome: string | null;
  observed_outcome: string | null;
  verdict: string | null;
  variance_summary: string | null;
  cause_tags: string[];
  lessons: string[];
  followup_actions: string[];
  created_at: string;
  completed_at: string | null;
  submit_execution_request_id: string | null;
  submit_execution_receipt_id: string | null;
  complete_execution_request_id: string | null;
  complete_execution_receipt_id: string | null;
  latest_outcome_status: string | null;
  latest_outcome_reason: string | null;
  knowledge_feedback_packet_id: string | null;
  governance_hint_count: number;
  intelligence_hint_count: number;
  metadata: Record<string, unknown>;
}

export interface TraceReferenceResponse {
  object_type: string;
  object_id: string | null;
  status: string;
  relation_source: string;
  detail: Record<string, unknown>;
}

export interface TraceBundleResponse {
  root_type: string;
  root_id: string;
  analysis: TraceReferenceResponse;
  recommendation: TraceReferenceResponse;
  review: TraceReferenceResponse;
  workflow_run: TraceReferenceResponse;
  intelligence_run: TraceReferenceResponse;
  agent_action: TraceReferenceResponse;
  execution_request: TraceReferenceResponse;
  execution_receipt: TraceReferenceResponse;
  review_execution_request: TraceReferenceResponse;
  review_execution_receipt: TraceReferenceResponse;
  latest_audit_events: TraceReferenceResponse[];
  report_artifact: TraceReferenceResponse;
  outcome: TraceReferenceResponse;
  knowledge_feedback: TraceReferenceResponse;
}

export interface KnowledgeRefResponse {
  object_type: string;
  object_id: string;
  relation: string;
  path?: string | null;
}

export interface KnowledgeEntryResponse {
  id: string;
  title: string;
  narrative: string;
  knowledge_type: string;
  confidence: number;
  feedback_targets: string[];
  derived_from: KnowledgeRefResponse;
  evidence_refs: KnowledgeRefResponse[];
  created_at: string;
}

export interface KnowledgePacketSummaryResponse {
  id: string;
  recommendation_id: string;
  review_id?: string | null;
  knowledge_entry_ids: string[];
  governance_hint_count: number;
  intelligence_hint_count: number;
}

export interface RecurringIssueResponse {
  issue_key: string;
  occurrence_count: number;
  sample_narratives: string[];
  recommendation_ids: string[];
  review_ids: string[];
  knowledge_entry_ids: string[];
}

export interface CandidateRuleResponse {
  id: string;
  issue_key: string;
  summary: string;
  status: string;
  recommendation_ids: string[];
  review_ids: string[];
  knowledge_entry_ids: string[];
  created_at: string;
}

export interface KnowledgeRetrieveResponse {
  root_type: string;
  root_id: string;
  advisory_only: boolean;
  entries: KnowledgeEntryResponse[];
  packets: KnowledgePacketSummaryResponse[];
  recurring_issues: RecurringIssueResponse[];
  candidate_rules: CandidateRuleResponse[];
}
