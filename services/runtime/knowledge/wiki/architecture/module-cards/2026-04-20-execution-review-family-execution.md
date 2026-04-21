# Execution | Review Family Execution

- Module: Execution | Review Family Execution
- Layer: Execution
- Role: 把 `review_complete` 从当前的 domain/service 直接写 row 和 audit，推进成真实的 execution family，具备 request / receipt / failure model，并保持 review 状态合法性仍由 domain/state machine 决定。
- Current Value:
  - `ReviewService.create(...)` 当前直接创建 review row 并写 `review_submitted` audit。
  - `ReviewService.complete_review(...)` 当前直接更新 review row、写 `review_completed` audit、backfill outcome、persist lessons，并准备 knowledge feedback。
  - `execution/catalog.py` 已将 `review_complete` 标记为 primary receipt candidate。
  - 但真实执行路径里还没有 request / receipt / failure model，也没有 API response refs。
- Remaining Gap:
  - review family 还是“动作真实发生了，但 execution 层还没接住”。
  - `review_complete` 成功时没有 execution refs。
  - 失败时没有 failed receipt，也没有与 row state 一致的 execution 审计链。
  - outcome / lesson / feedback 都挂在 review 下游，如果 review family 还不 receipt 化，会继续污染主链。
- Immediate Action:
  - 本轮只做 `review_complete`，不同时做 `review_submit`。
  - 新增 `execution/adapters/reviews.py`：
    - 作为 review family execution facade
    - 负责 request / receipt lifecycle
    - 负责 family-level execution semantics
    - 负责 audit refs attachment
    - 不重写 review domain transition rules
  - Success path:
    1. validate action context / boundary
    2. create execution request
    3. perform domain completion
    4. create success receipt only after domain completion succeeds
    5. attach request/receipt refs to audit payload
    6. return response with refs
  - Failure path:
    1. validate action context / boundary
    2. create execution request
    3. completion fails / invalid
    4. create failed receipt
    5. write failure audit with refs
    6. do not mutate review into completed success state
- Required Test Pack:
  - `python -m compileall ...`
  - unit:
    - review execution adapter success request/receipt
    - review execution adapter failure receipt
  - integration:
    - review complete API -> request / receipt / audit / review row 一致
  - failure-path:
    - invalid completion / missing review -> failed receipt
    - 无 success receipt 不得进入 completed success state
  - invariants:
    - review row final status must match execution receipt result
    - success receipt 对应成功 completion
    - failed receipt 不得伴随 success completion
  - state/data:
    - API response / audit payload / execution_request / execution_receipt / review row refs 一致
- Done Criteria:
  - `review_complete` 成为真实 request/receipt family
  - response / audit / state 三者都能看到 refs
  - failed receipt 不伴随 completed success state
  - 至少一组集成测试证明同一次 `review_complete` 动作的 refs 一致、语义一致
- Next Unlock:
  - `Knowledge | Feedback Consumption into Governance`
  - 后续 `review_submit` execution 化
- Not Doing:
  - 不改 review domain state machine 语义
  - 不做 `review_submit` execution 化
  - 不做 validation family execution 化
  - 不做全 execution adapter registry/platform
  - 不重构 outcome / lesson / feedback 下游逻辑
