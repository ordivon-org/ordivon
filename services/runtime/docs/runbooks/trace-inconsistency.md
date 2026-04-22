# Trace Inconsistency

Use when trace links appear missing or inconsistent.

- Prefer persisted direct refs first.
- Then inspect structured fallback relations.
- Use `/api/v1/health/history` to confirm whether blocked runs or scheduler lag coincided with the inconsistency.
- Do not invent relations from narrative metadata.
