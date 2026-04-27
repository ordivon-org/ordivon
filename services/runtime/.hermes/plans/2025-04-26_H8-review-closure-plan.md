# H-8: Review Closure on Manual Outcome — 只读审计 + 最小实现计划

**日期**: 2025-04-26  
**阶段**: H-8  
**状态**: 审计完成，等待确认后实现

---

## 1. 审计结果 (Read-Only Audit)

### 1.1 当前 Review 创建和完成路径

**数据层 (已完成)**:
- `ReviewORM` (`domains/journal/orm.py:19-20`): 已有 `outcome_ref_type` / `outcome_ref_id` 列
- `Review` 模型 (`domains/journal/models.py:18-19`): 已有 `outcome_ref_type: str | None`, `outcome_ref_id: str | None`
- `ReviewRepository.create()` (`domains/journal/repository.py:29-30`): 已持久化 outcome_ref 字段
- `ReviewRepository.to_model()` (`domains/journal/repository.py:118-119`): 已读回 outcome_ref 字段

**服务层**:
- `ReviewService.create()` → `create_with_options()` → `repository.create()`: 透传全部字段 ✅
- `ReviewService.complete_review()` (line 66-147): 设置 observed_outcome, verdict, cause_tags, lessons, followup_actions 等字段，**不修改** outcome_ref_type/outcome_ref_id → **自动保留** ✅

**能力层 (ReviewCapability)**:
- `create_review()` (line 159-181): 只接受 `recommendation_id`, `review_type`, `expected_outcome` — **不支持 outcome_ref 字段** ❌
- `complete_review()` (line 183-252): 委托给 adapter → service.complete_review() ✅
- `get_detail()` (line 79-119): 不返回 outcome_ref_type/outcome_ref_id 字段 ❌

**API 层**:
- `ReviewCreateRequest` (schema): 不支持 outcome_ref_type/outcome_ref_id ❌
- `ReviewDetailResponse` (schema): 不支持 outcome_ref_type/outcome_ref_id ❌
- `POST /api/v1/reviews/submit`: 使用 ReviewCreateRequest ❌
- `POST /api/v1/reviews/{review_id}/complete`: 使用 ReviewCompleteRequest ✅ (不变)
- `GET /api/v1/reviews/{review_id}`: 返回 ReviewDetailResponse ❌ (缺少 outcome_ref)

**应用层服务门面**:
- `apps/api/app/services/review_service.py`: `create_review()` 不接受 outcome_ref 字段 ❌

### 1.2 complete_review 是否保留 outcome_ref_type/outcome_ref_id?

**是** ✅ — `ReviewService.complete_review()` 只设置 outcome/verdict/lessons 字段，不触碰 outcome_ref 字段。从 DB 读取的 row 保留原值。

### 1.3 Lesson / KnowledgeFeedback 派生路径

**Lesson 派生** (line 116-128):
- 在 `complete_review()` 中，遍历 lessons 列表，创建 `Lesson` 模型
- Lesson 包含 `review_id` (非空) 和 `recommendation_id` (可为 None)
- 即使 review 没有 recommendation_id，Lesson 仍会基于 review_id 创建 ✅
- **但是**: Lesson 的 `source_refs` 不包含 outcome 引用

**KnowledgeFeedback 派生** (line 196-233):
- `_build_knowledge_feedback()` 调用 `LessonExtractionService.extract_for_recommendation(recommendation_id)`
- **当 recommendation_id 为 None 时返回 None** ❌ (line 197-198)
- 这意味着: 如果 review 仅引用 manual outcome 且无 recommendation_id，不会生成 KnowledgeFeedback
- H-8 规则允许: "completed review derives KnowledgeFeedback when existing H-3 path supports it"

**LessonExtractionService** (`knowledge/extraction.py`):
- `extract_for_recommendation()`: 查询 lessons + outcomes，然后用 `KnowledgeEntryBuilder.from_lesson()` / `from_lesson_with_outcome()` 构建知识条目
- `from_lesson()` (adapters.py:12-63): 从 lesson 创建 KnowledgeEntry，evidence_refs 包含 review_id, recommendation_id, wiki_path, source_refs — **不含 manual outcome 引用**
- `from_lesson_with_outcome()` (adapters.py:65-85): 接受 `OutcomeSnapshot` (strategy outcome) — **不能直接接受 FinanceManualOutcome**

### 1.4 KnowledgeFeedback 能否引用 outcome evidence?

**当前**: 不能。原因:
1. `KnowledgeEntryBuilder.from_lesson()` 的 evidence_refs 不包括 outcome 引用
2. `from_lesson_with_outcome()` 接受 `OutcomeSnapshot`，不接受 `FinanceManualOutcome`
3. `LessonExtractionService` 只查询 strategy 层的 `OutcomeRepository`，不查询 `FinanceManualOutcomeRepository`

**H-8 最小需求**: 当 review 的 outcome_ref_type="finance_manual_outcome" 时，知识条目 evidence 应包含 outcome 引用 (作为支持规则)

### 1.5 现有 Review API 端点

