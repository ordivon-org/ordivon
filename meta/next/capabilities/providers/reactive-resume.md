# Provider: Reactive Resume

Status: **UPSTREAM NATIVE AGENT PLUGIN / HOSTED MCP AUTH BOUNDARY VERIFIED**
Pinned latest stable self-host release: `v6.0.9` (`854459a44eb896ca185611bf669a65be4d5111cf`)
Observed current main: `ddedd46dcdadf984da06968c0df6e7bd343dc43a`

Reactive Resume is the primary external product surface for resumes, cover letters and user-side application tracking. Pinned latest stable `v6.0.9` itself ships the Agent Plugins 1.0 package and MCP configuration, and both schemas validate against Ordivon's pinned Agent Plugins 1.0 fixtures. Ordivon therefore does not add a wrapper.

The hosted endpoint `https://rxresu.me/mcp` returned HTTP 401 with an OAuth protected-resource challenge to an unauthenticated probe. No credential or user data was supplied.

## Adoption boundary

Self-hosted use must pin and verify a stable release/image. Hosted-service currentness is observed independently. Reactive Resume product state such as applied/interview/offer is a user-side case record until independently supported by employer/ATS/provider evidence.

Custom Ordivon resume editors, application boards and template products are DELETE-by-default while this provider satisfies the consumer.
