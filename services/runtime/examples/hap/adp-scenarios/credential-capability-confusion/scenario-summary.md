# AP-CRED: Credential Capability Confusion
- **ADP pattern ID:** AP-CRED | **HAP objects:** HarnessCapability, HarnessBoundaryDeclaration | **Risk:** AP-R4
- **Boundary violated:** can_read_credentials != credential access
- **Expected gate:** BLOCKED | **Receipt:** BLOCKED | **Review:** REVIEW_REQUIRED
- **CandidateRule:** NON-BINDING (CR-ADP-007)
- **Safe:** "can_read_credentials=true (declaration only). credential_access_blocked=true."
- **Unsafe:** "The harness can read credentials, so it can access .env."
- **Field name:** can_access_secrets is forbidden. Use can_read_credentials.
- **No-action-authorization:** Non-executing. BLOCKED does not authorize credential access.
