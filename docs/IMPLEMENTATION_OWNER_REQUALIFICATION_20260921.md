# Ordivon Capital implementation-owner requalification — 2026-09-21

## Rule

External existence, age, stars, or project maturity makes an implementation a candidate, not an owner.

For replaceable mechanics, the unit of comparison is one exact LEGO contract. The external candidate competes against the smallest credible local composition built on appropriate mature primitives. Authority/provider facts are not replaceable mechanics.

## Decisions

| Contract | Previous assumption | Comparative evidence | Current standing |
| --- | --- | --- | --- |
| bounded policy decision | OPA 1.20.2 owner | 354 deterministic differential cases, 0 mismatches; local direct rule avoids per-decision subprocess and no independent policy-authority boundary exists | local deterministic Python owns current bounded rules; OPA is a historical/future distributed-policy challenger |
| single-host accounting | TigerBeetle 0.17.9 owner | TigerBeetle passes Python 3.14.7 and historical smokes; SQLite WAL/FULL passes same bounded mechanics; 400-step randomized differential has 0 status and 0 balance mismatches | SQLite 3.53.1 owns current ACID/WAL primitive; TigerBeetle is a future distributed-accounting challenger |
| US-equity sizing/feasibility | LEAN owner | latest LEAN 985ef30 builds on .NET SDK 10.0.401 and M1/M2/M3/M4/M6 pass; naive local formula had 1/57 mismatch; fee-aware local implementation corrected the missing IB-style commission loop and reached 0/57 mismatches | local bounded fee-aware sizer owns exact current contract; LEAN remains isolated historical/general-engine challenger |
| historical/general trading engine | LEAN admitted by prior bounded qualification | latest functionality passes, but latest build reports known critical/high NuGet advisories | not core-admitted; historical/general-engine challenger only |
| Market observability consumer | Prometheus/node-exporter/Grafana treated as deployed stack | Network v2 Prometheus is active but has no Market target/rules/series; shared Prometheus 29091 and node exporter 29100 are inactive; Market rules are valid but not loaded | no active Market observability implementation owner; Prometheus 3.14.0 remains a future TSDB/PromQL/alerting candidate |
| lineage/telemetry/visualization | OpenLineage / OpenTelemetry / Grafana implied owners | no active lineage event, collector/exporter, or Grafana service contract | candidates only |

## Current top-level implementation owner

The machine census now has one top-level IMPLEMENTATION_OWNER:

- SQLite 3.53.1 through canonical Python 3.14.7 stdlib sqlite3, scoped only to bounded single-host ACID/WAL accounting mechanics.

Current directly imported mechanics primitives remain explicit at responsibility level rather than being promoted into broad framework ownership:

- websockets 17.1 for WebSocket client/protocol mechanics;
- NumPy 2.5.3, SciPy 1.18.1, and scikit-learn 1.9.1 for admitted numerical/statistical/model primitives;
- PyArrow 25.0.1 / Parquet and DuckDB 1.5.5 for admitted materialization/readback mechanics; jsonschema 4.26.0 for Draft 2020-12 evaluation; MLflow/Pandera/pandas are no longer current dependencies.

Future frameworks such as OpenBB, Qlib/RD-Agent, PyPortfolioOpt, Riskfolio-Lib, NautilusTrader, OpenLineage, OpenTelemetry, and Grafana remain candidates until an exact active contract and comparative qualification exists.

## Canonical closure after requalification

R0-R5 current path:

PyArrow/Parquet + DuckDB primitive readback
-> local bounded US-equity feasibility
-> FIX projection from frozen historical mechanics evidence
-> SQLite durable accounting restart
-> capability census
-> read-only private-reality preflight
-> local deterministic effect policy

Standing:

PASS_BOUNDED_NONLIVE_R0_R5_COMPOSITION_CLOSURE

Full effect path standing:

PASS_FULL_EFFECT_PATH_OKX_LIVE_PROVIDER_BOUND_NO_EXTERNAL_EFFECT_ADMISSION

