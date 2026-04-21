from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.app.deps import get_db
from apps.api.app.schemas.traces import TraceBundleResponse, TraceReferenceResponse
from state.trace import TraceBundle, TraceReference, TraceService

router = APIRouter()


def _to_reference_response(reference: TraceReference) -> TraceReferenceResponse:
    return TraceReferenceResponse(
        object_type=reference.object_type,
        object_id=reference.object_id,
        status=reference.status,
        relation_source=reference.relation_source,
        detail=reference.detail,
    )


def _to_bundle_response(bundle: TraceBundle) -> TraceBundleResponse:
    return TraceBundleResponse(
        root_type=bundle.root_type,
        root_id=bundle.root_id,
        analysis=_to_reference_response(bundle.analysis),
        recommendation=_to_reference_response(bundle.recommendation),
        review=_to_reference_response(bundle.review),
        workflow_run=_to_reference_response(bundle.workflow_run),
        intelligence_run=_to_reference_response(bundle.intelligence_run),
        agent_action=_to_reference_response(bundle.agent_action),
        execution_request=_to_reference_response(bundle.execution_request),
        execution_receipt=_to_reference_response(bundle.execution_receipt),
        review_execution_request=_to_reference_response(bundle.review_execution_request),
        review_execution_receipt=_to_reference_response(bundle.review_execution_receipt),
        latest_audit_events=[_to_reference_response(ref) for ref in bundle.latest_audit_events],
        report_artifact=_to_reference_response(bundle.report_artifact),
        outcome=_to_reference_response(bundle.outcome),
        knowledge_feedback=_to_reference_response(bundle.knowledge_feedback),
    )


@router.get("/workflow-runs/{workflow_run_id}", response_model=TraceBundleResponse)
async def trace_workflow_run(workflow_run_id: str, db: Session = Depends(get_db)):
    try:
        bundle = TraceService(db).trace_workflow_run(workflow_run_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail=f"WorkflowRun not found: {workflow_run_id}")
        return _to_bundle_response(bundle)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/recommendations/{recommendation_id}", response_model=TraceBundleResponse)
async def trace_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    try:
        bundle = TraceService(db).trace_recommendation(recommendation_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail=f"Recommendation not found: {recommendation_id}")
        return _to_bundle_response(bundle)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/reviews/{review_id}", response_model=TraceBundleResponse)
async def trace_review(review_id: str, db: Session = Depends(get_db)):
    try:
        bundle = TraceService(db).trace_review(review_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail=f"Review not found: {review_id}")
        return _to_bundle_response(bundle)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
