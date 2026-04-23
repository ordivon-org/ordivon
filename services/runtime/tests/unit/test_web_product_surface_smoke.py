from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_dashboard_page_composes_real_v1_widgets():
    source = read("apps/web/src/app/page.tsx")

    assert "SystemStatusBar" in source
    assert "LatestDecisionList" in source
    assert "RiskSnapshot" in source
    assert "LatestReportsList" in source
    assert "EvalStatus" in source
    assert "RecentRecommendations" in source
    assert "PendingReviews" in source
    assert "ValidationHub" in source
    assert "Command Center" in source
    assert "Live command center" in source


def test_analyze_page_uses_real_api_and_honest_failure_state():
    source = read("apps/web/src/app/analyze/page.tsx")

    assert "/api/v1/analyze-and-suggest" in source
    assert "Analyze API is currently unavailable. No analysis result was generated." in source
    assert "Workflow Execution Workspace" in source
    assert "Hand off recommendation to review workbench" in source
    assert "Return to command center" in source
    assert "1. Confirm the result" in source
    assert "2. Hand off to supervision" in source
    assert "evt_offline" not in source
    assert "action_plan" not in source
    assert "thesis" not in source
    assert "decision: 'allow'" not in source


def test_gold_path_handoff_copy_and_route_intent_are_explicit():
    quick_analyze = read("apps/web/src/components/features/dashboard/QuickAnalyze.tsx")
    analyze_page = read("apps/web/src/app/analyze/page.tsx")
    recos = read("apps/web/src/components/features/dashboard/RecentRecommendations.tsx")
    pending_reviews = read("apps/web/src/components/features/dashboard/PendingReviews.tsx")

    assert "router.push(`/analyze?${params.toString()}`)" in quick_analyze
    assert "autoRun: 'true'" in quick_analyze
    assert "Hand off recommendation to review workbench" in analyze_page
    assert "Continue in review workbench" in recos
    assert "Start supervision in review workbench" in recos
    assert "Open recommendation in review workbench" in recos
    assert 'href={`/reviews?recommendation_id=${recommendation.id}`}' in recos
    assert 'href={`/reviews?review_id=${review.id}&trace_ref=${review.id}`}' in pending_reviews
    assert 'href={`/reviews?review_id=${review.id}&recommendation_id=${review.recommendation_id}`}' in pending_reviews


def test_analyze_panels_only_render_real_contract_fields():
    reasoning = read("apps/web/src/components/features/analyze/ReasoningPanel.tsx")
    governance = read("apps/web/src/components/features/analyze/GovernancePanel.tsx")

    assert "data.summary" in reasoning
    assert "data.recommendations" in reasoning
    assert "data.metadata?.symbol" in reasoning
    assert "thesis" not in reasoning
    assert "action_plan" not in reasoning
    assert "next_steps" not in reasoning

    assert "data.decision" in governance
    assert "data.risk_flags" in governance
    assert "data.audit_event_id" in governance
    assert "data.report_path" in governance
    assert "data.metadata?.governance_source" in governance


def test_audits_page_and_components_use_real_audit_api_without_sample_rows():
    page = read("apps/web/src/app/audits/page.tsx")
    summary = read("apps/web/src/components/features/audits/AuditSummary.tsx")
    listing = read("apps/web/src/components/features/audits/AuditList.tsx")

    assert "/api/v1/audits/recent" in page
    assert "ConsolePageFrame" in page
    assert "/api/v1/audits/recent?limit=20" in summary
    assert "/api/v1/audits/recent?limit=20" in listing
    assert "Open Related Tabs" in listing
    assert "useWorkspaceContext" in listing
    assert "156" not in summary
    assert "passRate" not in summary
    assert "evt_1" not in listing
    assert "BTC/USDT" not in listing


