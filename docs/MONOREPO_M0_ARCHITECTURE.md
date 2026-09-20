# Ordivon Monorepo M0 Architecture

Date: 2026-09-20

Status: **M0 DESIGN CANDIDATE — migration architecture, not runtime authority**
Source baseline: `ordivon-next@ae1ac43130f95b264d908f7c73f268809300c0ea`

## 1. Decision

Ordivon will converge toward **one primary Git monorepo with many independent authorities**.

The decision changes source placement and repository-level coordination. It does **not** collapse execution, continuity, cognition, infrastructure, domain, scientific, security, or external-effect truth into one owner.

The target invariant is:

```text
ONE GIT REPOSITORY
!=
ONE PACKAGE
!=
ONE ENVIRONMENT
!=
ONE LOCKFILE
!=
ONE RELEASE
!=
ONE DATABASE
!=
ONE SERVICE
!=
ONE AUTHORITY
```

The monorepo is a source/change/history container. Ordivon owners remain bounded by their own contracts and natural external authorities.

## 2. System of interest

**System of interest:** the source-control, build/test navigation, change coordination, and migration boundary for the active Ordivon estate.

**Whole-system outcome:** an Agent can discover, modify, test, review, and coordinate a cross-Ordivon change from one source tree without losing the independent truth, environment, release, state, permission, or scientific lifecycle of the affected owners.

This M0 design does not attempt to redesign Runtime, Host, Harness, Research, Artifact, Media, Game, Capital, or other domain internals.

## 3. Why monorepo now

The current multi-repository estate has more Git boundaries than the observed code-level dependency and authority graph requires. Many repositories are already thin compositions around mature external owners, while cross-repository architecture, migration, capability, release, and consumer work repeatedly needs coordinated source inspection.

Observed code-level cross-repository edges are sparse and mostly intentional capability-consumption boundaries, for example Harness→Runtime, Workstation→Runtime, Network→Runtime, Distribution→Runtime, Media→Artifact/Runtime, and Capital→Research. The estate is not currently a single code monolith hidden behind multiple repositories.

Therefore the change is primarily:

```text
many Git coordination boundaries
            ->
one Git coordination boundary
with retained owner boundaries
```

## 4. External paradigms adopted

M0 adopts mature external principles rather than creating an Ordivon monorepo framework.

### 4.1 Git

Use Git as the history and source authority.

For history relocation, use `git-filter-repo`, not `git filter-branch`. Git's own documentation warns that `filter-branch` has safety and performance pitfalls and recommends alternatives such as `git-filter-repo`.

Before rewriting/importing any source history:

1. freeze the exact source HEAD;
2. create a full `git bundle --all`;
3. verify the bundle;
4. record its SHA-256;
5. perform history rewriting on a disposable clone, never on the source repository.

### 4.2 Bazel visibility principle, not Bazel adoption

Bazel treats visibility as an architectural boundary: implementation targets are private unless deliberately exposed.

Ordivon adopts this principle:

```text
default private
explicit public contract
no incidental cross-owner imports
```

M0 does **not** adopt Bazel or require BUILD-file conversion. The current estate does not justify replacing each owner's mature native build system.

### 4.3 Nx module-boundary principle, not Nx as the whole-repo owner

Nx demonstrates declarative dependency constraints between tagged projects. This is useful as a design reference.

M0 does not adopt Nx Conformance as the cross-language architecture owner because its language-agnostic enforcement requires Nx Enterprise. JavaScript/TypeScript owners may independently use the free lint integration when useful.

### 4.4 uv project isolation

uv workspaces intentionally share one lockfile and one resolution domain. Ordivon owners have independent dependency graphs, acceptance surfaces, release lifecycles, and environment rollback needs even when they currently target the same Python release.

Harness has now independently passed its full owner acceptance on Python `3.14.7`, so the former Harness-3.12-versus-3.14 incompatibility is no longer an architectural premise.

