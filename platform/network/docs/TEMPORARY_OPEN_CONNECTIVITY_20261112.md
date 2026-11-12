# Temporary open-connectivity phase (2026-11-12)

User direction: remove optional Network routing and destination limits first;
reconsider consumer-specific constraints later. This is a temporary transition,
not a claim that a working VPN is always available.

## Actual scope

- Surfshark Gluetun server selection no longer narrows country or region.
  Upstream server catalog, WireGuard authentication, Kill Switch and automatic
  health recovery remain upstream-owned.
- Existing nine sing-box consumer proxy configurations no longer contain domain
  allowlists or terminal domain rejection. They retain existing HTTP listener
  and shared-Carrier addresses. The Finance Treasury and FRED direct lanes
  remain explicitly bound to those two inbounds.
- Developer interactive login no longer injects the shared proxy by default;
  explicitly set ORDIVON_DEV_VPN=on to opt back in. Native managed
  --systemd-env materialization retains the original service contract.
- Gluetun native BLOCK_MALICIOUS=off disables this optional DNS filter
  without replacing Cloudflare/Google authenticated DoT transport.
- Windows current-user WinINET system proxy is disabled as a separate local
  setting, not controlled by the Linux repository.

## Source-to-production and rollback boundaries

The nine production sing-box configs have originals backed up beside the
installed files with suffix .pre-unrestricted-20261112. The Gluetun native
environment has an original backup, same suffix, mode 0600. The interactive
login profile also has an original backup. Restore one service owner at a
time. Broad VPN restarts temporarily disconnect Tailnet.

Production evidence must separately confirm source, installed, loaded
and actual consumer transport. A running process or CONNECT=200 is not
proof of full HTTPS. Some existing authority metadata, readiness scripts,
negative-test fixtures and Z3 proofs still represent former default-deny
policy. Those are legacy semantics that currently fail CI until openly
requalified, NOT evidence that new effective transport did not change.
Do not silently skip outdated tests while claiming comprehensive CI.

## Still not promised

- Arbitrary direct fallback from a fail-closed consumer namespace, mandatory
  plain Internet access without a VPN, anonymous credentials, a second
  Carrier, or globally disabling Windows Sandbox firewall.
- Device-origin iOS Exit Node verification, provider service stability or
  guaranteed IPv6 from a v4-only provider.
- Public proxy listening sockets: existing loopback/namespace bindings remain.
