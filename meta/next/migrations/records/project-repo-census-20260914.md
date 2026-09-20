# Ordivon local project-repository census — 2026-09-14

Status: current-machine census; no repository deletion performed by this record.

## Decision rule

This census separates two questions that must not be conflated:

1. **Current architectural authority** — should this repository still own or carry forward current behavior?
2. **Physical local retention** — can the clone under `/root/projects` be removed now without breaking services, Runtime workspaces, provenance, or recovery?

`ARCHIVE` therefore does not automatically mean `rm -rf`. Historical Git/source may remain valuable while the repository has zero forward authority.

## Current inventory

Observed physical Git repositories under `/root/projects`: **30** (excluding `.worktrees`; `/root/projects/workstation` is only a symlink to `/root/workstation-lab`).

| Repository | Current disposition | Target disposition | Basis |
|---|---|---|---|
| `ordivon-host-v2` | KEEP — core | KEEP_MINIMAL_CORE | Current narrow continuity/work-state utility; v1 is retired. |
| `ordivon-runtime` | KEEP — core | KEEP_CORE | Current physical execution authority. |
| `ordivon-harness` | KEEP — core | KEEP_CORE | Current Agent/run adaptation and provider/tool composition surface. |
| `ordivon-next` | KEEP — transitional architecture/migration | KEEP_TRANSITIONAL, later shrink/dissolve by evidence | Current migration, standards/provider composition, capability and cross-project decision corpus; not a fourth runtime primitive. |
| `ordivon-artifact-v2` | KEEP — active owner | KEEP_WHILE_RESIDUAL_EXISTS | Current Artifact Build & Delivery residual; one source-tree-bound Temporal worker is live. |
| `ordivon-distribution-v2` | KEEP — active owner | KEEP_WHILE_RESIDUAL_EXISTS | Current external-first distribution control-plane residual; no retirement marker observed. |
| `ordivon-finance` | KEEP — migration hold | MERGE/RETIRE only after proven consumer cutover | `finance-retention-disposition.md` explicitly says `RETAIN ACTIVE / ... / DO NOT ARCHIVE YET`; Market Capital Next is a convergence target, not yet a demonstrated equivalent successor. |
| `ordivon-market-capital-next` | KEEP — active convergence target | KEEP_DOMAIN | Current clean-room market/capital composition using mature standards/providers. |
| `ordivon-media` | KEEP — active owner | KEEP_WHILE_CURRENT_CONSUMERS_EXIST | Current structured mediation/Studio capability owner. |
| `ordivon-network-v2` | KEEP — active owner | KEEP_WHILE_RESIDUAL_EXISTS | Current Network E2E authority; mature mechanisms/providers are composed rather than reimplemented. |
| `ordivon-operations-v2` | KEEP — active owner | KEEP_DOMAIN | Current machine/operations composition; current systemd source reference exists for Cloudflare edge GC. |
| `ordivon-paper2` | KEEP — active research project | KEEP_PROJECT / reproducibility carrier | Active Paper-2 screening/full-text/calibration work; not a shared platform owner. |
| `ordivon-research-v2` | KEEP — active owner | KEEP_DOMAIN | Accepted forward Research E2E source authority. |
| `ordivon-security-v2` | KEEP — active owner | KEEP_WHILE_RESIDUAL_EXISTS | Current external-first security verification substrate. |
| `ordivon-game` | EXTERNAL-CARRIER — active product | KEEP_SEPARATE_PRODUCT | Active Game product/research/development surface; should not be collapsed into the three core primitives. |
| `ordivon-web` | EXTERNAL-CARRIER — active product/interface | KEEP_SEPARATE_CARRIER | Active Web/public-facing carrier; not a core execution primitive. |
| `ordivon-host` | ARCHIVE — superseded v1 | LOCAL_EVICT_AFTER_WORKSPACE_CLOSE | Repository states `ARCHIVED / PRODUCTION RETIRED / NO ACTIVE HOST V1 AUTHORITY`; successor is Host v2. |
| `ordivon-market-capital-v2` | ARCHIVE — superseded | LOCAL_EVICT_AFTER_WORKSPACE_CLOSE | Retired; retained capabilities migrated to `ordivon-market-capital-next`. |
| `ordivon-research` | ARCHIVE — superseded v1 | LOCAL_EVICT_AFTER_WORKSPACE_CLOSE | Shared historical/provenance corpus; forward Research authority is v2. |
| `ordivon-security` | ARCHIVE — superseded v1 | LOCAL_EVICT_AFTER_WORKSPACE_CLOSE | Superseded by Security v2. |
| `ordivon-workstation-v2` | ARCHIVE — retired owner | LOCAL_EVICT_AFTER_WORKSPACE_CLOSE | Explicitly inert historical archive; generic machine responsibilities moved to Operations/upstream tools. |
| `codex-harness-mcp` | ARCHIVE — retired adapter | LOCAL_EVICT_AFTER_RESIDUAL_CHECK | Local MCP path retired and units removed; remote Cloudflare route remains a separate cleanup residual. |
| `ordivon-atlas` | ARCHIVE — historical corpus | MOVE_OUT_OF_ACTIVE_PROJECTS | Explicitly archived; current classification lives in Next, scientific prior art in Research v2. |
| `ordivon-computational-possibility` | ARCHIVE — historical research | MOVE_OUT_OF_ACTIVE_PROJECTS | Explicitly archived research/reproducibility corpus. |
| `ordivon-computing` | ARCHIVE — historical broad owner | MOVE_OUT_OF_ACTIVE_PROJECTS | Broad cross-project owner explicitly retired. |
| `ordivon-human` | ARCHIVE — historical research | MOVE_OUT_OF_ACTIVE_PROJECTS | Historical programme, no current owner/routing role. |
| `ordivon-interlocus` | ARCHIVE — historical research | MOVE_OUT_OF_ACTIVE_PROJECTS | Historical research/network semantics corpus; no current authority. |
| `ordivon-normative` | ARCHIVE — historical research | MOVE_OUT_OF_ACTIVE_PROJECTS | Historical research corpus; no current policy/authorization authority. |
| `ordivon-scd` | ARCHIVE — historical research | MOVE_OUT_OF_ACTIVE_PROJECTS | Historical Semantics of Computational Descriptions corpus. |
| `ordivon-world` | ARCHIVE — historical owner | MOVE_OUT_OF_ACTIVE_PROJECTS | Provider absorption into Operations completed; historical source preserved. |

