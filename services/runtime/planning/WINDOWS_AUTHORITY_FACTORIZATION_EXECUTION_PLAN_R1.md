# Windows Authority Factorization LEGO R1

## Target algebra

BrokerAuthority(provider-internal) × PayloadIdentity(service|active_user) × PayloadPrivilege(limited|elevated) -> Canonical Windows Execution Context

Legacy mapping is frozen: limited=service×limited; elevated=service×elevated; active_user=active_user×limited.

## Waves

| Wave | LEGO | Goal |
|---|---|---|
| WA0 | WA01, WA02, WA03, WA04 | ContractFreeze |
| WA1 | WA05, WA06, WA07, WA08 | CanonicalModel |
| WA2 | WA09, WA10, WA11, WA12 | ProviderTokenAcquisition |
| WA3 | WA13, WA14, WA15, WA16 | EvidenceAndAdmission |
| WA4 | WA17, WA18, WA19, WA20 | CompatibilityAndSurface |
| WA5 | WA21, WA22, WA23, WA24 | NativeAcceptance |
| WA6 | WA25, WA26, WA27, WA28 | GatewayUnblock |
| WA7 | WA29, WA30, WA31, WA32 | CutoverContinuation |

## Nodes

### WA01 — Freeze current WindowsAuthority legacy semantics and live advertised capabilities.
- Owner: runtime
- Depends: none
- Acceptance: limited/elevated/active_user mapping captured with tests and evidence.

### WA02 — Freeze launcher/broker current token evidence fields and provider digests.
- Owner: runtime
- Depends: none
- Acceptance: current limited/elevated/active_user evidence contract has golden fixtures.

### WA03 — Freeze compatibility rule: old requests and exact replays must not change identity.
- Owner: runtime
- Depends: none
- Acceptance: operation/request digests remain stable for legacy request shapes.

### WA04 — Create authority-factorization ADR with brokerAuthority vs payloadIdentity vs payloadPrivilege terminology.
- Owner: runtime
- Depends: WA01, WA02
- Acceptance: no caller-visible field is ambiguously called authority if it describes identity.

### WA05 — Add WindowsExecutionIdentity enum: service|active_user.
- Owner: runtime-core
- Depends: WA04
- Acceptance: serde/schema/unit tests pass.

### WA06 — Add WindowsPayloadPrivilege enum: limited|elevated.
- Owner: runtime-core
- Depends: WA04
- Acceptance: serde/schema/unit tests pass.

### WA07 — Add canonical WindowsExecutionContextRequest {identity, privilege}.
- Owner: runtime-core
- Depends: WA05, WA06
- Acceptance: canonicalization is deterministic and deny_unknown_fields remains enforced.

### WA08 — Implement legacy WindowsAuthority -> canonical context compiler.
- Owner: runtime-core
- Depends: WA07
- Acceptance: limited->service+limited; elevated->service+elevated; active_user->active_user+limited, with compatibility tests.

### WA09 — Refactor token acquisition API to accept payload identity and payload privilege separately.
- Owner: windows-launcher
- Depends: WA07
- Acceptance: existing three contexts still produce identical effective token evidence.

### WA10 — Implement active_user+elevated token discovery using active session token plus Windows linked-token semantics.
- Owner: windows-launcher
- Depends: WA09
- Acceptance: same SID/session bound; linked token handle is closed; no password/UAC prompt path.

### WA11 — Validate elevated active-user token: primary token, expected SID/session, elevated, High+ integrity, Administrators enabled.
- Owner: windows-launcher
- Depends: WA10
- Acceptance: all mismatches fail closed before target process spawn.

### WA12 — Extend broker argument validator for the exact new launcher context without broadening arbitrary spawn surface.
- Owner: windows-broker
- Depends: WA09, WA10
- Acceptance: only Runtime-bound bundle/job/attempt launch can request composed active-user elevated context.

### WA13 — Replace token-class-only validation with identity+privilege evidence validation.
- Owner: runtime-core
- Depends: WA09, WA11
- Acceptance: start evidence independently proves identity and privilege dimensions.

### WA14 — Freeze admission SID/session and privilege intent into execution plan identity.
- Owner: runtime-core
- Depends: WA07, WA13
- Acceptance: session/user change after admission fails closed.

### WA15 — Bind privileged broker digest for all contexts that require broker transport.
- Owner: runtime-core
- Depends: WA12, WA14
- Acceptance: provider drift invalidates dispatch before effect.

### WA16 — Keep immutable-input Windows authority contract limited-only.
- Owner: runtime-core
- Depends: WA07
- Acceptance: active_user/elevated/composed contexts remain rejected for immutable-input entrypoints until separately graduated.

### WA17 — Add optional structured windowsContext to ordinary workspace.exec/plan contracts while retaining windowsAuthority legacy field.
- Owner: runtime-mcp
- Depends: WA08, WA14
- Acceptance: old clients continue to work; new clients can express active_user+elevated.