def test_dashboard_reports_validation_evals_and_reviews_use_real_v1_surfaces():
    reports_card = read("apps/web/src/components/features/dashboard/LatestReportsList.tsx")
    reports_list_page = read("apps/web/src/components/features/reports/LatestReportsList.tsx")
    validation = read("apps/web/src/components/features/validation/ValidationHub.tsx")
    evals = read("apps/web/src/components/features/dashboard/EvalStatus.tsx")
    recos = read("apps/web/src/components/features/dashboard/RecentRecommendations.tsx")
    pending_reviews = read("apps/web/src/components/features/dashboard/PendingReviews.tsx")
    review_detail = read("apps/web/src/components/features/dashboard/ReviewDetailPanel.tsx")
    system_status = read("apps/web/src/components/status/SystemStatusBar.tsx")
    decisions = read("apps/web/src/components/features/dashboard/LatestDecisionList.tsx")
    trace_panel = read("apps/web/src/components/state/TraceDetailPanel.tsx")
    semantic = read("apps/web/src/lib/semanticSignals.ts")
    reviews_page = read("apps/web/src/app/reviews/page.tsx")
    workspace_shell = read("apps/web/src/components/workspace/WorkspaceShell.tsx")
    recommendation_workspace = read("apps/web/src/components/features/reviews/RecommendationWorkspacePanel.tsx")
    dashboard_page = read("apps/web/src/app/page.tsx")
    console_frame = read("apps/web/src/components/workspace/ConsolePageFrame.tsx")
    reports_route = read("apps/web/src/app/reports/page.tsx")
    history_page = read("apps/web/src/app/history/page.tsx")

    assert "/api/v1/reports/latest?limit=5" in reports_card
    assert "/api/v1/reports/latest?limit=20" in reports_list_page
    assert "Report document not generated yet." in reports_list_page
    assert "/api/v1/validation/summary" in validation
    assert "summary.system_go_no_go" in validation
    assert "summary.metadata?.key_lessons" in validation
    assert "/api/v1/evals/latest" in evals
    assert "/api/v1/recommendations/recent" in recos
    assert "Command-center preview of recommendation objects." in recos
    assert "deep supervision and trace follow-through move into the review workbench" in recos
    assert "Continue in review workbench" in recos
    assert "Start supervision in review workbench" in recos
    assert "Open recommendation in review workbench" in recos
    assert "Trace references" in recos
    assert "Outcome signal" in recos
    assert "Knowledge hints prepared" in recos
    assert "Policy set:" in recos
    assert "honestMissingCopy('trace_detail')" in recos
    assert "semanticNote('knowledge_hint')" in recos
    assert "semanticNote('outcome_signal')" in recos
    assert "Completed learning" not in recos
    assert "Final truth" not in recos
    assert "recommendation.recommendation_id" not in recos
    assert "recommendation.lifecycle_status" not in recos
    assert "TraceDetailPanel" not in recos
    assert "Open trace tab" not in recos
    assert "Trace in audits" not in recos
    assert "Trace to reports" not in recos
    assert "Open supporting recommendation tab" in recos
    assert 'href={`/reviews?recommendation_id=${recommendation.id}`}' in recos
    assert "/api/v1/reviews/pending?limit=5" in pending_reviews
    assert "Command-center preview of supervision-needed review objects." in pending_reviews
    assert "Continue in review workbench" in pending_reviews
    assert "command-center preview" in pending_reviews
    assert "Trace references" in pending_reviews
    assert "Outcome signal" in pending_reviews
    assert "Knowledge hints prepared" in pending_reviews
    assert "honestMissingCopy('trace_detail')" in pending_reviews
    assert "honestMissingCopy('outcome_signal')" in pending_reviews
    assert "honestMissingCopy('knowledge_hint')" in pending_reviews
    assert "semanticNote('outcome_signal')" in pending_reviews
    assert "semanticNote('knowledge_hint')" in pending_reviews
    assert "ReviewDetailPanel" not in pending_reviews
    assert "Completed learning" not in pending_reviews
    assert "Final truth" not in pending_reviews
    assert "/api/v1/reviews/${reviewId}" in review_detail
    assert "Show review detail" in review_detail
    assert "Execution references" in review_detail
    assert "Latest outcome signal" in review_detail
    assert "Feedback packet signal" in review_detail
    assert "semanticNote('knowledge_hint')" in review_detail
    assert "semanticNote('outcome_signal')" in review_detail
    assert "Completed learning" not in review_detail
    assert "Final truth" not in review_detail
    assert "Trace detail for" in trace_panel
    assert "Show trace detail" in trace_panel
    assert "trustTierForSignal" in semantic
    assert "semanticNote" in semantic
    assert "honestMissingCopy" in semantic
    assert "not linked yet" in semantic
    assert "unavailable" in semantic
    assert "Not prepared yet" in semantic
    assert "This is the latest recorded outcome signal, not a fully closed loop." in semantic
    assert "These are derived signals, not state truth, policy updates, or system learning." in semantic
    assert "outcome_signal" in semantic
    assert "hint" in semantic
    assert "/api/v1/health" in system_status
    assert "health.monitoring_status" in system_status
    assert "health.recent_failed_workflow_count" in system_status
    assert "health.recent_failed_execution_count" in system_status
    assert "Last Workflow:" in system_status
    assert "Recent Failures:" in system_status
    assert "Monitoring:" in system_status
    assert "/api/v1/audits/recent?limit=1" in system_status
    assert "/api/v1/audits/recent?limit=5" in decisions
    assert "ReviewConsole" in reviews_page
    assert "ConsolePageFrame" in reviews_page
    assert "Command Center" in dashboard_page
    assert "Live command center" in dashboard_page
    assert "ConsolePageFrame" in dashboard_page
    assert "ConsolePageFrame" in reports_route
    assert "ConsolePageFrame" in history_page
    assert "WorkspaceShell" in workspace_shell
    assert "Recommendation detail" in recommendation_workspace
    assert "/api/v1/recommendations/${recommendationId}" in recommendation_workspace
    assert "Sidebar" in console_frame
