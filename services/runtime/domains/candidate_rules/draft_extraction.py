"""CandidateRule Draft Extraction Service.

Extracts CandidateRule drafts from Lessons marked as ``lesson_type == "rule_candidate"``
after Review completion.

Rules:
  - Only lessons with ``lesson_type == "rule_candidate"`` are processed.
  - Created CandidateRules always start in ``status == "draft"``.
  - Each draft carries ``source_refs`` including review_id, lesson_id, and
    outcome_ref when present.
  - Idempotent: the same lesson never produces a duplicate CandidateRule.
  - Fails safe: extraction errors do not block Review completion.
  - No Policy promotion, no broker/order/trade side effects.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from domains.candidate_rules.models import CandidateRule
from domains.candidate_rules.repository import CandidateRuleRepository
from shared.utils.ids import new_id

logger = logging.getLogger(__name__)


@dataclass
class DraftExtractionResult:
    """Summary of a draft extraction run."""

    lessons_scanned: int = 0
    rule_candidate_lessons: int = 0
    drafts_created: int = 0
    drafts_skipped_duplicate: int = 0
    errors: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


class CandidateRuleDraftExtractionService:
    """Extracts CandidateRule drafts from rule_candidate lessons after Review completion."""

    def __init__(self, repository: CandidateRuleRepository) -> None:
        self._repo = repository

    def extract_from_review(
        self,
        *,
        review_id: str,
        recommendation_id: str | None = None,
        lessons: list[dict],
        outcome_ref_type: str | None = None,
        outcome_ref_id: str | None = None,
    ) -> DraftExtractionResult:
        """Scan completed review lessons and create CandidateRule drafts.

        Args:
            review_id: The completed Review ID.
            recommendation_id: Optional linked Recommendation ID.
            lessons: List of lesson dicts, each with keys:
                - id (str): Lesson ID (required)
                - lesson_type (str): Lesson type (default "review_learning")
                - body (str): Lesson body text
                - tags (list[str]): Lesson tags
            outcome_ref_type: Optional outcome reference type from the Review.
            outcome_ref_id: Optional outcome reference ID from the Review.

        Returns:
            DraftExtractionResult with counts of processed lessons.
        """
        result = DraftExtractionResult(lessons_scanned=len(lessons))

        for lesson in lessons:
            lesson_id = lesson.get("id", "")
            lesson_type = lesson.get("lesson_type", "review_learning")

            if lesson_type != "rule_candidate":
                continue

            result.rule_candidate_lessons += 1

            try:
                self._extract_one(
                    lesson=lesson,
                    review_id=review_id,
                    recommendation_id=recommendation_id,
                    outcome_ref_type=outcome_ref_type,
                    outcome_ref_id=outcome_ref_id,
                    result=result,
                )
            except Exception as exc:
                msg = f"Failed to extract CandidateRule from lesson {lesson_id}: {exc}"
                logger.warning(msg)
                result.errors.append(msg)

        return result

    def _extract_one(
        self,
        *,
        lesson: dict,
        review_id: str,
        recommendation_id: str | None,
        outcome_ref_type: str | None,
        outcome_ref_id: str | None,
        result: DraftExtractionResult,
    ) -> None:
        lesson_id = lesson["id"]
        lesson_body = lesson.get("body", "")
        lesson_tags: list[str] = list(lesson.get("tags", []))

        # ── Idempotency check ──────────────────────────────────────
        existing = self._repo.find_by_lesson_id(lesson_id)
        if existing is not None:
            result.drafts_skipped_duplicate += 1
            return

        # ── Build source_refs ──────────────────────────────────────
        source_refs: list[str] = [f"review:{review_id}", f"lesson:{lesson_id}"]
        if recommendation_id:
            source_refs.append(f"recommendation:{recommendation_id}")
        if outcome_ref_type and outcome_ref_id:
            source_refs.append(f"{outcome_ref_type}:{outcome_ref_id}")

        review_ids: list[str] = [review_id]
        lesson_ids_list: list[str] = [lesson_id]
        recommendation_ids: list[str] = [recommendation_id] if recommendation_id else []

        # ── Build CandidateRule ────────────────────────────────────
        issue_key = f"lesson_{lesson_id}"
        summary = lesson_body or lesson_tags[0] if lesson_tags else f"Draft rule from lesson {lesson_id}"

        draft = CandidateRule(
            id=new_id("crule"),
            issue_key=issue_key,
            summary=summary,
            status="draft",
            recommendation_ids=tuple(recommendation_ids),
            review_ids=tuple(review_ids),
            lesson_ids=tuple(lesson_ids_list),
            knowledge_entry_ids=(),
            source_refs=tuple(source_refs),
        )

        self._repo.create(draft)
        result.drafts_created += 1
