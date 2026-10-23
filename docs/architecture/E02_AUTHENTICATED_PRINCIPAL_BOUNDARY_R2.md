# E02 Authenticated Principal Boundary R2

Date: 2026-09-21
Status: I01-I03 IMPLEMENTED / I04 PENDING LIVE TRACE ACCEPTANCE

## Identity separation

Cloudflare Access user identity, Gateway-to-owner machine credentials, Host writerLabel, and OpenTelemetry correlation are separate authorities.

- Cloudflare Access verifies signature, issuer, audience, expiry, and subject before protected MCP requests enter the server.
- Gateway derives the stable pseudonymous `principal:cf-access:<digest>` only from verified issuer + subject.
- `GatewayAuditMiddleware` reads principal/issuer only from the verified ASGI request state. Tool arguments are never consulted for identity.
- Owner calls continue to use owner-specific machine credentials. The user principal is not copied into bearer tokens or Cloudflare service-token headers.
- Host `writerLabel` remains self-asserted provenance and is not authenticated identity.

## Span attribution

The audit middleware runs inside the MCP SDK OpenTelemetry middleware. It records:

- `enduser.id` = stable verified principal;
- `ordivon.auth.issuer` = verified Access issuer;
- compatibility attributes `ordivon.gateway.auth.principal` and `ordivon.gateway.auth.issuer`;
- after the Tool result is sealed, owner-derived identifiers such as `ordivon.operation_ref`, `ordivon.owner_id`, and `ordivon.native_id`.

The same identifiers are emitted in the structured audit log as observability correlation only. Neither the span nor the log becomes execution, continuity, authorization, or domain truth.

## I04 gate

I04 closes only after a real authenticated Gateway Tool call produces a persisted/queryable Tempo trace containing the verified principal and the returned owner operation reference on the same trace/span. Until then, this document does not claim durable authenticated audit correlation.
