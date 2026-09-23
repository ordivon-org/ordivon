# Infrastructure Liveness Acceptance R1

Status: **ACCEPTED WITH EXPLICIT WINDOWS AND COLD-BOOT TRUTH BOUNDARIES**

Acceptance window: 2026-09-24 00:16-00:23 +08:00.

Implementation commit: `c49023f47` (`refactor(infra): enforce core service liveness contract`).

Source truth at the start of destructive Linux acceptance was clean local `main` at `e3c50f70b012ad51b3aabfe6e3fbc87cde83e3f0`. During acceptance, unrelated work advanced clean local `main` to `db7dac63d5b4694e11dd762b2d7007b0db3660f0`; the closeout candidate is based on that newer exact main. At the pre-closeout census, `origin/main` remained `6231bda83a066a73d95392c6cfeee1371681a8e1` and local main was 85 commits ahead / 0 behind. No publication push is part of this acceptance.

## Static contract verification

The existing contract tests were run separately, preserving the repository's known duplicate-basename pytest collection boundary:

- `python -m pytest -q services/gateway/tests/test_systemd_contract.py` -> 12 passed;
- `python -m pytest -q services/runtime/tests/test_systemd_liveness_contract.py` -> 1 passed;
- `python -m pytest -q services/host/tests/test_systemd_liveness_contract.py` -> 1 passed.

Durable Runtime evidence: `job-01a0cf06-6456-7983-af95-528fe5cfea3c`.

## A1 - Linux Runtime restart isolation

Before: Runtime PID `2216001`, Host PID `2234628`, Gateway PID `2236054`; Gateway health HTTP 200.

`systemctl restart ordivon-runtime.service` produced Runtime PID `2433154`. Host stayed `2234628`; Gateway stayed `2236054`; Gateway remained `active/running` and health stayed HTTP 200. No manual Gateway start was used.

After Runtime recovery, an execution submitted through Gateway capability `execution.linux` completed successfully (`job-01a0cf0e-9ca8-79e1-b1ec-7862531e693a`). Gateway-to-Host `continuity.get(task:host-northbound-ux-convergence-r1-20260923)` also succeeded at revision 5 without a Gateway restart.

Durable Runtime evidence: `job-01a0cf0e-2b51-7491-adea-7702285df87f`.

## A2 - Host restart isolation

Before: Runtime PID `2433154`, Host PID `2234628`, Gateway PID `2236054`.

`systemctl restart ordivon-host-v2.service` produced Host PID `2437814`. Runtime stayed `2433154`; Gateway stayed `2236054`; Gateway health stayed HTTP 200. Gateway-to-Host continuity then succeeded again at revision 5. No manual Gateway start was used.

Durable Runtime evidence: `job-01a0cf0f-7a4f-7123-a60d-cd9fec78a435`.

## A3 - Gateway unexpected-process self recovery

Gateway main PID `2236054` was terminated with SIGKILL, not with `systemctl stop`. systemd replaced it with PID `2444349`; `NRestarts` increased from `0` to `1`; the service returned to `active/running`; health returned HTTP 200. Runtime PID `2433154` and Host PID `2437814` did not change. Gateway-to-Host continuity then succeeded again at revision 5.

Durable Runtime evidence: `job-01a0cf0f-e3e9-7992-b327-ccaf0af1a4e7`.

## A4 - Explicit operator stop authority

Gateway PID before the test was `2444349`, with `NRestarts=1`. After explicit `systemctl stop ordivon-gateway.service`, an 8-second observation window was held, which is longer than the configured `RestartSec=3`. At the end of that window the unit was still `inactive/dead`, PID `0`, `NRestarts=1`.

An explicit `systemctl start ordivon-gateway.service` then restored Gateway as PID `2451468`, `active/running`, health HTTP 200. Runtime remained `2433154` and Host remained `2437814`. The start reset the unit's current `NRestarts` counter to `0`; the earlier A3 restart delta remains preserved by the A3 evidence.

The initial Runtime admission response for this test reported `REGISTRY_BUSY` with `commitState=committed`; the committed Job was reconciled by Job ID rather than reissuing the effect. The Job completed successfully.

Durable Runtime evidence: `job-01a0cf10-8241-7111-9f0f-b24277dfa902`.

## A5 - Production ingress self recovery

The two production tunnel units were tested one at a time. The direct-route prerequisite remained `active/exited` and was not modified.

### Path A

Before: A PID `2264855`, `NRestarts=1`; B PID `2268127`, `NRestarts=0`.

