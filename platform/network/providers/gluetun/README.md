# Gluetun owned provider cold-start reconciliation

This is a native systemd timer and oneshot service, not a custom polling loop.
When the selected mode and enabled Provider target authorize recovery, it
starts the actual Gluetun container service and the compatibility adapter.
Starting an already-active target alone would not recover a failed child
service; starting the actual healthy services is an idempotent no-op.

It fixes the observed failure mode where an early Podman storage error
prevented the generated provider-network unit from starting during WSL boot.
Podman later recovered, but systemd did not re-attempt the failed target.
Periodic attempts use a two-minute calendar plus a boot-relative attempt.

The existing provider-identity-exclusive check refuses competing WireGuard
identity realization. A missing selector or disabled Gluetun target disables
recovery, allowing owned provider mode changes and operator maintenance.
No Windows-wide proxy, Surfshark GUI, host default route or extra WireGuard
identity is created. Service start success is not a proof of provider Internet
health; downstream consumer readiness must be separately verified.

Install this timer only after source tests and live owner preflight; disabling
the timer stops periodic recovery without changing a currently working provider.

## Source and installed closure

Quadlet configuration lives under quadlet/, the physical identity guard is
identity-exclusive.sh and the systemd recovery units live under systemd/.
Credentials stay outside Git. The native Gluetun healthchecker handles
in-tunnel reconnects; Network systemd reconciliation handles cold-start units.
Use task provider:gluetun:verify to inspect installed source and consumer result.
The same verification now checks the running Podman container's selected loaded
non-secret environment against the source-generated profile; an edited env file
without a provider restart is **not** a successful deployment. Unexpected
hostname/city/category filters **and** loaded WireGuard endpoint/key overrides
fail closed, without printing credentials. The loaded container must use the
Quadlet-owned `WIREGUARD_PRIVATE_KEY_SECRETFILE`; a matching
`SERVER_COUNTRIES` value alone cannot prove the selected WireGuard identity
and server pool are unmodified. The JSON selector rejects duplicate keys
instead of silently accepting the last occurrence. These are source-to-loaded
admission witnesses, not proof that an external endpoint is reachable.


## Optional IPinfo witness

`task provider:gluetun:observe-exit` performs a single explicitly proxied
HTTPS request to IPinfo and reports IP, country and ASN organization. It
requires proxy CONNECT=200 and origin HTTP=200 but is not a VPN lifecycle
health check or a server-ranking algorithm. This avoids creating another
background poller and preserves Gluetun-native health recovery.

## Native Surfshark mode — selected physical provider

The production Quadlet uses Gluetun native Surfshark WireGuard.
The source-owned country selector is providers/gluetun/config/exit-selector.json.
Hong Kong is the only excluded country; the other 99 countries and territories
in the actual installed Surfshark WireGuard catalog are positively listed as
SERVER_COUNTRIES (177 of 178 WireGuard records). SERVER_REGIONS is absent;
Japan, South Korea, Singapore and all other catalog countries are allowed.

Gluetun v3.41.3 has a positive country filter, not a negative exclusion filter.
Merely declaring excludedCountries without positive selectedCountries permits
Hong Kong, so source validation rejects excluded-only policies. The native
catalog evidence Task rejects a positive list that fails to cover every
nonexcluded catalog country; after an upstream catalog expansion, regenerate
the list before the next rollout. Gluetun itself owns endpoint selection,
health checks and reconnects, with no new custom endpoint scheduler.

A policy file change does not affect the running container. Source validation,
0600 environment materialization, controlled restart, loaded OCI SourceCut and
real consumer readiness must all pass. A physical Provider restart may briefly
interrupt Tailnet; Mobile must rebind to the new network namespace if needed.
A catalog entry is not evidence of consumer reachability or public IP country.

Native Gluetun owns its own healthchecks, VPN reconnect and server selection.
The official server catalog updates at `UPDATER_PERIOD=480h`; the systemd
oneshot only restarts physically stopped services. No Ordivon candidate loop
or competing WireGuard session is created.

## Health and DNS are separate capabilities

Gluetun's physical VPN startup/full checks now use native TLS IP endpoints
HEALTH_TARGET_ADDRESSES=1.1.1.1:443,8.8.8.8:443 instead of requiring
working DNS to check the physical tunnel. Both IP endpoints were checked
inside the running VPN namespace using certificate-verified TLS.

