# ADR-006 Execution Plan — Finance Semantic Extraction from Core

> **For Hermes:** 按任务顺序 TDD 执行。每个任务 5-15 分钟，逐文件提交。
> **Prerequisite**: ADR-006 accepted. Wave 0-2 complete.

**Goal**: 将 `stop_loss` / `is_chasing` / `max_loss_usdt` 等 10 个 finance 字段名从 Core RiskEngine 中移除，迁移到 Finance Pack。

**Architecture**: RiskEngine 接受可选 `pack_policy` 参数，委托 domain 验证。Finance Pack 提供 `TradingDisciplinePolicy` 实现全部 Gate 1-4 逻辑。

**Tech Stack**: Python 3.11+, dataclasses, pytest

---

## 调用点全景

### 生产代码（1 处需改）

| 文件 | 行 | 当前 | 改为 |
|------|-----|------|------|
| `capabilities/domain/finance_decisions.py` | 66 | `RiskEngine().validate_intake(intake)` | `RiskEngine().validate_intake(intake, pack_policy=TradingDisciplinePolicy())` |

### 测试代码（48 处需改）

| 文件 | 调用次数 | 改动 |
|------|---------|------|
| `tests/unit/governance/test_h5_finance_governance_hard_gate.py` | 21 | 每处加 `pack_policy=TradingDisciplinePolicy()` |
| `tests/unit/governance/test_h9c2_escalate_coverage.py` | 17 | 同上 |
| `tests/unit/governance/test_h9c3_thesis_quality.py` | 10 | 同上 |

---

## Task 1: 创建 PackIntakePolicy 协议 + TradingDisciplinePolicy

**Objective**: 将 RiskEngine Gate 1-4 的全部逻辑精确迁移到一个新文件。不删除 RiskEngine 中的原有代码（留着做对比验证）。

**Files**:
- Create: `packs/finance/trading_discipline_policy.py`
- Create: `tests/unit/finance/test_trading_discipline_policy.py`

**Step 1: 写失败测试（全部 16 个）**

```python
# tests/unit/finance/test_trading_discipline_policy.py
import pytest
from packs.finance.trading_discipline_policy import (
    TradingDisciplinePolicy, RejectReason, EscalateReason,
)

@pytest.fixture
def policy():
    return TradingDisciplinePolicy()

# Gate 1: Field existence
def test_reject_missing_thesis(policy):
    reasons = policy.validate_fields({"stop_loss":"2%","emotional_state":"calm"})
    assert any("thesis" in r.message.lower() for r in reasons if isinstance(r, RejectReason))

def test_reject_missing_stop_loss(policy):
    reasons = policy.validate_fields({"thesis":"valid thesis with invalidation condition","emotional_state":"calm"})
    assert any("stop_loss" in r.message.lower() for r in reasons if isinstance(r, RejectReason))

def test_reject_missing_emotional_state(policy):
    reasons = policy.validate_fields({"thesis":"valid thesis with invalidation condition","stop_loss":"2%"})
    assert any("emotional_state" in r.message.lower() for r in reasons if isinstance(r, RejectReason))

# Gate 1: Thesis quality (from H-9C3)
def test_reject_banned_thesis(policy):
    reasons = policy.validate_fields({"thesis":"no specific thesis, just feels right","stop_loss":"2%","emotional_state":"calm"})
    assert any("banned" in r.message.lower() for r in reasons if isinstance(r, RejectReason))

def test_escalate_short_thesis(policy):
    reasons = policy.validate_fields({"thesis":"Short","stop_loss":"2%","emotional_state":"calm"})
    assert any("too short" in r.message.lower() for r in reasons if isinstance(r, EscalateReason))

def test_escalate_no_verifiability(policy):
    reasons = policy.validate_fields({"thesis":"BTC is going up because trend is strong","stop_loss":"2%","emotional_state":"calm"})
    assert any("verifiability" in r.message.lower() for r in reasons if isinstance(r, EscalateReason))

def test_valid_thesis_passes(policy):
    payload = {"thesis":"BTC breaking resistance with volume; invalidated if closes below 200 EMA.","stop_loss":"2%","emotional_state":"calm"}
    reasons = policy.validate_fields(payload)
    assert not any(isinstance(r, RejectReason) for r in reasons)
    assert not any(isinstance(r, EscalateReason) for r in reasons)

# Gate 2: Numeric fields
def test_reject_missing_max_loss(policy):
    reasons = policy.validate_numeric({"position_size_usdt":100,"risk_unit_usdt":10})
    assert any("max_loss_usdt" in r.message for r in reasons)

def test_reject_missing_position_size(policy):
    reasons = policy.validate_numeric({"max_loss_usdt":20,"risk_unit_usdt":10})
    assert any("position_size_usdt" in r.message for r in reasons)

def test_reject_missing_risk_unit(policy):
    reasons = policy.validate_numeric({"max_loss_usdt":20,"position_size_usdt":100})
    assert any("risk_unit_usdt" in r.message for r in reasons)

# Gate 3: Risk limits
def test_reject_max_loss_exceeds_ratio(policy):
    reasons = policy.validate_limits({"max_loss_usdt":500,"position_size_usdt":100,"risk_unit_usdt":100})
    assert any("exceeds" in r.message for r in reasons)

def test_reject_position_size_exceeds_ratio(policy):
    reasons = policy.validate_limits({"max_loss_usdt":100,"position_size_usdt":5000,"risk_unit_usdt":100})
    assert any("exceeds" in r.message for r in reasons)

def test_valid_limits_pass(policy):
    reasons = policy.validate_limits({"max_loss_usdt":200,"position_size_usdt":1000,"risk_unit_usdt":100})
    assert len(reasons) == 0

# Gate 4: Behavioral
def test_escalate_revenge_trade(policy):
    reasons = policy.validate_behavioral({"is_revenge_trade":True})
    assert any("is_revenge_trade" in r.message for r in reasons)

def test_escalate_chasing(policy):
    reasons = policy.validate_behavioral({"is_chasing":True})
    assert any("is_chasing" in r.message for r in reasons)

def test_calm_no_flags_passes(policy):
    reasons = policy.validate_behavioral({"is_revenge_trade":False,"is_chasing":False,"emotional_state":"calm","confidence":0.7,"rule_exceptions":[]})
    assert len(reasons) == 0
```

