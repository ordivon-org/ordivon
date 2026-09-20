# Governance Persistence Ratchet R1

Date: 2026-09-19
Status: ACTIVE MIGRATION RATCHET — explicitly disposable

## Purpose

This is not a new Ordivon architecture layer. It is a temporary anti-layer: a migration ratchet that prevents Task + Workspace + Evidence + Gate + Lens + Operator + Registry from turning into seven durable control planes.

Design target: conditional continuity + ephemeral execution carrier + owner-native evidence/provenance + stateless decision predicates + versioned analytical methods + stateless reasoning transformations + rebuildable discovery indexes.

The ratchet MUST be deleted when natural owners enforce the same boundaries and repeated lifecycle audits show that the local guard no longer changes decisions.

## External-standard mapping

| Local word | Mature owner/pattern | Consequence |
| --- | --- | --- |
| Task | OMG CMMN for adaptive case semantics; Temporal only when durable executable workflow is actually required | Host Task stays a narrow continuity claim, not a universal workflow/domain object |
| Workspace | Git worktree + Kubernetes finished-Job TTL, owner/dependent GC and finalizers | Workspaces are disposable carriers; retention needs a live claimant/finalizer-equivalent reason |
| Evidence | W3C PROV + in-toto/SLSA + OpenLineage | persist references, digests, provenance and claims; do not copy owner-native raw truth by default |
| Gate | OPA decision/enforcement split | gate should be a pure decision or external policy evaluation, not a stateful coordinator/store |
| Registry | MCP Registry / OCI distribution patterns | discovery/index points to natural packages/content; it is not global semantic truth |

Canonical references:
- https://www.omg.org/spec/CMMN/
- https://docs.temporal.io/
- https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/
- https://kubernetes.io/docs/concepts/architecture/garbage-collection/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/
- https://git-scm.com/docs/git-worktree
- https://www.w3.org/TR/prov-primer/
- https://in-toto.io/docs/specs/
- https://slsa.dev/spec/v1.2/build-provenance
- https://openlineage.io/docs/spec/
- https://www.openpolicyagent.org/docs
- https://modelcontextprotocol.io/specification/2026-07-28
- https://github.com/modelcontextprotocol/registry
- https://github.com/opencontainers/distribution-spec/blob/main/spec.md

## Negative-lifecycle laws

### Task

A Host Task exists only to preserve cross-session semantic continuity.

Candidate terminalization law:

(progress in {LOCALLY_COMPLETE, SATURATED})
AND valueNow == NO_POSITIVE_VALUE_NOW
AND wake.conditions == []
=> semantic continuity should normally become terminal

This is a review rule, not an automatic destructive rule: the exact current Task revision must be resumed before mutation.

### Workspace

Workspace deletion follows a finalizer-like checklist:

active_jobs == 0
AND output_commit_or_artifact_preserved
AND (clean OR explicit_dirty_handoff)
AND no_current_semantic_claimant_requires_workspace
=> close

The commit/artifact is the retained product; the mutable worktree is not the archive.

### Evidence

Prefer subject/claim + producer identity + source/run identity + digest + provenance relation + verifier/version + verdict over copied raw bytes. Raw evidence remains with Runtime, Git, benchmark, browser, API or other natural owner whenever replay remains possible.

### Gate

A gate is behavior: decision = f(input, policy).

It must not own a second persistence plane merely because the decision matters. Persist a decision receipt only when a real replay/audit consumer exists.

### Analytical methods

Analytical methods are not a durable Ordivon object class. The natural owner is the mature external discipline or the domain itself. Invoke the method directly and retain only decision-relevant derived evidence when needed.

The former local Lens Registry, Router, Compiler, Portfolio, reserve pool, and operator ceilings are retired. Reintroducing a local method-selection ontology requires an irreducibility argument showing why direct external/domain method selection is insufficient.

### Registry

A local registry is acceptable only when it is the natural standard-defined authority or a rebuildable discovery projection.

A fixed dispatch map wrapped in a Registry class is not a registry and should collapse to direct dispatch or a pure function.

## Retired planning and question meta-layer

The local project LEGO plan schema, validator, rollout carrier, and Question Compiler are retired. They are not replaced by a second Ordivon planning ontology.

Use the natural owner directly:

- software implementation plans: obra-superpowers/writing-plans;
- implementation execution: obra-superpowers/subagent-driven-development and test-driven-development when applicable;
- codebase architecture discovery: codex-user/acquire-codebase-knowledge plus the project source/tests;
- scientific question formation: codex-user/hypothesis-generation;
- experiment design: codex-user/experimental-design;
- security analysis: codex-user/security-threat-model;
- other domains: the domain-native method or mature external standard.

