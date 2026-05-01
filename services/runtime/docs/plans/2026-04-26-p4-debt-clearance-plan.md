# Forward Hardening Sprint — P4 → P5 Foundation Strengthening

> **For Hermes:** 按 Wave 顺序执行，不可跳跃。每 Wave 自包含。
> 核心原则：**先让系统更可见，再让系统更会学，再让系统更通用，再让系统接受更多现实压力。**
>
> **前置要求**: P4 closure tag 存在。API 运行中。测试 DB 可用（pfios_test）。Postgres + Redis 容器运行。

## Wave 总览

```
Wave 0  基线 + 脚本提交       (15 分钟)  可立即执行
Wave 1  H-8R API 响应补齐     (25 分钟)  低风险高收益
Wave 2  H-10 KF 泛化          (45 分钟)  中风险高收益
Wave 3A ADR-006 设计          (20 分钟)  设计先行
Wave 3B Finance 语义抽离       (90 分钟)  高风险 — 视 Wave 1/2 结果决定
Wave 4  30 次扩展狗粮          (40 分钟)  放最后，测新系统
Wave 5  最终验证与声明          (15 分钟)
```

## 批准状态

| Wave | 批准 | 条件 |
|------|------|------|
| Wave 0 | ✅ 立即执行 | 无 |
| Wave 1 | ✅ 立即执行 | Wave 0 完成后 |
| Wave 2 | ✅ 立即执行 | Wave 1 完成后 |
| Wave 3A | ✅ 立即执行 | Wave 2 完成后 |
| Wave 3B | ⏳ 待决定 | Wave 1/2 测试结果 + ADR-006 设计完成 |
| Wave 4 | ⏳ 待决定 | Wave 1/2/3A 后 |
| Wave 5 | ⏳ 待决定 | 所有前序 Wave 完成 |

**目标**: 将 P4 重审计确认的全部 5 项技术债 + 2 项工程债彻底清零，使系统达到可声明 P4 完全关闭的状态。

**债务清单**:

| # | 债务 | 类别 | 当前状态 | 目标 |
|---|------|------|----------|------|
| 1 | H-10 KF 泛化 | 架构债 | KF 需要 recommendation_id，finance review 无法生成 | 任何 review 都能生成 KF |
| 2 | H-8R API 响应润色 | 契约债 | review 响应缺 outcome_ref 字段 | API 响应完整回显 |
| 3 | Finance 语义在 Core | 边界债 | stop_loss/is_chasing 在 RiskEngine 中 | 提取到 Pack 层 |
| 4 | 狗粮脚本未提交 | 工程债 | scripts/ 下未跟踪 | 提交并打 tag |
| 5 | 狗粮样本量不足 | 证据债 | 9 次自动化运行 | 30 次扩展狗粮 |
| 6 | OpenAPI 快照过期 | 契约债 | H-8R 改动后需更新 | 快照匹配当前 API |
| 7 | 文档命名残留 | 文档债 | 部分文件名含 pfios | 审计确认内容已更新 |

**架构**: 6 个阶段，顺序依赖。H-10 → H-8R → Finance 提取 → 文档 → 30 次狗粮 → 最终验证。

**技术栈**: Python 3.11+, SQLAlchemy, FastAPI, Pytest, urllib (狗粮脚本)

---

## Phase 0: 基础设施准备

**目标**: 审计环境、提交未跟踪文件、确认测试基线。

### Task 0.1: 确认测试基线

**目标**: 记录当前测试状态作为回归基线。

**命令**:
```bash
cd /root/projects/financial-ai-os
# 单元测试
uv run pytest tests/unit -q --no-header -p no:cacheprovider 2>&1 | tail -3
# 集成测试
uv run pytest tests/integration -q --no-header 2>&1 | tail -3
# PG 全回归
PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test uv run pytest tests/ -q --no-header -p no:cacheprovider 2>&1 | tail -3
```

**预期**: 377 unit + 134 integration + 4 contract = 515 PG 全回归，0 失败。

**输出**: 记录基线数字到 `docs/audits/p4-closure/baseline.txt`。

---

### Task 0.2: 提交狗粮和验证脚本

**目标**: 将未跟踪的脚本纳入版本控制，建立审计追踪。

**文件**:
- `scripts/h9_dogfood_runs.py` — H-9E 自动化狗粮运行器
- `scripts/h9c_verification.py` — H-9C 验证运行器

**Step 1**: 审计脚本内容，确认不含密钥/密码/内网地址

```bash
cd /root/projects/financial-ai-os
rg "api_key|password|secret|token|sk-" scripts/
```

**预期**: 无匹配。

**Step 2**: 提交

```bash
git add scripts/h9_dogfood_runs.py scripts/h9c_verification.py
git commit -m "chore: commit H-9 dogfood and verification scripts for audit trail"
git tag h9-scripts-committed
```

**验证**: `git status --short` 只剩 `.hermes/` 未跟踪。

---

### Task 0.3: 确认 API 和数据库运行

```bash
# API
curl -s http://127.0.0.1:8000/api/v1/health | python3 -m json.tool | head -5

# Postgres
docker exec pfios-postgres pg_isready -U pfios -d pfios

# 测试 DB 存在
docker exec pfios-postgres psql -U pfios -d pfios -c "SELECT 1" > /dev/null 2>&1 && echo "OK"
```

**预期**: 全部 OK。

---

## Phase 1: H-10 — KnowledgeFeedback 泛化 (5 个任务, 预计 45 分钟)

**目标**: Finance DecisionIntake review（recommendation_id=None）也能生成 KnowledgeFeedback packet。

**当前状态**:

```
Review.complete → _build_knowledge_feedback(recommendation_id, review_id)
  → if recommendation_id is None: return None  ← 问题在这里
  → LessonExtractionService.extract_for_recommendation(recommendation_id)
    → LessonRepository.list_for_recommendation(recommendation_id)
```

**目标状态**:

```
Review.complete → _build_knowledge_feedback(recommendation_id, review_id)
  → if recommendation_id is not None: extract_for_recommendation(recommendation_id)
  → else: extract_for_review_by_id(review_id)
    → LessonRepository.list_for_review(review_id)
    → 通过 review.outcome_ref 找到 FinanceManualOutcome
```

---

### Task 1.1: 审计现有代码路径（只读）

**目标**: 确认依赖链，不修改任何代码。

**文件**: 三个文件，顺序阅读。

**Step 1**: 阅读 `domains/journal/lesson_repository.py`

```bash
cd /root/projects/financial-ai-os
```

需要确认:
- `LessonORM` 是否有 `review_id` 列
- `list_for_recommendation()` 的查询模式
- `to_model()` 方法签名

**Step 2**: 阅读 `knowledge/extraction.py`

需要确认:
- `extract_for_recommendation()` 的完整实现
- `extract_for_review()` 如何委托到 recommendation 路径
- `KnowledgeEntryBuilder.from_lesson()` 和 `from_lesson_with_outcome()` 签名

**Step 3**: 阅读 `domains/journal/service.py` 中 `_build_knowledge_feedback()` (约 207-244 行)

需要确认:
- 何时返回 None
- 如何调用 extraction service
- 如何创建 KF packet

**Step 4**: 阅读 `domains/finance_outcome/orm.py` 确认字段

需要确认: `FinanceManualOutcomeORM` 的字段列表和类型。

**输出**: 在 plan 文档中记录依赖链。不提交代码变更。

---

### Task 1.2: 添加 LessonRepository.list_for_review() — TDD

**目标**: 添加按 review_id 查询 lesson 的方法。

**文件**:
- 创建: `tests/unit/journal/test_h10_lesson_repository.py`
- 修改: `domains/journal/lesson_repository.py`

**Step 1: 写失败测试**

