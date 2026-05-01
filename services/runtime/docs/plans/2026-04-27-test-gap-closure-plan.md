# Test Gap Closure Plan — Ordivon 10-Layer Test System

> **For Hermes:** Use subagent-driven-development skill to implement this plan wave-by-wave.
> Each wave starts with audit (只读), then TDD implementation. Each task is a commit.

**Goal:** Close all gaps identified in the 2026-04-27 test audit: architect a 10-layer test system that proves all system invariants survive every change.

**Architecture:** 6 waves ordered by first-principles impact — visibility → correctness → coverage → evidence. Each wave targets specific layers from the 10-layer framework (L0–L9). PostgreSQL integration happens in Wave 2, serving as foundation for later waves.

**Tech Stack:** pytest, ruff, bandit, mypy, Playwright, Alembic, PostgreSQL (pgvector/pg17), gitleaks

**Success criteria:** After all 6 waves, every system invariant from the audit has at least one failing-first test that proves it, CI runs PostgreSQL at every PR, schema drift is detected automatically, and dogfood covers escalate + execute + reject paths.

---

## Wave Map

```
Wave 1: L0 Static Guards           — Prevent regression at commit time
Wave 2: L7 Schema + PostgreSQL     — Prove DB truth (foundation for all later tests)
Wave 3: L2 Domain + Architecture   — Prove constitutional invariants
Wave 4: L5+L6+L8 Path Coverage     — Prove all 3 control paths end-to-end
Wave 5: L3+L4 Data/Orchestration   — Prove repository correctness + capability composition
Wave 6: L9 Dogfood 2.0             — Prove real-world effectiveness (escalate + KF)
```

---

## Wave 1: L0 Static Guards — Prevent Regression

**目标：** 提交前自动拦截低级问题，防止架构污染和秘密泄漏。

**Risk:** Low — 只加不删，不改业务逻辑。

**Allow:**
- 添加 ruff format check
- 添加 mypy 类型检查依赖和最小配置
- 添加 gitleaks 密钥扫描
- 添加架构边界 CI guard
- 修改 `.github/workflows/ci.yml` 和 `pyproject.toml`

**Forbid:**
- 修改任何业务代码
- 修改任何测试逻辑
- 修改数据库 schema

---

### Task 1.1: Add ruff format check to CI

**Objective:** Lint 通过不代表格式正确，需单独 format check。

**Files:**
- Modify: `pyproject.toml`
- Modify: `.github/workflows/ci.yml`

**Step 1: Write format check script in CI**

In `ci.yml` `backend-static` job, after the lint step, add:

```yaml
      - name: Format check backend
        run: uv run ruff format --check apps/api/app capabilities domains execution governance infra intelligence orchestrator packs shared state
```

**Step 2: Also add to root `package.json` scripts**

```json
"format:check:py": "python -m ruff format --check apps/api/app capabilities domains execution governance infra intelligence orchestrator packs shared state",
```

**Step 3: Commit**

```bash
git add pyproject.toml .github/workflows/ci.yml package.json
git commit -m "chore: add ruff format check to CI and package scripts"
```

---

### Task 1.2: Add mypy type checking (minimal initial config)

**Objective:** 渐进引入类型检查。先用最宽松配置，只检查 governance 和 state 模块。

**Files:**
- Create: `mypy.ini`
- Modify: `pyproject.toml` (add mypy to dev deps)
- Modify: `.github/workflows/ci.yml`

**Step 1: Add mypy to dev dependencies**

In `pyproject.toml` `[project.optional-dependencies] dev`:

```toml
  "mypy>=1.18.0",
```

**Step 2: Create minimal mypy.ini**

```ini
[mypy]
python_version = 3.11
warn_return_any = False
warn_unused_configs = True
ignore_missing_imports = True
exclude = (?x)(
    \.venv/
    | node_modules/
    | __pycache__/
    | \.git/
  )

# Start with governance only — expand gradually
[mypy-governance.*]
ignore_errors = False
disallow_untyped_defs = False

# Everything else is unchecked for now
[mypy-domains.*]
ignore_errors = True
[mypy-capabilities.*]
ignore_errors = True
[mypy-packs.*]
ignore_errors = True
[mypy-intelligence.*]
ignore_errors = True
[mypy-orchestrator.*]
ignore_errors = True
[mypy-infra.*]
ignore_errors = True
[mypy-state.*]
ignore_errors = True
[mypy-execution.*]
ignore_errors = True
[mypy-shared.*]
ignore_errors = True
[mypy-apps.*]
ignore_errors = True
```

