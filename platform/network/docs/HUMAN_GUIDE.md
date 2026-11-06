# Ordivon Network | Human guide

**Who this is for:** people who want to know what Network does, use it, or diagnose it. This is a task-oriented guide, not a second status registry.

## 1. What Network actually does

Network composes mature networking components and checks real consumers. It does **not** automatically route every Windows application or iOS device through a VPN.

    Application → consumer-specific proxy/policy → shared carrier
                                                   → single Gluetun/WireGuard
                                                   → Internet

    Generic Linux Network: dnsproxy + sing-box + Blackbox + Prometheus
    Windows application: explicit per-process proxy selection
    iPad/iPhone: explicit client-side Tailscale Exit Node selection

One physical Gluetun/Surfshark WireGuard identity is shared by eligible consumers. Network generic core, Provider, and each Consumer are separate ownership boundaries. Workstation owns Windows boot/WSL; Runtime owns Workspaces; Security owns secrets; Host owns mutable Work state.

## 2. Read-only getting started

Run the following from platform/network/:

| Question | Native command | Evidence provided |
| --- | --- | --- |
| Which capabilities exist? | task --list-all | Current callable owner interfaces |
| Is Linux core current and healthy? | task core:verify | Installed bytes, DNS, proxy and monitoring probes |
| Is the VPN provider healthy? | task provider:gluetun:verify | Gluetun SourceCut and live shared provider |
| Which public VPN exit was sampled? | task provider:gluetun:observe-exit | HTTPS ipinfo.io sample; NOT guaranteed future IP |
| Is Codex's Linux proxy ready? | task consumer:codex:verify | Bounded HTTPS policy and rejection |
| Is the Tailscale Exit Node server ready? | task consumer:mobile-tailnet-exit:verify | Server-side advertisement and approval only |
| Are source configurations valid? | task all:validate | Static source validity, not live application traffic |

Every other consumer has its own native Taskfile: Claude, Browserless, Finance, Supply Chain, Discord, Model Provider, Chat Ingress, X Reality, and Windows Chrome. Discover actual task names with task --list-all rather than guessing.

## 3. Do a real task

### Check VPN location with IPinfo

1. Run task provider:gluetun:verify.
2. Run task provider:gluetun:observe-exit. This makes one explicitly proxied HTTPS request to https://ipinfo.io/json.
3. Verify the specific consumer via its consumer:*:verify task.
4. Make an actual request **from the application**.

The host may separately have a different direct public IP. A successful explicit proxy call does not prove that an already-running app adopted the proxy.

### Use Windows Codex

The approved dedicated local proxy is 127.0.0.1:19982. Windows global proxy is deliberately not changed. A new Codex CLI process can receive HTTP_PROXY and HTTPS_PROXY in its own environment; a process already running before the .codex/.env edit **cannot inherit that edit retroactively**.

The optional source-owned, read-only observer (Windows interactive user, upstream psutil) is:

    uv run --no-project --with "psutil>=7,<8" python consumers/codex/windows_process_egress.py

It reports process name/PID, proxy-environment classification, whether the profile is newer, and aggregated connection counts. It does NOT print credentials, environment values, command lines, or remote IPs. It deliberately reports END_TO_END_EGRESS_UNKNOWN; only independent observation of the actual client request and carrier can advance that claim. Running an isolated fresh CLI need not close your existing ChatGPT desktop session.

### Send an iPhone or iPad through VPN

The server advertises the approved node ordivon-surfshark-exit. On each **device**, open Tailscale and select that Exit Node. Then use that same device's browser to visit https://ipinfo.io. Test Wi-Fi and cellular separately and check that expected DNS works.

Server-side task consumer:mobile-tailnet-exit:verify does not prove iPad/iPhone selection. An offline iOS peer is not evidence that it uses the exit. Do not claim that an iPhone is protected based on an active Linux service alone.

## 4. When something is not working

| Symptom | Next observation | Owner |
| --- | --- | --- |
| Linux generic proxy or DNS down | task core:verify | Network core |
| VPN/exit not reachable | task provider:gluetun:verify and one IPinfo sample | Gluetun Provider |
| DNS timeout triggers repeated VPN checks | Check loaded Gluetun DNS and health targets; compare literal IP/TLS with DNS | Provider native DNS/health |
| One domain denied, others fine | That consumer's Taskfile and real request | That Consumer |
| Old Windows Codex ignored new .env | Actual process environment/creation time, scoped TCP socket | Codex Consumer + Workstation |
| iPad/iPhone uses unexpected public IP | Actual Tailscale client Exit Node choice and device IPinfo | iOS + Tailscale |
| Windows reboot does not start Linux | Windows startup → WSL → systemd → Podman | Workstation, then Network |
| Prometheus healthy but config differs | Native SourceCut plus loaded scrape pools | Network Observability |

A WireGuard interface being up does not mean encrypted DNS is functioning. DNS timeouts can also be an **effect** of tunnel instability, not necessarily its cause. Gluetun's own native healthcheck and WireGuard restart own recovery; Ordivon must not create a competing VPN watchdog.

## 5. Making changes and cleanup

From platform/network/: run mise run ci, mise run behavior and task all:validate for source; run core:verify and the affected consumer:verify for installed/real behavior. The native task core:converge skips work when already verified, but may restart generic services if a repair is actually required. Provider preparation and Provider activation are separate operations.

Publish through the existing monorepo GitHub PR, required checks and merge queue. A detached Workspace test PASS is not a deployed release. Clean Podman storage through native Podman volume operations after checking container references. Clean Runtime Workspaces through Runtime lifecycle after consumers release them; never directly remove the backing worktree.

## 6. More details

- [Architecture / explanation](ARCHITECTURE.md)
- [Acceptance reference](ACCEPTANCE_MATRIX.md)
- [Mechanism decision reference](DECISION_MATRIX.md)
- [Agent contract](AGENT_GUIDE.md)
- [Diátaxis documentation framework](https://diataxis.fr/)
- [C4 architecture model](https://c4model.com/)
- [Official Gluetun DNS options](https://github.com/qdm12/gluetun-wiki/blob/main/setup/options/dns.md)
- [Official Gluetun healthcheck options](https://github.com/qdm12/gluetun-wiki/blob/main/setup/options/healthcheck.md)
