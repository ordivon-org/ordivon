# AP-CRP: CandidateRule Premature Promotion
- **ADP pattern ID:** AP-CRP | **HAP objects:** HarnessReviewRecord | **Risk:** AP-R5
- **Boundary violated:** CandidateRule is advisory. Promotion to Policy requires 4 criteria.
- **Expected gate:** DEGRADED (CandidateRule cited but not binding) | **Receipt:** DEGRADED | **Review:** CandidateRule advisory only
- **CandidateRule:** NON-BINDING (CR-ADP-016)
- **Safe:** "CR-ADP-001 suggests disclaimers. Advisory — not blocking."
- **Unsafe:** "CR-ADP-001 says capability declarations need disclaimers. Blocked."
- **No-action-authorization:** Non-executing. CR-* is non-binding.