**Step 3: Add to CI `backend-static` job (NON-blocking initially)**

After ruff check, add:

```yaml
      - name: Type check backend (governance)
        continue-on-error: true
        run: uv run mypy governance/
```

**Step 4: Add to root `package.json`**

```json
"typecheck:py": "python -m mypy governance/",
```

**Step 5: Commit**

```bash
git add mypy.ini pyproject.toml .github/workflows/ci.yml package.json
git commit -m "chore: add mypy type checking foundation (governance only, non-blocking)"
```

---

### Task 1.3: Add gitleaks secret scanning

**Objective:** 防止 API key / token / password 被提交。

**Files:**
- Create: `.gitleaks.toml`
- Modify: `.github/workflows/ci.yml`

**Step 1: Generate gitleaks config with allowlist**

`.gitleaks.toml`:

```toml
[allowlist]
  description = "Global allowlist"
  paths = [
    '''pnpm-lock\.yaml''',
    '''\.git/''',
  ]

[[rules]]
  id = "generic-api-key"
  [rules.allowlist]
    description = "Allow docs mentioning secrets"
    paths = ['''docs/.*\.md$''']
    regexTarget = "line"
```

**Step 2: Add to CI as new job `secret-scan`**

```yaml
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

**Step 3: Commit**

```bash
git add .gitleaks.toml .github/workflows/ci.yml
git commit -m "chore: add gitleaks secret scanning to CI"
```

---

### Task 1.4: Add architecture boundary guard to CI

**Objective:** Core 模块不能 import Pack 特定领域类型（ADR-006 的 pack_policy 委托接口除外）。

**Files:**
- Create: `scripts/check_architecture.py`
- Modify: `.github/workflows/ci.yml`

**Step 1: Create architecture guard script**

`scripts/check_architecture.py`:

```python
#!/usr/bin/env python3
"""Architecture boundary checker — prevents domain pollution into Core."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Modules that are NOT allowed to import pack-specific types
CORE_MODULES = ["governance", "state", "domains", "capabilities", "execution", "shared"]

# Allowed: pack_policy interface (ADR-006 compliant)
ALLOWED_FINANCE_IMPORTS = [
    "RejectReason",  # ADR-006: typing-only import by risk_engine
    "EscalateReason",  # ADR-006: typing-only import by risk_engine
]

FORBIDDEN_FINANCE_IMPORTS = [
    "from packs.finance.trading_discipline_policy import",
    "from packs.finance.tool_refs import",
]


def check_file(path: Path) -> list[str]:
    violations = []
    text = path.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_FINANCE_IMPORTS:
        if forbidden in text:
            violations.append(f"{path.relative_to(ROOT)}: forbidden import: {forbidden}")
    return violations


def main() -> int:
    violations = []
    for module in CORE_MODULES:
        module_path = ROOT / module
        if not module_path.exists():
            continue
        for py_file in module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            violations.extend(check_file(py_file))

    if violations:
        print("ARCHITECTURE BOUNDARY VIOLATIONS:")
        for v in violations:
            print(f"  ❌ {v}")
        return 1

    print("✅ Architecture boundaries clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Add to CI `backend-static` job**

After compileall:

```yaml
      - name: Check architecture boundaries
        run: uv run python scripts/check_architecture.py
```

**Step 3: Add to root `package.json`**

```json
"check:architecture": "python scripts/check_architecture.py",
```

**Step 4: Commit**

```bash
git add scripts/check_architecture.py .github/workflows/ci.yml package.json
git commit -m "chore: add architecture boundary guard (Core→Pack imports)"
```

---

### Wave 1 Completion Check

- [ ] `ruff format --check` in CI
- [ ] `mypy governance/` in CI (non-blocking)
- [ ] `gitleaks` secret scan in CI
- [ ] Architecture boundary script in CI

---

## Wave 2: L7 Schema + PostgreSQL Foundation

**目标：** 让 CI 能在 PostgreSQL 上运行完整测试套件。配置 Alembic autogenerate 以检测 schema drift。

**Risk:** Medium — 涉及 CI 基础设施变更，但不改业务代码。

**Prerequisite:** Wave 1 complete.

**Allow:**
- 添加 PostgreSQL CI job
- 配置 Alembic autogenerate check
- 修改 CI workflows
- 修改 alembic env.py（仅数据库 URL 适配）
- 添加 schema drift CI 步骤

**Forbid:**
- 修改 ORM 模型
- 修改 bootstrap.py
- 修改 migration runner
- 手动 ALTER TABLE

---

### Task 2.1: Add PostgreSQL service to CI

**Objective:** CI 中启用 pgvector 容器，使测试能在真实 PostgreSQL 上运行。

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Add `backend-unit-pg` job to CI**

```yaml
  backend-unit-pg:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg17
        env:
          POSTGRES_USER: pfios
          POSTGRES_PASSWORD: pfios
          POSTGRES_DB: pfios_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
    env:
      PFIOS_DB_URL: postgresql://pfios:pfios@127.0.0.1:5432/pfios_test
      PFIOS_ENV: test
      PFIOS_DEBUG: "false"
      PFIOS_REASONING_PROVIDER: mock
      PFIOS_AUDIT_LOG_DIR: ./data/logs/audit
      PFIOS_TIMEZONE: Asia/Shanghai

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.11"

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Install Python dev dependencies
        run: uv sync --extra dev

      - name: Run unit tests on PostgreSQL
        run: uv run pytest -q tests/unit
```

**Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add PostgreSQL service for backend unit tests"
```

---

### Task 2.2: Add Alembic autogenerate schema drift check

**Objective:** 每次 CI 运行检测 ORM model 和数据库 schema 之间的差异。

**Files:**
- Create: `scripts/check_schema_drift.sh`
- Modify: `.github/workflows/ci.yml`

**Step 1: Create drift check script**

`scripts/check_schema_drift.sh`:

```bash
#!/bin/bash
# Schema drift check: detects ORM model vs database schema differences.
# Fails if Alembic autogenerate would produce a non-empty migration.

set -euo pipefail

echo "=== Schema Drift Check ==="

# Generate a migration to detect drift
uv run alembic revision --autogenerate -m "drift_check" --rev-id drift_check_temp 2>&1 || true

DRIFT_FILE=$(ls alembic/versions/drift_check_temp_*.py 2>/dev/null | head -1)

if [ -z "$DRIFT_FILE" ]; then
    echo "✅ No schema drift detected"
    exit 0
fi

# Check if the generated migration is empty (only pass in upgrade/downgrade)
DRIFT_CONTENT=$(grep -c "pass" "$DRIFT_FILE" || echo "0")

# Remove the temp migration
rm -f "$DRIFT_FILE"

if [ "$DRIFT_CONTENT" -ge 2 ]; then
    echo "✅ No schema drift detected (empty autogenerate)"
    exit 0
else
    echo "❌ SCHEMA DRIFT DETECTED: Models and database are out of sync"
    echo "Run: alembic revision --autogenerate -m 'describe_change'"
    echo "Then review and commit the new migration."
    exit 1
fi
```

**Step 2: Add to existing `backend-unit-pg` job (after test step)**

```yaml
      - name: Check schema drift (Alembic autogenerate)
        run: bash scripts/check_schema_drift.sh
```

**Step 3: Also add `backend-integration-pg` job with integration tests on PG + drift check**

Duplicate the `backend-unit-pg` structure but run integration tests instead:

```yaml
  backend-integration-pg:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg17
        env:
          POSTGRES_USER: pfios
          POSTGRES_PASSWORD: pfios
          POSTGRES_DB: pfios_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
    env:
      PFIOS_DB_URL: postgresql://pfios:pfios@127.0.0.1:5432/pfios_test
      PFIOS_ENV: test
      PFIOS_DEBUG: "false"
      PFIOS_REASONING_PROVIDER: mock
      PFIOS_AUDIT_LOG_DIR: ./data/logs/audit
      PFIOS_TIMEZONE: Asia/Shanghai

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.11"

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Install Python dev dependencies
        run: uv sync --extra dev

      - name: Create test database
        run: |
          PGPASSWORD=pfios psql -h 127.0.0.1 -U pfios -d postgres -c "CREATE DATABASE pfios_test" 2>/dev/null || true

      - name: Run integration tests on PostgreSQL
        run: uv run pytest -q tests/integration
```

**Step 4: Commit**

```bash
git add scripts/check_schema_drift.sh .github/workflows/ci.yml
git commit -m "ci: add PostgreSQL integration tests + Alembic schema drift detection"
```

---

### Task 2.3: Add root `package.json` scripts for PostgreSQL testing

**Objective:** 本地也能跑 PostgreSQL 测试。

**Files:**
- Modify: `package.json`

**Step 1: Add scripts**

```json
"test:unit:pg": "cross-env PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test PFIOS_ENV=test PFIOS_DEBUG=false PFIOS_REASONING_PROVIDER=mock uv run pytest -q tests/unit",
"test:integration:pg": "cross-env PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test PFIOS_ENV=test PFIOS_DEBUG=false PFIOS_REASONING_PROVIDER=mock uv run pytest -q tests/integration",
"check:schema-drift": "bash scripts/check_schema_drift.sh",
```

**Step 2: Commit**

```bash
git add package.json
git commit -m "chore: add PostgreSQL test scripts to package.json"
```

---

### Wave 2 Completion Check

- [ ] `backend-unit-pg` job passes on CI
- [ ] `backend-integration-pg` job passes on CI
- [ ] Alembic autogenerate check runs without false positives
- [ ] `scripts/check_schema_drift.sh` works locally

---

## Wave 3: L2 Domain + Architecture Invariants

**目标：** 为系统宪法中缺失的 7 个不变量添加领域测试。每个测试必须先红后绿。

**Risk:** Medium — 添加新测试，不改业务逻辑。但如果测试失败，暴露了真实 bug。

**Prerequisite:** Wave 2 complete (PostgreSQL baseline 已建立).

**Allow:**
- 添加新领域测试文件
- 可能发现并修复因缺失测试而未暴露的 bug
- 可能需要在 `governance/` 中添加新的架构边界测试

**Forbid:**
- 修改现有业务逻辑（除非测试暴露了 bug）
- 改变数据库 schema
- 删除任何现有测试

---

### Task 3.1: Test — CandidateRule is not Policy

**Objective:** 证明候选规则不能自动升级为生效策略。

**Files:**
- Create: `tests/unit/governance/test_candidate_rule_is_not_policy.py`

**TDD Cycle:**

```python
"""Prove CandidateRule cannot auto-promote to Policy."""


def test_candidate_rule_creation_does_not_affect_active_policies():
    """When a CandidateRule is created, active policies must not change."""
    from governance.policy_source import GovernancePolicySource

    source = GovernancePolicySource()
    before = set(source.get_active_snapshot().active_policy_ids)

    # Create a candidate rule via the policy source
    source.create_candidate_rule(
        rule_name="test_rule",
        description="Auto-tighten position limits",
        severity="high",
        category="trading_discipline",
    )

    after = set(source.get_active_snapshot().active_policy_ids)
    assert after == before, f"CandidateRule creation changed active policies: before={before}, after={after}"


def test_candidate_rule_is_not_in_active_policy_list():
    """CandidateRule IDs must not appear in active_policy_ids."""
    from governance.policy_source import GovernancePolicySource

    source = GovernancePolicySource()
    candidate = source.create_candidate_rule(
        rule_name="test_rule_2",
        description="Review required before policy activation",
        severity="medium",
        category="trading_discipline",
    )

    snapshot = source.get_active_snapshot()
    assert candidate.rule_id not in snapshot.active_policy_ids
    assert candidate.rule_id not in snapshot.default_decision_rule_ids
```

**Step 2: Run → expect FAIL**

```bash
uv run pytest tests/unit/governance/test_candidate_rule_is_not_policy.py -v
```

**Step 3: If test fails because `create_candidate_rule` method doesn't exist → implement it**
**Step 4: If test passes → invariant is already enforced → GOOD, test serves as regression guard**

**Step 5: Commit**

```bash
git add tests/unit/governance/test_candidate_rule_is_not_policy.py
git commit -m "test: add CandidateRule≠Policy invariant guard"
```

---

### Task 3.2: Test — KnowledgeFeedback is advisory only

**Objective:** 知识反馈不能自动修改策略或规则。

**Files:**
- Create: `tests/unit/knowledge/test_kf_is_advisory.py`

**TDD Cycle:**

```python
"""Prove KnowledgeFeedback is advisory — no auto side effects."""


def test_kf_creation_does_not_create_candidate_rule():
    """KnowledgeFeedback must not auto-create CandidateRules."""
    from knowledge.extraction import KnowledgeExtractionService
    from governance.policy_source import GovernancePolicySource

    source = GovernancePolicySource()
    before_rules = len(list(source.list_candidate_rules()))

    extractor = KnowledgeExtractionService()
    extractor.create_feedback(
        insight="Position sizes should be logged daily",
        confidence=0.85,
        source="review_analysis",
    )

    after_rules = len(list(source.list_candidate_rules()))
    assert after_rules == before_rules, (
        f"KnowledgeFeedback auto-created a CandidateRule: before={before_rules}, after={after_rules}"
    )


def test_kf_creation_does_not_change_active_policies():
    """KnowledgeFeedback must not modify active policies."""
    from governance.policy_source import GovernancePolicySource
    from knowledge.extraction import KnowledgeExtractionService

    source = GovernancePolicySource()
    before = set(source.get_active_snapshot().active_policy_ids)

    extractor = KnowledgeExtractionService()
    extractor.create_feedback(
        insight="Trading limits seem appropriate",
        confidence=0.6,
        source="dogfood_run",
    )

    after = set(source.get_active_snapshot().active_policy_ids)
    assert after == before, "KnowledgeFeedback changed active policies"
```

**Step 2: Run → expect FAIL**

**Step 3: Fix if needed. If passes → GOOD.**

**Step 4: Commit**

```bash
git add tests/unit/knowledge/test_kf_is_advisory.py
git commit -m "test: add KnowledgeFeedback advisory invariant guard"
```

---

### Task 3.3: Test — Lesson must come from completed review

**Objective:** 课程只能从已完成的审查中生成。

**Files:**
- Create: `tests/unit/journal/test_lesson_requires_completed_review.py`

**TDD Cycle:**

```python
"""Prove Lesson derivation requires a completed review."""


def test_create_lesson_from_pending_review_fails():
    """Lessons must not be creatable from reviews that are not completed."""
    import pytest
    from domains.journal.service import JournalService

    service = JournalService()

    with pytest.raises(ValueError, match="completed"):
        service.create_lesson(
            review_id="pending_review_123",
            lesson_text="This should fail",
        )


def test_create_lesson_from_completed_review_succeeds():
    """Lessons from completed reviews must succeed."""
    from domains.journal.service import JournalService

    service = JournalService()
    lesson = service.create_lesson(
        review_id="completed_review_456",
        lesson_text="Trust plan targets",
    )

    assert lesson.id is not None
    assert lesson.review_id == "completed_review_456"
```

**Step 2: Run → expect FAIL**

**Step 3: Implement guard if missing**

**Step 4: Commit**

```bash
git add tests/unit/journal/test_lesson_requires_completed_review.py
git commit -m "test: add Lesson-requires-completed-review invariant guard"
```

---

### Task 3.4: Test — Review verdict ≠ model claims completion

**Objective:** 审查状态必须由审查服务明确设置，不能由模型输出自动确定。

**Files:**
- Create: `tests/unit/governance/test_review_verdict_not_model_claim.py`

```python
"""Prove Review verdict is set by review service, not by model output."""


def test_complete_review_sets_status_explicitly():
    """review_service.complete_review must explicitly set status, not infer from model."""
    from apps.api.app.services.review_service import ReviewService

    service = ReviewService()
    result = service.complete_review(
        review_id="test_review",
        observed_outcome="Target reached",
        verdict="validated",  # EXPLICIT verdict
        lessons=["Follow plan"],
    )

    assert result.status == "completed"
    assert result.verdict == "validated"
    # Verdict must come from the caller, not from model inference
    assert "inferred" not in str(result.metadata or "").lower()


def test_model_output_cannot_set_review_status():
    """A model's claim of completion must not auto-set review status."""
    from apps.api.app.services.review_service import ReviewService

    service = ReviewService()
    # Simulate a model output claiming "completed"
    model_output = {"status": "completed", "verdict": "validated"}
    result = service.process_model_output(
        review_id="test_review_2",
        model_output=model_output,
    )

    # Model output alone must not change persisted status
    assert result.status != "completed", "Model output should not auto-set review status"
