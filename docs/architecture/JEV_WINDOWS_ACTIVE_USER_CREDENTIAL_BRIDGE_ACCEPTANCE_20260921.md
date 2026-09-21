# Jev Windows Active-User Credential Bridge Acceptance — 2026-09-21

## Decision

Jev's Windows fast path is admitted as an **active-user consumer** rather than a Runtime-owned secret consumer or a Windows service-account workload.

Accepted composition:

    consumer-owned WSL secret source
      -> one-shot stdin materialization
      -> Windows DPAPI CurrentUser blob
      -> Workstation status: present + decryptable, no value/digest
      -> Harness route admission
      -> Windows Runtime active_user authority
      -> allowlisted Windows PowerShell launcher
      -> exact pinned Jev provider venv Python
      -> Harness route adapter
      -> Jev adapter
      -> temporary in-process provider secret environment
      -> explicit semantic witness

Authority remains separated:

- **Workstation** owns node-local Jev bytes, pinned versions, browser/profile paths, DPAPI binding materialization, and read-only credential usability evidence.
- **Harness** owns browser-route selection, effect fencing, request/receipt semantics, and the Jev adapter.
- **Runtime** owns physical execution admission and Windows token authority; it does not own provider credentials or browser semantic success.
- **Jev / upstream providers** retain their own provider/network semantics.

## Why active_user

The Jev Chrome profile and DPAPI CurrentUser blobs belong to the interactive Windows user. A service limited token is therefore the wrong identity even when the physical Jev installation is healthy. Runtime already exposes active_user as a native Windows authority; Harness now binds the Jev proposal to that authority.

## Secret transport

Plaintext API keys are not serialized into Git, Harness proposals, Runtime Jobs, or receipts.

Materialization accepts the consumer-owned source values on stdin and writes:

- %LOCALAPPDATA%\Ordivon\Secrets\jev-fastpath-v1\typesafe-api-key.dpapi
- %LOCALAPPDATA%\Ordivon\Secrets\jev-fastpath-v1\text-model-api-key.dpapi

using Windows DPAPI CurrentUser.

Workstation status returns only presence, current-user decryptability, the non-secret DPAPI blob paths, secretValuesReturned=false, and secretDigestsReturned=false.

Router readiness requires both presence and decryptability for every required credential. Mere file existence is insufficient.

## Runtime executable admission

The pinned Jev venv Python lives under the active user's LOCALAPPDATA, outside the Windows Runtime executable-root allowlist. The Runtime allowlist is not widened.

Instead, the Runtime-admitted executable is:

    C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe

The Harness-owned jev_active_user_launcher.ps1 is digest-bound in the proposal and receives only non-secret paths and bounded launch parameters. It then invokes the exact Workstation-projected Jev venv Python under the active_user token.

## Verification evidence

### Physical provider

Live Workstation readback established:

- Chrome 153.0.8010.48;
- Python 3.12.13;
- Jev 0.1.0;
- browser-harness 0.1.13;
- frozen Jev source 452c1ad2dd628008f1d5608f28158d76e49e6cc0;
- exact uv executable digest binding;
- physicalHealthy=true;
- provider receipt bound.

### Credential materialization

Live DPAPI materialization established both consumer bindings without returning secret contents or secret digests.

A non-sensitive round-trip fixture (ordivon-dpapi-fixture-v1) was encrypted with the same Windows DPAPI CurrentUser materializer and decrypted by the Harness Jev adapter. Result: FIXTURE_PASS.

Runtime evidence:

- Job: job-01a0c3e4-06f3-71d2-bd32-3861a0603ba7
- operation digest: sha256:2fe71038b5c32cb730fb095dad67cce23ad0eee5d48b82a0751e4bcb46cd8159

### Live credential usability

The installed Workstation provider reports:

- typesafePresent=true;
- typesafeDecryptable=true;
- textModelPresent=true;
- textModelDecryptable=true;
- secretValuesReturned=false;
- secretDigestsReturned=false.

Harness Router then returns READY with no missing credential names for both the navigate/click profile and the navigate/click/text-entry profile.

### Gateway / Windows Runtime path

A prior service-to-service call using the canonical Gateway Cloudflare Access identity reached the Windows Runtime Core at canary-mcp.ordivon.com. The request was rejected only because the requested response tail exceeded Runtime's compact limit, with commitState=not_committed. This proves the existing Access/Tunnel/MCP path reaches Runtime without claiming Jev semantic execution.

## Current connector boundary

The live Windows Runtime Core advertises limited, elevated, and active_user. The source MCP schema and tests likewise include active_user.

However, the Windows Runtime connector already loaded into this ChatGPT conversation still validates windowsAuthority against the stale enum limited|elevated. A fresh direct active_user identity smoke is rejected by the connector schema before reaching Runtime.

This is a **client connector registration/cache boundary**, not a Runtime Core, Workstation, Harness, Jev, credential, or Cloudflare readiness failure. It must not be bypassed by smuggling the secret through a different authority.

## Non-claims

This acceptance does not claim:

- Jev upstream network/model serviceability;
- semantic success for an arbitrary browser task;
- that DPAPI file presence alone proves usability;
- that Runtime execution success implies browser outcome success;
- that the stale current-conversation connector supports active_user.

A live Jev semantic smoke through Runtime remains pending only on an MCP client surface that admits the Runtime's already-supported active_user authority.
