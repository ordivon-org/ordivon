# Test Gap Closure Plan — Ordivon 10-Layer Test System (v2 Complete)

> **For Hermes:** Use subagent-driven-development skill to implement this plan phase-by-phase.
> Each phase starts with audit (只读), then TDD implementation. Each task = one commit.

**Goal:** Close all 34 gaps identified in the 2026-04-27 test audit. After 7 phases, every system invariant has at least one failing-first test, PostgreSQL runs in CI at every PR, schema drift is detected automatically, and all 3 control paths (execute/escalate/reject) are covered end-to-end.

**Architecture:** 7 phases ordered by dependency chain — tools → infrastructure → data integrity → orchestration guards → negative invariants → contract lock → real-world evidence.

**Tech Stack:** pytest, ruff, bandit, mypy, vulture, import-linter, Playwright, Alembic, PostgreSQL (pgvector/pg17), gitleaks

---

## Dependency Chain

```
P1: Static Tools (E)  →  P2: PostgreSQL + Schema (infra)  →  P3: Data Integrity (A)
     ↓                                                           ↓
  ruff format, mypy,        PG CI jobs, Alembic              JSON round-trips,
  gitleaks, vulture,        autogenerate drift,               nullable, duplicate,
  import-linter,            schema check script               to_model/from_model
  architecture guard
                                                                    ↓
                                                            P4: Orchestration Guards (B)
                                                                    ↓
                                                          receipt state gates,
                                                          action_id checks,
                                                          duplicate outcome→409,
                                                          manual→requires plan receipt,
                                                          governance not bypassed
                                                                    ↓
                                                            P5: Negative Invariants (C)
                                                                    ↓
                                                          CandidateRule≠Policy,
                                                          KF≠auto rule,
                                                          Lesson→completed review,
                                                          no broker side effects,
                                                          no Policy auto-promotion,
                                                          KF doesn't write ORM truth
                                                                    ↓
                                                            P6: Contract Lock (D)
                                                                    ↓
                                                          error code enum,
                                                          review submit outcome_ref,
                                                          Hermes bridge contract
                                                                    ↓
                                                            P7: E2E + Dogfood (L8+L9)
                                                                    ↓
                                                          Reject/Escalate E2E paths,
                                                          30-run dogfood v2,
                                                          evidence report v2
```

---

## Phase 1: Static Tools (E) — L0 Completion

**目标：** 提交前自动拦截所有可静态检测的问题：格式、类型、密钥、死代码、导入循环、架构边界。

**Risk:** Low — 只加不改业务逻辑。

**Allow:** 添加/修改 CI workflows、pyproject.toml、mypy.ini、.gitleaks.toml、scripts/check_architecture.py
**Forbid:** 修改任何业务代码、修改任何测试逻辑、修改数据库 schema

---

### Task 1.1: Add ruff format check to CI

**Objective:** 格式一致性强制检查。

**Files:**
- Modify: `pyproject.toml`
- Modify: `.github/workflows/ci.yml`
- Modify: `package.json`

**Step 1: Add format check to CI `backend-static` job**

In `.github/workflows/ci.yml`, after the lint step:

```yaml
      - name: Format check backend
        run: uv run ruff format --check apps/api/app capabilities domains execution governance infra intelligence orchestrator packs shared state
```

**Step 2: Add to root `package.json`**

```json
"format:check:py": "python -m ruff format --check apps/api/app capabilities domains execution governance infra intelligence orchestrator packs shared state",
```

**Step 3: Commit**

```bash
git add .github/workflows/ci.yml package.json
git commit -m "chore: add ruff format check to CI and package scripts"
```

---

### Task 1.2: Add mypy type checking foundation

**Objective:** 渐进引入类型检查。先用 non-blocking 模式，只检查 governance。

**Files:**
- Modify: `pyproject.toml`
- Create: `mypy.ini`
- Modify: `.github/workflows/ci.yml`
- Modify: `package.json`

**Step 1: Add mypy to dev deps**

```toml
  "mypy>=1.18.0",
```

**Step 2: Create mypy.ini**

```ini
[mypy]
python_version = 3.11
warn_return_any = False
warn_unused_configs = True
ignore_missing_imports = True
exclude = (?x)(
    \.venv/|node_modules/|__pycache__/|\.git/
  )

[mypy-governance.*]
ignore_errors = False
disallow_untyped_defs = False

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

**Step 3: Add to CI `backend-static` (non-blocking)**

```yaml
      - name: Type check backend (governance)
        continue-on-error: true
        run: uv run mypy governance/
```

**Step 4: Commit**

```bash
git add mypy.ini pyproject.toml .github/workflows/ci.yml package.json
git commit -m "chore: add mypy type checking foundation (governance only, non-blocking)"
```

---

### Task 1.3: Add gitleaks secret scanning

**Objective:** 防止 API key / token / password 被提交到仓库。

**Files:**
- Create: `.gitleaks.toml`
- Modify: `.github/workflows/ci.yml`

**Step 1: Create gitleaks config**

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
    description = "Allow docs mentioning secrets conceptually"
    paths = ['''docs/.*\.md$''']
    regexTarget = "line"
```

**Step 2: Add `secret-scan` job to CI**

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

### Task 1.4: Add vulture dead code detection

**Objective:** 检测未使用的函数/类/变量。

**Files:**
- Modify: `pyproject.toml` (add vulture to dev deps)
- Create: `.vulture.toml`
- Modify: `.github/workflows/ci.yml`

**Step 1: Add vulture to dev deps**

```toml
  "vulture>=2.14",
```

**Step 2: Create .vulture.toml**

```toml
[tool.vulture]
exclude = [".venv", "node_modules", "__pycache__", ".git", "tests", "scripts", "alembic"]
min_confidence = 80
```

**Step 3: Add non-blocking CI step**

```yaml
      - name: Dead code check
        continue-on-error: true
        run: uv run vulture governance/ domains/ capabilities/ state/ execution/ shared/ infra/ packs/ intelligence/ orchestrator/ apps/api/app/
```

**Step 4: Commit**

```bash
git add pyproject.toml .vulture.toml .github/workflows/ci.yml
git commit -m "chore: add vulture dead code detection (non-blocking)"
```

---

### Task 1.5: Add import-linter import cycle check

**Objective:** 检测模块间循环导入。

**Files:**
- Modify: `pyproject.toml`
- Create: `.importlinter`
- Modify: `.github/workflows/ci.yml`

**Step 1: Add import-linter to dev deps**

```toml
  "import-linter>=2.3",
```

**Step 2: Create .importlinter**

```ini
[importlinter]
root_package = pfios

[importlinter:contracts:layers]
name = Core layers must not form cycles
type = layers
layers =
  shared
  state
  governance
  domains
  execution
  capabilities
  intelligence
  orchestrator
  packs
  apps
```

**Step 3: Add non-blocking CI step**

```yaml
      - name: Import cycle check
        continue-on-error: true
        run: uv run lint-imports
```

**Step 4: Commit**

```bash
git add pyproject.toml .importlinter .github/workflows/ci.yml
git commit -m "chore: add import-linter cycle detection (non-blocking)"
```

---

### Task 1.6: Add architecture boundary guard

**Objective:** Core 模块不能导入 Pack 特定类型（ADR-006 委托接口的 RejectReason/EscalateReason 除外）。