Derived plans/questions remain working artifacts. Project truth stays in project-native source, tests, specifications, domain records, and owner-native evidence.

## Baseline

Live 2026-09-19 audit:
- Host open Tasks: 270
- NO_POSITIVE_VALUE_NOW: 97
- LOCALLY_COMPLETE: 51
- SATURATED: 23
- Runtime open Workspaces: 150
- dirty: 39
- with active Jobs: 3
- ordivon-next: 90
- core-zero/core-elimination named: 51

These counts diagnose retention pressure. They do not independently authorize deletion.

## Executable enforcement

scripts/check_governance_persistence_r1.py checks repository-static rules:
- the retained governance roles have explicit persistence classes;
- Gate is stateless;
- Registry is rebuildable by default;
- retired local method-routing infrastructure remains absent;
- retired local planning/question schemas, validators, and skills remain absent.

Dynamic Task/Workspace cleanup remains owner-native and revision-fenced through Host/Runtime; this repository does not create a second lifecycle database.

## Sunset

This ratchet is successful when it can disappear.

Delete it after:
1. natural owners enforce the same retention/cleanup invariants;
2. three consecutive lifecycle audits show no material stale-carrier backlog requiring local governance;
3. removing the ratchet does not permit additive Lens/Operator/Registry/Gate state to re-enter through another maintained contract.

## Lifecycle audit — 2026-09-20

Standing: **SUNSET_NOT_MET / STALE_CARRIER_PRESSURE_REMAINS**.

This audit used the Host and Runtime owner-native inventory surfaces directly. Counts are point-in-time observations; they are not deletion authority and may move while concurrent agents create or close carriers.

| Measure | 2026-09-19 baseline | 2026-09-20 observation |
| --- | ---: | ---: |
| Host open Tasks | 270 | 269 |
| `NO_POSITIVE_VALUE_NOW` | 97 | 97 |
| `LOCALLY_COMPLETE` | 51 | 50 |
| `SATURATED` | 23 | 23 |
| Runtime open Workspaces | 150 | 283 |
| Runtime dirty Workspaces | 39 | 46 |
| Runtime Ordivon Next Workspaces | 90 | 140 |
| `core-zero` / `core-elimination` named Workspaces | 51 | 38 |

The static ratchet remains healthy (`scripts/check_governance_persistence_r1.py` passes), but the dynamic sunset criterion does not. Host continuity pressure is essentially unchanged and Runtime carrier pressure remains material.

### Owner-native cleanup performed

For Ordivon Next workspaces, a bounded cleanup required all of the following before closure:

- no current non-terminal Host Task checkpoint referenced the Workspace;
- Runtime reported the Workspace clean;
- no active Runtime Job was attached;
- the Workspace HEAD was already reachable from current `main`, proving the Git output was preserved;
- the Workspace predated the current-day parallel work, reducing interference with active agents;
- `workspace.close` used the exact current `sourceStateDigest` with `force=false`.

Nine historical Workspaces satisfied those conditions and were removed:

- `ws-commercial-marketing-integration-r2-20260919`
- `ws-agent-service-standards-wave3-integrate-r1-20260919`
- `ws-r40-reconcile-latest-b2eab-20260919`
- `ws-commercial-integration-r5-20260919`
- `ws-commercial-integration-r3-20260919`
- `ws-agent-service-main-integration-r1-20260919`
- `ws-standards-wave2-next-20260919`
- `ws-agentservice-standards-wave2-r1-20260919`
- `ws-toolchain-authority-census-r3-20260919`

A separate bounded census found 112 clean, Host-unclaimed Ordivon Next Workspaces whose HEADs were **not** reachable from current `main`. They were deliberately retained: a clean worktree is not proof that its unique commit has been integrated, archived, rejected, or handed off. Deleting those carriers without resolving that preservation question would violate this ratchet's own finalizer-like law.

### Sunset consequence

This observation does **not** count as one of the three consecutive clean lifecycle audits required for deletion. The ratchet still changes real decisions: it caused safe closure of preserved carriers while preventing deletion of unpreserved unique commits.

Do not add a second lifecycle database or custom garbage collector to solve this. Continue using Host claimant navigation, Runtime Workspace state, Git reachability, and exact close fences. The next audit should reassess whether natural-owner lifecycle behavior has made this local review rule redundant.


## Lifecycle audit — 2026-09-20, preservation census R2

