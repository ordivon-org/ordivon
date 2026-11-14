# Gluetun owned provider cold-start reconciliation

This is a native systemd timer and oneshot service, not a custom polling loop.
When the selected mode and enabled Provider target authorize recovery, it
starts the actual Gluetun container service and the compatibility adapter.
Starting an already-active target alone would not recover a failed child
service; starting the actual healthy services is an idempotent no-op.

It fixes the observed failure mode where an early Podman storage error
prevented the generated provider-network unit from starting during WSL boot.
Podman later recovered, but systemd did not re-attempt the failed target.
Periodic attempts use the existing **one-minute native timer** plus a boot-relative attempt.

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


Native auth materialization is owned by the existing Provider:
`task provider:gluetun:native-auth:validate` checks the official TOML
roles from source (no secret), `native-auth:prepare` generates a 256-bit
API key directly into the already-mounted protected host volume
`/var/lib/network-v2/gluetun/auth/config.toml` without printing it, and
`native-auth:verify` confirms owner-only permissions and exact route
authority. Existing read-only Gluetun status endpoints stay public only
inside the container loopback; VPN settings GET/PUT require the API key.
Even successful preparation is only INSTALLED, not LOADED: the upstream
Gluetun process requires a controlled restart for the role to take effect.
Do not restart a healthy production tunnel merely to change these bytes.

## Authenticated native Gluetun switch (fail-closed until configured)

`task provider:gluetun:native-control-preflight` checks the genuine native
Gluetun control settings GET in the live Gluetun network namespace. The
pinned Gluetun v3.41.3 accepts an authenticated HTTP PUT to
`/v1/vpn/settings` with exactly
`{"provider":{"server_selection":{"countries":["Japan"]}}}`.
Production update (2026-11-14): the protected API role was installed
root-only (0600), loaded by the **existing** Gluetun provider, and the
authenticated `GET /v1/vpn/settings` now returns HTTP 200; an unauthenticated
GET still returns HTTP 401. Native source parses Gluetun's lowercase country
names and returns canonical allowed-country identities. The official PUT
performed a real MY→North Macedonia→MY round trip: consumer-qualified
end-to-end 6.35s out / 6.50s back, same Gluetun PID, no extra VPN session.
**These are real roundtrip trial receipts, not an outage TTR guarantee.**
Do not substitute
`HTTP_CONTROL_SERVER_AUTH_DEFAULT_ROLE={"auth":"none"}`.

The native adapter expects a root-only pre-installed TOML role named
`ordivon-native-country-switch` with API-key authentication and precisely
`GET /v1/vpn/settings` and `PUT /v1/vpn/settings` permissions; preserve the
previous publicly consumed read-only status route separately. This must be
qualified and atomically installed using the official Gluetun config before
a controlled provider restart. No API key goes in Git or an env variable.
A start-up config change to a running process is not effective until the
official Gluetun process loads it. Keep HTTP control bound to container
localhost (never publish it).

`task provider:gluetun:native-recover` is a guarded, one-shot consumer of
a real history+live-source report. It holds while consumers are healthy,
while the physical underlay is down/unknown, during insufficient evidence,
or without authenticated API access. A permitted historical country is
only a **trial**, not a current certified standby. If its consumer/TLS tests
do not pass after a bounded period, native settings selection is returned
to its previous source; this cannot resurrect original TCP sessions or
guarantee the former exact Surfshark endpoint IP. Production automatic triggering **was installed on the existing native
systemd reconciler** after PR #2181 merged (2026-11-14), and both a manual
systemd start and repeated automatic healthy no-op runs were observed.
This is activated native logic; real unattended failure-triggered failover
time is still UNKNOWN.

## Native recovery detection speed (consumer-scoped, 2026-11-14)

The source-selected one-minute Gluetun recovery timer reuses the original systemd
unit. Claude API, Codex MCP and PyPI source-owned Prometheus Blackbox jobs
scrape every **30 seconds**, retaining their original 12-second timeout,
source URLs, module mapping and credential boundaries. Other Codex and
Supply Chain jobs remain at their existing intervals. No new monitor,
extra API listener, control agent or VPN identity is created.