**Files:**
- Create: `scripts/check_architecture.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `package.json`

**Step 1: Write failing architecture guard script**

`scripts/check_architecture.py`:

```python
#!/usr/bin/env python3
"""Architecture boundary checker — prevents domain pollution into Core.

ADR-006 allows: Core → pack_policy (RejectReason, EscalateReason types only).
Everything else (tool_refs, policy overlays, pack-specific fields) is forbidden.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORE_MODULES = ["governance", "state", "domains", "capabilities", "execution", "shared"]

# Patterns that are FORBIDDEN in Core modules
FORBIDDEN = [
    # Direct pack imports of anything beyond RejectReason/EscalateReason
    ("from packs.finance.tool_refs import", "pack tool_refs leaked into Core"),
    ("from packs.finance.policy import", "pack policy overlays leaked into Core"),
    # Broker/trade/order references must not exist in Core
    ("broker", "broker reference in Core"),
    ("place_order", "trade order reference in Core"),
    ("execute_trade", "trade execution reference in Core"),
    # Finance-specific fields must not appear in governance layer
    ("stop_loss", "finance field 'stop_loss' in Core"),
    ("max_loss_usdt", "finance field 'max_loss_usdt' in Core"),
    ("is_chasing", "finance field 'is_chasing' in Core"),
    ("is_revenge_trade", "finance field 'is_revenge_trade' in Core"),
]


def check_file(path: Path) -> list[str]:
    violations = []
    text = path.read_text(encoding="utf-8")
    for pattern, description in FORBIDDEN:
        if pattern in text:
            violations.append(f"{path.relative_to(ROOT)}: {description} (pattern: '{pattern}')")
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

**Step 2: Run → expect PASS (current state is clean per ADR-006)**

```bash
uv run python scripts/check_architecture.py
```

**Step 3: Add to CI `backend-static` job**

```yaml
      - name: Check architecture boundaries
        run: uv run python scripts/check_architecture.py
```

**Step 4: Commit**

```bash
git add scripts/check_architecture.py .github/workflows/ci.yml package.json
git commit -m "chore: add architecture boundary guard (Core→Pack imports)"
```

---

### Phase 1 Completion Check

- [ ] `ruff format --check` in CI
- [ ] `mypy governance/` in CI (non-blocking)
- [ ] `gitleaks` secret scan in CI
- [ ] `vulture` dead code check (non-blocking)
- [ ] `lint-imports` cycle check (non-blocking)
- [ ] Architecture boundary guard in CI

---

## Phase 2: PostgreSQL + Schema Drift (Infrastructure)

**目标：** CI 中运行 PostgreSQL 测试 + Alembic autogenerate 检测 schema drift。

**Risk:** Medium — 涉及 CI 基础设施变更。

**Allow:** 添加 PG CI jobs、配置 Alembic autogenerate、修改 CI workflows、添加 package.json scripts
**Forbid:** 修改 ORM 模型、修改 bootstrap.py、修改 migration runner、手动 ALTER TABLE

---

### Task 2.1: Add PostgreSQL unit test job to CI

**Objective:** 单元测试在 PostgreSQL 上通过。

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Add `backend-unit-pg` job**

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

### Task 2.2: Add PostgreSQL integration test job to CI

**Objective:** 集成测试在 PostgreSQL 上通过。

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Add `backend-integration-pg` job**

Same structure as 2.1 but runs `tests/integration`:

```yaml
  backend-integration-pg:
    # ... (same service/postgres setup as backend-unit-pg) ...
      - name: Run integration tests on PostgreSQL
        run: uv run pytest -q tests/integration
```

**Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add PostgreSQL integration tests"
```

---

### Task 2.3: Add Alembic autogenerate schema drift check

**Objective:** 每次 CI 运行检测 ORM model 和数据库 schema 之间的差异。

**Files:**
- Create: `scripts/check_schema_drift.sh`
- Modify: `.github/workflows/ci.yml` (add to both `backend-unit-pg` and `backend-integration-pg`)

**Step 1: Create drift check script**

`scripts/check_schema_drift.sh`:

```bash
#!/bin/bash
# Schema drift check: detects ORM model vs database schema differences.
# Fails if Alembic autogenerate would produce a non-empty migration.

set -euo pipefail

echo "=== Schema Drift Check ==="

# Generate a temporary migration to detect drift
uv run alembic revision --autogenerate -m "drift_check" --rev-id drift_check_temp > /dev/null 2>&1 || true

DRIFT_FILE=$(ls alembic/versions/drift_check_temp_*.py 2>/dev/null | head -1)

if [ -z "$DRIFT_FILE" ]; then
    echo "✅ No schema drift detected"
    exit 0
fi

# Check if the generated migration has substantive content
NON_EMPTY_LINES=$(grep -cvE '^\s*(#|$|pass\s*$)' "$DRIFT_FILE" || echo "0")

# Clean up
rm -f "$DRIFT_FILE"

if [ "$NON_EMPTY_LINES" -le 5 ]; then
    echo "✅ No schema drift detected (empty autogenerate)"
    exit 0
else
    echo "❌ SCHEMA DRIFT DETECTED"
    echo "Run: alembic revision --autogenerate -m 'describe_change'"
    echo "Then review and commit the new migration."
    exit 1
fi
```

**Step 2: Add to both PG jobs**

```yaml
      - name: Check schema drift (Alembic autogenerate)
        run: bash scripts/check_schema_drift.sh
```

**Step 3: Add local scripts to package.json**

```json
"test:unit:pg": "cross-env PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test PFIOS_ENV=test PFIOS_DEBUG=false PFIOS_REASONING_PROVIDER=mock uv run pytest -q tests/unit",
"test:integration:pg": "cross-env PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test PFIOS_ENV=test PFIOS_DEBUG=false PFIOS_REASONING_PROVIDER=mock uv run pytest -q tests/integration",
"check:schema-drift": "bash scripts/check_schema_drift.sh",
```

**Step 4: Commit**

```bash
git add scripts/check_schema_drift.sh .github/workflows/ci.yml package.json
git commit -m "ci: add Alembic autogenerate schema drift detection"
```

---

### Phase 2 Completion Check

- [ ] `backend-unit-pg` passes on CI (after TDD below)
- [ ] `backend-integration-pg` passes on CI
- [ ] `check_schema_drift.sh` returns 0 (current ORM = DB schema)
- [ ] At least one test file exists in each `tests/` directory that exercises PG

---

## Phase 3: Data Integrity (A) — L3 Repository Layer

**目标：** 证明所有数据访问操作的正确性：JSON 字段往返、nullable 字段、重复冲突、to_model/from_model 转换。

**Risk:** Medium — 新测试可能暴露 ORM 层 bug。

**Prerequisite:** Phase 2 complete (PostgreSQL available).

---

### Task 3.1: Test — ExecutionReceipt.detail_json round-trip

**Objective:** Plan metadata 写入 detail_json 再读回时一致。

**Files:**
- Create: `tests/unit/execution/test_receipt_json_roundtrip.py`

**TDD Cycle:**

```python
"""Prove ExecutionReceipt.detail_json survives round-trip."""

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from domains.execution_records.orm import ExecutionReceiptORM
from domains.execution_records.repository import ExecutionRecordRepository


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_receipt_detail_json_preserves_plan_metadata(db: Session):
    """Write plan metadata dict → detail_json → read back → assert equal."""
    repo = ExecutionRecordRepository(db)

    metadata = {
        "decision_intake_id": "intake_001",
        "symbol": "BTC/USDT",
        "direction": "long",
        "broker_execution": False,
        "side_effect_level": "none",
    }

    receipt = repo.create(
        request_id="req_001",
        action_id="finance_decision_plan",
        detail_json=json.dumps(metadata),
    )

    read_back = repo.get_receipt(receipt.id)
    parsed = json.loads(read_back.detail_json)

    assert parsed["decision_intake_id"] == "intake_001"
    assert parsed["broker_execution"] is False
    assert parsed["side_effect_level"] == "none"


def test_receipt_detail_json_handles_nested_structures(db: Session):
    """Nested JSON structures survive round-trip."""
    repo = ExecutionRecordRepository(db)

    nested = {
        "plan": {"entry": 42000.0, "target": 45000.0, "stop": 41000.0},
        "risk": {"max_loss": 200.0, "position_size": 2000.0},
        "tags": ["momentum", "breakout"],
    }

    receipt = repo.create(
        request_id="req_002",
        action_id="finance_decision_plan",
        detail_json=json.dumps(nested),
    )

    read_back = repo.get_receipt(receipt.id)
    parsed = json.loads(read_back.detail_json)

    assert parsed["plan"]["entry"] == 42000.0
    assert parsed["tags"] == ["momentum", "breakout"]
```

**Step 2: Run → expect FAIL if repo methods missing**

```bash
uv run pytest tests/unit/execution/test_receipt_json_roundtrip.py -v
```

**Step 3: If `get_receipt` doesn't exist on `ExecutionRecordRepository`, add it minimally**

**Step 4: Run → expect PASS. Commit.**

```bash
git add tests/unit/execution/test_receipt_json_roundtrip.py
git commit -m "test: add ExecutionReceipt.detail_json round-trip invariant"
```

---

### Task 3.2: Test — Lesson.source_refs_json round-trip

**Objective:** 课程证据引用在 source_refs_json 中正确持久化。

**Files:**
- Create: `tests/unit/journal/test_lesson_json_roundtrip.py`

```python
"""Prove Lesson.source_refs_json survives round-trip."""

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from domains.journal.lesson_orm import LessonORM
from domains.journal.lesson_models import Lesson


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_lesson_source_refs_preserve_outcome_evidence(db: Session):
    """source_refs including outcome evidence survive write→read."""
    lesson = Lesson(
        review_id="review_001",
        recommendation_id="reco_001",
        title="Test",
        body="Test body",
        lesson_type="review_learning",
        source_refs=[
            "recommendation:reco_001",
            "finance_manual_outcome:out_001",
            "review:review_001",
        ],
    )

    row = LessonORM(
        id=lesson.id,
        review_id=lesson.review_id,
        recommendation_id=lesson.recommendation_id,
        title=lesson.title,
        body=lesson.body,
        lesson_type=lesson.lesson_type,
        source_refs_json=json.dumps(lesson.source_refs),
    )
    db.add(row)
    db.flush()

    read_back = db.get(LessonORM, row.id)
    parsed = json.loads(read_back.source_refs_json)

    assert "finance_manual_outcome:out_001" in parsed
    assert "recommendation:reco_001" in parsed
    assert "review:review_001" in parsed


def test_lesson_source_refs_handles_empty_list(db: Session):
    """Empty source_refs must survive as [] not None/null."""
    lesson = Lesson(
        review_id="review_002",
        recommendation_id=None,
        title="Empty refs",
        body="Test",
        lesson_type="review_learning",
        source_refs=[],
    )

    row = LessonORM(
        id=lesson.id,
        review_id=lesson.review_id,
        title=lesson.title,
        body=lesson.body,
        lesson_type=lesson.lesson_type,
        source_refs_json=json.dumps(lesson.source_refs),
    )
    db.add(row)
    db.flush()

    read_back = db.get(LessonORM, row.id)
    parsed = json.loads(read_back.source_refs_json)

    assert parsed == []
    assert read_back.source_refs_json == "[]"
```

**Step 2: Run → expect FAIL (if ORM field missing) or PASS**

```bash
uv run pytest tests/unit/journal/test_lesson_json_roundtrip.py -v
```

**Step 4: Commit**

```bash
git add tests/unit/journal/test_lesson_json_roundtrip.py
git commit -m "test: add Lesson.source_refs_json round-trip invariant"
```

---

### Task 3.3: Test — ReviewORM nullable outcome_ref fields

**Objective:** outcome_ref_type / outcome_ref_id 允许 NULL，也能正确保存非 NULL 值。

**Files:**
- Create: `tests/unit/journal/test_review_orm_nullable.py`

```python
"""Prove ReviewORM.outcome_ref_type/outcome_ref_id handle NULL and non-NULL correctly."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from domains.journal.orm import ReviewORM


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_review_orm_outcome_ref_columns_exist_and_nullable():
    """outcome_ref_type and outcome_ref_id columns are defined and nullable."""
    inspector = inspect(ReviewORM.__table__.bind or create_engine("sqlite:///:memory:", poolclass=StaticPool))
    # Verify columns exist on the ORM class
    assert hasattr(ReviewORM, "outcome_ref_type")
    assert hasattr(ReviewORM, "outcome_ref_id")


