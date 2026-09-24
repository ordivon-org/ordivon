# ARIES Same-Authority Lifecycle Fork Baseline R1

Date: 2026-09-23
Source: `aries-review-response-core-r1` + parent `aries-bounded-core-r1`

The upstream reply carrier contains **23,706 official-review records** and **32,691 author replies**. Restricting to the 1,720 papers already bound by the ARIES edit/comment core yields **6,380 official reviews** and **10,464 author responses**, with zero orphan reply parents.

All **196/196 manual test concerns** resolve to an exact source review with zero forum mismatches. All 196 have at least one review-level author-response context; **87/196** also have at least one positive concern-to-revision correspondence.

```text
Concern
  ├── exact source-review identity -> author reply thread
  └── annotated concern-edit correspondence -> revision edit(s)
```

This is a **lifecycle fork**, not a causal chain. It does not identify which reply resolves a particular concern and does not assert a `Response -> Revision` semantic or causal edge.