```python
# tests/unit/journal/test_h10_lesson_repository.py
"""H-10: LessonRepository.list_for_review 单元测试."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from state.db.base import Base
from domains.journal.lesson_orm import LessonORM
from domains.journal.lesson_repository import LessonRepository


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_list_for_review_returns_lessons_for_review_id(db):
    """list_for_review 返回特定 review_id 的所有 lesson。"""
    repo = LessonRepository(db)

    # 插入两条 lesson：一条属于 review_a，一条属于 review_b
    lesson_a = LessonORM(
        id="lesson-001",
        review_id="review-a",
        recommendation_id=None,
        lesson_text="Lesson from review A",
        cause_tags_json="[]",
        source_refs_json="[]",
    )
    lesson_b = LessonORM(
        id="lesson-002",
        review_id="review-b",
        recommendation_id=None,
        lesson_text="Lesson from review B",
        cause_tags_json="[]",
        source_refs_json="[]",
    )
    db.add_all([lesson_a, lesson_b])
    db.commit()

    # 查询 review-a 的 lesson
    results = repo.list_for_review("review-a")
    assert len(results) == 1
    assert results[0].id == "lesson-001"
    assert results[0].lesson_text == "Lesson from review A"


def test_list_for_review_returns_empty_for_unknown_review(db):
    """不存在的 review_id 返回空列表。"""
    repo = LessonRepository(db)
    results = repo.list_for_review("nonexistent")
    assert results == []


def test_list_for_review_returns_empty_when_no_lessons(db):
    """有 review 但没有 lesson 时返回空列表。"""
    repo = LessonRepository(db)
    # lesson 表为空
    results = repo.list_for_review("review-c")
    assert results == []
```

**Step 2: 运行测试，确认失败**

```bash
cd /root/projects/financial-ai-os
uv run pytest tests/unit/journal/test_h10_lesson_repository.py -v
```

**预期**: 3 个测试全部 FAIL — `AttributeError: 'LessonRepository' object has no attribute 'list_for_review'`

**Step 3: 实现方法**

```python
# 在 domains/journal/lesson_repository.py 中添加（仿照现有 list_for_recommendation 模式）


def list_for_review(self, review_id: str) -> list[LessonORM]:
    """Return all lessons linked to a specific review_id.

    Unlike list_for_recommendation(), this does NOT require
    recommendation_id — it queries directly by review_id.
    Used by H-10 KF generalization for finance DecisionIntake reviews.
    """
    return self.db.query(LessonORM).filter(LessonORM.review_id == review_id).order_by(LessonORM.created_at.asc()).all()
```

**Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/unit/journal/test_h10_lesson_repository.py -v
```

**预期**: 3 passed。

**Step 5: 提交**

```bash
git add domains/journal/lesson_repository.py tests/unit/journal/test_h10_lesson_repository.py
git commit -m "feat(h10): add LessonRepository.list_for_review(review_id)"
```

---

### Task 1.3: 添加 LessonExtractionService.extract_for_review_by_id() — TDD

**目标**: 添加不依赖 recommendation_id 的 extraction 方法，通过 review 的 outcome_ref 找到关联的 outcome。

**文件**:
- 创建: `tests/unit/knowledge/test_h10_extraction.py`
- 修改: `knowledge/extraction.py`

**前置**: 需先阅读 `knowledge/extraction.py` 的第 1-73 行（Task 1.1 已完成）。

**Step 1: 写失败测试**

```python
# tests/unit/knowledge/test_h10_extraction.py
"""H-10: LessonExtractionService.extract_for_review_by_id 单元测试."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from state.db.base import Base
from domains.journal.lesson_orm import LessonORM
from domains.journal.orm import ReviewORM
from domains.finance_outcome.orm import FinanceManualOutcomeORM
from knowledge.extraction import LessonExtractionService


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_extract_for_review_by_id_returns_entries(db):
    """extract_for_review_by_id 对带有 lesson + outcome_ref 的 review 返回 KnowledgeEntry 列表。"""
    now = datetime.now(timezone.utc)

    # 创建 FinanceManualOutcome
    outcome = FinanceManualOutcomeORM(
        id="fmout-test001",
        decision_intake_id="intake-test001",
        execution_receipt_id="exrcpt-test001",
        outcome_source="manual",
        observed_outcome="Price went up 5%",
        verdict="validated",
        variance_summary="Clean execution",
        plan_followed=True,
        created_at=now,
    )
    db.add(outcome)

    # 创建 Review（带 outcome_ref）
    review = ReviewORM(
        id="review-test001",
        recommendation_id=None,
        review_type="recommendation_postmortem",
        status="completed",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout-test001",
        created_at=now,
    )
    db.add(review)

    # 创建 Lesson
    lesson = LessonORM(
        id="lesson-test001",
        review_id="review-test001",
        recommendation_id=None,
        lesson_text="Stop loss should be wider",
        cause_tags_json='["stop_placement"]',
        source_refs_json='["outcome:fmout-test001"]',
        created_at=now,
    )
    db.add(lesson)
    db.commit()

    service = LessonExtractionService(db)
    entries = service.extract_for_review_by_id("review-test001")

    assert len(entries) >= 1
    assert entries[0].content is not None


def test_extract_for_review_by_id_returns_empty_for_no_lessons(db):
    """没有 lesson 时返回空列表。"""
    now = datetime.now(timezone.utc)
    review = ReviewORM(
        id="review-empty",
        recommendation_id=None,
        review_type="recommendation_postmortem",
        status="completed",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout-xxx",
        created_at=now,
    )
    db.add(review)
    db.commit()

    service = LessonExtractionService(db)
    entries = service.extract_for_review_by_id("review-empty")
    assert entries == []


def test_extract_for_review_by_id_returns_empty_for_unknown_review(db):
    """不存在的 review_id 返回空列表。"""
    service = LessonExtractionService(db)
    entries = service.extract_for_review_by_id("nonexistent")
    assert entries == []
```

**Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/unit/knowledge/test_h10_extraction.py -v
```

**预期**: 3 个测试全部 FAIL — `AttributeError: 'LessonExtractionService' object has no attribute 'extract_for_review_by_id'`

**Step 3: 实现方法**

```python
# 在 knowledge/extraction.py 的 LessonExtractionService 类中，
# 在 extract_for_review() 方法之后添加：


def extract_for_review_by_id(self, review_id: str) -> list[KnowledgeEntry]:
    """Derive KnowledgeEntries from lessons linked to a review.

    Works WITHOUT recommendation_id — uses review-scoped lesson
    lookup and outcome_ref linkage to find the associated outcome.
    This is the H-10 generalization path for finance DecisionIntake
    reviews that have no recommendation_id.
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

    # Try to find the linked outcome via outcome_ref
    latest_outcome = None
    if review_row.outcome_ref_id and review_row.outcome_ref_type == "finance_manual_outcome":
        outcome_repo = FinanceManualOutcomeRepository(self.db)
        outcome_row = outcome_repo.get(review_row.outcome_ref_id)
        if outcome_row:
            from domains.finance_outcome.models import FinanceManualOutcome

            created_str = (
                outcome_row.created_at.isoformat()
                if hasattr(outcome_row.created_at, "isoformat")
                else str(outcome_row.created_at)
            )
            latest_outcome = FinanceManualOutcome(
                id=outcome_row.id,
                decision_intake_id=outcome_row.decision_intake_id,
                execution_receipt_id=outcome_row.execution_receipt_id,
                outcome_source=outcome_row.outcome_source,
                observed_outcome=outcome_row.observed_outcome,
                verdict=outcome_row.verdict,
                variance_summary=outcome_row.variance_summary or "",
                plan_followed=outcome_row.plan_followed or False,
                created_at=created_str,
            )

    entries: list[KnowledgeEntry] = []
    for lesson in lessons:
        if latest_outcome is None:
            entries.append(KnowledgeEntryBuilder.from_lesson(lesson))
        else:
            entries.append(KnowledgeEntryBuilder.from_lesson_with_outcome(lesson, latest_outcome))
    return entries
