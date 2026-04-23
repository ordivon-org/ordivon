from pydantic import BaseModel


class KnowledgeRefResponse(BaseModel):
    object_type: str
    object_id: str
    relation: str
    path: str | None = None


class KnowledgeEntryResponse(BaseModel):
    id: str
    title: str
    narrative: str
    knowledge_type: str
    confidence: float
    feedback_targets: list[str]
    derived_from: KnowledgeRefResponse
    evidence_refs: list[KnowledgeRefResponse]
    created_at: str


class KnowledgePacketSummaryResponse(BaseModel):
    id: str
    recommendation_id: str
    review_id: str | None = None
    knowledge_entry_ids: list[str]
    governance_hint_count: int
    intelligence_hint_count: int


class RecurringIssueResponse(BaseModel):
    issue_key: str
    occurrence_count: int
    sample_narratives: list[str]
    recommendation_ids: list[str]
    review_ids: list[str]
    knowledge_entry_ids: list[str]


class CandidateRuleResponse(BaseModel):
    id: str
    issue_key: str
    summary: str
    status: str
    recommendation_ids: list[str]
    review_ids: list[str]
    knowledge_entry_ids: list[str]
    created_at: str


class KnowledgeRetrieveResponse(BaseModel):
    root_type: str
    root_id: str
    advisory_only: bool = True
    entries: list[KnowledgeEntryResponse]
    packets: list[KnowledgePacketSummaryResponse]
    recurring_issues: list[RecurringIssueResponse]
    candidate_rules: list[CandidateRuleResponse]