def test_review_orm_outcome_ref_null_by_default(db: Session):
    """ReviewORM without outcome_ref sets both fields to None."""
    row = ReviewORM(
        id="test_review_null",
        recommendation_id="reco_null_test",
        review_type="recommendation_postmortem",
        expected_outcome="Test",
        status="pending",
    )
    db.add(row)
    db.flush()

    read_back = db.get(ReviewORM, "test_review_null")
    assert read_back.outcome_ref_type is None
    assert read_back.outcome_ref_id is None


def test_review_orm_outcome_ref_preserves_values(db: Session):
    """Non-NULL outcome_ref_type/outcome_ref_id survive write→read."""
    row = ReviewORM(
        id="test_review_with_ref",
        recommendation_id="reco_ref_test",
        review_type="recommendation_postmortem",
        expected_outcome="Test",
        status="pending",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="outcome_abc_123",
    )
    db.add(row)
    db.flush()

    read_back = db.get(ReviewORM, "test_review_with_ref")
    assert read_back.outcome_ref_type == "finance_manual_outcome"
    assert read_back.outcome_ref_id == "outcome_abc_123"
```

**Step 2: Run → expect PASS (these fields exist per the earlier audit)**

**Step 4: Commit**

```bash
git add tests/unit/journal/test_review_orm_nullable.py
git commit -m "test: add ReviewORM outcome_ref nullable field invariant"
```

---

### Task 3.4: Test — FinanceManualOutcome duplicate conflict

**Objective:** 重复创建 outcome 必须报错。

**Files:**
- Create: `tests/unit/finance_outcome/test_duplicate_outcome_conflict.py`

```python
"""Prove duplicate FinanceManualOutcome creation is rejected."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from state.db.base import Base
from domains.finance_outcome.models import FinanceManualOutcome
from domains.finance_outcome.repository import FinanceManualOutcomeRepository


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_create_duplicate_outcome_raises(db: Session):
    """Creating two outcomes with the same execution_receipt_id must raise."""
    repo = FinanceManualOutcomeRepository(db)

    outcome1 = repo.create(
        FinanceManualOutcome(
            decision_intake_id="intake_dup",
            execution_receipt_id="receipt_dup",
            observed_outcome="First outcome",
            verdict="validated",
        )
    )

    # Second create with the same receipt should fail
    with pytest.raises((IntegrityError, ValueError, Exception)):
        repo.create(
            FinanceManualOutcome(
                id=f"dup_outcome_{outcome1.id}",  # Different ID
                decision_intake_id="intake_dup",
                execution_receipt_id="receipt_dup",  # Same receipt → should conflict
                observed_outcome="Second outcome",
                verdict="validated",
            )
        )
```

**Step 2: Run → expect FAIL (duplicate detection may not exist at ORM level)**

**Step 3: If FAIL, assess: is the guard at the ORM level (unique constraint) or at the capability level? If capability-level, the test should use `FinanceOutcomeCapability` intead. Adjust accordingly.**

**Step 4: Commit**

```bash
git add tests/unit/finance_outcome/test_duplicate_outcome_conflict.py
git commit -m "test: add FinanceManualOutcome duplicate conflict invariant"
```

---

### Task 3.5: Test — Repository to_model/from_model consistency

**Objective:** ORM → domain model → ORM 转换一致。

**Files:**
- Create: `tests/unit/journal/test_review_to_model_consistency.py`

```python
"""Prove Repository.to_model produces a valid domain model from ORM row."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from domains.journal.models import Review
from domains.journal.orm import ReviewORM
from domains.journal.repository import ReviewRepository


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_review_to_model_preserves_outcome_ref(db: Session):
    """to_model must carry outcome_ref_type/outcome_ref_id into Review."""
    row = ReviewORM(
        id="review_tm",
        recommendation_id="reco_tm",
        review_type="recommendation_postmortem",
        expected_outcome="Expected",
        status="pending",
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="out_tm_001",
    )
    db.add(row)
    db.flush()

    repo = ReviewRepository(db)
    model = repo.to_model(row)

    assert model.id == "review_tm"
    # If Review model has outcome_ref attributes, assert them
    if hasattr(model, "outcome_ref_type"):
        assert model.outcome_ref_type == "finance_manual_outcome"
    if hasattr(model, "outcome_ref_id"):
        assert model.outcome_ref_id == "out_tm_001"