**Step 2: 运行测试 — 预期全部 FAIL**

```bash
uv run pytest tests/unit/finance/test_trading_discipline_policy.py -v
# 16 failed — ModuleNotFoundError: No module named 'packs.finance.trading_discipline_policy'
```

**Step 3: 实现 TradingDisciplinePolicy**

复制 RiskEngine 的精确逻辑。文件结构：

```python
# packs/finance/trading_discipline_policy.py
from __future__ import annotations

class RejectReason:
    def __init__(self, message: str): self.message = message

class EscalateReason:
    def __init__(self, message: str): self.message = message

_MAX_LOSS_TO_RISK_UNIT_RATIO = 2.0
_MAX_POSITION_TO_RISK_UNIT_RATIO = 10.0

_EMOTIONAL_RISK_KEYWORDS = frozenset({...})  # 从 RiskEngine 复制
_BANNED_THESIS_PATTERNS = frozenset({...})   # 从 thesis_quality 复制

class TradingDisciplinePolicy:
    def validate_fields(self, payload: dict) -> list[RejectReason | EscalateReason]:
        ...  # Gate 1: thesis + thesis_quality + stop_loss + emotional_state

    def validate_numeric(self, payload: dict) -> list[RejectReason]:
        ...  # Gate 2: max_loss_usdt / position_size_usdt / risk_unit_usdt

    def validate_limits(self, payload: dict) -> list[RejectReason]:
        ...  # Gate 3: 比率限制

    def validate_behavioral(self, payload: dict) -> list[EscalateReason]:
        ...  # Gate 4: is_revenge_trade / is_chasing / emotions / confidence / rule_exceptions

# Private helpers: _as_str, _as_positive_float, _contains_emotional_risk, _has_verifiability
```

**Step 4: 运行测试 — 预期全部 PASS**

```bash
uv run pytest tests/unit/finance/test_trading_discipline_policy.py -v
# 16 passed
```

**Step 5: 对比验证 — 确认新 Policy 与旧 RiskEngine 行为一致**

写一个快速对比脚本（手动跑一次即可）：
```bash
uv run python -c "
from governance.risk_engine.engine import RiskEngine
from packs.finance.trading_discipline_policy import TradingDisciplinePolicy
# 用相同输入同时跑两边，确认决策一致
"
```

