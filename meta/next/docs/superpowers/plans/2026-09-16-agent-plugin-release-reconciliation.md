# Agent Plugin Release Reconciliation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote a standards-native Ordivon Agent Plugin release without making Agent Plugin the semantic owner of Skills, and separately reconcile the temporary Skill MCP bridge with current Agent Skills conformance.

**Architecture:** Keep Agent Skills, MCP Runtime/Host surfaces, and Agent Plugin packaging as separate standards-owned layers. The Agent Plugin materializer produces an MCP-only package by default and composes canonical `.agents/skills` only by explicit opt-in. The Skill MCP conformance candidate is reviewed on its own release line and is never merged merely because the Plugin release is ready.

**Tech Stack:** Python 3 stdlib, `unittest`, Git, Agent Plugins 1.0 schemas, Agent Skills, MCP, Hermes v0.21.3 validation/doctor.

**Spec:** `docs/AGENT_PLUGINS_ADOPTION_R1.md`

## Global Constraints

- External standards are canonical wherever applicable.
- `.agents/skills` remains the canonical source for project Agent Skills.
- Agent Plugin bundling is composition, not Skill semantic ownership.
- Default Plugin release omits Skills; Skill bundling requires explicit `--include-skills`.
- Portable Plugin files contain no credentials or private OAuth metadata.
- Runtime and Host remain their own semantic authorities behind MCP.
- Skill MCP remains temporary compatibility infrastructure and must not regrow registry/watcher/marketplace ownership.
- Canonical Git promotion uses fast-forward-only integration after focused and full gates pass.

---

### Task 1: Make Skill composition explicit

**Files:**
- Modify: `scripts/materialize_agent_plugin.py`
- Modify: `tests/test_agent_plugin_materialization.py`

**Interfaces:**
- Consumes: canonical Plugin skeleton `plugins/ordivon-control-plane/` and optional Skill source `.agents/skills/`.
- Produces: `materialize(plugin: Path, skills_root: Path | None, output: Path, receipt: Path) -> dict`, CLI flag `--include-skills`, receipt field `skillComposition`.

- [x] **Step 1: Write failing tests**

Add a test that calls `materialize(plugin, None, output, receipt)` and requires no generated `skills/`, `skillCount == 0`, `skillComposition == "omitted"`, and null Skill source fields. Add CLI parsing coverage proving `--include-skills` is opt-in.