Standing: **SUNSET_NOT_MET / CARRIER_BACKLOG_MATERIALLY_REDUCED**.

A later same-day owner-native census found that the earlier 112 clean, Host-unclaimed, main-unreachable Ordivon Next Workspaces were no longer present in Runtime inventory. The audit therefore re-froze current reality instead of acting on the stale earlier list.

Point-in-time owner-native inventory during R2:

| Measure | Earlier 2026-09-20 observation | R2 observation |
| --- | ---: | ---: |
| Host open Tasks | 269 | 269 |
| `NO_POSITIVE_VALUE_NOW` | 97 | 98 |
| `LOCALLY_COMPLETE` | 50 | 51 |
| `SATURATED` | 23 | 23 |
| Runtime open Workspaces | 283 | 163 |
| Runtime dirty Workspaces | 46 | 43 |
| Runtime Ordivon Next Workspaces | 140 | 5 |
| Runtime dirty Ordivon Next Workspaces | not separately frozen | 2 |

The five Ordivon Next carriers at this cut were:

- one current preservation-census carrier;
- one dirty Dependabot carrier whose only output is the GitHub-native `.github/dependabot.yml` candidate;
- two clean carriers with explicit Host claimants for reflexive-security/reflexive-closure continuity;
- one dirty Chaoxing MVP carrier with an explicit Host claimant.

### Preservation method

For historical dirty Workspaces with no Host claimant and no active Runtime Job, the owner-native conversion is now:

```text
mutable Git worktree
    -> dirty-delta secret scan
    -> unique-history secret scan when HEAD is not in main
    -> temporary-index full snapshot
    -> git commit-tree
    -> annotated archive/workspaces/... tag
    -> reset/clean original worktree
    -> Runtime exact-digest close with force=false
```

This uses Git itself as the immutable history owner. It is not a new Ordivon archive service, lifecycle database or garbage collector.

Thirteen historical dirty Workspaces were converted to immutable Git snapshot tags and then closed. One old test-only credential sentinel was first replaced by a low-entropy test material value; its targeted historical test suite passed (16 tests) and its dirty delta then passed Gitleaks before archival.

Two additional carriers were removed without archive because their only dirty content was rebuildable external material:

- `ws-lit-synthesis-debt-r1-20260919`: 26 downloaded writing-skill audit files under `.audit/`, about 70 KB;
- `ws-chaoxing-repo-study-r1-20260917`: a clean nested clone whose HEAD exactly matched locally recorded `origin/main` for `https://github.com/tianshiemo7/chaoxing-auto-sign.git`.

The nested clone was removed only after verifying zero local changes, exact HEAD == `origin/main`, stable origin URL, no Host claimant and no non-terminal Runtime Job. Git, not Ordivon, remains the natural source owner.

An obsolete earlier preservation-census Workspace was also closed after its HEAD became reachable from main.

### Sunset consequence

R2 is substantial progress but still does **not** count as a clean sunset audit. The ratchet still changes decisions:

- claimant-bound Workspaces are retained even when clean;
- dirty unique work is converted to immutable Git history before carrier deletion;
- rebuildable external caches are discarded instead of being archived;
- current provider-native infrastructure output is integrated rather than frozen as historical debt.

The ratchet remains disposable. Delete it only after repeated future owner-native inventories show that these lifecycle decisions happen correctly without this local review rule.


## Lifecycle audit — 2026-09-20, cross-repository carrier preservation R3

Standing: **SUNSET_NOT_MET / HISTORICAL_CLEAN_IDLE_UNCLAIMED_ZERO**.

R3 re-entered owner-native state after a machine reboot rather than trusting the pre-reboot inventory. Host still reported 269 open continuity Tasks. Runtime re-froze at 130 open Workspaces / 44 dirty, and the previous preservation frontier reproduced exactly: 30 historical Workspaces were clean, idle, had no current Host claimant, and still carried Git history not preserved by current `main`.

This audit then resolved those 30 carriers without introducing a Workspace garbage collector, lifecycle database, archive service, or new Ordivon control plane.

### Unique-history preservation

Twenty-two historical carriers across Runtime, Host, Harness, Artifact, Security, and Game passed Gitleaks scans over the union of commits reachable from their historical HEADs but not current `main`.

For each carrier:

```text
historical clean Workspace
    -> current Host claimant recheck
    -> active Runtime Job recheck
    -> Git unique-history secret scan
    -> annotated archive/workspaces/<workspace-id> tag at exact HEAD
    -> verify peeled tag target == original HEAD
    -> re-read Runtime sourceStateDigest
    -> exact-digest workspace.close(force=false)
```

