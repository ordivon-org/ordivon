# R7 — Persistent finance-okx Shadow Topology

Date: 2026-09-12

## Scope

R7 turns the R6 provider-independent composition into a persistent, independently owned, non-production `finance-okx` shadow service without transferring consumer authority away from the legacy production path.

Production remains unchanged:

- legacy consumer listener: `127.0.0.1:19083`;
- legacy provider member listeners: `127.0.0.1:19084` and `127.0.0.1:19085`;
- Network v2 shadow listener: `127.0.0.1:19283`;
- Network v2 local sing-box API: `127.0.0.1:19289`.

The R7 target is deliberately active but disabled at boot. R7 proves a persistent systemd-owned shadow topology; it does **not** authorize cutover or boot-time production authority.

## Mature-tool composition

R7 does not add a custom shadow supervisor or provider daemon. Lifecycle is expressed with systemd and existing upstream tools:

```text
network-v2-finance-okx-shadow.target
├─ network-v2-finance-okx-netns@a.service
│  └─ network-v2-finance-okx-wireguard@a.service
│     └─ network-v2-finance-okx-carrier@a.service
├─ network-v2-finance-okx-netns@b.service
│  └─ network-v2-finance-okx-wireguard@b.service
│     └─ network-v2-finance-okx-carrier@b.service
└─ network-v2-finance-okx-shadow.service
```

Responsibilities:

- systemd owns ordering, restart policy, dependency propagation and persistent service state;
- Linux network namespaces + veth own isolated provider topology;
- `NetworkNamespacePath=` places WireGuard and carrier processes in the target namespace;
- `wg-quick` + pinned official `wireguard-go` own tunnel lifecycle;
- static R6 profiles remain the numeric-endpoint WireGuard input;
- sing-box owns provider carrier, exact destination fencing, URLTest health/selection and local API observation;
- Taskfile owns reproducible materialization and acceptance entry points.

There is no new always-running Ordivon controller.

## Runtime input boundary

An early R7 attempt reused `task test:r6` during every shadow materialization. This caused service materialization to depend on live Git fetches for the pinned external repositories. That coupling was rejected.

The final R7 runtime boundary is:

```text
R6 graduation / rebuild
  -> may fetch exact pinned upstream revisions
  -> may rebuild wireguard-go
  -> may rematerialize provider profiles

R7 shadow lifecycle
  -> no external fetch
  -> verify already-graduated local inputs by version/digest/manifest
  -> install systemd/config bytes
  -> start and verify shadow
```

`task verify:r6-local-inputs` checks locally installed R6 inputs before shadow materialization:

- exact `wireguard-go` version;
- exact Gluetun Surfshark catalog SHA-256;
- six-entry provider-profile manifest;
- each profile SHA-256;
- `wg-quick strip` validity;
- numeric endpoint identity;
- `Table=off`;
- `MTU=1280`;
- DNS absent from `wg-quick` ownership.

This separates CI/source graduation from service startup and prevents network availability of GitHub or upstream Git from becoming a shadow-service prerequisite.

## Functional readiness finding

A canonical replay initially failed even though every systemd unit was `active` and later inspection showed all shadow services healthy.

The failure was a startup race: `Type=simple` process state became active before the sing-box listener/API had necessarily reached functional readiness. An immediate socket check could therefore fail even while the service was converging normally.

R7 does not mask this with a fixed sleep. The final acceptance uses functional readiness gates:

1. the real `https://openapi.okx.com/api/v5/public/time` request must succeed through `19283` and satisfy the OKX application predicate;
2. `sing-box api group show finance-okx-shadow-auto` must succeed;
3. only then may destructive provider tests begin.

This preserves the existing Network v2 principle:

> process active is not application ready.

## Canonical acceptance

Canonical repository-level replay:

- entry point: `task test:r7`;
- Runtime Job: `job-01a09501-d92a-73e1-b920-07a4d6fa29d5`;
- operation digest: `sha256:5a359f5ecb134dcccfd19c45e008981b518f777d9349fca4c725cb14af4a4f7f`;
- stdout artifact: `attempt-01a09501-d92a-73e1-b920-07ba12ab28ba.stdout`;
- stdout SHA-256: `7f02b42f8bdee6ca79515dd7a75151d8873573adb33ac9fa6eede76d25c25117`;
- terminal evidence SHA-256: `85858e0179525f78092e619d7837c0c2f2cbd8963e676832bd96132cea800d68`.

Observed sequence:

1. local R6 version/digest/manifest gate passed;
2. shadow configs and systemd units materialized;
3. target started;
4. legacy `19083` request succeeded;
5. shadow `19283` request succeeded;
6. non-OKX destination rejected;
7. provider B stopped -> provider A continued serving shadow;
8. provider B recovered;
9. provider A stopped -> provider B continued serving shadow;
10. both providers stopped -> shadow failed closed, curl rc `35`;
11. provider A recovered from all-down -> shadow recovered;
12. provider B recovered -> full two-provider state restored;
13. root shadow sing-box service restarted -> shadow request recovered;
14. legacy production and Runtime/Cloudflare control-plane guards remained green.

The sing-box API agreed with the functional path:

- B down: provider B delay `-`, provider A healthy;
- A down: provider A delay `-`, provider B healthy;
- both down: both delays `-`;
- A recovered: provider A healthy again.

## Post-state proof

Post-acceptance audit:

- Runtime Job: `job-01a09503-6ee4-71e0-a0ba-6ca402932e9e`;
- operation digest: `sha256:38662d70b36c37164f541536e53328f9de9436fee2e99ab84c1fafab0d3c2abb`;
- stdout SHA-256: `6adfacf1be63ae8151e5697ccb2a2e2910d42afc9d62e8da8416a18c00128aed`.

Observed final state:

- shadow target: active;
- shadow target boot enablement: disabled;
- A/B netns units: active;
- A/B WireGuard units: active;
- A/B carrier units: active;
- root shadow service: active;
- listeners: `127.0.0.1:19283` and `127.0.0.1:19289`;
- installed unit/config bytes: exact match to repository source;
- provider env files: mode `0600`, no PrivateKey/token/password/secret content;
- Cloudflare production A/B/canary HA connections: `4/4/4`;
- Runtime listener `127.0.0.1:8897`: retained;
- legacy Finance listeners `19083/19084/19085`: retained;
- legacy Finance services: active.

## Standing

**R7 persistent non-production finance-okx shadow: PASSED.**

R7 closes:

- ephemeral-only provider topology;
- custom shadow-supervisor requirement;
- service-start dependency on live external Git fetches;
- process-state false readiness for the shadow acceptance path;
- inability to destructively test A/B provider loss against a persistent Network v2 service.

R7 does **not** close:

- long-duration soak;
- host reboot recovery;
- standard-Linux kernel-WireGuard/Gluetun/containerlab differential;
- actual `finance-okx` consumer cutover;
- legacy Network retirement;
- Cloudflare/Runtime control-plane migration.

The next production-facing gate is therefore not more provider mechanics. It is a bounded shadow observation/soak plus make-before-break consumer authority transfer from `19083` to the independently running Network v2 realization. The Cloudflare/Runtime DO-NOT-CUT set remains outside that transfer.
