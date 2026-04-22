from __future__ import annotations

from domains.candidate_rules.models import CandidateRule
from domains.candidate_rules.repository import CandidateRuleRepository
from knowledge.retrieval import RecurringIssueSummary


class CandidateRuleService:
    def __init__(self, repository: CandidateRuleRepository) -> None:
        self.repository = repository

    def create_from_recurring_issue(self, issue: RecurringIssueSummary):
        summary = issue.sample_narratives[0] if issue.sample_narratives else issue.issue_key
        return self.repository.create(
            CandidateRule(
                issue_key=issue.issue_key,
                summary=summary,
                status="draft",
                recommendation_ids=issue.recommendation_ids,
                review_ids=issue.review_ids,
                knowledge_entry_ids=issue.knowledge_entry_ids,
            )
        )
