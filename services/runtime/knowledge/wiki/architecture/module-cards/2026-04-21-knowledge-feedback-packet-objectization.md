# Module Card

- Module: Knowledge | Feedback Packet Objectization
- Layer: Knowledge
- Role: 把当前只存在于 `KnowledgeFeedbackService`、review completion metadata、audit signal 中的 `KnowledgeFeedbackPacket`，推进成最小 first-class persisted object，使其可以被查询、追踪、审计，但不把它升级成 policy truth 或长期 memory。
- Current Value:
  - `KnowledgeFeedbackPacket` 目前是 [knowledge/feedback.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/knowledge/feedback.py) 中的 dataclass。
  - 生成路径已经真实存在：
    - `domains/journal/service.py` 的 `ReviewService.complete_review(...)`
    - `LessonExtractionService -> KnowledgeFeedbackService.build_packet(...)`
  - 消费路径已经真实存在：
    - [governance/feedback.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/governance/feedback.py)
    - [intelligence/feedback.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/intelligence/feedback.py)
  - 当前留下的 only durable trace 是：
    - `knowledge_feedback_prepared` audit event
    - review completion response metadata
    - later analyze metadata counters
- Remaining Gap:
  - 没有 `KnowledgeFeedbackPacket` 的 ORM / repository / service。
  - 没有 packet id，无法稳定查询、追踪或做后续消费统计。
  - 当前 governance/intelligence consumption 需要每次从 lesson/outcome 现算 packet，缺少明确的 persisted feedback object。
  - trace 里目前只有 `knowledge_feedback` signal，不是 first-class feedback object relation。
- Immediate Action:
  - 本轮只做最小对象化，不做 retrieval 系统，不做 rule candidate，不做 policy rewrite。
  - 具体最小动作：
    1. 新增 `KnowledgeFeedbackPacket` 的 state-backed object：
       - packet id
       - recommendation_id
       - knowledge_entry_ids
       - governance_hints
       - intelligence_hints
       - created_at
    2. 在 `ReviewService.complete_review(...)` 中，packet 生成后真实持久化
    3. governance / intelligence reader 优先读取 persisted packet，而不是每次现算
    4. audit 继续保留，但 audit 不再是 packet 的唯一 durable source
    5. 如有需要，在 trace 中补最小 packet ref，但不发明新的闭环语义
- Required Test Pack:
  - `python -m compileall ...`
  - unit:
    - feedback packet model validation
    - repository create/get/list behavior
    - governance/intelligence reader 优先读取 persisted packet
  - integration:
    - `review_complete -> packet persisted -> governance/intelligence read path` 成立
  - failure-path:
    - packet persistence 失败时不得伪装 packet 已存在
    - governance/intelligence read path 在 packet 不存在时诚实 fallback
  - invariants:
    - feedback packet 是 derived object，不覆盖 state truth
    - feedback packet 不等于 policy update
    - feedback packet 不等于 long-term memory write
  - state/data:
    - packet row 与 recommendation / knowledge_entry_ids / audit refs 一致
- Done Criteria:
  - `KnowledgeFeedbackPacket` 成为真实 persisted object
  - review completion 后可查询到 packet
  - governance / intelligence 至少一条读取路径优先走 persisted packet
  - packet 仍被明确表达为 derived feedback，不冒充 truth 或 policy
  - 至少一组集成测试证明 `review -> packet -> downstream read` 真实成立
- Next Unlock:
  - `Knowledge | Retrieval / Recurring Issue Aggregation`
  - `State | Trace Relation Hardening`
  - 后续 feedback consumption analytics
- Not Doing:
  - 不做 policy source rewrite
  - 不做 long-term memory / shared memory
  - 不做 knowledge retrieval 全系统
  - 不做 rule candidate aggregation
  - 不做 UI surface 扩展
