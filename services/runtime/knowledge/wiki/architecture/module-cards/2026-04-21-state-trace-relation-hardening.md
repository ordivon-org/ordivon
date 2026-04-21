# Module Card

- Module: State | Trace Relation Hardening
- Layer: State
- Role: Replace the softest trace relations on the main review-side chain with harder persisted links where practical, so trace stops depending as heavily on audit-payload reconstruction for review execution and feedback packet references.
- Current Value:
  - `TraceService` already supports roots for workflow run, recommendation, and review.
  - Trace now reaches review, outcome, review execution refs, and knowledge feedback packet signal.
  - The current relation discipline is honest:
    - direct row fields first
    - metadata or audit fallback second
    - `present / missing / unlinked` instead of fabricated links
- Remaining Gap:
  - Review execution request/receipt refs are still reconstructed primarily from `review_completed` audit payloads.
  - Review-facing detail and trace both depend on audit-derived execution refs instead of stronger persisted links.
  - Knowledge feedback packet is persisted, but review and trace still mostly discover it via audit event payload rather than a harder review-linked relation path.
  - Recommendation -> latest review is still a query lookup, not a first-class relation.
- Immediate Action:
  1. Add the smallest practical hard links for the review-side chain.
  2. Prioritize:
     - persisted review execution refs
     - persisted latest feedback packet ref for review
  3. Update trace resolution order to prefer those direct persisted refs before audit fallback.
  4. Keep honest `missing / unlinked` behavior when older rows do not have the new links.
- Required Test Pack:
  - `python -m compileall ...`
  - unit:
    - trace prefers hard review refs over audit fallback
    - missing direct row falls back honestly to audit or unlinked
    - feedback packet relation prefers persisted ref over audit payload
  - integration:
    - review submit/complete path persists harder refs
    - `trace_review` and `trace_recommendation` resolve the harder refs
  - failure-path:
    - old rows without the new links still trace honestly
    - direct ref points to missing row -> `missing`, not fabricated `present`
  - invariants:
    - trace cannot invent relations from narrative data
    - direct persisted relations must outrank audit/metadata fallback
    - hardened refs still do not turn derived feedback into state truth
  - state/data:
    - review / execution / outcome / feedback packet refs remain semantically consistent across state, trace, and API surface
- Done Criteria:
  - At least the review-side execution refs are backed by harder persisted links.
  - Trace prefers direct persisted review-side relations over audit reconstruction.
  - Older rows without the new refs still degrade honestly.
  - Tests prove the harder relation path is real and preferred.
- Next Unlock:
  - `Knowledge | Retrieval / Recurring Issue Aggregation`
  - `Infrastructure | Health / Monitoring`
  - later richer graph behavior
- Not Doing:
  - Do not build a general graph engine.
  - Do not redesign report as a first-class object.
  - Do not change truth semantics for outcome or feedback packet.
  - Do not rewrite all trace roots at once.
