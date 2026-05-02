# Agentic Pattern Taxonomy v0 (ADP-1)

> **v0 / internal mapping / reference-only.** Pattern identification is not policy
> activation. CandidateRule is not binding policy. Risk classification is not
> authorization.
> **Phase:** ADP-1 | **Risk:** AP-R0

## Agentic Pattern Risk Ladder

| Level | Name | Scope | Allowed in ADP-1? |
|-------|------|-------|-------------------|
| AP-R0 | Documentation / taxonomy | Mapping only | ✅ Current phase |
| AP-R1 | Read-only / interpretive | Observation risk | 📋 Described only |
| AP-R2 | Workspace-write / patch | Modification risk | 📋 Described only |
| AP-R3 | Shell / build / test | Execution risk | 📋 Described only |
| AP-R4 | Credential / external API / MCP | Side-effect risk | 📋 Described only |
| AP-R5 | Live financial / production / irreversible | Catastrophic risk | ❌ NO-GO |

ADP-1 is AP-R0 only. The taxonomy describes AP-R1 through AP-R5 patterns but
does not enable or authorize them.

---

## Pattern 1: Capability-to-Authorization Collapse (AP-COL)

**Short definition:** A harness can technically perform an action (can_X), so the
system, user, or agent treats it as authorized to perform that action (may_X).

**Source seeds:** SRC-001 (OGAP-Z can_X≠may_X), SRC-002 (HAP capability≠authorization),
SRC-006 (OpenAI PF capability threshold), SRC-007 (Anthropic RSP ASL deployment standards)

**HAP objects affected:** HarnessCapability, HarnessAdapterManifest, HarnessBoundaryDeclaration
**OGAP concepts affected:** Capability→Authorization mapping, READY≠approval
**EGB concepts affected:** Capability-scaled governance gap, deployment authorization gap
**Ordivon controls affected:** Boundary Confirmation, NO-GO Ladder, Authority Impact, Stage Gate

**Trigger conditions:** can_X=true in capability manifest, no boundary declaration,
no governance review, no authority impact check.

**Boundary violated:** Capability declaration ≠ authorization. can_X ≠ may_X.

**Detection signals:**
- Adapter manifest has can_X=true but no authority_statement disclaiming authorization
- Task request consumes capability without boundary_declaration blocking it
- Receipt claims action was "approved" based on capability alone
- No Stage Gate or Closure Predicate check before action

**Required evidence:**
- Capability manifest with explicit authority_statement (denial)
- Boundary declaration showing capabilities blocked or review-required
- Stage Gate result (READY/DEGRADED/BLOCKED)
- Authority Impact classification

**Gate response:** BLOCKED if capability is consumed without boundary check.
DEGRADED if boundary exists but authority impact is unset.

**Review outcome:** REVIEW_REQUIRED. Capability consumption requires explicit
boundary declaration and authority statement.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-001: "Every harness capability
declaration must include an authority denial statement stating can_X does not
imply may_X."

**Future checker/schema/eval implication:** Schema validator should reject any
HarnessCapability object lacking authority_statement. Architecture checker
should verify no adapter consumes capability without boundary.

**NO-GO condition:** Automatic authorization based on capability presence.

**Example safe phrasing:** "can_run_shell=True means the harness has the technical
ability to execute shell commands. This does not authorize shell execution.
Shell is blocked at the task boundary until reviewed."

**Example unsafe phrasing:** "The harness can run shell commands, so it's approved
to execute the build."

---

## Pattern 2: Approval Fatigue / Sandbox Drift (AP-FAT)

**Short definition:** Manual approval friction leads to auto-approval creep,
sandbox boundary erosion, or approval scope expansion without corresponding
governance escalation.

**Source seeds:** SRC-002 (HAP boundary declaration), SRC-006 (OpenAI PF
deployment gate), SRC-011 (Codex allow/ask/deny model)

**HAP objects affected:** HarnessBoundaryDeclaration, HarnessTaskRequest, HarnessReviewRecord
**OGAP concepts affected:** GovernanceDecision (READY/DEGRADED/BLOCKED)
**EGB concepts affected:** Deployment authorization gap, capability-scaled governance
**Ordivon controls affected:** Stage Gate, Review Record, Boundary Confirmation

**Trigger conditions:** Frequent manual approval events, approval scope
expansion without Stage Gate escalation, boundary drift (blocked→review→allowed
without explicit justification).

**Boundary violated:** Boundary scopes must match risk level. Scope expansion
requires governance escalation.

**Detection signals:**
- Approval frequency increases while boundary tightness decreases
- requires_review_for list shrinks over time
- Blocked actions migrate to "requires review" without justification
- Stage Gate classification does not escalate with scope expansion

**Required evidence:**
- Boundary declaration change history
- Review record showing approval rationale
- Stage Gate classification consistency

**Gate response:** BLOCKED if boundary scope expands without Stage Gate
escalation. DEGRADED if approval frequency high but boundary stable.

**Review outcome:** Needs escalation review. Scope expansion must be
justified with risk assessment.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-002: "Boundary scope
expansion requires Stage Gate escalation and explicit risk reclassification."

**Future checker/schema/eval implication:** Boundary declaration change
tracker. Diff-based boundary drift detection.

**NO-GO condition:** Automatic scope expansion.

