from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from domains.journal.repository import ReviewRepository
from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from domains.research.orm import AnalysisORM
from domains.strategy.orm import RecommendationORM
from knowledge.extraction import LessonExtractionService
from knowledge.models import KnowledgeEntry


@dataclass(frozen=True, slots=True)
class KnowledgePacketSummary:
    id: str
    recommendation_id: str
    review_id: str | None
    knowledge_entry_ids: tuple[str, ...] = field(default_factory=tuple)
    governance_hint_count: int = 0
    intelligence_hint_count: int = 0


@dataclass(frozen=True, slots=True)
class KnowledgeRetrievalResult:
    entries: tuple[KnowledgeEntry, ...] = field(default_factory=tuple)
    packets: tuple[KnowledgePacketSummary, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RecurringIssueSummary:
    issue_key: str
    occurrence_count: int
    sample_narratives: tuple[str, ...] = field(default_factory=tuple)
    recommendation_ids: tuple[str, ...] = field(default_factory=tuple)
    review_ids: tuple[str, ...] = field(default_factory=tuple)
    knowledge_entry_ids: tuple[str, ...] = field(default_factory=tuple)


class RecurringIssueAggregator:
    def aggregate(self, entries: tuple[KnowledgeEntry, ...]) -> tuple[RecurringIssueSummary, ...]:
        grouped: dict[str, dict[str, object]] = {}
        for entry in entries:
            key = self.normalize_issue_key(entry.narrative)
            if not key:
                continue
            bucket = grouped.setdefault(
                key,
                {
                    "narratives": [],
                    "recommendation_ids": set(),
                    "review_ids": set(),
                    "knowledge_entry_ids": set(),
                },
            )
            narratives = bucket["narratives"]
            if isinstance(narratives, list) and entry.narrative not in narratives:
                narratives.append(entry.narrative)
            recommendation_ids = bucket["recommendation_ids"]
            review_ids = bucket["review_ids"]
            knowledge_entry_ids = bucket["knowledge_entry_ids"]
            if isinstance(knowledge_entry_ids, set):
                knowledge_entry_ids.add(entry.id)
            for ref in entry.evidence_refs:
                if ref.object_type == "recommendation" and isinstance(recommendation_ids, set):
                    recommendation_ids.add(ref.object_id)
                if ref.object_type == "review" and isinstance(review_ids, set):
                    review_ids.add(ref.object_id)

        summaries = [
            RecurringIssueSummary(
                issue_key=issue_key,
                occurrence_count=len(data["knowledge_entry_ids"]),
                sample_narratives=tuple(data["narratives"][:3]),
                recommendation_ids=tuple(sorted(data["recommendation_ids"])),
                review_ids=tuple(sorted(data["review_ids"])),
                knowledge_entry_ids=tuple(sorted(data["knowledge_entry_ids"])),
            )
            for issue_key, data in grouped.items()
        ]
        return tuple(sorted(summaries, key=lambda item: (-item.occurrence_count, item.issue_key)))

    @staticmethod
    def normalize_issue_key(text: str) -> str:
        normalized = re.sub(r"[^a-z0-9\s]+", " ", text.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized


class KnowledgeRetrievalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.extraction_service = LessonExtractionService(db)
        self.review_repository = ReviewRepository(db)
        self.packet_repository = KnowledgeFeedbackPacketRepository(db)
        self.recurring_issue_aggregator = RecurringIssueAggregator()

    def retrieve_for_recommendation(self, recommendation_id: str) -> KnowledgeRetrievalResult:
        entries = tuple(self.extraction_service.extract_for_recommendation(recommendation_id))
        packet_rows = self.packet_repository.list_for_recommendations([recommendation_id], limit=10)
        packets = tuple(self._packet_summary(row) for row in packet_rows)
        return KnowledgeRetrievalResult(entries=entries, packets=packets)

    def retrieve_for_review(self, review_id: str) -> KnowledgeRetrievalResult:
        review = self.review_repository.get(review_id)
        if review is None or review.recommendation_id is None:
            return KnowledgeRetrievalResult()
        result = self.retrieve_for_recommendation(review.recommendation_id)
        packets = tuple(packet for packet in result.packets if packet.review_id == review_id)
        return KnowledgeRetrievalResult(entries=result.entries, packets=packets)

    def retrieve_for_symbol(self, symbol: str) -> KnowledgeRetrievalResult:
        recommendation_ids = tuple(
            row.id
            for row in (
                self.db.query(RecommendationORM)
                .join(AnalysisORM, AnalysisORM.id == RecommendationORM.analysis_id)
                .filter(AnalysisORM.symbol == symbol)
                .order_by(RecommendationORM.created_at.desc())
                .all()
            )
        )
        if not recommendation_ids:
            return KnowledgeRetrievalResult()

        entries: list[KnowledgeEntry] = []
        packets: list[KnowledgePacketSummary] = []
        seen_entry_ids: set[str] = set()
        seen_packet_ids: set[str] = set()

        for recommendation_id in recommendation_ids:
            result = self.retrieve_for_recommendation(recommendation_id)
            for entry in result.entries:
                if entry.id in seen_entry_ids:
                    continue
                seen_entry_ids.add(entry.id)
                entries.append(entry)
            for packet in result.packets:
                if packet.id in seen_packet_ids:
                    continue
                seen_packet_ids.add(packet.id)
                packets.append(packet)

        return KnowledgeRetrievalResult(entries=tuple(entries), packets=tuple(packets))

    def aggregate_recurring_issues_for_symbol(self, symbol: str) -> tuple[RecurringIssueSummary, ...]:
        retrieval = self.retrieve_for_symbol(symbol)
        if not retrieval.entries:
            return ()
        return self._aggregate_entries(retrieval.entries)

    def aggregate_recurring_issues_for_recommendation(
        self,
        recommendation_id: str,
    ) -> tuple[RecurringIssueSummary, ...]:
        retrieval = self.retrieve_for_recommendation(recommendation_id)
        if not retrieval.entries:
            return ()
        return self._aggregate_entries(retrieval.entries)

    def _aggregate_entries(
        self,
        entries: tuple[KnowledgeEntry, ...],
    ) -> tuple[RecurringIssueSummary, ...]:
        return self.recurring_issue_aggregator.aggregate(entries)

    def _packet_summary(self, row) -> KnowledgePacketSummary:
        packet = self.packet_repository.to_model(row)
        return KnowledgePacketSummary(
            id=packet.id,
            recommendation_id=packet.recommendation_id,
            review_id=packet.review_id,
            knowledge_entry_ids=tuple(packet.knowledge_entry_ids),
            governance_hint_count=len(packet.governance_hints),
            intelligence_hint_count=len(packet.intelligence_hints),
        )

