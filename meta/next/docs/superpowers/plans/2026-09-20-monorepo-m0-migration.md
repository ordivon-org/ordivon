# Ordivon Monorepo M0–M7 Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the active Ordivon source estate into one history-preserving Git monorepo while retaining independent authority, environment, lockfile, release, state, service, and scientific boundaries.

**Architecture:** The target repository is a source/change container, not a universal Ordivon runtime. Existing owner-native build systems remain authoritative. Each source is backed up, imported under a stable path by `git-filter-repo`, byte/tree-verified, owner-tested, and only later cut over at release/consumer boundaries.

**Tech Stack:** Git 2.55+, git-filter-repo, Git bundle, Ordivon Runtime workspaces, uv, Cargo, pnpm, mise monorepo tasks, GitHub CODEOWNERS/rulesets/Actions.

**Spec:** `docs/MONOREPO_M0_ARCHITECTURE.md`

## Global Constraints

- The monorepo root is a Git/repository-mechanics owner only.
- Do not create a root uv workspace, root `uv.lock`, or root Python package.
- Python owners target the latest stable Python accepted by their owner-native gates; Harness `main` is accepted and pinned to Python `3.14.7`. Common runtime currency does not merge owner environments or lockfiles.
- All language runtimes/toolchains follow latest-stable-by-default: exact accepted version pinned after verification; prereleases are opt-in; older-version exceptions require a reproduced blocker and explicit exit condition.
- Runtime keeps its Cargo workspace inside `services/runtime`; do not create a root Cargo workspace in M0.
- Media and Game keep separate pnpm workspaces/lockfiles in M0.
- Source relocation and semantic refactoring are separate commits.
- Every imported source gets a verified full Git bundle before any history rewrite.
- Run `git-filter-repo` only on disposable clones.
- Do not normalize/deduplicate/recompute Research/Paper data during relocation.
- Do not wholesale-import `/root/workstation-lab`.
- Do not separately import the Paper1 frozen checkout because it shares Research history.
- A successful source import does not authorize a production/service cutover.
- Do not retire an old source repository until its release/consumer/rollback gates are satisfied.
- No new universal Task/State/Evidence/Gate/Registry/Workflow abstraction is admitted by this migration.

---

## Target File Structure

```text
/root/projects/ordivon/
├── .github/
├── docs/
├── mise.toml
├── meta/next/
├── services/runtime/
├── services/host/
├── services/harness/
├── platform/workstation/
├── platform/network/
├── platform/security/
├── platform/skills/
├── capabilities/artifact/
├── capabilities/media/
├── capabilities/distribution/
├── capabilities/research/
├── domains/game/
├── domains/capital/
├── studies/paper1/
├── studies/paper2/
├── studies/paper3/
└── tools/repo/migration/
```

The `tools/repo/migration/` helpers are temporary. Remove them after M7 once all source imports and cutovers are accepted.

---

### Task 1: Freeze and review M0 architecture evidence

**Files:**
- Create: `docs/MONOREPO_M0_ARCHITECTURE.md`
- Create: `planning/monorepo-migration-baseline-r1.json`
- Create: `docs/superpowers/plans/2026-09-20-monorepo-m0-migration.md`

**Interfaces:**
- Consumes: exact local source HEAD census and current live-path census.
- Produces: authoritative migration design candidate and disposable migration inventory.

- [ ] **Step 1: Validate the temporary baseline JSON**

Run:

```bash
python -m json.tool planning/monorepo-migration-baseline-r1.json >/dev/null
```

Expected: exit 0.

- [ ] **Step 2: Check that the documents do not reintroduce retired planning infrastructure**

Run:

```bash
uv run --locked python scripts/check_governance_persistence_r1.py
```

Expected: PASS.

- [ ] **Step 3: Run the Next architecture/document checks**

Run:

```bash
uv lock --check
uv sync --locked
uv run --locked python -m pytest
uv run --locked --group authority python scripts/check_authority_catalog_r1.py
uv run --locked --group authority python scripts/check_standard_native_enterprise_r2.py
uv run --locked --group reasoning python scripts/check_reasoning_waist_r1.py
```

Expected: all exit 0.

- [ ] **Step 4: Commit only the M0 design artifacts**

Run:

```bash
git add docs/MONOREPO_M0_ARCHITECTURE.md \
        planning/monorepo-migration-baseline-r1.json \
        docs/superpowers/plans/2026-09-20-monorepo-m0-migration.md
git commit -m "docs: define monorepo M0 migration architecture"
```

Expected: one documentation/planning commit; no runtime/source behavior changes.

---

### Task 2: Form the cleaned Next migration candidate without moving source main

**Files:**
- Existing semantic candidate: `fcca32e1384e869fece1e506e14b991ed87e99ac`
- No new source files beyond the Task 1 documentation commit.

**Interfaces:**
- Consumes: Task 1 documentation commit and the linear Agent Service retirement candidate.
- Produces: one detached/integration candidate that contains two separate commits: retirement then M0 documentation.

- [ ] **Step 1: Record the Task 1 commit**

Run:

```bash
M0_DOCS="$(git rev-parse HEAD)"
test "$(git rev-parse HEAD^)" = "ae1ac43130f95b264d908f7c73f268809300c0ea"
printf '%s\n' "$M0_DOCS"
```

Expected: the parent is the frozen Next baseline.

- [ ] **Step 2: Verify the retirement candidate is still the expected linear descendant**

Run:

```bash
git merge-base --is-ancestor ae1ac43130f95b264d908f7c73f268809300c0ea \
  fcca32e1384e869fece1e506e14b991ed87e99ac
test "$(git rev-list --count ae1ac43130f95b264d908f7c73f268809300c0ea..fcca32e1384e869fece1e506e14b991ed87e99ac)" = 1
```

Expected: exit 0 and exactly one retirement commit.

- [ ] **Step 3: Rebase the documentation commit onto the already-existing semantic retirement without rewriting either source main or retirement commit**

Run:

```bash
git switch --detach fcca32e1384e869fece1e506e14b991ed87e99ac
git cherry-pick "$M0_DOCS"
```

Expected: HEAD contains retirement as parent and a new documentation commit as tip.

- [ ] **Step 4: Run the candidate's current CI-equivalent checks**

Run:

```bash
uv python install
uv lock --check
uv sync --locked
uv run --locked python -m pytest
uv run --locked --group quality ruff check scripts tests
uv run --locked --group quality ruff format --check scripts tests
uv run --locked --group authority python scripts/check_authority_catalog_r1.py
uv run --locked --group authority python scripts/check_standard_native_enterprise_r2.py
uv run --locked --group reasoning python scripts/check_reasoning_waist_r1.py
uv run --locked --group security bandit -r scripts -q -s B404,B603
```

Expected: all exit 0.

- [ ] **Step 5: Export the accepted workspace commit back to a non-main source-repository migration ref**

Run from the isolated Runtime Workspace:

```bash
git branch -f migration/monorepo-m0-next "$(git rev-parse HEAD)"
git -C /root/projects/ordivon-next fetch "$(pwd)" \
  refs/heads/migration/monorepo-m0-next:refs/heads/migration/monorepo-m0-next
git -C /root/projects/ordivon-next rev-parse migration/monorepo-m0-next
git -C /root/projects/ordivon-next rev-parse main
```

Expected: the migration ref resolves to the accepted candidate, while source `main` remains at its pre-migration revision. This explicit fetch also guarantees that `git bundle --all` from the source repository will contain the migration candidate.

---

### Task 3: Verify the other linear pre-import cleanup candidates

**Files:**
- Network candidate `9aec70bbfa3c8847dbd52c03a939c61f45e2f338`
- Distribution candidate `3f206409989e9274c1645ec25416df61b1662bff`
- Media candidate `30f6d1228a4270a68cd715ca9a7b17742478958e`

**Interfaces:**
- Consumes: existing candidate commits.
- Produces: accepted import revisions without changing source `main`.

- [ ] **Step 1: Verify Network ancestry and validate the candidate**

Run in a disposable detached worktree at the candidate:

```bash
git -C /root/projects/ordivon-network-v2 merge-base --is-ancestor \
  869b73a7859bead08dc9aaadb70a74e12ee59b2f \
  9aec70bbfa3c8847dbd52c03a939c61f45e2f338
rm -rf /root/ordivon-migration-tmp/network-validate
git -C /root/projects/ordivon-network-v2 worktree add --detach \
  /root/ordivon-migration-tmp/network-validate \
  9aec70bbfa3c8847dbd52c03a939c61f45e2f338
cd /root/ordivon-migration-tmp/network-validate
task all:validate
git -C /root/projects/ordivon-network-v2 worktree remove /root/ordivon-migration-tmp/network-validate
```

Expected: static/provider/finance validation exits 0 and no live install/converge task is invoked.

- [ ] **Step 2: Verify Distribution ancestry and candidate tests**

Run:

```bash
git -C /root/projects/ordivon-distribution-v2 merge-base --is-ancestor \
  d579eb56d0ee26289159d3addfa8130d5b07ce60 \
  3f206409989e9274c1645ec25416df61b1662bff
rm -rf /root/ordivon-migration-tmp/distribution-validate
git -C /root/projects/ordivon-distribution-v2 worktree add --detach \
  /root/ordivon-migration-tmp/distribution-validate \
  3f206409989e9274c1645ec25416df61b1662bff
cd /root/ordivon-migration-tmp/distribution-validate
uv python install 3.14.7
uv lock --check
uv sync --locked
bash scripts/test-all.sh
git -C /root/projects/ordivon-distribution-v2 worktree remove /root/ordivon-migration-tmp/distribution-validate
```

Expected: exit 0.

- [ ] **Step 3: Verify Media ancestry and candidate checks**

Run:

```bash
git -C /root/projects/ordivon-media merge-base --is-ancestor \
  300ce04ea669c0f029f7a67277a5f2e1bdb6f817 \
  30f6d1228a4270a68cd715ca9a7b17742478958e
rm -rf /root/ordivon-migration-tmp/media-validate
git -C /root/projects/ordivon-media worktree add --detach \
  /root/ordivon-migration-tmp/media-validate \
  30f6d1228a4270a68cd715ca9a7b17742478958e
cd /root/ordivon-migration-tmp/media-validate
uv python install 3.14.7
pnpm install --frozen-lockfile
pnpm bootstrap:python
.venv/bin/ruff check .
pnpm check
git -C /root/projects/ordivon-media worktree remove /root/ordivon-migration-tmp/media-validate
```

Expected: exit 0.

- [ ] **Step 4: Preserve accepted candidate refs without advancing source main**

Run:

```bash
git -C /root/projects/ordivon-network-v2 branch -f migration/monorepo-preclean \
  9aec70bbfa3c8847dbd52c03a939c61f45e2f338
git -C /root/projects/ordivon-distribution-v2 branch -f migration/monorepo-preclean \
  3f206409989e9274c1645ec25416df61b1662bff
git -C /root/projects/ordivon-media branch -f migration/monorepo-preclean \
  30f6d1228a4270a68cd715ca9a7b17742478958e
```

Expected: the three migration refs exist; the three source `main` refs remain at the M0 baseline.

---

### Task 4: Create verified source-history backups

**Files:**
- Create outside Git: `/root/ordivon-migration-backups/2026-09-20/*.bundle`
- Create outside Git: `/root/ordivon-migration-backups/2026-09-20/SHA256SUMS`

**Interfaces:**
- Consumes: all original repositories and accepted import revisions.
- Produces: portable full-ref backup plus exact digest before history rewriting.

- [ ] **Step 1: Create the backup root**

Run:

```bash
install -d -m 0700 /root/ordivon-migration-backups/2026-09-20
install -d -m 0700 /root/ordivon-migration-tmp
rm -f /root/ordivon-migration-backups/2026-09-20/SHA256SUMS
```

- [ ] **Step 2: Bundle the repositories whose import revision is already a source ref**

Run:

```bash
set -euo pipefail
for spec in \
  "next /root/projects/ordivon-next" \
  "runtime /root/projects/ordivon-runtime" \
  "host /root/projects/ordivon-host-v2" \
  "harness /root/projects/ordivon-harness" \
  "workstation /root/projects/ordivon-workstation-v2" \
  "network /root/projects/ordivon-network-v2" \
  "security /root/projects/ordivon-security-v2" \
  "artifact /root/projects/ordivon-artifact-v2" \
  "distribution /root/projects/ordivon-distribution-v2" \
  "research /root/projects/ordivon-research-v2" \
  "media /root/projects/ordivon-media" \
  "game /root/projects/ordivon-game" \
  "capital /root/projects/ordivon-market-capital-next" \
  "paper2 /root/projects/ordivon-paper2" \
  "workstation-lab /root/workstation-lab"
do
  set -- $spec
  id="$1"
  repo="$2"
  out="/root/ordivon-migration-backups/2026-09-20/$id.bundle"
  git -C "$repo" bundle create "$out" --all
  git -C "$repo" bundle verify "$out"
  sha256sum "$out" >>/root/ordivon-migration-backups/2026-09-20/SHA256SUMS
done
sort -k2 -o /root/ordivon-migration-backups/2026-09-20/SHA256SUMS \
  /root/ordivon-migration-backups/2026-09-20/SHA256SUMS
sha256sum -c /root/ordivon-migration-backups/2026-09-20/SHA256SUMS
```

