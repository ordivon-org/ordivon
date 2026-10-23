# External Pull Worker E2E R3

## Focused TDD

Verified cases include queue/claim/start/complete, artifact projection/read, lease expiry,
new attempt, stale-attempt rejection, duplicate identical completion idempotence, changed
terminal replay conflict, generation fence, revocation, Ed25519 request verification, nonce
replay rejection, operator capability ceiling, schema migration, and HTTP worker flow.

## Real network E2E

A real loopback Uvicorn server was started with the actual Gateway streamable HTTP app.
The MCP streamable HTTP client called execution.submit. A fake external worker then used
ordinary HTTP to claim and complete the operation with Ed25519 signatures. The same MCP
client called execution.get and observed terminal completed plus the uploaded artifact.

Result: PASS.

No internal Python shortcut was used across the Gateway/worker HTTP boundary.

## Regression

Gateway full suite and Ruff are required before candidate commit. Runtime/Host source was
not modified by R3.
