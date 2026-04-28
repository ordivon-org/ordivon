from domains.candidate_rules.models import CandidateRule
from domains.candidate_rules.repository import CandidateRuleRepository

# NOTE: CandidateRuleService is NOT imported here — it imports knowledge.retrieval
# which causes transitive import failures in scripts that only need the ORM/model.
# Import CandidateRuleService directly: from domains.candidate_rules.service import CandidateRuleService

__all__ = ["CandidateRule", "CandidateRuleRepository"]