Expected: every bundle verifies and every SHA-256 check passes.

- [ ] **Step 3: Capture non-clean source state outside Git bundles**

A Git bundle does not contain the index/worktree. Before any cleanup, freeze workstation-lab's currently staged semantic delta:

```bash
backup=/root/ordivon-migration-backups/2026-09-20
git -C /root/workstation-lab status --porcelain=v1 \
  >"$backup/workstation-lab.status"
git -C /root/workstation-lab diff --binary \
  >"$backup/workstation-lab.unstaged.patch"
git -C /root/workstation-lab diff --cached --binary \
  >"$backup/workstation-lab.staged.patch"
git -C /root/workstation-lab ls-files --others --exclude-standard -z \
  >"$backup/workstation-lab.untracked.zlist"
sha256sum "$backup"/workstation-lab.{status,unstaged.patch,staged.patch,untracked.zlist} \
  >>"$backup/SHA256SUMS"
```

Expected: the status records exactly the four known staged Creative Library paths; the staged patch is non-empty; the unstaged patch and untracked list are empty at the M0 baseline. If reality differs, stop and refresh the baseline before continuing.

- [ ] **Step 4: Prove the accepted cleanup refs are inside their corresponding bundles**

Run:

```bash
git bundle list-heads /root/ordivon-migration-backups/2026-09-20/next.bundle \
  | grep -F migration/monorepo-m0-next
git bundle list-heads /root/ordivon-migration-backups/2026-09-20/network.bundle \
  | grep -F migration/monorepo-preclean
git bundle list-heads /root/ordivon-migration-backups/2026-09-20/media.bundle \
  | grep -F migration/monorepo-preclean
```

Distribution is checked here only after its full candidate validation has created `migration/monorepo-preclean`. Until then, its bundle may be created, but the candidate must not be used as an import revision.

Expected: every accepted migration ref is present in its source bundle.

---

### Task 5: Create the local monorepo skeleton

**Files:**
- Create: `/root/projects/ordivon/README.md`
- Create: `/root/projects/ordivon/AGENTS.md`
- Create: `/root/projects/ordivon/.gitignore`
- Create: `/root/projects/ordivon/docs/migration/receipts/.gitkeep`

**Interfaces:**
- Consumes: M0 spec.
- Produces: local target Git history with no product/service semantics.

- [ ] **Step 1: Initialize the repository without a remote**

Run:

```bash
test ! -e /root/projects/ordivon
mkdir -p /root/projects/ordivon/docs/migration/receipts
cd /root/projects/ordivon
git init -b main
```

- [ ] **Step 2: Create the root README**

Write exactly:

```markdown
# Ordivon

This repository is the primary source monorepo for Ordivon.

Repository co-location does not merge authority. Runtime, Host, Harness, platform capabilities, domain owners, and scientific studies retain their own state, environment, release, and semantic acceptance boundaries.

The root owns repository mechanics only. It does not define a Universal Task, State, Evidence, Gate, Registry, Workflow, or Domain Model.

See `docs/MONOREPO_M0_ARCHITECTURE.md` after Next is imported under `meta/next`.
```

- [ ] **Step 3: Create the root Agent instruction**

Write exactly:

```markdown
# Ordivon Monorepo Agent Rules

1. Work inside the natural owner directory.
2. Run that owner's native verification before claiming completion.
3. Do not import another owner's internals merely because they are in the same Git tree.
4. Cross-owner effects use the producing/consuming owners' explicit contracts.
5. Root tooling may orchestrate checks but may not redefine owner truth.
6. Do not unify lockfiles, environments, databases, releases, or scientific state as a repository-cleanup shortcut.
7. Keep source relocation separate from semantic refactoring.
```

- [ ] **Step 4: Create root ignores**

Write exactly:

```gitignore
.venv/
node_modules/
target/
dist/
build/
.mypy_cache/
.pytest_cache/
.ruff_cache/
__pycache__/
.DS_Store
```

- [ ] **Step 5: Commit the root-only skeleton**

Run:

```bash
touch docs/migration/receipts/.gitkeep
git add README.md AGENTS.md .gitignore docs/migration/receipts/.gitkeep
git commit -m "chore: initialize Ordivon monorepo source root"
```

Expected: one root-mechanics commit and no application/package manifest at repository root.

---

### Task 6: Add a temporary, tested history-import helper

**Files:**
- Create: `tools/repo/migration/import-owner.sh`
- Create: `tools/repo/migration/test-import-owner.sh`

**Interfaces:**
- Consumes: source repository, exact source revision, target path.
- Produces: verified bundle, filtered history, monorepo merge, commit-map receipt, byte/tree equality check.
- Sunset: delete both files after M7 source retirement.

- [ ] **Step 1: Write the failing smoke test**

Create `tools/repo/migration/test-import-owner.sh` that:

1. creates a temporary two-commit source repository;
2. initializes a temporary target repository;
3. calls `import-owner.sh sample SOURCE SOURCE_HEAD platform/sample TARGET_ROOT`;
4. asserts the imported files exist only under `platform/sample`;
5. compares `git ls-tree -r SOURCE_HEAD` to `git ls-tree -r REWRITTEN:platform/sample`;
6. verifies the generated bundle;
7. verifies a receipt contains source revision, rewritten revision, merge revision, target path, and bundle SHA-256.

The test exits non-zero if any assertion fails.

- [ ] **Step 2: Run the smoke test and verify the expected initial failure**

Run:

```bash
bash tools/repo/migration/test-import-owner.sh
```

Expected: FAIL because `import-owner.sh` does not yet exist.

- [ ] **Step 3: Implement the helper as a thin Git wrapper**

`import-owner.sh` must:

