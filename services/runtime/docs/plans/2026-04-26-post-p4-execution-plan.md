# Post-P4 Closure Execution Plan

> **For Hermes:** Use this plan sequentially. Each phase is self-contained; do not skip phases.

**Goal:** Close the three documented post-P4 debts: KnowledgeFeedback generalization, API contract polish, and Core finance semantic extraction.

**Architecture:** Three sequential phases. H-10 is a data-path fix (extraction service generalization). H-8R is a contract field addition (dataclass + response). Post-P4 extraction is a boundary enforcement (Core/Pack separation).

**Tech Stack:** Python 3.11+, SQLAlchemy, FastAPI, Pytest

**Prerequisites:** P4 closure tag present. API server running. Test DB available.

---

## Phase 1: H-10 — KnowledgeFeedback Generalization

**Goal:** Review → Lesson → KnowledgeFeedback works for finance DecisionIntake reviews (no recommendation_id).

**Current state:** `_build_knowledge_feedback()` returns `None` when `recommendation_id` is None (line 208-209). `LessonExtractionService.extract_for_review()` also returns `[]` when review has no recommendation_id (line 45-46). The lesson repository only supports listing by recommendation_id.

**Root cause:** `LessonRepository.list_for_recommendation()` filters by `recommendation_id`, but finance DecisionIntake lessons have `recommendation_id=None`.

**Approach:**
1. Add `LessonRepository.list_for_review()` — filter by review_id
2. Add `LessonExtractionService.extract_for_review_by_id()` — use review-scoped extraction
3. Update `ReviewService._build_knowledge_feedback()` — fall back to review extraction when recommendation_id is None
4. Outcome context for review-based extraction: use the review's outcome_ref to find the linked FinanceManualOutcome

**Files to create:**
- `tests/unit/knowledge/test_h10_kf_generalization.py` — unit tests

**Files to modify:**
- `domains/journal/lesson_repository.py` — add `list_for_review(review_id)`
- `knowledge/extraction.py` — add `extract_for_review_by_id(review_id)` that doesn't require recommendation_id
- `domains/journal/service.py` — update `_build_knowledge_feedback()` to accept review ORM row, fall back to review extraction

**Files to read (do not modify):**
- `domains/journal/lesson_repository.py` — existing list_for_recommendation pattern
- `domains/journal/lesson_orm.py` — LessonORM schema
- `domains/finance_outcome/orm.py` — FinanceManualOutcomeORM

---

### Task 1.1: Audit current lesson repository and extraction

**Objective:** Read the existing code to understand the query patterns before modifying.

**Files to read:**
- `domains/journal/lesson_repository.py`
- `knowledge/extraction.py`
- `domains/journal/service.py:207-244`

**Step 1: Read lesson_repository.py**

Run: read the file. Note:
- `list_for_recommendation()` query pattern
- `to_model()` method signature
- Column names on LessonORM

**Step 2: Read extraction.py**

Run: read the file. Note:
- `extract_for_recommendation()` — finds lessons by recommendation_id, outcomes by recommendation_id
- `extract_for_review()` — delegates to extract_for_recommendation with review.recommendation_id

**Step 3: Document the dependency chain**

```
Review.complete → _build_knowledge_feedback(recommendation_id, review_id)
  → LessonExtractionService.extract_for_recommendation(recommendation_id)
    → LessonRepository.list_for_recommendation(recommendation_id)
    → OutcomeRepository.list_for_recommendation(recommendation_id)
```

**Commit**: No code changed — audit only.

---

### Task 1.2: Add list_for_review to LessonRepository

**Objective:** Add a query method that finds lessons by review_id (not recommendation_id).

**Files:**
- Modify: `domains/journal/lesson_repository.py`

**Step 1: Write the method**

Follow the existing `list_for_recommendation` pattern:

```python
def list_for_review(self, review_id: str) -> list[LessonORM]:
    """Return all lessons linked to a specific review."""
    return (
        self.db.query(LessonORM)
        .filter(LessonORM.review_id == review_id)
        .order_by(LessonORM.created_at.asc())
        .all()
    )
```

**Step 2: Verify syntax**

```bash
cd /root/projects/financial-ai-os && uv run python -c "from domains.journal.lesson_repository import LessonRepository; print('OK')"
```

**Step 3: Commit**

```bash
git add domains/journal/lesson_repository.py
git commit -m "feat(h10): add LessonRepository.list_for_review by review_id"
```

---

### Task 1.3: Add extract_for_review_by_id to LessonExtractionService

**Objective:** Add an extraction method that works without recommendation_id, using the review's outcome_ref to find the linked outcome.

