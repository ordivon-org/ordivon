# Execution Action Catalog

## Status

This document records the current execution action universe for PFIOS as of `2026-04-19`.

It complements the code-backed catalog in [execution/catalog.py](../../execution/catalog.py).

Use this document to answer:

**which current actions are real execution actions, how consequential are they, and which families should receive request/receipt modeling first?**

## Classification Rules

- An execution action performs or records a concrete write, artifact write, audit write, or operational write.
- Intelligence reasoning alone is not an execution action.
- In-memory rendering without persistence is not a consequential execution action by itself.
- A state mutation may still be execution-relevant if it represents a concrete system action rather than pure read-model assembly.

## Current Action Families

| Action | Family | Side-Effect Level | Boundary Status | Owner Path | State Targets | Receipt Priority |
| --- | --- | --- | --- | --- | --- | --- |
| `analysis_persist` | analysis | `state_mutation` | covered | `orchestrator.workflows.analyze.PersistAnalysisStep` | `analyses` | no |
| `recommendation_generate` | recommendation | `state_mutation` | covered | `orchestrator.workflows.analyze.GenerateRecommendationStep` | `recommendations` | yes |
| `usage_snapshot_write` | usage | `operational_write` | covered | `orchestrator.workflows.analyze.RecordUsageStep` | `usage_snapshots` | no |
| `analysis_audit_write` | audit | `audit_write` | covered | `orchestrator.workflows.analyze.AuditTrailStep` | `audit_events` | no |
| `recommendation_audit_write` | audit | `audit_write` | covered | `orchestrator.workflows.analyze.AuditTrailStep` | `audit_events` | no |
| `analysis_report_render` | report | `artifact_write` | not covered | `orchestrator.workflows.analyze.RenderReportStep` | none | no |
| `analysis_report_write` | report | `artifact_write` | covered | `orchestrator.workflows.analyze.WriteWikiStep` | `wiki/reports/*.md` | yes |
| `analysis_metadata_update` | analysis | `state_mutation` | covered | `orchestrator.workflows.analyze.WriteWikiStep` | `analyses.metadata` | yes |
| `analysis_report_audit_write` | audit | `audit_write` | covered | `orchestrator.workflows.analyze.WriteWikiStep` | `audit_events` | no |
| `recommendation_status_update` | recommendation | `state_mutation` | covered | `domains.strategy.service.RecommendationService.transition` | `recommendations`, `audit_events` | yes |
| `review_submit` | review | `state_mutation` | covered | `domains.journal.service.ReviewService.create` | `reviews`, `audit_events` | yes |
| `review_complete` | review | `state_mutation` | covered | `domains.journal.service.ReviewService.complete_review` | `reviews`, `lessons`, `audit_events` | yes |
| `validation_issue_report` | validation | `state_mutation` | covered | `domains.journal.issue_service.IssueService.create` | `issues`, `audit_events` | yes |
| `validation_usage_sync` | validation | `operational_write` | covered | `capabilities.diagnostic.validation.ValidationCapability.sync_usage` | `usage_snapshots` | no |
| `intelligence_run_write` | intelligence | `operational_write` | partially_covered | `domains.intelligence_runs.service.IntelligenceRunService` | `intelligence_runs` | yes |
| `agent_action_write` | intelligence | `state_mutation` | partially_covered | `domains.ai_actions.service.AgentActionService` | `agent_actions` | yes |

## First Request / Receipt Candidate Families

These are the best first families for request/receipt modeling:

1. `recommendation_generate`
2. `analysis_report_write`
3. `analysis_metadata_update`
4. `recommendation_status_update`
5. `review_submit`
6. `review_complete`
7. `validation_issue_report`
8. `intelligence_run_write`
9. `agent_action_write`

## Notes

- `analysis_report_render` remains in the catalog to avoid hiding it, but it is not yet treated as a consequential write because it returns an in-memory dict only.
- `intelligence_run_write` and `agent_action_write` are execution-relevant but still await full receipt modeling.
- This catalog should be treated as the source list for the upcoming execution request/receipt module.