## Counts

- Core retained: **3** — Host v2, Runtime, Harness.
- Transitional/current owner or active project retained: **11** — Next, Artifact v2, Distribution v2, Finance, Market Capital Next, Media, Network v2, Operations v2, Paper2, Research v2, Security v2.
- Separate external product/interface carriers: **2** — Game, Web.
- Explicit archived/retired repositories: **14**.
- Immediate hard-delete candidates: **0**. Local eviction is gated by workspace/provenance checks, not by architectural authority alone.

## Physical blockers observed

The source repositories are clean at their current checked-out heads, but Runtime still has open workspaces sourced from several retired repositories, including Host v1, Market Capital v2, Research v1, Security v1, Workstation v2, Atlas, Computing, Human, World, SCD, Normative, Interlocus, Computational Possibility and `codex-harness-mcp`. Some historical workspaces are dirty. Therefore deleting source trees before workspace reconciliation would be mechanically unsafe and would conflate workspace cleanup with repository retirement.

Current direct source-tree service/process references found by census:

- `ordivon-artifact-v2`: active Temporal artifact-delivery worker executes a script from the repo tree.
- `ordivon-operations-v2`: `ordivon-edge-gc.service` uses its Cloudflare provider directory as working directory.

Absence from this narrow source-path grep is not proof that an installed release is inactive; e.g. Host v2 intentionally runs from immutable `/opt/ordivon/host-v2/...` release material rather than the source tree.

## Finance / Market Capital convergence rule

Do **not** retire Finance merely because Market Capital Next exists. The current migration record requires demonstrated destinations and regression gates for Finance's current consequences. Market Capital Next is the preferred convergence target, but current equivalence is explicitly not assumed.

Target sequence:

`Finance current consumers -> mature/provider-native owners + Market Capital Next + Research v2 + Runtime + Operations -> regression proof -> Finance archive`

## First cleanup wave

The first physical cleanup should be repository-neutral and reversible:

1. close/reconcile old clean Runtime workspaces for already archived repositories;
2. inspect dirty archived workspaces and preserve any unique changes before closure;
3. verify remote/archive or other durable Git preservation for each archived source;
4. move fully retired local clones out of `/root/projects` (or delete local clones only after preservation proof);
5. remove the obsolete `/root/projects/workstation` compatibility symlink only when no caller remains;
6. repeat the census and require `/root/projects` to represent current work rather than historical ownership.

No architectural authority is created by this census.

## Post-cleanup current-machine addendum — 2026-09-14

The 30-repository table above is the initial census that drove cleanup and is intentionally retained as historical evidence. It is **not** the current `/root/projects` inventory after cleanup waves.

Current physical project-directory count is **15**. Finance has crossed its previously documented retirement gates and is no longer present under `/root/projects`; its complete Git archive and retirement receipts are recorded in `migrations/records/finance-source-retirement-closeout-20260914.md`. The earlier `KEEP — migration hold` Finance row is therefore superseded for current-machine standing.

The current 15 directories are:

- `ordivon-artifact-v2`
- `ordivon-distribution-v2`
- `ordivon-game`
- `ordivon-harness`
- `ordivon-host-v2`
- `ordivon-market-capital-next`
- `ordivon-media`
- `ordivon-network-v2`
- `ordivon-next`
- `ordivon-paper2`
- `ordivon-research-v2`
- `ordivon-runtime`
- `ordivon-security-v2`
- `ordivon-web`
- `ordivon-workstation-v2`

The original `ordivon-operations-v2` entry has also been superseded on the active project surface by the separately recorded Workstation-v2 operations-provider cutover. This does not change the three-core rule: Host v2 / Runtime / Harness remain the core primitives; other repositories are domain owners, products, projects or replaceable carriers.
