# ChatGPT / OpenAI consumer registration

Server endpoint: `https://skills-mcp.ordivon.com/mcp`

Expected protocol: MCP `2026-07-28` over Streamable HTTP.

Expected tools:

- `skills.list`
- `skills.search`
- `skills.resolve`
- `skills.read`

Authentication: static Bearer credential. The token is server-local secret material and must be entered only into a supported consumer credential store or authentication field. It must never be copied into `plugin.json`, `mcp.json`, source control, Board messages, logs, or prompts. OpenAI's current MCP credential APIs expose `static_bearer` and `mcp_oauth` as first-class credential types and do not return stored secret values.

Before consumer registration, run:

```bash
/opt/ordivon/skills-mcp/current/scripts/skills_mcp_consumer_readiness.py
```

A successful result must report `status=ready`, public HTTP `401` with a Bearer challenge, and exactly the four expected local tools.

For ChatGPT custom apps, current OpenAI product documentation requires an account/workspace surface where Developer mode / Apps Create is available. Configure the remote endpoint, select the supported Bearer/static-token authentication option if offered, scan tools, and verify the exact four-tool set before creating the app. If the product UI does not offer custom MCP creation for the current plan, that is a consumer-product availability blocker rather than an MCP server defect.

Do not switch the server to OAuth solely to satisfy a presumed requirement. Use OAuth/OIDC only if the actual consumer surface requires it or if delegated/per-user authorization becomes a product requirement.

## Cloudflare machine-client note

The zone currently has Browser Integrity Check enabled. Validation on 2026-09-16 showed that Cloudflare Error 1010 is triggered specifically by the default `Python-urllib/3.12` browser signature, while explicit machine-client signatures including `python-httpx/0.28.1`, `mcp-python/2.0.0`, `OpenAI-MCP/1.0`, `ChatGPT-MCP/1.0`, and Node reached the origin Bearer boundary normally. Therefore BIC does not need to be disabled for the MCP hostname today. The readiness checker sends its own explicit machine-client User-Agent rather than relying on urllib's default signature.