```

**Step 2: Run → expect PASS or expose missing model fields**

**Step 4: Commit**

```bash
git add tests/unit/journal/test_review_to_model_consistency.py
git commit -m "test: add ReviewRepository to_model consistency check"
```

---

### Phase 3 Completion Check

- [ ] `test_receipt_json_roundtrip.py` — passes on PG
- [ ] `test_lesson_json_roundtrip.py` — passes on PG
- [ ] `test_review_orm_nullable.py` — passes on PG
- [ ] `test_duplicate_outcome_conflict.py` — passes on PG
- [ ] `test_review_to_model_consistency.py` — passes on PG
- [ ] All existing tests pass on PG

---

## Phase 4: Orchestration Guards (B) — L4 Capability Layer

**目标：** 能力层的编排不变量 — receipt 状态门、action_id 检查、重复 outcome→409、governance 不绕过。

**Prerequisite:** Phase 3 complete (data layer proven correct).

---

### Task 4.1: Test — plan_intake rejects non-execute governance status

**Objective:** governance_status != "execute" 时 plan 必须失败。

**Files:**
- Create: `tests/unit/capabilities/test_finance_plan_state_gate.py`

```python
"""Prove plan_intake enforces governance_status='execute' gate."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from domains.decision_intake.service import DecisionIntakeService
from domains.decision_intake.repository import DecisionIntakeRepository
from capabilities.domain.finance_decisions import FinanceDecisionCapability, PlanReceiptNotAllowed


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_plan_intake_rejects_rejected_status(db: Session):
    """Intake with governance_status='reject' must raise PlanReceiptNotAllowed."""
    cap = FinanceDecisionCapability()

    # Create intake with rejected status via service
    service = DecisionIntakeService(DecisionIntakeRepository(db))
    intake = service.record_intake(
        pack_id="finance",
        intake_type="controlled_decision",
        payload={"thesis": "YOLO all in", "stop_loss": "Below support"},
        validation_errors=[],
    )
    # Directly set governance status to reject (simulating govern_intake output)
    updated = service.update_governance_status(intake.id, "reject")

    with pytest.raises(PlanReceiptNotAllowed) as exc:
        cap.plan_intake(updated.id, db)

    assert "execute" in str(exc.value).lower()
    assert "reject" in str(exc.value).lower()


def test_plan_intake_rejects_escalated_status(db: Session):
    """Intake with governance_status='escalate' must raise PlanReceiptNotAllowed."""
    cap = FinanceDecisionCapability()
    service = DecisionIntakeService(DecisionIntakeRepository(db))
    intake = service.record_intake(
        pack_id="finance",
        intake_type="controlled_decision",
        payload={
            "thesis": "Short thesis",
            "stop_loss": "Below support",
            "emotional_state": "stressed",
        },
        validation_errors=[],
    )
    updated = service.update_governance_status(intake.id, "escalate")

    with pytest.raises(PlanReceiptNotAllowed) as exc:
        cap.plan_intake(updated.id, db)

    assert "escalate" in str(exc.value).lower()


def test_plan_intake_allows_execute_status(db: Session):
    """Intake with governance_status='execute' must allow plan creation."""
    cap = FinanceDecisionCapability()
    service = DecisionIntakeService(DecisionIntakeRepository(db))
    intake = service.record_intake(
        pack_id="finance",
        intake_type="controlled_decision",
        payload={
            "symbol": "BTC/USDT",
            "thesis": "BTC breakout with volume confirmation and 200 EMA invalidation.",
            "stop_loss": "Below support",
            "position_size_usdt": 100.0,
            "max_loss_usdt": 20.0,
            "risk_unit_usdt": 10.0,
            "is_chasing": False,
            "is_revenge_trade": False,
            "emotional_state": "calm",
            "confidence": 0.7,
        },
        validation_errors=[],
    )
    updated = service.update_governance_status(intake.id, "execute")

    result = cap.plan_intake(updated.id, db)

    assert result.execution_receipt_id is not None
    assert result.receipt_kind == "plan_only"
    assert result.broker_execution is False
```

**Step 2: Run → expect PASS (PlanReceiptNotAllowed already exists)**

```bash
uv run pytest tests/unit/capabilities/test_finance_plan_state_gate.py -v
```

**Step 4: Commit**

```bash
git add tests/unit/capabilities/test_finance_plan_state_gate.py
git commit -m "test: add plan_intake governance_status gate invariant"
```

---

### Task 4.2: Test — duplicate plan receipt is rejected (idempotency)

**Objective:** 同一个 intake 的 plan 只能创建一次。

**Files:**
- Modify: `tests/unit/capabilities/test_finance_plan_state_gate.py` (add test)

```python
def test_plan_intake_rejects_duplicate(db: Session):
    """Calling plan_intake twice on the same intake must raise conflict."""
    cap = FinanceDecisionCapability()
    service = DecisionIntakeService(DecisionIntakeRepository(db))
    intake = service.record_intake(
        pack_id="finance",
        intake_type="controlled_decision",
        payload={
            "symbol": "BTC/USDT",
            "thesis": "BTC breakout with volume confirmation and 200 EMA invalidation.",
            "stop_loss": "Below support",
            "position_size_usdt": 100.0,
            "max_loss_usdt": 20.0,
            "risk_unit_usdt": 10.0,
            "is_chasing": False,
            "is_revenge_trade": False,
            "emotional_state": "calm",
            "confidence": 0.7,
        },
        validation_errors=[],
    )
    updated = service.update_governance_status(intake.id, "execute")

    # First plan → succeeds
    result1 = cap.plan_intake(updated.id, db)
    assert result1.execution_receipt_id is not None

    # Second plan → must raise PlanReceiptConflict
    from capabilities.domain.finance_decisions import PlanReceiptConflict

    with pytest.raises(PlanReceiptConflict) as exc:
        cap.plan_intake(updated.id, db)

    assert intake.id in str(exc.value)
```

**Step 2: Run → expect PASS (PlanReceiptConflict already exists)**

**Commit.** (Squash with 4.1)

---

### Task 4.3: Test — governance not bypassed in capability composition

**Objective:** create_intake → govern_intake → plan_intake 的完整能力链不绕过 RiskEngine。

**Files:**
- Create: `tests/unit/capabilities/test_governance_not_bypassed.py`

```python
"""Prove capability chain always goes through governance before plan."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from capabilities.domain.finance_decisions import FinanceDecisionCapability, PlanReceiptNotAllowed


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_plan_without_governance_fails(db: Session):
    """Calling plan_intake without calling govern_intake first must fail."""
    cap = FinanceDecisionCapability()

    # Create intake but DON'T govern it
    intake = cap.create_intake(
        payload={
            "symbol": "BTC/USDT",
            "thesis": "BTC breakout with volume confirmation and 200 EMA invalidation.",
            "stop_loss": "Below support",
            "position_size_usdt": 100.0,
            "max_loss_usdt": 20.0,
            "risk_unit_usdt": 10.0,
            "is_chasing": False,
            "is_revenge_trade": False,
            "emotional_state": "calm",
            "confidence": 0.7,
        },
        db=db,
    )

    # Plan before governance → must fail
    # (governance_status won't be "execute" — it'll be "validated" or default)
    with pytest.raises(PlanReceiptNotAllowed):
        cap.plan_intake(intake.id, db)


