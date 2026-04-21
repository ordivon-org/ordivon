# Governance | Policy Source of Truth

- Module: Governance | Policy Source of Truth
- Layer: Governance
- Role: 把当前散落在 `RiskEngine` 和默认治理逻辑里的规则来源显式化成最小 policy source，让治理决策不仅有 `decision / reasons / source`，还可追到它是由哪套 policy snapshot 产生的。
- Current Value:
  - `RiskEngine` 当前内嵌：
    - `ForbiddenSymbolsPolicy`
    - 默认 `no suggested actions -> escalate`
    - 默认 pass -> `execute`
  - 当前能看到的治理来源只有：
    - `risk_engine.forbidden_symbols_policy`
    - `risk_engine.default_validation`
  - 这已经足够表达 decision language，但还不足以表达“系统当前到底在用哪套 policy”。
- Remaining Gap:
  - 没有 first-class policy source object
  - `RiskEngine` 和 surface 只能给出 source 字符串，不能给出 policy set snapshot
  - 后续 governance / experience / execution 很难共享“同一套 active policy source”
- Immediate Action:
  - 本轮只做最小 policy source，不做复杂配置中心。
  - 具体实现：
    1. 新增 governance policy source 模块
       - 提供最小 `GovernancePolicySnapshot`
       - 至少包含：
         - `policy_set_id`
         - `active_policy_ids`
         - `default_decision_rule_ids`
    2. `RiskEngine` 改为从该 source 读取 active policies / default rules
    3. `GovernanceDecision` 增加最小 policy source exposure
       - 如 `policy_set_id`
       - `active_policy_ids`
    4. analyze response / audit / analysis metadata 中都能看到 policy source signal
- Required Test Pack:
  - `python -m compileall ...`
  - unit:
    - policy source snapshot load
    - risk engine uses policy source
  - integration:
    - analyze response / audit / metadata 含 policy source refs
  - failure-path:
    - policy source read failure时 honest fallback or explicit fail
  - invariants:
    - UI / workflow / service 不再各自发明 policy source
    - policy source 不自动被 knowledge hint 改写
  - state/data:
    - response / audit / metadata 中的 policy source 来自同一 snapshot
- Done Criteria:
  - 至少 analyze 主链能暴露统一 policy source
  - RiskEngine 不再只靠内部硬编码解释“当前策略”
  - response / audit / metadata 的 policy source refs 一致
- Next Unlock:
  - 更完整的 governance policy evolution
- Not Doing:
  - 不做复杂配置中心
  - 不做 policy hot reload
  - 不让 knowledge hint 直接改 policy
