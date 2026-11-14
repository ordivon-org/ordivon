# Harness R25 — Native V4 author and original PostgreSQL consumer

2026-11-15; **local private source candidate**, not production-installed or published.

## Core result

Rust now authors ProviderCallV4 CLAIMED → DISPATCHING → UNKNOWN records and typed FailureReceipt, using source-equivalent `recordId` and exact Canonical JSON. The original Python producer creates ONLY independent source-oracle record bytes and the original Run/State/Source fixture (not the native Provider V4 or Failure CAS objects). Native Rust writes all four newly generated objects via the same original PostgreSQL CAS primitive shared with Run birth, then the existing lease-fenced Journal commits the associated events.

The R24 test-only `DurableJournal` adapter now authors/stores Claim and Dispatch V4 CAS only in `prepare_provider` (before actual HTTP), then authors/stores Failure and UNKNOWN CAS only in `record_pause` (after the real local server has received exact request bytes and closed without a reply). The server has an independent SELECT-only PostgreSQL reader, proving that `DISPATCHING` is durably committed before physical request processing. NativeAgentLoop reports `PausedUnknown`; PG ProviderHead is UNKNOWN, Run status is still active (no fabricated official RunPaused Event). Original Python Store and Rust reader independently verify the same V4 causal history and exact CAS bytes. No blind transport resend.

## Reuse and consumer boundaries

- Thought: reuse > compose > custom; Event Sourcing, Design by Contract, causality, exact representation, independent falsification, UNKNOWN is not FALSE.
- Logic: L1 contract/provider identity; L2 PG CAS+Journal; L4 NativeAgentLoop; L5 Provider request; L8 ambiguity/recovery; L9 usage only ephemeral as of R22.
- Ability: `provider_v4_author.rs` native typed V4/Failure author (new), `harness-pg::provider_cas` (new narrow typed CAS entry), **existing** `run_create::store_cas`, `journal_write::append_events`, `lease::acquire_run_lease`, original Python V4 pure source oracle and Source Store, R23 frozen request bytes, actual loopback HTTP, existing real PG18 runner.

No new SQLite, proxy, external writer, scheduler or duplicate state authority. No credentials, HTTP Provider bodies or private tool outputs are stored in this change.

## Evidence

- Live scratch PG18 test: original Python Run/State/Source, native Rust V4/Failure CAS authorship, NativeAgentLoop-driven Claim/Dispatch/UNKNOWN, actual local HTTP loss, independent Python Store + SELECT-only Rust readback, original negative source cases: PASS.
- Full Cargo workspace tests, format and strict Clippy: PASS, Harness Loop **86/86**, source before commit R24 `0d77b2a337bb2343bca1156daecb7abf1c3226aa`.
- Verification Job: `job-01a1dbd2-718b-701f-9771-8bc62b68a440` (scratch PG stopped/removed).
- Free model metadata audit: configured OpenRouter credential entry exists and the public official /api/v1/models returned 14 free text models priced zero prompt/completion and advertising tools; selected targets are `particle-ai/particle-1:free`, `recursive/flint-v1.0:free`, `cohere/north-mini-code:free`. Default configured model `openrouter/auto` **is not price-qualified**. A first proposal to combine credential use with an external HTTP call was blocked by tool security review; no authenticated model request was made or charged. Do not bypass protection or call any paid fallback.

## Hard unresolved P0

1. The current Native V4 test-only adapter still receives test-only source identity and simulated clock; move source-authored semantics into a production CAS+Journal Port that checks true PG current Run/Provider binding, request bytes, lease, budget, model policy and Security-owned credentials *at physical send*. No direct `config.apiKey` injection into the tool command.
2. ModelSuccess path with source-valid `AgentTurnResult`, completed Provider V4 Record, committed Usage observation with actual pricing/late settlement and no fabricated cost. Actual authenticated free-model API call needs an approved Security/credential-materialization tool.
3. Installed Gateway capability `execution.harness`, issuer currentness at physical Tool spawn, Runtime OwnerReceipt and an independently evaluated real Coding task.
4. Later: independent TLA+/Quint / SQL/physical schedule refinement, consumers graph/README and duplicate code cleanup only once qualified. Keep Work OPEN.