Therefore **there will be no root uv workspace in M0**. Each Python owner retains its own `pyproject.toml`, `uv.lock`, exact accepted interpreter pin, and project environment. Common runtime currency does not imply common dependency resolution.

### 4.5 language runtime currency

Ordivon uses a **latest-stable-by-default** language runtime policy.

1. Resolve the latest stable release from the language's official upstream authority at upgrade time.
2. Pre-release, beta, RC, nightly, and experimental channels are not the default.
3. After owner-native acceptance succeeds, pin the exact accepted patch/toolchain version in that owner's environment and CI.
4. Upgrade owner-by-owner; a repository-wide flag day is not required.
5. An older runtime may remain only when a concrete incompatibility is reproduced. The exception must name the blocker, affected owner, temporary version, and exit condition.
6. A newer stable runtime exposing latent warnings, deprecations, resource leaks, or dependency drift is treated as useful migration evidence to fix, not as a reason to remain indefinitely on the old runtime.
7. Sharing the same runtime version never implies sharing one virtual environment, lockfile, release, or rollback boundary.

At the current M0 migration point, Harness `main` has been accepted and fast-forwarded to Python `3.14.7` at `f747f6d3f513e76530d9777725a6727351c47dc8`, including a fresh cold-start owner environment, 909 pytest cases + 156 subtests, wheel install smoke, dependency/docs/evidence contracts, and vulnerability audit. Future Python, Node.js, Rust, and other language upgrades apply the same rule using their own official release authorities and owner-native acceptance.

### 4.6 mise as thin monorepo task navigation

mise supports explicit monorepo config roots, project-local tools/environments/tasks, path-qualified task execution, and affected-task selection.

M0 may use root mise only for repository-level task discovery/orchestration. Compilation, dependency resolution, tests, and release semantics remain owned by each project.

Because current Ordivon projects already have separate tool locks and need mixed-version compatibility, root configuration must preserve project-local mise locks:

```toml
monorepo_root = true

[monorepo]
lockfile = false
```

No root task may silently replace an owner's native build graph.

### 4.7 GitHub path ownership and protected integration

Use GitHub-native CODEOWNERS, rulesets, status checks, and reusable workflows rather than creating an Ordivon review/ownership platform.

Avoid making many path-filtered workflows individually required: GitHub documents that a workflow skipped by path filtering can leave its check Pending and block merge. Prefer a small always-running required root gate that deterministically selects and invokes applicable owner checks.

## 5. LEGO decomposition of the migration

Repository migration is decomposed into these responsibilities:

| LEGO | Responsibility | Natural owner |
| --- | --- | --- |
| Source history | commit graph, branches, tags | Git |
| Backup | portable pre-rewrite source preservation | Git bundle + filesystem backup policy |
| Path relocation | rewrite imported main history under target subtree | git-filter-repo |
| Change ownership | path-level review responsibility | GitHub CODEOWNERS/rulesets |
| Build/test environment | tool versions, dependency lock, project commands | owner-native Cargo/uv/pnpm/mise |
| Dependency visibility | public vs internal source contracts | language/native lint/build rules; Bazel/Nx principle only |
| Deployment identity | exact deployable source/release | each owner |
| Running state | live service/process/database state | each owner/provider |
| Consumer cutover | old-path→new-path transition | affected owner + consumer |
| Migration evidence | source SHA, rewritten SHA, validation and cutover receipt | temporary migration records |
| Rollback | restore old source/release path or archived repository | each migration slice |
| Scientific truth | frozen data/protocol/result lineage | study/domain owner |

No new M0 object becomes a global Task, State, Gate, Evidence Store, Registry, or workflow engine.

## 6. Target source layout

```text
ordivon/
├── .github/
├── docs/
├── mise.toml
│
├── meta/
│   └── next/
│
├── services/
│   ├── runtime/
│   ├── host/
│   └── harness/
│
├── platform/
│   ├── workstation/
│   ├── network/
│   ├── security/
│   └── skills/
│
├── capabilities/
│   ├── artifact/
│   ├── media/
│   ├── distribution/
│   └── research/
│
├── domains/
│   ├── game/
│   └── capital/
│
├── studies/
│   ├── paper1/
│   ├── paper2/
│   └── paper3/
│
└── tools/
    └── repo/
```