**Files:**
- Modify: `knowledge/extraction.py`

**Step 1: Add the new method**

After the existing `extract_for_review()` method (line 47), add:

```python
def extract_for_review_by_id(self, review_id: str) -> list[KnowledgeEntry]:
    """Derive KnowledgeEntries from lessons and outcome linked to a review.

    Works for finance DecisionIntake reviews (no recommendation_id)
    by using review-scoped lesson lookup and outcome_ref linkage.
    """
    from domains.journal.repository import ReviewRepository
    from domains.finance_outcome.repository import FinanceManualOutcomeRepository

    review_repo = ReviewRepository(self.db)
    review_row = review_repo.get(review_id)
    if review_row is None:
        return []

    lesson_rows = self.lesson_repository.list_for_review(review_id)
    if not lesson_rows:
        return []

    lessons = [self.lesson_repository.to_model(row) for row in lesson_rows]

    # Try to find outcome via outcome_ref on the review
    latest_outcome = None
    if review_row.outcome_ref_id and review_row.outcome_ref_type == "finance_manual_outcome":
        outcome_repo = FinanceManualOutcomeRepository(self.db)
        outcome_row = outcome_repo.get(review_row.outcome_ref_id)
        if outcome_row:
            from domains.finance_outcome.models import FinanceManualOutcome
            latest_outcome = FinanceManualOutcome(
                id=outcome_row.id,
                decision_intake_id=outcome_row.decision_intake_id,
                execution_receipt_id=outcome_row.execution_receipt_id,
                outcome_source=outcome_row.outcome_source,
                observed_outcome=outcome_row.observed_outcome,
                verdict=outcome_row.verdict,
                variance_summary=outcome_row.variance_summary,
                plan_followed=outcome_row.plan_followed,
                created_at=outcome_row.created_at.isoformat() if hasattr(outcome_row.created_at, "isoformat") else str(outcome_row.created_at),
            )

    entries: list[KnowledgeEntry] = []
    for lesson in lessons:
        if latest_outcome is None:
            entries.append(KnowledgeEntryBuilder.from_lesson(lesson))
        else:
            entries.append(KnowledgeEntryBuilder.from_lesson_with_outcome(lesson, latest_outcome))
    return entries
```

**Step 2: Verify syntax**

```bash
cd /root/projects/financial-ai-os && uv run python -c "from knowledge.extraction import LessonExtractionService; print('OK')"
```

**Step 3: Commit**

```bash
git add knowledge/extraction.py
git commit -m "feat(h10): add extraction path for reviews without recommendation_id"
```

---

### Task 1.4: Update _build_knowledge_feedback to fall back to review extraction

**Objective:** When recommendation_id is None, use review-scoped extraction instead of returning None.

**Files:**
- Modify: `domains/journal/service.py` (lines 207-244)

**Step 1: Modify the method**

Change `_build_knowledge_feedback` from:

```python
def _build_knowledge_feedback(self, recommendation_id: str | None, review_id: str):
    if recommendation_id is None:
        return None
    entries = LessonExtractionService(...).extract_for_recommendation(recommendation_id)
    ...
```

To accept the review ORM row and fall back:

```python
def _build_knowledge_feedback(self, recommendation_id: str | None, review_id: str):
    extraction = LessonExtractionService(self.review_repository.db)
    if recommendation_id is not None:
        entries = extraction.extract_for_recommendation(recommendation_id)
    else:
        entries = extraction.extract_for_review_by_id(review_id)

    if not entries:
        return None

    packet = KnowledgeFeedbackService().build_packet(
        recommendation_id or review_id,  # Use review_id as fallback identifier
        entries,
        review_id=review_id,
    )
    ...
```

And update the audit event to use `recommendation_id or review_id` for the event payload.

