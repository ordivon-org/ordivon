# Harness R27 — Verified Wire Observation for real HTTP Provider results

2026-11-15. Local PRIVATE source, parent R26 `07d7d9f2920a48aee76993a03d6c7a1b1d70641f`. Not a production Provider journal or completed external API canary.

## Critical positive-path information boundary

R26's `NativeAgentLoop` gave the `DurableJournal::complete_provider(turn, decision)` caller ONLY an inferred `ModelDecision`, and R22's Token Usage remained entirely private to the HTTP Provider. A future PG `COMPLETED` V4 consumer cannot construct accurate `AgentTurnResult` and `Usage` or link source raw Provider response bytes from that decision alone. Doing so would fabricate external evidence or treat missing Usage as zero.

R27 minimally refines the existing Provider and Journal Ports without creating a new Provider SDK, proxy, PostgreSQL Writer or invented domain success:

- `ProviderWireObservation` is a private-constructor value built ONLY by `HttpModelProvider` after the exact bounded HTTP response bytes are completely read and the model completion (including SSE `[DONE]`) is semantically decoded; carries exact SHA256 raw wire bytes digest, length, reported model (optional), Usage (optional), finish_reason.
- `Provider::last_wire_observation()` defaults to None for scripted/fake Providers; the actual HTTP implementation supplies a positive witness or None on unknown/truncation/malformed results. This witness is not a signature, private Tool grant, cost invoice or self-attested DomainSuccess.
- `DurableJournal::complete_provider(turn, decision, wire: Option<&ProviderWireObservation>)` now receives the optional source. Production Journal may fail closed if missing; old scripted tests remain truthful None. Existing consumers updated in Rust-native Loop and three integration tests.
- Source original disposable PG18 Run + real local HTTP: the existing `native_pg_no_tool_http` test Journal now REQUIRES a nonempty verified wire digest/length for positive completed Provider decisions, and requires *no wire evidence* on truncated/unknown results. The noTool Journal is explicitly test-only and does not emit the production `COMPLETED` record.
- Existing real HTTP/SSE tests assert reported token usage is available with the wire witness, while valid responses with no Usage return witness with `reported_usage=None`, and truncated SSE produces no positive witness.
- This is a necessary capability for the positive Provider V4 path; not yet an exact native source `AgentTurnResult` producer or live PG Completed consumer. Do not turn `CompletionProposal` into `AgentSolved`.

## LEGO

Thought: provenance, typed evidence, explicit missing/unknown, causal semantics, source separation, no duplication. Logic L4 native Loop, L5 Provider decoding, L2 PG Journal consumer seam, L9 Usage. Ability existing Rust HTTP/SSE, `cc_usage`, `ProviderWireObservation`, `NativeAgentLoop` trait, original disposable real PG18 noTool HTTP fixture.

## P0 next

Native source-equivalent `AgentTurnResult` and `ProviderCallV4 Completed` writing under live PG fencing, using exact positive wire observation; source Provider reported model / pricing / privacy / usage validation; single safe Security-approved FREE model end-to-end; Gateway installed Harness grant and trusted Agent Coding Task. Direct credential-bearing API attempt was blocked by tool security checks and was NOT worked around; local config keys remain untouched.
