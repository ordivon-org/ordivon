# Agent Automation owner migration R7

Date: 2026-09-14

Harness becomes the source/release authority for Agent Automation. Workstation v2 retains only the stable node-local `/root/tools/bin/agent-automation` carrier and its shared admission lease; Runtime remains execution truth; Network v2 remains Browserless transport authority; Browserless/Temporal/Podman remain their own substrate authorities.

The migration source baseline is legacy Workstation commit `dc698bde912dcab09a80c93a53c97f51582a879d`. Production remains on immutable legacy release `cdaa5112594917fd21312e5b1a4da5cc99a8ef91` until a committed Harness candidate passes focused tests, Harness regression tests, exact runtime import preflights, materialization checks, and quiescent release activation.

`config/agent-automation.toml` replaces the former dependency on global `workstation.toml`; only the `agent_automation` and `browserless_network` coordinates required by this owner are retained. Release materialization archives an explicit Agent Automation closure rather than the entire Harness research/evidence repository.

Release admission gates now bind candidate commit to an exact source repository. Legacy schema-v1 closed gates are never silently reinterpreted across the Workstation→Harness Git-universe change; they require explicit reconciliation.

## Pre-cutover acceptance receipt

The Harness-owned candidate source passed the complete pre-cutover acceptance on 2026-09-14 while production remained on legacy immutable release `cdaa5112594917fd21312e5b1a4da5cc99a8ef91`.

- migrated runtime/deploy surface references to `/root/workstation-lab` or `workstation.toml`: **0**;
- release closure: **41 explicit paths**, including the generic Browser Use adapter, with no whole-`scripts/` archive path;
- exact MCP/registry/Browserless runtime tests: **64 passed** (`45 + 13 + 6`);
- exact Playwright route tests: **4 passed**;
- MCP deployment tests: **8 passed**;
- release-manager tests: **24 passed**;
- Browser Use tests: **5 passed**;
- Harness owner suite: **626 tests, process exit 0**, with six exact-runtime-only tests skipped in the dependency-minimal owner environment and separately exercised above;
- `ruff check src tests scripts`: PASS;
- `git diff --check`: PASS;
- dependency, documentation, evidence and `uv lock --check` gates: PASS;
- deterministic demo: PASS;
- scale acceptance: PASS (`8` runs, `96` events, inspect p95 `0.79 ms`, reopen+full-doctor `33.866 ms`);
- wheel isolation: PASS for `ordivon_harness-0.6.0-py3-none-any.whl`.

No production release switch is implied by this receipt. Production activation remains a separate quiescent release transaction with exact candidate import checks, operator-carrier currentness, Temporal running-workflow observation and rollback.

## Stable operator carrier boundary

`/root/tools/bin/agent-automation` remains a Workstation v2-owned stable node carrier. Harness does not archive, materialize, or byte-compare a duplicate wrapper. Release preflight only requires the external stable carrier to exist and be executable; Workstation owns its exact-byte materialization/currentness, while Harness owns the immutable release behind `/opt/ordivon/agent-automation/current`.