```

**Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/unit/knowledge/test_h10_extraction.py -v
```

**预期**: 3 passed。

**Step 5: 提交**

```bash
git add knowledge/extraction.py tests/unit/knowledge/test_h10_extraction.py
git commit -m "feat(h10): add extract_for_review_by_id for reviews without recommendation_id"
```

---

### Task 1.4: 更新 _build_knowledge_feedback 回退逻辑 — TDD

**目标**: 当 recommendation_id 为 None 时，使用 review-scoped extraction 替代直接返回 None。

**文件**:
- 创建: `tests/unit/journal/test_h10_kf_service.py`
- 修改: `domains/journal/service.py` (约 207-244 行)

**前置**: Task 1.1 已确认 `_build_knowledge_feedback` 的精确位置和逻辑。

**Step 1: 写失败测试**

```python
# tests/unit/journal/test_h10_kf_service.py
"""H-10: ReviewService._build_knowledge_feedback 回退逻辑测试."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from state.db.base import Base
from domains.journal.orm import ReviewORM
from domains.journal.lesson_orm import LessonORM
from domains.finance_outcome.orm import FinanceManualOutcomeORM


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_kf_generated_for_finance_review_without_recommendation_id(db):
    """H-10: finance review (recommendation_id=None) 生成 KF packet。"""
    now = datetime.now(timezone.utc)

    # Setup: outcome + review + lesson（无 recommendation_id）
    outcome = FinanceManualOutcomeORM(
        id="fmout-h10-001",
        decision_intake_id="intake-h10-001",
        execution_receipt_id="exrcpt-h10-001",
        outcome_source="manual",
        observed_outcome="Price went up 5%",
        verdict="validated",
        variance_summary="Clean",
        plan_followed=True,
        created_at=now,
    )
    db.add(outcome)

    review = ReviewORM(
        id="review-h10-001",
        recommendation_id=None,  # ← 关键：无 recommendation_id
        review_type="recommendation_postmortem",
        status="completed",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout-h10-001",
        expected_outcome="Price goes up",
        observed_outcome="Price went up 5%",
        verdict="validated",
        cause_tags_json='["plan_execution"]',
        lessons_json='["lesson text here"]',
        followup_actions_json="[]",
        created_at=now,
        completed_at=now,
    )
    db.add(review)

    lesson = LessonORM(
        id="lesson-h10-001",
        review_id="review-h10-001",
        recommendation_id=None,
        lesson_text="Good entry timing",
        cause_tags_json='["entry_timing"]',
        source_refs_json="[]",
        created_at=now,
    )
    db.add(lesson)
    db.commit()

    # 调用 _build_knowledge_feedback
    from domains.journal.service import ReviewService
    # 需要注入 db session 到 service
    # （具体调用方式取决于 ReviewService 的构造方式，审计时确认）

    # 期望：不再返回 None，而是返回 KF packet
    # packet = service._build_knowledge_feedback(None, "review-h10-001")
    # assert packet is not None
    # assert packet.id is not None


def test_existing_recommendation_path_unchanged(db):
    """H-10: 有 recommendation_id 的 review 不受影响，仍走原路径。"""
    # Setup: 带 recommendation_id 的 review
    # 验证 extract_for_recommendation 仍被调用

    # 读取 domains/journal/service.py 确定 ReviewService 构造方式后补充
    pass
```

**注意**: 以上测试需要在 Task 1.1 审计 `ReviewService` 构造方式后补充。ReviewService 可能需要 `db`、`review_repository`、`lesson_repository` 等依赖注入。

**Step 2: 审计 ReviewService 构造方式**

```bash
cd /root/projects/financial-ai-os
rg "class ReviewService" domains/journal/service.py -A 20
```

**Step 3: 修改 _build_knowledge_feedback**

将:
```python
def _build_knowledge_feedback(self, recommendation_id: str | None, review_id: str):
    if recommendation_id is None:
        return None
    entries = LessonExtractionService(...).extract_for_recommendation(recommendation_id)
```

改为:
```python
def _build_knowledge_feedback(self, recommendation_id: str | None, review_id: str):
    extraction = LessonExtractionService(self.review_repository.db)
    if recommendation_id is not None:
        entries = extraction.extract_for_recommendation(recommendation_id)
    else:
        entries = extraction.extract_for_review_by_id(review_id)

    if not entries:
        return None
    # ... 其余逻辑不变
```

**Step 4: 运行测试**

```bash
uv run pytest tests/unit/journal/test_h10_kf_service.py -v
```

**Step 5: 运行 H-8 回归测试，确认不影响现有 recommendation 路径**

```bash
uv run pytest tests/integration/test_h8_review_closure.py -v
```

**预期**: 全部通过。

**Step 6: 提交**

```bash
git add domains/journal/service.py tests/unit/journal/test_h10_kf_service.py
git commit -m "feat(h10): generalize KF to fall back to review extraction when recommendation_id is None"
```

---

### Task 1.5: H-10 集成验证

**目标**: 端到端验证 finance DecisionIntake review 现在能生成 KF packet。

**Step 1: 确保 API 运行并重启**

```bash
cd /root/projects/financial-ai-os
docker compose restart api
sleep 3
curl -s http://127.0.0.1:8000/api/v1/health | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])"
```

**预期**: healthy

**Step 2: 运行 H-9C 验证脚本（含完整链路 → review → KF 检查）**

```bash
uv run python scripts/h9c_verification.py
```

检查输出中的 review completion 响应是否包含 `knowledge_feedback_packet_id`。

**Step 3: 运行完整测试套件**

```bash
uv run pytest tests/unit/ tests/integration/ -q --no-header
```

**预期**: 全部通过（511+）。

**Step 4: PG 全回归**

```bash
PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test uv run pytest tests/ -q --no-header -p no:cacheprovider
```

**预期**: 515+ passed, 0 failed。

**Step 5: Tag**

```bash
git tag h10-kf-generalization
```

---

## Phase 2: H-8R — API 响应契约润色 (3 个任务, 预计 25 分钟)

**目标**: Review 创建和详情 API 响应中包含 `outcome_ref_type` 和 `outcome_ref_id` 字段。

**当前状态**: DB 行有这些字段，ORM 有，但 `ReviewResult` dataclass 和 API 响应中没有。

---

### Task 2.1: 验证当前 schema

**目标**: 确认哪些 API 响应模型需要更新。

**Step 1: 找到 ReviewResult dataclass**

```bash
cd /root/projects/financial-ai-os
rg "class ReviewResult" capabilities/ -A 15
```

**Step 2: 找到 API response schemas**

```bash
rg "class ReviewDetailResponse|class ReviewSubmitResponse" apps/ -A 10
```

**Step 3: 找到 create_review 返回点**

```bash
rg "return ReviewResult\(" capabilities/workflow/reviews.py -A 8
```

---

### Task 2.2: 添加 outcome_ref 到 ReviewResult 并填充 — TDD

**目标**: dataclass 加字段，填充逻辑同步。

**文件**:
- 修改: `capabilities/contracts/domain.py` — 加字段到 ReviewResult
- 修改: `capabilities/workflow/reviews.py` — 填充字段
- 创建: `tests/unit/capabilities/test_h8r_review_result.py`

**Step 1: 写失败测试**

```python
# tests/unit/capabilities/test_h8r_review_result.py
"""H-8R: ReviewResult outcome_ref 字段测试."""

from capabilities.contracts.domain import ReviewResult


def test_review_result_has_outcome_ref_fields():
    """ReviewResult 可以接受 outcome_ref_type 和 outcome_ref_id。"""
    result = ReviewResult(
        id="rv-test",
        status="completed",
        created_at="2026-01-01T00:00:00Z",
        recommendation_id=None,
        lessons_created=2,
    )
    # 默认值应为 None
    assert result.outcome_ref_type is None
    assert result.outcome_ref_id is None


def test_review_result_populated_with_outcome_ref():
    """ReviewResult 填充 outcome_ref 值。"""
    result = ReviewResult(
        id="rv-test",
        status="completed",
        created_at="2026-01-01T00:00:00Z",
        recommendation_id=None,
        lessons_created=2,
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout-abc123",
    )
    assert result.outcome_ref_type == "finance_manual_outcome"
    assert result.outcome_ref_id == "fmout-abc123"
```

**Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/unit/capabilities/test_h8r_review_result.py -v
```

**预期**: FAIL — `TypeError: ReviewResult.__init__() got an unexpected keyword argument 'outcome_ref_type'`

**Step 3: 修改 ReviewResult dataclass**

```python
# capabilities/contracts/domain.py


@dataclass(slots=True)
class ReviewResult:
    id: str
    status: str
    created_at: str
    recommendation_id: str | None
    lessons_created: int
    outcome_ref_type: str | None = None  # ← H-8R 新增
    outcome_ref_id: str | None = None  # ← H-8R 新增
    metadata: dict[str, Any] = field(default_factory=dict)
```

**Step 4: 修改 create_review 填充逻辑**

在 `capabilities/workflow/reviews.py` 的 `create_review()` 方法中，找到 `return ReviewResult(...)` 语句，添加:

```python
return ReviewResult(
    id=row.id,
    status=row.status,
    created_at=row.created_at.isoformat() if hasattr(row, "created_at") else utc_now().isoformat(),
    recommendation_id=row.recommendation_id,
    lessons_created=0,
    outcome_ref_type=row.outcome_ref_type,  # ← H-8R 新增
    outcome_ref_id=row.outcome_ref_id,  # ← H-8R 新增
    metadata={"action_context": asdict(context)},
)
```

**Step 5: 运行测试，确认通过**

```bash
uv run pytest tests/unit/capabilities/test_h8r_review_result.py -v
```

**预期**: 2 passed。

**Step 6: 提交**

```bash
git add capabilities/contracts/domain.py capabilities/workflow/reviews.py tests/unit/capabilities/test_h8r_review_result.py
git commit -m "feat(h8r): add outcome_ref fields to ReviewResult and populate in create_review"
```

---

### Task 2.3: H-8R 集成验证 + OpenAPI 快照更新

**Step 1: 重启 API**

```bash
docker compose restart api
sleep 3
```

**Step 2: 狗粮验证 API 响应**

```bash
cd /root/projects/financial-ai-os
uv run python -c "
import json, urllib.request, urllib.error

BASE = 'http://127.0.0.1:8000/api/v1'

def api(method, path, data=None):
    url = f'{BASE}{path}'
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {'_error': e.code, '_body': json.loads(e.read())}

# 查询已有 review（从之前的狗粮运行中）
# 验证响应中包含 outcome_ref 字段
print('Checking review detail endpoint for outcome_ref fields...')
# 使用已知的 review ID 进行测试
"
```

**Step 3: 运行 H-8 测试确认无回归**

```bash
uv run pytest tests/integration/test_h8_review_closure.py tests/integration/test_api_v1_reviews.py -v
```

**预期**: 全部通过。

**Step 4: 更新 OpenAPI 快照**

ReviewResult 加了新字段后，FastAPI 生成的 OpenAPI schema 会变化。需要更新快照:

```bash
# 运行 contract test（预期 FAIL — 快照过期）
uv run pytest tests/contracts/test_api_contracts.py::test_openapi_snapshot_matches_committed_contract -v
# 预期: FAIL（快照不匹配）

# 重新生成快照
cd /root/projects/financial-ai-os
PFIOS_DB_URL=duckdb:///:memory: uv run python -c "
import json, os
os.environ['PFIOS_ENV'] = 'test'
os.environ['PFIOS_DEBUG'] = 'false'
os.environ['PFIOS_REASONING_PROVIDER'] = 'mock'
from apps.api.app.main import app
snapshot = app.openapi()
with open('tests/contracts/openapi.snapshot.json', 'w') as f:
    json.dump(snapshot, f, indent=2)
print('Snapshot updated')
"

# 验证快照通过
uv run pytest tests/contracts/test_api_contracts.py::test_openapi_snapshot_matches_committed_contract -v
# 预期: PASS
```

**Step 5: 完整测试套件**

```bash
# 单元 + 集成
uv run pytest tests/unit/ tests/integration/ -q --no-header

# PG 全回归
PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test uv run pytest tests/ -q --no-header -p no:cacheprovider
```

**预期**: 全部通过。

**Step 6: 提交 + Tag**

```bash
git add tests/contracts/openapi.snapshot.json
git commit -m "chore(h8r): update OpenAPI snapshot with ReviewResult outcome_ref fields"
git tag h8r-outcome-ref-response
```

---

## Phase 3: ADR-006 — Finance 语义从 Core 提取 (4 个任务, 预计 120 分钟)

**目标**: 将 `stop_loss`、`is_chasing`、`max_loss_usdt` 等 finance 字段名从 `RiskEngine.validate_intake()` 中移除，迁移到 Finance Pack policy。

**设计原则**: Core RiskEngine 只做通用结构验证（field presence、status）。Domain 特定验证（交易纪律、风险限制、情绪状态）属于 Pack 层 policy。

**这是本次收口计划中最大的变更**。Phase 3 分两个子阶段:
- 3A: ADR 设计文档（只写不写代码）
- 3B: 实现提取（TDD）

---

### Task 3.1 (设计): 写 ADR-006 — Pack Policy Binding 设计

**目标**: 产出架构决策记录，定义 Core 和 Pack 之间 policy binding 的接口契约。

**文件**:
- 创建: `docs/decisions/ADR-006-pack-policy-binding.md`

**内容模板**:

```markdown
# ADR-006: Pack Policy Binding — Finance Semantic Extraction from Core

> **Date**: 2026-04-26
> **Status**: PROPOSED
> **Replaces**: Known debt from P4 closure re-audit

## Context

RiskEngine.validate_intake() currently hardcodes finance-specific field names:
stop_loss, max_loss_usdt, position_size_usdt, risk_unit_usdt,
is_revenge_trade, is_chasing.

This violates the Core/Pack boundary: Core should not know about
finance-domain semantics.

## Decision

### Interface

RiskEngine.validate_intake() will accept an optional pack_policy parameter:

```python
class PackIntakePolicy(Protocol):
    def validate_fields(self, payload: dict) -> list[RejectReason | EscalateReason]:
        ...
```

### Migration

Gate 1 (field existence): thesis, stop_loss, emotional_state →
  thesis + emotional_state → generic required_fields list from pack_policy.
  stop_loss moves to finance Pack.

Gate 2 (numeric fields): max_loss_usdt, position_size_usdt, risk_unit_usdt →
  all move to finance Pack.

Gate 3 (risk limits): max_loss/risk_unit ratio, position_size/risk_unit ratio →
  all move to finance Pack.

Gate 4 (behavioral): is_revenge_trade, is_chasing, emotional_state keywords,
  rule_exceptions, confidence threshold →
  all move to finance Pack.

### RiskEngine after extraction

Gate 0: intake.status == "validated" (stays — generic)
Gate 1: pack_policy.validate_fields(payload) → reject/escalate reasons
Gate 2: pack_policy.validate_numeric(payload) → reject reasons
Gate 3: pack_policy.validate_limits(payload) → reject reasons
Gate 4: pack_policy.validate_behavioral(payload) → escalate reasons

### Finance Pack Policy

packs/finance/trading_discipline_policy.py:
  - TradingDisciplinePolicy implements PackIntakePolicy
  - All H-5 gate logic (stop_loss, risk_unit, position_size, etc.) moves here
  - Emotional risk keywords, thesis quality checks move here

## Consequences

