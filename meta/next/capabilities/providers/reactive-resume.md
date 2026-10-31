# Provider: Reactive Resume

Status: **STABLE NATIVE INTERFACE VERIFIED / NOT AUTHENTICATED OR BEHAVIORALLY ADMITTED**
Pinned stable release: `v6.0.9` (`854459a44eb896ca185611bf669a65be4d5111cf`)
Observed current main: `ddedd46dcdadf984da06968c0df6e7bd343dc43a`

The pinned stable release itself ships an Agent Plugins 1.0 package and streamable-HTTP MCP configuration, and both schemas validate against Ordivon's Agent Plugins 1.0 fixtures. Ordivon therefore does not create a wrapper or duplicate resume/application UI.

The hosted endpoint `https://rxresu.me/mcp` returned HTTP 401 with an OAuth protected-resource challenge to an unauthenticated probe. No credential or user data was supplied.

## Admission boundary

This is **interface qualification**, not product-behavior qualification. No authenticated resume, cover-letter, or application operation has been executed in this candidate. Until a real connected consumer exists, Reactive Resume stays the preferred external product surface by architecture/interface fit, but no product-state behavior is claimed as verified.

Product state such as applied/interview/offer is a user-side case record until independently supported by employer/ATS/provider evidence.
