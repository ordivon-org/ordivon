from typing import Any
from state.usage.models import UsageSnapshot
from state.usage.repository import UsageSnapshotRepository


class UsageService:
    def __init__(self, repository: UsageSnapshotRepository) -> None:
        self.repository = repository

    def create(self, snapshot: UsageSnapshot):
        return self.repository.create(snapshot)

    def list_recent(self, limit: int = 30):
        return self.repository.list_recent(limit=limit)

    def get_aggregate_metrics(self, issue_repo: Any, limit: int = 7) -> dict:
        usage_rows = self.list_recent(limit=limit)
        open_issues = issue_repo.list_open()

        days_used = len(usage_rows)
        analysis_count = sum(row.analyses_count for row in usage_rows)
        recommendations_count = sum(row.recommendations_generated_count for row in usage_rows)
        reviews_count = sum(row.reviews_completed_count for row in usage_rows)
        open_p0_count = sum(1 for row in open_issues if row.severity == "p0")
        open_p1_count = sum(1 for row in open_issues if row.severity == "p1")

        key_lessons = []
        from shared.utils.serialization import from_json_text

        for row in usage_rows:
            metadata = from_json_text(row.metadata_json, {})
            note = metadata.get("note") or metadata.get("last_symbol")
            if note:
                key_lessons.append(str(note))

        return {
            "days_used": days_used,
            "analysis_count": analysis_count,
            "recommendations_count": recommendations_count,
            "reviews_count": reviews_count,
            "open_p0_count": open_p0_count,
            "open_p1_count": open_p1_count,
            "key_lessons": key_lessons[:5],
            "go_no_go": "stabilize_more" if open_p0_count or open_p1_count else "continue",
        }