**Step 6: 提交**

```bash
git add packs/finance/trading_discipline_policy.py tests/unit/finance/test_trading_discipline_policy.py
git commit -m "feat(adr-006): create TradingDisciplinePolicy with all H-5 gate logic"
```

---

## Task 2: 重构 RiskEngine.validate_intake() 接受 pack_policy

**Objective**: RiskEngine 不再直接引用 finance 字段名，改为委托 pack_policy。

**Files**:
- Modify: `governance/risk_engine/engine.py`
- Modify: `tests/unit/governance/test_h5_finance_governance_hard_gate.py` (21 calls)
- Modify: `tests/unit/governance/test_h9c2_escalate_coverage.py` (17 calls)
- Modify: `tests/unit/governance/test_h9c3_thesis_quality.py` (10 calls)

**Step 1: 重构 RiskEngine**

将 `validate_intake()` 改为：

```python
def validate_intake(
    self,
    intake: DecisionIntake,
    pack_policy=None,  # ADR-006: optional PackIntakePolicy
    advisory_hints: ... = None,
) -> GovernanceDecision:
    hints = tuple(advisory_hints or ())
    snapshot = self.policy_source.get_active_snapshot()

    reject_reasons: list[str] = []
    escalate_reasons: list[str] = []

    # Gate 0: intake must be validated (generic — stays)
    if intake.status != "validated":
        reject_reasons.append(...)

    # Gates 1-4: delegated to pack_policy
    if pack_policy is not None and intake.payload:
        payload = intake.payload

        for reason in pack_policy.validate_fields(payload):
            if isinstance(reason, RejectReason):
                reject_reasons.append(reason.message)
            elif isinstance(reason, EscalateReason):
                escalate_reasons.append(reason.message)

        for reason in pack_policy.validate_numeric(payload):
            reject_reasons.append(reason.message)

        for reason in pack_policy.validate_limits(payload):
            reject_reasons.append(reason.message)

        for reason in pack_policy.validate_behavioral(payload):
            escalate_reasons.append(reason.message)

    # Decision priority (generic — stays)
    if reject_reasons:
        return GovernanceDecision(decision="reject", ...)
    if escalate_reasons:
        return GovernanceDecision(decision="escalate", ...)
    return GovernanceDecision(decision="execute", ...)
```

**保留但不调用**：原有 Gate 1-4 代码作为注释保留一个 commit，下一个 commit 再删除。这样 git history 清晰。

**导入添加**：
```python
from packs.finance.trading_discipline_policy import RejectReason, EscalateReason
```

这个导入是过渡性的——pack_policy 的类型在 protocol 中定义，但 RejectReason/EscalateReason 的具体类需要导入做 isinstance 检查。最终应该提取到 shared 层，但先不引入额外重构。

**Step 2: 更新所有测试 — 每处加 `pack_policy=TradingDisciplinePolicy()`**

对 test_h5、test_h9c2、test_h9c3 三个文件，全局搜索替换：
```
engine.validate_intake(intake)
→
engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
```

**Step 3: 运行测试 — 必须全部通过**

```bash
uv run pytest tests/unit/governance/test_h5_finance_governance_hard_gate.py tests/unit/governance/test_h9c2_escalate_coverage.py tests/unit/governance/test_h9c3_thesis_quality.py tests/unit/finance/test_trading_discipline_policy.py -v
```

**Step 4: 提交**

```bash
git add governance/risk_engine/engine.py tests/unit/governance/
git commit -m "refactor(adr-006): delegate RiskEngine gates to pack_policy"
```

---

## Task 3: 更新生产调用点

**Objective**: 唯一的运行时调用者传入 TradingDisciplinePolicy。

**Files**:
- Modify: `capabilities/domain/finance_decisions.py`

**Step 1: 修改**

```python
# capabilities/domain/finance_decisions.py:66
# Before:
decision = RiskEngine().validate_intake(intake)

# After:
from packs.finance.trading_discipline_policy import TradingDisciplinePolicy
decision = RiskEngine().validate_intake(intake, pack_policy=TradingDisciplinePolicy())
```

**Step 2: 运行集成测试**

