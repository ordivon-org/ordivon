# D01 Compatibility Debt Retirement Acceptance — 2026-09-21

Status: **ACCEPTED**

D01 removes compatibility only after consumer evidence. It does not delete a surface merely because it is old, duplicated-looking, or no longer the default.

## Gates

The three prerequisite convergence gates are complete:

- C02: Gateway is the normal ChatGPT/remote northbound path and current-session execution → observation → artifact discovery → artifact read is proven.
- C03: Skill MCP is retired per consumer; local clients are native-Skill consumers while ChatGPT remains one exact bridge consumer.
- E03/R03: Host monorepo release packaging, live release reconciliation, schema identity, and tool-catalog identity are proven.

## Retired debt

### Default Agent Plugin direct-owner routing

`ordivon-control-plane` v0.2.0 now declares exactly one MCP server:

```text
ordivon-gateway → https://gateway-mcp.ordivon.com/mcp
```

The default portable package no longer declares public Runtime or Host endpoints.

### Codex direct Runtime configuration

The stale `ordivonRuntime → https://mcp.ordivon.com/mcp` entry was removed with Codex's native MCP CLI. The remaining Ordivon entry is `ordivonGateway`.

Both the old Runtime entry and the new Gateway entry were observed as `Not logged in`; removing the old entry did not discard an authenticated session. Gateway OAuth remains a client-local interactive action when Codex is next used.

### Hermes stale direct-owner Plugin installation

The installed `ordivon-control-plane` package under Hermes still contained Runtime+Host direct endpoints but was disabled. It was removed through `hermes plugins remove`. Future materialization uses the canonical Gateway-only package.

### Host standalone-repository packaging fallback

The canonical Host installer now requires `services/host/pyproject.toml` at the exact Git commit and archives only the `services/host` subtree. The fallback that treated an arbitrary standalone repository root as the Host package has been deleted.

Consumer evidence for deletion:

- no tracked caller requires standalone Host layout;
- no active /etc, systemd, or operator-script reference requires the old standalone source;
- `/root/projects/ordivon-host` is absent;
- R03 production deployment is already monorepo-native.

A fail-closed test first demonstrated RED against the old fallback, then passed after deletion.

## Deliberately retained surfaces

These are not D01 deletion targets:

- **Runtime direct MCP** — retained as an explicit operator/admin/recovery surface. It is no longer the default Agent Plugin or Codex distribution path.
- **Host direct MCP** — retained as an explicit operator/admin/recovery surface. It is no longer in the default Agent Plugin.
- **Skill MCP** — retained only for the exact ChatGPT filesystem-to-remote Skill projection proven by C03.
- **Agent Automation / Temporal / Browserless** — a separate live Harness/Workstation automation system, not the retired Agent Service implementation.
- **historical Agent Service research/evidence** — retained as provenance. The executable `agent_service/` implementation tree is already absent under C01.

All four public MCP surfaces currently return Cloudflare Access `401` to unauthenticated probes.

## Canonical verification

Verified from fresh canonical workspace at Git `649cdc78355b209bce57019899e44080542c01ae`:

- `mise run next:verify` — PASS;
- `mise run host:verify` — PASS, 20 tests passed and 18 skipped;
- `mise run repo:ci` — PASS;
- owner-boundary literal audit — PASS;
- composition-architecture check — PASS;
- integrate-main smoke — PASS;
- GitHub governance — PASS;
- Host installer remains executable mode `100755`.

Live regression evidence:

- Gateway reports Linux Runtime, Windows Runtime, and Host configured;
- `artifact.runtime`, `continuity.external`, `execution.linux`, and `execution.windows` are all available;
- Host PostgreSQL journal schema 5 and all doctor checks are healthy;
- Linux Runtime and Windows Runtime are configured/available at their native owners;
- Skill MCP catalog remains readable for the retained ChatGPT consumer;
- Gateway Linux Job `job-01a0c422-50a5-70a1-a64c-72d6d00d9352` succeeded with exit code 0;
- Gateway artifact discovery returned four artifact IDs and `artifact.read` returned `d01-live-smoke-ok`.

## Landing-safety correction

D01 also exposed a Git-mechanics bug in a synthetic concurrent replay: the validated Host installer blob was replayed with mode `100644` instead of its original executable mode `100755`. Fresh canonical Host verification caught this as `PermissionError`.

The source blob was unchanged. Canonical mode was repaired to `100755`, and the complete canonical verification suite then passed. Future synthetic tree replays must preserve each source entry's original tree mode rather than hard-coding `100644`.

## Result

The normal client/distribution topology is now:

```text
Agent client / portable Agent Plugin
              ↓
           Gateway
       ┌──────┼──────┐
       ↓      ↓      ↓
 Linux Runtime   Windows Runtime   Host
```

Compatibility remains only where a current consumer or recovery role is explicitly proven.