The three-lane failure gate still requires three original raw scrape
samples per lane, aligned and recent, and an independent physical underlay
before any official Gluetun API country trial. With reliable 30-second
sampling and a 60-second timer, the scheduling-only worst-case before the
recovery decision is approximated by three probes (up to 90s after failure)
plus a next timer (up to 60s plus native timer jitter); this is **not** a
real-world failover-time SLA or an estimate of the following API trial. The
normal healthy consumer no-op has been observed below 0.2 seconds; direct
and VPN probes must continue proving the physical WAN distinction.

This targeted probe-rate increase costs six samples per minute rather than
three across the failure-detection lanes. Recent healthy 30min observed
P90 Blackbox probe durations were below 2.2 seconds (native timeout 12s),
leaving ample execution slack in the 30s scrape cadence. Production installation requires an explicit byte-verified migration of
three consumer-owned Prometheus fragments with native Prometheus SIGHUP;
the existing Provider bundle installer owns the original timer unit's
systemd reload/restart. The timer restart does NOT restart Gluetun.
Do not invoke generic core:converge to silently overwrite a protected
monitoring SourceCut. Verify loaded native Prometheus targets' interval,
all 19 scrape pools, current real HTTPS consumers and stable VPN/Tailscale
PIDs separately after migration.

## Active bounded recovery consumer on existing systemd timer

The existing `network-v2-gluetun-owned-reconcile.timer` has a source-bound
**one-minute** cadence (previously two minutes). It remains the same native
systemd timer and oneshot with exactly one physical Gluetun instance. The selected source adds exactly one
`ExecStartPost` action to that same service:
`/usr/bin/python3 /usr/local/libexec/network-v2/gluetun-native/native_switch.py --recover`.
No new daemon, timer, WireGuard interface or proxy is created. The native
Gluetun internal healthcheck remains responsible for prompt tunnel reconnect;
our existing systemd timer is only a secondary quality-aware escalation.

The one-shot first reads existing Prometheus Blackbox samples for Claude,
Codex and PyPI. When all three consumers are healthy or the observations
are UNKNOWN, it exits 0 immediately without costly whole-history scans,
extra HTTPS requests or any API GET/PUT. Only a fresh correlated failure
enters the bounded live quality/history/underlay and official authenticated
Gluetun API trial. The timer's `TimeoutStartSec=4min` accommodates the
two distinct bounded API trials and selection rollback.

`task provider:gluetun:native-bundle:validate` checks source only;
`...:install` checks source-vs-loaded Gluetun configuration and an actually
authorized upstream API GET, copies only the required nonsecret Python
modules and three source policy JSONs to the root-owned libexec tree,
then installs the existing updated oneshot unit and performs
`systemctl daemon-reload`. It does not restart Gluetun, Tailscale or
other consumers. `...:verify` proves exact source/installed file and
systemd loaded-equivalence. The API key remains in the separate existing
root-only mounted `/var/lib/network-v2/gluetun/auth/config.toml`.

Do not call this a verified fast switchover until a real outage and
actual consumer recovery time have been observed. Native Gluetun session
replacement can interrupt TCP connections and rotate physical IP/country.
A healthy no-op and missing monitor metrics remain distinct from genuine
VPN failure.

## VPN selection consumer graph (actually measured versus pending)

- **Decision evidence only**: Gluetun kernel WireGuard endpoint/country/hostname,
  native historical journal timestamps, Prometheus Claude API, Codex MCP and
  PyPI HTTPS/TLS consumer probes. A connected server hostname and multiple
  valid IP addresses are not the same as independently live backup tunnels.
- **Immediate failover impact**: the single Gluetun WireGuard endpoint feeds
  the shared Carrier and scoped Claude/Codex/model-provider/Supply Chain/
  Finance consumers, Windows Chrome proxy and the Tailscale mobile Exit Node.
  Switching this one endpoint interrupts existing flows and changes public
  network origin. No consumer should silently fall back to direct.