- require exactly five arguments: `ID SOURCE REVISION TARGET TARGET_ROOT`;
- fail if `TARGET_ROOT` is not a Git repository;
- fail if `REVISION` is not a commit in `SOURCE`;
- create `/root/ordivon-migration-backups/2026-09-20/ID.bundle` with `git bundle create --all` if it does not already exist;
- verify the bundle;
- clone `SOURCE` with `--no-local --no-tags` into `/root/ordivon-migration-tmp/import-ID`;
- create local branch `import-main` at the exact `REVISION`;
- remove the clone's origin;
- run:
  `git filter-repo --refs refs/heads/import-main --to-subdirectory-filter TARGET --force`;
- copy `.git/filter-repo/commit-map` to `TARGET_ROOT/docs/migration/receipts/ID.commit-map`;
- add the filtered clone as temporary remote `import-ID`;
- fetch `import-main`;
- record the fetched rewritten tip;
- merge it with `--allow-unrelated-histories --no-ff`;
- compare source and rewritten target tree entries with `git ls-tree -r`;
- write `TARGET_ROOT/docs/migration/receipts/ID.md` with exact source path, source revision, rewritten revision, merge revision, target path, bundle path and bundle SHA-256;
- remove the temporary remote;
- retain the disposable clone until the caller accepts the receipt.

No owner-native tests are embedded in this helper; those remain explicit caller responsibilities.

- [ ] **Step 4: Run the helper smoke test**

Run:

```bash
bash tools/repo/migration/test-import-owner.sh
```

Expected: PASS.

- [ ] **Step 5: ShellCheck the migration scripts**

Run:

```bash
shellcheck tools/repo/migration/import-owner.sh tools/repo/migration/test-import-owner.sh
```

Expected: no findings.

- [ ] **Step 6: Commit the temporary migration helper**

Run:

```bash
git add tools/repo/migration/import-owner.sh tools/repo/migration/test-import-owner.sh
git commit -m "chore: add temporary history import harness"
```

---

### Task 7: M1 canary import — Next

**Files:**
- Import into: `meta/next/**`
- Create receipt: `docs/migration/receipts/next.md`
- Create commit map: `docs/migration/receipts/next.commit-map`

**Interfaces:**
- Consumes: accepted `migration/monorepo-m0-next` revision from Task 2.
- Produces: Next history under `meta/next`.

- [ ] **Step 1: Resolve the exact accepted source revision**

Run:

```bash
NEXT_IMPORT="$(git -C /root/projects/ordivon-next rev-parse migration/monorepo-m0-next)"
git -C /root/projects/ordivon-next merge-base --is-ancestor \
  ae1ac43130f95b264d908f7c73f268809300c0ea "$NEXT_IMPORT"
```

Expected: exit 0.

- [ ] **Step 2: Import**

Run from `/root/projects/ordivon`:

```bash
tools/repo/migration/import-owner.sh \
  next \
  /root/projects/ordivon-next \
  "$NEXT_IMPORT" \
  meta/next \
  /root/projects/ordivon
```

Expected: merge commit created and tree comparison passes.

- [ ] **Step 3: Verify Next from its new root**

Run:

```bash
cd /root/projects/ordivon/meta/next
uv python install
uv lock --check
uv sync --locked
uv run --locked python -m pytest
uv run --locked --group quality ruff check scripts tests
uv run --locked --group quality ruff format --check scripts tests
uv run --locked --group authority python scripts/check_authority_catalog_r1.py
uv run --locked --group authority python scripts/check_standard_native_enterprise_r2.py
uv run --locked --group reasoning python scripts/check_reasoning_waist_r1.py
```

Expected: all exit 0.

- [ ] **Step 4: Commit the generated receipt files if not already included by the import merge**

Run:

```bash
cd /root/projects/ordivon
git add docs/migration/receipts/next.md docs/migration/receipts/next.commit-map
git commit -m "docs: record Next monorepo import provenance"
```

Expected: receipt commit contains no owner source changes.

---

### Task 8: M1 canary import — Security

**Files:**
- Import into: `platform/security/**`
- Create corresponding receipt and commit map.

- [ ] **Step 1: Import exact Security baseline**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh \
  security \
  /root/projects/ordivon-security-v2 \
  f5db8508857ee844323f145891fb9cb832b12785 \
  platform/security \
  /root/projects/ordivon
```

Expected: tree equality passes.

- [ ] **Step 2: Run Security owner-native checks from the new root**

Run:

```bash
cd /root/projects/ordivon/platform/security
uv python install 3.14.7
uv sync --frozen --python 3.14.7
uv run --frozen --python 3.14.7 ruff check .
uv run --frozen --python 3.14.7 python -m unittest discover -s tests -v
uv run --frozen --python 3.14.7 python scripts/validate_threat_model_binding.py \
  threat-models/security-v2-r1.json --repo-root .
