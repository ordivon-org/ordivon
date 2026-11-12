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

## P0 source contract convergence (2026-11-12 late execution)

The new independent config/open-connectivity.json declares a temporary
transport policy, not a new network controller. The native sing-box sources
remain the executable data plane. Z3 source refinement checks nine HTTP/mixed
TCP consumers and 17 loopback listener tags over symbolic hostnames and TCP
destination ports, with two declared Finance direct exceptions. Independent
default-reject and rogue-Finance-direct mutations yield SMT counterexamples.

Source-only mise run ci passed 446/446 native tests and all formal checks.
Existing Go Task validator checks for Claude, ChatIngress, Finance, X Reality
and Supply Chain also passed. Original negative assertions were not skipped:
independent upstream Carrier spies now require an unrelated destination to be
forwarded by sing-box, and reject an intentionally restrictive mutant.

Native read-only real Carrier observation for Codex, Claude, Model Provider
and Supply Chain ran without a service or VPN restart. 20/20 observations
passed. Each business HTTP origin and unrelated example.com completed an
origin HTTPS response. Other TCP ports and IP literals were observed at the
Carrier only; they are not claims of end-to-end remote TLS or IPv6.

Finance business payloads remain read-only and independently source-declared
even though the Network transport accepts other destinations. No trading
or credential use is authorized. Finance live witness now binds all nine
business authority files, the two direct exceptions and positive open
Carrier observations.

## Source, installed, loaded and runtime distinctions

The previous production run (2026-11-12) installed nine open sing-box JSON
configurations and Gluetun's unrestricted geo selector and
BLOCK_MALICIOUS=off. This further source requalification modified ready.sh,
Taskfiles, formal checks and Carrier witnesses IN SOURCE. Until these changed
scripts are installed through the native consumer deployment flow and running
processes consume their exact content, green source tests are not proof of
a matching production script SourceCut or loaded-policy generation.

PR #2145 must be reviewed and merged using existing GitHub checks. A local
green owner test cannot establish official CI success, protected main
advancement or deployment. Do not restart the shared VPN merely to make
a GitHub test pass. Release and live readback are separate evidence stages.


## Still not promised

- Arbitrary direct fallback from a fail-closed consumer namespace, mandatory
  plain Internet access without a VPN, anonymous credentials, a second
  Carrier, or globally disabling Windows Sandbox firewall.
- Device-origin iOS Exit Node verification, provider service stability or
  guaranteed IPv6 from a v4-only provider.
- Public proxy listening sockets: existing loopback/namespace bindings remain.