The native DNS server uses encrypted DNS-over-TLS
(DNS_UPSTREAM_RESOLVER_TYPE=dot) with Cloudflare and Google upstreams,
rather than inheriting the previous DoH setting from the archived Custom
Provider candidate. Gluetun's native VPN restart, firewall and cache
remain the only owners of those functions. Physical and DNS failures
must still be independently measured; this configuration does not prove
that future reconnect storms have ceased.

The existing Custom provider candidate environment remains a valid
credential materialization input and recovery source. Deployment is
a new native environment SourceCut followed by a controlled physical
Provider restart and downstream consumer verification, not an
additional WireGuard identity.

The physical identity is imported from the already-owned WireGuard profile
by `task provider:gluetun:native:prepare`, which writes a root-only native
environment file and stores the private key in Podman Secret
`network-v2-gluetun-surfshark-wgkey`. The container receives only the
`WIREGUARD_PRIVATE_KEY_SECRETFILE` path. Never place the key in Git,
plain environment variables, CLI arguments or log messages.

The pre-native `/etc/network-v2/browserless/nv2blwg.conf` and
`/etc/network-v2/gluetun/serialized-candidate.env` remain source inputs
for credential materialization and an explicit recovery route, rather than
being treated as unused cache. The current selected SourceCut requires
`task provider:gluetun:verify` and functional consumer acceptance.

The 2026-11-05 production acceptance demonstrated one unsuccessful native
Asia Pacific endpoint followed by Gluetun-internal recovery, then successful
Singapore/Japan selection and all 12 Network provider/consumer checks.
This does not prove future arbitrary endpoint reachability or an iOS client
actually selecting the Tailscale exit node.

## Mobile Tailnet local underlay (2026-11-07)

The upstream Gluetun FIREWALL_OUTBOUND_SUBNETS option now carries
192.168.0.0/24 in the generated native provider env. The setting
restores direct UDP connectivity for an iPad on that LAN, without
changing the Tailscale Exit Node's selected physical VPN. It is
CIDR-wide access to this private subnet, not a per-port UDP filter.
Changing local LAN topology requires source/install/loaded rule proof,
a direct-vs-DERP test and iPad public-IP revalidation. Avoid overlap
with the tunnel 10.14.0.0/16. Upstream firewall options:
https://github.com/qdm12/gluetun-wiki/blob/main/setup/options/firewall.md

The source generator and the production 0600 native env are distinct
SourceCuts. A syntactically valid file does not prove Tailscale route use.

## Upstream server catalog persistence (SourceCut requirement)

The Quadlet source binds a root-only host directory at
/var/lib/network-v2/gluetun to the upstream /gluetun directory. Its native
systemd ExecStartPre creates that directory before the provider process starts.
This preserves Gluetun's built-in servers.json updates across Podman container
replacements; it does not introduce an Ordivon updater, second WireGuard
session, credential file or new proxy.

A changed Quadlet is not an installed effect: inspect actual native generator,
deployed Quadlet, loaded unit and service preimage before a controlled single-
session restart, and verify the current Gluetun profile plus real consumers
afterward. Upstream UPDATER_MIN_RATIO admission remains independent; persisting
an outdated cache alone cannot make a rejected server update successful.


## Upstream v3.41.3 Surfshark updater ratio (2026-11-11)

The pinned Gluetun v3.41.3 native updater compares provider fetch results
against the transport-expanded built-in server count. In the current selected
Surfshark catalog there are 363 protocol records, corresponding to 185 unique
physical hostnames (178 WireGuard records). With the upstream default
UPDATER_MIN_RATIO=0.8, its admission gate requests 290 hostnames, while the
real Surfshark fetch returns 185: it rejects an otherwise complete hostname
set and enters 5-second retry cycles. These facts were independently checked
against qdm12/gluetun tag v3.41.3 and the official gluetun-servers repository.

The native UPDATER_MIN_RATIO=0.51 makes the pinned upstream integer admission
threshold int(0.51*363) = 185. A fetch of 184 is still rejected; this is the
strictest two-decimal setting compatible with the 185-hostname current census.
A matching count does not prove matching server identities or working endpoints.
Do not treat this as a general endorsement of fewer servers.
The source/loaded fingerprint, country restriction, current server identities,
DNS, and downstream consumer probes remain separately necessary.

The current released binary does not yet implement the newer
UPDATER_PREFER_DIRECT_DOWNLOAD option described in the upstream master docs;
do not set unsupported flags or introduce a custom server updater. Revisit
this explicit ratio when adopting a newer official release or if the provider
hostname-to-record mapping changes. The live provider must not be restarted
by a source-only PR.


