# Workstation zero-base stock architecture and source audit — executable Spec R1

**Baseline:** GitHub main `ef17d6879d12faa61fff3bb762b0d500d73c9113`, observed 2026-11-10 around 01:43 Asia/Shanghai.
**Natural Owner:** `platform/workstation` only; cross-owner readers retain their own authority.
**Inventory:** all 265 tracked Workstation files; 29,720 physical line terminators/count (including lock and historical files). The 265-row appendix is an exact SHA12-bound *file census and candidate disposition*, not a machine-proof that all dynamic consumers are known.
**Mode:** stock cleanup/refactor/repair **only**. No new features, tests, test frameworks, consumer routes, experimental weak-model evaluation, extra Owner, Agent controller, universal registry, new installer or service. **Existing** native checks may run; source tests tied exclusively to retired code may be removed or corrected.

## 1. Problem representation — avoid patch-by-patch local optimization

The strategic problem is *mixed authority and temporal standing*: production systemd/Ansible/DSC/Quadlet/Cloudflare/Runtime node bindings, disposable migration/smoke implementations, and dated historical receipts coexist as if they were one current Workstation product. This inflates file count, makes old evidence look current, retains tests that only protect retired implementation shape, and prompts future Agents to build new tools from obsolete plans. Lines of code alone and a zero lexical reference count do **not** diagnose it. Current desired source, installed generation, active service, execution principal and domain consumer are separate.

Existing neighboring Draft PR **#1997** already retires `docs/MIGRATION_R1.md` and `inventory/current-substrate.md` after rebinding README, **do not alter those paths here**; review/rebase against its final state rather than duplicating its commit. PR #1967 and #1987 have already merged their WSL authority and Ansible frame fixes. Do not reimplement.

## 2. Mature theory -> decision, with limits

1. **Parnas information hiding (CACM 1972):** decompose by reasons to change, not chronological stages or filenames. Workstation owns node realization/selected provider materialization; Host owns Work truth; Runtime owns Job/Attempt effect; Cloudflare owns remote Worker state; consuming domain owns semantic success. A different reason-to-change sharing one path is a hypothesis for moving/retiring ownership, not automatic refactor authorization. Source: https://doi.org/10.1145/361598.361623
2. **Assume–Guarantee / Pacti / R2.1:** replacement `A_old => A_new` and `G_new => G_old` only under a common behavior universe, saturation, environment and effect/observer conditions; successful code builds do not discharge external assumptions. Source: https://www.pacti.org/
3. **Hoare/Frame:** bounded source edits must satisfy `WriteSet(change) ⊆ {Workstation tracked files, one explicitly qualified Repo SQL legacy callsite}`. No physical host service/configuration/database/archive is rewritten. Ansible static source semantics do not universally prove OS noninterference. Source: https://doi.org/10.1145/363235.363259
4. **Refinement / observational equivalence:** `Obs_c(Traces(new)) ⊆ Obs_c(Traces(old contract))` applies only to named live consumers, with explicit stuttering/environment/effect assumptions. Git history can preserve historical source but cannot prove a disconnected manual or remote consumer.
5. **DSM / MIT:** derive edges from actual source imports, Ansible templates, systemd units, checked-in manifests, test callers and native installed service references. Distinguish deliberate identical systemd settings in different unit/manager scopes from accidentally duplicated application logic. Source: https://dsmweb.org/
6. **Theory of Constraints / Lean:** focus on the bottleneck—wrong present-tense authority, duplicate one-shot machinery, and current/archived confusion—not filing more review documents. Remove a whole obsolete dependency chain when it has no necessary owner; use existing Git and CI feedback rather than additional approval stages.
7. **NASA V&V / causal falsification:** inspect the current machine for known installed consumers and independently read file refs before deletion. Static path absence leaves external manual use UNKNOWN; a reversible source deletion is acceptable without declaring production data deleted.
8. **Recursive LEGO R2.1:** use existing `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` for the **semantic responsibilities** already admitted, not 265 more LEGOs. Do not invent cost or abstraction values to make a table look formal. Source: `.agents/skills/recursive-lego-calculus/SKILL.md`.

## 3. Upstream mechanism map and subtraction boundaries

| Source family | Mature adopted mechanism / reference | Current durable Workstation role | Zero-base action |
|---|---|---|---|
| Linux host and service state | systemd, Ansible, Podman Quadlet | Declarations, node materialization, scoped no-regression | KEEP; review one-time retirement playbooks; never blanket-enable cold observability |
| Windows native node | WinGet Configuration, DSC v3, PowerShell/WSL | User vs service-context config and bounded provider status | KEEP current native authorities; do not add global WSL controller |
| Linux user/tool state | Nix/Home Manager, mise, pnpm, uv | Desired shell/tool materialization and exact binding | KEEP; no generic second inventory |
| Inventory and update | osquery, pacman, WinGet/uninstall registry, Syft | Read-only physical facts and selected tool resolution | KEEP native sources; remove stale current-sounding snapshots via PR #1997 |
| Infrastructure / network | OpenTofu, Cloudflare, WireGuard/Network Owner | Workstation owns node-side provider install only | KEEP until remote/live readback; official Wrangler handles deployments and rollback, custom receipt/idempotency may remain |
| Workflow / integration | Temporal, n8n, CloudEvents, AsyncAPI, outbox | Stable generic workflow/interface substrate | KEEP active interfaces; review one-off smoke/workflow fixtures separately |
| Evidence / backup | pgBackRest, PostgreSQL, Git, standard archival formats | Generic backup substrate and exact source receipts | KEEP pgBackRest; RETIRE retired Host v1 one-shot query projector from current executable tree, preserve original in Git and immutable source archive |
| Telemetry | Prometheus, journald/Vector/Loki, Grafana, Gatus, OpenTelemetry | Declarative telemetry, not universal health oracle | KEEP source where intentional; live inactive status is not an incident |
| Domain-specific node bindings | Runtime direct target, JEV, Playwright CLI, D-drive compact | Thin conditional physical adapters only | REVIEW actual calls and role overlap; no speculative replacement during this slice |

References: https://developers.cloudflare.com/workers/versions-and-deployments/ ; https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/ ; https://opentofu.org/docs/language/import/

## 4. Engineering Skills adapted without installing a new framework

- **Matt Pocock:** `to-spec` freezes this already-decided objective and its current public seam; `to-tickets` inspires the blocking-edge DAG below, not a second tracker; `codebase-design / improve-codebase-architecture` questions deep-module boundaries; `code-review` checks independent **Standards** (owner quality and no needless custom work) versus **Spec** (actual requested stock subtraction). For this cleanup, existing tests are the seam; user expressly forbids adding more.
- **ECC (affaan-m/ECC):** apply `search-first` (Git/source consumers and mature upstream), `change-impact` on current callers and `verification-loop` via existing `mise`/Root Repo checks; do not install its entire hook/Agent/memory apparatus or change model selection.
- **Superpowers (obra/superpowers):** reuse isolated Runtime Workspace, plan in exact files, systematic debugging of real native failures and `verification-before-completion`. Its test-first advice does not override the explicit no-new-tests rule.
- **Ordivon:** use already-installed `method-router`, `systems-engineering`, `design-structure-matrix`, `compositional-contracts`, `recursive-lego-calculus` and `skill-supply-chain-audit` selectively. No second source of authority.

