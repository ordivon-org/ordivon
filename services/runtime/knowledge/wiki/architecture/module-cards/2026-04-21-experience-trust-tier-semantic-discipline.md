# Experience | Trust-tier / Semantic Discipline

- Module: Experience | Trust-tier / Semantic Discipline
- Layer: Experience
- Role: 把当前局部存在的 truthfulness copy 和 `TrustTierBadge` 收成更明确的前端语义纪律，区分 fact / artifact / outcome signal / derived hint / trace detail。
- Current Value:
  - 当前已有：
    - `TrustTierBadge`
    - 局部文案约束
    - RecentRecommendations / PendingReviews 上的 honest copy
  - 但这些语义是分散的，不是统一 helper / discipline。
- Remaining Gap:
  - surface 文案仍然靠局部手写
  - 没有统一 semantic copy helper
  - trace/outcome/hint/detail 的 tier 还没有更细分
- Immediate Action:
  - 本轮只做最小 semantic discipline helper
  - 具体实现：
    1. 新增前端 semantic helper / config
       - 统一 object signal 的 tier / copy
    2. 在 recommendation / pending review surface 复用这套 helper
       - 明确：
         - outcome = signal
         - knowledge hint = derived hint
         - trace detail = relation detail
         - report = artifact
    3. 增加测试，约束关键 copy 不回退成“closed loop / learned / truth”
- Required Test Pack:
  - `pnpm --dir apps/web exec tsc --noEmit`
  - unit:
    - semantic copy helper
    - tier mapping assertions
  - integration:
    - recommendation / review surface semantic smoke
  - failure-path:
    - unavailable/missing copy remains honest
  - invariants:
    - hint 不能显示成 truth
    - outcome 不能显示成 closed loop
    - artifact 不能显示成 fact
- Done Criteria:
  - 至少 recommendation / pending review 两个 surface 共享统一 semantic discipline helper
  - trust-tier copy 更一致
  - 关键误导文案被测试锁住
- Next Unlock:
  - 更完整 trust-tier system
- Not Doing:
  - 不做全站 design system 重构
  - 不做大规模 copy rewrite