A's main process was SIGKILLed. A immediately entered `activating/auto-restart`; B stayed `active/running` with PID `2268127`. While A was still in the recovery window, the public ChatGPT -> Gateway connector successfully executed `system.describe()`, proving public Gateway ingress remained reachable through the surviving path. A recovered as PID `2457796`, `NRestarts=2`; B still had PID `2268127`; local Gateway health was HTTP 200.

Durable Runtime evidence: kill `job-01a0cf11-bd8a-7743-8af9-8ba67ef689cd`; recovery `job-01a0cf12-1d06-7b92-a707-589e31c2affd`.

### Path B

Before: A PID `2457796`, `NRestarts=2`; B PID `2268127`, `NRestarts=0`.

B's main process was SIGKILLed. B immediately entered `activating/auto-restart`; A stayed `active/running` with PID `2457796`. While B was still in the recovery window, the public ChatGPT -> Gateway connector again successfully executed `system.describe()`. B recovered as PID `2460603`, `NRestarts=1`; A still had PID `2457796`; local Gateway health was HTTP 200.

Durable Runtime evidence: kill `job-01a0cf12-5669-7701-b9d5-a9af7a9c4eab`; recovery `job-01a0cf12-add1-7123-9fc8-566b00f5fe70`.

The existing `Requires=ordivon-cloudflare-direct-route.service` relation was not changed: current evidence shows it is a routing prerequisite, not the Runtime/Host-style lifecycle coupling that ILC-R1 removes.

## A6 - Windows SCM evidence closeout

Fresh Windows SCM census at `2026-09-24T00:22:24+08:00` showed:

- `OrdivonRuntimeR6Candidate`: Running / Auto, PID `8072`, SCM restart actions 5s / 15s / 60s;
- `OrdivonRuntimeR6ElevatedCandidate`: Running / Auto, PID `6692`, SCM restart actions 5s / 15s / 60s;
- `OrdivonRuntimePrivilegedBroker`: Running / Auto, PID `5856`;
- `OrdivonGatewayCandidateR2`: Running / Auto, service PID `13052`, release `eaa045252ef7fc61d65325aa9dfbb2d40d8f4054`, port 19000, SCM restart actions 5s / 15s / 60s;
- `Cloudflared`: Running / Auto, PID `9480`, SCM restart action configured;
- retired `OrdivonGatewayCandidateR1`: Stopped / Manual, PID `0`.

The port-19000 listener was present and owned by PID `11928` (the Gateway child process under the R2 service wrapper).

Standing: **CONFIGURATION_ACCEPTED / DESTRUCTIVE_LIVE_RECOVERY_NOT_EXECUTED**. Concurrent Windows authority-cutover work was active around this acceptance window, so no Windows service/process was deliberately killed. This document does not claim Windows destructive recovery evidence.

Durable Windows Runtime evidence: `job-01a0cf13-4e6a-7f73-afdf-38be0d556acd`.

## A7 - Cold boot truth boundary

Linux Runtime, Host, Gateway, production ingress A/B, and the direct-route setup unit are enabled according to systemd. The Windows core services above are configured `AUTO_START` where intended.

**BOOT/COLD-START NOT PHYSICALLY EXECUTED.** No Linux host reboot, Windows reboot, WSL cold boot, or machine cold start was performed for ILC-R1. Enabled/Automatic configuration is startup configuration evidence only.

## Final live standing

At the final Linux census (`2026-09-24T00:23:28+08:00`):

- Runtime: `active/running`, PID `2433154`, enabled, `Restart=always`;
- Host: `active/running`, PID `2437814`, enabled, `Restart=always`;
- Gateway: `active/running`, PID `2451468`, enabled, `Restart=always`, health HTTP 200;
- production ingress A: `active/running`, PID `2457796`, enabled, `Restart=always`, `NRestarts=2`;
- production ingress B: `active/running`, PID `2460603`, enabled, `Restart=always`, `NRestarts=1`;
- direct-route: `active/exited`, enabled, `Type=oneshot` behavior retained.

Host Doctor was re-read after the live tests and remained healthy on PostgreSQL journal schema 5 with all integrity checks OK. Gateway-to-Host continuity remained readable at revision 5.

D: headroom remained `41,889,275,904` bytes, below Runtime's 48 GiB workspace admission threshold; this is a capacity condition, not an ILC service failure.

Pre-closeout currentness evidence: `job-01a0cf14-43d8-7653-9b9d-b6e882945cfe`.

## Conclusion and truth boundary

ILC-R1's Linux service-manager liveness, owner restart isolation, Gateway unexpected-exit recovery, explicit operator-stop authority, and dual production-ingress self-recovery are physically accepted. Windows service-manager configuration is accepted from current SCM state, but Windows destructive recovery is not claimed. Cold-start behavior is not claimed as physically tested.

No custom watchdog, lease controller, heartbeat database, or tunnel supervisor was added.