**Example safe phrasing:** "Boundary unchanged since initial declaration.
requires_review_for list: 3 items, reviewed weekly."

**Example unsafe phrasing:** "We used to block shell, but it was annoying.
Now it just needs approval. It's fine."

---

## Pattern 3: Permission Rule Drift (AP-DRF)

**Short definition:** allow/ask/deny rules grow stale, conflict with each
other, or create bypass paths that allow actions the system intended to block.

**Source seeds:** SRC-002 (HAP boundary), SRC-007 (Anthropic RSP security
standards), SRC-011 (Codex allow/ask/deny), SRC-012 (Claude Code permissions),
SRC-013 (MCP authorization)

**HAP objects affected:** HarnessBoundaryDeclaration, HarnessTaskRequest,
HarnessAdapterManifest
**OGAP concepts affected:** GovernanceDecision, capability-manifest
**EGB concepts affected:** Systematic risk taxonomy gap
**Ordivon controls affected:** Architecture Checker, Boundary Confirmation,
NO-GO Ladder

**Trigger conditions:** Permission rules added over multiple phases without
consistency check. Conflicting allow/deny rules. Rules that can be satisfied
by alternative paths.

**Boundary violated:** Permission rules must be consistent and non-bypassable.
No path from allow to forbidden action without review.

**Detection signals:**
- Conflicting entries in allowed_actions and forbidden_actions
- Action appears in allowed_actions but is also in NO-GO Ladder
- Two rules that together enable a forbidden action chain
- Old rules from previous phases still active without review

**Required evidence:**
- Permission rule consistency check
- Cross-reference between boundary declaration and NO-GO Ladder
- Phase-boundary rule expiration audit

**Gate response:** BLOCKED if conflicting rules detected. DEGRADED if old
rules present but no conflicts.

**Review outcome:** Needs rule audit. Stale rules expired or re-justified.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-003: "Permission rules must
be audited for consistency at each Stage Gate. Conflicting rules must be
resolved before READY."

**Future checker/schema/eval implication:** Rule consistency checker. Stale
rule expiration automation.

**NO-GO condition:** Bypass path from allow to forbidden without review.

**Example safe phrasing:** "Permission rules audited at Phase boundary.
allowed_actions ∩ forbidden_actions = ∅. No expired rules active."

**Example unsafe phrasing:** "Shell is in forbidden_actions but the task
request's boundary_declaration doesn't block it. It should be fine."

---

## Pattern 4: Instruction Truncation / Priority Drift (AP-INS)

**Short definition:** Repo instructions (AGENTS.md, CLAUDE.md, custom
instructions, task prompts) become too long, stale, conflicting, or ignored by
the agent runtime.

**Source seeds:** SRC-005 (Ordivon AI onboarding), SRC-012 (Claude Code
CLAUDE.md)

**HAP objects affected:** HarnessTaskRequest, HarnessAdapterManifest
**OGAP concepts affected:** WorkClaim (claim vs actual behavior)
**EGB concepts affected:** Organizational accountability gap
**Ordivon controls affected:** New AI Context Check, Document Registry,
Current Truth

**Trigger conditions:** Multiple instruction sources compete. Instructions
exceed effective context length. Instructions not versioned or freshness-tracked.

**Boundary violated:** Agent must follow current instructions. Stale or
truncated instructions are not valid governance.

**Detection signals:**
- AGENTS.md last-updated date > 7 days old
- Multiple CLAUDE.md / Cursor rules / custom instructions with overlapping scope
- Instructions exceed model context window in practice
- Agent behavior contradicts documented instructions

**Required evidence:**
- New AI Context Check pass status
- Document Registry freshness dates
- Instruction conflict audit

**Gate response:** BLOCKED if AI Context Check fails. DEGRADED if
instructions stale but no conflicts.

**Review outcome:** Needs instruction refresh. Consolidate or expire
competing sources.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-004: "AI onboarding
docs must pass New AI Context Check at every phase boundary. Stale
instructions must be refreshed or explicitly marked historical."

**Future checker/schema/eval implication:** Instruction freshness checker.
Context-length-aware instruction consolidation.

**NO-GO condition:** Agent operating on truncated instructions with
missing boundary statements.

**Example safe phrasing:** "AGENTS.md last updated: 2026-05-02. New AI
Context Check: PASS. No competing instruction sources detected."

**Example unsafe phrasing:** "The agent probably read the instructions.
It has CLAUDE.md and AGENTS.md and the task prompt. It'll figure it out."

---

## Pattern 5: Protected Path Violation (AP-PPV)

**Short definition:** Agent modifies governance files, CI configuration,
credentials, policy definitions, schemas, registries, or runtime boundary
files without explicit scope authorization.

**Source seeds:** SRC-002 (HAP boundary), SRC-011 (Codex workspace
boundaries), SRC-012 (Claude Code workspace trust), SRC-014 (Copilot
agent firewall)

**HAP objects affected:** HarnessBoundaryDeclaration, HarnessTaskRequest,
HarnessExecutionReceipt
**OGAP concepts affected:** WorkClaim (changed_objects field)
**EGB concepts affected:** Systematic risk taxonomy gap
**Ordivon controls affected:** Architecture Checker, Protected Path detection,
Boundary Confirmation