## 5. Findings from current real files (not speculative future design)

- **Coverage:** 265 tracked files, 29,720 source lines including 1,574-line Cloudflare pnpm lock. `providers/cloudflare` has 58 files, `workstation` 40, `tests` 40, `ansible` 20, `docs` 16, `scripts` 13 and `inventory` 12.
- **Largest implementation responsibilities:** `ordivon_edge_release.py` 1,318 lines; `ordivon_cloudflare_tofu_handoff.py` 865; `input_authority_ingress.py` 669; `jev_fastpath_provider.py` 635; `ansible/n8n.yml` 623; `d_drive_compact_gate_r3.py` 548. High LOC is a review priority, not delete authorization.
- **Intentional byte duplicates:** system/user manager limits are separate systemd manager scopes; Loki/Netdata/Vector heavy profile drop-ins have identical bytes but distinct service scopes. No cleanup by hash alone.
- **Dated source vs actual runtime:** live observed temporal.service and postgresql.service active, backup and update-discovery timers active; Prometheus, node exporter, Gatus, Vector, Loki, Netdata and Edge GC inactive/disabled. Do not apply historical September acceptance as a desired live state. Podman currently runs Artifact Zot, Browserless and Network Gluetun, not the n8n pod.
- **One high-confidence executable debris chain:** `scripts/host_historical_projection.py` (463 lines) creates a one-off 2026-09 Host v1 SQLite→Parquet/DuckDB historical projection. Inbound named source references are its retired test, its 2026-09 evidence and the Repo's SQLite legacy debt gate. No installed systemd unit or timer references this script; retired Host v1 immutable SQLite snapshot remains on disk and Host current owner resides in `services/host`. `tests/test_host_historical_projection.py` only asserts legacy source shape. This is a candidate to remove **as one complete chain**, not per-file independent microtasks. Preservation is the exact Git source commit and unchanged physical historical archive; never delete the backup.
- **Current but conditional implementation:** `workstation/input_authority_ingress.py` has an Ansible node-carrier source consumer, `equipment_binding.py` is imported by Media/Harness, `update_candidate_report.py` has installed systemd consumer and `ordivon_edge_release.py` has Cloudflare operational callers. These are not orphans even if their static import graph looks sparse.
- **Zero-string reference is not consumer proof:** 87 of 265 files had zero bounded named matches; many are service units, test fixture helpers, CLI entrypoints or dynamically loaded resources. None is automatically obsolete.

## 6. Complete ordered task graph (stock work only)

| ID | Dependency | Existing-code action | Exact stopping condition |
|---|---|---|---|
| Z0 | — | Freeze remote main, isolate Runtime workspace, inspect open PRs and AGENTS | exact SourceCut, no worktree interference |
| Z1 | Z0 | Enumerate **all** tracked Workstation files with digest, size, role, bounded edges; inspect high-impact source bodies and current native state | Appendix A 265/265; UNKNOWN remains typed |
| Z2 | Z1 | Compare upstream system/engineering patterns and current Ordivon Skills; audit each high-risk branch for theory fidelity, overconservatism, superficiality, wrong representation, mature reuse and native consumer | concise category decisions with concrete counterexamples |
| Z3 | Z2 | Exchange candidate graphs and negative findings in existing Host Space, request actual independent Agent reply; do not treat posting as approval | SourceCut-tagged messages and explicit response standing |
| Z4 | Z2, Z3 request sent | Subtract **only** the tightly bounded retired Host v1 projection source/test/2026-09 artifacts; remove stale root SQLite debt expectation because implementation is gone | no named existing-source consumers left, current Host storage untouched, Git history recoverable, existing Owner & Repo checks pass |
| Z5 | Z2 | Inspect other high-code families and one-shot smoke tasks; only change with confirmed redundant mechanics and no production ownership collision | each decision KEEP/REPAIR/RETIRE/UNKNOWN with exact native owner; no feature or test creation |
| Z6 | Z4, Z5 | Reconcile with pending Draft PR #1997; never duplicate its README/Sept snapshot cleanup | no overlapping Git edits or stale currentness claim |
| Z7 | Z4–Z6 | Execute **existing** Workstation `mise run verify`, root SQL dialect/architecture/retirement checks, affected Cloudflare/Ansible checks if code changed, `git diff --check`, review exact changed SHA | scopes and skipped/blocked checks reported honestly |
| Z8 | Z7 | Commit source-only stock cleanup and publish protected PR; invite separate Standards/Spec review, no auto production application | PR head SHA and native checks observed; MERGED/INSTALLED/CONSUMED distinct |

**Scope exception:** Root `tools/repo/check_sql_dialects.py` and its existing test contain direct references to the retired Workstation legacy projector, so Z4 may remove those expected legacy-debt entries. This does **not** alter current PG drivers or add/expand tests. All other Owner paths remain unchanged.

## 7. Pre-implementation adversarial review of each change family

| Target | Theory / R2.1 | Matt / ECC / Superpowers | Over-conservative? | Superficial? | Root representation / mature replacement / negative counterexample |
|---|---|---|---|---|---|
| Historical Host projector | No current Host semantic LEGO; retired data re-projection is one-shot archival source, not active authority | search-first callsites, source-cut and native ref checks; do not create test harness | Keeping a 463-line CLI solely due tests is conservative | Deleting only docs would be superficial | Remove whole self-referential historical chain; must **not** remove immutable Host v1 backup, current PG Work truth or SQLite migration utility still used |
| Host and WSL systemd | Single effect owner; source vs activated generation differ | native Ansible and OS readback | Adding an approval controller is conservative | Renaming YAML without fixing effects is superficial | Keep current #1967/#1987 hardening; verify active/cold profile; never re-add Windows global writer |
| Cloudflare large Python adapters | Remote provider and local installer have separate A/G and idempotency obligations | compare existing Wrangler before code removal, existing Cloudflare tests only | Treating 1,318 lines all as untouchable is conservative | Simply splitting files is superficial | Wrangler native version/deploy/rollback can replace generic operations **only when** custom receipt/effect identity remains; no deletion this pass without exact proof |
| Windows/JEV/D-drive | Native Windows identity and maintenance effects may be high-consequence | direct PowerShell/Runtime/DSC, focused existing checks | Adding a fresh platform daemon is conservative | Moving wrappers is cosmetic | Retain current boundaries until actual conflicting execution observed; avoid unsafe live compaction/restart |
| Telemetry/n8n historical smokes | Desired source does not imply running service | inspect systemd and Podman plus CLI/manual runbooks | Keeping every old smoke as must-run is conservative | Deleting YAML merely because disabled is superficial | Separate config from experiment; do not start inactive services or create consumer routes |
| Existing user/Agent text | Only human/Agent discovery can justify current docs | exact README and root source graph | Permanent documents for every past milestone overconservative | Cosmetic shortening misses stale authority | Pending #1997 handles the two known obsolete current-sounding docs; no overlapping edits |

