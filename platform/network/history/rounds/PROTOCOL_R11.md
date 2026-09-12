# R11 — Protocol Divergence and Isolated UDP/QUIC Graduation

Date: 2026-09-12

## Scope

R11 hardens the already-graduated generic Network v2 platform against protocol-divergence false greens. It does not change the live R0 routing model and does not involve Finance or any consumer migration.

The live generic R0 remains a loopback mixed proxy at `127.0.0.1:28080`. R11 adds acceptance coverage for HTTP versions, DNS transports, repeated long flows, stable egress identity, and an isolated sing-box TUN capability for UDP/QUIC.

## Protocol-divergence gate

`tests/protocol-divergence-smoke.sh` requires:

- HTTP/1.1 through live R0: HTTP 200 and negotiated version 1.1;
- HTTP/2 through live R0: HTTP 200 and negotiated version 2;
- DNS A over UDP;
- DNS AAAA over UDP;
- DNS A over TCP;
- DNS AAAA over TCP;
- five consecutive public-egress observations with the same identity;
- three independent 5 MB proxied downloads.

Canonical R11 observed the stable public egress identity `39.144.242.0`. All three 5 MB transfers completed with HTTP 200.

## HTTP/3 boundary

Native HTTP/3 on the host was independently proven healthy:

```text
HTTP 200
httpver=3
```

HTTP/3 over an HTTP CONNECT proxy is not an appropriate equivalence test because CONNECT supplies a TCP tunnel while QUIC uses UDP. curl also explicitly rejects HTTP/3 over its SOCKS proxy path. R11 therefore does not label those entry limitations as a QUIC/network failure.

Instead, R11 uses sing-box's mature TUN inbound in a dedicated Linux network namespace to provide an isolated UDP-capable path.

## Isolated TUN design

`tests/tun-quic-smoke.sh` creates only transient state:

```text
host
└─ sing-box process
   └─ TUN inbound bound to temporary netns
      ├─ IPv4 route table 2022
      ├─ IPv6 route table 2022
      └─ TCP + UDP/QUIC traffic from processes inside that netns
```

Important boundaries:

- no host-wide TUN is installed;
- no host default route is changed;
- no persistent TUN service is enabled;
- the Runtime/Cloudflare control plane remains outside the temporary namespace;
- cleanup removes the temporary systemd unit, netns, TUN device, and files.

Functional readiness is not inferred from process state. The test waits for:

- transient sing-box unit active;
- TUN link UP;
- IPv4 default route in table 2022;
- IPv6 default route in table 2022;
- a real TCP HTTPS request through the TUN.

Only then does it run the UDP/QUIC proof.

Cloudflare publishes multiple anycast A addresses, so the acceptance uses bounded attempts across the current A set and still requires at least one actual HTTP/3 success rather than accepting a listening-only or route-only state.

## Canonical acceptance

Entry point:

```text
task test:r11
```

Canonical Runtime Job:

- Job: `job-01a0955d-2118-7d32-a16a-4715fd07f8d4`;
- operation digest: `sha256:a23e97aaef50a4fbb72d82d53892d50cde5c31a2458dc9385a387a0a070b1fc9`;
- stdout SHA-256: `62d3f0773853653c9e3d7328bd740e580865fbc0e1325f088bd8b42230c60100`;
- terminal evidence SHA-256: `a98bbb9b728490982f23fe71f8f7754e2db17c23055921ff3602d6872a789628`.

Observed results:

```text
HTTP/1.1: 200, httpver=1.1
HTTP/2:   200, httpver=2
DNS UDP A:     PASS
DNS UDP AAAA:  PASS
DNS TCP A:     PASS
DNS TCP AAAA:  PASS
stable egress: 39.144.242.0
5 MB flow #1: PASS
5 MB flow #2: PASS
5 MB flow #3: PASS

QUIC endpoint: 104.18.26.14
QUIC over isolated TUN: HTTP 200, httpver=3
TCP over isolated TUN:  HTTP 200, httpver=2
TUN RX packets: 156
TUN TX packets: 55
```

The canonical task verifies live R0 before and after both protocol tests.

## Post-state

Post-state Runtime Job:

- Job: `job-01a0955d-d093-7233-905e-0a53b1fa39e9`;
- operation digest: `sha256:318f4a6714dde2814057d35e2bce3aad48a801754a25682e28db5de0b035ca71`;
- stdout SHA-256: `4c9454ffc13c000eb917a5f35062a7b4a1ad1923883a09893bf250d66c10339a`;
- terminal evidence SHA-256: `469daad068e598b4c5f0c0e394203d893a53c25658188ff8987fbd05d269f1d6`.

Verified after cleanup:

- no R11 temporary netns remains;
- no R11 transient TUN service remains active;
- no host `nv2tun0` remains;
- IPv4 host default route remains via `192.168.0.1 dev eth4`;
- IPv6 host default route remains via the existing eth4 gateway;
- no host default route references the temporary TUN;
- `task verify:live` passes;
- Cloudflare production A/B/canary remain `4/4/4`;
- Runtime remains active with the same independent control-plane topology.

## Standing

**R11 protocol-divergence coverage and isolated UDP/QUIC capability: PASSED.**

The intended platform model after R11 is:

- live default R0: loopback mixed proxy + dual-stack DNS, appropriate for normal TCP proxy workloads;
- on-demand UDP/QUIC/full-IP workloads: isolated sing-box TUN in a dedicated netns;
- host-wide TUN/default-route takeover: intentionally not part of Network v2's default mode;
- `tc/netem`, containerlab and kernel-WireGuard differential: remain standard-Linux external-fidelity gates because the current WSL kernel cannot supply those exact capabilities.