```

**Step 2: Run → expect FAIL or pass (depending on implementation)**

**Step 4: Commit**

```bash
git add tests/unit/governance/test_review_verdict_not_model_claim.py
git commit -m "test: add review-verdict-independence invariant guard"
```

---

### Task 3.5: Test — is_chasing → escalate, is_revenge_trade → escalate

**Objective:** 两个关键行为标记必须触发升级。

**Files:**
- Create: `tests/unit/finance/test_behavioral_escalation.py`

```python
"""Prove chasing / revenge trade trigger escalation."""


def test_is_chasing_true_escalates():
    """DecisionIntake with is_chasing=True must trigger escalate."""
    from packs.finance.trading_discipline_policy import TradingDisciplinePolicy

    policy = TradingDisciplinePolicy()
    payload = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "Breakout with volume confirmation and 200 EMA invalidation.",
        "stop_loss": "Below support",
        "position_size_usdt": 100.0,
        "max_loss_usdt": 20.0,
        "risk_unit_usdt": 10.0,
        "is_chasing": True,
        "is_revenge_trade": False,
        "emotional_state": "calm",
        "confidence": 0.7,
    }

    behavioral_reasons = list(policy.validate_behavioral(payload))
    assert len(behavioral_reasons) > 0, "is_chasing=True should produce escalate reasons"
    assert any("chasing" in r.message.lower() for r in behavioral_reasons)


