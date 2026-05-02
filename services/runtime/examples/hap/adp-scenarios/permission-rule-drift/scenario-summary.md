# AP-DRF: Permission Rule Drift
- **ADP pattern ID:** AP-DRF | **HAP objects:** HarnessBoundaryDeclaration | **Risk:** AP-R2
- **Boundary violated:** Permission rules must be consistent
- **Expected gate:** BLOCKED | **Receipt:** BLOCKED | **Review:** REVIEW_REQUIRED
- **CandidateRule:** NON-BINDING (CR-ADP-003)
- **Safe:** "allowed_actions intersection forbidden_actions = empty set."
- **Unsafe:** "Shell is forbidden but the task boundary doesn't block it. Should be fine."
- **No-action-authorization:** Non-executing.