**Auditor prompts for every file and change:** (1) Does its semantic responsibility exist today? (2) Who consumes it physically or by name? (3) Are all pre/post/effect/provenance assumptions valid and current? (4) Does the external mature system already implement it? (5) Are we protecting a test of retired implementation instead of an actual outcome? (6) Are we blocking a needed change for speculative safety? (7) Is a rename masking the wrong Owner? (8) Can this exact change be refuted by a real existing native check or observed service? No new compulsory sign-off loop.

## 8. Space and current publication boundary

Collaboration: `space:ordivon-capability-task-forum-r1:20261101` / `topic:ordivon-capability-task-forum-r1:03-refinement:20261101`, request sequence **25890**. Other Agents are asked for precise readset/effect counterexamples, not generic endorsements. Their direct replies are not assumed until observed. Workstation source remains the natural implementation authority; Host messages are evidence exchange only.

The execution workspace is isolated and based on the SHA above. PR #1997 is Draft at source audit time. Historic source references in Git are not the same as active consumed generation. Do not delete/compact any production archive, systemd service, network tunnel, WSL instance, PostgreSQL database or external Cloudflare resource as a consequence of source retirement.

---

## Appendix A: 265-file current-source inventory and candidate disposition

> Git main ef17d6879d12faa61fff3bb762b0d500d73c9113, 2026-11-10. Content SHA-256 abbreviated to 12 hex. A reference count is a bounded lexical scan of tracked UTF-8 sources of at most 160 KB (large locks omitted), not static or dynamic complete consumer proof. Zero refs never authorizes deletion. RETIRE and REVIEW labels are candidates until consumer and effect checks.

