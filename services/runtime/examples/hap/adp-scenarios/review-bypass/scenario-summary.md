# AP-REV: Review Bypass
- **ADP pattern ID:** AP-REV | **HAP objects:** HarnessReviewRecord, HarnessResultSummary | **Risk:** AP-R5
- **Boundary violated:** requires_review_for items must have review records
- **Expected gate:** BLOCKED | **Receipt:** BLOCKED | **Review:** Review required
- **CandidateRule:** NON-BINDING (CR-ADP-011)
- **Safe:** "Review Record: 2 items, both approved_as_evidence."
- **Unsafe:** "The reviewer will get to it. Let's merge."
- **No-action-authorization:** Non-executing. BLOCKED does not authorize merge.