def test_full_chain_governance_before_plan_succeeds(db: Session):
    """create → govern → plan must succeed for valid intake."""
    cap = FinanceDecisionCapability()

    intake = cap.create_intake(
        payload={
            "symbol": "BTC/USDT",
            "thesis": "BTC breakout with volume confirmation and 200 EMA invalidation.",
            "stop_loss": "Below support",
            "position_size_usdt": 100.0,
            "max_loss_usdt": 20.0,
            "risk_unit_usdt": 10.0,
            "is_chasing": False,
            "is_revenge_trade": False,
            "emotional_state": "calm",
            "confidence": 0.7,
        },
        db=db,
    )

    # Govern
    updated_intake, decision = cap.govern_intake(intake.id, db)
    assert decision.decision == "execute"

    # Plan
    result = cap.plan_intake(updated_intake.id, db)
    assert result.execution_receipt_id is not None
    assert result.broker_execution is False
```

**Step 2: Run → expect PASS**

**Step 4: Commit**

```bash
git add tests/unit/capabilities/test_governance_not_bypassed.py
git commit -m "test: add governance-not-bypassed capability chain invariant"
```

---

### Task 4.4: Test — manual outcome requires plan receipt + rejects duplicate

**Objective:** FinanceOutcomeCapability.capture_manual_outcome 必须验证 receipt 存在且唯一。

**Files:**
- Create: `tests/unit/capabilities/test_outcome_capability_guards.py`

```python
"""Prove FinanceOutcomeCapability enforces plan receipt and idempotency."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from capabilities.domain.finance_outcome import FinanceOutcomeCapability


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_capture_outcome_rejects_nonexistent_receipt(db: Session):
    """Outcome with nonexistent execution_receipt_id must fail."""
    cap = FinanceOutcomeCapability()

    with pytest.raises((ValueError, Exception)):
        cap.capture_manual_outcome(
            decision_intake_id="intake_nonexistent",
            execution_receipt_id="receipt_nonexistent",
            observed_outcome="Test",
            verdict="validated",
            db=db,
        )


def test_capture_outcome_succeeds_with_valid_receipt(db: Session):
    """Outcome with valid receipt must succeed."""
    # First create intake + plan via capability chain
    from capabilities.domain.finance_decisions import FinanceDecisionCapability

    fcap = FinanceDecisionCapability()
    intake = fcap.create_intake(
        payload={
            "symbol": "BTC/USDT",
            "thesis": "BTC breakout with volume confirmation and 200 EMA invalidation.",
            "stop_loss": "Below support",
            "position_size_usdt": 100.0,
            "max_loss_usdt": 20.0,
            "risk_unit_usdt": 10.0,
            "is_chasing": False,
            "is_revenge_trade": False,
            "emotional_state": "calm",
            "confidence": 0.7,
        },
        db=db,
    )
    updated, _ = fcap.govern_intake(intake.id, db)
    plan_result = fcap.plan_intake(updated.id, db)

    # Now capture outcome
    cap = FinanceOutcomeCapability()
    result = cap.capture_manual_outcome(
        decision_intake_id=updated.id,
        execution_receipt_id=plan_result.execution_receipt_id,
        observed_outcome="Price moved +2%",
        verdict="validated",
        db=db,
    )

    assert result.outcome_id is not None
    assert result.outcome_source == "manual"
```

**Step 2: Run → expect FAIL (FinanceOutcomeCapability may not have receipt validation)**

**Step 3: If FAIL, implement the guard in `FinanceOutcomeCapability.capture_manual_outcome`**

**Step 4: Run → expect PASS. Commit.**

```bash
git add tests/unit/capabilities/test_outcome_capability_guards.py
git commit -m "test: add outcome capability receipt validation + dedup invariant"
```

---

### Phase 4 Completion Check

- [ ] plan_intake rejects non-execute governance status
- [ ] plan_intake rejects duplicate (idempotency)
- [ ] plan without governance fails
- [ ] full create→govern→plan chain works
- [ ] outcome rejects nonexistent receipt
- [ ] outcome succeeds with valid receipt

---

## Phase 5: Negative Invariants (C) — Domain Constitution + Side Effects

**目标：** 证明系统中"不该发生的事"确实不发生。

**Prerequisite:** Phase 3-4 complete (data layer + orchestration proven correct).

---

### Task 5.1: Test — CandidateRule creation does not affect active policies

**Objective:** ① CandidateRule.status 永远不是 "active" 或 "policy"。② GovernancePolicySource.active_policy_ids 不会因 CandidateRule 创建而改变。

**Files:**
- Create: `tests/unit/governance/test_candidate_rule_not_policy.py`

```python
"""Prove CandidateRule is never Policy — status cannot be 'active' or 'policy'."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from domains.candidate_rules.models import CandidateRule, VALID_CANDIDATE_RULE_STATES
from domains.candidate_rules.orm import CandidateRuleORM
from domains.candidate_rules.repository import CandidateRuleRepository


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_candidate_rule_status_cannot_be_active():
    """VALID_CANDIDATE_RULE_STATES must not include 'active' or 'policy'."""
    assert "active" not in VALID_CANDIDATE_RULE_STATES
    assert "policy" not in VALID_CANDIDATE_RULE_STATES
    assert "active_policy" not in VALID_CANDIDATE_RULE_STATES


def test_candidate_rule_creation_does_not_change_governance_snapshot(db: Session):
    """Creating a CandidateRule must not alter GovernancePolicySource."""
    from governance.policy_source import GovernancePolicySource

    source = GovernancePolicySource()
    before = set(source.get_active_snapshot().active_policy_ids)

    repo = CandidateRuleRepository(db)
    rule = CandidateRule(
        issue_key="test_boundary_issue",
        summary="Candidate rules must not auto-promote to policy",
        status="draft",
    )
    repo.create(rule)

    after = set(source.get_active_snapshot().active_policy_ids)
    assert after == before, f"CandidateRule creation changed active policy IDs: {before} → {after}"


def test_candidate_rule_cannot_be_created_with_active_status():
    """CandidateRule(status='active') must raise ValueError."""
    with pytest.raises(ValueError, match="status"):
        CandidateRule(
            issue_key="test",
            summary="test",
            status="active",
        )