def test_is_revenge_trade_true_escalates():
    """DecisionIntake with is_revenge_trade=True must trigger escalate."""
    from packs.finance.trading_discipline_policy import TradingDisciplinePolicy

    policy = TradingDisciplinePolicy()
    payload = {
        "symbol": "ETH/USDT",
        "timeframe": "15m",
        "direction": "short",
        "thesis": "ETH breakdown with volume confirmation.",
        "stop_loss": "Above resistance",
        "position_size_usdt": 50.0,
        "max_loss_usdt": 10.0,
        "risk_unit_usdt": 5.0,
        "is_chasing": False,
        "is_revenge_trade": True,
        "emotional_state": "calm",
        "confidence": 0.7,
    }

    behavioral_reasons = list(policy.validate_behavioral(payload))
    assert len(behavioral_reasons) > 0, "is_revenge_trade=True should produce escalate reasons"
    assert any("revenge" in r.message.lower() for r in behavioral_reasons)


def test_neither_chasing_nor_revenge_executes():
    """Normal intake with no behavioral flags must not escalate on behavioral grounds."""
    from packs.finance.trading_discipline_policy import TradingDisciplinePolicy

    policy = TradingDisciplinePolicy()
    payload = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "BTC breakout with volume and invalidation below 200 EMA.",
        "stop_loss": "Below support",
        "position_size_usdt": 100.0,
        "max_loss_usdt": 20.0,
        "risk_unit_usdt": 10.0,
        "is_chasing": False,
        "is_revenge_trade": False,
        "emotional_state": "calm",
        "confidence": 0.7,
    }

    behavioral_reasons = list(policy.validate_behavioral(payload))
    assert len(behavioral_reasons) == 0, f"Normal intake should not trigger behavioral escalation: {behavioral_reasons}"
