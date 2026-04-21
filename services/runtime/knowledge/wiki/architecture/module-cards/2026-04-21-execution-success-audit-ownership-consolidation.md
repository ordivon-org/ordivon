# Module Card

- Module: Execution | Success Audit Ownership Consolidation
- Layer: Execution
- Role: 把当前 execution family 中仍然存在的 success audit owner 分散问题收口成“每个 family 只有一个 success audit owner”，避免同一次动作同时由 adapter 和 domain/service 各自解释成功。
- Current Value:
  - `review_submit` / `review_complete` 已经由 [execution/adapters/reviews.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/execution/adapters/reviews.py) 作为 success audit owner，domain service 通过 `emit_*_audit=False` 让位。
  - `validation_issue_report` 已经支持 [issue_service.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/domains/journal/issue_service.py) 的 `emit_validation_issue_audit=False`，adapter 已是 success audit owner。
  - `recommendation_status_update` 目前在 [execution/adapters/recommendations.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/execution/adapters/recommendations.py) 和 [domains/strategy/service.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/domains/strategy/service.py) 两处都具备 success audit 能力，owner 语义不够单一。
  - `recommendation_generate` 和 `analysis_report_write` 目前仍由 analyze workflow 拥有 success audit，暂时没有 adapter/domain 双写问题。
- Remaining Gap:
  - recommendation family 的 success audit ownership 还没有正式收口。
  - execution catalog 虽然已有 family owner path，但“success audit 到底谁负责”没有统一纪律。
  - 如果现在不收口，后续更多 family 接入时会继续复制 adapter/service 双边成功审计逻辑。
- Immediate Action:
  - 本轮只做 family-level owner consolidation，不做 execution platform。
  - 最小动作：
    1. 为 `RecommendationService.transition(...)` 增加 `emit_recommendation_status_audit` 选项
    2. `RecommendationExecutionAdapter.update_status(...)` 调用 service 时显式关闭 domain success audit
    3. 明确 `recommendation_status_update` 的 success audit owner 为 adapter
    4. 补一组一致性测试，验证同一次动作只产生一条 success audit
  - 如代码中存在其他同类 obvious duplicate risk，只处理同模块最小必要点，不扩到全 execution registry
- Required Test Pack:
  - `python -m compileall ...`
  - unit:
    - recommendation transition with suppressed success audit
    - adapter success path still writes one audit
  - integration:
    - status update API success path 只留下单条 `recommendation_status_update` audit
  - failure-path:
    - failed path 仍只留下 failure audit，不影响现有 honest failure
  - invariants:
    - one action family -> one success audit owner
    - success audit refs / request / receipt / row state 语义一致
  - state/data:
    - recommendation status update response / audit / request / receipt / row 一致
- Done Criteria:
  - `recommendation_status_update` family 只有一个 success audit owner
  - success path 不再可能产生双重 success audit
  - failure path 保持现有 honest failure
  - 至少一组测试证明 single-owner discipline 真实成立
- Next Unlock:
  - `Orchestration | Recovery Policy Object`
  - `State | Trace Relation Hardening`
  - 后续 `Execution | Adapter Registry / Platform`
- Not Doing:
  - 不做 execution registry/platform
  - 不改 `recommendation_generate` owner
  - 不改 `analysis_report_write` owner
  - 不扩到 validation_usage_sync
  - 不重构所有 family 的审计体系