- **Post-switch admission**: use `provider:gluetun:observe-active` first;
  then the existing `consumer:claude:verify`, `consumer:codex:verify`,
  `consumer:model-provider:verify`, `consumer:supply-chain:verify`,
  `consumer:finance:verify`, `consumer:windows-real-chrome:verify`
  and `consumer:mobile-tailnet-exit:verify` as relevant. The mobile
  task proves only the server, not the actual iOS device public IP or DNS.
  A country trial succeeding for Claude/Codex/PyPI does NOT imply that
  Finance or mobile device traffic can use it.
- **Recovery trigger**: existing Gluetun health-restart remains authoritative
  for tunnel recovery. The existing native provider systemd timer **is
  now wired to** `native-recover`; its repeated active healthy results are
  `HOLD_CONSUMER_HEALTHY_OR_PARTIAL` with no effect. Failover uses at most
  two distinct recently successful country candidates, only after the
  existing real three-lane sample witness (three fresh, timestamp-aligned
  Blackbox results per lane) plus healthy independent underlay. Neither
  temporary monitor silence nor a missing kernel endpoint alone authorizes
  or blocks the proven failure action. Official native API readback verifies
  attempted changes and selection restoration. No claim of hot standby.

### Current-sample admission boundary after the 30-second rollout

2026-11-14 production fault-falsification found that the previous one-minute
scrape logic still allowed **three failed origin samples whose latest original
timestamp was 135 seconds old**. When monitoring stopped after prior failures,
that stale evidence could authorize a new country trial even if a client had
already recovered. The 30-second native sampling cadence must therefore be
paired with a source-bound original-timestamp safety condition.

The one-shot now requires each of three distinct raw samples per lane to have
its most recent sample at most **75 seconds** old, the oldest at most
**165 seconds** old, and no gap greater than **45 seconds**. The three lanes'
latest sample timestamps may differ by at most **45 seconds**. Late/missing
telemetry returns `UNKNOWN` and never grants a VPN mutation. Real current
successful samples return `FALSE` for a correlated failure. This uses the
existing single Prometheus range-vector call; there is no new monitoring
process, storage, timetable or additional endpoint probe.

The finite source-bound Z3 test enumerates sampling ages, missing-interval
gaps and cross-lane skews, including the previously accepted 135-second-old
all-zero mutant. This proves the bounded timestamp predicate against its
explicit abstraction, not all possible Prometheus scheduling behavior or
real-world VPN failover time. Required live consumer checks and healthy
Gluetun/Tailscale PID continuity remain separate release gates.

### Recovery decision and partial failures

The production fast gate consumes **existing Prometheus data**; it checks
unique Claude, Codex and PyPI series, three distinct aligned **raw
scrape timestamps** from the native Prometheus `/api/v1/query` range-vector
API (not interpolation from `/api/v1/query_range`), and a recent last
sample. A monitored endpoint may return
HTTP 401/404 successfully at the transport layer; these are deliberately
not a provider failure. Monitor silence or conflicting series => UNKNOWN
and no VPN mutation. Only sustained correlated 3-lane failures proceed.

The native one-shot ranks countries using the recent successful consumer
sessions and attempts **up to two distinct permitted countries** in order
within one bounded recovery; repeated sessions of the same country are
deduplicated, so one known-bad first preference does not starve the next
candidate. It does not claim any candidate currently alive. Each candidate
must pass actual new kernel endpoint and HTTPS-origin/TLS checks; failure
moves to the second candidate, and exhaustion attempts the prior native
selection with authenticated GET readback. Restoring a selection filter
does **not** imply restored sessions or successful consumer traffic.
Cooldown remains ten minutes between auto-triggered recovery runs.
Never select Hong Kong.

## Cold catalog trial after historical quality evidence expires (2026-11-14)

The existing 7-day source quality hint **still expires**; its latency and
consumer success ratios never become fresh measurements after expiry.
One live WireGuard provider can only directly qualify its connected country.
After 2026-11-20, staying exclusively connected to Malaysia would otherwise
make the current policy return HOLD_NO_RECENT_EVIDENCE forever after a genuine
three-lane VPN-only outage, despite stored official Gluetun WireGuard server
catalog countries being available for an API trial.

