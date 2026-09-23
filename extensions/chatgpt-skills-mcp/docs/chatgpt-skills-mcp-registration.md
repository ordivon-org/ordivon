# ChatGPT / OpenAI consumer registration

Server endpoint: `https://skills-mcp.ordivon.com/mcp`

Expected protocol: MCP `2026-07-28` over Streamable HTTP.

Expected tools:

- `skills.list`
- `skills.search`
- `skills.resolve`
- `skills.read`

Authentication: Cloudflare Access Managed OAuth on the public hostname. The OAuth client receives an opaque Access token; Cloudflare resolves it and injects a signed `Cf-Access-Jwt-Assertion` to the origin. The Skills MCP verifies that assertion with the configured Access issuer, application audience, JWKS, RS256 signature, and expiry. The server-local static Bearer remains only as a loopback operator/readiness credential and must never be sent to the public endpoint or copied into portable plugin data.

Before consumer registration, run:

```bash
/opt/ordivon/skills-mcp/current/scripts/skills_mcp_consumer_readiness.py
```

A successful result must report `status=ready`, public HTTP `401` with a Cloudflare OAuth Bearer challenge carrying `resource_metadata`, and exactly the four expected local tools. The loopback verification path continues to use the private operator Bearer without exposing it publicly.

For ChatGPT custom apps, current OpenAI product documentation requires an account/workspace surface where Developer mode / Apps Create is available. Configure the remote endpoint, select OAuth, complete the Cloudflare Access authorization prompt, scan tools, and verify the exact four-tool set before creating the app. If the product UI does not offer custom MCP creation for the current plan, that is a consumer-product availability blocker rather than an MCP server defect.

Public authentication is intentionally standardized on the same Cloudflare Access Managed OAuth pattern used by the other Ordivon MCP control surfaces. Do not implement a second OAuth authorization server inside Skills MCP; Cloudflare owns authorization-code, refresh-token, client registration, and policy enforcement, while the origin owns Access-JWT verification.

## Cloudflare machine-client note

The zone currently has Browser Integrity Check enabled. Validation on 2026-09-16 showed that Cloudflare Error 1010 is triggered specifically by the default `Python-urllib/3.12` browser signature, while explicit machine-client signatures including `python-httpx/0.28.1`, `mcp-python/2.0.0`, `OpenAI-MCP/1.0`, `ChatGPT-MCP/1.0`, and Node reached the Access/origin boundary normally. Therefore BIC does not need to be disabled for the MCP hostname today. The readiness checker sends its own explicit machine-client User-Agent rather than relying on urllib's default signature.

## Retained-consumer boundary

As of 2026-09-21, ChatGPT is the only evidence-backed consumer that requires this public compatibility bridge. Local Codex and Hermes installations consume their own native Agent Skill roots and must not be configured to call this endpoint merely because those roots are also projected as bridge input sources. The canonical consumer census is recorded in `docs/architecture/C03_SKILL_BRIDGE_CONSUMER_CENSUS_R1.md`.

The bridge remains temporary. Retire it when ChatGPT can directly consume the same local Agent Skills / Agent Plugin package with equivalent discovery, exact activation/read, refresh and trust semantics.
