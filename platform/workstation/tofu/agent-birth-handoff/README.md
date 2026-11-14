# Agent Birth Cloudflare handoff

This OpenTofu root owns the public Cloudflare resources required to project the existing loopback
noVNC human-verification transports for Browserless carriers 11–13 through Cloudflare Access.

## Ownership

- Harness owns human-handoff/effect identity and keeps noVNC bound to loopback.
- Cloudflare Access owns public identity admission.
- Cloudflare Tunnel owns published-hostname transport.
- This root owns three handoff Access applications, three CNAME records, and the three ingress
  overlays on the existing `ordivon-wsl` tunnel.
- Every unrelated tunnel ingress is read from the provider and preserved. The existing tunnel
  configuration is imported before mutation and protected with `prevent_destroy`.
- The owner identity and IdP choice are derived from the existing exact
  `skills-mcp.ordivon.com` Access application; no email identity is stored in Git.
- OpenTofu state is local and private under
  `/var/lib/ordivon/operations-v2/tofu/agent-birth-handoff/`.

The public names are:

- `handoff-11.ordivon.com` → loopback noVNC 16011
- `handoff-12.ordivon.com` → loopback noVNC 16012
- `handoff-13.ordivon.com` → loopback noVNC 16013

Access applications use a 15-minute session, the same single IdP behavior as the established
Skills MCP application, an exact owner-email allow rule derived at plan time, binding cookies, and
HttpOnly Access cookies.

DNS records depend on the tunnel configuration, while the tunnel configuration depends on the
Access applications. This preserves the Access-first publication order: authenticated admission
exists before a public DNS name becomes reachable.

## Toolchain

- OpenTofu 1.12.6
- Cloudflare provider 5.25.0
- provider bytes supplied through the node-local verified filesystem mirror

The provider binary is not vendored into Git. The checked-in lock file pins the selected provider
build for this Linux owner node.

## Acceptance sequence

1. `tofu fmt -check`
2. `tofu validate`
3. live read-only `tofu plan -out=handoff.tfplan` through the existing Cloudflare credential owner
4. inspect the machine-readable plan and require:
   - no delete or replacement;
   - the five existing MCP ingress rules preserved exactly;
   - handoff 11/12/13 inserted after them;
   - the HTTP-status catch-all remains last;
5. apply the exact reviewed plan file;
6. run a second plan and require no drift;
7. verify unauthenticated public requests stop at Cloudflare Access rather than reaching noVNC;
8. only after those gates, project the three HTTPS origins into Harness
   `browserlessHumanPublicOrigins`.

Do not add token parsing, raw token files, cookie extraction, or another Cloudflare API controller
to this root. Cloudflare authentication remains owned by the existing provider credential carrier.

## Production Gateway DNS standing (2026-11-15)

The original Cloudflare **Account API Token** is obtained through the private
`/root/.config/ordivon/secrets/cloudflare.json` alias; the alias resolves to
the private active Account API credential, not the historical backup, Tunnel runtime
`TUNNEL_TOKEN` or Access Service Token pair. Official Cloudflare account
Token Verify returned `active` and a matching `ordivon.com` Zone. Never print
or copy token values, or infer Token identity from filename alone.

A read-only Cloudflare DNS API GET proved the **live** `gateway-mcp.ordivon.com`
CNAME is proxied and targets the `ordivon-wsl` production Tunnel. The
existing OpenTofu stored State referred to the very same record ID, but
retained a stale `ordivon-native-canary` target. Independently, native
Windows Runtime observed **no** listener and an unreachable MCP endpoint
at `127.0.0.1:19000`, the native Tunnel's currently declared Gateway origin.

The source of truth for the **currently serving primary** is therefore
`local.production_tunnel_id` until the Windows native ingress actually
passes MCP/Agent consumer canaries. Both production and native remote Tunnel
rules remain separate, and no Host direct connector or Access identity is
modified by aligning this DNS declaration.

Do **not** apply an old reviewed plan that targets the unqualified Native
Tunnel; existing plans are source-commit/digest-bound and need new review.
The original native script must explicitly check the desired production
Tunnel CNAME in the planned Gateway record before any apply. Refreshing
OpenTofu State without updating this declaration would permit the next
ordinary plan to switch the functioning public Gateway to a missing origin.

A Native cutover is a separate intentional change after Windows `:19000`
actually listens, a real MCP Gateway endpoint and authorized Agent readback
succeed, and the official DNS binding + whole-configuration plan are verified.
