# Claude Code consumer profile

This consumer projects a dedicated Claude Code egress authority over the already-running Gluetun-owned shared Surfshark WireGuard carrier. It does not own the provider tunnel and does not create a second WireGuard session.

## Boundary

- Host listener: `127.0.0.1:19481` (HTTP proxy).
- Namespace listener: `127.0.0.1:19480` inside `nv2-browserless-prod`.
- Carrier: shared physical Gluetun-owned Surfshark WireGuard; Browserless target remains the mode-neutral client network namespace substrate.
- DNS: Browserless namespace DNS, IPv4-only.
- Direct fallback: forbidden.
- Destination policy: exact Anthropic/Claude HTTPS domains only; final route action is reject.

The initial core allowlist follows Anthropic's documented Claude Code network requirements for model/auth/update traffic and optional documentation lookup:

- `api.anthropic.com`
- `claude.ai`
- `claude.com`
- `platform.claude.com`
- `downloads.claude.ai`
- `code.claude.com`

Cloud MCP connectors, Artifact hosts, plugin registries, GitHub and telemetry endpoints are intentionally not admitted by this authority. If a later workload needs one, it must receive a separate explicit authority or an intentional policy extension with consequence acceptance.

## Security invariant

`DECLARED ALLOWLIST == TRANSPORT ENFORCEMENT`

A host-side metadata file alone is not considered enforcement. The sing-box route table carries the same exact domain set and ends in `reject`.

This consumer is a network authority only. Claude process identity, timezone/locale projection, filesystem projection, foreground/background convergence and OAuth browser isolation belong to separate Claude privacy/runtime owners.

## Evidence and native acceptance

The bounded consumer readiness script proves allowed-origin TLS transport and
absence of direct client default routes. For native sing-box reject behavior
that accepts CONNECT then closes the stream, it returns TRANSPORT_READY with
upstreamNonforwarding=UNKNOWN, not a fictional CONNECT=403 policy verdict.
The existing owner-native consumer:claude:verify Task additionally executes
acceptance/egress/live-carrier-witness.py --consumers claude, binding source and
installed configuration bytes and process identity to a real Carrier packet
observer. The upstream must see the allowed CONNECT and zero unknown-host or
wrong-port attempts. This is sampled HTTPS/IPv4 evidence, not a universal
DNS/IPv6, credential or old desktop process guarantee.
## Client process and timezone evidence boundary

Network validates the dedicated proxy, not a running Claude Code PID. Its
consumer:claude:verify composes exact source/deployed bytes, the no-direct-route
client namespace, permitted HTTPS, independent denied Carrier forwarding, and
process continuity. None of these certifies a signed-in account, region
eligibility, the actual Claude Code launch, or background worker inheritance.

The general Linux development shell can use the shared Gluetun HTTP proxy
10.252.246.2:19680. That is **not** the Claude-specific client proxy at
10.252.247.1:19482 in nv2-claude-client, nor the loopback host relay
127.0.0.1:19481. A plain host-shell Claude invocation does not inherit
Claude-specific routing solely because HTTPS_PROXY is set. Workstation and
Harness own the process startup identity and tool worker decomposition;
Network owns the verified dedicated egress policy.

Evidence needed for a real Claude Code consumer:

1. Attribute the actual executable SHA, running PID and start time. Verify
   its /proc/PID/ns/net is the intended Claude client namespace; if no live
   process exists, report PROCESS_BOUND=UNKNOWN, never PASS.
2. Redact all credentials and tokens. Inspect only effective proxy target,
   NO_PROXY bypass semantics and any explicitly configured LLM gateway.
   Claude Code checks lowercase https_proxy before uppercase HTTPS_PROXY,
   then lowercase http_proxy and uppercase HTTP_PROXY. A generic inherited
   lowercase variable can silently supersede the intended upper-case proxy.
   ANTHROPIC_BASE_URL chooses an LLM API/gateway, **not** an HTTP forward proxy.
3. Keep the existing native Network task as transport and independent
   upstream no-forward evidence; maintain explicit sampled IPv4 HTTPS, DNS,
   IPv6 and process-memory evidence limitations. Do not infer runtime use from
   curl-only tests, nor policy denial merely from CONNECT=200 then TLS close.
4. For long-lived Claude Code background sessions, confirm configuration in
   the actual supervisor/worker. Shell-only exports and PATH wrappers are
   insufficient for all worker modes; follow the documented settings env
   precedence and processWrapper integration under Workstation/Harness.
5. Current six first-party domains are a narrow basic core. Enterprise SSO,
   hosted claude.ai MCP connectors, browser bridge, plugin registries and
   optional telemetry have separate consumers. Add a domain only after a
   justified capability actually needs it. A blocked optional endpoint is
   not evidence of account enforcement.
6. Record host UTC synchronization, physical provider egress observation,
   process timezone and locale as different facts. Do not use a timezone-IP
   equivalence score, alter the OS timezone to masquerade as another region,
   or treat network success as Anthropic supported-region approval.
   Authentication and account eligibility remain the provider's authority.

References (living external contracts):
https://code.claude.com/docs/en/network-config
https://code.claude.com/docs/en/settings
https://code.claude.com/docs/en/legal-and-compliance
https://privacy.claude.com/en/articles/11186740-does-claude-use-my-location
