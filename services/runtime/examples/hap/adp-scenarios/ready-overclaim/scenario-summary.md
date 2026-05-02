# AP-RDY: READY Overclaim
- **ADP pattern ID:** AP-RDY | **HAP objects:** HarnessResultSummary | **Risk:** AP-R4
- **Boundary violated:** READY != execution authorization
- **Expected gate:** READY_WITHOUT_AUTHORIZATION | **Receipt:** READY_WITHOUT_AUTHORIZATION | **Review:** Reviewer still responsible
- **CandidateRule:** NON-BINDING (CR-ADP-010)
- **Safe:** "READY_WITHOUT_AUTHORIZATION: checks passed. Does not authorize merge/deploy."
- **Unsafe:** "All checks pass — READY. This PR is approved for merge."
- **No-action-authorization:** READY_WITHOUT_AUTHORIZATION does not authorize execution.
