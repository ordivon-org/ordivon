# Claude Code consumer profile

This consumer projects a dedicated Claude Code egress authority over the already-running Browserless Surfshark WireGuard carrier. It does not own the provider tunnel and does not create a second WireGuard session.

## Boundary

- Host listener: `127.0.0.1:19481` (HTTP proxy).
- Namespace listener: `127.0.0.1:19480` inside `nv2-browserless-prod`.
- Carrier: existing `network-v2-browserless.target` / `nv2blwg`.
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
