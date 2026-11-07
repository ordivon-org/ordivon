# Ordivon Network | Agent guide and capability contract

**Purpose:** operational representation and owner-native instructions for Agents. Not a new Skill registry, VPN controller, test framework, scheduler, or mutable status database. Root monorepo AGENTS.md stays authoritative.

## 1. Semantics first

A Network LEGO is a replaceable semantic responsibility with a consumer, not an individual script, file or Task. Prefer DELETE unconsumed custom code → REUSE upstream-native capabilities → COMPOSE bounded Lego → CREATE only for a witnessed missing contract.

When formally declaring/admitting a LEGO, use the existing Recursive LEGO R2.1 type and canonical repository Skill; do not invent a local calculus.

For each consequential change, independently record:
- SOURCE: exact upstream Git commit, relevant files and source hash.
- INSTALLED: byte-verified systemd/Quadlet/config state.
- LOADED: running PID/generation, Gluetun **non-secret** env, Prometheus loaded scrape pools.
- EXECUTED: admitted request; forbidden-domain and wrong-port no-forward observed by independent upstream spy.
- CONSUMED: the actual application request, app process binding, and its real return.
- UNKNOWN: all unsampled paths. A historical PASS expires when its relevant source/installation/process/evironment/consumer edge changes.

SOURCE_PASS is not APPLICATION_PASS. CONNECT 200 alone is not TLS success. A sample of zero upstream CONNECT is not universal noninterference across IPv6, DNS/DoH or other clients.

## 2. Capability → owner → native interface

| Natural owner / capability LEGO | Mature implementation | Entry point |
| --- | --- | --- |
| Generic DNS / proxy | dnsproxy + sing-box + systemd | task core:validate / core:verify |
| Observability | Blackbox + Prometheus native scrape_config_files / rule_files | task core:verify and acceptance/observability |
| Physical VPN / failover | one Gluetun Quadlet, native WireGuard, Podman Secret and healthcheck | task provider:gluetun:verify |
| Surfshark profile/catalog | pinned Gluetun catalog | task provider:surfshark:verify-local |
| Scoped application destination | consumer-owned sing-box policy, bounded relay | task consumer:<name>:validate / verify |
| Scoped HTTP policy symbolic refinement | Z3 SMT with separate authority JSON and native sing-box route source | mise run formal (also native Network mise run ci) |

| iOS Exit Node server | Tailscale userspace in Gluetun network namespace | task consumer:mobile-tailnet-exit:verify |
| Optional fault/test mechanisms | Toxiproxy, isolated netns/TUN, HAProxy, tc/netem, containerlab | acceptance/, capabilities/, reference/linux/ |
| Windows boot / app process bindings | Workstation, OS environment; Codex read-only process witness | consumers/codex/windows_process_egress.py |
| Work/Job/Workspace lifecycle | Host Work and Runtime native APIs | Do not implement a parallel registry |

The generic Network Core MUST NOT own Finance/Claude/X destination policy. Observability may consume consumer scrape fragments via **native Prometheus includes**, but monitoring does not become business authority.

## 3. Agent standard workflow

1. Fetch latest origin/main, inspect active PRs and peer Agent Workspaces; open one Runtime-managed Workspace at the exact latest revision. Do not trust a stale local main.
2. Identify a real consumer, owner, effect boundary and the best current representation. Separate generic core, Provider, Consumer, Workstation, Runtime, Security, Host.
3. State pre/post/invariant/effect scope, including which negative counterexample would falsify the proposal.
4. Use existing upstream-native mechanisms. Prefer current Go Task includes, systemd/Podman lifecycle, Gluetun health, sing-box routing, Prometheus, Tailscale. Do not add a second watcher or provider loop.
5. Run the minimum focused falsification, then task all:validate, mise run ci / mise run behavior and the applicable owner-native verifier. For real network claims, inspect exact installed and loaded configuration and a live consumer consequence.
6. Publish through existing GitHub PR/required CI/merge queue. Re-fetch merged main; requalify deployed source and consumer effects. If main is new but live differs, say SOURCE_MERGED_LIVE_OLD rather than PASS.
7. Before deleting a file, volume, unit or Workspace, check consumers for read/write/start/recovery dependency. Remove via the **native owner API**; never direct-delete an actively protected Runtime backing store.
8. Report source commit, installed generation, loaded processes, real positive and negative consumer witness, deleted resources and remaining UNKNOWN. Host Work owns changing task state; do not create a second status file.

### Formal scoped-route proof (source, not live effects)

Run cd platform/network && mise run formal to prove equivalence of the
independently declared authority and first-match sing-box routing policy for
Claude, Discord, Model Provider, Supply Chain, X, nine Finance lanes,
Codex and Chat Ingress. Chat Ingress reuses its existing allowedOrigins
authority while keeping the mixed inbound explicitly TCP-restricted.
Codex has one small immutable approved domain tuple in the canonical
verifier because no second Codex authority exists; do not mirror a second
independent policy JSON. Finance's illegal public-direct escape is also a
deliberately rejected SMT mutation.
Symbolic variables are normalized HTTP CONNECT hostname, incoming scoped
listener and TCP destination port; UNSAT means no differing routing outcome
within this admitted model. The tool refuses unsupported policy constructs,
confirms every declared lane is reachable, and deliberately introduces a
rogue route to obtain a real SMT counterexample. Z3 is version-pinned in the
Network-local mise task; this is not a new framework or Skill registry.