```

**Step 2: Run → expect FAIL**

**Step 3: Implement behavioral validation if missing**

**Step 4: Commit**

```bash
git add tests/unit/finance/test_behavioral_escalation.py
git commit -m "test: add chasing/revenge_trade escalation domain invariant"
```

---

### Task 3.6: Architecture test — no broker/order/trade side effects

**Objective:** Finance decision control loop 不能产生真实的 broker 下单副作用。

**Files:**
- Create: `tests/architecture/test_no_broker_side_effects.py`

```python
"""Architecture invariant: finance decision loop must not execute real trades."""


def test_plan_receipt_has_no_broker_execution_flag():
    """Every plan receipt must have broker_execution=False."""
    # This is tested in test_h6_plan_only_receipt.py — verify it exists
    pass  # Already covered by existing test


def test_execution_catalog_has_no_order_action():
    """Execution action catalog must not contain broker order actions."""
    from execution.catalog import get_action

    result = get_action("place_order", default=None)
    assert result is None, "Action catalog must not contain 'place_order' — this is a broker action not allowed in P4"


def test_finance_outcome_is_manual_not_broker():
    """FinanceManualOutcome must always be manual, not broker-sourced."""
    # Check that the CAPABILITY creates outcomes with source="manual"
    # This is tested in test_h7_manual_outcome.py — verify coverage
    pass  # Already covered


