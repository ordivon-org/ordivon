# Model Provider consumer network profile

This consumer owns bounded transport authority for the current external model API surfaces used by Ordivon Provider-gateway dogfood. It exposes `127.0.0.1:19881` as an HTTP proxy and lowers admitted HTTPS traffic through the single shared Network v2 provider carrier at `10.252.246.2:19680`.

Admitted destinations are intentionally narrow:

- `api.deepseek.com`
- `generativelanguage.googleapis.com`
- `openrouter.ai`
- `api.cerebras.ai`
- `integrate.api.nvidia.com`
- `open.bigmodel.cn`

Unknown destinations are rejected and `directFallback` is false.

This consumer does **not** own Provider credentials, OAuth refresh state, model routing, fallback selection, Harness Provider-call continuity, or semantic completion. Runtime CredentialAuthority remains separate. Harness may reference this network profile as execution evidence; that reference does not transfer Network authority.

The current physical provider carrier still lives under the historical Browserless namespace for compatibility. That physical identifier does not make Browserless the semantic owner of this consumer.