This proof does NOT cover Chrome mixed/public-web policy, physical Gluetun,
Unicode/IDN normalization, IP literals, UDP, DNS/DoH, installed/loaded
sing-box equivalence or real app process capture. Retain mise run behavior,
task consumer:...:verify and live Carrier no-forward witnesses for those
boundaries. An unsupported construct is NOT_PROVED, not silently admitted.

## 4. Targeted falsification selection

- SOURCE-only: focused native tests + mise run ci; Green pytest does not certify a deployed VPN.
- Generic Linux: task core:verify; Blackbox/Prometheus actual targets, DNS A/AAAA, HTTPS. Idempotent task core:converge is still effectful when source/install differ.
- Gluetun: provider:gluetun:verify, ipinfo one-shot, loaded non-secret env and literal IP/TLS health; verify down-stream consumers before closing. DNS timeout may be cause OR effect of tunnel impairment.
- Scoped consumer: one admitted real request plus independently observed wrong-host/wrong-port/IPv4-literal/IPv6-literal **zero upstream CONNECT**; require failed TLS/HTTP origin for each negative probe. Reuse acceptance/egress/live-carrier-witness.py; the observer understands bracketed IPv6 CONNECT syntax but this is **not** a positive native IPv6/UDP/no-DNS-bypass proof. Do not mistake shared-carrier temporal correlation for exclusive flow identity.
- IPv4/IPv6/UDP QUIC: task accept:family-fallback, task accept:full-ip (isolated namespace).
- DNS faults: task accept:dns-resilience; check cached answer, SERVFAIL under all-upstream outage, recovery and stable daemon PID.
- Generic cold start: task accept:cold-start touches running R0. A full Windows boot→WSL→systemd→Podman→Consumer is **Workstation** acceptance, not the generic isolated cold-start test.
- Windows app process: upstream psutil one-shot observer; read actual proxy environment/sockets, do not infer from .codex/.env. Fresh CLI doctor plus shared Carrier CONNECT remains correlated, not uniquely attributed.
- Windows Chrome: `consumer:windows-real-chrome:verify` proves only the
  Linux proxy. Read the current interactive-user Chrome
  `HKCU\Software\Policies\Google\Chrome\ProxySettings` and
  `chrome://policy` (Workstation owns registry lifecycle). Use upstream
  Chrome `--headless=new --dump-dom` with disposable `--user-data-dir`,
  **without** a `--proxy-server` argument; compare an actual
  https://ipinfo.io/json browser response with sampled Gluetun egress.
  Remove the disposable profile via OS-native cleanup. Proxied curl
  success is not browser-process proof; one Chrome HTTPS request is not
  universal WebRTC/DNS/IPv6 no-bypass proof. Do not add another Chrome
  proxy launcher or Windows global proxy manager.
- Mobile: native server ready is not an iPad/iPhone client selection; collect IPinfo and DNS evidence **on each device** separately.

### Shared-path incident classifier (native Prometheus, not a new controller)

Use existing `NetworkCorrelatedConsumerOutage` alongside the individual `NetworkVPNPyPIUnavailable` / `NetworkScopedConsumerUnavailable` alerts. Its exact predicate is `count(series) == 3 AND sum(series) == 0 AND count(time()-timestamp(series) < 90s) == 3` maintained for 2m. This models **three simultaneously sampled failures**, not a proved VPN-causal fault. A missing series makes the correlated predicate UNKNOWN; individual `absent()` alerts retain missing-series coverage. One healthy consumer is a counterexample to the correlated predicate; CONNECT 200 with TLS failing does not count as healthy.

Triage: source+loaded Prometheus rule parity → `/api/v1/alerts` plus Blackbox history → native Gluetun health and endpoint-rotation journal → Provider HTTPS `verify` → exact impacted Consumer request. Match source timestamps, target/PID, installed generation and origin HTTPS. Gluetun's official native check/auto-heal owns physical recovery; do not add an Agent polling loop, a second tunnel or an IPinfo scraper. Any new endpoint/health-target policy is justified only with independent before/after consumer SLO evidence.

## 5. Concrete task snippets

From platform/network/:

    task --list-all
    task core:verify
    task provider:gluetun:verify
    task provider:gluetun:observe-exit
    task consumer:codex:verify
    task consumer:mobile-tailnet-exit:verify

Independent bounded upstream observation:

    python3 acceptance/egress/live-carrier-witness.py --consumers codex discord model-provider

Windows active-user observation (source-owned script and upstream psutil):

    uv run --no-project --with "psutil>=7,<8" python consumers/codex/windows_process_egress.py

Native monitoring SourceCut + live pool readback:

    python3 scripts/monitoring-sourcecut-preflight.py --source config --live /etc/network-v2 --check-loaded-prometheus
    promtool check config /etc/network-v2/prometheus/prometheus.yml

Never print Podman Secrets, full container environments, app tokens, credentials, or arbitrary packet captures.

## 6. Further documents

- [Human how-to](HUMAN_GUIDE.md)
- [Architecture](ARCHITECTURE.md) — C4-style context and responsibility explanation
- [Acceptance matrix](ACCEPTANCE_MATRIX.md) — reference for existing native proofs
- [Decision matrix](DECISION_MATRIX.md) — reusable mature mechanism choices
- [Existing execution work DAG](../planning/execution-program-r1.md) — Host Work owns mutable state

The documentation follows Diátaxis: how-to for Humans, contract/reference
for Agents, and existing architecture for explanation. Do not add a fourth
parallel reference corpus just to satisfy a directory taxonomy.