- [x] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_agent_plugin_materialization`

Expected pre-implementation result: errors for missing `include_skills`, missing `skillComposition`, and attempting `.resolve()` on a null Skill source.

- [x] **Step 3: Implement the minimum composition change**

Allow `skills_root=None`, create no `skills/` component in that case, add `--include-skills`, preserve existing explicit Skill materialization behavior, and record included/omitted composition in the external receipt.

- [x] **Step 4: Verify GREEN**

Run: `python3 -m unittest tests.test_agent_plugin_materialization`

Expected: `9 tests`, `OK`.

### Task 2: Reconcile architecture documentation

**Files:**
- Modify: `docs/AGENT_PLUGINS_ADOPTION_R1.md`

**Interfaces:**
- Consumes: current public Skill MCP OAuth state and the user-approved boundary that Skill is an independent component.
- Produces: one release policy that distinguishes independent Skill ownership, optional Plugin composition, and temporary remote bridge behavior.

- [x] **Step 1: Remove the implicit Plugin-owns-Skills assumption**

Document `.agents/skills` as independently canonical Agent Skills and make Plugin `skills/` an optional release composition.

- [x] **Step 2: Correct stale Skill MCP status**

Replace the old public-promotion freeze with the current truth: `skills-mcp.ordivon.com` is an OAuth-protected temporary compatibility bridge whose public reachability does not make it canonical Skill architecture.

- [x] **Step 3: Add the evidence gate for the final Skill ↔ Plugin boundary**

Require native Skill discovery, Plugin lifecycle, bundled/non-bundled behavior, refresh, and coexistence evidence before changing the default composition policy.

### Task 3: Validate the Agent Plugin reconciliation candidate

**Files:**
- Verify: `plugins/ordivon-control-plane/plugin.json`
- Verify: `plugins/ordivon-control-plane/mcp.json`
- Verify: `scripts/materialize_agent_plugin.py`
- Verify: `tests/test_agent_plugin_materialization.py`

**Interfaces:**
- Consumes: reconciled candidate workspace.
- Produces: focused/full test receipts plus two native Hermes validation paths: MCP-only and explicit Skills composition.

- [x] **Step 1: Run Python syntax/lint/focused tests**

Run the repository's existing Python lint/compile gates plus `python3 -m unittest tests.test_agent_plugin_materialization`.

- [x] **Step 2: Build two deterministic release forms**

Build one default MCP-only release and one `--include-skills` release. Repeat both builds and compare output manifests/digests.

- [x] **Step 3: Validate both releases with Hermes**

Run `hermes plugins validate` and `hermes plugins doctor --ci` for both release forms.

- [x] **Step 4: Run the full Next test suite**

Use the same complete test command that previously established the candidate baseline and require zero failures.

**Task 3 completion evidence (2026-09-20):** repository materializer tests passed 12/12; MCP-only and explicit `--include-skills` releases were each built twice with stable tree digests; Hermes v0.21.3 `plugins validate` and `plugins doctor --ci` passed for both release forms; the complete Ordivon Next suite passed 354/354. This closes Plugin candidate validation only. It does not close the independent Skill MCP conformance or canonical-promotion tasks below.

### Task 4: Review Skill MCP upstream conformance separately

**Files:**
- Review candidate: `1c31b3b726b0c67e8e6a21e9bfeaa36bd44eb7a3`
- Potentially modify: `src/ordivon_harness/skills/parser.py`
- Potentially modify: `src/ordivon_harness/skills/sep2640.py`
- Potentially modify: `tests/test_skill_catalog_r2.py`
- Potentially modify: `tests/test_skills_sep2640.py`
- Potentially modify: `docs/SKILL_MCP_STANDARDS_ALIGNMENT.md`

**Interfaces:**
- Consumes: deployed Skill MCP release `04274874212e654099227ba33f183a5c0a4ad921`, current Agent Skills normative specification, and candidate `1c31b3b`.
- Produces: a bridge-only conformance candidate or an explicit rejection; no Agent Plugin coupling.

- [ ] **Step 1: Confirm current normative name rules**

Require the Agent Skills specification, not `skills-ref`, as authority. Verify Unicode lowercase alphanumeric + hyphen rules, NFKC-sensitive length/matching behavior, and optional frontmatter preservation.

- [ ] **Step 2: Apply/reconcile the candidate in an isolated workspace**

Cherry-pick or manually reconcile only the upstream-conformance changes onto the deployed Skill MCP release lineage; do not import unrelated platform behavior.

- [ ] **Step 3: Run focused and full Skill MCP gates**

Require the Unicode/NFKC/URI tests, existing SEP-2640 E2E, lint/compile gates, and full harness suite.

### Task 5: Promote only proven release lines

**Files:**
- Git refs only; no new feature files.

**Interfaces:**
- Consumes: green Agent Plugin reconciliation candidate and independently green Skill MCP conformance candidate.
- Produces: fast-forward canonical Next for the Agent Plugin line; Skill MCP promotion only if its own controller gates pass.

- [ ] **Step 1: Re-read canonical HEAD and clean state**

Require `/root/projects/ordivon-next` to remain at the expected ancestor or reconcile intervening commits before promotion.

- [ ] **Step 2: Fast-forward Agent Plugin candidate**

Use `git merge --ff-only` into canonical Next; reject merge commits or unrelated branch mixing.

- [ ] **Step 3: Re-run read-back verification from canonical**

Confirm exact HEAD, clean working tree, Plugin manifests, optional composition behavior, and focused tests from the canonical checkout.

- [ ] **Step 4: Update Host continuity**

Record canonical revision, gate receipts, remaining native-client E2E work, and leave the Skill ↔ Plugin default composition decision open until consumer evidence exists.
