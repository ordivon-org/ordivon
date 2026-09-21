# Execution Reconciliation Comparative Qualification R1

## Exact contract split

The prior question "local reconciliation vs NautilusTrader" was too coarse. The current local file contains two different LEGO contracts:

1. execution-state reconciliation: venue order/fill/position evidence -> reconciled execution state;
2. capital-resolution seam: qualified reconciliation standing -> TigerBeetle pending-transfer resolution.

NautilusTrader is a candidate owner for contract 1. It is not a semantic owner for contract 2.

## Local baseline

Current local baseline:

- source: src/ordivon_capital/market/execution_reconciliation.py;
- size: 168 source lines in the audited workspace;
- direct unit tests: 6;
- venues normalized in this seam: Binance and OKX;
- explicit outcomes: UNKNOWN, AMBIGUOUS, PARTIAL_OPEN, CONTRADICTORY, PROVEN_NO_EFFECT, RECONCILED_ZERO_FILL_TERMINAL, POSITIVE_EXECUTION;
- accounting actions: NO_MUTATION, VOID_PENDING_TRANSFER, POST_PENDING_TRANSFER.

The baseline is intentionally conservative. Absence from a broad snapshot is not proof of no effect, unverified read authority stays UNKNOWN, and zero-fill terminal orders release reservations only when fill coverage is complete.

## External candidate evidence

Local candidate rc4 exposes live reconciliation configuration and the ExecutionMassStatus, OrderStatusReport, FillReport and PositionStatusReport report model.

Upstream latest observed during this audit is 2.0.0rc5, released 2026-09-15 as a pre-release. Upstream documents startup and continuous reconciliation over order, fill and position reports, including external-order recovery, missing-event generation, bounded-history safety and duplicate/report consistency handling.

rc5 also fixes several reconciliation defects that existed in prior releases, including generate_missing_orders=false behavior, Binance Futures bounded-history completeness, hedge-mode position reconciliation, and reconciliation without a data client. This is positive evidence for upstream state-space learning, but also evidence that the release-candidate line is still changing materially.

## Local rc5 qualification attempt

A separate /root/external/nautilus-trader/2.0.0rc5 Python 3.12 environment was created without changing the rc4 control environment or the canonical candidate binding.

The package download did not complete before the 180-second Runtime execution deadline. The environment therefore does not contain an importable nautilus_trader rc5 package and no rc5 executable qualification is claimed.

Standing: EXTERNAL_PREFERRED_FOR_EXECUTION_STATE_PENDING_LOCAL_RC5_QUALIFICATION.

## Decision

No local reconciliation code is deleted in R1.

Target decomposition:

- Nautilus/venue reports own execution-state reconciliation after a locally executable current candidate passes the fault matrix;
- independent venue read-only observation remains a useful cross-check where it provides independent authority;
- Ordivon permanently retains only the cross-owner mapping from qualified reconciliation outcome to TigerBeetle reservation resolution and evidence identity.

External project breadth is not used to erase the local accounting seam.

## rc4 executable differential evidence

The already-bound rc4 candidate was re-run during R1.

Non-live effect matrix standing: PASS_NAUTILUS_NONLIVE_EFFECT_RECONCILIATION_MATRIX.

Observed scenarios and capital resolutions:

- FILL -> POST_PENDING_TRANSFER;
- CANCEL -> VOID_PENDING_TRANSFER;
- DENY -> VOID_PENDING_TRANSFER;
- PARTIAL_FILL_SLICES (two fills) -> POST_PENDING_TRANSFER;
- UNKNOWN_AFTER_SUBMISSION -> NO_MUTATION.

The separate frozen M6 differential also re-ran successfully as a test harness, but Nautilus rc4 lost that exact semantic contract: all frozen AT_THE_OPEN orders were rejected as unsupported while the DAY lifecycle control passed. Overall standing remained PARTIAL_PASS_OMS_RISK_BLOCKED_AT_OPEN_SIMULATION.

This is the required counterexample to project-level adoption: Nautilus demonstrates a material advantage for execution-state/recovery machinery while simultaneously failing an unrelated frozen execution-semantics contract.


## Current standing after latest-language requalification

The earlier provisional preference for NautilusTrader is superseded by executable evidence.

- 2.0.0rc4: historical matrix evidence remains useful, but it was qualified on Python 3.12.13 and therefore fails the current Python 3.14.7 language gate.
- 1.231.0: imports on canonical Python 3.14.7 and exposes reconciliation configuration, but the same effect/risk matrix fails its DENY scenario after a thin API adaptation. The observed outcome was a positive effect followed by AccountBalanceNegative, not the required pre-trade denial/void outcome.
- 2.0.0rc5: upstream targets Python 3.12–3.14 and Rust 1.98.1, but it is a pre-release challenger and local executable qualification has not completed.

Standing: NO_CURRENT_EXTERNAL_CANDIDATE_ADMITTED.

The bounded local reconciliation baseline is therefore retained. It must not grow into a general OMS/recovery engine; a future stable latest-language candidate can still replace the execution-state portion after passing the identical contract.