### Native multi-country ordered fallback — qualified preview, NOT live

Gluetun's **official upstream master** contains `SERVER_SELECTION_MODE=ordered`
(from the upstream 2026-09-11 server-selection change). The current production
stable **v3.41.3** has no such implementation. The native selector can now
accept an optional source-only `selectionMode: ordered`, with two or more
`selectedCountries` in priority order and `regions: []`. For example:

```json
{
  "regions": [],
  "selectedCountries": ["Singapore", "Malaysia", "Hong Kong", "Thailand", "Taiwan"],
  "excludedCountries": ["Japan", "South Korea"],
  "selectionMode": "ordered"
}
```

This is **a preview, not permission to change the production Exit Node's
country**. Gluetun's upstream tier ranking prioritizes regions above countries;
leaving `regions: ["Asia Pacific"]` would silently defeat country priority,
so the policy rejects it. The existing source-owned candidate-catalog Task
also works when regions are empty, and remains CATALOG_ONLY_NOT_HEALTH.
The native generator does not append the unsupported mode for the current
singleton Singapore policy; a source-only preview can use `--check
--selector-policy PATH`, while `--apply` additionally refuses ordered mode
unless explicitly passed `--allow-ordered-apply`.

Before a production cutover, qualify a pinned immutable upstream image
supporting ordered mode, each consumer's actual allowed egress countries
(including iOS/Finance), native DNS/HTTPS through every fallback country,
real source/installed/loaded effect, and a return path. A single shared Gluetun
can only have **one exit country at a time**; if iOS must remain SG-only,
multi-country fallback requires a separate qualified Carrier. Ordered mode
cycles through candidate connections on successive reconnects; it is not an
independent VPN, proof of endpoint health, or proactive failback when SG
recovers. Do not use a host-direct fallback for VPN-only consumers.


### DNS measurement planes (operational interpretation)

The host network DNSproxy serves 127.0.0.1:25353 and uses direct UDP/53
Cloudflare and Google upstreams. Blackbox probes named
`blackbox-dns-upstream-cloudflare` and `...-google` run in the **host**
network namespace; their legacy alert names do **not** measure VPN DoT.
Prometheus annotates the legacy alerts with
`observation_plane=host_direct_udp53` to prevent false Gluetun restarts.

The actual Gluetun VPN DNS uses DoT/853 inside the Gluetun container
network namespace. The existing native `provider:gluetun:verify` includes
a one-shot `provider:gluetun:dns-consumer`: inspect the *running* Podman
container's PID, enter that network namespace with util-linux `nsenter`,
and use mature `dig` against its local 127.0.0.1:53 to require real
example.com A and AAAA answers. This tests the consumer's actual local
DNS **effect** without another daemon, sidecar, privileged listening socket,
or host-direct VPN fallback. Because answers may be served from Gluetun's
cache or filtering layers, passing does **not** prove each encrypted upstream
is working, a particular iOS device selected the Exit Node, or public WAN
failover occurred. The independent shared-carrier HTTPS probe remains a
separate business effect.


### Native DoT upstream attribution (separate from cached consumer DNS)

The existing provider:gluetun:verify now reuses BIND 9.20 dig's TLS
certificate validation and Linux util-linux nsenter inside the actual
running Gluetun Podman network namespace. It derives the **configured**
DNS_UPSTREAM_RESOLVER_TYPE and DNS_UPSTREAM_RESOLVERS from that container's
existing metadata and tests the qualified native provider endpoints:
Cloudflare (1.1.1.1:853, cloudflare-dns.com) and Google
(8.8.8.8:853, dns.google). No extra sidecar, daemon, registry, credential,
connection selector, or new network path is introduced.

Unlike the local 127.0.0.1:53 consumer check, this makes a new TLS+DNS
request to the remote source with CA validation and an expected hostname.
An answer is mandatory: BIND dig may return exit status 0 even when TLS
peer certificate validation fails. One upstream failed but another returned
a valid A answer is **DEGRADED**, not complete DNS failure. Zero successful
upstreams or an unrecognized currently configured resolver fails the
readiness check, without automatically restarting or reconfiguring VPN.

This is a point-in-time, explicitly scoped observation, not assurance
that Gluetun internally selected exactly the same upstream, that every
future query succeeds, or that an iPhone/iPad used its expected Exit Node.
Provider DNS consumer answers, remote DoT transport, carrier HTTPS
readiness, and device-origin receipts remain distinct evidence.