- Core RiskEngine becomes domain-agnostic
- Adding a second domain Pack requires zero Core changes
- H-5/H-9C test expectations preserved (pack policy tested separately)
- 100% backward compatible: same inputs → same decisions
```

**Step 1**: 写 ADR 文档，提交

```bash
mkdir -p docs/decisions
git add docs/decisions/ADR-006-pack-policy-binding.md
git commit -m "docs: add ADR-006 — Pack Policy Binding for finance semantic extraction"
```

---

### Task 3.2 (设计): 审计 RiskEngine 需要保留的通用逻辑

**目标**: 区分哪些是通用逻辑（留在 Core）、哪些是 finance 特定逻辑（移到 Pack）。

**Step 1**: 完整阅读 `governance/risk_engine/engine.py`

```bash
cd /root/projects/financial-ai-os
# 记录行号和逻辑分类
```

**分类结果**:

| 行号 | 逻辑 | 分类 | 目标 |
|------|------|------|------|
| 93-98 | Gate 0: intake.status != "validated" | **通用** | 留在 Core |
| 101-122 | Gate 1: thesis 字段 + thesis_quality | **混合** | thesis 字段检查通用，thesis_quality 移到 Pack |
| 124-126 | stop_loss 存在检查 | **Finance** | 移到 Pack |
| 128-130 | emotional_state 存在检查 | **Finance** | 移到 Pack |
| 133-143 | max_loss_usdt / position_size_usdt / risk_unit_usdt | **Finance** | 移到 Pack |
| 146-159 | Gate 3: 风险限制比率 | **Finance** | 移到 Pack |
| 162-190 | Gate 4: is_revenge_trade, is_chasing, emotional_keywords, rule_exceptions, confidence | **Finance** | 移到 Pack |
| 192-222 | Decision priority (reject > escalate > execute) | **通用** | 留在 Core |
| 248-263 | Emotional risk keyword detection | **Finance** | 移到 Pack |

**Step 2**: 记录分类结果，不提交（设计参考）。

---

### Task 3.3 (实现): 提取 Finance 逻辑到 Pack — TDD

**目标**: 创建 `TradingDisciplinePolicy`，将 Gate 1-4 的 finance 逻辑全部迁移过去。

**文件**:
- 创建: `packs/finance/trading_discipline_policy.py`
- 创建: `tests/unit/finance/test_trading_discipline_policy.py`
- 修改: `governance/risk_engine/engine.py`
- 修改: `governance/policy_source.py`

**Step 1: 创建 Pack Intake Policy Protocol**

```python
# packs/finance/trading_discipline_policy.py
"""H-5/H-9C Finance Trading Discipline — Pack-level policy.

All finance-specific governance logic extracted from Core RiskEngine.
Core only calls validate_fields / validate_numeric / validate_limits /
validate_behavioral — it never knows about stop_loss, is_chasing, etc.
"""

from __future__ import annotations
from typing import Protocol

# ── Protocol (defined here; eventually moves to governance/protocols.py) ──


class RejectReason:
    def __init__(self, message: str):
        self.message = message


class EscalateReason:
    def __init__(self, message: str):
        self.message = message


class PackIntakePolicy(Protocol):
    """Protocol that any domain Pack can implement for intake validation."""

    def validate_fields(self, payload: dict) -> list[RejectReason | EscalateReason]:
        """Validate required field presence and type. Return reject/escalate reasons."""
        ...

    def validate_numeric(self, payload: dict) -> list[RejectReason]:
        """Validate numeric field values. Return reject reasons."""
        ...

    def validate_limits(self, payload: dict) -> list[RejectReason]:
        """Validate risk limit ratios. Return reject reasons."""
        ...

    def validate_behavioral(self, payload: dict) -> list[EscalateReason]:
        """Validate behavioral red flags. Return escalate reasons."""
        ...


# ── Finance Implementation ────────────────────────────────────────────

_MAX_LOSS_TO_RISK_UNIT_RATIO = 2.0
_MAX_POSITION_TO_RISK_UNIT_RATIO = 10.0

_EMOTIONAL_RISK_KEYWORDS: frozenset[str] = frozenset({
    "stress",
    "stressed",
    "stressful",
    "fear",
    "fearful",
    "scared",
    "terrified",
    "panicked",
    "panic",
    "anger",
    "angry",
    "furious",
    "frustrated",
    "fomo",
    "greedy",
    "desperate",
    "reckless",
    "revenge",
    "impulsive",
})

_BANNED_THESIS_PATTERNS: frozenset[str] = frozenset({
    "just feels right",
    "no specific thesis",
    "trust me",
    "yolo",
    "vibes",
    "gut feeling",
    "intuition",
    "going to the moon",
    "to the moon",
    "moon shot",
    "full port",
    "all in",
    "yolo all in",
    "pumping",
    "fomo is real",
    "i need in",
    "no idea",
    "whatever",
    "because why not",
    "feeling lucky",
    "hope this works",
    "pray for me",
})


class TradingDisciplinePolicy:
    """Finance Pack intake policy — all H-5 gate rules.

    Extracted from Core RiskEngine per ADR-006.
    """

    def validate_fields(self, payload: dict) -> list[RejectReason | EscalateReason]:
        reasons: list[RejectReason | EscalateReason] = []

        # ── thesis: required + quality ──
        thesis = _as_str(payload.get("thesis"))
        if not thesis:
            reasons.append(RejectReason("Missing required field: thesis."))
        else:
            # Thesis quality checks (was H-9C3)
            lowered = thesis.lower()
            for banned in _BANNED_THESIS_PATTERNS:
                if banned in lowered:
                    reasons.append(RejectReason(f"Thesis quality rejected: banned pattern '{banned}'."))
                    break
            if len(thesis.strip()) < 50:
                reasons.append(EscalateReason(f"Thesis too short ({len(thesis.strip())} chars, min 50)."))
            if not _has_verifiability(thesis):
                reasons.append(EscalateReason("Thesis lacks verifiability criteria."))

        # ── stop_loss: required ──
        if not _as_str(payload.get("stop_loss")):
            reasons.append(RejectReason("Missing required field: stop_loss."))

        # ── emotional_state: required ──
        if not _as_str(payload.get("emotional_state")):
            reasons.append(RejectReason("Missing required field: emotional_state."))

        return reasons

    def validate_numeric(self, payload: dict) -> list[RejectReason]:
        reasons: list[RejectReason] = []

        max_loss = _as_positive_float(payload.get("max_loss_usdt"))
        if max_loss is None:
            reasons.append(RejectReason("Missing or non-positive: max_loss_usdt."))

        position_size = _as_positive_float(payload.get("position_size_usdt"))
        if position_size is None:
            reasons.append(RejectReason("Missing or non-positive: position_size_usdt."))

        risk_unit = _as_positive_float(payload.get("risk_unit_usdt"))
        if risk_unit is None:
            reasons.append(RejectReason("Missing or non-positive: risk_unit_usdt."))

        return reasons

    def validate_limits(self, payload: dict) -> list[RejectReason]:
        reasons: list[RejectReason] = []
        max_loss = _as_positive_float(payload.get("max_loss_usdt"))
        position_size = _as_positive_float(payload.get("position_size_usdt"))
        risk_unit = _as_positive_float(payload.get("risk_unit_usdt"))

        if max_loss and risk_unit and risk_unit > 0:
            if max_loss > _MAX_LOSS_TO_RISK_UNIT_RATIO * risk_unit:
                reasons.append(
                    RejectReason(
                        f"max_loss_usdt ({max_loss}) exceeds "
                        f"{_MAX_LOSS_TO_RISK_UNIT_RATIO}× risk_unit_usdt ({risk_unit})."
                    )
                )

        if position_size and risk_unit and risk_unit > 0:
            if position_size > _MAX_POSITION_TO_RISK_UNIT_RATIO * risk_unit:
                reasons.append(
                    RejectReason(
                        f"position_size_usdt ({position_size}) exceeds "
                        f"{_MAX_POSITION_TO_RISK_UNIT_RATIO}× risk_unit_usdt ({risk_unit})."
                    )
                )

        return reasons

    def validate_behavioral(self, payload: dict) -> list[EscalateReason]:
        reasons: list[EscalateReason] = []

        if payload.get("is_revenge_trade") is True:
            reasons.append(EscalateReason("is_revenge_trade=true."))

        if payload.get("is_chasing") is True:
            reasons.append(EscalateReason("is_chasing=true."))

        emotional = _as_str(payload.get("emotional_state"))
        if emotional and _contains_emotional_risk(emotional):
            reasons.append(EscalateReason(f"emotional_state='{emotional}' indicates risk."))

        rule_exceptions = payload.get("rule_exceptions")
        if isinstance(rule_exceptions, list) and len(rule_exceptions) > 0:
            reasons.append(EscalateReason(f"rule_exceptions not empty ({len(rule_exceptions)} item(s))."))

        confidence = payload.get("confidence")
        if isinstance(confidence, (int, float)) and 0 <= confidence < 0.3:
            reasons.append(EscalateReason(f"confidence={confidence} below 0.3 threshold."))

        return reasons


