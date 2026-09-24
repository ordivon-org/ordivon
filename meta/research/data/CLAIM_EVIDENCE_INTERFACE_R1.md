# Claim Evidence Interface R1

R1 adds a thin evidence interface over the bounded Context24 identity core:

```text
Claim
  ├── annotated_supporting_evidence_identity --> EvidenceIdentity
  └── annotated_method_context              --> MethodContext
```

`Claim` identity is the source coordinate `task:split:source_row_index`, not the native Context24 `id`, because the current Task 1 training carrier contains native-ID collisions.

`EvidenceIdentity` is identity-only in R1. Figure/table pixels, captions and full text are deliberately not inherited from an unmaterialized source. `MethodContext` is content-bound because the public Task 2 train carrier contains the annotated snippet text itself.

The correspondence edges encode organizer annotations. They do not establish scientific truth, causality, evidential sufficiency, method adequacy, or publication authority. Challenge-test gold remains withheld and is never synthesized by the adapter.
