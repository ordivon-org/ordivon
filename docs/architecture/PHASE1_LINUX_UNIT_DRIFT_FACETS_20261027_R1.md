# Phase 1: Linux installed unit drift and agent-friendly role labels

This file complements existing exact-Git exhaustive_coverage.py and the PR #993 source/installed report, without creating another registry, new Owner, LEGO or physical rename.

## Evidence scope

Reused independent Host/Runtime peer systemd classification across 114 unit names; specifically rechecked 12 byte-mismatched unit fragments. On three exact accessible source cuts (see machine JSON), every one of the 12 Git source byte sequences is unchanged, while all corresponding installed files under /etc/systemd/system are byte-different.

Seven units differ in directive-key multiplicity; five have the same directive-key counts but still differ bytewise. Secret-bearing directive VALUES, ExecStart arguments, credential content, drop-in override files, effective merged units and consumers are not in this evidence. A byte mismatch does not establish a bug or an authorized fix.

## Distinctions for Agent-facing names

- network.finance.egress is an installed network egress unit, NOT the Capital domain economic decision engine.
- network.x-api.egress is the actual X API transport profile in the source context; the historical x-reality path is NOT an XRay protocol claim.
- workflow.agent.temporal-worker is a Harness-scoped process installation, NOT a Research study authority or task semantic owner.
- agent.automation.mcp differs in environment/credential directive counts; values and appropriateness were deliberately not inspected.
- runtime.lifecycle and timer may have deliberate provider-specific realization; do not rewrite based on pathname equivalence.

Source identity is exact Git SourceCut + Git path and blob; installed identity is node + installed unit fragment SHA-256. Display aliases are navigational only, and unresolved semantic/consumer/authorization standing is UNKNOWN.

Machine-readable itemized 12-row evidence: evidence/PHASE1_LINUX_UNIT_DRIFT_FACETS_20261027_R1.json.

No runtime service was restarted, moved, or reconfigured. Installation revisions and consumer-qualified source relations remain Phase 1 frontiers.
