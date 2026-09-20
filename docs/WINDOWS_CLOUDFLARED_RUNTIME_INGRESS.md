# Native Windows Runtime Cloudflare ingress

Status: desired-state source added; live credential materialization remains a separate node-local secret operation.

## Ownership

This ingress is a Workstation realization, not Runtime Core logic.

- Cloudflare owns the Tunnel protocol, remote connector state, edge routing, and the remote-managed hostname configuration.
- Workstation owns the local cloudflared package and Windows SCM realization.
- Runtime owns only the native MCP origin on 127.0.0.1:18997, Runtime authentication, execution, Job/Attempt truth, evidence, and reconciliation.
- Network does not own this management ingress.

The current remote-managed canary Tunnel already routes canary-mcp.ordivon.com to http://127.0.0.1:18997. No Cloudflare remote-route mutation is required to add a Windows connector replica.

## Desired state

workstation/windows/cloudflared-runtime.dsc.yaml uses upstream owners directly:

- Microsoft.WinGet/Package -> Cloudflare.cloudflared;
- Microsoft.Windows/Service -> provider-native SCM service Cloudflared;
- LocalSystem;
- Automatic;
- Running;
- provider-native cloudflared --token-file;
- metrics at 127.0.0.1:20246.

No Ordivon proxy, tunnel protocol, service supervisor, retry loop, or credential parser is introduced.

On Windows, the upstream cloudflared binary itself registers its SCM handler under the fixed service name Cloudflared and installs the matching Event Log source and provider-native recovery action. The Workstation declaration therefore preserves that upstream service identity rather than renaming it. The token-file flag belongs to tunnel run and is placed after run in the ImagePath.

## Credential boundary

The service expects an existing raw Tunnel token file at:

C:\ProgramData\Ordivon\Cloudflare\windows-runtime-canary.token

The file is node-local secret material and MUST NOT be committed to Git, embedded in DSC, placed in SCM ImagePath, returned in Runtime output, or represented by a public content digest.

Materialization is a separate credential operation. The repository contains the one-shot workstation/windows/materialize-cloudflared-runtime-token.ps1 helper for this node migration. It has no runtime/service role: it reads the existing canary env only on explicit operator invocation, writes the provider-native raw token file, removes ACL inheritance, grants only LocalSystem read plus Administrators full control, and returns no token bytes or content digest. Before the service is applied:

1. the file must contain only the raw remote-managed Tunnel token;
2. ACL inheritance must be disabled;
3. read access must be limited to the identities required for administration and the LocalSystem service;
4. the token file must already exist before DSC requests status: Running.

Credential materialization does not grant Cloudflare account API authority and does not reuse the production Tunnel token merely because both credentials exist on the same node.

## Migration acceptance

The Windows connector is accepted only when all of the following hold:

1. OrdivonRuntimeR6Candidate is Running and owns 127.0.0.1:18997;
2. Cloudflared is Running, Automatic, and runs independently of WSL;
3. 127.0.0.1:20246 reports at least one provider-native Cloudflare Tunnel HA connection;
4. authenticated runtime.describe succeeds through canary-mcp.ordivon.com;
5. a real wsl.exe --terminate archlinux leaves the native Runtime PID/SCM state unchanged;
6. while archlinux remains offline, authenticated remote runtime.describe through the Windows connector still succeeds;
7. after the full C3 gate passes, the WSL-only ordivon-cloudflare-canary.service transition carrier may be retired.

The Linux production A/B Tunnel connectors are a different ingress serving Linux Runtime, Host, Skills, and other Linux origins. C3 does not authorize deleting or moving them.

## Cold boot

C4 additionally requires a real Windows reboot proving both native services recover without WSL:

Windows SCM -> OrdivonRuntimeR6Candidate + Cloudflared -> remote MCP reachable

Only after C3 and C4 pass should Runtime C5 production cutover retire the remaining WSL-hosted Windows execution carrier.