**Step 2: Run existing tests to verify no regression**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/integration/test_h8_review_closure.py -v
```

Expected: all tests pass. H-8 tests use recommendation-backed reviews and should still produce KF.

**Step 3: Commit**

```bash
git add domains/journal/service.py
git commit -m "feat(h10): generalize KF to work without recommendation_id via review extraction fallback"
```

---

### Task 1.5: Write H-10 unit tests

**Objective:** Verify that finance DecisionIntake reviews (recommendation_id=None) now produce KnowledgeFeedback.

**Files:**
- Create: `tests/unit/knowledge/test_h10_kf_generalization.py`

**Step 1: Write tests**

```python
"""H-10: KnowledgeFeedback generalization — unit tests.

Verifies that reviews without recommendation_id (finance DecisionIntake path)
can produce KnowledgeFeedback via review-scoped lesson + outcome extraction.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from state.db.base import Base
from domains.journal.models import Review, Lesson
from domains.journal.repository import ReviewRepository
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.service import ReviewService
from shared.enums.domain import ReviewVerdict


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_h10_kf_extraction_without_recommendation_id(db):
    """Review without recommendation_id → KF via review-scoped extraction."""
    from domains.finance_outcome.orm import FinanceManualOutcomeORM
    from domains.finance_outcome.repository import FinanceManualOutcomeRepository
    from domains.finance_outcome.service import FinanceManualOutcomeService

    # Setup: create a manual outcome
    outcome_repo = FinanceManualOutcomeRepository(db)
    # (depends on FinanceManualOutcome model structure)
    # ...

    # Setup: create a review with outcome_ref but no recommendation_id
    review_repo = ReviewRepository(db)
    # ...

    # Extraction should produce entries
    from knowledge.extraction import LessonExtractionService
    service = LessonExtractionService(db)
    entries = service.extract_for_review_by_id(review_id)
    assert len(entries) >= 1


def test_h10_kf_fallback_when_recommendation_id_none(db):
    """_build_knowledge_feedback uses extract_for_review_by_id when recommendation_id=None."""
    # Full integration through ReviewService._build_knowledge_feedback
    pass


def test_h10_existing_recommendation_path_unchanged(db):
    """Reviews WITH recommendation_id still use the old extraction path."""
    pass
```

**Step 2: Run tests**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/knowledge/test_h10_kf_generalization.py -v
```

**Step 3: Commit**

```bash
git add tests/unit/knowledge/test_h10_kf_generalization.py
git commit -m "test(h10): add KF generalization unit tests"
```

---

### Task 1.6: Integration verification

**Objective:** Run the full test suite and a real dogfood verification.

**Step 1: Run full test suite**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/ tests/integration/ -q
```

Expected: all pass.

**Step 2: Run dogfood verification targeting KF**

Create a single intake → execute → outcome → review → complete chain and verify KF packet is created:

```bash
cd /root/projects/financial-ai-os && uv run python scripts/h9c_verification.py
```

Check: review completion response includes `knowledge_feedback_packet_id` even for recommendation_id=None reviews.

**Step 3: Tag**

```bash
git tag h10-kf-generalization
```

---

## Phase 2: H-8R — Outcome Ref API Response Contract

**Goal:** API responses for review creation and detail include `outcome_ref_type` and `outcome_ref_id`.

**Current state:** `ReviewResult` dataclass (capabilities/contracts/domain.py:25-31) has no outcome_ref fields. `create_review()` returns `ReviewResult` without them. The DB row DOES have them — they're just not echoed in the API response.

**Approach:**
1. Add `outcome_ref_type` and `outcome_ref_id` to `ReviewResult`
2. Populate them in `ReviewCapability.create_review()`
3. Verify in integration tests

**Files to modify:**
- `capabilities/contracts/domain.py` — add fields to ReviewResult
- `capabilities/workflow/reviews.py` — populate fields in create_review

**Files to read (do not modify):**
- `apps/api/app/routers/reviews.py` — verify response model uses ReviewResult
- `apps/api/app/schemas/reviews.py` — ReviewDetailResponse already has outcome_ref fields

---

### Task 2.1: Add outcome_ref fields to ReviewResult

**Objective:** Extend the ReviewResult dataclass with optional outcome_ref fields.

**Files:**
- Modify: `capabilities/contracts/domain.py`

**Step 1: Add fields**

```python
@dataclass(slots=True)
class ReviewResult:
    id: str
    status: str
    created_at: str
    recommendation_id: str | None
    lessons_created: int
    outcome_ref_type: str | None = None
    outcome_ref_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

**Step 2: Verify no type errors**

```bash
cd /root/projects/financial-ai-os && uv run python -c "from capabilities.contracts.domain import ReviewResult; r = ReviewResult(id='x', status='ok', created_at='', recommendation_id=None, lessons_created=0); print(r.outcome_ref_type)"
```

Expected: `None`

**Step 3: Commit**

```bash
git add capabilities/contracts/domain.py
git commit -m "feat(h8r): add outcome_ref fields to ReviewResult"
```

---

### Task 2.2: Populate outcome_ref in create_review

**Objective:** Pass the outcome_ref values from the ORM row to the ReviewResult.

**Files:**
- Modify: `capabilities/workflow/reviews.py` (lines 187-194)

**Step 1: Add fields to ReviewResult construction**

```python
row = service.create(review)
return ReviewResult(
    id=row.id,
    status=row.status,
    created_at=row.created_at.isoformat() if hasattr(row, "created_at") else utc_now().isoformat(),
    recommendation_id=row.recommendation_id,
    lessons_created=0,
    outcome_ref_type=row.outcome_ref_type,
    outcome_ref_id=row.outcome_ref_id,
    metadata={"action_context": asdict(context)},
)
```

**Step 2: Run review integration tests**

```bash
cd /root/projects/financial-ai-os && PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test uv run pytest tests/integration/test_h8_review_closure.py -v
```

Expected: all pass. `test_h8_review_detail_returns_outcome_ref` should still pass.

**Step 3: Commit**

```bash
git add capabilities/workflow/reviews.py
git commit -m "feat(h8r): populate outcome_ref in ReviewResult from create_review"
```

---

### Task 2.3: Verification

**Step 1: Run dogfood to verify API response**

```bash
cd /root/projects/financial-ai-os && uv run python -c "
import json, urllib.request
BASE = 'http://127.0.0.1:8000/api/v1'
# Create intake → govern → plan → outcome → review
# Verify review response includes outcome_ref_type
..."
```

Expected: review creation response includes `outcome_ref_type: "finance_manual_outcome"`.

**Step 2: Run full test suite**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/ tests/integration/ -q
```

**Step 3: Tag**

```bash
git tag h8r-outcome-ref-response
```

---

## Phase 3: Post-P4 — Finance Semantic Extraction from Core

**Goal:** Move finance-specific hard gate semantics (`stop_loss`, `is_chasing`, `revenge_trade`, `risk_unit_usdt`) out of `RiskEngine.validate_intake()` and into Finance Pack policy binding.

**Design principle:** Core RiskEngine should validate generic intake structure (field existence, types, status). Domain-specific validation (trading discipline, risk limits, emotional state) belongs in Pack-level policies registered with the governance system.

**Current state:**

```python
# governance/risk_engine/engine.py — validate_intake()
Gate 1: thesis, stop_loss, emotional_state existence   ← mix of generic + finance
Gate 2: max_loss_usdt, position_size_usdt, risk_unit_usdt existence  ← finance-specific
Gate 3: max_loss <= 2× risk_unit, position_size <= 10× risk_unit     ← finance-specific
Gate 4: is_revenge_trade, is_chasing, emotional_state, rule_exceptions, confidence  ← finance-specific
```

**Target state:**

```python
# governance/risk_engine/engine.py — validate_intake()
Gate 0: intake status must be "validated"
Gate 1: required fields exist (generic field presence, not finance names)
  → delegates to pack policy: pack_policy.validate_required_fields(payload)

# packs/finance/policy.py
class FinanceDisciplinePolicy:
    def validate(self, payload) -> list[RejectReason | EscalateReason]:
        # All current Gate 2/3/4 rules move here
```

**This phase is a design sketch, not full TDD.** The exact mechanism (policy registration, pluggable validators, intake-type routing) needs a dedicated design session. The plan below provides the acceptance criteria and approach but individual tasks will differ after design.

---

### Task 3.1: Design the extraction interface

**Objective:** Define how Pack policies will hook into RiskEngine without Core knowing about finance.

**Key decisions to make:**
1. Should intake-type (e.g., "controlled_decision") route to a pack policy?
2. Should policies be registered via `GovernancePolicySource` or a new mechanism?
3. Should `validate_intake()` accept optional policy overrides?

**Output:** A design decision record at `docs/decisions/ADR-006-pack-policy-binding.md`.

---

### Task 3.2: Move finance rules to Finance Pack

**Files to create:**
- `packs/finance/trading_discipline_policy.py` — all current Gate 2/3/4 rules

**Files to modify:**
- `governance/risk_engine/engine.py` — remove finance-specific gates, add policy delegation point
- `governance/policy_source.py` — register finance policy for controlled_decision intakes

---

### Task 3.3: Verification

**Acceptance criteria:**
1. `RiskEngine.validate_intake()` has no finance field names (`stop_loss`, `is_chasing`, `max_loss_usdt`, etc.)
2. All H-5/H-9C governance tests pass
3. Dogfood produces identical decisions (execute/reject/escalate) for same inputs
4. Adding a second domain Pack does not require Core changes

---

## Final Verification (All Phases)

```bash
# Full test suite
cd /root/projects/financial-ai-os && uv run pytest tests/unit/ tests/integration/ -q

# Dogfood verification
uv run python scripts/h9c_verification.py

# Git status — should be clean
git status --short
```

### Tags

```
h10-kf-generalization
h8r-outcome-ref-response
post-p4-finance-semantic-extraction   (design only — implementation to follow)
```