```bash
uv run pytest tests/integration/test_finance_decision_intake_api.py tests/integration/test_h7_manual_outcome_api.py tests/integration/test_h8_review_closure.py -v
```

**Step 3: 提交**

```bash
git add capabilities/domain/finance_decisions.py
git commit -m "feat(adr-006): wire TradingDisciplinePolicy into finance decision govern path"
```

---

## Task 4: 从 RiskEngine 中删除 Finance 代码

**Objective**: 清理 RiskEngine 中不再需要的 finance 特定代码。

**Files**:
- Modify: `governance/risk_engine/engine.py`

**Step 1: 删除**

删除以下内容：
- `from governance.risk_engine.thesis_quality import check_thesis_quality` (import)
- `_MAX_LOSS_TO_RISK_UNIT_RATIO` 常量
- `_MAX_POSITION_TO_RISK_UNIT_RATIO` 常量
- `_as_str()` 函数
- `_as_positive_float()` 函数
- `_EMOTIONAL_RISK_KEYWORDS` 常量
- `_contains_emotional_risk()` 函数
- Gate 1-4 的注释代码（如果 Task 2 中保留了注释版本）

保留：
- `from domains.decision_intake.models import DecisionIntake` (import)
- `from governance.decision import GovernanceDecision` (import)
- `from governance.policy_source import GovernancePolicySource` (import)
- `validate_analysis()` 方法（不涉及 finance）
- Gate 0：status 检查
- Decision priority：reject > escalate > execute

**Step 2: 验证 RiskEngine 中不再有 finance 字段名**

```bash
rg "stop_loss|max_loss_usdt|position_size_usdt|risk_unit_usdt|is_revenge_trade|is_chasing" governance/risk_engine/engine.py
```
**预期**: 0 结果

```bash
rg "thesis_quality" governance/risk_engine/engine.py
```
**预期**: 0 结果

**Step 3: 运行全部测试**

```bash
uv run pytest tests/unit/ tests/integration/ -q --no-header
# 预期: 全部通过
```

**Step 4: 提交**

```bash
git add governance/risk_engine/engine.py
git commit -m "refactor(adr-006): remove finance semantics from Core RiskEngine"
```

---

## Task 5: 最终验证

**Step 1: PG 全回归**

```bash
PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test uv run pytest tests/ -q --no-header -p no:cacheprovider
```

**Step 2: 狗粮验证**

```bash
uv run python scripts/h9c_verification.py
# 预期: H-9C1 5/5, H-9C2 7/7, H-9C3 6/6 = 18/18
```

**Step 3: 端到端狗粮**

```bash
uv run python scripts/h9_dogfood_runs.py
# 预期: 9 runs, governance 分布与 H-9E 一致
```

**Step 4: git log 确认**

```bash
git log --oneline -5
# 应该看到 6 个 commit（含 Task 4）
```

**Step 5: Tag**

```bash
git tag post-p4-finance-extraction
```

---

## 任务总览

```
Task 1  创建 TradingDisciplinePolicy     (20 分钟)  1 新文件 + 16 新测试
Task 2  重构 RiskEngine                  (15 分钟)  1 文件修改 + 48 测试适配
Task 3  更新生产调用点                   (5 分钟)   1 行改动
Task 4  删除 RiskEngine 中的 Finance 代码 (10 分钟)  删除 ~150 行
Task 5  最终验证                         (15 分钟)  全量测试 + 狗粮
─────────────────────────────────────────────────
总计                                    ~65 分钟   5 个 commit
```

## 风险与回滚

- **每个 Task 独立可回滚**：git revert 单个 commit 即可
- **Task 1 是纯新增**：不影响任何现有代码
- **Task 2 是传染性最大的改动**（48 个测试调用点），但改动机械（每处加一个参数）
- **如果 Task 4 后测试失败**：回滚 Task 4，保留 Task 1-3（Finance 代码仍在 RiskEngine 中但不再被调用）
- **最终保险**：`rg "stop_loss" governance/risk_engine/engine.py` → 0 结果 = 提取成功

## 接受标准

1. `rg "stop_loss|is_chasing|risk_unit_usdt" governance/risk_engine/engine.py` → 0 结果
2. 全部 H-5/H-9C 测试通过
3. 狗粮产生相同的 governance 决策
4. 加上第二个 domain Pack 不需要修改 Core
