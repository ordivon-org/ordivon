---
schema_version: 1
id: harness.verification
title: Harness Verification
type: reference
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - builder
  - operator
  - researcher
  - agent
updated: 2026-09-18
summary: Claim classes, evidence strength, historical evidence interpretation and current release gates.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.status
  - harness.compatibility
  - harness.releases
---
# Harness Verification

## Evidence classes

| Evidence | Proves | Does not prove |
| --- | --- | --- |
| deterministic unit/integration test | current source invariant under controlled inputs | live Provider or Runtime behavior |
| frozen fixture | a named failure trajectory and expected repair | arbitrary repositories or Providers |
| live receipt | one real journey on an exact dependency graph | current `main` after later changes |
| immutable research projection/result | one bounded owner/research observation bound to a tested implementation lineage | whole-current-product certification after later source changes |
| historical closeout/report | design evolution and prior decisions | current implementation correctness |

No implementation-bound evidence should be cited without its Harness/implementation revision and dependency context.

## Current portable gate

The current release gate includes:

- compile and Ruff;
- complete deterministic suite with `ResourceWarning` as error;
- exact dependency and lockfile checks;
- Host import-boundary tests;
- stable API contract tests;
- semantic-history validation tests;
- documentation and evidence-index validation;
- wheel metadata validation, isolated installation, CLI smoke testing and dependency audit;
- bounded atomic Event-batch replay/rollback tests and the deterministic scale smoke.
- Agent Automation pre-switch Browser Security qualification after admission closure and workflow drain, using same-carrier LKG comparisons across the Browserless pool. Drift is localization evidence only; the qualification never claims provider-authoritative root cause.

## Evidence index and revision binding

`evidence/index.json` classifies every repository `evidence/*.json` object and `scripts/check_evidence.py` enforces exact file correspondence, revision binding and `verified` currentness.

Two revision-binding modes are supported:

- **embedded** — the default legacy receipt mode. The payload itself must carry the exact implementation/source revision recorded by the index.
- **index-creation-lineage** — explicit opt-in for immutable research projections/results whose frozen payload shape does not carry the legacy receipt revision field. The index revision must be an ancestor of the evidence file's unique Git creation commit, no invalidating implementation path may change before evidence creation, and the evidence bytes must remain identical to the creation commit. Recognized embedded tested-revision hints, when present, must agree with the index.

The second mode does not make the index semantic truth owner. It binds repository provenance/currentness without rewriting frozen evidence bytes.

A `verified` entry is current only while no later invalidating implementation path has changed after its bound revision. Once that condition fails, the evidence remains useful historical evidence but must be demoted rather than silently certifying current code.

## P0 scale acceptance

The full P0 persistence closeout uses:

```bash
uv run python scripts/harness_p0_scale_acceptance.py \
  --runs 1000 \
  --events-per-run 100 \
  --batch-size 99 \
  --output evidence/hho-p0-scale-1000x100-<revision>.json
```

The receipt must bind the exact implementation revision and prove 1,000 Runs, 100,000 Events, a healthy full-history Doctor after reopen, exact object-reference/file agreement, and sampled current-Run inspection below the recorded one-second gate. Thresholds and machine measurements remain in the receipt rather than becoming timeless prose.

## Historical live receipts

`evidence/index.json` classifies repository evidence. Existing Codex, Hermes, DeepSeek, Runtime and replacement/recovery receipts are historical because they bind commits before current `main`. They remain valuable evidence for those trajectories but must not be described as certification of current code.

## Current live acceptance

A current release-changing Provider, Runtime, recovery or completion path should produce a new receipt containing:

- Harness Git commit and package version;
- Protocol revision, and Host/caller revision only when that caller participates in the exercised graph;
- Runtime identity and Tool catalog digest when Runtime Tools participate;
- Provider adapter/model identity;
- caller reference and Harness Run identity;
- relevant Tool Step and Provider Call identities;
- final status and explicit unknowns;
- receipt integrity digest;
- limitations.

The canonical command is `scripts/local-acceptance run` on an owner-trusted acceptance environment.

