# Skill MCP R2 — auxiliary Phase A handoff

Date: 2026-09-16
Workspace: `ws-skill-mcp-r2-aux-20260916`
Base: `ordivon-harness@0400157eb8295a26e7c12d1fa7d13d76e6cd18aa`
Status: **tested implementation slice; not yet MCP transport**

## What this slice proves

This branch materializes the first catalog correctness layer proposed by the Ordivon Next `SKILL_MCP_R2_DESIGN.md` without creating a second execution or trust authority.

Implemented:

- typed `SkillSource`, `SkillRecord`, `TrustState`, and `EligibilityState`;
- conservative Agent Skills frontmatter extraction for required `name` + `description`;
- multi-source filesystem discovery;
- canonical namespaced identity `skillId = <sourceId>/<name>`;
- collision-preserving raw inventory plus a separately filtered effective view;
- distinct `catalogRevision` for raw inventory and `snapshotRevision` for the effective view;
- deterministic friendly-name resolution by source priority;
- explicit fully-qualified identity resolution;
- exact SHA-256 instruction digest;
- lexical metadata search;
- digest-fenced `SKILL.md` read;
- relative resource containment and path-escape rejection;
- blocked/untrusted/quarantined entries retained in raw inventory but excluded from the default effective view.

Not implemented in this slice:

- context-specific workspace/project applicability;
- independent scope-precedence policy beyond configured source priority;
- scanner/quarantine evidence production;
- environment/tool eligibility probes;
- per-agent visibility/allowlists;
- package manifests / package revision;
- filesystem watch + atomic publication;
- MCP tools/resources/transports;
- operator control plane;
- immutable historical package retention.

Those should remain later slices rather than being hidden in this foundation.

## Local dogfood evidence

The catalog was run against the currently present machine roots:

```text
/root/projects/ordivon/meta/next/.agents/skills
/root/.codex/skills
/root/.agents/skills
/root/.hermes/skills
/root/.local/share/ordivon/vendor/obra-superpowers-main/skills
```

Observed raw inventory:

```text
ordivon-next       3
codex-user        20
generic-user       2
hermes-user      118
obra-superpowers  14
--------------------
total            157
```

Observed real friendly-name collisions:

```text
artifact-work
browser-use
requesting-code-review
systematic-debugging
test-driven-development
web-provider-routing
```

This directly validates the R2 identity decision: destructive first-wins dedupe at inventory time would already discard real local candidates.

Example current binding under the test priorities:

```text
test-driven-development
  hermes-user/test-driven-development
  obra-superpowers/test-driven-development

winner: hermes-user/test-driven-development
reason: source-priority
```

A caller can still explicitly resolve `obra-superpowers/test-driven-development`, so source-qualified identity bypasses friendly-name precedence as intended.

## Verification

Behavior/security test module:

```text
tests/test_skill_catalog_r2.py
```

Current result:

```text
12 tests passed
compileall passed
ruff passed
```

Covered cases include:

- multiple same-name candidates retained;
- explicit source-qualified selection;
- blocked/untrusted candidates retained in raw inventory but excluded from effective resolution;
- raw `catalogRevision` separated from effective `snapshotRevision`;
- deterministic snapshot identity;
- snapshot change after instruction-byte change;
- stale instruction digest failure;
- `../` resource escape rejection;
- symlinked external `SKILL.md` exclusion;
- search ordering baseline;
- required frontmatter validation.

Runtime verification jobs:

```text
job-01a0a921-fd46-7a90-b3e6-f7b22ab333fa  # first 11-test slice OK
job-01a0a922-cfb1-7152-a0dd-2797dedb5625  # real five-source dogfood
job-01a0a926-4f60-7bd0-a23d-a2c0eafbfcf9  # final 12 tests + compileall + ruff OK
```

## Protocol correction for the controller

Do not conflate MCP protocol cache hints with application-level catalog snapshots.

MCP 2026-07-28 standardizes `ttlMs` / `cacheScope` on protocol list/resource-read results such as `tools/list`, `prompts/list`, `resources/list`, and `resources/read`. A custom tool named `skills.list` or `skills.search` is still a normal `tools/call`; its application payload does not automatically inherit protocol-level list caching semantics merely because the tool name contains `list`.

Therefore keep both layers explicit:

```text
MCP protocol discovery/resource caching
  -> ttlMs/cacheScope where the standard defines them

Skill application consistency
  -> catalogRevision/snapshotRevision/instructionDigest
```

The second layer is required even if every MCP SDK eventually implements the first perfectly.

## External implementation checks retained

Current Codex app-server documentation confirms:

- `skills/list` can be scoped by cwd;
- `forceReload` exists;
- local Skill changes emit `skills/changed` invalidation;
- explicit `skill` turn input is recommended to avoid model-side re-resolution latency.

Current OpenClaw documentation confirms:

- location precedence and agent allowlists are separate;
- eligibility gating includes OS/binary/env/config conditions;
- sessions snapshot selected Skill IDs/revisions;
- ordinary file-backed Skill refresh is applied on a later agent turn;
- managed revisions are retained independently of later publication changes.

These checks reinforce the existing R2 design rather than requiring a new abstraction.

## Recommended next controller slices

### B1 — context + policy

Add a `SkillContext` value with explicit `workspace_path/workspace_id/agent_id/invocation_mode`, then make project applicability, scope precedence, allowlists, and implicit/explicit policy testable without touching MCP.

### B2 — package/resource identity

Add bounded package manifest hashing, file-count/size ceilings, and exact resource digest fencing. Keep historical CAS retention deferred; stale reads may fail closed initially.

### B3 — MCP surface

Only after B1/B2 semantics are stable, map the catalog to exactly four model-facing tools:

```text
skills.list
skills.search
skills.resolve
skills.read
```

and `skill://<sourceId>/<skill-name>/<path>` resources.

### B4 — trust/refresh

Add project trust config, scanner diagnostics/quarantine, off-side catalog rebuild + atomic swap, watcher invalidation, and TTL-triggered full refresh.

### B5 — ChatGPT closure

Expose Streamable HTTP through the approved plugin/connector edge, then dogfood the explicit TDD path and one implicit Artifact path from a fresh conversation.

## Boundary law preserved

```text
Skill source owns bytes.
Agent Skills owns package semantics.
Skills catalog/MCP owns discovery + resolution + exact read projection.
Model owns relevance choice.
Operator owns trust/install.
Runtime/provider owns execution.
Domain owner owns semantic acceptance.
```
