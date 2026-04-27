from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.app.deps import get_db
from apps.api.app.schemas.knowledge import (
    CandidateRuleResponse,
    FeedbackRecordResponse,
    KnowledgeEntryResponse,
    KnowledgePacketSummaryResponse,
    KnowledgeRefResponse,
    KnowledgeRetrieveResponse,
    RecurringIssueResponse,
)
from domains.candidate_rules.repository import CandidateRuleRepository
from domains.journal.repository import ReviewRepository
from knowledge.retrieval import KnowledgeRetrievalService

router = APIRouter()


def _to_ref_response(ref) -> KnowledgeRefResponse:
    return KnowledgeRefResponse(
        object_type=ref.object_type,
        object_id=ref.object_id,
        relation=ref.relation,
        path=ref.path,
    )


def _to_entry_response(entry) -> KnowledgeEntryResponse:
    return KnowledgeEntryResponse(
        id=entry.id,
        title=entry.title,
        narrative=entry.narrative,
        knowledge_type=entry.knowledge_type,
        confidence=entry.confidence,
        feedback_targets=list(entry.feedback_targets),
        derived_from=_to_ref_response(entry.derived_from),
        evidence_refs=[_to_ref_response(ref) for ref in entry.evidence_refs],
        created_at=entry.created_at,
    )


def _candidate_rule_responses(db: Session, issue_keys: set[str]) -> list[CandidateRuleResponse]:
    if not issue_keys:
        return []
    repository = CandidateRuleRepository(db)
    responses: list[CandidateRuleResponse] = []
    for row in repository.list_all():
        model = repository.to_model(row)
        if model.issue_key not in issue_keys:
            continue
        responses.append(
            CandidateRuleResponse(
                id=model.id,
                issue_key=model.issue_key,
                summary=model.summary,
                status=model.status,
                recommendation_ids=list(model.recommendation_ids),
                review_ids=list(model.review_ids),
                knowledge_entry_ids=list(model.knowledge_entry_ids),
                created_at=model.created_at,
            )
        )
    return responses


def _response_for(
    root_type: str, root_id: str, retrieval, recurring_issues, candidate_rules
) -> KnowledgeRetrieveResponse:
    return KnowledgeRetrieveResponse(
        root_type=root_type,
        root_id=root_id,
        entries=[_to_entry_response(entry) for entry in retrieval.entries],
        packets=[
            KnowledgePacketSummaryResponse(
                id=packet.id,
                recommendation_id=packet.recommendation_id,
                review_id=packet.review_id,
                knowledge_entry_ids=list(packet.knowledge_entry_ids),
                governance_hint_count=packet.governance_hint_count,
                intelligence_hint_count=packet.intelligence_hint_count,
            )
            for packet in retrieval.packets
        ],
        feedback_records=[
            FeedbackRecordResponse(
                id=record.id,
                packet_id=record.packet_id,
                recommendation_id=record.recommendation_id,
                review_id=record.review_id,
                consumer_type=record.consumer_type,
                subject_key=record.subject_key,
                knowledge_entry_ids=list(record.knowledge_entry_ids),
                consumed_hint_count=record.consumed_hint_count,
                created_at=record.created_at,
            )
            for record in retrieval.feedback_records
        ],
        recurring_issues=[RecurringIssueResponse(**asdict(issue)) for issue in recurring_issues],
        candidate_rules=candidate_rules,
    )


@router.get("/recommendations/{recommendation_id}", response_model=KnowledgeRetrieveResponse)
async def get_knowledge_for_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    try:
        service = KnowledgeRetrievalService(db)
        retrieval = service.retrieve_for_recommendation(recommendation_id)
        recurring_issues = service.aggregate_recurring_issues_for_recommendation(recommendation_id)
        candidate_rules = _candidate_rule_responses(db, {issue.issue_key for issue in recurring_issues})
        return _response_for("recommendation", recommendation_id, retrieval, recurring_issues, candidate_rules)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/reviews/{review_id}", response_model=KnowledgeRetrieveResponse)
async def get_knowledge_for_review(review_id: str, db: Session = Depends(get_db)):
    try:
        service = KnowledgeRetrievalService(db)
        retrieval = service.retrieve_for_review(review_id)
        review_row = ReviewRepository(db).get(review_id)
        recommendation_id = review_row.recommendation_id if review_row is not None else None
        recurring_issues = (
            service.aggregate_recurring_issues_for_recommendation(recommendation_id) if recommendation_id else ()
        )
        candidate_rules = _candidate_rule_responses(db, {issue.issue_key for issue in recurring_issues})
        return _response_for("review", review_id, retrieval, recurring_issues, candidate_rules)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