**Trigger conditions:** Task prompt does not explicitly scope governance
file changes. Agent modifies files matching protected path patterns.

**Boundary violated:** Governance, CI, credential, policy, schema, registry,
and runtime boundary files are protected. Changes require explicit scope.

**Detection signals:**
- files_changed contains paths matching protected patterns (governance/,
  scripts/check_*, docs/governance/document-registry.jsonl,
  .github/workflows/, .env*, src/*/schemas/)
- Task request description does not mention governance file changes
- Architecture Checker flags forbidden patterns

**Required evidence:**
- Task request scope statement
- Execution receipt files_changed diff
- Architecture Checker result

**Gate response:** BLOCKED if protected path modified without scope.
REJECT if CI or credential file modified.

**Review outcome:** Needs scope verification. Was path change explicitly
authorized in task request?

**CandidateRule suggestion (NON-BINDING):** CR-ADP-005: "Protected paths
(governance, CI, credentials, policy, schema, registry, runtime boundary)
must be explicitly named in task scope before modification."

**Future checker/schema/eval implication:** Protected path registry.
Pre-commit hook for protected file changes.

**NO-GO condition:** Modification of .env, credential files, or CI
workflows without explicit phase authorization.

**Example safe phrasing:** "Task scope includes: governance file
modification (AGENTS.md, docs/ai/current-phase-boundaries.md). These
files are explicitly listed in the task request."

**Example unsafe phrasing:** "I also cleaned up some governance files
while I was in there. They're better now."

---

## Pattern 6: Shell Risk Escalation (AP-SHE)

**Short definition:** A task that starts as read-only or patch-proposal
escalates into shell execution without corresponding Stage Gate escalation
or boundary review.

**Source seeds:** SRC-002 (HAP risk levels), SRC-006 (OpenAI PF
capability threshold), SRC-008 (DeepMind FSF dangerous capability),
SRC-014 (Copilot agent firewall)

**HAP objects affected:** HarnessRiskProfile, HarnessTaskRequest,
HarnessBoundaryDeclaration, HarnessCapability
**OGAP concepts affected:** GovernanceDecision, capability thresholds
**EGB concepts affected:** Capability-scaled governance gap,
deployment authorization gap
**Ordivon controls affected:** Stage Gate, Risk Level, Boundary Confirmation,
NO-GO Ladder

**Trigger conditions:** Task starts at AP-R1 or AP-R2. Shell capability
requested or consumed without risk level escalation.

**Boundary violated:** Risk level must match capability consumption.
Shell execution requires AP-R3 classification and Stage Gate escalation.

**Detection signals:**
- Task request starts as read-only but consumes can_run_shell
- Risk profile at read_only but commands_run in receipt is non-empty
- shell_blocked=false in boundary but task originated as read-only
- Risk level not escalated before shell execution

**Required evidence:**
- Initial risk classification
- Boundary declaration at time of shell execution
- Stage Gate escalation record (if any)
- Execution receipt commands_run

**Gate response:** BLOCKED if shell executed without AP-R3 classification.
HOLD if shell capability present but blocked at boundary.

**Review outcome:** Needs escalation review. Shell execution requires
risk reclassification.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-006: "Shell execution
requires AP-R3 risk classification and explicit Stage Gate escalation
from the originating risk level."

**Future checker/schema/eval implication:** Risk level consistency checker.
Shell execution audit trail.

**NO-GO condition:** Shell execution from AP-R0 or AP-R1 origin.

**Example safe phrasing:** "Task originated at AP-R2 (workspace-write).
Shell execution requested. Risk escalated to AP-R3. Stage Gate: READY
after escalation review."

**Example unsafe phrasing:** "The task was just supposed to read files,
but running the tests requires shell. I ran them. All pass."

---

## Pattern 7: Credential Capability Confusion (AP-CRED)

**Short definition:** can_read_credentials or equivalent capability
declaration is mistaken for credential access permission, secret access,
or external-system authorization.

**Source seeds:** SRC-001 (OGAP-Z capability≠authorization), SRC-002
(HAP can_read_credentials), SRC-011 (Codex credential controls), SRC-013
(MCP authorization)

**HAP objects affected:** HarnessCapability (can_read_credentials),
HarnessBoundaryDeclaration (credential_access_blocked), HarnessRiskProfile
**OGAP concepts affected:** Capability-manifest, authority_request
**EGB concepts affected:** Capability-scaled governance gap
**Ordivon controls affected:** Boundary Confirmation, NO-GO Ladder,
Authority Impact

**Trigger conditions:** can_read_credentials=true in capability manifest
but credential_access_blocked is false or unset in boundary declaration.

**Boundary violated:** can_read_credentials is a technical capability
declaration, not authorization. Credential access requires explicit
boundary override and governance review.

**Detection signals:**
- can_read_credentials=true AND credential_access_blocked=false
- Task request mentions credential access but boundary blocks it
- Receipt claims "credentials accessed successfully" without boundary review
- Field name can_access_secrets reintroduced (forbidden — use can_read_credentials)

**Required evidence:**
- Capability manifest with can_read_credentials declaration
- Boundary declaration with credential_access_blocked status
- Authority statement clarifying capability≠access

**Gate response:** BLOCKED if credential_access_blocked=false without
governance review. BLOCKED if can_access_secrets field name detected.

**Review outcome:** Needs credential boundary confirmation.
can_read_credentials=true requires credential_access_blocked=true
unless explicitly reviewed.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-007: "can_read_credentials
describes technical capability only. Credential access is blocked by default.
Any credential access requires explicit boundary override and governance review."

**Future checker/schema/eval implication:** Credential boundary consistency
checker. Schema validator must reject can_access_secrets.

**NO-GO condition:** Credential access without governance review.
can_access_secrets field name reintroduced.

**Example safe phrasing:** "can_read_credentials=true (capability declaration
only). credential_access_blocked=true. No credentials accessed."

**Example unsafe phrasing:** "The harness can read credentials, so it can
access the .env file to get the API key."

---

## Pattern 8: External Side-effect Drift (AP-EXT)

**Short definition:** Agent uses browser, MCP, external API, network, or
remote tool surface without explicit authorization, or declares
can_call_external_api but boundary does not block it.

**Source seeds:** SRC-002 (HAP external_side_effect risk level), SRC-008
(DeepMind FSF mitigations), SRC-013 (MCP authorization / confused deputy)

**HAP objects affected:** HarnessCapability (can_call_external_api,
can_use_browser, can_use_mcp), HarnessBoundaryDeclaration
(external_api_blocked), HarnessRiskProfile
**OGAP concepts affected:** GovernanceDecision (BLOCKED for unauthorized
external calls)
**EGB concepts affected:** Systematic risk taxonomy gap
**Ordivon controls affected:** Boundary Confirmation, NO-GO Ladder,
Runtime Evidence Checker

**Trigger conditions:** can_call_external_api=true or can_use_mcp=true
without external_api_blocked=true in boundary. Agent makes network call
not in task scope.

**Boundary violated:** External API, browser, MCP, and network calls
require explicit boundary override and AP-R4 classification.

**Detection signals:**
- can_call_external_api=true AND external_api_blocked=false
- can_use_mcp=true without MCP tool allowlist
- Receipt shows network activity not in task scope
- MCP server connection without capability manifest

**Required evidence:**
- Boundary declaration with external_api_blocked status
- MCP tool allowlist (if MCP in use)
- Runtime evidence of network activity

**Gate response:** BLOCKED if external call made without AP-R4 classification.
HOLD if external capability present but blocked.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-008: "External API,
browser, MCP, and network calls require AP-R4 classification, explicit
boundary override, and tool allowlist. External calls are blocked by default."

**Future checker/schema/eval implication:** MCP tool allowlist validation.
External call audit trail.

**NO-GO condition:** External side-effect from AP-R0 through AP-R3 origin.

**Example safe phrasing:** "can_call_external_api=true (capability only).
external_api_blocked=true. No external calls authorized."

**Example unsafe phrasing:** "The MCP server exposed a fetch tool. I used
it to look up the latest docs. It was helpful."

---

## Pattern 9: Evidence Laundering (AP-EVL)

**Short definition:** Logs, screenshots, summaries, or agent-generated
receipts are treated as sufficient evidence without independent verification.

**Source seeds:** SRC-001 (OGAP-Z Evidence/Authority separation), SRC-008
(DeepMind FSF capability monitoring), SRC-009 (NIST RMF Measure function)

**HAP objects affected:** HarnessEvidenceBundle, HarnessExecutionReceipt,
HarnessResultSummary
**OGAP concepts affected:** EvidenceBundle (evidence_quality field)
**EGB concepts affected:** External audit trail gap
**Ordivon controls affected:** Runtime Evidence Checker, Receipt Integrity,
Coverage Governance

**Trigger conditions:** evidence_quality=self_reported. No machine_verified
or human_reviewed quality level. Receipt claims "all checks passed" but
evidence bundle has gaps.

**Boundary violated:** Evidence must be verifiable. Self-reported evidence
is not sufficient for READY status.

**Detection signals:**
- evidence_quality=self_reported in all bundles
- evidence_bundle.gaps is empty but receipt has skipped_checks
- No machine_verified or human_reviewed evidence_quality
- Receipt claims completion without verification evidence

**Required evidence:**
- Evidence bundle with evidence_quality field
- Machine-verified or human-reviewed evidence for critical claims
- Gaps declared when evidence missing

**Gate response:** BLOCKED if critical claims have only self_reported
evidence. DEGRADED if evidence has gaps but gaps are declared.

**Review outcome:** Needs evidence quality upgrade. Self-reported
evidence requires machine verification for READY.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-009: "Evidence for
Stage Gate decisions must reach at least machine_verified quality.
Self-reported evidence is not sufficient for READY."

**Future checker/schema/eval implication:** Evidence quality linter.
Receipt-to-evidence consistency checker.

**NO-GO condition:** READY based solely on self-reported evidence.

**Example safe phrasing:** "Evidence quality: machine_verified. Gaps
declared: 2 items (integration tests, load tests)."
**Example unsafe phrasing:** "I ran the tests and they all passed. Here's
the terminal output as proof."

---

## Pattern 10: READY Overclaim (AP-RDY)

**Short definition:** READY means the artifact validates or is prepared,
but is mistaken for execution authorization, production readiness, merge
approval, or deployment permission.

**Source seeds:** SRC-001 (OGAP-Z READY≠authorization), SRC-002 (HAP
READY≠execution authorization)

**HAP objects affected:** HarnessResultSummary (status=READY)
**OGAP concepts affected:** GovernanceDecision (READY semantics)
**EGB concepts affected:** Deployment authorization gap
**Ordivon controls affected:** Boundary Confirmation, Authority Impact,
Stage Gate

**Trigger conditions:** Status=READY without authority_statement
disclaiming execution authorization. Agent or human treats READY as
authorization to proceed.

**Boundary violated:** READY means evidence is adequate for review.
It does not authorize execution, merge, deployment, or production.

**Detection signals:**
- READY appears without "does not authorize execution" disclaimer
- Task claimed "complete" with READY status
- Merge or deploy action triggered by READY without separate authorization
- READY treated as equivalent to APPROVED

**Required evidence:**
- Result summary with authority_statement (denial)
- Separate authorization record (not READY) for execution
- Stage Gate confirmation

**Gate response:** BLOCKED if READY used as authorization claim.
DEGRADED if disclaimer present but weak.

**Review outcome:** READY is evidence, not approval. Separate
authorization required for execution.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-010: "READY status
must include an explicit statement that READY does not authorize
execution, merge, deployment, or production."

**Future checker/schema/eval implication:** READY disclaimer validator.
Authorization gate separate from READY gate.

**NO-GO condition:** READY treated as execution authorization.

**Example safe phrasing:** "Status: READY. READY means selected checks
passed. It does not authorize execution, merge, deployment, or
production. Human reviewer is still responsible."

**Example unsafe phrasing:** "All checks pass — READY. This PR is
approved for merge."

---

## Pattern 11: Review Bypass (AP-REV)

**Short definition:** Agent produces changes and moves toward merge,
deployment, or action without completing required review steps.

**Source seeds:** SRC-005 (Ordivon Review Record), SRC-009 (NIST RMF
Manage function), SRC-010 (ISO 42001 auditability)

**HAP objects affected:** HarnessReviewRecord, HarnessResultSummary
**OGAP concepts affected:** GovernanceDecision
**EGB concepts affected:** Organizational accountability gap, external
audit trail gap
**Ordivon controls affected:** Review Record, Stage Gate, Closure Predicate

**Trigger conditions:** Changes produced, but no Review Record exists.
requires_review_for items not reviewed before READY claim.

**Boundary violated:** Actions in requires_review_for must have review
records before proceeding.

**Detection signals:**
- requires_review_for is non-empty but Review Record is empty
- READY claimed without review completion
- Review Record verdict is missing or pending
- Merge/deploy action triggered without review gate

**Required evidence:**
- Review Record with verdict (approved_as_evidence/needs_rework/rejected)
- Review completion timestamp
- Reviewer identity

**Gate response:** BLOCKED if requires_review_for non-empty and no
Review Record. HOLD if review pending.

**Review outcome:** Review required before gate passage.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-011: "Actions in
requires_review_for must have completed Review Records with non-pending
verdicts before Stage Gate READY."

**Future checker/schema/eval implication:** Review completeness checker.
Merge/deploy gate with mandatory review check.

**NO-GO condition:** Merge/deploy without required review.

**Example safe phrasing:** "Review Record: 2 items, both approved_as_evidence.
Reviewer: domain-owner. Timestamp: 2026-05-02."

**Example unsafe phrasing:** "The reviewer will get to it. The changes
are straightforward. Let's merge."

---

## Pattern 12: Current Truth Drift (AP-CTD)

**Short definition:** Code, docs, receipts, registries, AI onboarding,
and actual repo state diverge over time. What docs say ≠ what code does ≠
what registry lists ≠ what AI reads.

**Source seeds:** SRC-003 (EGB-1 gap analysis), SRC-004 (Verification
Debt Ledger), SRC-005 (Ordivon Document Registry), SRC-009 (NIST RMF
Map function), SRC-010 (ISO 42001 documentation)

**HAP objects affected:** HarnessEvidenceBundle, HarnessExecutionReceipt
**OGAP concepts affected:** WorkClaim (claim vs reality)
**EGB concepts affected:** Organizational accountability gap, external
audit trail gap
**Ordivon controls affected:** Document Registry, New AI Context Check,
Current Truth, Receipt Integrity

**Trigger conditions:** Docs updated without registry sync. Registry
entries stale. AI onboarding does not match current phase status.
Receipt claims differ from verification results.

**Boundary violated:** Current truth must be single-source. Docs,
registry, onboarding, and repo state must be consistent.

**Detection signals:**
- Document Registry freshness dates > stale_after_days
- AGENTS.md phase status disagrees with current-phase-boundaries.md
- Receipt claims "12/12 PASS" but pr-fast actually shows 11/12
- New AI Context Check fails

**Required evidence:**
- Document Registry freshness check
- Cross-reference: AGENTS.md ↔ boundaries.md ↔ registry ↔ actual repo
- New AI Context Check pass/fail
- Receipt Integrity checker result

**Gate response:** BLOCKED if critical docs stale or contradictory.
DEGRADED if non-critical docs stale.

**Review outcome:** Needs doc sync. Stale docs refreshed or expired.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-012: "Current truth
sources (AGENTS.md, boundaries.md, document registry, AI onboarding)
must be consistent at every phase boundary. Cross-reference check
required before CLOSED."

**Future checker/schema/eval implication:** Cross-reference consistency
checker. Automated current truth sync verification.

**NO-GO condition:** Phase CLOSED with contradictory truth sources.

**Example safe phrasing:** "Current truth check: AGENTS.md ↔
boundaries.md ↔ registry: consistent. All freshness dates within
stale_after_days."

**Example unsafe phrasing:** "The docs are mostly right. A few things
changed in the last phase. The agent will figure it out from the code."

---

## Pattern 13: Scope Creep / Opportunistic Refactor (AP-SCP)

**Short definition:** Agent expands from requested task into adjacent
cleanup, architecture changes, unrelated refactors, or style churn
without explicit scope authorization.

**Source seeds:** SRC-002 (HAP task request scope), SRC-012 (Claude Code
workspace boundaries)

**HAP objects affected:** HarnessTaskRequest, HarnessTaskPlan,
HarnessExecutionReceipt
**OGAP concepts affected:** WorkClaim (changed_objects vs claimed scope)
**EGB concepts affected:** Systematic risk taxonomy gap
**Ordivon controls affected:** Boundary Confirmation, Execution Receipt

**Trigger conditions:** files_changed contains files outside task
description scope. Task plan steps include unrequested refactors.
Changed objects count >> expected scope.

**Boundary violated:** Agent must operate within declared task scope.
Scope expansion requires explicit request.

**Detection signals:**
- files_changed contains files not in requested_capabilities scope
- Task plan includes "while I'm here" or "also cleaned up" steps
- Changed files count exceeds expected scope by >50%
- Files changed include style-only modifications in unrelated modules

**Required evidence:**
- Task request description vs execution receipt files_changed diff
- Task plan vs actual execution diff
- Scope creep detection: unexpected file changes

**Gate response:** DEGRADED if scope expanded without authorization.
BLOCKED if scope expansion touches protected paths.

**Review outcome:** Needs scope verification. Were extra changes
explicitly authorized?

**CandidateRule suggestion (NON-BINDING):** CR-ADP-013: "Agent must
operate within declared task scope. Changes outside scope require
explicit authorization or separate task request."

**Future checker/schema/eval implication:** Scope-to-execution diff
checker. Task scope linter.

**NO-GO condition:** Unauthorized scope expansion into protected paths.

**Example safe phrasing:** "Task scope: refactor validator.py.
Files changed: src/validator.py (2 files). Scope match: 100%."

**Example unsafe phrasing:** "I refactored the validator, and while I
was there I also cleaned up the imports in 8 other files and renamed
some variables for consistency."

---

## Pattern 14: Test Omission / Selective Verification (AP-TST)

**Short definition:** Agent claims completion but runs only easy,
fast, or cherry-picked tests. Skips integration, edge-case, regression,
or governance tests without declaring them.

**Source seeds:** SRC-004 (Verification Debt Ledger — skipped_verification
category), SRC-009 (NIST RMF Measure function)

**HAP objects affected:** HarnessExecutionReceipt (passed_checks,
failed_checks, skipped_checks), HarnessEvidenceBundle
**OGAP concepts affected:** CoverageReport (claimed_universe vs actual)
**EGB concepts affected:** Organizational accountability gap
**Ordivon controls affected:** Coverage Governance, Verification Baseline,
Receipt Integrity

**Trigger conditions:** skipped_checks declared but not justified.
Passed check count high but coverage narrow. Only fast/smoke tests run.

**Boundary violated:** Test scope must match claimed coverage universe.
Skipped tests must be declared with justification.

**Detection signals:**
- Skipped checks not declared in evidence bundle gaps
- Coverage report claimed_universe >> actual test scope
- Only unit tests run; integration/e2e/gov tests skipped
- Test pass rate 100% but coverage narrow

**Required evidence:**
- Execution receipt with complete passed/failed/skipped lists
- Evidence bundle gaps declaration
- Coverage report matching actual test scope
- Pr-fast baseline or equivalent verification gate

**Gate response:** BLOCKED if skipped checks undeclared. DEGRADED if
coverage narrow but declared.

**Review outcome:** Needs coverage verification. Skipped tests must be
declared or run.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-014: "All skipped
verification must be declared in evidence bundle gaps with justification.
Selective verification without declaration is evidence laundering."

**Future checker/schema/eval implication:** Skipped-to-declared
consistency checker. Coverage-vs-actual scope diff.

**NO-GO condition:** READY claimed with undeclared skipped verification.

**Example safe phrasing:** "Tests run: 1256 passed, 0 failed, 1 skipped
(DOC-WIKI-FLAKY-001, known debt). Coverage: unit + governance + product."

**Example unsafe phrasing:** "All tests pass. (Ran the fast ones. The
integration tests take too long. They're probably fine.)"

---

## Pattern 15: Baseline Debt Masking (AP-BDM)

**Short definition:** Pre-existing failures are used to hide new
regressions. New failures are misclassified as baseline. Phase claims
"no new failures" while debt accumulates.

**Source seeds:** SRC-003 (EGB-1 gap analysis), SRC-004 (Verification
Debt Ledger), SRC-005 (Ordivon baseline discipline), SRC-010 (ISO 42001
continual improvement)

**HAP objects affected:** HarnessResultSummary (status, warnings),
HarnessEvidenceBundle (gaps)
**OGAP concepts affected:** DebtDeclaration
**EGB concepts affected:** External audit trail gap
**Ordivon controls affected:** Verification Debt Ledger, Baseline
Integrity, Receipt Integrity

**Trigger conditions:** Baseline known failures used to absorb new
regressions. New failures attributed to pre-existing debt without
verification. Debt ledger entries grow without triage.

**Boundary violated:** Each failure must be classified as new or
pre-existing. Pre-existing classification requires evidence that
failure existed before current phase.

**Detection signals:**
- "Pre-existing" claim without baseline comparison evidence
- Debt ledger open entries growing without triage
- New phase claims "no new failures" but test results differ from baseline
- Failure count unchanged but failure set rotated (old fixed, new appeared)

**Required evidence:**
- Baseline test results from before phase start
- Current test results with diff
- Each failure classified: new vs pre-existing with evidence
- Debt ledger entry for each new failure

**Gate response:** BLOCKED if new failures unregistered.
DEGRADED if baseline growth unexplained.

**Review outcome:** Needs failure classification audit. Every
failure must have a classification record.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-015: "New test
failures must be classified as new or pre-existing with baseline
comparison evidence. Pre-existing failures must be registered in
the verification debt ledger."

**Future checker/schema/eval implication:** Baseline diff checker.
Failure classification audit trail.

**NO-GO condition:** New regression masked as pre-existing.

**Example safe phrasing:** "10 product test failures: 10 pre-existing
(PV-N8 build artifact, wedge audit token false positive — verified
against baseline 7226e56). 0 new failures."

**Example unsafe phrasing:** "Some tests fail but they always failed.
Nothing new here. Moving on."

---

## Pattern 16: CandidateRule Premature Promotion (AP-CRP)

**Short definition:** A CandidateRule (advisory observation) is treated
as binding Policy before meeting promotion criteria: ≥2 weeks observation,
≥3 real interceptions, documented bypass conditions, stakeholder sign-off.

**Source seeds:** SRC-005 (Ordivon CandidateRule≠Policy doctrine)

**HAP objects affected:** HarnessReviewRecord (candidate_rule_suggestions)
**OGAP concepts affected:** GovernanceDecision (cannot be based on
CandidateRule alone)
**EGB concepts affected:** Deployment authorization gap
**Ordivon controls affected:** CandidateRule (advisory), Policy (binding),
Stage Gate

**Trigger conditions:** CandidateRule used as blocking rule. Merge/deploy
blocked by CandidateRule without Policy activation. Agent treats
CR-XXX-001 as binding.

**Boundary violated:** CandidateRule is advisory only. Promotion to
Policy requires 4 criteria.

**Detection signals:**
- CandidateRule cited as reason for BLOCKED
- "CR-XXX-001 says this should be blocked" without Policy activation
- CandidateRule used in gate decision without promotion record
- Agent treats CR-* as equivalent to Policy

**Required evidence:**
- CandidateRule promotion status (advisory vs promoted)
- Policy activation record (if promoted)
- Gate decision rationale (must cite Policy, not CandidateRule)

**Gate response:** DEGRADED if CandidateRule used in decision without
promotion. Override if advisory-only.

**Review outcome:** CandidateRule is advisory. Not a valid gate
blocker unless promoted to Policy.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-016: "CandidateRule
is advisory only. Promotion to Policy requires: ≥2 weeks observation,
≥3 real interceptions, documented bypass conditions, stakeholder sign-off."

**Future checker/schema/eval implication:** CandidateRule-vs-Policy
gate blocker. Promotion criteria tracker.

**NO-GO condition:** CandidateRule used as blocking gate without
Policy activation.

**Example safe phrasing:** "CR-ADP-001 suggests capability declarations
should include authority disclaimers. This is advisory — not blocking.
For reference only."

**Example unsafe phrasing:** "CR-ADP-001 says capability declarations
need disclaimers. This PR doesn't have them. Blocked."

---

## Pattern 17: External Benchmark Overclaim (AP-EBO)

**Short definition:** References to OpenAI, Anthropic, DeepMind, NIST,
or ISO frameworks are misrepresented as compliance, certification,
endorsement, equivalence, or partnership.

**Source seeds:** SRC-003 (EGB-1 safe-language clause), SRC-006 through
SRC-010 (all external benchmarks)

**HAP objects affected:** HarnessAdapterManifest (if external refs in
manifest metadata)
**OGAP concepts affected:** All objects (any could contain unsafe claims)
**EGB concepts affected:** All EGB-1 safe-language boundaries
**Ordivon controls affected:** Public Wedge Audit, Overclaim Scan,
Boundary Confirmation

**Trigger conditions:** External framework name appears without
safe-language disclaimer. "Compliant with", "Certified by", "Endorsed
by", "Equivalent to", "Partnered with" language detected.

**Boundary violated:** External frameworks are benchmarks for internal
comparison only. No compliance/certification/endorsement/partnership/
equivalence is claimed.

**Detection signals:**
- "compliant", "certified", "endorsed", "partnered", "equivalent",
  "official alignment" near external org names
- External framework cited as authority for Ordivon decision
- Absence of safe-language disclaimer in docs referencing external frameworks

**Required evidence:**
- Safe-language disclaimer presence in every doc referencing external frameworks
- Overclaim scan result
- Public Wedge Audit result

**Gate response:** BLOCKED if unsafe compliance/endorsement claim detected.
DEGRADED if safe-language present but weak.

**Review outcome:** Needs safe-language audit. All external references
require disclaimer.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-017: "All references
to external frameworks must include safe-language disclaimer stating they
are internal comparison benchmarks only, not compliance/certification/
endorsement claims."

**Future checker/schema/eval implication:** Safe-language lint rule.
Overclaim scan automation.

**NO-GO condition:** Public claim of compliance/certification/endorsement.

**Example safe phrasing:** "ADP-1 references OpenAI PF, Anthropic RSP,
and NIST AI RMF as external benchmarks for internal comparison and gap
analysis only. This does not imply compliance, certification, or endorsement."

**Example unsafe phrasing:** "Our governance is based on OpenAI's
Preparedness Framework and NIST AI RMF."

---

## Pattern 18: MCP Tool Injection / Confused Deputy (AP-MCP)

**Short definition:** MCP or remote tool surfaces introduce tool
descriptions, prompts, or proxy behavior that cause unauthorized actions
by the agent. The agent is tricked or confused into executing actions
outside its scope.

**Source seeds:** SRC-013 (MCP authorization, confused deputy risks)

**HAP objects affected:** HarnessCapability (can_use_mcp),
HarnessBoundaryDeclaration, HarnessTaskRequest
**OGAP concepts affected:** Capability-manifest (MCP server surface)
**EGB concepts affected:** Systematic risk taxonomy gap,
capability-scaled governance gap
**Ordivon controls affected:** Boundary Confirmation, Architecture
Checker, Runtime Evidence Checker

**Trigger conditions:** MCP server connected without tool allowlist.
Tool description contains prompt injection. Agent follows MCP tool
instruction without scope check.

**Boundary violated:** MCP tools must have explicit allowlists. Tool
descriptions are untrusted input. Agent must not follow tool
instructions that exceed task scope.

**Detection signals:**
- can_use_mcp=true without tool allowlist
- MCP server tool description contains action-oriented language
  ("execute", "deploy", "delete", "authorize")
- Agent receipt shows actions triggered by MCP tool description
- MCP server connected without capability manifest

**Required evidence:**
- MCP tool allowlist
- Tool description audit (no prompt injection)
- Capability manifest for MCP server

**Gate response:** BLOCKED if MCP server connected without allowlist.
HOLD if tool descriptions contain potentially dangerous instructions.

**Review outcome:** Needs MCP tool audit. All tools must be allowlisted.
Tool descriptions must be treated as untrusted.

**CandidateRule suggestion (NON-BINDING):** CR-ADP-018: "MCP servers
require tool allowlists. Tool descriptions are untrusted input. Agent
must not execute tool instructions that exceed task scope."

**Future checker/schema/eval implication:** MCP tool allowlist validator.
Tool description injection scanner.

**NO-GO condition:** MCP tool execution without allowlist or capability
manifest.

**Example safe phrasing:** "MCP server connected. Tool allowlist: 3 tools
(read_file, search, grep). All tool descriptions audited: no injection
detected."

**Example unsafe phrasing:** "The MCP server suggested I run 'deploy.sh'.
It seemed like a good idea so I did it."

---

## Pattern Frequency by Risk Level

| AP Risk Level | Pattern Count | Patterns |
|--------------|--------------|----------|
| AP-R0 (taxonomy) | 0 | (none — ADP-1 scope) |
| AP-R1 (read-only) | 3 | AP-CTD, AP-EBO, AP-INS |
| AP-R2 (workspace-write) | 4 | AP-SCP, AP-PPV, AP-DRF, AP-FAT |
| AP-R3 (shell) | 2 | AP-SHE, AP-TST |
| AP-R4 (credential/external) | 6 | AP-COL, AP-CRED, AP-EXT, AP-EVL, AP-MCP, AP-RDY |
| AP-R5 (live/irreversible) | 3 | AP-REV, AP-BDM, AP-CRP |

> Note: Patterns may span multiple risk levels. Classification above
> shows the minimum risk level where the pattern becomes critical.

## Ordivon Control Coverage

| Ordivon Control | Patterns Mapping |
|-----------------|-----------------|
| Boundary Confirmation | 1, 2, 3, 5, 6, 7, 8, 10, 13, 17, 18 |
| Stage Gate | 1, 2, 6, 10, 11, 16 |
| NO-GO Ladder | 1, 3, 6, 7, 8 |
| Review Record | 2, 11 |
| CandidateRule (advisory) | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 |
| Verification Debt Ledger | 14, 15 |
| Document Registry | 4, 12 |
| New AI Context Check | 4, 12 |
| Architecture Checker | 3, 5 |
| Runtime Evidence Checker | 8, 9 |
| Receipt Integrity | 9, 12, 14 |
| Coverage Governance | 9, 14 |
| Public Wedge Audit | 17 |

*Phase: ADP-1 | Pattern identification is not policy activation. All CandidateRule suggestions are NON-BINDING.*