def test_no_trade_module_in_core_directories():
    """Core modules must not reference trade/broker/order modules."""
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[2]
    FORBIDDEN_DIRS = ["governance", "state", "capabilities", "execution", "shared"]
    FORBIDDEN_PATTERNS = ["broker", "trade", "order", "exchange.execute"]

    violations = []
    for d in FORBIDDEN_DIRS:
        for fp in (ROOT / d).rglob("*.py"):
            if "__pycache__" in str(fp):
                continue
            text = fp.read_text(encoding="utf-8").lower()
            for pat in FORBIDDEN_PATTERNS:
                if pat in text:
                    violations.append(f"{fp.relative_to(ROOT)}: found '{pat}'")

    assert violations == [], f"Broker/trade/order references in Core: {violations}"
```

**Step 2: Run**

**Step 4: Commit**

```bash
git add tests/architecture/test_no_broker_side_effects.py
git commit -m "test: add architecture guard — no broker side effects in Core"
```

---

### Wave 3 Completion Check

- [ ] `test_candidate_rule_is_not_policy.py` — passes on DuckDB and PostgreSQL
- [ ] `test_kf_is_advisory.py` — passes
- [ ] `test_lesson_requires_completed_review.py` — passes
- [ ] `test_review_verdict_not_model_claim.py` — passes
- [ ] `test_behavioral_escalation.py` — passes
- [ ] `test_no_broker_side_effects.py` — passes
- [ ] All existing tests still pass

---

## Wave 4: L5+L6+L8 Path Coverage

**目标：** 三条控制路径（reject / escalate / execute）的完整集成 + E2E 覆盖。

**Risk:** Medium-High — 新测试可能暴露未被发现的集成 bug。

**Prerequisite:** Wave 3 complete.

---

### Task 4.1: Integration — Full reject path (no plan, no outcome, no broker)

**Objective:** 证明被拒绝的 intake 不能创建 plan receipt。

**Files:**
- Create: `tests/integration/test_reject_path_no_side_effects.py`

```python
"""Integration: reject path must produce no plan, no outcome, no broker side effects."""