./scripts/validate_tmbom.sh threat-models/security-v2-r1.json
```

Expected: all exit 0.

- [ ] **Step 3: Commit receipt files**

Run:

```bash
cd /root/projects/ordivon
git add docs/migration/receipts/security.md docs/migration/receipts/security.commit-map
git commit -m "docs: record Security monorepo import provenance"
```

---

### Task 9: M1 canary import — Network

**Files:**
- Import into: `platform/network/**`
- Create corresponding receipt and commit map.

- [ ] **Step 1: Resolve accepted Network migration revision**

Run:

```bash
NETWORK_IMPORT="$(git -C /root/projects/ordivon-network-v2 rev-parse migration/monorepo-preclean)"
test "$NETWORK_IMPORT" = "9aec70bbfa3c8847dbd52c03a939c61f45e2f338"
```

Expected: exact candidate SHA.

- [ ] **Step 2: Import**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh \
  network \
  /root/projects/ordivon-network-v2 \
  "$NETWORK_IMPORT" \
  platform/network \
  /root/projects/ordivon
```

Expected: tree equality passes.

- [ ] **Step 3: Validate the imported Network source without mutating live state**

Run:

```bash
cd /root/projects/ordivon/platform/network
task all:validate
```

Expected: exit 0.

- [ ] **Step 4: Commit receipt files**

Run:

```bash
cd /root/projects/ordivon
git add docs/migration/receipts/network.md docs/migration/receipts/network.commit-map
git commit -m "docs: record Network monorepo import provenance"
```

---

### Task 10: Establish root ownership and thin monorepo task navigation after the canary

**Files:**
- Create: `.github/CODEOWNERS`
- Create: `mise.toml`
- Create: `meta/next/mise.toml` only if Next has no imported mise config.
- Create: `platform/network/mise.toml` only if Network has no imported mise config.
- Reuse: `platform/security/mise.toml` if already present.

**Interfaces:**
- Consumes: three accepted canary owners.
- Produces: source-navigation/task namespace only; no new build authority.

- [ ] **Step 1: Create CODEOWNERS**

Write:

```text
* @zycxfyh

/meta/next/ @zycxfyh
/platform/network/ @zycxfyh
/platform/security/ @zycxfyh
/services/ @zycxfyh
/capabilities/ @zycxfyh
/domains/ @zycxfyh
/studies/ @zycxfyh
/tools/repo/ @zycxfyh
```

- [ ] **Step 2: Create root mise monorepo configuration**

Write:

```toml
monorepo_root = true

[monorepo]
config_roots = [
  "meta/next",
  "platform/network",
  "platform/security",
]
lockfile = false
```

- [ ] **Step 3: Add a Next verify wrapper only if the imported Next tree lacks `mise.toml`**

Use:

```toml
[tasks.verify]
run = """
set -euo pipefail
uv lock --check
uv sync --locked
uv run --locked python -m pytest
uv run --locked --group authority python scripts/check_authority_catalog_r1.py
uv run --locked --group authority python scripts/check_standard_native_enterprise_r2.py
uv run --locked --group reasoning python scripts/check_reasoning_waist_r1.py
"""
```

- [ ] **Step 4: Add a Network verify wrapper only if the imported Network tree lacks `mise.toml`**

Use:

```toml
[tasks.verify]
run = "task all:validate"
```

- [ ] **Step 5: Ensure Security exposes a non-mutating verify task**

If its imported `mise.toml` lacks `verify`, add:

```toml
[tasks.verify]
run = """
set -euo pipefail
uv sync --frozen --python 3.14.7
uv run --frozen --python 3.14.7 ruff check .
uv run --frozen --python 3.14.7 python -m unittest discover -s tests -v
"""
```

- [ ] **Step 6: Prove namespaced task discovery**

Run:

```bash
cd /root/projects/ordivon
mise tasks
mise //meta/next:verify
mise //platform/security:verify
mise //platform/network:verify
```

Expected: all three owner tasks resolve and pass using their own config roots.

- [ ] **Step 7: Commit root navigation**

Run:

```bash
git add .github/CODEOWNERS mise.toml \
  meta/next/mise.toml platform/network/mise.toml platform/security/mise.toml
git commit -m "chore: add monorepo owner navigation"
```

Use `git add` only for files that actually changed.

---

### Task 11: M2 import Workstation without changing its live service path

**Files:**
- Import: `platform/workstation/**`
- Do not edit `/etc/systemd/system/ordivon-edge-gc.service` in this task.

- [ ] **Step 1: Import stable Workstation main**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh \
  workstation \
  /root/projects/ordivon-workstation-v2 \
  1ee414a9fcf40ce69c8fe53235134e3f55a5eee7 \
  platform/workstation \
  /root/projects/ordivon
```

- [ ] **Step 2: Verify from new path**

Run:

```bash
cd /root/projects/ordivon/platform/workstation
uv python install 3.14.7
uv lock --check
uv sync --locked
uv run ruff check .
uv run python -m pytest
```

Expected: PASS.

- [ ] **Step 3: Record but do not switch the live `ordivon-edge-gc.service` path**

Run:

```bash
grep -nF '/root/projects/ordivon-workstation-v2/providers/cloudflare' \
  /etc/systemd/system/ordivon-edge-gc.service
```

Expected: old source path still present; source import has no live effect.

---

### Task 12: M2 import Distribution, Media, and Artifact as separate commits

**Files:**
- Import `capabilities/distribution/**`
- Import `capabilities/media/**`
- Import `capabilities/artifact/**`

- [ ] **Step 1: Import accepted Distribution candidate and verify**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh distribution \
  /root/projects/ordivon-distribution-v2 \
  3f206409989e9274c1645ec25416df61b1662bff \
  capabilities/distribution /root/projects/ordivon
cd capabilities/distribution
uv python install 3.14.7
uv lock --check
uv sync --locked
bash scripts/test-all.sh
```

- [ ] **Step 2: Import accepted Media candidate and verify**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh media \
  /root/projects/ordivon-media \
  30f6d1228a4270a68cd715ca9a7b17742478958e \
  capabilities/media /root/projects/ordivon
cd capabilities/media
uv python install 3.14.7
pnpm install --frozen-lockfile
pnpm bootstrap:python
.venv/bin/ruff check .
pnpm check
```

- [ ] **Step 3: Import current Artifact main unchanged and verify**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh artifact \
  /root/projects/ordivon-artifact-v2 \
  3762b3f033f1173aa93609c79284980610301d37 \
  capabilities/artifact /root/projects/ordivon
cd capabilities/artifact
uv python install 3.14.7
uv lock --check
uv sync --locked
uv run python -m pytest -m "not integration"
```

Expected: all three owner-native verification paths pass.

- [ ] **Step 4: Prove Artifact production remains on the old source path**

Run:

```bash
systemctl cat ordivon-artifact-temporal-worker.service \
  | grep -F '/root/projects/ordivon-artifact-v2'
```

Expected: old path remains until the separate cutover task.

---

### Task 13: M3 import Game and Capital without unifying their toolchains

**Files:**
- Import `domains/game/**`
- Import `domains/capital/**`

- [ ] **Step 1: Import Game and run its native checks**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh game \
  /root/projects/ordivon-game \
  a4fdaa065f8daee963154c4647a920c6bc9e75a5 \
  domains/game /root/projects/ordivon
cd domains/game
pnpm install --frozen-lockfile
pnpm check
```

The full Playwright E2E remains an owner-native CI/acceptance check; run `pnpm e2e` when the browser dependency is installed for the migration gate.

- [ ] **Step 2: Import Capital and run its native checks**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh capital \
  /root/projects/ordivon-market-capital-next \
  8590c3eeb7d2712a1f796a70c839a7d3cbda0ff8 \
  domains/capital /root/projects/ordivon
cd domains/capital
uv python install 3.14.7
uv lock --check
uv sync --locked --group test
uv run --group test ruff check .
uv run --group test python -m pytest
```

Expected: Game and Capital retain independent pnpm/uv locks and pass their own checks.

---

### Task 14: M4 import Host as an independent service owner

**Files:**
- Import `services/host/**`

- [ ] **Step 1: Import exact Host source**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh host \
  /root/projects/ordivon-host-v2 \
  a95a8e112edfbe85582ff8e6fa25bb268038ea48 \
  services/host /root/projects/ordivon
```

- [ ] **Step 2: Verify Host build/tests from new source root**

Run:

```bash
cd /root/projects/ordivon/services/host
uv python install 3.14.7
uv lock --check
uv sync --locked
uv run ruff check .
uv run python -m pytest
```

- [ ] **Step 3: Prove source co-location did not change production**

Run:

```bash
readlink -f /opt/ordivon/host-v2/current
systemctl is-active --quiet ordivon-host-v2.service
```

Expected: production still resolves to the previously deployed immutable Host release.

---

### Task 15: M4 import the accepted Python 3.14.7 Harness main, then reconstruct reduction separately

**Files:**
- Import `services/harness/**`
- Later semantic CL may remove owner-misplaced capability islands.
- Do not extract Skills in the import commit.

- [ ] **Step 1: Import the independently accepted Harness Python 3.14.7 main exactly**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh harness \
  /root/projects/ordivon-harness \
  f747f6d3f513e76530d9777725a6727351c47dc8 \
  services/harness /root/projects/ordivon
```

- [ ] **Step 2: Verify Harness from its own pinned Python 3.14.7 environment**

Run:

```bash
cd /root/projects/ordivon/services/harness
uv sync --locked
uv run python scripts/check_runtime_search_profile.py
uv lock --check
uv run python -m compileall -q src tests scripts evals
uvx ruff==0.15.17 check src tests scripts
uv run python -W error::ResourceWarning -m pytest -q tests
uv run python scripts/check_dependencies.py
uv run python scripts/check_docs.py
uv run python scripts/check_evidence.py
uv run python scripts/demo_deterministic_run.py
```

Expected: PASS on Python 3.14.7 using Harness's own locked environment; no sibling owner's virtual environment or lockfile is used.

- [ ] **Step 3: Create a separate reduction branch from the imported monorepo**

Run:

```bash
cd /root/projects/ordivon
git switch -c refactor/harness-capability-islands
```

The reduction must be reconstructed from the intent of `660915590357d7122d7466a23cacd14f1a40bda9`, not merged blindly. Its acceptance requires the Harness checks above plus explicit Skills/Browser consumer revalidation. Do not mix this branch with further history imports.

---

### Task 16: M4 import Runtime while retaining its Cargo workspace and release authority

**Files:**
- Import `services/runtime/**`

- [ ] **Step 1: Return to monorepo main after the Harness reduction branch has been reviewed or parked**

Run:

```bash
cd /root/projects/ordivon
git switch main
git status --short
```

Expected: clean main.

- [ ] **Step 2: Import Runtime**

Run:

```bash
tools/repo/migration/import-owner.sh runtime \
  /root/projects/ordivon-runtime \
  9d8bf81b446aca5cf675e49af52a9d65c04533ab \
  services/runtime /root/projects/ordivon
```

- [ ] **Step 3: Verify Runtime from its new root**

Run:

```bash
cd /root/projects/ordivon/services/runtime
cargo fmt --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-targets --all-features
cargo test -p ordivon-runtime-core --no-default-features --features transactional-runtime
python -m unittest discover -s scripts/tests -v
python scripts/check_docs.py
scripts/local-acceptance check
```

Expected: PASS.

- [ ] **Step 4: Verify no root Cargo workspace was created**

Run:

```bash
test ! -e /root/projects/ordivon/Cargo.toml
test -e /root/projects/ordivon/services/runtime/Cargo.toml
test -e /root/projects/ordivon/services/runtime/Cargo.lock
```

Expected: exit 0.

---

### Task 17: M5 import Research without altering scientific bytes

**Files:**
- Import `capabilities/research/**`
- Preserve Research data/research_objects/results exactly.

- [ ] **Step 1: Freeze the exact Research import revision immediately before migration**

Run:

```bash
test "$(git -C /root/projects/ordivon-research-v2 status --porcelain)" = ""
RESEARCH_IMPORT="$(git -C /root/projects/ordivon-research-v2 rev-parse main)"
printf '%s\n' "$RESEARCH_IMPORT"
```

If this differs from the M0 baseline `39f586bd1d956f7206c9e0e04f8b02e30fa1eab0`, append the new exact source revision to a migration receipt before import; do not silently use the stale baseline.

- [ ] **Step 2: Import the frozen revision**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh research \
  /root/projects/ordivon-research-v2 \
  "$RESEARCH_IMPORT" \
  capabilities/research /root/projects/ordivon
```

- [ ] **Step 3: Verify Research**

Run:

```bash
cd /root/projects/ordivon/capabilities/research
uv python install 3.14.7
uv lock --check
uv sync --locked --extra dev
uv run --extra dev ruff check src tooling tests discovery research
uv run --extra dev python -m pytest -q
```

- [ ] **Step 4: Compare the largest frozen source objects by Git blob identity**

Run:

```bash
git -C /root/projects/ordivon-research-v2 ls-tree -r "$RESEARCH_IMPORT" \
  research_objects papers results > /tmp/research-old-tree.txt
git -C /root/projects/ordivon ls-tree -r \
  "$(git rev-parse HEAD):capabilities/research" \
  research_objects papers results > /tmp/research-new-tree.txt
diff -u /tmp/research-old-tree.txt /tmp/research-new-tree.txt
```

Expected: no content/mode/path differences within the imported Research subtree.

---

### Task 18: M5 import Paper2 as a scientific authority

**Files:**
- Import `studies/paper2/**`

- [ ] **Step 1: Import exact Paper2 source**

Run:

```bash
cd /root/projects/ordivon
tools/repo/migration/import-owner.sh paper2 \
  /root/projects/ordivon-paper2 \
  fd0fef6b0ed4b792f784726d2632551d6d5fd2b0 \
  studies/paper2 /root/projects/ordivon
```

- [ ] **Step 2: Run Paper2 method-tooling checks**

Run:

```bash
cd /root/projects/ordivon/studies/paper2
uv python install 3.14.7
uv lock --project tools/paper2 --check
uv sync --project tools/paper2 --locked --group dev
uv run --project tools/paper2 ruff check . --config tools/paper2/pyproject.toml
uv run --project tools/paper2 python -m pytest -q tests
```

Expected: PASS.

- [ ] **Step 3: Preserve scientific-source identity**

Run:

```bash
git -C /root/projects/ordivon-paper2 ls-tree -r \
  fd0fef6b0ed4b792f784726d2632551d6d5fd2b0 \
  screening campaigns sampling discovery \
  > /tmp/paper2-old-tree.txt
git -C /root/projects/ordivon ls-tree -r \
  "$(git rev-parse HEAD):studies/paper2" \
  screening campaigns sampling discovery \
  > /tmp/paper2-new-tree.txt
diff -u /tmp/paper2-old-tree.txt /tmp/paper2-new-tree.txt
```

Expected: no difference.

---

### Task 19: M6 extract Paper1/Paper3 from imported Research using normal Git moves

**Files:**
- Move only Research-owned study paths proven to belong to Paper1/Paper3.
- Target: `studies/paper1/**`, `studies/paper3/**`

**Interfaces:**
- Consumes: already-imported Research history.
- Produces: clearer current source placement without a second history rewrite.

- [ ] **Step 1: Produce an exact path census before moving anything**

Run:

```bash
cd /root/projects/ordivon
find capabilities/research -type f \
  \( -path '*first_paper*' -o -path '*paper1*' -o -path '*paper3*' \) \
  -print | sort > /tmp/research-study-paths.txt
cat /tmp/research-study-paths.txt
```

- [ ] **Step 2: Compare Paper1 candidates against the frozen Paper1 checkout by Git blob identity**

For each candidate path, use `git ls-tree`/blob OIDs. Only paths whose study ownership and lineage are proven move in this task. Shared Research tooling remains under `capabilities/research`.

- [ ] **Step 3: Perform only Git moves**

Run `git mv` for the proven study-owned directories. Do not edit file contents in the same commit.

- [ ] **Step 4: Re-run Research and paper-specific checks**

Run the Research verify commands from Task 17 and the available Paper1/Paper3 manuscript/artifact checks.

- [ ] **Step 5: Commit path-only extraction**

Run:

```bash
git diff --check
git diff --summary
git commit -am "refactor: separate research studies from shared capability"
```

Expected: commit contains moves/renames only, with no scientific byte edits.

---

### Task 20: M6 extract Skills from Harness as a separate owner migration

**Files:**
- Move: `services/harness/src/ordivon_harness/skills/**`
- Move/adapt: Skills MCP source/config/tests required for the new owner
- Target: `platform/skills/**`

**Interfaces:**
- Consumes: imported Harness and current live Skills MCP consumer contract.
- Produces: Skills owner package independent of Harness Run core.

- [x] **Step 1: Freeze the current Skills MCP release identity**

Run:

```bash
readlink -f /opt/ordivon/skills-mcp/current
```

Record the exact release path in the migration receipt.

- [x] **Step 2: Move source without redesigning semantics**

Use `git mv` for the Skills package and its owner-specific tests/config. Preserve parser/catalog/scanner/eligibility behavior.

- [x] **Step 3: Update imports and package metadata minimally**

Only update the package/import coordinates required by the move. Do not change trust, eligibility, scan, resolution, or precedence semantics in this commit.

- [x] **Step 4: Run the existing Skills tests**

Run the migrated equivalents of:

```text
tests/test_skill_catalog_r2.py
tests/test_skills_mcp_r2.py
tests/test_skills_mcp_r3.py
tests/test_skills_sep2640.py
tests/test_skillspector_adapter.py
```

Expected: PASS.

- [x] **Step 5: Verify Harness core tests still pass without importing Skills internals**

Run Harness verification from Task 15.

Expected: PASS.


**Accepted 2026-09-21:** source/owner extraction is recorded in
docs/migration/acceptance/SKILLS_M6_OWNER_EXTRACTION_ACCEPTANCE_20260921.md.
Production Skills MCP remains on the pre-M6 release and is intentionally deferred to Task 24.

---

### Task 21: M6 classify and retire workstation-lab without wholesale import

**Files:**
- Source only: `/root/workstation-lab`
- Targets determined by existing natural owner paths.
- Archive: verified `workstation-lab.bundle`.

- [ ] **Step 1: Freeze and resolve the four staged Creative Library changes before migration**

Run:

```bash
git -C /root/workstation-lab status --porcelain
git -C /root/workstation-lab diff --cached --stat
python -m unittest /root/workstation-lab/tests/test_creative_library.py
```

Expected staged set:

```text
M  artifacts/creative-library/catalog-v1.json
D  artifacts/creative-library/evidence/geospatial-carrier-friction-resolution-r1.json
M  scripts/creative_library.py
M  tests/test_creative_library.py
```

The observed delta removes the geospatial presentation-kind/carrier path and contracts the catalog (7 insertions / 437 deletions). Resolve this as its own semantic change: if its tests and owning Creative Library acceptance pass, commit it to workstation-lab history before migration; otherwise reset/reject it explicitly. Do not transplant or force-clean these staged bytes as part of repository relocation.

- [ ] **Step 2: Prove the full bundle exists and verifies**

Run:

```bash
git -C /root/workstation-lab bundle verify \
  /root/ordivon-migration-backups/2026-09-20/workstation-lab.bundle
sha256sum -c /root/ordivon-migration-backups/2026-09-20/SHA256SUMS \
  --ignore-missing
```

- [ ] **Step 3: Classify tracked top-level ownership**

Use current owner boundaries:

- node/substrate/recovery → `platform/workstation`;
- Media/creative production → `capabilities/media`;
- Game product/research → `domains/game`;
- Paper2 scientific material already canonical in `studies/paper2`;
- obsolete governance/history → remain only in archived workstation-lab history.

- [ ] **Step 4: Migrate only still-live unique bytes with Git-native provenance**

Each migrated residue is its own commit in the natural target owner and records source commit/path in the commit message or migration receipt.

- [ ] **Step 5: Mark workstation-lab read-only only after no current consumer/write path remains**

Do not delete the archived repository or bundle.

---

### Task 22: M7 cut over Workstation edge-gc to monorepo source/release

**Files/effects:**
- New source: `platform/workstation/providers/cloudflare`
- Live unit: `ordivon-edge-gc.service`

- [ ] **Step 1: Build/verify from the exact monorepo revision using Workstation's existing provider release path**

Use the existing Workstation Cloudflare release script from the new source tree; do not create a new deployment mechanism.

- [ ] **Step 2: Update the systemd source path through Workstation-owned desired state**

Do not hand-edit a generated/live file if Ansible/provider desired state already owns it.

- [ ] **Step 3: Reload and read back**

Run:

```bash
systemctl daemon-reload
systemctl cat ordivon-edge-gc.service
systemctl is-active --quiet ordivon-edge-gc.service
```

Expected: unit references the monorepo-derived release/source contract and remains active.

- [ ] **Step 4: Preserve rollback**

Keep the prior unit/release generation until consumer validation passes.

---

### Task 23: M7 cut over Artifact Temporal worker

**Files/effects:**
- New source: `capabilities/artifact`
- Live unit: `ordivon-artifact-temporal-worker.service`

- [ ] **Step 1: Build the Artifact worker/release from an exact monorepo revision**

Use Artifact's existing Temporal deployment script; do not point production at a mutable arbitrary worktree if the owner supports an immutable release path.

- [ ] **Step 2: Switch the unit through owner-native deployment**

The resulting unit must no longer use:

```text
/root/projects/ordivon-artifact-v2
```

- [ ] **Step 3: Read back service identity and health**

Run:

```bash
systemctl cat ordivon-artifact-temporal-worker.service
systemctl is-active --quiet ordivon-artifact-temporal-worker.service
systemctl status --no-pager ordivon-artifact-temporal-worker.service
```

- [ ] **Step 4: Execute one real Artifact consumer validation**

Use an existing deterministic Artifact build/verification workload. Mechanical worker liveness alone is not consumer acceptance.

---

### Task 24: M7 cut over Skills MCP source bindings

**Files/effects:**
- New source owner: `platform/skills`
- Live release: `/opt/ordivon/skills-mcp/current`

- [ ] **Step 1: Build a new Skills MCP immutable release from the monorepo**

Use existing Skills release semantics and exact source revision binding.

- [ ] **Step 2: Ensure release/config contains no active dependency on old source paths**

Run:

```bash
grep -R -nF '/root/projects/ordivon-next/.agents/skills' \
  /opt/ordivon/skills-mcp/current/config \
  /opt/ordivon/skills-mcp/current/scripts \
  /opt/ordivon/skills-mcp/current/src 2>/dev/null && exit 1 || true
grep -R -nF '/root/projects/ordivon-harness' \
  /opt/ordivon/skills-mcp/current/config \
  /opt/ordivon/skills-mcp/current/scripts \
  /opt/ordivon/skills-mcp/current/src 2>/dev/null && exit 1 || true
```

- [ ] **Step 3: Exercise real Skills consumer surfaces**

Verify current `skills.search`, `skills.resolve`, and `skills.read` against an Ordivon project context, including exact snapshot/instruction/package revision fences.

Expected: successful resolution from monorepo-owned source bindings.

---

### Task 25: Consolidate GitHub governance without collapsing owner CI

**Files:**
- Create/update: root `.github/CODEOWNERS`
- Create/update: root `.github/workflows/ci.yml`
- Create/update: root `.github/dependabot.yml`
- Preserve owner-specific release workflows only where they remain independently meaningful.

- [ ] **Step 1: Keep one always-running required root workflow**

The root workflow itself runs on every PR to `main`; do not put `paths:` on the required workflow.

- [ ] **Step 2: Use conditional steps/jobs inside the running workflow or mise affected selection**

This avoids GitHub's documented behavior where a path-filtered required workflow can stay Pending when skipped.

- [ ] **Step 3: Preserve pinned actions already accepted by owners**

Reuse existing pinned SHAs for checkout/setup-uv/setup-node/pnpm/rust actions when moving equivalent CI logic. Do not silently replace them with floating tags.

- [ ] **Step 4: Require the root verification check via GitHub ruleset after it is green on the monorepo**

Also block force-push to `main`.

---

### Task 26: Archive old source repositories only after per-owner retirement acceptance

**Files/effects:**
- Original repositories remain available read-only.
- Bundles remain under `/root/ordivon-migration-backups/2026-09-20`.

- [ ] **Step 1: For each old source, prove all applicable gates**

Required evidence per owner:

```text
SOURCE_ACCEPTED
BOUNDARY_ACCEPTED
RELEASE_ACCEPTED          # when owner has a release
CONSUMER_ACCEPTED         # when owner has live consumers
ROLLBACK_RECORDED
NO_UNRESOLVED_DIRTY_WORK
```

- [ ] **Step 2: Remove temporary migration compatibility bridges**

A bridge has no standing once every consumer uses the monorepo-derived source/release.

- [ ] **Step 3: Remove temporary migration helper scripts**

Run after the final import:

```bash
cd /root/projects/ordivon
git rm -r tools/repo/migration
git commit -m "chore: retire completed monorepo migration harness"
```

- [ ] **Step 4: Remove the temporary baseline planning record**

Run only after its sunset condition is met:

```bash
git rm meta/next/planning/monorepo-migration-baseline-r1.json
git commit -m "docs: retire completed monorepo migration baseline"
```

If Next planning files were subsequently moved to root docs during normal source organization, remove the actual current path instead; do not duplicate the baseline.

---

## Final Acceptance

The migration is complete only when all of the following hold:

```text
ONE-SOURCE-TREE TEST: PASS
  Every active Ordivon source owner is reachable from the monorepo, except explicitly archived-only history.

AUTHORITY-SEPARATION TEST: PASS
  Runtime/Host/Harness/platform/domain/study truth boundaries remain independent.

ENVIRONMENT-SEPARATION TEST: PASS
  Harness and other Python owners may converge on Python 3.14.7 while still running from independent locked environments.

HISTORY-PRESERVATION TEST: PASS
  Every imported source has verified bundle + commit-map + tree-equality evidence.

LIVE-CUTOVER TEST: PASS
  Old source paths are absent from active services/consumers where cutover applies.

SCIENTIFIC-PRESERVATION TEST: PASS
  Research/Paper frozen source and result bytes retain provenance and identity.

ROOT-THINNESS TEST: PASS
  No universal Ordivon state/task/evidence/gate/registry/workflow framework was introduced.

ROLLBACK TEST: PASS
  Original bundle/repository and previous release generation remain sufficient to recover each migrated owner until retirement acceptance.

MIGRATION-INFRA-SUNSET TEST: PASS
  Temporary import helpers and the temporary baseline record are removed after they stop changing decisions.
```
