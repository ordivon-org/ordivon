# Harness R23 — Frozen Provider Wire Bytes / PG V4 Causal Source Consumer

2026-11-15. PRIVATE LOCAL SOURCE, NOT installed, pushed, merged or production-qualified.
Base HEAD R22 `87bc328318489837533bc61b000c4a7cc4879942`.
Reuses existing R22 PG-only ProviderConfig and original PostgreSQL Writer/CAS/Lease/Reader.

## What changed and why (P0-CC-03 preparation)

- Existing `HttpModelProvider` now has private `PreparedHttpRequest` containing the **exact** serialised JSON bytes, their SHA256 digest, observed Tool inputs, frozen messages and streaming flag.
- `freeze_next_request_digest` previews/fixes the bytes **before** PG Claim; it returns a digest but no transport, Secret, Tool, Run/lease or model dispatch grant. The actual `reqwest` send uses the frozen bytes with `Content-Type: application/json`, never serializes a second JSON representation. Mismatch to frozen Tool observations or streaming state causes UNKNOWN and quarantines that instance. Unknown cannot refreeze/resend without independently reconciled authority.
- Original Python PG18 Provider V4 test source now builds the exact no-Tool Chat Completions request body and authors `providerRequestDigest` using the **real serialized request bytes**, replacing R22's synthetic provider-request hash. The original `requestDigest` is still a test synthetic caller/request id and no external model/charge is performed.
- Original Rust PG18 `pg_provider_head` native test constructs the exact Provider from the *same PG Contract-bound Transport Snapshot*, freezes its request digest and requires byte equality with Python V4 source *before* it commits `CLAIMED → DISPATCHING`. A real local HTTP server at the PG-selected endpoint consumes the entire transmitted request body, checks byte SHA against the **same** V4 ProviderRequestDigest, and then intentionally closes without a reply. Rust Provider returns UNKNOWN, second PG lease/journal commits UNKNOWN and read-only Rust plus original Python Store verify causal recovery. Changed exact PG retry payload rejected; no duplicate Provider send.
- Independent unit tests assert zero physical dispatch at freeze time, digest changes when task input changes, and post-freeze Tool input drift cannot resubmit or refreeze. Any failure retains UNKNOWN.
- This is one bounded genuine causal test of CAS↔request-body↔loopback-effect; **not** a proof that an installed production Runner rechecks issuer permission atomically at send, nor complete PG/SQL/TLA+ formal refinement.

## Evidence / consumer chart

`HarnessRunContract.sourceRefs` (original PG Contract source)
→ `ObservedProviderTransport` (source kind + exact CAS digest / provider/model/endpoint)
→ `HttpModelProvider::freeze_next_request_digest` (immutable body)
→ original Python V4 `providerRequestDigest` (same exact bytes)
→ Rust PG Lease + `CLAIMED/DISPATCHING` (same Run)
→ genuine local HTTP POST bytes (same digest)
→ connection loss → Provider UNKNOWN (no second send)
→ Rust PG Lease + `UNKNOWN` (same Run)
→ Rust SELECT-only Reader + original Python Store independent readback.

Original opt-in PG18 test with request-body binding: PASS job `job-01a1dbb2-001e-71b2-9ffa-05bd0adcfdba`. True scratch PostgreSQL18 started, stopped and removed, externalProviderCalls=0, physicalToolCalls=0. After test-only freeze/drift negative refinement, full Cargo Workspace all-target suite + strict Clippy and original real PG18 runner: PASS job `job-01a1dbb4-4e4f-72bc-b326-a3ccdf5ce275`, Loop tests 84/84. Journal in noTool Loop remains test-only.

## LEGO / limits

- Thought: Representation-first, Design by Contract, Event Sourcing, causal ordering, immutable-bytes witness, UNKNOWN≠FALSE, independent falsification, reuse-first, current-owner authorization.
- Logic: L1 Run/Provider binding, L2 PG Journal, L5 Provider request, L8 Recovery; L9 cost has only ephemeral token observation; L6/L7 Tool effects / L10 DomainSuccess remain unproven.
- Ability: existing Rust Core `digest_bytes`, `reqwest`, `harness-pg` real PostgreSQL Writer/Lease/CAS/SELECT-only Reader, original Python Store and V4 source fixture, R21 SSE, R22 PG Transport, native Rust HTTP Provider.
- No new SQLite, PG Writer, Proxy, Scheduler, external model credentials, production service, unsafe retry or domain result verifier.

## P0 outstanding

1. Actual authorized external Provider call with Security credentials and precise endpoint/ProviderCall/Run identity, live lease/dispatch and account-entitled or explicitly authorized capped cost, usage + deferred billing reconciliation.
2. Installed Gateway `execution.harness` with issuer-at-physical-spawn grant, same PG Tool Intent/Fence and native Runtime OwnerReceipt.
3. A real model-produced coding patch, independent trusted hidden QA/domain success and comparable external Codex/Claude Agent baseline.
4. Only after actual consumers pass, delete redundant route/wire/transport and consider formal SQL-to-model refinement plus documentation/Workspace maintenance.
