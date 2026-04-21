from capabilities.analyze import AnalyzeCapability
from capabilities.audits import AuditCapability
from capabilities.dashboard import DashboardCapability
from capabilities.evals import EvalCapability
from capabilities.recommendations import RecommendationCapability
from capabilities.reports import ReportCapability
from capabilities.reviews import ReviewCapability
from capabilities.validation import ValidationCapability


def test_capabilities_expose_declared_abstraction_type():
    assert AnalyzeCapability.abstraction_type == "workflow"
    assert RecommendationCapability.abstraction_type == "domain"
    assert ReviewCapability.abstraction_type == "workflow"
    assert DashboardCapability.abstraction_type == "view"
    assert ReportCapability.abstraction_type == "view"
    assert AuditCapability.abstraction_type == "view"
    assert EvalCapability.abstraction_type == "diagnostic"
    assert ValidationCapability.abstraction_type == "diagnostic"