# ── Private helpers (copied from RiskEngine) ──────────────────────


def _as_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _as_positive_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _contains_emotional_risk(emotional_state: str) -> bool:
    lowered = emotional_state.lower()
    return any(kw in lowered for kw in _EMOTIONAL_RISK_KEYWORDS)


def _has_verifiability(thesis: str) -> bool:
    """Check if thesis contains invalidation or confirmation language."""
    lowered = thesis.lower()
    verifiability_markers = [
        "unless",
        "invalidated if",
        "invalid if",
        "confirmed by",
        "confirmation",
        "confirm",
        "if price",
        "if the",
        "stop if",
        "exit if",
        "target at",
        "target is",
        "entry at",
    ]
    return any(marker in lowered for marker in verifiability_markers)
```

**Step 2: 写 Finance Pack policy 单元测试**

```python
# tests/unit/finance/test_trading_discipline_policy.py
"""TradingDisciplinePolicy 单元测试 — 验证从 RiskEngine 提取后的行为一致性。

每个测试对应 H-5/H-9C 的一个 gate 场景。
"""

import pytest
from packs.finance.trading_discipline_policy import (
    TradingDisciplinePolicy,
    RejectReason,
    EscalateReason,
)


@pytest.fixture
def policy():
    return TradingDisciplinePolicy()


# ── Gate 1: Field existence + Thesis quality ──


def test_reject_missing_thesis(policy):
    reasons = policy.validate_fields({"stop_loss": "2%", "emotional_state": "calm"})
    assert any("thesis" in r.message.lower() for r in reasons if isinstance(r, RejectReason))


def test_reject_missing_stop_loss(policy):
    reasons = policy.validate_fields({"thesis": "BTC breaking resistance with volume", "emotional_state": "calm"})
    assert any("stop_loss" in r.message.lower() for r in reasons if isinstance(r, RejectReason))


def test_reject_missing_emotional_state(policy):
    reasons = policy.validate_fields({"thesis": "BTC breaking resistance with volume", "stop_loss": "2%"})
    assert any("emotional_state" in r.message.lower() for r in reasons if isinstance(r, RejectReason))


def test_reject_banned_thesis(policy):
    reasons = policy.validate_fields({
        "thesis": "No specific thesis, just feels right",
        "stop_loss": "2%",
        "emotional_state": "calm",
    })
    reject_msgs = [r.message for r in reasons if isinstance(r, RejectReason)]
    assert any("banned pattern" in m for m in reject_msgs)


def test_escalate_short_thesis(policy):
    reasons = policy.validate_fields({
        "thesis": "Short thesis",
        "stop_loss": "2%",
        "emotional_state": "calm",
    })
    escalate_msgs = [r.message for r in reasons if isinstance(r, EscalateReason)]
    assert any("too short" in m for m in escalate_msgs)


def test_escalate_no_verifiability(policy):
    reasons = policy.validate_fields({
        "thesis": "BTC is going up because trend is strong and volume is high",
        "stop_loss": "2%",
        "emotional_state": "calm",
    })
    escalate_msgs = [r.message for r in reasons if isinstance(r, EscalateReason)]
    assert any("verifiability" in m.lower() for m in escalate_msgs)


def test_valid_thesis_passes(policy):
    reasons = policy.validate_fields({
        "thesis": "BTC breaking above resistance with volume confirmation; invalidated if price closes below 200 EMA.",
        "stop_loss": "2%",
        "emotional_state": "calm",
    })
    reject_msgs = [r.message for r in reasons if isinstance(r, RejectReason)]
    escalate_msgs = [r.message for r in reasons if isinstance(r, EscalateReason)]
    assert len(reject_msgs) == 0
    assert len(escalate_msgs) == 0


# ── Gate 2: Numeric fields ──


def test_reject_missing_max_loss(policy):
    reasons = policy.validate_numeric({"position_size_usdt": 100.0, "risk_unit_usdt": 10.0})
    assert any("max_loss_usdt" in r.message for r in reasons)


def test_reject_missing_position_size(policy):
    reasons = policy.validate_numeric({"max_loss_usdt": 20.0, "risk_unit_usdt": 10.0})
    assert any("position_size_usdt" in r.message for r in reasons)


def test_reject_missing_risk_unit(policy):
    reasons = policy.validate_numeric({"max_loss_usdt": 20.0, "position_size_usdt": 100.0})
    assert any("risk_unit_usdt" in r.message for r in reasons)


# ── Gate 3: Risk limits ──


def test_reject_max_loss_exceeds_ratio(policy):
    reasons = policy.validate_limits({
        "max_loss_usdt": 500.0,
        "position_size_usdt": 100.0,
        "risk_unit_usdt": 100.0,
    })
    assert any("max_loss_usdt" in r.message and "exceeds" in r.message for r in reasons)


def test_reject_position_size_exceeds_ratio(policy):
    reasons = policy.validate_limits({
        "max_loss_usdt": 100.0,
        "position_size_usdt": 5000.0,
        "risk_unit_usdt": 100.0,
    })
    assert any("position_size_usdt" in r.message and "exceeds" in r.message for r in reasons)


def test_valid_limits_pass(policy):
    reasons = policy.validate_limits({
        "max_loss_usdt": 200.0,
        "position_size_usdt": 1000.0,
        "risk_unit_usdt": 100.0,
    })
    assert len([r for r in reasons if isinstance(r, RejectReason)]) == 0


# ── Gate 4: Behavioral ──


def test_escalate_revenge_trade(policy):
    reasons = policy.validate_behavioral({"is_revenge_trade": True, "is_chasing": False})
    assert any("is_revenge_trade" in r.message for r in reasons)


def test_escalate_chasing(policy):
    reasons = policy.validate_behavioral({"is_revenge_trade": False, "is_chasing": True})
    assert any("is_chasing" in r.message for r in reasons)


def test_escalate_emotional_risk(policy):
    reasons = policy.validate_behavioral({"emotional_state": "stressed"})
    assert any("emotional_state" in r.message for r in reasons)


def test_escalate_rule_exceptions(policy):
    reasons = policy.validate_behavioral({"rule_exceptions": ["override"]})
    assert any("rule_exceptions" in r.message for r in reasons)


def test_escalate_low_confidence(policy):
    reasons = policy.validate_behavioral({"confidence": 0.2})
    assert any("confidence" in r.message for r in reasons)


def test_calm_no_flags_passes(policy):
    reasons = policy.validate_behavioral({
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.7,
        "rule_exceptions": [],
    })
    assert len(reasons) == 0