A deletion-only recovery change needs evidence for the capability that actually remains. If the retired path has no current writer/consumer and retained-state census finds no instances, do not recreate the obsolete writer merely to manufacture a "live" trajectory. Bind the exact pre-evidence implementation revision, prove writer/consumer and retained-state absence with bounded read-only evidence, regress the surviving Recovery/UNKNOWN path, and run the normal portable gate. Such a deletion receipt proves the scoped retirement; it does not generalize absence beyond the observed authorities.

## Claim discipline

Use these terms consistently:

- **operational**: repeatedly exercised in the supported graph;
- **experimental**: implemented and tested, but public behavior may still change;
- **verified in pinned graph**: deterministic/live evidence exists for named revisions;
- **historical**: evidence exists only for an earlier graph;
- **unsupported**: no contract or safe path exists.

Tests and evidence verify bounded behavior. They do not turn Runtime success into semantic Task completion or remove Provider/domain uncertainty.

## Browser Security release qualification

Agent Automation activation uses the immutable candidate's own `browser_security_pool_runner.py` and `browser_security_witness_source.py` after new admission is closed and the production Temporal task queue is drained, but before the worker stops and before `/opt/ordivon/agent-automation/current` changes. The runner verifies Security-v2 LKG bundle digests, observes the current Browserless pool through neutral/read-only probes, and delegates canonicalization/classification to Security-v2.

The release owner admits only `NO_OBSERVED_DRIFT` as an automatic PASS. `DETECTOR_DRIFT`, `GLOBAL_DRIFT`, `CARRIER_LOCAL_DRIFT`, `MIXED_DRIFT`, malformed receipts, baseline digest failure, busy carriers, or collector failure produce HOLD. A private `0600` qualification receipt binds the candidate commit, Security revision, pool identity/index digest, classification standing, and the explicit facts that no provider challenge was visited and no provider SEND was attempted.

This is a **pre-switch currentness gate**, not proof of the behavioral effect of a Browserless/Chromium launch change that has not yet been deployed. Browser-substrate mutation still requires a separate candidate/canary and post-change witness transaction before promotion.

## Browserless paired image canary

Browserless/Chromium image changes are qualified before production mutation with reserved instance 91. The control image is discovered from the live 11/12/13 consensus; candidate identity is an exact locally present OCI digest. Control and candidate run sequentially with an empty profile class, the same Network-v2 namespace, equivalent Ordivon-owned environment, 1440x1000 headful Xvfb geometry, and the same neutral Browser Security detectors.

Acceptance requires the same-image control to return `PASS_CONTROL_REPRODUCIBLE`. A different image may carry expected browser/control identity changes, but any detector-shape drift, Network-v2 authority drift, challenge metadata drift, or CF02-CF07 public observation change fails closed. The canary receipt explicitly records `productionMutationAttempted=false`, `providerChallengeVisited=false`, `providerSendAttempted=false`, and `rootCauseEstablished=false`.

The 2026-09-18 negative control passed; a genuinely different older local image was held because PeetPrint and User-Agent changed. Production carriers were not restarted or rewritten in either run, and reserved instance 91 left no container, profile, X socket, or Xauthority residue.


## Browserless image promotion transaction

Promotion verification is split across authority owners. Harness verifies exact source/rendered/installed Quadlet identities, live carrier image consensus, exact paired-canary receipt, Network-v2 generation, admission fencing, Temporal/browser quiescence, staged restart health, rollback, and durable post-change evidence. Security-v2 independently rebuilds candidate bundles from manifests and recomputes old-LKG versus candidate pool drift before it may reseal per-carrier LKG fixtures.

After reseal is reviewed and committed, Harness finalize requires: the promotion gate is still closed, MCP is still stopped, the worker remains active, no Workflow/browser session is active, the Security-v2 revision differs from the pre-reseal revision, the pool-index digest differs from the pre-reseal digest, and a fresh live pool against that new index returns `NO_OBSERVED_DRIFT`. Any failure preserves the closed gate; image-mutation failures additionally restore the pre-attempt Quadlet and carriers.

A current-image live read-only plan on 2026-09-18 returned `NOOP_ALREADY_CURRENT`, with rendered source Quadlet SHA-256 exactly equal to the installed Quadlet, carriers 11/12/13 all on the same control image, MCP/worker/carriers active, and admission still open. No real different-image `--apply` has been executed as part of this acceptance.
