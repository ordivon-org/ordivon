# Workstation lab residual status

- Source: `/root/workstation-lab`
- Current observed source revision after Agent Automation contraction: `7a376d1bbe0df3aadf193a3e2e1f4812f86175b2`
- Assessed: 2026-09-14
- Disposition: **RETAIN_RESIDUAL_CONTAINER / CONTINUE_RESPONSIBILITY_EXTRACTION / DO_NOT_REACTIVATE_WORKSTATION_E2E**

## Decision

`/root/workstation-lab` is not a surviving unified Workstation E2E. The standalone `ordivon-workstation-v2` owner is already retired and generic machine operations belong to Operations/upstream systems. However, the historical lab still contains several live residual implementations and recovery/control artifacts, so deleting or globally archiving the repository would currently be false.

The repository is treated as a residual container whose responsibilities are removed one proven consumer at a time. Presence of a file or Task command does not itself establish current ownership.

## Agent Automation residual — retained active, contracted

Agent Automation / Agent Birth remains a real current consumer and therefore survives for now. Two important couplings were removed on 2026-09-14:

1. **Mutable source execution removed.** `ordivon-browserless-display@.service` previously executed `/root/workstation-lab/scripts/browserless_display_auth.py` directly. The exact helper was already present in the immutable Agent Automation release. The unit now executes `/opt/ordivon/agent-automation/current/scripts/browserless_display_auth.py`; targeted validation passed 41 tests plus 5 subtests. Agent Automation release `8812ccbb9948032312625e4d98327a1e22cac412` was materialized/activated and Browserless deployment converged successfully.
2. **Archived Computing Protocol dependency removed.** A consumer census showed `agent_automation_inquiry.py` was the sole code consumer of `ordivon-protocol`/legacy `anc_canonical`, and the Inquiry surface had no current caller outside its own unit tests. The unused Inquiry implementation/tests and exact Computing Protocol requirement were deleted rather than migrated. The MCP runtime doctor now rejects an installed `ordivon-protocol`. Full owner validation passed: 1128 Workstation tests, 6 Browserless clean-surface tests, 105 Agent Automation tests, and 14 Node policy/runtime-domain tests. Release `7a376d1bbe0df3aadf193a3e2e1f4812f86175b2` was activated; its production MCP venv reports no `ordivon-protocol` distribution and neither `ordivon_protocol` nor `anc_canonical` is importable.

After that activation the current Agent Automation MCP, Temporal worker, and Browserless display 11/12/13 services all remained active. Installed systemd units contained zero direct `/root/workstation-lab` execution/reference paths.

## Codex adapter residual — locally retired

The separate self-built `codex-harness-mcp` / `codex-exec-server` systemd path was inactive, disabled and consumer-free. Its local units were removed; see `migrations/records/codex-harness-mcp-retirement.md`. Native Codex CLI remains independent. A Cloudflare hostname-specific remote exposure remains an explicit cleanup HOLD.

## What still prevents full workstation-lab archive

The remaining repository includes at least:

- current Agent Automation source/release authority;
- Workstation recovery/backup retained as `RETAIN_MINIMAL_RECOVERY`: immutable generation execution plus Restic/semantic recovery; Operations owns only the generic scheduler substrate;
- node/equipment/Windows substrate residuals whose current consumers must be proven before migration/deletion;
- historical Network research/recovery tools that may now be superseded by Network v2 but require bounded consumer/service proof;
- historical creative/company/artifact material, much of which is provenance rather than runtime authority;
- Finance-related residuals, explicitly out of scope for the current cleanup round.

## Next rule

Continue by consumer consequence, not by directory name. For each residual:

1. identify current service/config/repository consumer;
2. prefer an already-admitted mature/current owner;
3. cut over or delete only after exact consumer proof;
4. preserve immutable recovery/research evidence separately;
5. do not recreate a unified Workstation owner.