To prevent that deterministic liveness hole without rotating a healthy VPN,
the existing nonsecret recovery-hints.json also declares up to two **cold
trial country preferences**, currently North Macedonia then Mexico. They
are independently checked against the loaded Gluetun Surfshark WireGuard
server catalog at the failure boundary. Catalog membership proves neither
reachability nor latency: standing is SOURCE_CATALOG_COLD_TRIAL_UNVERIFIED,
certifiedHotStandbyCount is zero. Recent actual live-session consumer quality
remains first priority, then unexpired historic hints, then catalog-only cold
preferences; no auto selection occurs when consumers are healthy.

ONLY a fresh 30-second-origin three-lane failure and independent live
underlay success can reach the existing one-shot, and both the official
authenticated Gluetun settings GET/PUT and real kernel endpoint plus two
TLS/HTTP consumer checks are still required to accept a trial. At most two
distinct countries, 10-minute cooldown, Hong Kong excluded and previous
native country *filter* restored on complete failure. This does not create
a second VPN, scheduled healthy rotation, background controller or live
hot standby. If the catalog drops either country, that candidate is not
tried. If both disappear, the system correctly holds for lack of evidence.
The first verified automatic real outage TTR remains UNKNOWN.

## Time-bounded alternative-country memory without a new registry

The production 2026-11-14 common-underlay outage generated 3,178 native
Gluetun health reconnects in about 5.6 hours, while the Windows WLAN and USB
RNDIS interfaces simultaneously lost Internet reachability (NCSI). The
existing two-minute systemd consumer correctly recorded 169
`HOLD_SHARED_UNDERLAY_OR_UNKNOWN` decisions and never initiated a futile
country switch. Both interfaces use the same gateway IP **and gateway MAC**:
they are not proven independent WAN supplies.

The 3,178 repeated log sessions also left the 48-hour quality report with
only current Malaysia sessions, despite previously validated successful
North Macedonia and Mexico sessions. For a genuinely different event
where the **physical underlay is reachable but the current VPN is down**,
that missing evidence should not permanently disable second-country trials.

The source-owned `config/recovery-hints.json` retains only two already
verified **historical** country hints, from a native Gluetun-journal and
three-consumer Prometheus sample observed at 2026-11-14 02:56 CST:
North Macedonia (99.644%, consumer P90-median 1820ms) and Mexico
(99.153%, 3732ms). Hints expire after at most seven days. They are
`SOURCE_TIME_BOUNDED_CONSUMER_TRIAL_HINT`, never a currently live standby.
Actual recent consumer-qualified journal segments always rank ahead of these
source hints. Only fresh correlated consumer failure, independently healthy
direct underlay, original API authorization, non-Hong-Kong allowlist, cooldown
and post-switch real HTTPS origin evidence can lead to an actual change.

No session is restarted merely because this source policy is installed.
No extra Timer, daemon, database, hot WireGuard or IP endpoint registry is
introduced. Expired hints cease to be eligible; refreshing them requires
another real observed qualified consumer interval, not guessing an IP.
This avoids treating a remembered country as evidence of present liveness.

## Historical consumer quality — native evidence, never fictitious hot spares

Run `task provider:gluetun:quality-history` to correlate real native Gluetun
WireGuard session dwell times and Prometheus Blackbox success/latency
for Claude, Codex and PyPI. It uses only existing journalctl, the Surfshark
catalog and existing Prometheus query_range. Disallowed catalog countries
are excluded; startup warmup and incomplete observations cannot be silently
treated as successful. Each qualified historical interval is explicitly
`RECENT_HISTORICAL_CONSUMER_SUCCESS`, **not** `QUALIFIED_NOW_STANDBY`.
There are zero certified hot standbys in a one-session architecture until
another session has actually been verified independently.

The pure decision policy holds a working active node, holds when active
health or underlay is UNKNOWN, uses a cooldown and only recommends
a bounded trial of a recent historical candidate after a demonstrated
provider failure with a reachable physical underlay. It does not write
an endpoint status database, configure Gluetun, or run periodically.
Any native API effect must separately prove authorization, exact
candidate policy and post-switch consumer recovery.

## Active endpoint qualification (single snapshot, no false standby claims)

