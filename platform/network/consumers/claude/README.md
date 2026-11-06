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