两个 review 路由:
1. `apps/api/app/api/v1/reviews.py` — 主路由 (挂载在 `/api/v1/reviews`)
2. `apps/api/app/routers/reviews.py` — 旧路由 (挂载在 `/reviews`，可能在另一处)

主路由端点:
- `POST /api/v1/reviews/submit` — 提交 review (使用 submit_review)
- `GET /api/v1/reviews/pending` — 列出待处理 review
- `GET /api/v1/reviews/{review_id}` — 查看 review 详情
- `POST /api/v1/reviews/{review_id}/complete` — 完成 review
- `POST /api/v1/reviews/generate-skeleton` — 生成骨架

**注意**: `POST /api/v1/reviews/submit` 调用 `review_capability.submit_review()` (line 110)，它内部创建 Review 对象但不支持 outcome_ref 传参。submit_review 比 create_review 更复杂，涉及 execution adapter。

### 1.6 ORM Schema 变更需求

**不需要** ✅ — `ReviewORM` 已有 `outcome_ref_type` 和 `outcome_ref_id` 列，无需迁移。

### 1.7 当前 Critical Gap 总结

| 能力 | 当前状态 | H-8 需求 | 差距 |
|------|---------|---------|------|
| Review 创建接受 outcome_ref | 能力层不支持 | 必须支持 | schema + capability |
| outcome_ref 验证 (manual outcome 存在性) | 无 | 必须验证 | API/service 层补充 |
| complete_review 保留 outcome_ref | 自动保留 | 保留即可 | 无差距 |
| complete_review 派生 Lessons | 工作正常 | 工作正常 | 无差距 |
| complete_review 派生 KnowledgeFeedback | 需 recommendation_id | 有时派生 | 无差距(规则允许) |
| Knowledge evidence 含 outcome 引用 | 不支持 | 支持时更好 | 可选增强 |
| Review 详情包含 outcome_ref | 不支持 | 支持 | schema + capability |
| 不创建 CandidateRule | complete_review 不创建 | 不创建 | 无差距 |
| 不提升 Policy | complete_review 不提升 | 不提升 | 无差距 |
| 不触发 broker/order/trade | complete_review 不触发 | 不触发 | 无差距 |

---

## 2. H-8 最小实现计划

### 策略: 最小侵入 — 只扩展现有路径，不创建新路径

遵循 H-8 原则: 只打通 Manual Outcome → Review → complete → Lesson / KnowledgeFeedback 闭环。

### Step 1: 扩展 ReviewCreateRequest Schema

**文件**: `apps/api/app/schemas/reviews.py`

```python
class ReviewCreateRequest(BaseModel):
    # ... existing fields ...
    outcome_ref_type: Optional[str] = None    # NEW
    outcome_ref_id: Optional[str] = None      # NEW
```

### Step 2: 扩展 ReviewDetailResponse Schema

**文件**: `apps/api/app/schemas/reviews.py`

```python
class ReviewDetailResponse(BaseModel):
    # ... existing fields ...
    outcome_ref_type: Optional[str] = None    # NEW
    outcome_ref_id: Optional[str] = None      # NEW
```

### Step 3: 扩展 ReviewCapability.create_review()

**文件**: `capabilities/workflow/reviews.py`

```python
def create_review(
    self,
    service: ReviewService,
    recommendation_id: str,
    action_context: ActionContext | None,
    review_type: str = "recommendation_postmortem",
    expected_outcome: str | None = None,
    outcome_ref_type: str | None = None,       # NEW
    outcome_ref_id: str | None = None,         # NEW
) -> ReviewResult:
    review = Review(
        recommendation_id=recommendation_id,
        review_type=review_type,
        expected_outcome=expected_outcome or "",
        outcome_ref_type=outcome_ref_type,     # NEW
        outcome_ref_id=outcome_ref_id,         # NEW
    )
    row = service.create(review)
    # ... rest unchanged ...
```

### Step 4: 扩展 ReviewCapability.get_detail() 以包含 outcome_ref

**文件**: `capabilities/workflow/reviews.py`

在 `get_detail()` 返回的 `ReviewDetailResult` 中添加:
```python
outcome_ref_type=review.outcome_ref_type,
outcome_ref_id=review.outcome_ref_id,
```

### Step 5: 扩展 ReviewCapability 合约

**文件**: `capabilities/contracts.py`

在 `ReviewDetailResult` 中添加 `outcome_ref_type` 和 `outcome_ref_id` 字段（如果不在已有 dataclass 中）。

### Step 6: API 端点添加 outcome 引用验证

**文件**: `apps/api/app/api/v1/reviews.py`

在 `submit_performance_review` 中:
- 将 outcome_ref_type/outcome_ref_id 传入选出 payload
- 如果 outcome_ref_type="finance_manual_outcome"，验证 FinanceManualOutcome 存在
- 如果 outcome_ref_id 指向不存在或类型不匹配的 outcome，返回 422

### Step 7: 旧路由同步更新

**文件**: `apps/api/app/routers/reviews.py`

在 `create_review` 中同步支持 outcome_ref 字段（保持一致性）。

