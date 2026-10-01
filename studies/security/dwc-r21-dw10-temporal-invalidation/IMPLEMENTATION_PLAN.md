# DW10 Temporal Invalidation Implementation Plan

**Goal:** Build a DWC-local deterministic projection that measures defense-epoch latency, computes advisory critical-path/slack only from explicit timing inputs, and invalidates only dependency descendants whose support changed.

**Architecture:** Keep DW10 under `studies/security` until repeated cross-case evidence justifies promotion into shared Composition. Model one Defense Epoch as owner-scoped source/derived nodes plus explicit dependency edges. Each edge independently declares whether source change invalidates the consumer and whether it participates in temporal precedence; no scheduling, authority, retry, or domain-verdict semantics are introduced.

**Tech Stack:** CPython stdlib, unittest, deterministic JSON/SHA-256.

**Spec:** Host Work `work:security:dwc-r21:dw10-temporal-invalidation:20261001` rev1 plus parent `work:security:defense-window-convergence-r21:20261001` rev2.

## Global Constraints

- No hidden global priority ranker.
- No scheduler in Composition or this study.
- No optimization outside the qualified feasible region.
- Unknown attacker timing must not be converted into fake precise slack.
- Host continuity is not domain/effect truth.
- Exact subject/currentness/policy/authority/circuit bindings remain owner-scoped.
- Changed support invalidates only explicitly dependent descendants.
- `schedulerAuthorityEstablished=false` and `domainAcceptanceEstablished=false` in every projection.

---

### Task 1: Selective invalidation core

**Files:**
- Create: `studies/security/dwc-r21-dw10-temporal-invalidation/dwc_dw10/temporal_invalidation.py`
- Create: `studies/security/dwc-r21-dw10-temporal-invalidation/tests/test_temporal_invalidation.py`

**Interfaces:**
- Consumes: previous/current Defense Epoch dictionaries.
- Produces: `project_epoch(previous_epoch, current_epoch) -> dict`.

- [ ] Test policy-only drift invalidates DW03 -> DW06 -> DW07 -> DW08, but not independent DW04/DW05/DW09.
- [ ] Implement exact node/edge validation, change detection, transitive invalidation and cost accounting.
- [ ] Add currentness-only, topology-change, non-invalidating-edge, cycle/dangling negative controls.

### Task 2: Temporal performance projection

**Files:**
- Modify: `.../dwc_dw10/temporal_invalidation.py`
- Modify: `.../tests/test_temporal_invalidation.py`

**Interfaces:**
- Consumes: explicit milestone timestamps, explicit stage durations/bases, explicit DW03 deadline budget.
- Produces: latency vector, TTVP, compromise->eradication/recovery metrics, critical-path standing, and policy-deadline slack.

- [ ] Test full observed latency vector.
- [ ] Test missing milestones remain UNKNOWN.
- [ ] Test known-duration DAG critical path and policy slack.
- [ ] Test any unknown duration suppresses precise slack.

### Task 3: Replay fixtures and acceptance evidence

**Files:**
- Create synthetic before/after epoch fixtures.
- Create Exchange public-timeline negative-control fixture with only source-grounded public milestones.
- Create fixture runner and acceptance receipt.

- [ ] Measure full recompute vs selective revalidation cost on synthetic drift.
- [ ] Demonstrate stale-support prevention on previously VERIFIED descendants.
- [ ] Demonstrate historical/public timeline does not invent local TTVP or attacker slack.

### Task 4: Documentation and verification

**Files:**
- Create `README.md`.
- Record exact verification commands and result digest.

- [ ] Run study unit tests.
- [ ] Run fixture runner.
- [ ] Run compileall.
- [ ] Inspect diff/status.
- [ ] Commit candidate in isolated Runtime workspace.
- [ ] Update Host Work with evidence, boundaries, and next shared-promotion gate.