All 22 were converted to Git-owned immutable history and physically removed from Runtime with `force=false`.

### Paper2 false-positive adjudication

The remaining eight historical carriers were all in `/root/workstation-lab` and belonged to the Paper2 evidence lineage. A default Gitleaks scan initially failed closed with 41,581 findings, so these carriers were held rather than archived.

The findings were then adjudicated structurally without exposing candidate secret values:

- 41,577 `sourcegraph-access-token` findings mapped exactly to 40-hex research identifiers embedded in `paperId`, `source_record_id`, `record_id`, or URL fields. Counts matched the source structures exactly, including the expected duplicated matches where the same identifier appeared in more than one field representation. No modern Sourcegraph token prefixes were present in the inspected finding files.
- Four `generic-api-key` findings mapped to the top-level `token` field of Semantic Scholar bulk-search responses. Each response contained exactly 1,000 paper records while `total` exceeded 1,000; the four token values were distinct 124–125 byte base64url-like strings. The response shape was `total / token / data`, and official API semantics distinguish this continuation token from API-key authentication.
- After those two rule classes were explicitly adjudicated as corpus-induced false positives, a temporary scan extending the default Gitleaks rules while disabling only `sourcegraph-access-token` and `generic-api-key` passed the complete unique history of all eight carriers with no findings from any other default rule.

The scoped configuration was temporary and was deleted after the scan; no repository-wide secret rule was weakened. The eight carriers then received annotated `archive/workspaces/...` tags recording the adjudication and were closed only after another clean / idle / Host-unclaimed / unchanged-HEAD / exact-digest revalidation. All eight closures used `force=false`.

### Resulting inventory

The post-cleanup owner-native inventory was:

| Measure | R2 observation | R3 observation |
| --- | ---: | ---: |
| Host open Tasks | 269 | 269 |
| Runtime open Workspaces | 163 | 99 |
| Runtime dirty Workspaces | 43 | 42 |
| Runtime clean Workspaces | not separately frozen | 57 |
| Runtime Ordivon Next Workspaces | 5 | 3 |
| Runtime dirty Ordivon Next Workspaces | 2 | 1 |
| historical clean + idle + Host-unclaimed Workspaces | material backlog | **0** |

The Runtime total moved from 130 at the post-reboot R3 re-freeze to 99 at the final census while concurrent agents were also changing inventory. R3 itself explicitly closed 30 historical unique carriers; the raw global count delta is therefore an observation, not sole attribution.

The three remaining Ordivon Next Workspaces are all claimant-backed:

- `ws-reflexive-next-current-r1-20260918`: clean, current Host claimant;
- `ws-reflexive-closure-r1-20260918`: clean, retained WAIT continuity;
- `ws-chaoxing-mvp-r1-20260917`: dirty, current Host claimant.

### Sunset consequence

R3 proves that the historical clean-idle-unclaimed backlog can be reduced to zero using only Host claimant state, Runtime carrier state, Git reachability/equivalence/history, secret scanning, annotated Git refs, and exact compare-and-close fences.

R3 still does **not** count as one of the three clean audits required for ratchet deletion. The ratchet materially changed decisions during this audit: it prevented eight Paper2 carriers from being deleted on a raw secret-scan failure, required evidence-based false-positive adjudication, required 30 unique histories to be preserved before carrier removal, and retained claimant-backed Workspaces.

The next informative sunset evidence is a later owner-native lifecycle audit in which stale historical carriers do not accumulate and no manual ratchet intervention is required. Only such naturally clean observations should advance the three-audit deletion criterion.


## Lifecycle audit — 2026-09-20, historical dirty-carrier closure R4

Standing: **SUNSET_NOT_MET / HISTORICAL_IDLE_UNCLAIMED_BACKLOG_ZERO**.

R4 started from the 24 historical Workspaces that were dirty, idle, and had no current non-terminal Host claimant after R3 had already reduced the historical clean-idle-unclaimed backlog to zero.

The cleanup used the same finalizer-like owner-native rule: preserve unique work first, discard only proven rebuildable/external residue, then close through Runtime with a fresh sourceStateDigest and force=false.

### Directly discardable or already-preserved residue

Five Workspaces required no new snapshot archive:

