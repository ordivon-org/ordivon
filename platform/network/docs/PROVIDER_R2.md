# R2 v2-owned WireGuard lifecycle

Date: 2026-09-11

## Finding

The current WSL kernel cannot create an in-kernel WireGuard interface: `ip link add ... type wireguard` returns `Unknown device type`. Existing provider interfaces on this host are TUN devices, so their existence was not proof that the kernel WireGuard implementation was available.

Network v2 did not add a compatibility daemon. Instead it uses the mature upstream composition already supported by WireGuard tooling:

1. `wg-quick` owns interface configuration and lifecycle;
2. the official `wireguard-go` implementation supplies the userspace TUN data plane when the kernel interface creation fails;
3. `wg(8)` remains the configuration/control interface;
4. Linux netns + veth provide the controlled underlay for the local acceptance test.

The official source is pinned by exact revision in `external/wireguard-go.lock` and installed only under `/usr/local/libexec/network-v2/`, so Network v2 does not alter the global `wireguard-go` command resolution used by unrelated software.

## Acceptance result

`task lab:wireguard-userspace` proves the following sequence with ephemeral keys and no provider credentials:

```text
wg-quick up A/B
  -> encrypted tunnel connectivity PASS
wg-quick down A
  -> expected connectivity failure PASS
wg-quick up A
  -> connectivity recovery PASS
```

This closes the local mechanical lifecycle question for WireGuard on WSL.

## Still not provider graduation

R2 does not yet bind a commercial-provider configuration or credential authority to Network v2. The remaining provider boundary is now much smaller:

- exact external provider config/credential input authority;
- provider endpoint and DNS relation validation;
- provider-specific failure/recovery and rotation tests;
- multi-provider/path selection authority;
- reboot and soak;
- standard-Linux kernel-WireGuard + Gluetun/containerlab differential validation.

No legacy Surfshark controller code, schema, service name or state is required by this R2 lifecycle.