The categories are source-navigation clusters, not a new ontology. A component's authority is defined by its own contract, not by its directory name.

### 6.1 Root do-own

The monorepo root may own only repository mechanics:

- source navigation;
- CODEOWNERS;
- CI orchestration;
- changed/affected project selection;
- repository-wide secret scanning;
- history-migration documentation;
- repository contribution guidance.

### 6.2 Root do-not-own

The root must not introduce:

- Universal Task;
- Universal State;
- Universal Evidence;
- Universal Gate;
- Universal Registry;
- Universal Workflow;
- Universal Domain Model;
- a common database;
- a common release version;
- a common Python environment.

## 7. Owner placement

| Current source | Target | M0 action |
| --- | --- | --- |
| `ordivon-next` | `meta/next` | import cleaned main history |
| `ordivon-runtime` | `services/runtime` | import main history; keep Rust/Cargo release boundary |
| `ordivon-host-v2` | `services/host` | import main history; keep PostgreSQL/Alembic/service release |
| `ordivon-harness` | `services/harness` | import accepted Python 3.14.7 main `f747f6d3`; keep capability-island reduction as a separate semantic CL |
| `ordivon-workstation-v2` | `platform/workstation` | import stable main unchanged; reapply diverged carrier retirement separately |
| `ordivon-network-v2` | `platform/network` | deliver Browserless lifecycle decoupling before import |
| `ordivon-security-v2` | `platform/security` | direct low-risk import candidate |
| Harness `skills/` | `platform/skills` | extract only after Harness is imported; separate CL |
| `ordivon-artifact-v2` | `capabilities/artifact` | reconcile mailbox/delivery retirement before or after import as a separate semantic CL |
| `ordivon-media` | `capabilities/media` | deliver task-activated scope candidate before import |
| `ordivon-distribution-v2` | `capabilities/distribution` | deliver optional-effect downgrade before import |
| `ordivon-research-v2` | `capabilities/research` | data/provenance-heavy import; preserve bytes |
| `ordivon-game` | `domains/game` | direct import after canary proves history path |
| `ordivon-market-capital-next` | `domains/capital` | direct import after canary |
| `ordivon-paper2` | `studies/paper2` | direct scientific-source import late in migration |
| Paper1 frozen checkout | `studies/paper1` | do not import as independent history; derive from Research lineage |
| Paper3 under Research | `studies/paper3` | extract with `git mv` after Research import |
| `workstation-lab` | no wholesale target | bundle/archive; migrate only live residues to natural owners |

## 8. Authority boundaries after co-location

### Runtime

Owns Workspace, Job, Attempt, execution disposition, execution evidence, and reconciliation mechanics.

Does not own Host Task, Harness Run, or domain/scientific completion.

### Host

Owns cross-session continuity, revision-fenced checkpointing, Board collaboration state, and re-entry coordinates.

Does not own Runtime execution, Harness cognition, work priority, or domain truth.

### Harness

Owns bounded Agent Run identity/continuity, Provider/Tool interaction continuity, cognition loop semantics, run persistence contract, and completion proposals.

Does not own Host continuity, Runtime Job/Attempt truth, business workflow, or domain acceptance.

### Platform capabilities

Workstation, Network, Security, and Skills keep distinct owner contracts even when co-located.

### Capability/domain/study owners

Artifact, Media, Distribution, Research, Game, Capital, and each Paper retain their own semantic acceptance/truth boundaries.

## 9. Environment and lockfile laws