The full path performed authenticated provider reality reads without disclosing sensitive values. Provider trade capability is present but not bound to an admitted effect path. Order submission remains false; external financial writes and real-money effects were not attempted.

## Remaining boundaries

- Private-account-data admission remains NOT_ADMITTED pending fresh permission verification in the R0-R5 policy state.
- Optional Binance testnet / OKX demo provider registration remains external and pending; it is not required for the current bounded closure.
- Prometheus Market-domain TSDB/alerting is not active; only static Prometheus text projection and validated candidate rules exist.
- LEAN latest remains supply-chain blocked for core admission despite passing functional qualification.
- A broader sizing, leverage, derivatives, multi-lot, brokerage-fee, fill, slippage, distributed-accounting, or observability contract must reopen comparative qualification rather than silently expanding the bounded local implementation.

## Responsibility-level requalification wave

- QuickFIX/n 1.14.1: 120/120 byte-exact sessionless NewOrderSingle TagValue comparisons, zero mismatches. The bounded local projector owns that exact contract; QuickFIX/n is an oracle/future real-session candidate.
- websockets 17.1: retained as the narrow WebSocket protocol/client mechanics owner. The initial fresh dual-venue failure was traced to Network v2/sing-box DNS lookup failure. After DNS recovery and R3 runner hardening, fresh R2 and fresh R3 both pass; the latest hardened-binding R3 reconnect is 689.3 ms for OKX and 5826.4 ms for Binance, generation 2 on both, with three measured rounds each and zero connection errors. A prior PASS with Binance at 19.66 s / generation 4 is retained as transient-outlier evidence.
- OKX read client: the local GET-only Python stdlib client matched @okx_ai/okx-trade-cli 1.4.7 on 120/120 HMAC cases and 3/3 authenticated live structural reads. It owns the exact client mechanics for the provider-capability audit, but the audited live-trade credential has Trade permission and therefore is not admitted as the canonical private-Reality observer. OKX APIs remain provider truth; the dedicated observer lane remains pending fresh permission verification.
- Binance Spot 11.3.0 and USD-M 17.4.0 + Wallet 13.4.0: candidate surfaces only. Private account/USER_DATA contracts are not currently admitted, so method availability cannot create implementation ownership.
- Monitoring validation: local bounded validator matched Pandera 0.33.1 on 400/400 randomized acceptance decisions. MLflow had no current server/UI/search/registry consumer. MLflow, Pandera and pandas were removed; the research/test environment contracted from roughly 102 distributions to 20.
- PyArrow 25.0.1, DuckDB 1.5.5, jsonschema 4.26.0, NumPy 2.5.3, SciPy 1.18.1 and scikit-learn 1.9.1 remain admitted, each only for its explicit format/schema/numerical/statistical/estimator mechanics.


## Final closure verification after responsibility-level requalification

Fresh canonical R0-R5 standing:

PASS_BOUNDED_NONLIVE_R0_R5_COMPOSITION_CLOSURE

All canonical steps passed after the QuickFIX, OKX read-client, and monitoring-persistence substitutions.

Fresh full effect-path standing:

PASS_FULL_EFFECT_PATH_OKX_LIVE_PROVIDER_BOUND_NO_EXTERNAL_EFFECT_ADMISSION

The OKX provider-capability audit uses LOCAL_BOUNDED_OKX_READONLY_CLIENT on Python 3.14.7 stdlib. @okx_ai/okx-trade-cli 1.4.7 appears only as external differential/reference evidence. The audited live-trade credential currently reports read_only and trade permissions, so it is explicitly not promoted into private-Reality observer admission. Order submission remains false, provider trade capability is not bound to the external-effect path, external financial writes remain NOT_ADMITTED, and no real-money effect was attempted.

The synchronized Market environment now contains 20 installed distributions. Full pytest, full Ruff, uv lock consistency, installed-package compatibility, JSON/schema parsing, and git diff checks pass.