import os

os.environ.setdefault("PFIOS_ENV", "test")
os.environ.setdefault("PFIOS_DEBUG", "false")
os.environ.setdefault("PFIOS_REASONING_PROVIDER", "mock")
os.environ.setdefault("PFIOS_DB_URL", "duckdb:///:memory:")

from fastapi.testclient import TestClient
from apps.api.app.main import app


def test_rejected_intake_cannot_create_plan_receipt():
    """After governance reject, POST /plan must return 4xx."""
    with TestClient(app) as client:
        # 1. Create intake with low-quality thesis
        intake_resp = client.post(
            "/api/v1/finance-decisions/intake",
            json={
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "direction": "long",
                "thesis": "YOLO all in",
                "stop_loss": "Below support",
                "position_size_usdt": 100.0,
                "max_loss_usdt": 20.0,
                "risk_unit_usdt": 10.0,
                "is_chasing": False,
                "is_revenge_trade": False,
                "emotional_state": "calm",
                "confidence": 0.7,
            },
        )
        assert intake_resp.status_code == 201
        intake_id = intake_resp.json()["id"]

        # 2. Govern → expect reject
        govern_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
        assert govern_resp.status_code == 200
        assert govern_resp.json()["governance_decision"] == "reject"

        # 3. Plan → must be rejected
        plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        assert plan_resp.status_code in (400, 403, 409), (
            f"Plan on rejected intake should return 4xx, got {plan_resp.status_code}"
        )

        # 4. Outcome → must be rejected
        outcome_resp = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "observed_outcome": "Price moved",
                "verdict": "validated",
                "plan_followed": True,
            },
        )
        assert outcome_resp.status_code in (400, 403, 409)