1. No root `pyproject.toml` merely to aggregate all Python projects.
2. No root `uv.lock`.
3. Each Python project retains its own `.python-version` or equivalent exact accepted interpreter pin.
4. Each Python project retains its own `.venv` semantics and lockfile even when multiple owners use the same latest stable Python.
5. Every language owner targets the latest stable upstream runtime/toolchain by default and records any temporary exception with a blocker and exit condition.
6. Runtime retains its existing Cargo workspace and `Cargo.lock` inside `services/runtime`; M0 does not create a root Cargo workspace.
7. Media and Game retain independent pnpm workspace/lockfiles in M0. Common Node.js currency does not require one pnpm workspace.
8. mise may select tools and invoke owner-native commands, but must not replace the package manager or build system.
9. A root dependency cache is an optimization only and may not become a dependency authority.

## 10. Dependency-boundary laws

Co-location must not create accidental dependencies.

M0 uses the following laws:

1. Cross-owner imports are denied by default conceptually.
2. Public source interfaces must be deliberate and documented by the producing owner.
3. Tests may not reach into another owner's implementation internals merely because paths are local.
4. File-path coupling to another owner's source tree is a migration smell unless that path is an explicit source contract.
5. Provider/runtime interaction should cross an owner-defined API/CLI/protocol/immutable-input boundary rather than direct internal imports.
6. Any new `shared/` code requires at least two real consumers with the same semantics, lifecycle, and change reason. M0 creates no generic `shared/framework`.
7. Architecture enforcement should use language-native tools first; only add a cross-language graph product after measured need.

## 11. History-preserving import contract

Every independently imported repository follows this sequence.

### 11.1 Freeze

Record:

- source path;
- exact main SHA;
- dirty/clean state;
- important live consumers;
- tags/branches count;
- target monorepo path.

Dirty repositories are not imported until their live delta is committed, archived, rejected, or handed off.

### 11.2 Backup

Create a full bundle outside the source and target repositories:

```bash
mkdir -p /root/ordivon-migration-backups/2026-09-20
git -C SOURCE bundle create /root/ordivon-migration-backups/2026-09-20/NAME.bundle --all
git -C SOURCE bundle verify /root/ordivon-migration-backups/2026-09-20/NAME.bundle
sha256sum /root/ordivon-migration-backups/2026-09-20/NAME.bundle
```

This bundle preserves branch/tag history even though M0 imports only the cleaned main lineage into the active monorepo.

A Git bundle contains reachable Git objects/refs; it does **not** preserve the working tree, index, stash, or untracked files. Therefore any non-clean source must also receive a pre-migration dirty-state capsule before any cleanup or rewrite:

- exact `git status --porcelain=v1`;
- `git diff --binary` for unstaged tracked changes;
- `git diff --cached --binary` for staged tracked changes;
- an explicit manifest and byte-preserving archive for untracked files that are not rebuildable/ignored.

The capsule is temporary migration evidence. It never authorizes applying the dirty delta to the monorepo.

### 11.3 Rewrite on a disposable clone

```bash
git clone --no-local --single-branch --branch main SOURCE /root/ordivon-migration-tmp/NAME
git -C /root/ordivon-migration-tmp/NAME filter-repo --to-subdirectory-filter TARGET --force
```

The source repository is never history-rewritten.

### 11.4 Merge unrelated rewritten history

Fetch the rewritten `main` into the monorepo and merge with `--allow-unrelated-histories --no-ff`.

Preserve the `.git/filter-repo/commit-map` outside the temporary clone as migration evidence before deleting the clone.

### 11.5 Validate

For the imported owner:

- exact expected tree exists under target path;
- owner-native lockfile remains local;
- owner-native tests/build run from target path;
- no sibling owner's environment is required;
- main-tip commit mapping is recorded;
- repository-wide secret scan passes;
- no live service has been switched yet merely because source import succeeded.

## 12. Branch and tag policy

M0 does not expose every historical branch/tag from every old repository as active monorepo refs.

Why:

- active ref namespaces from ~16 repositories would collide and overwhelm navigation;
- many refs are historical research/recovery branches;
- full original refs remain recoverable in the verified Git bundles and archived source repositories.

Policy:

1. integrate active migration candidates to source `main` before import when they are accepted;
2. import the cleaned `main` lineage;
3. preserve all original refs in verified bundles;
4. selectively recreate only still-live branch/tag semantics in the monorepo when an actual consumer requires them;
5. annotate the import boundary with a migration tag/record rather than pretending old and new SHAs are identical.