| Path relative to Workstation | LoC | SHA12 | Audit disposition | Responsibility/basis | Bounded refs |
|---|---:|---|---|---|---:|
| `.gitignore` | 2 | `6feaded4e28e` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 25 |
| `.python-version` | 1 | `fd81c059718a` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 22 |
| `README.md` | 86 | `bdc4a81185eb` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 189 |
| `ansible/bootstrap.yml` | 28 | `e1cf36c90680` | KEEP-DECL | Native Ansible declarative host configuration | 0 |
| `ansible/game-production-tools.yml` | 20 | `aec952f50a2a` | KEEP-DECL | Native Ansible declarative host configuration | 0 |
| `ansible/host-substrate.yml` | 87 | `0bb69bf49639` | KEEP-DECL | Native Ansible declarative host configuration | 3 |
| `ansible/inventory.ini` | 2 | `da82e5114284` | KEEP-DECL | Native Ansible declarative host configuration | 2 |
| `ansible/jev-fastpath-provider.yml` | 109 | `a8d29923bc0c` | KEEP-DECL | Native Ansible declarative host configuration | 1 |
| `ansible/n8n.yml` | 623 | `88ae85ddb448` | KEEP-DECL | Native Ansible declarative host configuration | 1 |
| `ansible/observability-grafana.yml` | 208 | `52e44db92859` | KEEP-DECL | Native Ansible declarative host configuration | 1 |
| `ansible/observability-logs.yml` | 98 | `6d45c25be741` | KEEP-DECL | Native Ansible declarative host configuration | 1 |
| `ansible/observability-metrics.yml` | 89 | `672b91b60f7b` | KEEP-DECL | Native Ansible declarative host configuration | 1 |
| `ansible/observability-traces.yml` | 83 | `e1be44e53c21` | KEEP-DECL | Native Ansible declarative host configuration | 1 |
| `ansible/postgresql-backup.yml` | 148 | `b2b2c1074686` | KEEP-DECL | Native Ansible declarative host configuration | 1 |
| `ansible/ppt-master-provider.yml` | 229 | `16393c9bb0de` | KEEP-DECL | Native Ansible declarative host configuration | 2 |
| `ansible/retire-wsl-cloudflare-canary.yml` | 22 | `b5183ce53d5b` | REVIEW-RETIRE | Transition-only playbook; check installed consumer and unfinished state | 1 |
| `ansible/retire-wsl-windows-runtime-provider.yml` | 53 | `fef4cf37d8be` | REVIEW-RETIRE | Transition-only playbook; check installed consumer and unfinished state | 2 |
| `ansible/temporal-production.yml` | 316 | `7fca03853c3b` | KEEP-DECL | Native Ansible declarative host configuration | 0 |
| `ansible/workstation-node-carriers.yml` | 42 | `a64b56eaa632` | KEEP-DECL | Native Ansible declarative host configuration | 2 |
| `ansible/workstation-retire-legacy-launchers.yml` | 15 | `0b90302f86eb` | REVIEW-RETIRE | Transition-only playbook; check installed consumer and unfinished state | 0 |
| `ansible/workstation-service-profiles.yml` | 104 | `021bec6a1983` | KEEP-DECL | Native Ansible declarative host configuration | 1 |
| `ansible/workstation-tool-bindings.yml` | 75 | `409630b6f2b3` | KEEP-DECL | Native Ansible declarative host configuration | 0 |
| `ansible/workstation-windows-jev-fastpath-provider.yml` | 55 | `12c5c3582ac9` | KEEP-DECL | Native Ansible declarative host configuration | 0 |
| `contracts/README.md` | 13 | `e43109cb2257` | KEEP-CONTRACT | Existing CloudEvents AsyncAPI outbox contract | 0 |
| `contracts/asyncapi/distribution-admission-data.schema.json` | 32 | `50a0b5eadd65` | KEEP-CONTRACT | Existing CloudEvents AsyncAPI outbox contract | 2 |
| `contracts/asyncapi/distribution-integration-result-data.schema.json` | 17 | `783c2dace597` | KEEP-CONTRACT | Existing CloudEvents AsyncAPI outbox contract | 2 |
| `contracts/asyncapi/integration-events.asyncapi.yaml` | 94 | `7e646b0884a1` | KEEP-CONTRACT | Existing CloudEvents AsyncAPI outbox contract | 1 |
| `contracts/cloudevents/ordivon-event.schema.json` | 20 | `d5a6310b7a63` | KEEP-CONTRACT | Existing CloudEvents AsyncAPI outbox contract | 1 |
| `contracts/outbox/postgresql-outbox.sql.example` | 15 | `8d48a02f9867` | KEEP-CONTRACT | Existing CloudEvents AsyncAPI outbox contract | 0 |
| `docs/ARCHITECTURE.md` | 129 | `00354ee7427c` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 50 |
| `docs/CANONICAL_PATH_CUTOVER_R6.md` | 18 | `383830c98ae7` | KEEP-HISTORY | Named exact-path consumer in legacy source-reference policy | 1 |
| `docs/CLOUDFLARE_PROVIDER_MAINTENANCE.md` | 27 | `6d03ab78cd20` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 0 |
| `docs/D_DRIVE_OFFLINE_MAINTENANCE_R3.md` | 47 | `0ad3e6176e60` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 1 |
| `docs/HOST_HISTORICAL_PROJECTION_R3.md` | 227 | `c11c67cbca44` | ARCHIVE | 2026-09 Host v1 projection evidence; exact Git history remains | 0 |
| `docs/JEV_FASTPATH_PROVIDER.md` | 27 | `b8c3bca0321e` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 2 |
| `docs/MIGRATION_R1.md` | 73 | `36db695b38c0` | PR1997 | Old migration path linked by README; separate pending draft PR handles cutover | 1 |
| `docs/N8N_DISTRIBUTION_ADAPTER_SMOKE.md` | 32 | `9e415b52c755` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 1 |
| `docs/N8N_INTEGRATION_SMOKE.md` | 81 | `7620544a68f4` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 1 |
| `docs/N8N_SERVICE.md` | 86 | `2b6c1e7b8130` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 0 |
| `docs/PPT_MASTER_PROVIDER.md` | 26 | `e8053a86a721` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 0 |
| `docs/STANDARDS_FIRST_COMPOSITION.md` | 42 | `57b0dab5dd5b` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 1 |
| `docs/TEMPORAL_PRODUCTION_GREEN.md` | 34 | `8d0a07acef88` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 0 |
| `docs/UPDATE_DISCOVERY_R2.md` | 142 | `2987a8f4172c` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 0 |
| `docs/WINDOWS_CLOUDFLARED_RUNTIME_INGRESS.md` | 69 | `e02c803c58bd` | REVIEW-DOC | Check SourceCut, current semantics and real human or agent consumer | 1 |
| `docs/WORKSTATION_CONTRACT_FIRST_EXECUTION_SPEC_R1.md` | 404 | `dd413bf17950` | KEEP-SPEC | Existing R2.1 contract and actual earlier source-only work | 1 |
| `evidence/host-v1-final-pg-archive-20260913.json` | 163 | `03d87c5c640c` | ARCHIVE | 2026-09 receipt from final retired Host v1 source; exact Git history remains | 0 |
| `evidence/host-v1-parquet-duckdb-r3-20260913.json` | 265 | `5d84d4bb2224` | ARCHIVE | 2026-09 derived historical query proof; exact Git history remains | 1 |
| `grafana/grafana.env` | 28 | `679aaffd19f9` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `grafana/ordivon-grafana.container` | 27 | `0dca0b444779` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `host/coredump.conf.d-20-ordivon-agent-node.conf` | 3 | `6868e6143a5f` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `host/system.conf.d-20-ordivon-agent-limits.conf` | 2 | `cebf04f23836` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `host/user.conf.d-20-ordivon-agent-limits.conf` | 2 | `cebf04f23836` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `inventory/README.md` | 112 | `4473ebfbc41a` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 7 |
| `inventory/current-substrate.md` | 83 | `441704bde059` | PR1997 | Dated September snapshot with current-sounding name; separate pending draft PR | 0 |
| `inventory/probe_executables.ps1` | 31 | `4dc43ca235bd` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 2 |
| `inventory/probe_executables.py` | 67 | `43c9b12420eb` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 3 |
| `inventory/queries/npm_packages.sql` | 3 | `2a7f9262e3b1` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 3 |
| `inventory/queries/os_version.sql` | 1 | `beb3b892af28` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 3 |
| `inventory/queries/python_packages.sql` | 3 | `8c108ee331ca` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 3 |
| `inventory/queries/running_executables.sql` | 4 | `47ff16e0ad72` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 2 |
| `inventory/queries/system_identity.sql` | 1 | `bb0d41249dba` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 3 |
| `inventory/queries/uptime.sql` | 1 | `c29815c0c423` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 2 |
| `inventory/snapshots/2026-09-14-machine-tools.json` | 389 | `9ef1a7ae856f` | KEEP-HISTORY | Dated snapshot, not current authority | 2 |
| `inventory/sources.json` | 127 | `b564087cd4df` | KEEP-INVENTORY | Native osquery, pacman, WinGet or PATH observation | 2 |
| `manifests/external-stack-v1.json` | 39 | `6afd27850f8e` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 0 |
| `mise.toml` | 47 | `d8b3409c8bd7` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 91 |
| `n8n/n8n.env` | 30 | `f3ebb4d7c863` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `n8n/ordivon-n8n-runners.container` | 23 | `71f0b91fcf47` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `n8n/ordivon-n8n.container` | 26 | `aa3048800bd4` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `n8n/ordivon-n8n.pod` | 16 | `bf9a787f3aee` | KEEP-DECL | External-system native declaration; installed need not mean active | 3 |
| `n8n/workflows/ordivon-distribution-adapter-smoke-v1.json` | 175 | `55587b457c31` | REVIEW-SMOKE | Integration smoke workflow: confirm active n8n consumer | 2 |
| `n8n/workflows/ordivon-integration-smoke-v1.json` | 78 | `700d2e82c9fd` | REVIEW-SMOKE | Integration smoke workflow: confirm active n8n consumer | 3 |
| `observability/README.md` | 30 | `dd7a67e1303b` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `observability/gatus/config.yaml` | 88 | `462b5b764a75` | KEEP-DECL | External-system native declaration; installed need not mean active | 3 |
| `observability/gatus/ordivon-gatus.service` | 33 | `af1c384d9f9d` | KEEP-DECL | External-system native declaration; installed need not mean active | 6 |
| `observability/grafana-datasources.yaml` | 45 | `2a61f1249b1d` | KEEP-DECL | External-system native declaration; installed need not mean active | 3 |
| `observability/loki.yaml` | 48 | `32c6620a1fc7` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `observability/netdata-v2.conf` | 3 | `599b4910e49b` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `observability/node-exporter.conf` | 1 | `88ee4b1c0b1e` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `observability/prometheus.conf` | 1 | `602dcf778a58` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `observability/prometheus.yml` | 33 | `0cac4ba11390` | KEEP-DECL | External-system native declaration; installed need not mean active | 9 |
| `observability/tempo.yaml` | 25 | `fce889bc593e` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `observability/vector-systemd.conf` | 13 | `e07c0874da68` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `observability/vector.yaml` | 85 | `49fc70c8d4b2` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `policy/README.md` | 7 | `67c1e2719679` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 0 |
| `postgresql/ordivon-postgresql-backup.service` | 14 | `2734a5838a65` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `postgresql/ordivon-postgresql-backup.timer` | 11 | `fe37acad196b` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `postgresql/pgbackrest.conf` | 13 | `04b39fb6f11b` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `postgresql/postgresql-pgdata.conf` | 7 | `99232a3f9a39` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `providers/cloudflare/.gitignore` | 12 | `e974965f6f95` | KEEP-DECL | Cloudflare native package and config | 1 |
| `providers/cloudflare/AGENTS.md` | 15 | `ea421e882bbc` | KEEP-REF | Cloudflare provider runbook or historical provenance | 1 |
| `providers/cloudflare/LICENSE` | 202 | `c95bae1d1ce0` | KEEP-DECL | Cloudflare native package and config | 0 |
| `providers/cloudflare/MIGRATION_PROVENANCE.md` | 17 | `a9328cf7f21d` | KEEP-REF | Cloudflare provider runbook or historical provenance | 0 |
| `providers/cloudflare/README.md` | 86 | `228718f3fc6c` | KEEP-REF | Cloudflare provider runbook or historical provenance | 1 |
| `providers/cloudflare/config/edge-policy.json` | 102 | `80907310fde1` | KEEP-DECL | Cloudflare native package and config | 9 |
| `providers/cloudflare/deploy/systemd/ordivon-edge-gc.service` | 21 | `301cd446f678` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 5 |
| `providers/cloudflare/deploy/systemd/ordivon-edge-gc.timer` | 12 | `03c889a4bed7` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 3 |
| `providers/cloudflare/docs/operations.md` | 239 | `638c91b9ee27` | KEEP-REF | Cloudflare provider runbook or historical provenance | 0 |
| `providers/cloudflare/docs/release.md` | 121 | `efca0c551a06` | KEEP-REF | Cloudflare provider runbook or historical provenance | 0 |
| `providers/cloudflare/docs/reliability.md` | 154 | `ffd3a34d0352` | KEEP-REF | Cloudflare provider runbook or historical provenance | 4 |
| `providers/cloudflare/docs/security.md` | 135 | `a6a4e33994d3` | KEEP-REF | Cloudflare provider runbook or historical provenance | 0 |
| `providers/cloudflare/package.json` | 27 | `bf61aee0656e` | KEEP-DECL | Cloudflare native package and config | 0 |
| `providers/cloudflare/pnpm-lock.yaml` | 1574 | `070d8b2b8a2c` | KEEP-PIN | Native dependency/reproducibility lock | 11 |
| `providers/cloudflare/pnpm-workspace.yaml` | 14 | `f5f7c8e5578f` | KEEP-DECL | Cloudflare native package and config | 5 |
| `providers/cloudflare/scripts/check-operations` | 19 | `76e220529f27` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 1 |
| `providers/cloudflare/scripts/check-policy-config.py` | 45 | `e3187559c6fb` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 1 |
| `providers/cloudflare/scripts/configure-r2-lifecycle` | 3 | `ce66219dfc9c` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 1 |
| `providers/cloudflare/scripts/configure_r2_lifecycle.py` | 154 | `8761a9e9c07f` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 4 |
| `providers/cloudflare/scripts/emit-contract-fixtures.ts` | 144 | `8c895d0608a6` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 1 |
| `providers/cloudflare/scripts/install-edge-client` | 4 | `2a3e2a35173e` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 1 |
| `providers/cloudflare/scripts/install-edge-operations` | 50 | `467cf9954908` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 2 |
| `providers/cloudflare/scripts/ordivon_cloudflare_tofu_handoff.py` | 865 | `ee1b7f5c625b` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 5 |
| `providers/cloudflare/scripts/ordivon_edge_client.py` | 556 | `961f48b6be62` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 4 |
| `providers/cloudflare/scripts/ordivon_edge_gc.py` | 297 | `f9e666c5fbb5` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 4 |
| `providers/cloudflare/scripts/ordivon_edge_release.py` | 1318 | `9ff2af1c379e` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 3 |
| `providers/cloudflare/scripts/tsconfig.contracts.json` | 9 | `a7eb5457a638` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/scripts/wrangler-dry-run.mjs` | 82 | `f130b453655d` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 1 |
| `providers/cloudflare/src/artifacts.ts` | 27 | `55db16d3f686` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/auth.ts` | 144 | `bea250c4b975` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/body.ts` | 63 | `a8939a171a62` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/browser-manifest.ts` | 56 | `49404336209e` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/browser-policy.ts` | 138 | `3c1b6c7b607e` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 1 |
| `providers/cloudflare/src/browser-run.ts` | 281 | `79b2ed12bf56` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 2 |
| `providers/cloudflare/src/cleanup.ts` | 82 | `996d7d479edb` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/contracts.ts` | 148 | `a16ed23a34b2` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/errors.ts` | 43 | `7178cbdc1130` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/execution.ts` | 36 | `2b98ea440c33` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/external-fetch.ts` | 195 | `47f6626f906d` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 2 |
| `providers/cloudflare/src/fetch-policy.ts` | 160 | `da3e1f6d9c1f` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 1 |
| `providers/cloudflare/src/http.ts` | 40 | `bea8b3f773df` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/idempotency.ts` | 490 | `73aad11ea2c7` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/index.ts` | 549 | `04a44ffcd8df` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 1 |
| `providers/cloudflare/src/observability.ts` | 61 | `3490e670f492` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/policy.ts` | 48 | `8d20dd5e59c0` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/receipts.ts` | 135 | `e139a91b6828` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/src/version.ts` | 30 | `10515b7c8e80` | KEEP-REVIEW | Production Cloudflare adapter; review native Wrangler reuse and actual effects | 0 |
| `providers/cloudflare/test/client_test.py` | 218 | `f06f860436d4` | KEEP-CHECK | Existing Cloudflare tests and protocol checks | 1 |
| `providers/cloudflare/test/contracts.test.ts` | 305 | `5d9bfa823d19` | KEEP-CHECK | Existing Cloudflare tests and protocol checks | 3 |
| `providers/cloudflare/test/gc_test.py` | 114 | `537e39fcaa50` | KEEP-CHECK | Existing Cloudflare tests and protocol checks | 1 |
| `providers/cloudflare/test/handoff_tofu_test.py` | 441 | `1ffbe20f9e73` | KEEP-CHECK | Existing Cloudflare tests and protocol checks | 2 |
| `providers/cloudflare/test/helpers.ts` | 274 | `ebc7f7463e6a` | KEEP-CHECK | Existing Cloudflare tests and protocol checks | 0 |
| `providers/cloudflare/test/lifecycle_test.py` | 119 | `f507bbddc912` | KEEP-CHECK | Existing Cloudflare tests and protocol checks | 1 |
| `providers/cloudflare/test/release_controller_test.py` | 549 | `b17a9c4d3ca2` | KEEP-CHECK | Existing Cloudflare tests and protocol checks | 1 |
| `providers/cloudflare/test/transactions.test.ts` | 414 | `8d8b35b28ebf` | KEEP-CHECK | Existing Cloudflare tests and protocol checks | 2 |
| `providers/cloudflare/test/worker.test.ts` | 438 | `64869b83815c` | KEEP-CHECK | Existing Cloudflare tests and protocol checks | 2 |
| `providers/cloudflare/tsconfig.json` | 30 | `87842799f63c` | KEEP-DECL | Cloudflare native package and config | 0 |
| `providers/cloudflare/wrangler.jsonc` | 63 | `d310f8f2b837` | KEEP-DECL | Cloudflare native package and config | 7 |
| `pyproject.toml` | 38 | `fd5f97fd23ae` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 60 |
| `scripts/accept-n8n-distribution-adapter-smoke.sh` | 35 | `ee764373f349` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 4 |
| `scripts/converge-n8n-distribution-adapter-smoke.sh` | 32 | `13741b1ad5cb` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 1 |
| `scripts/converge-n8n-integration-smoke.sh` | 76 | `9bd85ee9adde` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 1 |
| `scripts/deploy-gatus` | 118 | `e17e616459c9` | KEEP-OPER | Existing Owner operation or binding script | 1 |
| `scripts/host_historical_projection.py` | 463 | `7dab17dac833` | RETIRE | One-off retired Host v1 SQLite to Parquet DuckDB projector; no installed unit observed | 4 |
| `scripts/invoke-n8n-distribution-adapter-smoke.py` | 41 | `4581b2f8ec7b` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 3 |
| `scripts/invoke-n8n-integration-smoke.py` | 64 | `ca60a35d4c77` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 1 |
| `scripts/temporal-n8n-integration-smoke.py` | 100 | `064fed5f7f5e` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 2 |
| `scripts/temporal_green_smoke.py` | 61 | `2628eac4f8f6` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 1 |
| `scripts/temporal_nexus_smoke.py` | 105 | `b9efc1dd79fb` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 1 |
| `scripts/temporal_pgbackrest_restore_smoke.sh` | 90 | `2693ba1475df` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 3 |
| `scripts/test-integration-contracts.py` | 34 | `7892d7799f20` | REVIEW-SMOKE | One-shot smoke or historical operation; review manual user invocation | 0 |
| `scripts/verify-n8n-rootless.sh` | 52 | `58f38a0ff432` | KEEP-OPER | Existing Owner operation or binding script | 1 |
| `systemd/ordivon-observability-heavy.target` | 4 | `bade2b075aff` | KEEP-DECL | External-system native declaration; installed need not mean active | 11 |
| `systemd/ordivon-update-discovery.service` | 15 | `6d452a2149f1` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `systemd/ordivon-update-discovery.timer` | 11 | `735dc6f24839` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `systemd/service-profiles/loki.service.d/20-ordivon-observability-heavy.conf` | 2 | `831a8280fa59` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `systemd/service-profiles/netdata.service.d/20-ordivon-observability-heavy.conf` | 2 | `831a8280fa59` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `systemd/service-profiles/vector.service.d/20-ordivon-observability-heavy.conf` | 2 | `831a8280fa59` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `tempo/ordivon-tempo.container` | 27 | `1c8ae9d9ad89` | KEEP-DECL | External-system native declaration; installed need not mean active | 3 |
| `temporal/production.yaml` | 84 | `5424694c0322` | KEEP-DECL | External-system native declaration; installed need not mean active | 2 |
| `temporal/temporal.service.j2` | 43 | `c9641e68a86a` | KEEP-DECL | External-system native declaration; installed need not mean active | 1 |
| `tests/test_codex_cli_pnpm_contract.py` | 60 | `6a4a49fe3541` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_d_drive_compact_r3.py` | 238 | `955059422662` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_distribution_adapter_source_binding.py` | 58 | `7f3cf9fa46f8` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_equipment_binding_compat.py` | 31 | `56998456d77b` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_executable_probe.py` | 87 | `265b3d98f1f0` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_gateway_mcp_tofu.py` | 61 | `d3f3e4f0213c` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_gatus_deployment.py` | 56 | `74d409bc2ada` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_host_historical_projection.py` | 37 | `d2d5e440b541` | RETIRE | Only proves retired projector source structure, not a current Host consumer | 0 |
| `tests/test_host_substrate_authority.py` | 132 | `7aab5944580f` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_jev_consumer_secret_materializer.py` | 21 | `f8abc715e430` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_jev_fastpath_provider.py` | 52 | `fe072b9342a6` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_machine_inventory_contract.py` | 50 | `6c2bb2c36ed9` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_node_manifest_unique_keys.py` | 49 | `c4372a42ed53` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_observability_prometheus.py` | 23 | `71796b8b55ee` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_observability_traces.py` | 72 | `6e2052f1a22b` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_playwright_cli_binding.py` | 53 | `6fbf1f81d86d` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_provider_authority_validation.py` | 31 | `0e256ced3939` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_provider_linux_observers.py` | 70 | `8a482eafb349` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_provider_windows_wsl.py` | 57 | `04dadaa5f7e4` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_provider_windows_wsl_service.py` | 28 | `5b1b09a13493` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_runtime_provider_retirement.py` | 27 | `5283d45b89ac` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_service_profiles.py` | 68 | `777a9d0eff3d` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_temporal_pgbackrest_restore_smoke.py` | 57 | `7270abf0aa89` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_temporal_restore_scratch_safety.py` | 76 | `27b645fc1246` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_temporal_restore_stop_failure.py` | 62 | `4a643f5d8cb8` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_temporal_sdk_ops_contract.py` | 32 | `76e153726c5a` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_tofu_agent_birth_handoff.py` | 68 | `38bf1119ff73` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_tool_binding_projection.py` | 77 | `4e2448343083` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_update_candidate_report.py` | 211 | `f00a8f0f5102` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_windows_cloudflared_runtime_ingress.py` | 57 | `303f9c2631b4` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_windows_jev_fastpath_provider.py` | 221 | `5302f9227d06` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_windows_update_discovery_contract.py` | 112 | `e31e910a9a58` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_windows_user_git_bundle_consumer.py` | 50 | `b5a8c940406a` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_windows_workspace_environment_doctor.py` | 92 | `a625d8f8bd4f` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_workstation_agent_automation_carrier.py` | 92 | `47b6365d9e7a` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 1 |
| `tests/test_workstation_consequences.py` | 136 | `3f28d5c2434f` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 5 |
| `tests/test_workstation_input_authority_ingress.py` | 392 | `462aedc9705f` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_workstation_tool_binding.py` | 41 | `9b7e706527e2` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_wsl_cloudflare_canary_retirement.py` | 21 | `40407a8dd4d5` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tests/test_wsl_sparse_guest_health.py` | 24 | `28857e5dd15f` | KEEP-CHECK | Existing owner-native regression/contract check; no new tests this round | 0 |
| `tofu/README.md` | 13 | `69594a774b64` | KEEP-DECL | External-system native declaration; installed need not mean active | 0 |
| `tofu/agent-birth-handoff/.gitignore` | 5 | `f5e680799657` | KEEP-DECL | External-system native declaration; installed need not mean active | 0 |
| `tofu/agent-birth-handoff/.terraform.lock.hcl` | 10 | `a2133078d430` | KEEP-PIN | Native dependency/reproducibility lock | 3 |
| `tofu/agent-birth-handoff/README.md` | 60 | `4dc53d2336bd` | KEEP-DECL | External-system native declaration; installed need not mean active | 0 |
| `tofu/agent-birth-handoff/main.tf` | 377 | `c3a9bc56bf00` | KEEP-DECL | External-system native declaration; installed need not mean active | 3 |
| `tofu/agent-birth-handoff/outputs.tf` | 39 | `337cf6dad77d` | KEEP-DECL | External-system native declaration; installed need not mean active | 0 |
| `tofu/agent-birth-handoff/tofurc` | 6 | `fa958f234b76` | KEEP-DECL | External-system native declaration; installed need not mean active | 0 |
| `tofu/agent-birth-handoff/variables.tf` | 4 | `bb52071177e2` | KEEP-DECL | External-system native declaration; installed need not mean active | 0 |
| `tofu/agent-birth-handoff/versions.tf` | 16 | `2d3d950e7d60` | KEEP-DECL | External-system native declaration; installed need not mean active | 0 |
| `tools/update_candidate_report.py` | 320 | `043fad3c3c49` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 3 |
| `uv.lock` | 327 | `b0ec89ffd52b` | KEEP-PIN | Native dependency/reproducibility lock | 51 |
| `windows/install_update_discovery.ps1` | 55 | `bcc2472e8cec` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 2 |
| `windows/update_candidate_report.ps1` | 183 | `4cb59591f897` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 3 |
| `windows/user_git_bundle_checkout.ps1` | 132 | `8e595c380d08` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 1 |
| `windows/workspace_environment_doctor.ps1` | 162 | `babd82f7077d` | KEEP-OWNER | Owner entrypoint, manifest, pinned toolchain or policy | 1 |
| `workstation/README.md` | 32 | `277eaa72a2c2` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/agent_automation_carrier.py` | 70 | `6e9eaed89130` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 4 |
| `workstation/equipment_binding.py` | 137 | `412eb4967263` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/input_authority_contract.py` | 183 | `583af37cd169` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 3 |
| `workstation/input_authority_ingress.py` | 669 | `e6aaae6dd375` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 3 |
| `workstation/nix/codex-cli/README.md` | 10 | `1452b01a086e` | KEEP-DECL | Nix Home Manager or DSC WinGet desired state | 0 |
| `workstation/nix/codex-cli/package.json` | 10 | `6df116222d86` | KEEP-DECL | Nix Home Manager or DSC WinGet desired state | 1 |
| `workstation/nix/codex-cli/pnpm-lock.yaml` | 243 | `32b597c94bcf` | KEEP-PIN | Native dependency/reproducibility lock | 11 |
| `workstation/nix/codex-cli/pnpm-workspace.yaml` | 2 | `970c1b094004` | KEEP-DECL | Nix Home Manager or DSC WinGet desired state | 5 |
| `workstation/nix/flake.lock` | 51 | `049f1b193a78` | KEEP-PIN | Native dependency/reproducibility lock | 0 |
| `workstation/nix/flake.nix` | 24 | `1843cefad603` | KEEP-DECL | Nix Home Manager or DSC WinGet desired state | 0 |
| `workstation/nix/nix/home.nix` | 172 | `10cd8e54d5a9` | KEEP-DECL | Nix Home Manager or DSC WinGet desired state | 3 |
| `workstation/playwright_cli_binding.py` | 149 | `e8d2866b144a` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 5 |
| `workstation/providers/README.md` | 52 | `2cc03ad0da7e` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 0 |
| `workstation/providers/acceptance/authority-validation-r1.json` | 33 | `2eb6e69d4d75` | KEEP-HISTORY | Scoped provider acceptance record; requalification may be needed | 0 |
| `workstation/providers/acceptance/windows-wsl-observer-r1.json` | 36 | `1b737bd1f213` | KEEP-HISTORY | Scoped provider acceptance record; requalification may be needed | 0 |
| `workstation/providers/acceptance/windows-wsl-service-control-r1.json` | 51 | `cde12921a182` | KEEP-HISTORY | Scoped provider acceptance record; requalification may be needed | 0 |
| `workstation/providers/authority_validation/AuthorityValidationProvider.ps1` | 99 | `dba66abe2ca9` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/providers/authority_validation/materialize.py` | 54 | `e092cc39ba2f` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 1 |
| `workstation/providers/d_drive_compact/DDriveCompactAuthorizeR4.ps1` | 32 | `dcf5fafa1654` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/providers/d_drive_compact/DDriveCompactRunR3.ps1` | 45 | `e078f92a581f` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/providers/d_drive_compact/DDriveOfflineCompactR3.ps1` | 178 | `948751b48b84` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/providers/d_drive_compact/d_drive_compact_gate_r3.py` | 548 | `84740361da29` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/providers/d_drive_compact/materialize.py` | 41 | `1d8fb0a6e960` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 0 |
| `workstation/providers/linux_service_observer.py` | 49 | `10368f4c0cc3` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 1 |
| `workstation/providers/runtime_control_provider.py` | 75 | `5035a97a1224` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 1 |
| `workstation/providers/windows_wsl/WindowsWslProvider.ps1` | 177 | `04bbab7a2388` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 3 |
| `workstation/providers/windows_wsl/materialize.py` | 69 | `d1e8cbb6e337` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 0 |
| `workstation/providers/windows_wsl_service/WindowsWslServiceControlProvider.ps1` | 94 | `1f326b9f68a6` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/providers/windows_wsl_service/materialize.py` | 44 | `d25d71879cb4` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 1 |
| `workstation/providers/wsl_sparse_guest_health.py` | 88 | `890e6d26ed62` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 1 |
| `workstation/software.toml` | 273 | `a5ea56307f39` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 5 |
| `workstation/tool_binding.py` | 268 | `7f415c7dc4cf` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 4 |
| `workstation/windows/cloudflared-runtime.dsc.yaml` | 25 | `f106b7b3a456` | KEEP-DECL | Nix Home Manager or DSC WinGet desired state | 3 |
| `workstation/windows/jev-fastpath-provider.toml` | 21 | `2a8b081014de` | KEEP-DECL | Nix Home Manager or DSC WinGet desired state | 4 |
| `workstation/windows/jev_fastpath_provider.py` | 635 | `ba1da708e35d` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 3 |
| `workstation/windows/materialize-cloudflared-runtime-token.ps1` | 67 | `4c37e5391f9d` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/windows/materialize-jev-consumer-secrets.ps1` | 60 | `2d2570a73fa0` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 3 |
| `workstation/windows/materialize_jev_consumer_secrets.py` | 109 | `91a4cfe1a657` | KEEP-BINDING | Owner-local tool or provider binding with separately qualified consumers | 2 |
| `workstation/windows/workstation.dsc.yaml` | 34 | `09d211ae2b6b` | KEEP-DECL | Nix Home Manager or DSC WinGet desired state | 4 |

### Bounded inbound references for review candidates

- `ansible/retire-wsl-cloudflare-canary.yml`: REVIEW-RETIRE; platform/workstation/tests/test_wsl_cloudflare_canary_retirement.py
- `ansible/retire-wsl-windows-runtime-provider.yml`: REVIEW-RETIRE; platform/workstation/tests/test_runtime_provider_retirement.py; platform/workstation/workstation/README.md
- `ansible/workstation-retire-legacy-launchers.yml`: REVIEW-RETIRE; no bounded named source reference
- `docs/ARCHITECTURE.md`: REVIEW-DOC; .agents/skills/finance-experiment-review/SKILL.md; README.md; catalogs/authorities/records/cpmi-iosco/cpmi-iosco-pfmi-2012.json; catalogs/authorities/records/fix-trading/fix-4.4-errata-20030618.json; +46
- `docs/CLOUDFLARE_PROVIDER_MAINTENANCE.md`: REVIEW-DOC; no bounded named source reference
- `docs/D_DRIVE_OFFLINE_MAINTENANCE_R3.md`: REVIEW-DOC; platform/workstation/tests/test_d_drive_compact_r3.py
- `docs/HOST_HISTORICAL_PROJECTION_R3.md`: ARCHIVE; no bounded named source reference
- `docs/JEV_FASTPATH_PROVIDER.md`: REVIEW-DOC; platform/workstation/tests/test_windows_jev_fastpath_provider.py; services/harness/config/browser-capability-routes.json
- `docs/MIGRATION_R1.md`: PR1997; platform/workstation/README.md
- `docs/N8N_DISTRIBUTION_ADAPTER_SMOKE.md`: REVIEW-DOC; tools/repo/dependency_contracts.toml
- `docs/N8N_INTEGRATION_SMOKE.md`: REVIEW-DOC; platform/workstation/docs/STANDARDS_FIRST_COMPOSITION.md
- `docs/N8N_SERVICE.md`: REVIEW-DOC; no bounded named source reference
- `docs/PPT_MASTER_PROVIDER.md`: REVIEW-DOC; no bounded named source reference
- `docs/STANDARDS_FIRST_COMPOSITION.md`: REVIEW-DOC; platform/workstation/README.md
- `docs/TEMPORAL_PRODUCTION_GREEN.md`: REVIEW-DOC; no bounded named source reference
- `docs/UPDATE_DISCOVERY_R2.md`: REVIEW-DOC; no bounded named source reference
- `docs/WINDOWS_CLOUDFLARED_RUNTIME_INGRESS.md`: REVIEW-DOC; platform/workstation/tests/test_windows_cloudflared_runtime_ingress.py
- `evidence/host-v1-final-pg-archive-20260913.json`: ARCHIVE; no bounded named source reference
- `evidence/host-v1-parquet-duckdb-r3-20260913.json`: ARCHIVE; platform/workstation/docs/HOST_HISTORICAL_PROJECTION_R3.md
- `inventory/current-substrate.md`: PR1997; no bounded named source reference
- `n8n/workflows/ordivon-distribution-adapter-smoke-v1.json`: REVIEW-SMOKE; platform/workstation/docs/N8N_DISTRIBUTION_ADAPTER_SMOKE.md; platform/workstation/scripts/converge-n8n-distribution-adapter-smoke.sh
- `n8n/workflows/ordivon-integration-smoke-v1.json`: REVIEW-SMOKE; platform/workstation/docs/N8N_INTEGRATION_SMOKE.md; platform/workstation/docs/STANDARDS_FIRST_COMPOSITION.md; platform/workstation/scripts/converge-n8n-integration-smoke.sh
- `scripts/accept-n8n-distribution-adapter-smoke.sh`: REVIEW-SMOKE; capabilities/distribution/README.md; platform/workstation/docs/N8N_DISTRIBUTION_ADAPTER_SMOKE.md; platform/workstation/tests/test_distribution_adapter_source_binding.py; tools/repo/dependency_contracts.toml
- `scripts/converge-n8n-distribution-adapter-smoke.sh`: REVIEW-SMOKE; platform/workstation/docs/N8N_DISTRIBUTION_ADAPTER_SMOKE.md
- `scripts/converge-n8n-integration-smoke.sh`: REVIEW-SMOKE; platform/workstation/docs/N8N_INTEGRATION_SMOKE.md
- `scripts/host_historical_projection.py`: RETIRE; platform/workstation/evidence/host-v1-parquet-duckdb-r3-20260913.json; platform/workstation/tests/test_host_historical_projection.py; tools/repo/check_sql_dialects.py; tools/repo/test_sql_dialects.py
- `scripts/invoke-n8n-distribution-adapter-smoke.py`: REVIEW-SMOKE; platform/workstation/docs/N8N_DISTRIBUTION_ADAPTER_SMOKE.md; platform/workstation/scripts/accept-n8n-distribution-adapter-smoke.sh; platform/workstation/tests/test_distribution_adapter_source_binding.py
- `scripts/invoke-n8n-integration-smoke.py`: REVIEW-SMOKE; platform/workstation/docs/N8N_INTEGRATION_SMOKE.md
- `scripts/temporal-n8n-integration-smoke.py`: REVIEW-SMOKE; platform/workstation/docs/N8N_INTEGRATION_SMOKE.md; platform/workstation/tests/test_temporal_sdk_ops_contract.py
- `scripts/temporal_green_smoke.py`: REVIEW-SMOKE; platform/workstation/tests/test_temporal_sdk_ops_contract.py
- `scripts/temporal_nexus_smoke.py`: REVIEW-SMOKE; platform/workstation/tests/test_temporal_sdk_ops_contract.py
- `scripts/temporal_pgbackrest_restore_smoke.sh`: REVIEW-SMOKE; platform/workstation/tests/test_temporal_pgbackrest_restore_smoke.py; platform/workstation/tests/test_temporal_restore_scratch_safety.py; platform/workstation/tests/test_temporal_restore_stop_failure.py
- `scripts/test-integration-contracts.py`: REVIEW-SMOKE; no bounded named source reference
- `tests/test_host_historical_projection.py`: RETIRE; no bounded named source reference

## 9. Actual bounded stock subtraction and verification (2026-11-10, same isolated Workspace)

**Z4 performed, source only:** removed five historically self-contained files: `scripts/host_historical_projection.py` (463 lines), `tests/test_host_historical_projection.py` (37), `docs/HOST_HISTORICAL_PROJECTION_R3.md` (227) and two dated `evidence/host-v1-*.json` (163 and 265). Original historical source remains readable at the pinned Git baseline. The retained 45,838,336-byte host-v1 SQLite snapshot at `/var/lib/ordivon/retired/host-v1/host-v1-48104ae46bc92c66.sqlite3` was observed and **not modified**. No Host v2 PG data, deployed service, Windows setting or Cloudflare resource was changed.

The two only present-tense cross-Owner text consumers were the static source-debt count in `tools/repo/check_sql_dialects.py` and the related existing `tools/repo/test_sql_dialects.py` expectation. The obsolete expected entry and test tuple were removed (existing test renamed to its actual domain+Harness scope); **no new tests were added**. Post-edit `git grep` found no named remaining source reference to the retired exact files outside this source-bound baseline ledger. This is evidence for a bounded source-only retirement, not a universal proof of no untracked external manual usage.

**Native verification in Runtime Job `job-01a1c177-74d0-7107-9b24-788f1db7dc2a`, exit 0:**
- `cd platform/workstation && mise run verify` — PASS, including Cloudflare provider CI/worker dry run and native Workstation consequence checks.
- `mise run repo:sql:verify` — PASS; existing 30 SQL dialect tests; six native osquery query files ran successfully; SQLite/Pg parser/current dialect checks passed.
- `mise run repo:retirement:verify` — PASS across archived source-reference policies.
- `python3 tools/repo/check_architecture_docs.py` — PASS.
- `git diff --check` and `git diff --cached --check` — PASS.
- Baseline retired projector test had 2/2 and root SQL tests 30/30 PASS *before* retirement; source-only retirement deletes the unnecessary source-self test rather than adding replacement tests.

**Non-overclaimed collateral finding:** Root SQL verifier still reports 32 remaining source files and 63 direct SQLite API calls, with repository-wide durable storage migration standing `NOT_CUT_OVER`. Host's current PostgreSQL authority is not proof that these unrelated source calls were removed. This broader concern belongs with its respective natural Owners, **not** a new Workstation feature or migration in this scope.

**Current source-diff scope:** seven paths including five removals and two minimal Repo code/test expectation adjustments; 1 insertion / 1,159 deletions (net 1,158). Appendix A intentionally remains the **before** SourceCut 265-file census, including retired files, to make the subtraction auditable, not a claim that all 265 paths remain at HEAD. Existing Draft PR #1997 remains separate.

**Independent cross-audit standing:** Host Space request at seq 25890 and precise Spec/falsifier packet at seq 25918; no direct peer acceptance claimed without an actual reply. GitHub CI, merge, installed generation and domain consumer status remain separately qualified when publication occurs.
