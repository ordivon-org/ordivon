import pytest

from domains.candidate_rules.models import CandidateRule
from domains.knowledge_feedback.feedback_record_models import FeedbackRecord


def test_candidate_rule_rejects_unknown_status():
    with pytest.raises(ValueError, match="Unsupported candidate rule status"):
        CandidateRule(issue_key="missed confirmation candle", summary="Wait for confirmation", status="active")


def test_feedback_record_rejects_unknown_consumer_type():
    with pytest.raises(ValueError, match="Unsupported feedback consumer_type"):
        FeedbackRecord(
            packet_id="kfpkt_test",
            recommendation_id="reco_test",
            consumer_type="policy",
            subject_key="policy.default",
        )