```

**Step 3: 运行 Pack policy 测试**

```bash
uv run pytest tests/unit/finance/test_trading_discipline_policy.py -v
```

**预期**: 16 passed。

**Step 4: 提交 Pack policy**

```bash
git add packs/finance/trading_discipline_policy.py tests/unit/finance/test_trading_discipline_policy.py
git commit -m "feat(pack): extract finance TradingDisciplinePolicy from Core RiskEngine — ADR-006"
```

---

### Task 3.4 (实现): 重构 RiskEngine 使用 Pack policy — TDD

**目标**: RiskEngine 不再直接引用 finance 字段名，改为委托给 Pack policy。

**文件**:
- 修改: `governance/risk_engine/engine.py`
- 修改: `governance/policy_source.py`（注入 pack policy）
- 修改: 所有调用 `validate_intake()` 的地方（注入 pack_policy 参数）

**Step 1: 重构 RiskEngine.validate_intake()**

```python
# governance/risk_engine/engine.py — 简化后的 validate_intake


def validate_intake(
    self,
    intake: DecisionIntake,
    pack_policy=None,  # ← ADR-006: optional PackIntakePolicy
    advisory_hints=None,
) -> GovernanceDecision:
    """Evaluate a DecisionIntake and return execute/escalate/reject.

    Core gates (generic, domain-agnostic):
      Gate 0: intake.status must be "validated"

    Pack gates (delegated to pack_policy):
      Gate 1: field existence + quality
      Gate 2: numeric field values
      Gate 3: risk limit ratios
      Gate 4: behavioral red flags
    """
    hints = tuple(advisory_hints or ())
    snapshot = self.policy_source.get_active_snapshot()

    reject_reasons: list[str] = []
    escalate_reasons: list[str] = []

    # ── Gate 0: intake must be validated (generic) ──
    if intake.status != "validated":
        reject_reasons.append(f"Intake status is '{intake.status}' — only validated intakes can be governed.")

    # ── Pack policy gates (ADR-006) ──
    if pack_policy is not None and intake.payload:
        payload = intake.payload

        # Gate 1: field existence + quality
        for reason in pack_policy.validate_fields(payload):
            if isinstance(reason, RejectReason):
                reject_reasons.append(reason.message)
            elif isinstance(reason, EscalateReason):
                escalate_reasons.append(reason.message)

        # Gate 2: numeric fields
        for reason in pack_policy.validate_numeric(payload):
            reject_reasons.append(reason.message)

        # Gate 3: risk limits
        for reason in pack_policy.validate_limits(payload):
            reject_reasons.append(reason.message)

        # Gate 4: behavioral
        for reason in pack_policy.validate_behavioral(payload):
            escalate_reasons.append(reason.message)

    # ── Decision (priority: reject > escalate > execute) ──
    if reject_reasons:
        return GovernanceDecision(
            decision="reject",
            reasons=reject_reasons,
            source="risk_engine.finance_governance_hard_gate",
            advisory_hints=hints,
            policy_set_id=snapshot.policy_set_id,
            active_policy_ids=snapshot.active_policy_ids,
            default_decision_rule_ids=snapshot.default_decision_rule_ids,
        )

    if escalate_reasons:
        return GovernanceDecision(
            decision="escalate",
            reasons=escalate_reasons,
            source="risk_engine.finance_governance_hard_gate",
            advisory_hints=hints,
            policy_set_id=snapshot.policy_set_id,
            active_policy_ids=snapshot.active_policy_ids,
            default_decision_rule_ids=snapshot.default_decision_rule_ids,
        )

    return GovernanceDecision(
        decision="execute",
        reasons=["Passed all governance gates."],
        source="risk_engine.finance_governance_hard_gate",
        advisory_hints=hints,
        policy_set_id=snapshot.policy_set_id,
        active_policy_ids=snapshot.active_policy_ids,
        default_decision_rule_ids=snapshot.default_decision_rule_ids,
    )
```

**注意**: 原有的 `_EMOTIONAL_RISK_KEYWORDS`、`_contains_emotional_risk()`、`_as_str()`、`_as_positive_float()` 等私有辅助函数可以从 RiskEngine 中移除（已复制到 Pack policy）。

**Step 2: 找到所有调用 validate_intake() 的地方，注入 pack_policy**

```bash
cd /root/projects/financial-ai-os
rg "validate_intake\(" --type py -n
```

对每个调用点，添加:
```python
from packs.finance.trading_discipline_policy import TradingDisciplinePolicy

pack_policy = TradingDisciplinePolicy()
decision = risk_engine.validate_intake(intake, pack_policy=pack_policy)
```

**Step 3: 运行全部现有 H-5/H-9C 测试，确认行为一致**

```bash
uv run pytest tests/unit/test_finance_decision_intake_validation.py -v
uv run pytest tests/unit/test_h7_manual_outcome.py -v
uv run pytest tests/unit/test_h6_plan_only_receipt.py -v
```

**预期**: 全部通过（或极少适配）。

**Step 4: 运行完整测试套件**

```bash
uv run pytest tests/unit/ tests/integration/ -q --no-header
```

**预期**: 全部通过。如有失败，逐个修复（可能是 mock 路径变化或导入路径变化）。

**Step 5: PG 全回归**

```bash
PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test uv run pytest tests/ -q --no-header -p no:cacheprovider
```

**预期**: 全部通过。

**Step 6: 验证 RiskEngine 不再有 finance 字段名**

```bash
cd /root/projects/financial-ai-os
rg "stop_loss|max_loss_usdt|position_size_usdt|risk_unit_usdt|is_revenge_trade|is_chasing" governance/risk_engine/engine.py
```

**预期**: 无匹配（或仅在注释/文档字符串中）。

**Step 7: 提交 + Tag**

```bash
git add governance/risk_engine/engine.py governance/policy_source.py
git commit -m "refactor(adr-006): extract finance semantics from Core RiskEngine into Pack TradingDisciplinePolicy"
git tag post-p4-finance-extraction
```

---

## Phase 4: 文档清理 (2 个任务, 预计 15 分钟)

### Task 4.1: 确认所有非 archive 文档无 finance-as-identity 残留

```bash
cd /root/projects/financial-ai-os
# 扫描 docs/（排除 archive/）和 policies/
rg "financial-ai-os.*product|trading system|Hermes as.*identity|execution-grade runtime" docs/ policies/ --glob '!docs/archive/**' -n
```

**预期**: 无匹配（或仅在命名说明文档中）。

### Task 4.2: 更新命名文档，标注 P4 收口后的命名状态

在 `docs/naming.md` 末尾追加:

```markdown
## P4 收口后状态 (2026-04-26)

- **内部代码**: 保持现有命名不变。
- **文档叙事**: 统一使用 Ordivon 作为系统身份，Finance 为第一个 Pack。
- **外部品牌**: Ordivon 预留，尚未在代码中激活。
- **文件命名**: 含 `pfios` 的文件名暂不重命名（cost > benefit），内容已全部更新。
```

```bash
git add docs/naming.md
git commit -m "docs: update naming status post-P4 closure"
```

---

## Phase 5: 30 次扩展狗粮 (3 个任务, 预计 40 分钟)

**目标**: 从 9 次自动化狗粮扩展到 30 次，覆盖更多边界场景。

### Task 5.1: 设计 30 次狗粮场景矩阵

**场景矩阵**（每行一次运行）:

| # | 场景 | 预期 governance | 是否全链路 | 测试重点 |
|---|------|-----------------|-----------|---------|
| 1 | 标准 BTC swing（已覆盖: Run 5） | execute | ✅ | 基线 |
| 2 | 保守 LINK 交易（已覆盖: Run 7） | execute | ✅ | 基线 |
| 3 | 假突破 AVAX（已覆盖: Run 9） | execute | ✅ | 损失路径 |
| 4 | 过度杠杆 ETH — reject | reject | — | 风险限制 |
| 5 | Meme 追涨 — reject | reject | — | is_chasing |
| 6 | FOMO 追涨 — reject | reject | — | is_chasing + 情绪 |
| 7 | 模糊 thesis — escalate | escalate | — | thesis 可证伪性 |
| 8 | 短 thesis — escalate | escalate | — | thesis 长度 |
| 9 | 弱 thesis（已封堵）— reject | reject | — | banned pattern |
| 10-15 | 新场景：不同品种 + 不同时间框架 | 混合 | 部分 | 多样化 |
| 16-20 | 新场景：边界风险比率（刚好通过/刚好拒绝） | 混合 | 部分 | 极限值 |
| 21-25 | 新场景：情绪状态变化（calm/neutral/excited/anxious/fearful） | 混合 | 部分 | 情绪门 |
| 26-30 | 新场景：全链路完成（3 execute） | execute | ✅ | KF 生成验证 |

### Task 5.2: 扩展狗粮脚本

在现有 `scripts/h9_dogfood_runs.py` 基础上添加 21 个新运行（Run 11-31），覆盖新场景。

**文件**: 修改 `scripts/h9_dogfood_runs.py`

**实施方式**: 添加 `# --- Run 11 ---` 到 `# --- Run 31 ---` 的代码块。