## 13. Large-data and artifact policy

History census found large but manageable blobs on active main lineages, including Media ~41.5 MB and Research ~33.5 MB. No active-main blob observed in the inspected high-data repositories exceeds GitHub's common 100 MB single-file hard limit.

M0 therefore does **not** perform opportunistic Git LFS migration, compression, deduplication, data normalization, or scientific-data cleanup during source migration.

This is intentional:

```text
history relocation
!=
data-lifecycle redesign
```

Any later LFS/object-store/data-product transition is a separate owner-native change with independent provenance and acceptance.

## 14. Scientific migration law

Research and Paper repositories require stronger invariants:

- exact source/frozen-input/result bytes preserved;
- scientific lineage preserved;
- no deduplication during relocation;
- no reformatting during relocation;
- no recomputation used as a substitute for byte identity;
- Paper2 remains its own scientific authority after placement under `studies/paper2`;
- Paper1 is not imported twice because its frozen checkout shares Research history;
- Paper1/Paper3 directory extraction occurs only after the Research lineage has been imported.

## 15. Live deployment and consumer cutover

A successful Git import does not authorize changing a live service.

Current known old-path consumers include:

- `ordivon-edge-gc.service` → `/root/projects/ordivon-workstation-v2/providers/cloudflare`;
- `ordivon-artifact-temporal-worker.service` → `/root/projects/ordivon-artifact-v2`;
- Skills MCP release/config/test material referencing `/root/projects/ordivon-next/.agents/skills` and `/root/projects/ordivon-harness`.

Each live cutover must be a separate effect:

```text
new source present
-> build/release from exact monorepo revision
-> switch service/provider config
-> native readback
-> consumer validation
-> retain rollback
-> only then retire old source path
```

A symlink compatibility bridge may be used temporarily only when a live consumer cannot be switched atomically. Every bridge must have an explicit removal condition; bridges are migration debt, not target architecture.

## 16. Pre-import metabolic cleanup

Do not import machinery already proven to be exiting when the cleanup can be safely delivered first.

Current candidate set at the M0 baseline:

- Next `fcca32e1`: retire legacy Agent Service — descendant of current main;
- Network `9aec70bb`: decouple Browserless from Agent Automation lifecycle — descendant of current main;
- Distribution `3f206409`: downgrade Distribution to optional effect profile — descendant of current main;
- Media `30f6d12`: scope Media to task-activated mediation — descendant of current main;
- Harness `66091559`: retire owner-misplaced capability layers — diverged;
- Workstation `f13d7640`: Agent Automation retirement lineage — diverged;
- Artifact `fceeee35`: mailbox-retirement lineage — diverged.

For the four linear descendant candidates, prefer independent acceptance and cleanup before import. For the three diverged candidates, do not make monorepo entry depend on a risky history/behavior reconciliation: import the current stable main unchanged unless the reduction has already been independently accepted, then reconstruct the reduction as a separate post-import semantic CL. Cleanup and source relocation are always separate commits. No history import commit may simultaneously change domain/service behavior.

## 17. Migration waves

### M0 — architecture and preservation

- freeze this architecture;
- freeze exact source baseline;
- establish backup/bundle procedure;
- classify cleanup candidates;
- define target repository skeleton and root governance.

### M1 — low-risk canary

Import cleaned:

1. Next → `meta/next`;
2. Security → `platform/security`;
3. Network → `platform/network`.

Acceptance: history mapping, owner-native tests, root CI mechanics, CODEOWNERS, independent project environments, no production cutover.

### M2 — platform and thin capabilities

Import:

- Workstation;
- Distribution;
- Media;
- Artifact.

Resolve old absolute source-path consumers separately.

### M3 — domains

Import Game and Capital without semantic refactoring.

### M4 — services

Import Host, cleaned Harness, and Runtime while keeping release/service/state identity fully independent.

