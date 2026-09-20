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
