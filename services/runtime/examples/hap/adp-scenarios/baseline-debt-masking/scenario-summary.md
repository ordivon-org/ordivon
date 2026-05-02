# AP-BDM: Baseline Debt Masking
- **ADP pattern ID:** AP-BDM | **HAP objects:** HarnessResultSummary, HarnessEvidenceBundle | **Risk:** AP-R5
- **Boundary violated:** Each failure must be classified as new or pre-existing with evidence
- **Expected gate:** BLOCKED | **Receipt:** BLOCKED | **Review:** Needs failure classification audit
- **CandidateRule:** NON-BINDING (CR-ADP-015)
- **Safe:** "10 failures: 10 pre-existing (verified against baseline commit). 0 new."
- **Unsafe:** "Some tests fail but they always failed. Nothing new."
- **No-action-authorization:** Non-executing.