**Step 1**: 写新运行

```python
# --- Run 11: SOLUSDT moderate position, borderline risk ratio ---
print("\n=== RUN 11: SOL moderate, borderline risk ===")
r11 = intake({
    "symbol": "SOLUSDT",
    "timeframe": "4h",
    "direction": "long",
    "thesis": "SOL reclaiming range low with volume spike confirming accumulation; "
    "invalidated if price closes back below range low.",
    "stop_loss": "4%",
    "max_loss_usdt": 200,
    "position_size_usdt": 1000,
    "risk_unit_usdt": 100,
    "is_revenge_trade": False,
    "is_chasing": False,
    "emotional_state": "neutral",
    "confidence": 0.65,
})
r11_gov = govern(r11["id"]) if "id" in r11 else {}
# max_loss=200, risk_unit=100 → ratio=2.0 → just at boundary → should pass
runs.append({"tag": "Run 11", "intake": r11, "governance": r11_gov})
print(f"  intake_id={r11.get('id')} → governance={r11_gov.get('governance_decision')}")

# --- Run 12: BTCUSDT anxious emotional state → escalate ---
print("\n=== RUN 12: BTC anxious → escalate ===")
r12 = intake({
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "direction": "short",
    "thesis": "BTC rejected at range high with bearish engulfing candle; invalidated if price closes above range high.",
    "stop_loss": "1.5%",
    "max_loss_usdt": 300,
    "position_size_usdt": 2000,
    "risk_unit_usdt": 200,
    "is_revenge_trade": False,
    "is_chasing": False,
    "emotional_state": "anxious",
    "confidence": 0.5,
})
r12_gov = govern(r12["id"]) if "id" in r12 else {}
runs.append({"tag": "Run 12", "intake": r12, "governance": r12_gov})
print(f"  intake_id={r12.get('id')} → governance={r12_gov.get('governance_decision')}")

# ... (Run 13-31 同理)
```

**Step 2**: 运行扩展狗粮

```bash
cd /root/projects/financial-ai-os
uv run python scripts/h9_dogfood_runs.py
```

**Step 3**: 提交

```bash
git add scripts/h9_dogfood_runs.py
git commit -m "feat(h9): extend dogfood script to 30 runs with diverse scenarios"
```

---

### Task 5.3: 记录 30 次狗粮证据

**目标**: 更新 `docs/runtime/h9-evidence-report.md`，添加 H-9F 部分。

**内容**:
- 30 次运行摘要表（governance 分布）
- 全链路完成详情
- KF 生成验证
- 新发现的问题（如有）
- 与 H-9E 的对比

```bash
git add docs/runtime/h9-evidence-report.md
git commit -m "docs(h9f): add 30-run extended dogfood evidence"
git tag h9f-30-run-evidence
```

---

## Phase 6: 最终验证与收口 (2 个任务, 预计 15 分钟)

### Task 6.1: 全量回归测试

```bash
cd /root/projects/financial-ai-os

# 1. 单元测试
uv run pytest tests/unit -q --no-header -p no:cacheprovider

# 2. 集成测试
uv run pytest tests/integration -q --no-header

# 3. PG 全回归
PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test uv run pytest tests/ -q --no-header -p no:cacheprovider

# 4. OpenAPI 契约
uv run pytest tests/contracts/ -v

# 5. 狗粮验证
uv run python scripts/h9c_verification.py
```

**预期**: 全部通过。0 失败，0 跳过，0 手动干预。

---

### Task 6.2: 债务清零声明 + 最终 Tag

**目标**: 更新重审计报告，标注全部债务已清零。

**文件**: 更新 `docs/audits/p4-closure/re-audit-report.md`

在报告末尾追加:

```markdown
## Post-Closure Debt Clearance (2026-04-26)

All 5 non-blocking debts from the re-audit have been resolved:

| # | Debt | Resolution | Tag |
|---|------|-----------|-----|
| 1 | H-10 KF 泛化 | extract_for_review_by_id + fallback | h10-kf-generalization |
| 2 | H-8R API 响应 | ReviewResult.outcome_ref fields | h8r-outcome-ref-response |
| 3 | Finance 语义提取 | TradingDisciplinePolicy + ADR-006 | post-p4-finance-extraction |
| 4 | 狗粮脚本提交 | scripts committed | h9-scripts-committed |
| 5 | 狗粮样本量 | 30-run extended dogfood | h9f-30-run-evidence |

Blocking debt: NONE (verified before)
Non-blocking debt: ALL CLEARED

### Final P4 Closure Status: PASS (CLEAN)

All debts cleared. System is ready for P5 pre-design.
```

**最终 Tag**:

```bash
git add docs/audits/p4-closure/re-audit-report.md
git commit -m "docs: declare P4 closure — all debts cleared"
git tag p4-closure-debt-cleared
```

---

## 执行顺序总览

```
Phase 0 (基础设施)
  ├── 0.1 基线
  ├── 0.2 提交脚本
  └── 0.3 确认服务

Phase 1 (H-10 KF 泛化)
  ├── 1.1 审计（只读）
  ├── 1.2 list_for_review → TDD
  ├── 1.3 extract_for_review_by_id → TDD
  ├── 1.4 _build_knowledge_feedback 回退 → TDD
  └── 1.5 集成验证 + Tag

Phase 2 (H-8R API 响应)
  ├── 2.1 验证 schema
  ├── 2.2 ReviewResult + 填充 → TDD
  └── 2.3 集成验证 + OpenAPI 快照 + Tag

Phase 3 (ADR-006 Finance 提取)  ← 最大变更
  ├── 3.1 ADR 文档
  ├── 3.2 审计分类
  ├── 3.3 TradingDisciplinePolicy → TDD
  └── 3.4 RiskEngine 重构 → TDD + Tag

Phase 4 (文档清理)
  ├── 4.1 残留扫描
  └── 4.2 命名文档更新

Phase 5 (30 次狗粮)
  ├── 5.1 场景矩阵
  ├── 5.2 扩展脚本
  └── 5.3 证据记录 + Tag

Phase 6 (最终验证)
  ├── 6.1 全量回归
  └── 6.2 声明 + 最终 Tag
```

**预计总耗时**: ~4 小时（不含 Phase 3 的调试时间）

**风险提示**:
- Phase 3（Finance 提取）是最大的重构。所有调用 `validate_intake()` 的地方都需要注入 `pack_policy`。测试覆盖充分时可以安全推进。
- 如果在 Phase 3 发现阻塞问题，可以先回滚到 Task 3.3 之前，只完成 Phase 1+2+4+5，Phase 3 作为独立 PR 后续推进。
