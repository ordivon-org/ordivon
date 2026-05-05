# Ordivon Completeness Red-Team Audit — 2026-05-05

Status: **CLOSED** | Date: 2026-05-05 | Phase: Completeness-Redteam
Tags: `completeness`, `redteam`, `checker-ecosystem`, `dg`, `alpha`, `pgi`, `egb-2`
Authority: `supporting_evidence` | AI Read Priority: 1

## Summary

This audit checks whether the current Ordivon bodies are operationally closed:
Core Governance Backbone, Checker Ecosystem, DG/Registry System, Alpha Trust
Flywheel, PGI Philosophical Governance, EGB-2 Engineering Governance, and the
Application/Pack/Adapter boundary.

Result: the system is substantively formed and baseline-verifiable, but not
complete in the strong sense. It has a working governance backbone, registry
coverage, red-team fixtures, and shadow-first external governance surfaces. The
main remaining risk is not missing architecture; it is drift between canonical
and deprecated surfaces, false-comfort evidence language, and diagnostic metrics
being misread as approval or project scoring.

This receipt is evidence only. It does not authorize merge, release,
deployment, publication, trading, policy activation, or external action.

## Current Fact Baseline

Observed before repair:

- `git status --short`: clean.
- `uv run python scripts/run_baseline.py --read-only`: READY, 26/26 hard gates.
- `uv run python scripts/check_document_registry.py`: PASS, 213 registered docs.
- `python scripts/check_artifact_registry.py`: FAIL, 643 registered artifacts,
  1 ungoverned symlink: `scripts/run_verification_baseline.py`.
- `uv run python scripts/run_alpha_casebook.py`: 4/4 cases matched expected
  trust signals.
- `python scripts/report_governance_delivery_metrics.py --json`:
  `missing_evidence_count=15`, `degraded_count=96`, `blocked_count=493`,
  `open_debt_count=3`, `checker_shadow_count=3`.

Repair applied:

- Registered `scripts/run_verification_baseline.py` as a deprecated compatibility
  symlink artifact.
- Preserved `scripts/run_baseline.py` as the canonical current baseline runner.
- Added red-team regression coverage for missing local test command evidence.
- Added EGB-2 red-team regression coverage for SLSA-level overclaim,
  ready-for-merge OEP language, and release-approval ownership wording.

Observed after repair:

- `python scripts/check_artifact_registry.py`: PASS, 644 registered artifacts,
  0 ungoverned, 0 class errors.
- `uv run python scripts/check_document_registry.py`: PASS, 214 registered docs,
  0 completeness violations.
- `python checkers/current-truth/run.py`: PASS.
- `uv run python scripts/run_baseline.py --read-only`: READY, 26/26 hard gates.
- Alpha/Verify targeted tests: 267 passed.
- EGB-2 + PGI + checker maturity targeted tests: 138 passed.
- Delivery metrics remained diagnostic-only:
  `missing_evidence_count=15`, `degraded_count=97`, `blocked_count=495`,
  `open_debt_count=3`, `checker_shadow_count=3`, `registry_drift_count=0`.

## Seven-System Review

| System | Completeness judgment | Red-team conclusion |
|---|---|---|
| Core Governance Backbone | Operational, not final. `run_baseline.py`, registries, reconciler, handoff, and current-truth checks exist. | Main risk is old runner/document references being mistaken for canonical current truth. |
| Checker Ecosystem | Operational. 36 checkers exist; 26 are hard in read-only baseline and EGB/PGI additions remain escalation/shadow-first. | Shadow checkers must not be promoted without owner review and red-team evidence. |
| DG / Registry System | Strong but drift-prone. Document registry passed; artifact registry caught an unregistered symlink. | Registry completeness can fail even when read-only baseline is green; artifact registry must remain a first-class pre-close gate. |
| Alpha Trust Flywheel | Seeded and useful, not broad enough. Alpha-0 has casebook runner and trust-laundering regressions. | Casebook now catches authorization laundering, CandidateRule/Policy confusion, missing receipts, safe DEGRADED, and local-test false comfort. More stale-doc and diff/test-schema cases remain. |
| PGI Philosophical Governance | Deeply scaffolded with validators and closure receipts. | Main risk is philosophical authority laundering: values, reflection, or self-models must not become unquestionable policy or action permission. |
| EGB-2 Engineering Governance | Core backbone implemented shadow-first. | Source/OEP/ownership checkers now cover additional overclaim and authorization-language false-comfort cases; still not eligible for hard-gate promotion. |
| Application / Pack / Adapter Boundary | Intentionally mixed. Ordivon Verify self-governance covers docs/tests/scripts/domains/src/checkers; apps/packs/adapters are governed targets, not fully self-governed surfaces yet. | This is acceptable only if kept explicit. Future work should classify app/pack/adapter files as register-now, observe-as-target, or deferred-with-rationale. |

## Findings

### P0 — Registry Drift Via Deprecated Symlink

`scripts/run_verification_baseline.py` is a tracked symlink to
`_deprecated_run_verification_baseline.py`. It was not present in
`artifact-registry.jsonl`, so artifact registry failed while read-only baseline
still passed.

Disposition: fixed by registering the symlink as a deprecated compatibility
artifact. The canonical runner remains `scripts/run_baseline.py`.

### P1 — False-Comfort Test Evidence

Alpha receipts could say "Tests passed locally" without naming a command. This
is weaker than the Alpha-0 trust objective because it lets confidence replace
reproducible evidence.

Disposition: receipt scanner now blocks the explicit local-test success phrase
when no nearby command evidence exists. This is intentionally narrow to avoid
breaking older minimal fixtures that only record tabular results.

### P1 — EGB-2 Overclaim Surface

EGB-2 already blocked common compliance/certification/endorsement language, but
the regression set needed explicit examples for SLSA-level claims, OEP
ready-for-merge phrasing, and ownership release-approval wording.

Disposition: tests added. EGB-2 checkers remain escalation/shadow-first.

### P1 — Current Truth Numerics

Some runtime receipts record historical registry counts. The current source of
truth is the live registry checker output, not stale numeric prose in older
receipts. Future receipts should distinguish "observed at closure" from
"current registry count".

Disposition: this audit records the current baseline and repair. No historical
receipt is treated as action authority.

### P2 — Trust Budget Interpretation

`blocked_count`, `degraded_count`, and `missing_evidence_count` are diagnostic
counts, not a score and not a release decision. They indicate where evidence is
missing or historical receipts contain blocked patterns.

Disposition: keep as repair backlog input only.

## Backlog

1. Expand Alpha casebook to stale current-truth citations, structured test
   evidence, diff evidence, and review completeness.
2. Add a checker ecosystem audit report that crosswalks checker registry,
   CHECKER.md metadata, maturity ledger, read-only side effects, and profile.
3. Create an application-boundary classification report for `apps/`, `packs/`,
   `adapters/`, `knowledge/`, and `skills/`.
4. Add a current-truth numeric drift checker for runtime receipts that claim
   live counts without "observed at closure" language.
5. Keep EGB-2 source/OEP/ownership checkers in escalation until explicit owner
   review and red-team promotion evidence exist.

## Boundary

This audit does not publish a standard, claim compliance, certify security,
activate policy, promote checkers, run agents, execute external tools, refresh
tokens, merge, release, deploy, trade, or authorize any external action.