- `ws-standards-wave5-workstation-control-20260919`: one Python `__pycache__` directory only; HEAD already preserved by main.
- `ws-xby-server-exposure-r1-20260918`: its only untracked JavaScript file was byte-identical to the same path on current main; HEAD was already an ancestor of main.
- `ws-jev-fastpath-workstation-r1-20260918`: dirty state was only Python bytecode; `git cherry main HEAD` marked the sole divergent commit with `-`, proving patch-equivalent preservation in main.
- `ws-market-capital-r2-w0-a01-nautilus-s02-20260915`: `.arbiter_upstream` was an unborn external Git container with NautilusTrader origin, no refs, and no worktree changes.
- `ws-paper2-a35-acr-review-20260915`: `acr-official` pointed at the recorded AutoCodeRover `origin/main` commit and contained only local deletions, with no added or modified local content.

These residues were removed explicitly, the Workspaces became clean, and all five were closed with fresh exact digests and force=false.

### Dirty snapshot preservation

Fifteen Workspaces containing real source, tests, paper assets, security/runtime changes, or audit material were preserved through:

```text
dirty Workspace
    -> temporary Git index
    -> full non-ignored snapshot tree
    -> commit-tree(parent = exact Workspace HEAD)
    -> Gitleaks over the snapshot commit
    -> annotated archive/workspaces/<workspace-id> tag
    -> Host claimant / active Job recheck
    -> reset + clean original mutable carrier
    -> fresh Runtime sourceStateDigest
    -> workspace.close(force=false)
```

All fifteen snapshot commits passed Gitleaks, all fifteen archive tags peeled to the expected snapshot commits, and all fifteen mutable Workspaces were removed.

### Paper2 dirty scientific carriers

Three remaining Paper2 Workspaces were handled separately:

- `ws-paper2-coder-a-prime-r74-20260919`: dirty snapshot passed default Gitleaks.
- `ws-paper2-r4-final-closure-20260915`: dirty snapshot passed default Gitleaks.
- `ws-paper2-coder-a-r57-clean-20260917`: default Gitleaks reported exactly 100 `sourcegraph-access-token` findings. All 100 came from the single file `ta-input-min/shard-015.jsonl`; that shard contained 100 records and exactly 100 40-hex substrings, all in the `record_id` field. A temporary scan disabling only that adjudicated rule passed every other default Gitleaks rule.

All three received annotated Git archive tags, were restored to clean original HEAD state, and were then closed with exact digests and force=false. No repository-wide secret rule was weakened.

### Media DVC forensic carrier

`ws-media-v2-assets-r6-20260911` contained a local DVC forensic sandbox under `.tmp/r6-dvc-forensic`, including a nested unborn Git repository and local DVC/cache/remote proof files. Because normal `git add -A` would treat the nested repository as a Git boundary rather than preserve its local forensic bytes, R4 used an archive-only payload:

- Gitleaks over the forensic directory: PASS;
- 12 non-`.git` files were packaged into a tar payload;
- tar size: 20,480 bytes;
- payload SHA256: `8e8450b7d005b47ae22482b3a880dc23ba8dcd10884849562011fb5378c84bef`;
- the tar blob was stored only in an archive commit/tag, not merged into main;
- snapshot commit: `e010edbe14a3`.

After the tag was verified, the temporary forensic directory was removed and the Workspace closed with force=false.

### Resulting inventory

The owner-native post-R4 census observed:

| Measure | R3 observation | R4 observation |
| --- | ---: | ---: |
| Host open Tasks | 269 | 269 |
| Runtime open Workspaces | 99 | 77 |
| Runtime dirty Workspaces | 42 | 20 |
| Runtime clean Workspaces | 57 | 57 |
| historical clean + idle + Host-unclaimed Workspaces | 0 | **0** |
| historical dirty + idle + Host-unclaimed Workspaces | 24 | **0** |

The arithmetic of total Runtime inventory remains point-in-time because same-day agents can create or close Workspaces concurrently. R4 itself explicitly resolved all 24 historical dirty-idle-unclaimed carriers that were frozen at its start.

A same-day clean main-equal Workspace, `ws-ordivon-lego-census-r1-20260920`, appeared during the final census. It is intentionally retained because same-day concurrent carriers are not classified as stale solely from being clean and Host-unclaimed.

### Sunset consequence

R4 still does **not** count toward the three naturally clean audits required to delete this ratchet. The ratchet again changed real decisions: it distinguished disposable cache/external residue from unique dirty work, forced secret scanning before preservation, required special handling for Paper2 false positives, and prevented a nested DVC forensic state from being lost.

The next useful sunset evidence must be a later audit in which both historical clean and historical dirty idle-unclaimed backlogs remain zero without another cleanup campaign.
