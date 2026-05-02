# Risk Ladder v0 (GOV-X)

> **v0 / internal governance / non-executing.** Risk classification is not permission.
> **Phase:** GOV-X

## AP-R0 through AP-R5 Formal Definitions

### AP-R0 — Mapping / Documentation Only

- **Capability equivalent:** C0
- **Allowed:** Documentation, taxonomy, source ledgers, stage notes, mappings
- **Forbidden:** File modification, shell execution, credential access, external calls
- **Gate:** READY_WITHOUT_AUTHORIZATION
- **Evidence:** Source references, boundary confirmation, New AI Context Check
- **Review:** Self-review + receipt
- **NO-GO triggers:** Any execution attempt

### AP-R1 — Read-Only Agentic Behavior

- **Capability equivalent:** C1
- **Allowed:** Read-only file analysis, grep/search, summarization
- **Forbidden:** File modification, shell write, external calls, credential access
- **Gate:** READY_WITHOUT_AUTHORIZATION or REVIEW_REQUIRED
- **Evidence:** Read scope, no-write confirmation, no-external-call confirmation
- **Review:** Self-review + boundary check
- **ADP patterns:** AP-INS (instruction truncation), AP-CTD (current truth drift), AP-EBO (external benchmark overclaim)

### AP-R2 — Workspace Write / Protected Path / Scope

- **Capability equivalent:** C2
- **Allowed:** File edits, patch generation, doc/code modifications
- **Forbidden:** Shell execution (unless separately gated), credentials, external calls
- **Gate:** REVIEW_REQUIRED; BLOCKED if protected paths or scope expansion
- **Evidence:** Files changed, allowed/forbidden comparison, protected path check, test/doc plan
- **Review:** Structured receipt + scope review
- **ADP patterns:** AP-FAT, AP-DRF, AP-PPV, AP-SCP

### AP-R3 — Shell / Build / Test Execution

- **Capability equivalent:** C3
- **Allowed:** Local commands, test runs, builds, migration dry-runs
- **Forbidden:** Credentials, external side effects (unless separately gated)
- **Gate:** REVIEW_REQUIRED; BLOCKED without explicit shell boundary and evidence plan
- **Evidence:** Exact commands, exit codes, relevant logs, failure classification, rollback plan
- **Review:** Structured receipt + evidence review + regression check
- **ADP patterns:** AP-SHE, AP-TST

### AP-R4 — Credential / Network / MCP / Browser / External Side-Effect

- **Capability equivalent:** C4
- **Allowed:** Nothing by default
- **Forbidden:** Everything by default
- **Gate:** **BLOCKED** by default; REVIEW_REQUIRED only under explicit future phase authorization
- **Evidence:** Authorization record, credential non-access proof, network/MCP/browser non-invocation proof, external side-effect block confirmation
- **Review:** Governance review required
- **ADP patterns:** AP-COL, AP-CRED, AP-EXT, AP-MCP, AP-EVL, AP-RDY
- **NO-GO triggers:** Any C4 capability without explicit authorization

### AP-R5 — Live Financial / Production / Irreversible Action

- **Capability equivalent:** C5
- **Allowed:** Nothing
- **Gate:** **NO-GO** in current project state
- **Evidence:** Cannot proceed — record NO-GO and stop
- **Review:** Cannot be approved by ordinary review
- **ADP patterns:** AP-REV, AP-BDM, AP-CRP
- **NO-GO triggers:** All C5 actions; review bypass; CandidateRule premature promotion

## Escalation Rules

1. Risk level can only increase, not decrease, without explicit reclassification
2. Shell escalation: AP-R1 → AP-R3 requires explicit boundary and evidence plan
3. External escalation: AP-R2 → AP-R4 requires governance review
4. Escalation must be recorded in execution receipt or review record
5. Escalation without record = BLOCKED

## Risk Level Rules (Repeated)

1. Risk level cannot decrease without explicit reclassification
2. External benchmark reference cannot lower risk
3. Existing baseline debt cannot lower risk
4. Evidence supports review; cannot grant authorization
5. C4 defaults to BLOCKED regardless of risk level
6. C5 defaults to NO-GO regardless of risk level
7. CandidateRule cannot become policy without review phase

*Phase: GOV-X | Risk classification is not permission.*