Use `task provider:gluetun:observe-active` to bind the existing native
WireGuard kernel endpoint, Gluetun official catalog country and actual
public Internet exit country to the SAME stable provider session. It checks
the source/installed/loaded Gluetun SourceCut, native VPN status, both
upstream HTTP CONNECT/TLS/origin business requests (example.com and GitHub)
and a second endpoint read to reject mid-observation rotations. The public
origin country may differ from the physical/catalog endpoint country.
No peer key, secret or endpoint IP is emitted by this task.

A `QUALIFIED_ACTIVE_SAMPLE` is a point-in-time active-provider witness, NOT
a persistent SLA, ranked quality estimate, proven standby, or automated
fast-failover decision. Unknown observations remain UNKNOWN; negative
business evidence remains NOT_QUALIFIED. Even an active qualification
reports `qualifiedStandbyCount=0` until independent actual standby traffic
is verified. Reuse native Gluetun switching until that qualification
exists; a historical unsuccessful random endpoint retry must not be
treated as proof that the individual server is defective.

## Optional IPinfo witness

`task provider:gluetun:observe-exit` performs a single explicitly proxied
HTTPS request to IPinfo and reports IP, country and ASN organization. It
requires proxy CONNECT=200 and origin HTTP=200 but is not a VPN lifecycle
health check or a server-ranking algorithm. This avoids creating another
background poller and preserves Gluetun-native health recovery.

## Native Surfshark mode — selected physical provider

The production Quadlet uses Gluetun native Surfshark WireGuard.
Two immutable semantic sources distinguish *permission* from *selection*:
`providers/gluetun/config/exit-allowlist.json` permits the actual 99 non-Hong-Kong
Surfshark WireGuard countries and excludes Hong Kong; its positive list must
continue matching the nonexcluded official catalog.
`providers/gluetun/config/exit-selector.json` is the candidate-country
filter. The initial `"selectedCountries": "allAllowed"` preserves the exact
previous 99-country production environment; a named country subset is allowed
only when it belongs to the permission list. Neither catalog membership nor
candidate admission proves a currently successful endpoint. The provider must
still observe actual consumer VPN readiness.

Gluetun v3.41.3 supports positive country filters, not a negative filter.
Source and native catalog validation reject excluded, unknown, duplicate or
empty candidate pools; even an excluded-only permission would accidentally
permit Hong Kong and is rejected. After an upstream catalog expansion, qualify
the updated permission source before the next rollout. Gluetun owns selection,
health checks and reconnects; this split adds no endpoint scheduler.

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
stable **v3.41.3** has no such implementation. The candidate source can accept an optional source-only
`selectionMode: ordered`, with two or more `selectedCountries`
in priority order and `regions: []`, independently of the immutable
non-Hong-Kong permission source. For example:

```json
{
  "regions": [],
  "selectedCountries": ["Singapore", "Malaysia", "Thailand", "Taiwan", "Australia"],
  "selectionMode": "ordered"
}
```

This is **a preview, not permission to change the production Exit Node's
country**. Gluetun's upstream tier ranking prioritizes regions above countries;
leaving `regions: ["Asia Pacific"]` would silently defeat country priority,
so the policy rejects it. The existing source-owned candidate-catalog Task
also works when regions are empty, and remains CATALOG_ONLY_NOT_HEALTH.
The native generator does not append the unsupported mode for the current
non-Hong-Kong production selector; a source-only preview can use `--check
--selector-policy PATH`, while `--apply` additionally refuses ordered mode
unless explicitly passed `--allow-ordered-apply`.

Before a production cutover, qualify a pinned immutable upstream image
supporting ordered mode, each consumer's actual allowed egress countries
(including iOS/Finance), native DNS/HTTPS through every fallback country,
real source/installed/loaded effect, and a return path. A single shared Gluetun
can only have **one exit country at a time**; if any consumer requires a
fixed country, multi-country fallback cannot be shared with that consumer
without a separate qualified Carrier. Ordered mode cycles through candidate
connections on successive reconnects; it is not an independent VPN, proof
of endpoint health, or proactive failback when a preferred country recovers.
Do not use a host-direct fallback for VPN-only consumers.


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
