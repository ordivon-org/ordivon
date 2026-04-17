from pfios.context.context_builder import ContextBuilder
from pfios.domain.analysis.models import AnalysisRequest
from pfios.reasoning.engine import ReasoningEngine
from pfios.governance.risk_engine.engine import RiskEngine
from pfios.audit.auditor import RiskAuditor
from pfios.expression.report_renderer import ReportRenderer
from pfios.core.db.session import SessionLocal
from pfios.domain.analysis.repository import AnalysisRepository
from pfios.domain.analysis.service import AnalysisService
from pfios.domain.recommendation.repository import RecommendationRepository
from pfios.domain.recommendation.service import RecommendationService
from pfios.domain.recommendation.models import Recommendation
from pfios.domain.usage.repository import UsageSnapshotRepository
from pfios.domain.usage.service import UsageService
from pfios.domain.usage.models import UsageSnapshot


class PFIOSOrchestrator:
    def __init__(self) -> None:
        self.context_builder = ContextBuilder()
        self.reasoning_engine = ReasoningEngine()
        self.risk_engine = RiskEngine()
        self.auditor = RiskAuditor()
        self.report_renderer = ReportRenderer()

    def execute_analyze(self, request: AnalysisRequest) -> dict:
        ctx = self.context_builder.build(request)
        analysis = self.reasoning_engine.analyze(ctx)
        analysis.query = request.query
        analysis.symbol = request.symbol
        analysis.timeframe = request.timeframe

        db = SessionLocal()
        reco_id = None
        analysis_id = None
        try:
            # 1. Persist Analysis
            analysis_service = AnalysisService(AnalysisRepository(db))
            analysis_row = analysis_service.create(analysis)
            analysis_id = analysis_row.id

            # 2. Governance Check
            governance = self.risk_engine.validate_analysis(analysis)

            # 3. GENERATE RECOMMENDATION (Wired!)
            reco_obj = None
            if governance.allowed:
                reco_service = RecommendationService(RecommendationRepository(db))
                reco_row = reco_service.create(
                    Recommendation(
                        analysis_id=analysis_id,
                        title=f"Action for {request.symbol}",
                        summary=f"Automated recommendation based on {analysis_id}",
                        rationale=analysis.thesis,
                        expected_outcome="System stabilization",
                        priority="normal",
                    )
                )
                reco_id = reco_row.id
                reco_obj = reco_row

            # 4. UPDATE USAGE (Wired!)
            usage_service = UsageService(UsageSnapshotRepository(db))
            usage_service.create(
                UsageSnapshot(
                    analyses_count=1,
                    recommendations_generated_count=1 if reco_id else 0,
                    metadata={"last_symbol": request.symbol},
                )
            )
        finally:
            db.close()

        # Audit Analysis
        self.auditor.record_event(
            "analysis_completed",
            {
                "analysis_id": analysis.id,
                "symbol": request.symbol,
                "allowed": governance.allowed,
            },
            entity_type="analysis",
            entity_id=analysis.id,
            analysis_id=analysis.id,
        )

        # Audit Recommendation (Wired!)
        if reco_id:
            self.auditor.record_event(
                "recommendation_generated",
                {
                    "recommendation_id": reco_id,
                    "analysis_id": analysis.id,
                },
                entity_type="recommendation",
                entity_id=reco_id,
                analysis_id=analysis.id,
                recommendation_id=reco_id,
            )

        return self.report_renderer.render_analysis_report(analysis, governance)
