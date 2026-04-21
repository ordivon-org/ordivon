# Knowledge Feedback Domain

`domains/knowledge_feedback/` owns persisted derived feedback packet objects.

## Owns

- `KnowledgeFeedbackPacketRecord`
- repository and service access
- durable packet lookup for downstream readers

## Important Boundary

This domain stores derived feedback.
It is not policy truth, not long-term memory truth, and not a replacement for state facts.