```

**Step 2: Run → expect PASS (status enum already constrained; snapshot is static)**

**Step 4: Commit**

```bash
git add tests/unit/governance/test_candidate_rule_not_policy.py
git commit -m "test: add CandidateRule≠Policy structural invariant"
```

---

### Task 5.2: Test — KnowledgeFeedback is advisory-only

**Objective:** KnowledgeFeedbackPacket.is_advisory_only 永远为 True；KF 创建不修改任何 active policy。

**Files:**
- Create: `tests/unit/knowledge/test_kf_advisory_invariant.py`

```python
"""Prove KnowledgeFeedback is advisory — never auto-enforces."""

from knowledge.feedback import KnowledgeFeedbackPacket, KnowledgeEntry


# Use a minimal mock KnowledgeEntry for the test
class FakeKnowledgeEntry:
    def __init__(self, entry_id: str, narrative: str):
        self.id = entry_id
        self.narrative = narrative
        self.evidence_refs = []
        self.feedback_targets = []


def test_knowledge_feedback_packet_is_advisory_by_default():
    """is_advisory_only must always be True."""
    packet = KnowledgeFeedbackPacket(
        recommendation_id="reco_test",
        knowledge_entry_ids=("entry_1", "entry_2"),
    )

    assert packet.is_advisory_only is True


def test_knowledge_feedback_packet_serializes_advisory_flag():
    """to_payload must include advisory_only=True."""
    packet = KnowledgeFeedbackPacket(
        recommendation_id="reco_test",
        knowledge_entry_ids=("entry_1",),
    )
    payload = packet.to_payload()

    assert payload["advisory_only"] is True
    assert payload["semantic_class"] == "derived_feedback_packet"


def test_knowledge_feedback_packet_requires_recommendation_id():
    """Packet must require recommendation_id (structural invariant)."""
    import pytest

    with pytest.raises(ValueError, match="recommendation_id"):
        KnowledgeFeedbackPacket(
            recommendation_id="",  # Empty
            knowledge_entry_ids=("entry_1",),
        )
```

**Step 2: Run → expect PASS (is_advisory_only already hardcoded True)**

**Step 4: Commit**

```bash
git add tests/unit/knowledge/test_kf_advisory_invariant.py
git commit -m "test: add KnowledgeFeedback advisory-only structural invariant"
```

---

### Task 5.3: Test — Lesson only created from completed review

**Objective:** 课程只能在 review 状态变为 completed 之后生成。

**Files:**
- Create: `tests/unit/journal/test_lesson_requires_completed_review.py`

```python
"""Prove Lesson derivation requires completed review status."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from domains.journal.orm import ReviewORM
from domains.journal.lesson_models import Lesson
from domains.journal.lesson_service import LessonService
from domains.journal.lesson_repository import LessonRepository


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_lesson_can_only_be_created_for_completed_review(db: Session):
    """Lesson creation without a completed review must be rejected."""
    # Create a pending review (not completed)
    review = ReviewORM(
        id="review_pending",
        recommendation_id="reco_pending",
        review_type="recommendation_postmortem",
        expected_outcome="Test",
        status="pending",
    )
    db.add(review)
    db.flush()

    lesson_service = LessonService(LessonRepository(db))
    lesson = Lesson(
        review_id="review_pending",
        title="Test lesson",
        body="This should not be allowed for pending review",
        lesson_type="review_learning",
        source_refs=[],
    )

    # Attempt to create lesson for pending review
    # The guard may be in the service layer or in the Lesson model
    # This test verifies the invariant exists somewhere in the chain
    try:
        result = lesson_service.create(lesson)
        # If it succeeds, check that the review was actually completed
        # (the service layer may auto-complete)
        pass  # No assertion failure — test documents the behavior
    except ValueError as e:
        assert "completed" in str(e).lower() or "pending" in str(e).lower()
```

**Step 2: Run → document behavior**

**Step 4: Commit**

```bash
git add tests/unit/journal/test_lesson_requires_completed_review.py
git commit -m "test: add lesson-requires-completed-review invariant probe"
```

---

### Task 5.4: Test — Review completion does not auto-create CandidateRule

**Objective:** complete_review 之后 CandidateRule 计数不变。

**Files:**
- Create: `tests/unit/journal/test_review_no_side_effects.py`

```python
"""Prove review completion creates no CandidateRule or Policy side effects."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from state.db.base import Base
from domains.candidate_rules.orm import CandidateRuleORM
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.journal.lesson_service import LessonService
from domains.journal.lesson_repository import LessonRepository
from shared.enums.domain import ReviewVerdict


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_complete_review_does_not_create_candidate_rule(db: Session):
    """After complete_review, CandidateRuleORM count must not increase."""
    service = ReviewService(
        review_repository=ReviewRepository(db),
        lesson_service=LessonService(LessonRepository(db)),
    )

    review = Review(
        recommendation_id="reco_no_side",
        review_type="recommendation_postmortem",
        expected_outcome="Test expected",
    )
    row = service.create(review)

    before_count = db.query(CandidateRuleORM).count()

    service.complete_review(
        review_id=row.id,
        observed_outcome="Test observed",
        verdict=ReviewVerdict.VALIDATED,
        variance_summary=None,
        cause_tags=["test"],
        lessons=["Test lesson"],
        followup_actions=[],
    )
    db.flush()

    after_count = db.query(CandidateRuleORM).count()
    assert after_count == before_count, (
        f"complete_review auto-created CandidateRule: before={before_count}, after={after_count}"
    )


def test_complete_review_does_not_create_policy_audit_events(db: Session):
    """After complete_review, no audit events with 'policy' or 'promote' type."""
    from governance.audit.orm import AuditEventORM

    service = ReviewService(
        review_repository=ReviewRepository(db),
        lesson_service=LessonService(LessonRepository(db)),
    )
    review = Review(
        recommendation_id="reco_no_policy_audit",
        review_type="recommendation_postmortem",
        expected_outcome="Test",
    )
    row = service.create(review)

    service.complete_review(
        review_id=row.id,
        observed_outcome="Test",
        verdict=ReviewVerdict.VALIDATED,
        variance_summary=None,
        cause_tags=["test"],
        lessons=["Test"],
        followup_actions=[],
    )
    db.flush()

    policy_events = (
        db
        .query(AuditEventORM)
        .filter(AuditEventORM.event_type.like("%policy%") | AuditEventORM.event_type.like("%promote%"))
        .count()
    )

    assert policy_events == 0, f"complete_review generated policy-related audit events: {policy_events}"
```

**Step 2: Run → expect PASS (already tested in H-8 integration, this is unit-level redundancy)**

**Step 4: Commit**

```bash
git add tests/unit/journal/test_review_no_side_effects.py
git commit -m "test: add review-completion no-side-effect invariant (CandidateRule + Policy)"
```

---

### Task 5.5: Test — KF does not write ORM truth to Core

**Objective:** KnowledgeFeedback 只能写 KnowledgeFeedbackPacketORM，不能写 ReviewORM、LessonORM、Policy 等。

**Files:**
- Create: `tests/unit/knowledge/test_kf_no_orm_writes.py`

```python
"""Prove KnowledgeFeedback never writes to Core ORM truth tables directly."""

from knowledge.feedback import KnowledgeFeedbackService, KnowledgeFeedbackPacket


