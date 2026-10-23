# B05 — Agent Plugin R4 Selective Composition Acceptance

Date: 2026-09-21
Status: ACCEPTED HISTORICAL COMPOSITION CANDIDATE
Historical standing: SUPERSEDED BY C02/D01 FOR CURRENT ENDPOINT TOPOLOGY

> The endpoint statement in this B05 snapshot predates C02/D01. The current canonical Plugin declares exactly one Gateway MCP endpoint; see `CURRENT_ARCHITECTURE.md`.

## Decision

Agent Plugins remains a composition/distribution surface, not the semantic owner of Skills, MCP servers, Runtime, Host, or Workstation tool materialization.

B05 closes the demonstrated composition gap by extending the existing materializer with **explicit selected-Skill composition**.

Supported modes are now:

```text
MCP-only
selected canonical Skill(s)
explicit all-Skills compatibility composition
```

The selected mode is the preferred mechanism for task/release-specific composition. It avoids the previous false binary of "no Skills" versus "every Skill".

## Canonical ownership

- Skills remain canonical under `meta/next/.agents/skills`.
- MCP server definitions remain the portable Plugin capability surface.
- Workstation exact Tool Bindings remain node-local evidence owned by Workstation.
- Gateway capability projection remains disposable owner-derived data.
- Plugin release materialization copies selected canonical assets; it does not take semantic ownership.

## R4 candidate

A real candidate was materialized twice using:

```text
--skill method-router
```

Both runs produced the same package digest:

`sha256:048a75c739bc3fc1ed1c5f24c4343a56d954e010930b2d80dcc74ff533b5a136`

The package contains exactly four files:

```text
plugin.json
mcp.json
skills/method-router/SKILL.md
skills/method-router/references/method-map.md
```

No unrelated Skill and no node-local Tool Binding payload is present.

## Materializer contract

- `--skill NAME` is repeatable;
- names are deduplicated and sorted deterministically;
- selected names must exist in the canonical Agent Skills source;
- unknown names fail closed;
- `--skill` and `--include-skills` are mutually exclusive;
- historical MCP-only and explicit all-Skills modes remain supported;
- release receipt records `skillComposition=selected` and exact `skillSelection`.

Focused B05 + Method Router verification: 19/19 PASS.

## Local-tool extension verdict

**DO NOT ADD YET.**

Agent Plugins 1.0 permits reverse-domain client extensions, but extension data has client-specific rather than portable semantics. Current `ordivon-control-plane` has no concrete node-local tool requirement: its portable capability is still MCP, and Method Router is a standard Agent Skill.

Therefore B04 Tool Binding projection is **not** embedded in the Plugin merely because the data exists.

A future Ordivon extension is justified only when a concrete client/plugin requirement cannot be represented by Skills, MCP, or client-local configuration. If that occurs, the extension should carry requirement identifiers/constraints, never observed machine paths, credential material, or claims of current availability.

## Public endpoint boundary

The canonical Plugin source still references the existing Runtime/Host MCP endpoints. It is not switched to Gateway until C02 establishes the public Gateway edge authentication/route and connector cutover evidence.

R4 is therefore a composition candidate, not a public connector-cutover claim.