### WA18 — Define conflict rule when legacy windowsAuthority and windowsContext are both supplied.
- Owner: runtime-mcp
- Depends: WA17
- Acceptance: equivalent pair canonicalized; conflicting pair rejected deterministically.

### WA19 — Extend runtime.describe from flat authorities to structured supported Windows contexts, retaining legacy projection during migration.
- Owner: runtime-mcp
- Depends: WA17
- Acceptance: availability advertised only after provider probe proves each context.

### WA20 — Keep Gateway context strings provider-defined; verify no Gateway enum needs new semantic authority.
- Owner: gateway
- Depends: WA17, WA19
- Acceptance: Gateway forwards new provider context without owning its semantics.

### WA21 — Unit/property tests for all four identity×privilege combinations and invalid combinations.
- Owner: runtime-tests
- Depends: WA11, WA13, WA18
- Acceptance: deterministic PASS with fail-closed negatives.

### WA22 — Real-machine context probe for active_user+elevated, no target effect.
- Owner: windows-native-acceptance
- Depends: WA21
- Acceptance: same interactive SID/session, elevated=true, High+ integrity, Administrators enabled.

### WA23 — Harmless process smoke under active_user+elevated and compare with limited/elevated/active_user.
- Owner: windows-native-acceptance
- Depends: WA22
- Acceptance: identity/session/integrity evidence matches requested context; Job lifecycle succeeds.

### WA24 — Negative acceptance: no-linked-token/session-change/provider-drift/cancel/timeout/descendant cleanup.
- Owner: windows-native-acceptance
- Depends: WA23
- Acceptance: all unsafe states fail closed; Job Object cleanup remains intact.

### WA25 — Use composed context to stage latest immutable Gateway release from WSL source into protected Windows candidate root.
- Owner: gateway-cutover
- Depends: WA23, WA24
- Acceptance: release receipt binds exact source SHA and ProgramData artifact digests.

### WA26 — Use composed context for repository file-to-file Runtime bearer materialization without emitting secret bytes.
- Owner: gateway-cutover
- Depends: WA23, WA24
- Acceptance: credential receipts contain destination/length/digest/DACL only; candidate stopped during copy.

### WA27 — Rebind/protect/start Windows Gateway candidate on latest release and re-run GC3-05..GC3-10.
- Owner: gateway-cutover
- Depends: WA25, WA26
- Acceptance: Windows/Linux execution + artifacts + Host + 16-tool parity all PASS.

### WA28 — Retire superseded manual H1 classification and update Host continuity/current-state artifacts.
- Owner: gateway-cutover
- Depends: WA27
- Acceptance: no current planning artifact claims inherent HUMAN_REQUIRED for this effect.

### WA29 — GC3-11 Windows northbound Cloudflare Access binding and isolated canary ingress.
- Owner: gateway-cutover
- Depends: WA27
- Acceptance: authenticated canary reaches Windows Gateway; production unchanged.

### WA30 — GC3-13/14 semantic differential and owner-fault matrix.
- Owner: gateway-cutover
- Depends: WA29
- Acceptance: WSL and Windows carriers semantically equivalent; owner failures are scoped.

### WA31 — GC3-15..17 WSL-off, WSL-return-without-Gateway-restart, and cold-boot acceptance.
- Owner: gateway-cutover
- Depends: WA30
- Acceptance: Gateway+Windows execution survive WSL absence; WSL capabilities recover independently.

### WA32 — GC3-18..24 reviewed public cutover, marker proof, rollback drill, WSL public ingress retirement, closure.
- Owner: gateway-cutover
- Depends: WA31
- Acceptance: public marker lands only on Windows carrier; rollback proven; old ingress retired only after proof.

## Current executable frontier

WA01 → WA04 can start immediately. No Gateway production-route mutation is required until WA29+.

## Do-not-build

- a second Windows execution engine
- a Gateway-owned privilege model
- a new credential store
- a password/UAC-prompt automation path
- global ACL relaxation
- a permanent active_user_elevated enum if structured identity+privilege can represent it
- duplicate Job/Attempt/effect lifecycle outside Runtime

## Current standing — 2026-09-23 17:02 +08:00

Source implementation has crossed WA01-WA21 mechanically. Core, MCP, and Windows static gates are green. `runtime.describe` now projects live-probed `windowsContexts` while preserving legacy `windowsAuthorities`; the immutable-input bound contract intentionally does not expose `windowsContext`.

The current executable frontier is WA22: deploy the isolated Windows Runtime candidate source and prove `active_user x elevated` through the real LocalSystem Privileged Broker. A direct probe launched merely as a SYSTEM payload is not valid evidence for WA22. During this run the machine also had no usable active interactive user token (`WTSQueryUserToken` Win32 1008); this is retained as one WA24 fail-closed observation, not treated as an implementation failure.

Legacy conflict semantics are compatibility-first: the legacy wire field defaults to `windowsAuthority=limited`, so `limited` acts as the sentinel when a structured `windowsContext` is present. Non-default legacy values (`elevated`, `active_user`) remain exact conflict fences.