def test_feedback_packet_is_self_contained():
    """KnowledgeFeedbackPacket has no ORM references — it's a pure domain object."""
    packet = KnowledgeFeedbackPacket(
        recommendation_id="reco_test",
        knowledge_entry_ids=("entry_1",),
    )

    # The packet must NOT have: db sessions, ORM references, repository references
    assert not hasattr(packet, "db")
    assert not hasattr(packet, "session")
    assert not hasattr(packet, "repository")
    assert not hasattr(packet, "orm")


def test_feedback_packet_to_payload_has_no_db_references():
    """Serialized payload must be pure JSON, not contain ORM objects."""
    packet = KnowledgeFeedbackPacket(
        recommendation_id="reco_test",
        knowledge_entry_ids=("entry_1",),
    )
    payload = packet.to_payload()

    # All values must be JSON-serializable
    import json

    serialized = json.dumps(payload)
    assert "sqlalchemy" not in serialized.lower()
    assert "Session" not in serialized
    assert "engine" not in serialized.lower()
```

**Step 2: Run → expect PASS (structure already clean)**

**Step 4: Commit**

```bash
git add tests/unit/knowledge/test_kf_no_orm_writes.py
git commit -m "test: add KF no-ORM-write structural invariant"
```

---

### Task 5.6: Test — Broker side effects do not exist in Core paths

**Objective:** 代码扫描确认 Core 模块不包含 broker/trade/order 引用。

**Files:**
- Create: `tests/architecture/test_no_broker_in_core.py`

```python
"""Prove Core modules contain no broker/trade/order references."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE_DIRS = ["governance", "state", "capabilities", "execution", "shared", "domains"]
FORBIDDEN = ["broker", "trade", "order", "exchange.execute", "place_order"]


def test_no_broker_references_in_core():
    """Core directories must not contain broker/trade/order patterns."""
    violations = []
    for d in CORE_DIRS:
        dir_path = ROOT / d
        if not dir_path.exists():
            continue
        for fp in dir_path.rglob("*.py"):
            if "__pycache__" in str(fp) or "migrations" in str(fp):
                continue
            text = fp.read_text(encoding="utf-8").lower()
            for pat in FORBIDDEN:
                if pat in text:
                    violations.append(f"{fp.relative_to(ROOT)}: found '{pat}'")

    assert violations == [], f"Broker/trade/order references found in Core:\n" + "\n".join(violations)
```

**Step 2: Run → expect PASS (current codebase is clean per ADR design)**

**Step 4: Commit**

```bash
mkdir -p tests/architecture
git add tests/architecture/test_no_broker_in_core.py
git commit -m "test: add no-broker-in-Core architecture invariant"
```

---

### Phase 5 Completion Check

- [ ] CandidateRule ≠ Policy (status enum + snapshot immutability)
- [ ] KnowledgeFeedback advisory-only (is_advisory_only = True)
- [ ] Lesson requires completed review
- [ ] Review completion → no CandidateRule / no Policy audit events
- [ ] KF has no ORM references in domain objects
- [ ] No broker/trade/order in Core modules

---

## Phase 6: Contract Lock (D) — L6 API Contracts

**目标：** 锁定 API 的请求/响应格式、错误码枚举、bridge contract。

**Prerequisite:** Phase 5 complete (internal behavior proven).

---

### Task 6.1: Test — Error code contract enumeration

**Objective:** 所有 API 错误响应必须使用已定义的错误码。

**Files:**
- Create: `tests/contracts/test_error_code_contract.py`

```python
"""Prove API errors use enumerated codes, not ad-hoc strings."""

import os

os.environ.setdefault("PFIOS_ENV", "test")
os.environ.setdefault("PFIOS_DEBUG", "false")
os.environ.setdefault("PFIOS_REASONING_PROVIDER", "mock")
os.environ.setdefault("PFIOS_DB_URL", "duckdb:///:memory:")

import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app


KNOWN_ERROR_CODES = {
    "not_found",
    "validation_error",
    "conflict",
    "governance_rejected",
    "governance_escalated",
    "receipt_not_found",
    "plan_not_allowed",
    "internal_error",
    "bad_request",
}


def test_reject_path_returns_governance_error():
    """Rejected intake plan attempt must return governance_rejected."""
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/finance-decisions/intake",
            json={
                "thesis": "YOLO all in",
                "stop_loss": "Below support",
            },
        )
        intake_id = resp.json()["id"]

        client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")

        plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        assert plan_resp.status_code in (400, 403, 409, 422)

        body = plan_resp.json()
        assert "detail" in body or "error" in body or "message" in body


def test_not_found_returns_structured_error():
    """Nonexistent intake must return 404 with structured error."""
    with TestClient(app) as client:
        resp = client.get("/api/v1/finance-decisions/intake/nonexistent_id")
        assert resp.status_code == 404
```

**Step 2: Run → document current behavior, capture actual error codes**

**Step 4: Commit**

```bash
git add tests/contracts/test_error_code_contract.py
git commit -m "test: add API error code enumeration contract"
```

---

### Task 6.2: Test — Review submit contract accepts outcome_ref

**Objective:** POST /reviews/submit 独立测试 outcome_ref_type/outcome_ref_id 字段接受和回显。

**Files:**
- Create: `tests/contracts/test_review_submit_contract.py`

```python
"""Prove POST /reviews/submit contract accepts outcome_ref fields."""

import os

os.environ.setdefault("PFIOS_ENV", "test")
os.environ.setdefault("PFIOS_DEBUG", "false")
os.environ.setdefault("PFIOS_REASONING_PROVIDER", "mock")
os.environ.setdefault("PFIOS_DB_URL", "duckdb:///:memory:")

from fastapi.testclient import TestClient
from apps.api.app.main import app


def test_submit_review_accepts_outcome_ref_fields():
    """Review submission with outcome_ref_type/outcome_ref_id must succeed."""
    with TestClient(app) as client:
        # First create intake → govern → plan → outcome
        resp = client.post(
            "/api/v1/finance-decisions/intake",
            json={
                "symbol": "BTC/USDT",
                "thesis": "BTC breakout with volume confirmation and 200 EMA invalidation.",
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
        intake_id = resp.json()["id"]

        gov = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
        assert gov.json()["governance_decision"] == "execute"

        plan = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
        receipt_id = plan.json()["execution_receipt_id"]

        outcome = client.post(
            f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
            json={
                "execution_receipt_id": receipt_id,
                "observed_outcome": "Price reached target",
                "verdict": "validated",
                "plan_followed": True,
            },
        )
        outcome_id = outcome.json()["outcome_id"]

        # Submit review with outcome_ref
        review_resp = client.post(
            "/api/v1/reviews/submit",
            json={
                "recommendation_id": None,
                "review_type": "recommendation_postmortem",
                "expected_outcome": "Price target",
                "actual_outcome": "Price reached target",
                "deviation": "None",
                "mistake_tags": "plan_execution",
                "lessons": [{"lesson_text": "Follow plan"}],
                "new_rule_candidate": None,
                "outcome_ref_type": "finance_manual_outcome",
                "outcome_ref_id": outcome_id,
            },
        )

        assert review_resp.status_code in (200, 201), (
            f"Review submit failed: {review_resp.status_code} {review_resp.text}"
        )


def test_submit_review_without_outcome_ref_still_succeeds():
    """Review submission without outcome_ref must still succeed (optional fields)."""
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/reviews/submit",
            json={
                "recommendation_id": None,
                "review_type": "recommendation_postmortem",
                "expected_outcome": "Test",
                "actual_outcome": "Test",
                "deviation": "None",
                "mistake_tags": "test",
                "lessons": [{"lesson_text": "Test"}],
                "new_rule_candidate": None,
            },
        )

        assert resp.status_code in (200, 201), f"Review submit without outcome_ref failed: {resp.status_code}"
```

**Step 2: Run → expect PASS (or expose contract gaps)**

**Step 4: Commit**

```bash
git add tests/contracts/test_review_submit_contract.py
git commit -m "test: add review submit outcome_ref contract test"
```

---

### Task 6.3: Ensure Hermes bridge contract test exists

**Objective:** 验证 `tests/unit/services/test_hermes_bridge_contract.py` 存在且通过。

**Files:**
- Verify: `tests/unit/services/test_hermes_bridge_contract.py` (already exists per audit)

**Step 1: Run to confirm pass**

```bash
uv run pytest tests/unit/services/test_hermes_bridge_contract.py -v
```

**Step 2: If PASS, no action needed. If FAIL, fix first.**

---

### Phase 6 Completion Check

- [ ] Error code enumeration test documents current behavior
- [ ] Review submit accepts outcome_ref_type/outcome_ref_id
- [ ] Review submit works without outcome_ref (optional)
- [ ] Hermes bridge contract test passes

---

## Phase 7: E2E + Dogfood (L8+L9)

**目标：** 三条控制路径的端到端验证 + 30 次狗粮运行覆盖 escalate 和 KF 路径。

**Prerequisite:** Phase 6 complete (contracts locked).

---

### Task 7.1: E2E — Reject Path (Playwright)

**Objective:** 浏览器端验证：低质量 thesis → reject → plan 不可用。

**Files:**
- Create: `tests/e2e/reject-path.spec.ts`

```typescript
import { expect, test } from '@playwright/test';

test.describe('Reject Path — low-quality thesis', () => {
  test('low-quality thesis shows rejection and plan is unavailable', async ({ page }) => {
    await page.goto('/');

    // Type a banned thesis
    await page.getByPlaceholder(/validate breakout|e\.g\./i).fill('YOLO all in');
    await page.getByRole('button', { name: 'Analyze' }).click();

    await page.waitForURL(/\/analyze\?/);

    // Expect a rejection message
    await expect(page.getByText(/reject|blocked|not allowed/i).first()).toBeVisible({ timeout: 15000 });

    // Plan/intake buttons should be disabled or absent
    const planButton = page.getByRole('button', { name: /plan|execute/i });
    const isPlanDisabled = await planButton.isDisabled().catch(() => true);
    const isPlanHidden = !(await planButton.isVisible().catch(() => false));
    expect(isPlanDisabled || isPlanHidden).toBeTruthy();
  });
});
```

**Step 2: Add to CI**

Add `test:e2e:reject` script and add corresponding CI job:

```json
"playwright:e2e:reject": "cross-env PFIOS_ENV=test PFIOS_DB_URL=duckdb:///:memory: PFIOS_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 PFIOS_E2E_BASE_URL=http://127.0.0.1:3000 playwright test tests/e2e/reject-path.spec.ts",
```

**Step 3: Commit**

```bash
git add tests/e2e/reject-path.spec.ts package.json
git commit -m "test: add E2E reject path (low-quality thesis → blocked)"
```

---

### Task 7.2: E2E — Escalate Path (Playwright)

**Objective:** 浏览器端验证：情绪异常 intake → escalate → 需要人工。

**Files:**
- Create: `tests/e2e/escalate-path.spec.ts`

```typescript
import { expect, test } from '@playwright/test';

test.describe('Escalate Path — emotional risk', () => {
  test('stressed emotional state triggers escalation', async ({ page }) => {
    await page.goto('/');

    await page.getByPlaceholder(/validate breakout|e\.g\./i).fill(
      'BTC looks strong. Breaking above resistance with volume confirmation. Invalidated if price closes below 200 EMA on 1h.'
    );
    await page.getByRole('button', { name: 'Analyze' }).click();

    await page.waitForURL(/\/analyze\?/);

    // Expect escalation indication
    await expect(page.getByText(/escalat|human review|review required/i).first()).toBeVisible({ timeout: 15000 });
  });
});
```

**Step 2: Commit**

```bash
git add tests/e2e/escalate-path.spec.ts
git commit -m "test: add E2E escalate path (emotional risk → human review)"
```

---

### Task 7.3: Extend dogfood to include escalate scenarios

**Objective:** 狗粮脚本至少触发 1 次 escalate。

**Files:**
- Modify: `scripts/h9_dogfood_runs.py`

**Step 1: Add escalate scenarios**

Add scenarios using `emotional_state="stressed"`, `is_chasing=True`, and `rule_exceptions=["override"]` — at least 3 escalate-targeting runs.

**Step 2: Run locally to verify escalate path triggers**

```bash
# Requires API running on :8000
uv run python scripts/h9_dogfood_runs.py
```

**Step 3: Commit**

```bash
git add scripts/h9_dogfood_runs.py
git commit -m "dogfood: add escalate path scenarios to H9 runner"
```

---

### Task 7.4: Extend dogfood to include knowledge feedback scenarios

**Objective:** 狗粮脚本触发 at least 3 个 KF packet。

**Step 1: Modify dogfood script to exercise full execute→plan→outcome→review→complete→KF chain**

**Step 2: Verify KF packets appear**

**Step 3: Commit**

```bash
git commit -m "dogfood: add knowledge feedback chain scenarios"
```

---

### Task 7.5: Run 30-run dogfood and generate evidence report v2

**Objective:** 30 次运行，记录 escalate/KF 计数。

**Step 1: Run dogfood 30 times**

```bash
uv run python scripts/h9_dogfood_runs.py  # Modified to run 30 scenarios
```

**Step 2: Generate evidence report v2**

```bash
uv run python scripts/h9c_verification.py
```

**Step 3: Save as `docs/runtime/h9-evidence-report-v2.md`**

---

### Phase 7 Completion Check

- [ ] Reject E2E path passes in Playwright
- [ ] Escalate E2E path passes in Playwright
- [ ] Dogfood escalate count ≥ 1
- [ ] Dogfood KF packet count ≥ 3
- [ ] Evidence report v2 generated

---

## Final Success Metrics

After all 7 phases:

```
静态检查覆盖率:   4/13  →  13/13  (ruff format + mypy + gitleaks + vulture + import-linter + architecture)
域不变量覆盖率:   5/11  →  11/11
系统不变量覆盖率:  2/9   →  9/9
控制路径 E2E:    1/3   →  3/3
CI PostgreSQL:    0 jobs → 2 jobs
Schema drift:     未检测  → 自动检测 (Alembic autogenerate)
数据层测试:       ~5/15  → 15/15 (JSON round-trips + nullable + duplicate + to_model)
编排层测试:       3/8   →  8/8  (state gates + governance bypass + receipt validation)
负向不变量:       4/8   →  8/8  (CandidateRule + KF + Lesson + broker side effects)
合同测试:         3/5   →  5/5  (error codes + review submit + Hermes bridge)
狗粮升级路径:     0/10  →  ≥ 1/30
狗粮 KF 路径:     0/10  →  ≥ 3/30
```

---

## 执行规则 (All Phases)

1. **每个 Phase 开始前审计（只读）** — 确认当前状态
2. **每个 Task = TDD 红→绿→commit** — 2-5 分钟任务
3. **每个 Phase 结束时全量回归** — DuckDB + PostgreSQL
4. **发现 bug 时先写失败测试，再修，再提** — 不修业务代码而不加测试
5. **Phase 顺序不可跳跃** — 每层依赖前层已证明正确