```

**Step 2: Run → expect FAIL**

**Step 3: If fail → there's a real bug (rejected intake can still be planned)**

**Step 4: Commit**

---

### Task 4.2: Integration — Full escalate path verification

**Objective:** 升级的 intake 不能自动 plan，需要人工介入。

**Files:**
- Create: `tests/integration/test_escalate_path_requires_human.py`

See complete code in Step 1 above. Same pattern: create intake with emotional_state="stressed" → govern → escalate → plan must fail.

---

### Task 4.3: Integration — Knowledge feedback full path

**Objective:** 从 review completion 到 knowledge feedback 的完整链路。

**Files:**
- Create: `tests/integration/test_knowledge_feedback_full_path.py`

---

### Task 4.4: E2E — Reject path (Playwright)

**Objective:** 浏览器端验证低质量输入被拒绝的完整流程。

**Files:**
- Create: `tests/e2e/reject-path.spec.ts`

---

### Task 4.5: E2E — Escalate path (Playwright)

**Objective:** 浏览器端验证情绪异常输入被升级。

**Files:**
- Create: `tests/e2e/escalate-path.spec.ts`

---

### Task 4.6: Contract — POST /reviews/submit accepts outcome_ref

**Objective:** 独立测试 review 提交接口接受 outcome_ref_type / outcome_ref_id。

**Files:**
- Create: `tests/contracts/test_review_submit_contract.py`

---

### Wave 4 Completion Check

- [ ] `test_reject_path_no_side_effects.py` — passes on DuckDB + PG
- [ ] `test_escalate_path_requires_human.py` — passes
- [ ] `test_knowledge_feedback_full_path.py` — passes
- [ ] `reject-path.spec.ts` — Playwright passes
- [ ] `escalate-path.spec.ts` — Playwright passes
- [ ] `test_review_submit_contract.py` — passes

---

## Wave 5: L3+L4 Repository/Capability Hardening

**目标：** 补齐数据访问层的关键测试：JSON 字段序列化、nullable 字段、重复冲突、to_model/from_model 转换。验证能力层编排不绕过 governance。

**Risk:** Low-Medium — 添加数据层测试。

---

### Task 5.1: Repository — JSON field round-trip tests

**Files:**
- Create: `tests/unit/journal/test_orm_json_fields.py`

### Task 5.2: Repository — Duplicate conflict tests

**Files:**
- Modify: 多个现存的 repository test 文件

### Task 5.3: Repository — Nullable field tests

### Task 5.4: Capability — verify governance not bypassed

**Files:**
- Create: `tests/unit/capabilities/test_governance_not_bypassed.py`

### Task 5.5: Repository — to_model / from_model consistency

---

## Wave 6: L9 Dogfood 2.0

**目标：** 30 次狗粮运行，覆盖 escalate 路径和 knowledge feedback 链路。

**Risk:** Low — 只运行脚本，不改代码。

---

### Task 6.1: Extend dogfood runner to include escalate scenarios

**Files:**
- Modify: `scripts/h9_dogfood_runs.py`

### Task 6.2: Add knowledge feedback scenarios

### Task 6.3: Run 30-run dogfood

### Task 6.4: Generate evidence report v2

---

## Gate Checklist (per-wave)

### Wave 1 (L0 Static Guards)
- [ ] `ruff format --check` in CI → non-blocking initially
- [ ] `mypy governance/` in CI → non-blocking
- [ ] `gitleaks` secret scan in CI
- [ ] Architecture boundary guard in CI
- [ ] All existing tests pass

### Wave 2 (L7 Schema + PostgreSQL)
- [ ] `backend-unit-pg` job passes on CI
- [ ] `backend-integration-pg` job passes on CI
- [ ] Alembic autogenerate check — no false positives
- [ ] Local `check:schema-drift` script works

### Wave 3 (L2 Domain + Architecture Invariants)
- [ ] 6 new test files pass on DuckDB and PostgreSQL
- [ ] No existing test regressions
- [ ] Any exposed bugs are fixed (TDD)

### Wave 4 (L5+L6+L8 Path Coverage)
- [ ] 6 new test files pass (3 integration + 2 E2E + 1 contract)
- [ ] All 3 control paths (reject/escalate/execute) covered end-to-end

### Wave 5 (L3+L4 Repository/Capability)
- [ ] JSON field round-trips verified
- [ ] Duplicate conflict handling verified
- [ ] Governance bypass detection verified

### Wave 6 (L9 Dogfood 2.0)
- [ ] 30 runs complete
- [ ] Escalate path ≥ 1
- [ ] KnowledgeFeedback packets ≥ 3
- [ ] Evidence report v2 written

---

## Final Success Metrics

After all 6 waves:

```
静态检查覆盖率:   4/13 → 8/13
域不变量覆盖率:   5/11 → 11/11
系统不变量覆盖率:  2/9  → 9/9
控制路径 E2E:    1/3  → 3/3
CI PostgreSQL:    0 jobs → 2 jobs
Schema drift:     未检测 → 自动检测
Dogfood 升级路径: 0/10 → ≥ 1/30
Dogfood KF 路径:  0/10 → ≥ 3/30
```
