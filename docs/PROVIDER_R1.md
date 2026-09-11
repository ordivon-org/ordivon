# R1 provider-path admission

Date: 2026-09-11

## What is now proven

The host currently exposes multiple externally managed provider namespaces backed by mature VPN implementations. Network v2 does not import their legacy controller code or state. Instead, it treats them as external substrate and tests them only through standard Linux, WireGuard, DNS, curl and sing-box interfaces.

Observed on this host:

- direct Internet HTTPS is available;
- multiple provider namespaces independently reach HTTPS targets;
- provider paths expose distinct public egress identities;
- `1.1.1.1` and `8.8.8.8` route through the selected WireGuard device inside the selected provider namespace;
- DNS A resolution succeeds inside that same provider relation;
- a transient sing-box HTTP proxy placed inside one provider namespace carries host HTTPS traffic over that provider path;
- the proxy-observed public egress differs from the direct public egress.

This is black-box evidence that mature provider substrate plus sing-box can replace the legacy custom CONNECT relay for the transport mechanics.

Run the non-production admission smoke with:

```sh
task smoke:provider-external
```

## What is deliberately not claimed

R1 does **not** claim that Network v2 owns provider lifecycle yet. The currently observed namespaces are externally managed and may be created, replaced or removed independently of v2. They are evidence inputs, not authority.

Still required before provider graduation:

- a v2-owned provider lifecycle using a mature upstream carrier such as Gluetun or a native WireGuard/OpenVPN service;
- exact provider configuration/currentness binding without importing legacy controller state;
- provider failure -> recovery tests;
- multi-path selection and failover authority;
- reboot and soak evidence;
- a standard-Linux containerlab/tc-netem runner;
- legacy-workload differential tests and cutover.

A target being unreachable on every observed path is not treated as a provider-path failure. During this round, `example.com` and GitHub succeeded on direct and provider paths while the DeepSeek API target failed consistently across all of them; target capability therefore remains relation- and time-specific evidence rather than a permanent path label.
