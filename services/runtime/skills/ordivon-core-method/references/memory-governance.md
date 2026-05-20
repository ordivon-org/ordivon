# Memory Governance (MEM0–MEM6)

From D4: AI Memory Governance debt processing.

| Type | Trust | Rule |
|------|-------|------|
| MEM0 — Task-local context | Expires with task | Never becomes project truth |
| MEM1 — User preference | Guides style | Cannot override factual evidence |
| MEM2 — Project context | Useful background | Verify against repo source before acting |
| MEM3 — Generated summary | Lossy | Must declare staleness risk; cannot be source |
| MEM4 — Source-linked | Higher confidence | Still requires freshness check |
| MEM5 — Deprecated / stale | Do not use | Historical analysis only |
| MEM6 — Sensitive | Restricted | Never expose in skills, prompts, or public receipts |

## Rules

- Memory may guide search, not replace source
- Memory may inform preference, not authorize action
- Conflict between memory and source → source wins
- Generated summaries in memory are always treated as lossy
- Stale memory must be marked or ignored
- Sensitive memory must not leak into skill output