### M5 — research/studies

Import Research and Paper2 late because provenance and data volume make them the highest source-migration consequence.

After Research import:

- relocate Paper1 study-owned paths using ordinary Git moves;
- relocate Paper3 study-owned paths using ordinary Git moves;
- validate frozen-byte/provenance invariants.

### M6 — post-import owner cleanup

- extract Skills from Harness to `platform/skills` in a separate architecture change;
- continue Harness loop/persistence/provider decomposition;
- selectively migrate useful workstation-lab residue;
- archive/retire workstation-lab.

### M7 — live source-path cutover and source-repo retirement

For each owner:

- build exact release from monorepo;
- deploy/switch;
- provider/native readback;
- real consumer validation;
- rollback exercise or proven rollback path;
- archive old repository read-only;
- remove temporary compatibility bridge.

## 18. Root CI model

M0 uses a small always-running required root workflow.

Responsibilities:

1. detect changed owner roots;
2. validate repository mechanics;
3. invoke each affected owner's canonical verify command;
4. report one stable required status;
5. run repository-wide secret scan.

Do not duplicate owner test logic into root scripts.

Initially, affected selection may remain simple and conservative. mise's monorepo/affected support may be adopted once target roots and dependency hints are stable. Correctness is preferred to an optimized CI graph during migration.

Full all-owner verification should run on a scheduled/manual path while the affected graph is being established.

## 19. CODEOWNERS/ruleset model

Use path ownership to make source responsibility visible.

Initial owner is the existing repository owner account `@zycxfyh`; path rules are still useful even with one human owner because they document boundaries and enable later delegation without restructuring the tree.

Rulesets should protect main from force-push and require the stable root verification check once the monorepo is authoritative.

## 20. Rollback model

Rollback is per migration slice, not one global monorepo rollback.

Before old-source retirement, every imported owner has three recovery routes:

1. verified original Git bundle;
2. unchanged/read-only old repository;
3. monorepo pre-cutover release/source revision.

For live services, source rollback is separate from state rollback. No migration step may imply that reverting source automatically rewinds PostgreSQL, Runtime Registry, Harness Run state, scientific state, provider state, or external effects.

## 21. Acceptance gates

### A. Source acceptance

PASS only when:

- exact old main tip is mapped to a rewritten monorepo commit;
- source tree under target path matches expected imported bytes after path prefixing;
- backup bundle verifies;
- owner-native build/tests pass.

### B. Boundary acceptance

PASS only when:

- owner environment remains independent;
- owner lockfile remains local;
- no prohibited direct cross-owner import was added by relocation;
- root contains no new universal semantic core.

### C. Release acceptance

PASS only when an exact monorepo revision can build the same owner release without relying on the old source checkout.

### D. Consumer acceptance

PASS only when real consumers observe the new release/source path correctly.

### E. Retirement acceptance

Old source repository/path may become read-only/retired only after:

- source acceptance;
- release acceptance where applicable;
- consumer acceptance where applicable;
- rollback path recorded;
- no unresolved dirty/current work depends on the old path.

## 22. Explicit non-goals for M0

M0 will not:

- force language owners into one shared runtime environment merely because they target the same latest stable version;
- unify uv lockfiles;
- create a root Python package;
- create a root Cargo workspace;
- unify Media/Game pnpm workspaces;
- adopt Bazel;
- adopt Nx Enterprise;
- redesign Runtime/Host/Harness state;
- migrate scientific bytes to new storage;
- deduplicate research/media data;
- create a component registry service;
- create an Ordivon monorepo control plane;
- remove old repositories before cutover proof.

## 23. Stop condition

M0 architecture work stops when the following are true:

1. target path for every active source authority is unambiguous;
2. environment/release/state boundaries are explicit;
3. each source has a preservation/import/validation strategy;
4. known live old-path consumers are recorded;
5. cleanup candidates are classified;
6. the low-risk M1 canary can be executed without reopening broad architecture discovery.

At that point architecture discussion gives way to small, evidence-producing migration changes.