### Step 8: 扩展 Lesson model 的 source_refs 以包含 outcome 引用

**文件**: `domains/journal/service.py` (complete_review 方法)

当 review 有 outcome_ref_id 时，将该引用添加到创建的 Lesson 的 source_refs 中。

### Step 9: 更新 OpenAPI 快照

运行快照重新生成命令。

### Step 10: 添加 H-8 集成测试

**文件**: `tests/integration/test_h8_review_closure.py`（新文件）

按 H-8 要求的 10 个测试:
1. review can be created with finance manual outcome reference
2. review rejects missing finance manual outcome reference
3. complete_review preserves outcome_ref_type/outcome_ref_id
4. complete_review derives lesson rows
5. complete_review derives knowledge feedback (when recommendation_id exists)
6. knowledge evidence includes review reference
7. knowledge evidence includes outcome reference if supported
8. completing review does not create CandidateRule
9. completing review does not promote Policy
10. completing review does not trigger broker/order/trade

---

## 3. 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `apps/api/app/schemas/reviews.py` | 扩展 | ReviewCreateRequest + ReviewDetailResponse 添加 outcome_ref 字段 |
| `apps/api/app/api/v1/reviews.py` | 扩展 | 传递 outcome_ref, 添加验证逻辑 |
| `apps/api/app/routers/reviews.py` | 扩展 | 同步更新旧路由 |
| `apps/api/app/services/review_service.py` | 扩展 | create_review 传递 outcome_ref |
| `capabilities/workflow/reviews.py` | 扩展 | create_review/get_detail 支持 outcome_ref |
| `capabilities/contracts.py` | 扩展 | ReviewDetailResult 添加 outcome_ref 字段 |
| `domains/journal/service.py` | 扩展 | Lesson source_refs 包含 outcome 引用 |
| `tests/contracts/openapi.snapshot.json` | 更新 | 重新生成 |
| `tests/integration/test_h8_review_closure.py` | 新增 | H-8 集成测试 |

### 不会修改

| 领域 | 不修改原因 |
|------|-----------|
| ORM / 数据库 schema | 已有字段 |
| ReviewRepository | 已完整支持 |
| ReviewService.complete_review() | 已保留 outcome_ref，不需修改 |
| KnowledgeFeedbackService | H-3 路径不支持无 recommendation_id 情况，H-8 规则允许 |
| CandidateRule | 不自动创建 (规则禁止) |
| Policy | 不自动提升 (规则禁止) |
| broker/order/trade | 不触发 (规则禁止) |

---

## 4. 验证步骤

```bash
# 1. 单元测试
uv run pytest -q tests/unit -p no:cacheprovider

# 2. H-8 集成测试
uv run pytest tests/integration/test_h8_review_closure.py -q -v

# 3. 全部集成测试
uv run pytest -q tests/integration

# 4. PG 回归测试
PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios uv run pytest tests/ -q

# 5. 合约测试
PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios uv run pytest tests/contracts/ -q

# 6. Ruff F821 检查
uv run ruff check . --select F821
```

---

## 5. H-8 规则逐项验证矩阵

| # | 规则 | 验证方式 |
|---|------|---------|
| 1 | Review can reference outcome_ref_type="finance_manual_outcome" | Test 1: API 创建 review 含 outcome_ref |
| 2 | Review can reference outcome_ref_id=<manual_outcome_id> | Test 1: API 创建并持久化 |
| 3 | complete_review preserves outcome_ref_type/outcome_ref_id | Test 3: 完成后查询 DB 验证 |
| 4 | completed review derives Lesson when lessons are provided | Test 4: 完成后验证 lesson 行 |
| 5 | completed review derives KnowledgeFeedback when H-3 path supports it | Test 5: 有 recommendation_id 时验证 |
| 6 | Knowledge evidence can include outcome reference | Test 7: 验证 evidence 含 outcome ref |
| 7 | Review completion does not create CandidateRule automatically | Test 8: 计数验证 |
| 8 | Review completion does not promote Policy automatically | Test 9: 审计事件验证 |
| 9 | Review completion does not trigger broker/order/trade | Test 10: DB 验证 |
| 10 | Review cannot reference missing outcome | Test 2: 422 错误 |
| 11 | Review cannot reference outcome of unsupported type without explicit rejection | 可选 |

---

## 6. 风险和注意

1. **无 recommendation_id 的 review**: 当 review 仅引用 manual outcome 且无 recommendation_id 时，`_build_knowledge_feedback()` 返回 None。H-8 规则允许此行为。
2. **合约测试**: 修改 API schema 后必须更新 OpenAPI snapshot。
3. **旧路由同步**: `apps/api/app/routers/reviews.py` 与 `apps/api/app/api/v1/reviews.py` 需保持 schema 一致（或废弃旧路由）。
4. **submit_review vs create_review**: submit_review 路径复杂（execution adapter），H-8 只扩展 create_review + complete_review 路径。
5. **Lesson source_refs**: 在 Lesson 中添加 outcome 引用可能影响现有测试的验证逻辑。
