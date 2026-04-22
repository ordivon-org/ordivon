from __future__ import annotations

from dataclasses import dataclass

from intelligence.feedback import IntelligenceFeedbackReader
from orchestrator.context.context_builder import AnalysisContext


@dataclass(frozen=True, slots=True)
class HintAwareContextBuildResult:
    context: AnalysisContext
    hint_status: str
    memory_lesson_count: int
    related_review_count: int
    hint_error: str | None = None


class HintAwareContextBuilder:
    def __init__(self, db) -> None:
        self.db = db

    def enrich(self, ctx: AnalysisContext, *, symbol: str | None) -> HintAwareContextBuildResult:
        if not self.db:
            return HintAwareContextBuildResult(
                context=ctx,
                hint_status="not_linked_yet",
                memory_lesson_count=0,
                related_review_count=0,
            )
        try:
            intelligence_feedback = IntelligenceFeedbackReader(self.db).read_for_symbol(symbol)
            if ctx.memory.policy.allow_channel("feedback_hints"):
                ctx.memory.lessons = list(intelligence_feedback.memory_lessons)
                ctx.memory.related_reviews = list(intelligence_feedback.related_reviews)
            else:
                ctx.memory.lessons = []
                ctx.memory.related_reviews = []
            return HintAwareContextBuildResult(
                context=ctx,
                hint_status="available",
                memory_lesson_count=len(intelligence_feedback.memory_lessons),
                related_review_count=len(intelligence_feedback.related_reviews),
            )
        except Exception as exc:
            ctx.memory.lessons = []
            ctx.memory.related_reviews = []
            return HintAwareContextBuildResult(
                context=ctx,
                hint_status="unavailable",
                memory_lesson_count=0,
                related_review_count=0,
                hint_error=str(exc),
            )
