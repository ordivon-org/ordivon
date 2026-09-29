# Review Lifecycle Evidence Schema R3

R3 adds the ARIES same-authority source-review/response bridge while retaining the R2 evidence kinds.

```text
Concern
  ├── source_review_for_concern --> OfficialReview --> AuthorResponse thread
  └── corresponds_to_revision --------------------> Revision
```

The graph is a **lifecycle fork**, not a causal chain. `source_review_for_concern` proves source-record identity only; it does not prove exact span alignment or that any author reply resolves that extracted concern. `corresponds_to_revision` remains the independent ARIES annotation. No `Response -> Revision` semantic or causal edge is admitted in R3.
